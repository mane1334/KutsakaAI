"""
Agente IA - Assistente Virtual Inteligente
Versão 1.0.0
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from ferramentas import ferramentas
from agenteia.core import gerenciador_gatilhos, TipoGatilho
import agenteia.config as config
from langchain_core.callbacks import BaseCallbackHandler
import re
from langchain.agents import create_openai_functions_agent
from langchain.tools import BaseTool
from langchain.llms import ChatOllama

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

class AgenteError(Exception):
    """Exceção personalizada para erros do agente."""
    pass

# ... (outras classes e funções permanecem iguais) ...

class AgenteIA:
    def __init__(self, modelo_geral="qwen3-4b", modelo_coder="qwen2.5-coder-3b-instruct"):
        """Inicializa o agente com os modelos especificados."""
        self.modelo_geral = modelo_geral
        self.modelo_coder = modelo_coder
        self.compreensao = CompreensaoMensagem()
        self.contexto_manager = ContextoManager()
        self.callback_manager = PensamentoCallback()
        
        # Configuração do sistema
        self.system_message = """Você é um assistente virtual inteligente que ajuda usuários com tarefas de programação e gerenciamento de arquivos.
        
Regras importantes:
1. SEMPRE responda em português
2. NUNCA use tags HTML ou markdown nas respostas
3. NUNCA use placeholders como {input} ou {output}
4. NUNCA use emojis ou caracteres especiais
5. Mantenha as respostas claras e diretas
6. Se não entender algo, peça mais detalhes
7. Use as ferramentas disponíveis quando apropriado
8. Mostre seu raciocínio antes de responder
9. Confirme a ação antes de executá-la

Ferramentas disponíveis:
- listar_arquivos: Lista arquivos em um diretório
- criar_estrutura_pastas: Cria uma estrutura de pastas
- criar_arquivo_codigo: Cria ou edita um arquivo de código
- executar_comando: Executa um comando no terminal

Lembre-se: Você é um assistente profissional e deve manter um tom amigável mas formal."""
        
        # Inicializa os executores
        self._inicializar_executores()
        
        logger.info(f"Agente inicializado com modelos {modelo_geral} e {modelo_coder}")

    def processar_mensagem(self, mensagem: str, mostrar_raciocinio: bool = True, 
                          temperatura: float = None, top_p: float = None, 
                          perfil: str = None) -> str:
        """Processa uma mensagem do usuário, permitindo comunicação entre os modelos geral e coder."""
        try:
            mensagem = mensagem.strip()
            if not mensagem:
                return "Por favor, digite algo para que eu possa ajudar."

            # Analisa a mensagem
            analise = self.compreensao.analisar_mensagem(mensagem)
            logger.info(f"Análise da mensagem: {analise}")

            self.contexto_manager.adicionar_mensagem('usuario', mensagem)

            # Se for uma solicitação de código ou programação
            if analise['intencao'] in ['editar', 'executar', 'criar'] or 'código' in mensagem.lower() or 'programa' in mensagem.lower():
                # 1. O modelo geral gera o contexto/explicação
                executor_geral = self._escolher_executor({'intencao': 'consulta'})
                template_vars_geral = {
                    "input": mensagem,
                    "chat_history": "",
                    "agent_scratchpad": []
                }
                callback_geral = PensamentoCallback()
                executor_geral.callbacks = [callback_geral]
                try:
                    result_geral = executor_geral.invoke(template_vars_geral)
                    explicacao = callback_geral.resposta_final or result_geral.get('output', str(result_geral))
                except Exception as e:
                    explicacao = f"[Erro ao gerar explicação geral: {str(e)}]"

                # 2. O modelo coder gera o código
                executor_coder = self._escolher_executor({'intencao': 'executar', 'parametros': {'código': True}})
                template_vars_coder = {
                    "input": mensagem,
                    "chat_history": "",
                    "agent_scratchpad": []
                }
                callback_coder = PensamentoCallback()
                executor_coder.callbacks = [callback_coder]
                try:
                    result_coder = executor_coder.invoke(template_vars_coder)
                    codigo = callback_coder.resposta_final or result_coder.get('output', str(result_coder))
                except Exception as e:
                    codigo = f"[Erro ao gerar código: {str(e)}]"

                resposta = f"{explicacao}\n\n---\n\nCódigo sugerido pelo modelo coder:\n\n{codigo}"
                self.contexto_manager.adicionar_mensagem('agente', resposta)
                try:
                    self.salvar_historico()
                except Exception as e:
                    logger.error(f"Erro ao salvar histórico: {str(e)}")
                return resposta

            # Caso contrário, segue o fluxo normal
            # Processa baseado na análise
            if analise['erro']:
                return analise['erro']
            
            # Se encontrou uma intenção com confiança razoável
            if analise['intencao'] and analise['confianca'] >= 0.3:
                # Escolhe o executor apropriado
                executor = self._escolher_executor(analise)
                
                # Prepara o histórico da conversa
                chat_history = "\n".join([
                    f"{'Usuário' if msg['tipo'] == 'usuario' else 'Assistente'}: {msg['mensagem']}"
                    for msg in self.contexto_manager.obter_historico()[-5:]  # Últimas 5 mensagens
                ])
                
                # Prepara as variáveis para o template
                template_vars = {
                    "input": mensagem,
                    "chat_history": chat_history,
                    "agent_scratchpad": []
                }
                
                # Cria e configura o callback
                callback = PensamentoCallback()
                executor.callbacks = [callback]
                
                # Executa o agente
                try:
                    result = executor.invoke(template_vars)
                    pensamentos = "".join(callback.pensamentos)
                    resposta = callback.resposta_final or result.get('output', str(result))
                    
                    # Limpa e formata a resposta
                    pensamentos = self._limpar_resposta(pensamentos)
                    resposta = self._limpar_resposta(resposta)
                    
                    # Verifica se a resposta está vazia
                    if not resposta or not resposta.strip():
                        resposta = "Desculpe, não consegui processar sua solicitação. Poderia reformular?"
                    
                    # Adiciona resposta ao histórico
                    resposta_completa = self._formatar_resposta(pensamentos, resposta, mostrar_raciocinio)
                    self.contexto_manager.adicionar_mensagem('agente', resposta_completa)
                    
                    # Salva o histórico
                    try:
                        self.salvar_historico()
                    except Exception as e:
                        logger.error(f"Erro ao salvar histórico: {str(e)}")
                    
                    return resposta_completa
                    
                except Exception as e:
                    logger.error(f"Erro ao processar mensagem: {str(e)}")
                    if "Input to ChatPromptTemplate is missing variables" in str(e):
                        return "Desculpe, ocorreu um erro interno. Por favor, tente novamente em alguns instantes."
                    return "Desculpe, ocorreu um erro ao processar sua mensagem. Poderia tentar novamente?"
            
            # Se não encontrou intenção ou confiança baixa
            if analise['intencao'] == 'saudacao':
                return "Olá! Como posso ajudar você hoje?"
            elif analise['intencao'] == 'ajuda':
                return self._gerar_mensagem_ajuda(analise['sugestoes'])
            else:
                return self._gerar_mensagem_confusao(analise['sugestoes'])
            
        except Exception as e:
            erro = f"Desculpe, ocorreu um erro. Por favor, tente novamente. Detalhes: {str(e)}"
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            return erro

    # ... (resto dos métodos permanecem iguais) ... 