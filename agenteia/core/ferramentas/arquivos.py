"""
Ferramentas para manipulação de arquivos
"""

import os
import json
import shutil
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from agenteia.config import CONFIG
from ..exceptions import FileError, SecurityError, ValidationError
from ...core.logs import setup_logging
from langchain.tools import BaseTool

# Configuração de logging
logger = logging.getLogger(__name__)

def _normalizar_caminho(caminho: str, is_dir: bool = False) -> str:
    """
    Normaliza e valida um caminho de arquivo/diretório.
    """
    caminho = caminho.strip('\"\\\'') # Remove aspas extras
    caminho = os.path.normpath(caminho)

    # Verifica se é um caminho do Windows System32 ou similar restrito (apenas para arquivos)
    if not is_dir:
        caminho_lower = caminho.lower()
        if 'system32' in caminho_lower or 'windows' in caminho_lower:
            raise FileError("Acesso à pasta do Windows não é permitido.")

    # Verifica se é um caminho do desktop
    if 'desktop' in caminho.lower() or 'área de trabalho' in caminho.lower():
        caminho = os.path.expanduser("~/Desktop")

    return caminho

def criar_diretorio_projetos() -> Path:
    """
    Cria e retorna o diretório padrão para projetos.
    """
    try:
        # Criar diretório na pasta do usuário
        diretorio_projetos = Path.home() / "AgenteIA_Projetos"
        diretorio_projetos.mkdir(exist_ok=True)
        return diretorio_projetos
    except Exception as e:
        raise FileError(f"Erro ao criar diretório de projetos: {e}")

def listar_unidades() -> str:
    """
    Lista as unidades (drives) disponíveis no sistema.

    Returns:
        Lista formatada de unidades.
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info("Delegando listar_unidades para MCP Server")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "listar_unidades",
                "parametros": {}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            # Retornar o resultado obtido do MCP Server
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")

        # Lógica existente (fallback local se MCP Client não estiver disponível)
        import psutil # Importar psutil localmente se necessário para o fallback
        unidades = []
        for part in psutil.disk_partitions():
            if 'fixed' in part.opts or 'cdrom' in part.opts: # Filtra por drives fixos e CD-ROMs
                 unidades.append(f"💾 {part.device}")
            elif 'removable' in part.opts:
                 unidades.append(f" removable {part.device}")
            else:
                 unidades.append(f" unknown {part.device}")


        if unidades:
            return "Unidades disponíveis:\n" + "\n".join(unidades)
        else:
            return "Nenhuma unidade encontrada."
                
    except Exception as e:
        logger.error(f"Erro ao listar unidades: {str(e)}")
        raise FileError(f"Erro ao listar unidades: {str(e)}")

def listar_arquivos(diretorio: str, extensao: Optional[str] = None, mcp_client: Optional[Any] = None) -> str:
    """
    Lista arquivos em um diretório.
    
    Args:
        diretorio: Caminho do diretório
        extensao: Extensão para filtrar (opcional)
        mcp_client: Instância do MCPClient para delegar a tarefa
        
    Returns:
        Lista formatada de arquivos
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando listar_arquivos para MCP Server com diretorio: {diretorio}, extensao: {extensao}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "listar_arquivos",
                "parametros": {"diretorio": diretorio, "extensao": extensao}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local" # Assumindo um nome para o agente local que executa as ferramentas
            )
            # Retornar o resultado obtido do MCP Server
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")
        
        # Lógica existente (fallback local se MCP Client não estiver disponível)
        # Normaliza o caminho para Windows
        diretorio = _normalizar_caminho(diretorio, is_dir=True)
        
        # Verifica diretório
        if not os.path.isdir(diretorio):
            raise FileError(f"Diretório não encontrado: {diretorio}")
        
        # Lista arquivos
        arquivos = []
        total_arquivos = 0
        total_diretorios = 0
        tamanho_total = 0
        
        for item in os.listdir(diretorio):
            caminho = os.path.join(diretorio, item)
            
            # Filtra por extensão
            if extensao and not item.endswith(extensao):
                continue
                
            # Adiciona informações
            if os.path.isfile(caminho):
                tamanho = os.path.getsize(caminho)
                tamanho_total += tamanho
                total_arquivos += 1
                # Formata o tamanho de forma legível
                if tamanho < 1024:
                    tamanho_str = f"{tamanho} bytes"
                elif tamanho < 1024 * 1024:
                    tamanho_str = f"{tamanho/1024:.1f} KB"
                else:
                    tamanho_str = f"{tamanho/(1024*1024):.1f} MB"
                arquivos.append(f"📄 {item} ({tamanho_str})")
            elif os.path.isdir(caminho):
                total_diretorios += 1
                arquivos.append(f"📁 {item}/")
        
        # Prepara o cabeçalho com informações do diretório
        cabecalho = f"Conteúdo do diretório: {diretorio}\n"
        cabecalho += f"Total: {total_arquivos} arquivo(s) e {total_diretorios} pasta(s)\n"
        if total_arquivos > 0:
            if tamanho_total < 1024 * 1024:
                tamanho_total_str = f"{tamanho_total/1024:.1f} KB"
            else:
                tamanho_total_str = f"{tamanho_total/(1024*1024):.1f} MB"
            cabecalho += f"Tamanho total: {tamanho_total_str}\n"
        cabecalho += "-" * 50 + "\n"
        
        # Retorna lista formatada
        if arquivos:
            return cabecalho + "\n".join(sorted(arquivos))
        else:
            return f"{cabecalho}Nenhum arquivo encontrado."
            
    except Exception as e:
        logger.error(f"Erro ao listar arquivos: {str(e)}")
        raise FileError(f"Erro ao listar arquivos: {str(e)}")

