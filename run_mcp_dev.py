"""
Script para iniciar o MCP Server em modo de desenvolvimento.
"""

import os
import sys
from pathlib import Path
import argparse
import uvicorn
import logging

# Adicionar diretório raiz ao PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from agenteia.core.mcp.api import app

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Iniciar MCP Server em modo de desenvolvimento")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host para o servidor (padrão: 127.0.0.1)"
    )
    parser.add_argument(
        "--porta",
        type=int,
        default=8000,
        help="Porta para o servidor (padrão: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Habilitar auto-reload"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="debug",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Nível de log (padrão: debug)"
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    print(f"Iniciando MCP Server em modo de desenvolvimento")
    print(f"Host: {args.host}")
    print(f"Porta: {args.porta}")
    print(f"Auto-reload: {args.reload}")
    print(f"Log level: {args.log_level}")
    print("\nDocumentação disponível em:")
    print(f"http://{args.host}:{args.porta}/docs")
    print(f"http://{args.host}:{args.porta}/redoc")
    
    # Iniciar servidor
    uvicorn.run(
        "agenteia.core.mcp.api:app",
        host=args.host,
        port=args.porta,
        reload=args.reload,
        log_level=args.log_level
    )
    
if __name__ == "__main__":
    main() 