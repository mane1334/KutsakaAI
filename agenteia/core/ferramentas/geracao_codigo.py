"""
Ferramentas para geração e análise de código com monitoramento de progresso.
"""

import os
import time
import subprocess
import ast
import astor
from typing import Dict, List, Optional, Callable, Tuple, Any
from pathlib import Path
import importlib.util
import sys
import json

from .monitoramento import (
    monitorar_tarefa, 
    obter_status_tarefa, 
    listar_tarefas_ativas,
    monitor
)
from ..exceptions import AgenteError

def _validar_python(codigo: str) -> Tuple[bool, str]:
    """Valida se o código Python é sintaticamente correto."""
    try:
        ast.parse(codigo)
        return True, "Código válido"
    except SyntaxError as e:
        return False, f"Erro de sintaxe na linha {e.lineno}: {e.msg}"

def _analisar_estrutura_codigo(codigo: str) -> Dict:
    """Analisa a estrutura do código Python."""
    try:
        arvore = ast.parse(codigo)
        
        # Contadores
        funcoes = []
        classes = []
        imports = []
        
        # Analisar nós
        for node in ast.walk(arvore):
            if isinstance(node, ast.FunctionDef):
                funcoes.append({
                    'nome': node.name,
                    'args': [arg.arg for arg in node.args.args],
                    'linha': node.lineno
                })
            elif isinstance(node, ast.ClassDef):
                metodos = [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
                classes.append({
                    'nome': node.name,
                    'metodos': metodos,
                    'linha': node.lineno
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.extend(alias.name for alias in (node.names or []))
        
        return {
            'num_linhas': len(codigo.splitlines()),
            'num_funcoes': len(funcoes),
            'num_classes': len(classes),
            'imports': imports,
            'funcoes': funcoes,
            'classes': classes
        }
    except Exception as e:
        raise AgenteError(f"Erro ao analisar código: {str(e)}")

def _executar_codigo(codigo: str, contexto: Optional[Dict] = None) -> Tuple[bool, str]:
    """Executa o código em um ambiente controlado."""
    contexto = contexto or {}
    
    # Criar um contexto de execução seguro
    contexto_exec = {
        '__builtins__': {
            'print': print,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
        },
        **contexto
    }
    
    try:
        # Executa o código no contexto fornecido
        exec(codigo, contexto_exec, contexto_exec)
        return True, "Código executado com sucesso"
    except Exception as e:
        return False, f"Erro durante a execução: {str(e)}"

def gerar_codigo(
    descricao: str, 
    linguagem: str = "python", 
    contexto: Optional[Dict] = None,
    mcp_client: Optional[Any] = None
) -> Dict:
    """
    Gera código com base em uma descrição.
    
    Args:
        descricao: Descrição do código a ser gerado
        linguagem: Linguagem de programação (atualmente só suporta 'python')
        contexto: Contexto adicional para geração
        mcp_client: Cliente MCP (se disponível)
        
    Returns:
        Dicionário com o código gerado e metadados
    """
    if linguagem.lower() != 'python':
        raise AgenteError("Apenas Python é suportado no momento")
    
    # Refatoração para usar MCP Client se disponível
    if mcp_client:
        logger.info(f"Delegando gerar_codigo para MCP Server para descrição: {descricao}")
        tarefa_execucao = {
            "tipo": "executar_ferramenta",
            "nome_ferramenta": "gerar_codigo",
            "parametros": {"descricao": descricao, "linguagem": linguagem, "contexto": contexto}
        }
        resultado = mcp_client.distribuir_tarefa(
            tarefa=json.dumps(tarefa_execucao),
            agente_id="Agente Local"
        )
        # O resultado esperado para gerar_codigo é um dicionário com o código e metadados
        # Adicionei a importação de json se já não estiver presente
        try:
            resultado_dict = json.loads(resultado.get("resultado", "{}"))
            return resultado_dict
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON do resultado do MCP Server: {e}")
            return {"erro": "Erro ao processar resultado do MCP Server", "detalhes": str(e)}

    # Em um cenário real, isso seria uma chamada para um modelo de linguagem
    # Aqui estamos simulando com um exemplo simples
    codigo_exemplo = f""""
# {descricao}

def main():
    print("Olá, mundo!")
    return "Função executada com sucesso"

if __name__ == "__main__":
    resultado = main()
    print(f"Resultado: {resultado}")
"""
    
    # Validar o código
    valido, mensagem = _validar_python(codigo_exemplo)
    
    # Analisar estrutura
    estrutura = _analisar_estrutura_codigo(codigo_exemplo)
    
    # Executar o código (opcional)
    executado, resultado_exec = _executar_codigo(codigo_exemplo, contexto or {})
    
    return {
        'codigo': codigo_exemplo,
        'valido': valido,
        'mensagem_validacao': mensagem,
        'executado': executado,
        'resultado_execucao': resultado_exec if executado else None,
        'estrutura': estrutura
    }

@monitorar_tarefa("Geração de código", 4)
def gerar_codigo_completo(
    requisitos: str, 
    linguagem: str = "python",
    progress_callback: Optional[Callable] = None
) -> Dict:
    """
    Gera código completo com monitoramento de progresso.
    
    Args:
        requisitos: Requisitos do código a ser gerado
        linguagem: Linguagem de programação
        progress_callback: Função de callback para atualização de progresso
        
    Returns:
        Dicionário com o código gerado e metadados
    """
    # Passo 1: Análise dos requisitos
    if progress_callback:
        progress_callback(1, "Analisando requisitos...")
    
    # Simular análise de requisitos
    time.sleep(1)
    
    # Passo 2: Geração do código base
    if progress_callback:
        progress_callback(1, "Gerando código base...")
    
    resultado = gerar_codigo(requisitos, linguagem)
    
    # Passo 3: Validação do código
    if progress_callback:
        progress_callback(1, "Validando código gerado...")
    
    if not resultado['valido']:
        raise AgenteError(f"Código inválido: {resultado['mensagem_validacao']}")
    
    # Passo 4: Teste de execução
    if progress_callback:
        progress_callback(1, "Testando execução do código...")
    
    if not resultado['executado']:
        raise AgenteError(f"Erro na execução: {resultado['resultado_execucao']}")
    
    return resultado

def obter_status_geracao_codigo(task_id: str) -> Dict:
    """
    Obtém o status de uma tarefa de geração de código.
    
    Args:
        task_id: ID da tarefa
        
    Returns:
        Status da tarefa
    """
    status = obter_status_tarefa(task_id)
    if not status:
        return {"erro": f"Tarefa {task_id} não encontrada"}
    
    # Adicionar informações específicas de geração de código
    if status['status'] == 'concluida' and 'resultado' in status:
        resultado = status['resultado']
        status.update({
            'estatisticas': {
                'linhas': len(resultado.get('codigo', '').splitlines()),
                'funcoes': len(resultado.get('estrutura', {}).get('funcoes', [])),
                'classes': len(resultado.get('estrutura', {}).get('classes', []))
            },
            'imports': resultado.get('estrutura', {}).get('imports', [])
        })
    
    return status

def listar_tarefas_ativas_geracao() -> List[Dict]:
    """
    Lista todas as tarefas ativas de geração de código.
    
    Returns:
        Lista de tarefas ativas
    """
    return listar_tarefas_ativas()

# Exemplo de uso:
if __name__ == "__main__":
    # Iniciar uma tarefa de geração de código
    task_id = monitor.criar_tarefa("Geração de código de exemplo", 4)
    
    try:
        # Simular progresso
        for i in range(4):
            monitor.atualizar_progresso(
                task_id, 
                1, 
                f"Etapa {i+1}/4 em andamento..."
            )
            time.sleep(1)
        
        # Finalizar com sucesso
        monitor.finalizar_tarefa(task_id, {
            'codigo': 'print("Hello, World!")',
            'estrutura': {
                'funcoes': [{'nome': 'main', 'args': [], 'linha': 1}],
                'classes': []
            }
        })
        
        # Verificar status
        print(obter_status_geracao_codigo(task_id))
        
    except Exception as e:
        monitor.registrar_erro(task_id, str(e))
        print(f"Erro: {e}")