def ler_arquivo(caminho: str, encoding: str = "utf-8") -> str:
    """
    Lê o conteúdo de um arquivo de texto.
    
    Args:
        caminho: Caminho do arquivo
        encoding: Codificação do arquivo (padrão: utf-8)
        
    Returns:
        Conteúdo do arquivo
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando ler_arquivo para MCP Server com caminho: {caminho}, encoding: {encoding}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "ler_arquivo",
                "parametros": {"caminho": caminho, "encoding": encoding}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")
        
        # Lógica existente (fallback local)
        caminho = _normalizar_caminho(caminho, is_dir=False)

        # Verifica arquivo
        if not os.path.isfile(caminho):
            raise FileError(f"Arquivo não encontrado: {caminho}")
        
        # Lê arquivo
        with open(caminho, 'r', encoding=encoding) as f:
            conteudo = f.read()
        
        return conteudo
        
    except Exception as e:
        logger.error(f"Erro ao ler arquivo: {str(e)}")
        raise FileError(f"Erro ao ler arquivo: {str(e)}")

def escrever_arquivo(caminho: str, conteudo: str) -> str:
    """
    Escreve conteúdo em um arquivo.
    Cria o arquivo se não existir, sobrescreve se existir.
    
    Args:
        caminho: Caminho do arquivo
        conteudo: Conteúdo para escrever
        
    Returns:
        Confirmação de sucesso ou erro
    """
    try:
        # Adicionar mcp_client como argumento opcional
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando escrever_arquivo para MCP Server com caminho: {caminho}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "escrever_arquivo",
                "parametros": {"caminho": caminho, "conteudo": conteudo}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")

        # Lógica existente (fallback local)
        final_caminho = _normalizar_caminho(caminho, is_dir=False)

        # A lógica para tratar caminhos relativos pode precisar ser ajustada
        # se _normalizar_caminho for chamado antes de determinar se é absoluto.
        # Por enquanto, mantenho o comentário para indicar onde estava a lógica original.
        # if not os.path.isabs(caminho):
        #     base_dir = CONFIG["agent"].default_code_output_dir
        #     final_caminho = os.path.join(base_dir, caminho)
        #     logger.info(f"Caminho relativo fornecido. Usando diretório padrão: {final_caminho}")

        # Garantir que o diretório de destino exista
        diretorio_pai = os.path.dirname(final_caminho)
        if diretorio_pai: # Only call makedirs if dirname is not empty
            os.makedirs(diretorio_pai, exist_ok=True)
        
        # Escrever arquivo
        with open(final_caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        return f"Arquivo criado com sucesso: {final_caminho}"
        
    except Exception as e:
        # Log o caminho original e o final_caminho para depuração
        logger.error(f"Erro ao escrever arquivo. Caminho original: '{caminho}', Caminho final: '{final_caminho if 'final_caminho' in locals() else 'N/A'}': {e}", exc_info=True)
        raise FileError(f"Falha ao escrever arquivo '{final_caminho if 'final_caminho' in locals() else caminho}': {e}")

def ler_json(caminho: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Lê um arquivo JSON.
    
    Args:
        caminho: Caminho do arquivo
        encoding: Codificação do arquivo
        
    Returns:
        Dados do JSON
    """
    try:
        # Lê arquivo
        conteudo = ler_arquivo(caminho, encoding)
        
        # Converte JSON
        return json.loads(conteudo)
        
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {str(e)}")
        raise FileError(f"Erro ao decodificar JSON: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao ler JSON: {str(e)}")
        raise FileError(f"Erro ao ler JSON: {str(e)}")

