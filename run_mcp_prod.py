"""
Script para executar o MCP Server em produção.
"""

import os
import sys
from pathlib import Path
import argparse
import uvicorn
import logging
from logging.handlers import RotatingFileHandler
import json

# Adicionar diretório raiz ao PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from agenteia.core.mcp.api import app

def configurar_logging(log_dir: str, log_level: str):
    """Configura o logging para produção."""
    # Criar diretório de logs
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar formato
    formato = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Handler para arquivo
    arquivo_handler = RotatingFileHandler(
        log_dir / "mcp.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    arquivo_handler.setFormatter(formato)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formato)
    
    # Configurar logger raiz
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.addHandler(arquivo_handler)
    logger.addHandler(console_handler)
    
def carregar_config(arquivo: str) -> dict:
    """Carrega configurações do arquivo."""
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar configurações: {e}")
        return {}

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Iniciar MCP Server em produção")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Caminho para arquivo de configuração"
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        help="Diretório para arquivos de log"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Nível de log"
    )
    
    args = parser.parse_args()
    
    # Carregar configurações
    config = carregar_config(args.config)
    if not config:
        sys.exit(1)
        
    # Configurar logging
    configurar_logging(args.log_dir, args.log_level)
    logger = logging.getLogger(__name__)
    
    # Obter configurações do servidor
    mcp_config = config.get("mcp", {})
    api_config = mcp_config.get("api", {})
    
    host = api_config.get("host", "0.0.0.0")
    porta = api_config.get("porta", 8000)
    
    # Configurar workers
    workers = mcp_config.get("workers", 4)
    
    logger.info(f"Iniciando MCP Server em produção")
    logger.info(f"Host: {host}")
    logger.info(f"Porta: {porta}")
    logger.info(f"Workers: {workers}")
    logger.info(f"Log level: {args.log_level}")
    
    # Iniciar servidor
    uvicorn.run(
        "agenteia.core.mcp.api:app",
        host=host,
        port=porta,
        workers=workers,
        log_level=args.log_level,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
    
if __name__ == "__main__":
    main() 