"""
Script para iniciar o MCP Server.
"""

import os
import sys
from pathlib import Path
import argparse

# Adicionar diretório raiz ao PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from agenteia.core.mcp.api import iniciar_servidor

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Iniciar MCP Server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host para o servidor (padrão: 0.0.0.0)"
    )
    parser.add_argument(
        "--porta",
        type=int,
        default=8000,
        help="Porta para o servidor (padrão: 8000)"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Caminho para arquivo de configuração"
    )
    
    args = parser.parse_args()
    
    # Configurar variáveis de ambiente
    if args.config:
        os.environ["MCP_CONFIG"] = args.config
        
    print(f"Iniciando MCP Server em {args.host}:{args.porta}")
    iniciar_servidor(host=args.host, porta=args.porta)
    
if __name__ == "__main__":
    main() 