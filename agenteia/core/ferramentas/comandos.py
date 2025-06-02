"""
Ferramentas para execução de comandos e gerenciamento de processos
"""

import os
import sys
import subprocess
import psutil
import logging
import json
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from ..exceptions import ToolError
from ...logs import setup_logging

# Configuração de logging
logger = logging.getLogger(__name__)

def executar_comando(
    comando: str,
    shell: bool = True,
    timeout: Optional[int] = 30,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    mcp_client: Optional[Any] = None
) -> str:
    """
    Executa um comando shell.
    
    Args:
        comando: Comando a executar
        shell: Se deve usar shell
        timeout: Timeout em segundos
        cwd: Diretório de trabalho
        env: Variáveis de ambiente
        mcp_client: Cliente MCP para delegar a execução (opcional)
        
    Returns:
        Saída do comando
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando executar_comando para MCP Server: {comando}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "executar_comando",
                "parametros": {"comando": comando, "shell": shell, "timeout": timeout, "cwd": cwd, "env": env}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")

        # Lógica existente (fallback local)
        # Prepara ambiente
        if env is None:
            env = os.environ.copy()
        
        # Executa comando
        processo = subprocess.run(
            comando,
            shell=shell,
            timeout=timeout,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # Verifica erro
        if processo.returncode != 0:
            erro = processo.stderr.strip()
            if not erro:
                erro = "Comando falhou sem mensagem de erro"
            raise ToolError(f"Erro ao executar comando: {erro}")
        
        # Retorna saída
        return processo.stdout.strip()
        
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout ao executar comando: {comando}")
        raise ToolError(f"Timeout ao executar comando: {comando}")
    except Exception as e:
        logger.error(f"Erro ao executar comando: {str(e)}")
        raise ToolError(f"Erro ao executar comando: {str(e)}")

def executar_comando_async(
    comando: str,
    shell: bool = True,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    mcp_client: Optional[Any] = None
) -> Tuple[subprocess.Popen, str]:
    """
    Executa um comando assincronamente.
    
    Args:
        comando: Comando a executar
        shell: Se deve usar shell
        cwd: Diretório de trabalho
        env: Variáveis de ambiente
        mcp_client: Cliente MCP para delegar a execução (opcional)
        
    Returns:
        Tupla (processo, id)
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando executar_comando_async para MCP Server: {comando}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "executar_comando_async",
                "parametros": {"comando": comando, "shell": shell, "cwd": cwd, "env": env}
            }
            # Para execução assíncrona, talvez precisemos de um tipo de retorno diferente
            # ou uma forma de consultar o status/saída via MCP. Por enquanto, vamos apenas
            # simular a delegação e retornar um placeholder ou levantar um NotImplementedError
            # se a API do MCP para async não estiver definida.
            # result = mcp_client.distribuir_tarefa(
            #     tarefa=json.dumps(tarefa_execucao),
            #     agente_id="Agente Local"
            # )
            # return result, result.get("id", "Erro: ID vazio do MCP Server.")
            raise NotImplementedError("Delegação assíncrona via MCP Client não implementada completamente.")

        # Prepara ambiente
        if env is None:
            env = os.environ.copy()
        
        # Executa comando
        processo = subprocess.Popen(
            comando,
            shell=shell,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # Gera ID
        id = f"cmd_{processo.pid}"
        
        return processo, id
        
    except Exception as e:
        logger.error(f"Erro ao executar comando assíncrono: {str(e)}")
        raise ToolError(f"Erro ao executar comando assíncrono: {str(e)}")

def verificar_processo(pid: int) -> Dict[str, Any]:
    """
    Verifica status de um processo.
    
    Args:
        pid: ID do processo
        
    Returns:
        Status do processo
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando verificar_processo para MCP Server com PID: {pid}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "verificar_processo",
                "parametros": {"pid": pid}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            return resultado.get("resultado", {"ativo": False, "pid": pid, "comando": None, "erro": "Erro ou resultado vazio do MCP Server."})

        # Verifica processo
        processo = subprocess.run(
            f"tasklist /FI \"PID eq {pid}\" /NH",
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # Processa saída
        if processo.returncode == 0 and str(pid) in processo.stdout:
            return {
                "ativo": True,
                "pid": pid,
                "comando": processo.stdout.strip()
            }
        else:
            return {
                "ativo": False,
                "pid": pid,
                "comando": None
            }
            
    except Exception as e:
        logger.error(f"Erro ao verificar processo: {str(e)}")
        raise ToolError(f"Erro ao verificar processo: {str(e)}")

def encerrar_processo(pid: int, forcar: bool = False) -> str:
    """
    Encerra um processo.
    
    Args:
        pid: ID do processo
        forcar: Se deve forçar encerramento
        
    Returns:
        Mensagem de confirmação
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando encerrar_processo para MCP Server com PID: {pid}, forcar: {forcar}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "encerrar_processo",
                "parametros": {"pid": pid, "forcar": forcar}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")

        # Verifica processo
        status = verificar_processo(pid)
        if not status["ativo"]:
            return f"Processo {pid} não está ativo"
        
        # Encerra processo
        comando = f"taskkill /F /PID {pid}" if forcar else f"taskkill /PID {pid}"
        subprocess.run(comando, shell=True, check=True)
        
        return f"Processo {pid} encerrado com sucesso"
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao encerrar processo: {str(e)}")
        raise ToolError(f"Erro ao encerrar processo: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao encerrar processo: {str(e)}")
        raise ToolError(f"Erro ao encerrar processo: {str(e)}")

def listar_processos() -> str:
    """
    Lista processos ativos.
    
    Returns:
        Lista formatada de processos
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info("Delegando listar_processos para MCP Server")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "listar_processos",
                "parametros": {}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")

        # Lista processos
        processo = subprocess.run(
            "tasklist /NH",
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # Processa saída
        if processo.returncode == 0:
            linhas = processo.stdout.strip().split('\n')
            processos = []
            
            for linha in linhas:
                if linha.strip():
                    partes = linha.split()
                    if len(partes) >= 2:
                        nome = partes[0]
                        pid = partes[1]
                        memoria = partes[4] if len(partes) > 4 else "N/A"
                        processos.append(f"- {nome} (PID: {pid}, Memória: {memoria})")
            
            return "\n".join(sorted(processos))
        else:
            return "Erro ao listar processos"
            
    except Exception as e:
        logger.error(f"Erro ao listar processos: {str(e)}")
        raise ToolError(f"Erro ao listar processos: {str(e)}")

def executar_python(
    script: str,
    args: Optional[List[str]] = None,
    timeout: Optional[int] = 30,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> str:
    """
    Executa um script Python.
    
    Args:
        script: Caminho do script
        args: Argumentos do script
        timeout: Timeout em segundos
        cwd: Diretório de trabalho
        env: Variáveis de ambiente
        
    Returns:
        Saída do script
    """
    try:
        # Prepara comando
        comando = ["python", script]
        if args:
            comando.extend(args)
        
        # Executa script
        processo = subprocess.run(
            comando,
            timeout=timeout,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # Verifica erro
        if processo.returncode != 0:
            erro = processo.stderr.strip()
            if not erro:
                erro = "Script falhou sem mensagem de erro"
            raise ToolError(f"Erro ao executar script: {erro}")
        
        # Retorna saída
        return processo.stdout.strip()
        
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout ao executar script: {script}")
        raise ToolError(f"Timeout ao executar script: {script}")
    except Exception as e:
        logger.error(f"Erro ao executar script: {str(e)}")
        raise ToolError(f"Erro ao executar script: {str(e)}")

def executar_pip(
    comando: str,
    timeout: Optional[int] = 30,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> str:
    """
    Executa um comando pip.
    
    Args:
        comando: Comando pip
        timeout: Timeout em segundos
        cwd: Diretório de trabalho
        env: Variáveis de ambiente
        
    Returns:
        Saída do comando
    """
    try:
        # Prepara comando
        comando_completo = f"pip {comando}"
        
        # Executa comando
        return executar_comando(
            comando=comando_completo,
            shell=True,
            timeout=timeout,
            cwd=cwd,
            env=env
        )
        
    except Exception as e:
        logger.error(f"Erro ao executar pip: {str(e)}")
        raise ToolError(f"Erro ao executar pip: {str(e)}") 