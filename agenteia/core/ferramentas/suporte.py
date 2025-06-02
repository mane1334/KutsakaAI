import logging
import traceback
import json
import time
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import os
import sys
import psutil
import platform
import socket
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

def gerar_log(mensagem: str, nivel: str = "INFO", contexto: Dict = None,
    mcp_client: Optional[Any] = None
) -> Dict:
    """Gera um log estruturado."""
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando gerar_log para MCP Server com mensagem: {mensagem}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "gerar_log",
                "parametros": {"mensagem": mensagem, "nivel": nivel, "contexto": contexto}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            # O resultado esperado para gerar_log é um dicionário com os detalhes do log gerado
            try:
                resultado_dict = json.loads(resultado.get("resultado", "{}"))
                return resultado_dict
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON do resultado do MCP Server para gerar_log: {e}")
                return {"erro": "Erro ao processar resultado do MCP Server", "detalhes": str(e)}

        # Lógica existente (fallback local)
        resultado = {
            "timestamp": datetime.now().isoformat(),
            "nivel": nivel.upper(),
            "mensagem": mensagem,
            "contexto": contexto or {},
            "sistema": {
                "plataforma": platform.platform(),
                "python": sys.version,
                "hostname": socket.gethostname(),
                "pid": os.getpid()
            }
        }
        
        # Adicionar stack trace se for erro
        if nivel.upper() in ["ERROR", "CRITICAL"]:
            resultado["stack_trace"] = traceback.format_exc()
        
        # Registrar log
        log_message = json.dumps(resultado)
        if nivel.upper() == "DEBUG":
            logger.debug(log_message)
        elif nivel.upper() == "INFO":
            logger.info(log_message)
        elif nivel.upper() == "WARNING":
            logger.warning(log_message)
        elif nivel.upper() == "ERROR":
            logger.error(log_message)
        elif nivel.upper() == "CRITICAL":
            logger.critical(log_message)
        
        return resultado
    except Exception as e:
        logger.error(f"Erro ao gerar log: {e}")
        raise

def analisar_erro(erro: Exception,
    mcp_client: Optional[Any] = None
) -> Dict:
    """Analisa um erro e retorna informações detalhadas."""
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info("Delegando analisar_erro para MCP Server")
            # Serializar a exceção pode ser complexo. Talvez enviar apenas o str(erro) e traceback?
            # Ou o MCP Server precisa de uma forma de receber exceções serializadas.
            # Por enquanto, vamos enviar uma representação simples.
            erro_serializado = {
                "tipo": type(erro).__name__,
                "mensagem": str(erro),
                "stack_trace": traceback.format_exc()
            }
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "analisar_erro",
                "parametros": {"erro": erro_serializado}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            # O resultado esperado é um dicionário com a análise do erro
            try:
                resultado_dict = json.loads(resultado.get("resultado", "{}"))
                return resultado_dict
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON do resultado do MCP Server para analisar_erro: {e}")
                return {"erro": "Erro ao processar resultado do MCP Server", "detalhes": str(e)}

        # Lógica existente (fallback local)
        resultado = {
            "tipo": type(erro).__name__,
            "mensagem": str(erro),
            "timestamp": datetime.now().isoformat(),
            "stack_trace": traceback.format_exc(),
            "contexto": {
                "sistema": {
                    "plataforma": platform.platform(),
                    "python": sys.version,
                    "hostname": socket.gethostname(),
                    "pid": os.getpid()
                },
                "memoria": {
                    "total": psutil.virtual_memory().total,
                    "disponivel": psutil.virtual_memory().available,
                    "percentual": psutil.virtual_memory().percent
                },
                "cpu": {
                    "percentual": psutil.cpu_percent(),
                    "nucleos": psutil.cpu_count()
                }
            }
        }
        
        # Adicionar informações específicas do erro
        if isinstance(erro, (ValueError, TypeError)):
            resultado["sugestoes"] = [
                "Verifique os tipos dos argumentos",
                "Confirme se os valores estão dentro dos limites esperados",
                "Valide os dados de entrada"
            ]
        elif isinstance(erro, (FileNotFoundError, PermissionError)):
            resultado["sugestoes"] = [
                "Verifique se o arquivo existe",
                "Confirme as permissões de acesso",
                "Valide o caminho do arquivo"
            ]
        elif isinstance(erro, (ConnectionError, TimeoutError)):
            resultado["sugestoes"] = [
                "Verifique a conexão com a rede",
                "Confirme se o servidor está online",
                "Aumente o timeout se necessário"
            ]
        
        return resultado
    except Exception as e:
        logger.error(f"Erro ao analisar erro: {e}")
        raise