def escrever_json(caminho: str, dados: Dict[str, Any], encoding: str = "utf-8", indent: int = 2) -> str:
    """
    Escreve dados em um arquivo JSON.
    
    Args:
        caminho: Caminho do arquivo
        dados: Dados para escrever
        encoding: Codificação do arquivo
        indent: Indentação do JSON
        
    Returns:
        Mensagem de confirmação
    """
    try:
        # Converte para JSON
        conteudo = json.dumps(dados, ensure_ascii=False, indent=indent)
        
        # Escreve arquivo
        return escrever_arquivo(caminho, conteudo, encoding)
        
    except Exception as e:
        logger.error(f"Erro ao escrever JSON: {str(e)}")
        raise FileError(f"Erro ao escrever JSON: {str(e)}")

def criar_diretorio(caminho: str) -> str:
    """
    Cria um novo diretório.
    
    Args:
        caminho: Caminho do diretório a ser criado
        
    Returns:
        Confirmação de sucesso ou erro
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando criar_diretorio para MCP Server com caminho: {caminho}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "criar_diretorio",
                "parametros": {"caminho": caminho}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")

        # Lógica existente (fallback local)
        # Normaliza o caminho para Windows
        caminho = _normalizar_caminho(caminho, is_dir=True)

        # Verifica se é um caminho do Windows System32 ou similar restrito
        # Esta verificação foi movida para _normalizar_caminho
        # caminho_lower = caminho.lower()
        # if 'system32' in caminho_lower or 'windows' in caminho_lower:
        #     return "Acesso à pasta do Windows não é permitido."
        
        # Verifica se é um caminho do desktop
        # Esta verificação foi movida para _normalizar_caminho
        # if 'desktop' in caminho_lower or 'área de trabalho' in caminho_lower:
        #     caminho = os.path.expanduser("~/Desktop")
        
        # Verifica diretório
        # A verificação se o diretório já existe será tratada por os.makedirs com exist_ok=True
        # if not os.path.isdir(caminho):
        #     raise FileError(f"Diretório não encontrado: {caminho}")
        
        # Criar diretório
        os.makedirs(caminho, exist_ok=True)
        
        return f"Diretório criado com sucesso: {caminho}"
        
    except Exception as e:
        logger.error(f"Erro ao criar diretório {caminho}: {e}")
        raise FileError(f"Falha ao criar diretório: {e}")

def remover_arquivo(caminho: str) -> str:
    """
    Remove (deleta) um arquivo.
    
    Args:
        caminho: Caminho do arquivo a ser removido
        
    Returns:
        Confirmação de sucesso ou erro
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando remover_arquivo para MCP Server com caminho: {caminho}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "remover_arquivo",
                "parametros": {"caminho": caminho}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")

        # Lógica existente (fallback local)
        # Normaliza o caminho para Windows
        caminho = _normalizar_caminho(caminho, is_dir=False)

        # Verifica se é um caminho do Windows System32 ou similar restrito
        # Esta verificação foi movida para _normalizar_caminho
        # caminho_lower = caminho.lower()
        # if 'system32' in caminho_lower or 'windows' in caminho_lower:
        #     return "Acesso à pasta do Windows não é permitido."
        
        # Verifica se é um caminho do desktop
        # Esta verificação foi movida para _normalizar_caminho
        # if 'desktop' in caminho_lower or 'área de trabalho' in caminho_lower:
        #     caminho = os.path.expanduser("~/Desktop")
        
        # Verifica diretório
        # A verificação de diretório não é necessária aqui, pois é para arquivo
        # if not os.path.isdir(caminho):
        #     raise FileError(f"Diretório não encontrado: {caminho}")
        
        # Verifica arquivo
        if not os.path.isfile(caminho):
            raise FileError(f"Arquivo não encontrado: {caminho}")
        
        # Remove arquivo
        os.remove(caminho)
        
        return f"Arquivo removido com sucesso: {caminho}"
        
    except Exception as e:
        logger.error(f"Erro ao remover arquivo {caminho}: {e}")
        raise FileError(f"Falha ao remover arquivo: {e}")

