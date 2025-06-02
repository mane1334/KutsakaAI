from agenteia.core.agente import AgenteIA, AgenteError
from agenteia.core.config import CONFIG # Assuming load_theme might be part of config or another module
# from agenteia.core.utils.theme_loader import load_theme # Example if theme loader is separate
from agenteia.logs import setup_logging
import logging

# Setup logging (adjust as needed)
# setup_logging() # Call this early if not handled by other imports
logger = logging.getLogger(__name__)

def main():
    print("Iniciando AgenteIA...")
    try:
        agente = AgenteIA()
        print("AgenteIA pronto. Digite 'sair' para terminar.")
        
        # Exemplo de como carregar um tema, se você tiver essa funcionalidade
        # theme_name = CONFIG['interface']['theme']
        # theme_config = load_theme(theme_name) # You'd need to ensure load_theme is imported
        # print(f"Tema '{theme_name}' carregado.")

        while True:
            mensagem_usuario = input("Você: ")
            if mensagem_usuario.lower() == 'sair':
                print("Encerrando AgenteIA.")
                break
            
            try:
                # Para resposta normal:
                resposta_agente = agente.processar_mensagem(mensagem_usuario)
                print(f"Agente: {resposta_agente}")

                # Para resposta em stream (descomente e comente a linha acima se quiser usar):
                # print("Agente: ", end="", flush=True)
                # for chunk in agente.processar_mensagem_stream(mensagem_usuario):
                #     print(chunk, end="", flush=True)
                # print() # Nova linha após o stream

            except AgenteError as e:
                logger.error(f"Erro do AgenteIA: {e}")
                print(f"Erro: {e}")
            except Exception as e:
                logger.error(f"Ocorreu um erro inesperado: {e}", exc_info=True)
                print("Ocorreu um erro inesperado. Verifique os logs.")

    except AgenteError as e:
        logger.critical(f"Falha ao inicializar o AgenteIA: {e}")
        print(f"Falha crítica ao inicializar: {e}")
    except Exception as e:
        logger.critical(f"Falha desconhecida ao inicializar o AgenteIA: {e}", exc_info=True)
        print(f"Falha crítica desconhecida ao inicializar. Verifique os logs.")

if __name__ == "__main__":
    # Ensure logging is configured. 
    # If your project's __init__.py or config.py already calls setup_logging, 
    # this might be redundant, but it's safer to ensure it's called.
    setup_logging(name='kutsaka_agent_cli') 
    main()
