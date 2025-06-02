"""
Arquivo principal para execução do Agente IA.
Suporta execução via CLI ou interface web.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

# Adicionar diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from agenteia.core.agente import AgenteIA
from agenteia.core.config import CONFIG, validar_configuracoes
from agenteia.logs import setup_logging

# Configuração de logging
logger = setup_logging(__name__)

def inicializar_agente() -> Optional[AgenteIA]:
    """
    Inicializa o agente com as configurações apropriadas.
    
    Returns:
        AgenteIA: Instância do agente ou None se houver erro
    """
    try:
        # Validar configurações
        validar_configuracoes()
        
        # Criar diretórios necessários
        for dir_path in [
            CONFIG['logging'].log_file.rsplit('/', 1)[0],
            CONFIG['agent'].historico_dir,
            CONFIG['agent'].temp_dir
        ]:
            os.makedirs(dir_path, exist_ok=True)
            
        # Inicializar o agente
        return AgenteIA()
        
    except Exception as e:
        logger.error(f"Erro ao inicializar agente: {e}")
        return None

def cli_loop(agente: AgenteIA) -> None:
    """
    Executa o loop de interação via linha de comando.
    
    Args:
        agente: Instância do agente
    """
    print("\n=== Agente IA - Assistente Virtual Inteligente ===")
    print("Digite 'sair' para encerrar ou 'limpar' para limpar o histórico.\n")
    
    while True:
        try:
            mensagem = input("\nVocê: ").strip()
            
            if mensagem.lower() == 'sair':
                print("\nEncerrando o agente...")
                break
                
            elif mensagem.lower() == 'limpar':
                agente.limpar_historico()
                print("Histórico limpo!")
                continue
                
            elif not mensagem:
                continue
                
            print("\nAgente: ", end='', flush=True)
            resposta = agente.processar_mensagem(mensagem)
            print(resposta)
            
        except KeyboardInterrupt:
            print("\n\nEncerrando o agente...")
            break
            
        except Exception as e:
            logger.error(f"Erro durante a interação: {e}")
            print(f"\nErro: {e}")
            continue

def iniciar_web(host: str = '0.0.0.0', port: int = 5000, debug: bool = False) -> None:
    """
    Inicia a interface web do agente.
    
    Args:
        host: Host para o servidor web
        port: Porta para o servidor web
        debug: Se deve executar em modo debug
    """
    try:
        from agenteia.web.app import app
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f"Erro ao iniciar interface web: {e}")
        sys.exit(1)

def main() -> None:
    """Função principal que processa argumentos e inicia o modo apropriado."""
    parser = argparse.ArgumentParser(description='Agente IA - Assistente Virtual Inteligente')
    
    parser.add_argument('--web', action='store_true', help='Iniciar em modo web')
    parser.add_argument('--host', default='0.0.0.0', help='Host para o servidor web')
    parser.add_argument('--port', type=int, default=5000, help='Porta para o servidor web')
    parser.add_argument('--debug', action='store_true', help='Executar em modo debug')
    
    args = parser.parse_args()
    
    try:
        if args.web:
            logger.info(f"Iniciando interface web em {args.host}:{args.port}")
            iniciar_web(args.host, args.port, args.debug)
        else:
            agente = inicializar_agente()
            if agente:
                cli_loop(agente)
            else:
                logger.error("Falha ao inicializar o agente")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)
    finally:
        print("\n=== Agente encerrado ===")

if __name__ == "__main__":
    main()