def remover_diretorio(caminho: str) -> str:
    """
    Remove (deleta) um diretório e todo o seu conteúdo recursivamente.
    
    Args:
        caminho: Caminho do diretório a ser removido
        
    Returns:
        Confirmação de sucesso ou erro
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando remover_diretorio para MCP Server com caminho: {caminho}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "remover_diretorio",
                "parametros": {"caminho": caminho}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")

        # Lógica existente (fallback local)
        # Normaliza o caminho para Windows
        caminho = _normalizar_caminho(caminho, is_dir=True)

        # Verifica se é um caminho do Windows System32 ou similar restrito
        # Esta verificação foi movida para _normalizar_caminho
        # caminho_lower = caminho.lower()
        # if 'system32' in caminho_lower or 'windows' in caminho_lower:
        #     return "Acesso à pasta do Windows não é permitido."
        
        # Verifica se é um caminho do desktop
        # Esta verificação foi movida para _normalizar_caminho
        # if 'desktop' in caminho_lower or 'área de trabalho' in caminho_lower:
        #     caminho = os.path.expanduser("~/Desktop")
        
        # Verifica diretório
        if not os.path.isdir(caminho):
            raise FileError(f"Diretório não encontrado: {caminho}")
        
        # Remove diretório e todo o seu conteúdo recursivamente
        shutil.rmtree(caminho)
        
        return f"Diretório removido com sucesso: {caminho}"
        
    except Exception as e:
        logger.error(f"Erro ao remover diretório {caminho}: {e}")
        raise FileError(f"Falha ao remover diretório: {e}")

def copiar_arquivo(origem: str, destino: str) -> str:
    """
    Copia um arquivo de uma origem para um destino.
    
    Args:
        origem: Caminho do arquivo de origem
        destino: Caminho do arquivo de destino
        
    Returns:
        Confirmação de sucesso ou erro
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando copiar_arquivo para MCP Server de origem: {origem} para destino: {destino}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "copiar_arquivo",
                "parametros": {"origem": origem, "destino": destino}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")

        # Lógica existente (fallback local)
        # Normaliza os caminhos para Windows
        origem = _normalizar_caminho(origem, is_dir=False)
        destino = _normalizar_caminho(destino, is_dir=False)

        # Verifica se é um caminho do Windows System32 ou similar restrito
        # Estas verificações foram movidas para _normalizar_caminho
        # origem_lower = origem.lower()
        # destino_lower = destino.lower()
        # if 'system32' in origem_lower or 'windows' in origem_lower or \
        #    'system32' in destino_lower or 'windows' in destino_lower:
        #     return "Acesso a pastas do Windows não é permitido."

        # Verifica se o diretório de destino existe
        if not os.path.isdir(destino):
            raise FileError(f"Diretório de destino não encontrado: {destino}")
        
        # Copiar arquivo
        shutil.copy2(origem, destino)
        
        return f"Arquivo copiado com sucesso: {origem} -> {destino}"
        
    except Exception as e:
        logger.error(f"Erro ao copiar arquivo {origem} -> {destino}: {e}")
        raise FileError(f"Falha ao copiar arquivo: {e}")