def monitorar_sistema(
    mcp_client: Optional[Any] = None
) -> Dict:
    """Monitora o estado do sistema."""
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info("Delegando monitorar_sistema para MCP Server")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "monitorar_sistema",
                "parametros": {}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            # O resultado esperado é um dicionário com o estado do sistema
            try:
                resultado_dict = json.loads(resultado.get("resultado", "{}"))
                return resultado_dict
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON do resultado do MCP Server para monitorar_sistema: {e}")
                return {"erro": "Erro ao processar resultado do MCP Server", "detalhes": str(e)}

        # Lógica existente (fallback local)
        resultado = {
            "timestamp": datetime.now().isoformat(),
            "sistema": {
                "plataforma": platform.platform(),
                "python": sys.version,
                "hostname": socket.gethostname(),
                "pid": os.getpid()
            },
            "recursos": {
                "cpu": {
                    "percentual": psutil.cpu_percent(interval=1),
                    "nucleos": psutil.cpu_count(),
                    "frequencia": psutil.cpu_freq().current if psutil.cpu_freq() else None
                },
                "memoria": {
                    "total": psutil.virtual_memory().total,
                    "disponivel": psutil.virtual_memory().available,
                    "percentual": psutil.virtual_memory().percent
                },
                "disco": {
                    "total": psutil.disk_usage('/').total,
                    "livre": psutil.disk_usage('/').free,
                    "percentual": psutil.disk_usage('/').percent
                },
                "rede": {
                    "conexoes": len(psutil.net_connections()),
                    "interfaces": psutil.net_if_stats()
                }
            },
            "processos": []
        }
        
        # Listar processos
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                resultado["processos"].append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return resultado
    except Exception as e:
        logger.error(f"Erro ao monitorar sistema: {e}")
        raise

def verificar_saude(
    mcp_client: Optional[Any] = None
) -> Dict:
    """Verifica a saúde do sistema."""
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info("Delegando verificar_saude para MCP Server")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "verificar_saude",
                "parametros": {}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            # O resultado esperado é um dicionário com o status de saúde
            try:
                resultado_dict = json.loads(resultado.get("resultado", "{}"))
                return resultado_dict
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON do resultado do MCP Server para verificar_saude: {e}")
                return {"erro": "Erro ao processar resultado do MCP Server", "detalhes": str(e)}

        # Lógica existente (fallback local)
        resultado = {
            "timestamp": datetime.now().isoformat(),
            "status": "OK",
            "componentes": {},
            "alertas": []
        }
        
        # Verificar CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        resultado["componentes"]["cpu"] = {
            "status": "OK" if cpu_percent < 80 else "ALERTA",
            "valor": cpu_percent
        }
        if cpu_percent >= 80:
            resultado["alertas"].append(f"CPU com uso alto: {cpu_percent}%")
        
        # Verificar memória
        mem = psutil.virtual_memory()
        resultado["componentes"]["memoria"] = {
            "status": "OK" if mem.percent < 80 else "ALERTA",
            "valor": mem.percent
        }
        if mem.percent >= 80:
            resultado["alertas"].append(f"Memória com uso alto: {mem.percent}%")
        
        # Verificar disco
        disco = psutil.disk_usage('/')
        resultado["componentes"]["disco"] = {
            "status": "OK" if disco.percent < 80 else "ALERTA",
            "valor": disco.percent
        }
        if disco.percent >= 80:
            resultado["alertas"].append(f"Disco com uso alto: {disco.percent}%")
        
        # Verificar rede
        try:
            response = requests.get('http://www.google.com', timeout=5)
            resultado["componentes"]["rede"] = {
                "status": "OK",
                "valor": response.status_code
            }
        except:
            resultado["componentes"]["rede"] = {
                "status": "ERRO",
                "valor": None
            }
            resultado["alertas"].append("Sem conexão com a internet")
        
        # Atualizar status geral
        if any(comp["status"] == "ERRO" for comp in resultado["componentes"].values()):
            resultado["status"] = "ERRO"
        elif any(comp["status"] == "ALERTA" for comp in resultado["componentes"].values()):
            resultado["status"] = "ALERTA"
        
        return resultado
    except Exception as e:
        logger.error(f"Erro ao verificar saúde: {e}")
        raise

def limpar_recursos(
    mcp_client: Optional[Any] = None
) -> Dict:
    """Limpa recursos do sistema."""
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info("Delegando limpar_recursos para MCP Server")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "limpar_recursos",
                "parametros": {}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            # O resultado esperado é um dicionário com as ações e erros
            try:
                resultado_dict = json.loads(resultado.get("resultado", "{}"))
                return resultado_dict
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON do resultado do MCP Server para limpar_recursos: {e}")
                return {"erro": "Erro ao processar resultado do MCP Server", "detalhes": str(e)}

        # Lógica existente (fallback local)
        resultado = {
            "timestamp": datetime.now().isoformat(),
            "acoes": [],
            "erros": []
        }
        
        # Limpar arquivos temporários
        temp_dir = Path(os.getenv('TEMP', '/tmp'))
        try:
            for file in temp_dir.glob('*'):
                if file.is_file():
                    try:
                        file.unlink()
                        resultado["acoes"].append(f"Arquivo temporário removido: {file}")
                    except:
                        resultado["erros"].append(f"Erro ao remover arquivo: {file}")
        except Exception as e:
            resultado["erros"].append(f"Erro ao limpar diretório temporário: {str(e)}")
        
        # Limpar memória
        try:
            import gc
            gc.collect()
            resultado["acoes"].append("Coleta de lixo executada")
        except Exception as e:
            resultado["erros"].append(f"Erro ao limpar memória: {str(e)}")
        
        return resultado
    except Exception as e:
        logger.error(f"Erro ao limpar recursos: {e}")
        raise 