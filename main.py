"""
Arquivo principal para execução do Agente IA
"""

import os
import logging
from agente import AgenteIA
import config

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agente.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Função principal que executa o loop de interação com o usuário."""
    try:
        print("\n=== Agente IA - Assistente Virtual Inteligente ===")
        print("Digite 'sair' para encerrar ou 'limpar' para limpar o histórico.")
        
        # Validar configurações
        config.validar_configuracoes()
        
        # Inicializar o agente
        agente = AgenteIA()
        
        while True:
            try:
                mensagem = input("\nVocê: ").strip()
                if mensagem.lower() == 'sair':
                    print("\nEncerrando o agente...")
                    break
                elif mensagem.lower() == 'limpar':
                    agente.limpar_historico()
                    print("Histórico limpo com sucesso!")
                    continue
                elif not mensagem:
                    continue
                print("\nAgente: ", end='')
                resposta = agente.processar_mensagem(mensagem)
                print(resposta)
            except KeyboardInterrupt:
                print("\n\nEncerrando o agente...")
                break
            except Exception as e:
                logger.error(f"Erro durante a interação: {str(e)}")
                print(f"\nErro: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"Erro fatal: {str(e)}")
        print(f"\nErro fatal: {str(e)}")
    finally:
        print("\n=== Agente encerrado ===")

if __name__ == "__main__":
    main() 