def mover_arquivo(origem: str, destino: str) -> str:
    """
    Move um arquivo de uma origem para um destino.
    
    Args:
        origem: Caminho do arquivo de origem
        destino: Caminho do arquivo de destino
        
    Returns:
        Confirmação de sucesso ou erro
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando mover_arquivo para MCP Server de origem: {origem} para destino: {destino}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "mover_arquivo",
                "parametros": {"origem": origem, "destino": destino}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")

        # Lógica existente (fallback local)
        # Normaliza os caminhos para Windows
        origem = _normalizar_caminho(origem, is_dir=False)
        destino = _normalizar_caminho(destino, is_dir=False)

        # Verifica se é um caminho do Windows System32 ou similar restrito
        # Estas verificações foram movidas para _normalizar_caminho
        # origem_lower = origem.lower()
        # destino_lower = destino.lower()
        # if 'system32' in origem_lower or 'windows' in origem_lower or \
        #    'system32' in destino_lower or 'windows' in destino_lower:
        #     return "Acesso a pastas do Windows não é permitido."

        # Verifica se o diretório de destino existe
        if not os.path.isdir(destino):
            raise FileError(f"Diretório de destino não encontrado: {destino}")
        
        # Mover arquivo
        shutil.move(origem, destino)
        
        return f"Arquivo movido com sucesso: {origem} -> {destino}"
        
    except Exception as e:
        logger.error(f"Erro ao mover arquivo {origem} -> {destino}: {e}")
        raise FileError(f"Falha ao mover arquivo: {e}")

def analisar_sentimento(texto: str) -> dict:
    """Analisa o sentimento em um texto."""
    try:
        # Aqui você pode integrar com uma API de análise de sentimento
        # Por exemplo, usando a biblioteca textblob ou uma API externa
        from textblob import TextBlob
        analysis = TextBlob(texto)
        return {
            "polaridade": analysis.sentiment.polarity,
            "subjetividade": analysis.sentiment.subjectivity,
            "sentimento": "positivo" if analysis.sentiment.polarity > 0 else "negativo" if analysis.sentiment.polarity < 0 else "neutro"
        }
    except Exception as e:
        return {"erro": str(e)}

def gerar_resumo(texto: str, max_palavras: int = 100) -> str:
    """Gera um resumo do texto."""
    try:
        # Aqui você pode integrar com uma biblioteca de sumarização
        # Por exemplo, usando a biblioteca sumy ou uma API externa
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.lsa import LsaSummarizer
        
        parser = PlaintextParser.from_string(texto, Tokenizer("portuguese"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, max_palavras)
        
        return " ".join([str(sentence) for sentence in summary])
    except Exception as e:
        return f"Erro ao gerar resumo: {str(e)}"

def classificar_texto(texto: str, categorias: list = None) -> dict:
    """Classifica o texto em categorias."""
    try:
        # Aqui você pode integrar com um modelo de classificação
        # Por exemplo, usando scikit-learn ou uma API externa
        if categorias is None:
            categorias = ["tecnologia", "esporte", "política", "entretenimento", "outros"]
        
        # Implementação básica usando palavras-chave
        categorias_encontradas = {}
        for categoria in categorias:
            palavras_chave = {
                "tecnologia": ["computador", "software", "hardware", "internet", "dados"],
                "esporte": ["futebol", "basquete", "jogos", "competição", "atleta"],
                "política": ["governo", "eleição", "partido", "político", "lei"],
                "entretenimento": ["filme", "música", "arte", "show", "teatro"]
            }
            
            score = sum(1 for palavra in palavras_chave.get(categoria, []) if palavra.lower() in texto.lower())
            if score > 0:
                categorias_encontradas[categoria] = score
        
        return {
            "categorias": categorias_encontradas,
            "categoria_principal": max(categorias_encontradas.items(), key=lambda x: x[1])[0] if categorias_encontradas else "outros"
        }
    except Exception as e:
        return {"erro": str(e)}

def extrair_entidades(texto: str) -> dict:
    """Extrai entidades nomeadas do texto."""
    try:
        # Aqui você pode integrar com uma biblioteca de NER
        # Por exemplo, usando spaCy ou uma API externa
        import spacy
        
        nlp = spacy.load("pt_core_news_sm")
        doc = nlp(texto)
        
        entidades = {
            "pessoas": [],
            "organizações": [],
            "locais": [],
            "datas": [],
            "outros": []
        }
        
        for ent in doc.ents:
            if ent.label_ == "PER":
                entidades["pessoas"].append(ent.text)
            elif ent.label_ == "ORG":
                entidades["organizações"].append(ent.text)
            elif ent.label_ == "LOC":
                entidades["locais"].append(ent.text)
            elif ent.label_ == "DATE":
                entidades["datas"].append(ent.text)
            else:
                entidades["outros"].append(ent.text)
        
        return entidades
    except Exception as e:
        return {"erro": str(e)}

def verificar_plagio(texto: str, fonte: str = None) -> dict:
    """Verifica similaridade entre textos."""
    try:
        # Aqui você pode integrar com uma API de detecção de plágio
        # Por exemplo, usando a biblioteca difflib ou uma API externa
        from difflib import SequenceMatcher
        
        if fonte:
            similaridade = SequenceMatcher(None, texto, fonte).ratio()
            return {
                "similaridade": similaridade,
                "plagio": similaridade > 0.8,
                "nivel": "alto" if similaridade > 0.8 else "médio" if similaridade > 0.5 else "baixo"
            }
        else:
            return {
                "erro": "É necessário fornecer um texto fonte para comparação"
            }
    except Exception as e:
        return {"erro": str(e)}

def verificar_url(
    url: str,
    mcp_client: Optional[Any] = None
) -> Dict[str, bool]:
    """
    Verifica se uma URL está acessível.

    Args:
        url: URL para verificar
        mcp_client: Instância do MCPClient para delegar a tarefa

    Returns:
        Dicionário com status da verificação
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando verificar_url para MCP Server para URL: {url}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "verificar_url",
                "parametros": {"url": url}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            # Adicionar um retorno padrão em caso de resultado vazio ou erro do MCP
            return resultado.get("resultado", {"acessivel": False, "redireciona": False, "https": url.startswith("https://"), "status_code": None, "erro": "Erro ou resultado vazio do MCP Server."})

        # Faz requisição
        response = requests.head(url, timeout=5, allow_redirects=True)

        # ... restante da função
    except Exception as e:
        return {"erro": str(e)} 