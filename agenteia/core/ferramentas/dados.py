import json
import csv
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def converter_formato(dados: Any, formato_origem: str, formato_destino: str) -> str:
    """Converte dados entre diferentes formatos (JSON, CSV, XML)."""
    try:
        # Converter para formato intermediário (dicionário)
        if formato_origem == "json":
            dados_intermediarios = json.loads(dados) if isinstance(dados, str) else dados
        elif formato_origem == "csv":
            dados_intermediarios = pd.read_csv(dados).to_dict() if isinstance(dados, str) else pd.DataFrame(dados).to_dict()
        elif formato_origem == "xml":
            root = ET.fromstring(dados) if isinstance(dados, str) else dados
            dados_intermediarios = xml_para_dict(root)
        else:
            raise ValueError(f"Formato de origem não suportado: {formato_origem}")

        # Converter do formato intermediário para o formato de destino
        if formato_destino == "json":
            return json.dumps(dados_intermediarios, ensure_ascii=False, indent=2)
        elif formato_destino == "csv":
            df = pd.DataFrame(dados_intermediarios)
            return df.to_csv(index=False)
        elif formato_destino == "xml":
            return dict_para_xml(dados_intermediarios)
        else:
            raise ValueError(f"Formato de destino não suportado: {formato_destino}")
    except Exception as e:
        logger.error(f"Erro ao converter dados: {e}")
        raise

def validar_dados(dados: Any, schema: Dict) -> Dict:
    """Valida dados contra um schema definido."""
    try:
        erros = []
        
        def validar_campo(valor: Any, regras: Dict) -> List[str]:
            erros_campo = []
            
            if "tipo" in regras:
                tipo_esperado = regras["tipo"]
                if tipo_esperado == "string" and not isinstance(valor, str):
                    erros_campo.append(f"Tipo esperado: string, recebido: {type(valor)}")
                elif tipo_esperado == "number" and not isinstance(valor, (int, float)):
                    erros_campo.append(f"Tipo esperado: number, recebido: {type(valor)}")
                elif tipo_esperado == "boolean" and not isinstance(valor, bool):
                    erros_campo.append(f"Tipo esperado: boolean, recebido: {type(valor)}")
            
            if "obrigatorio" in regras and regras["obrigatorio"] and valor is None:
                erros_campo.append("Campo obrigatório não preenchido")
            
            if "min" in regras and valor < regras["min"]:
                erros_campo.append(f"Valor menor que o mínimo permitido: {regras['min']}")
            
            if "max" in regras and valor > regras["max"]:
                erros_campo.append(f"Valor maior que o máximo permitido: {regras['max']}")
            
            if "padrao" in regras and not re.match(regras["padrao"], str(valor)):
                erros_campo.append(f"Valor não corresponde ao padrão esperado: {regras['padrao']}")
            
            return erros_campo
        
        for campo, regras in schema.items():
            if campo in dados:
                erros_campo = validar_campo(dados[campo], regras)
                if erros_campo:
                    erros.append({campo: erros_campo})
            elif regras.get("obrigatorio", False):
                erros.append({campo: ["Campo obrigatório não encontrado"]})
        
        return {
            "valido": len(erros) == 0,
            "erros": erros
        }
    except Exception as e:
        logger.error(f"Erro ao validar dados: {e}")
        raise

def filtrar_dados(dados: List[Dict], filtros: Dict) -> List[Dict]:
    """Filtra e ordena um conjunto de dados."""
    try:
        df = pd.DataFrame(dados)
        
        # Aplicar filtros
        for campo, valor in filtros.get("filtros", {}).items():
            if isinstance(valor, (list, tuple)):
                df = df[df[campo].isin(valor)]
            else:
                df = df[df[campo] == valor]
        
        # Aplicar ordenação
        if "ordenacao" in filtros:
            campo = filtros["ordenacao"]["campo"]
            ascendente = filtros["ordenacao"].get("ascendente", True)
            df = df.sort_values(by=campo, ascending=ascendente)
        
        # Aplicar limite
        if "limite" in filtros:
            df = df.head(filtros["limite"])
        
        return df.to_dict("records")
    except Exception as e:
        logger.error(f"Erro ao filtrar dados: {e}")
        raise

def agregar_dados(dados: List[Dict], agrupamentos: List[str], metricas: Dict[str, str]) -> Dict:
    """Realiza agregações e estatísticas nos dados."""
    try:
        df = pd.DataFrame(dados)
        
        # Realizar agrupamentos
        grupos = df.groupby(agrupamentos)
        
        # Calcular métricas
        resultados = {}
        for nome, funcao in metricas.items():
            if funcao == "soma":
                resultados[nome] = grupos.sum()
            elif funcao == "media":
                resultados[nome] = grupos.mean()
            elif funcao == "min":
                resultados[nome] = grupos.min()
            elif funcao == "max":
                resultados[nome] = grupos.max()
            elif funcao == "contagem":
                resultados[nome] = grupos.size()
        
        return {
            "agrupamentos": agrupamentos,
            "metricas": resultados
        }
    except Exception as e:
        logger.error(f"Erro ao agregar dados: {e}")
        raise

def visualizar_dados(dados: List[Dict], tipo: str, config: Dict) -> str:
    """Cria visualizações básicas dos dados."""
    try:
        df = pd.DataFrame(dados)
        
        if tipo == "grafico_barras":
            plt.figure(figsize=(10, 6))
            df.plot(kind="bar", x=config["eixo_x"], y=config["eixo_y"])
            plt.title(config.get("titulo", "Gráfico de Barras"))
            plt.xlabel(config.get("label_x", ""))
            plt.ylabel(config.get("label_y", ""))
            
        elif tipo == "grafico_linha":
            plt.figure(figsize=(10, 6))
            df.plot(kind="line", x=config["eixo_x"], y=config["eixo_y"])
            plt.title(config.get("titulo", "Gráfico de Linha"))
            plt.xlabel(config.get("label_x", ""))
            plt.ylabel(config.get("label_y", ""))
            
        elif tipo == "grafico_pizza":
            plt.figure(figsize=(10, 6))
            df.plot(kind="pie", y=config["valores"], labels=config["labels"])
            plt.title(config.get("titulo", "Gráfico de Pizza"))
            
        elif tipo == "histograma":
            plt.figure(figsize=(10, 6))
            df[config["coluna"]].hist()
            plt.title(config.get("titulo", "Histograma"))
            plt.xlabel(config.get("label_x", ""))
            plt.ylabel(config.get("label_y", "Frequência"))
            
        else:
            raise ValueError(f"Tipo de visualização não suportado: {tipo}")
        
        # Salvar gráfico
        caminho_arquivo = f"visualizacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(caminho_arquivo)
        plt.close()
        
        return caminho_arquivo
    except Exception as e:
        logger.error(f"Erro ao visualizar dados: {e}")
        raise

# Funções auxiliares
def xml_para_dict(elemento: ET.Element) -> Dict:
    """Converte um elemento XML para dicionário."""
    resultado = {}
    for filho in elemento:
        if len(filho) > 0:
            resultado[filho.tag] = xml_para_dict(filho)
        else:
            resultado[filho.tag] = filho.text
    return resultado

def dict_para_xml(dados: Dict) -> str:
    """Converte um dicionário para XML."""
    def _criar_elemento(pai: ET.Element, nome: str, valor: Any) -> None:
        elemento = ET.SubElement(pai, nome)
        if isinstance(valor, dict):
            for k, v in valor.items():
                _criar_elemento(elemento, k, v)
        else:
            elemento.text = str(valor)
    
    raiz = ET.Element("root")
    for k, v in dados.items():
        _criar_elemento(raiz, k, v)
    
    return ET.tostring(raiz, encoding="unicode") 