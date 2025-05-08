"""
Agente IA - Assistente Virtual Inteligente
Versão 1.0.0
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from ferramentas import ferramentas
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

def get_func_name(func):
    """Obtém o nome original da função, mesmo se decorada ou for um objeto tool."""
    # Caso seja um objeto tool do LangChain
    if hasattr(func, "func"):
        return get_func_name(func.func)
    # Caso seja decorada (lru_cache, wraps, etc)
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return getattr(func, "__name__", None)

class ContextoManager:
    def __init__(self, max_mensagens: int = 100):
        self.max_mensagens = max_mensagens
        self.historico = []

    def adicionar_mensagem(self, tipo: str, conteudo: str):
        self.historico.append({
            'tipo': tipo,
            'mensagem': conteudo,
            'timestamp': datetime.now().isoformat()
        })
        if len(self.historico) > self.max_mensagens:
            self.historico.pop(0)

    def obter_historico(self):
        return self.historico

    def limpar_historico(self):
        self.historico = []

class AgenteIA:
    def __init__(self):
        self.contexto_manager = ContextoManager()
        self.ferramentas = ferramentas
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.prompt = self._criar_prompt()
        self.llm_geral = ChatOpenAI(
            base_url="http://172.20.10.9:1234/v1",
            api_key="qwen3-4b",
            model="lmstudio-community/Qwen3-4B-GGUF",
            temperature=config.LLM_TEMPERATURE,
        )
        self.llm_coder = ChatOpenAI(
            base_url="http://172.20.10.9:1234/v1",
            api_key="qwen2.5-coder-3b-instruct",
            model="qwen2.5-coder-3b-instruct",
            temperature=config.LLM_TEMPERATURE,
        )
        self.agent_geral = create_tool_calling_agent(self.llm_geral, self.ferramentas, self.prompt)
        self.agent_coder = create_tool_calling_agent(self.llm_coder, self.ferramentas, self.prompt)
        self.agent_executor_geral = AgentExecutor(
            agent=self.agent_geral,
            tools=self.ferramentas,
            verbose=config.AGENT_VERBOSE,
            memory=self.memory
        )
        self.agent_executor_coder = AgentExecutor(
            agent=self.agent_coder,
            tools=self.ferramentas,
            verbose=config.AGENT_VERBOSE,
            memory=self.memory
        )
        logger.info("Agente IA inicializado com sucesso (LM Studio - multi-modelo)")

    def _criar_prompt(self) -> ChatPromptTemplate:
        """Cria o template do prompt para o agente."""
        return ChatPromptTemplate.from_messages([
            ("system", """Você é um assistente virtual inteligente, educado e objetivo.
Responda sempre em português, de forma clara e amigável.
Nunca mostre raciocínio interno, apenas a resposta final ao usuário.
Se a mensagem for apenas um cumprimento, responda de forma simpática e breve.
Se o usuário pedir uma ação, use as ferramentas disponíveis.

**Responda DIRETAMENTE (sem usar ferramentas) quando o pedido for:**
- Perguntas de conhecimento geral que VOCÊ JÁ SABE A RESPOSTA
- Geração de texto criativo (histórias, poemas, etc.)
- Resumos de texto (se o texto for fornecido na conversa)
- Geração de código APENAS como texto na resposta
- Conversas informais

**Use as FERRAMENTAS DISPONÍVEIS quando o pedido exigir:**
- Uma INTERAÇÃO com o sistema operacional ou aplicativos
- BUSCAR INFORMAÇÕES ATUAIS ou DADOS que você não possui internamente
- REALIZAR CÁLCULOS MATEMÁTICOS
- MANIPULAR ARQUIVOS E DIRETÓRIOS
- CRIAR, LER ou EDITAR arquivos Word, Excel, PowerPoint e arquivos de código
- GERAR E SALVAR códigos-fonte em arquivos
- CRIAR ESTRUTURAS DE PASTAS para projetos

**Para criar projetos estruturados, SEMPRE use a ferramenta criar_estrutura_pastas:**
1. Primeiro, analise o pedido do usuário para entender a estrutura necessária
2. Crie um dicionário com a estrutura completa do projeto
3. Use a ferramenta criar_estrutura_pastas com o caminho base e a estrutura
4. Verifique se a estrutura foi criada corretamente

Use as ferramentas com responsabilidade e segurança.
Se o pedido for ambíguo, tente interpretar a intenção mais provável do usuário.
Lembre-se das conversas anteriores para contexto."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def _escolher_executor(self, mensagem: str):
        termos_codigo = ['código', 'programa', 'python', 'script', 'função', 'classe', 'método', 'comando', 'terminal', 'algoritmo', 'bug', 'erro', 'debug', 'compilar', 'executar']
        if any(t in mensagem.lower() for t in termos_codigo):
            return self.agent_executor_coder
        return self.agent_executor_geral

    def processar_mensagem(self, mensagem: str, mostrar_raciocinio: bool = False) -> str:
        try:
            self.contexto_manager.adicionar_mensagem('usuario', mensagem)
            executor = self._escolher_executor(mensagem)
            result = executor.invoke({"input": mensagem})
            resposta = result.get('output', str(result))
            if mostrar_raciocinio:
                resposta = f"<think>{result.get('intermediate_steps', [])}</think>\n{resposta}"
            self.contexto_manager.adicionar_mensagem('agente', resposta)
            
            # Salva o histórico automaticamente após cada interação
            try:
                self.salvar_historico()
            except Exception as e:
                logger.error(f"Erro ao salvar histórico automático: {str(e)}")
            
            logger.info(f"Mensagem processada com sucesso: {mensagem[:50]}...")
            return resposta
        except Exception as e:
            erro = f"Erro ao processar mensagem: {str(e)}"
            logger.error(erro)
            return erro

    def usar_ferramenta(self, nome_ferramenta: str, **kwargs) -> str:
        """
        Usa uma ferramenta específica do agente.
        """
        try:
            nomes = [get_func_name(f) for f in self.ferramentas]
            logger.info(f"Ferramentas disponíveis: {nomes}")
            ferramenta = None
            for f in self.ferramentas:
                nome = get_func_name(f)
                if nome == nome_ferramenta:
                    ferramenta = f
                    break
            if not ferramenta:
                raise ValueError(f"Ferramenta '{nome_ferramenta}' não encontrada")
            resultado = ferramenta(**kwargs)
            logger.info(f"Ferramenta '{nome_ferramenta}' executada com sucesso")
            return resultado
        except Exception as e:
            erro = f"Erro ao usar ferramenta '{nome_ferramenta}': {str(e)}"
            logger.error(erro)
            return erro
            
    def limpar_historico(self):
        """Limpa o histórico de mensagens do agente."""
        self.contexto_manager.limpar_historico()
        self.memory.clear()
        logger.info("Histórico limpo com sucesso")
        
    def salvar_historico(self, caminho: str = None):
        """
        Salva o histórico de mensagens em um arquivo JSON.
        
        Args:
            caminho (str, optional): Caminho do arquivo para salvar o histórico.
                                   Se não fornecido, será gerado automaticamente com timestamp.
        """
        try:
            if caminho is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                caminho = os.path.join('historico', f'historico_{timestamp}.json')
            
            # Garante que o diretório existe
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(self.contexto_manager.obter_historico(), f, ensure_ascii=False, indent=2)
                
            logger.info(f"Histórico salvo com sucesso em '{caminho}'")
            
        except Exception as e:
            erro = f"Erro ao salvar histórico: {str(e)}"
            logger.error(erro)
            return erro
            
    def carregar_historico(self, caminho: str = None):
        """
        Carrega o histórico de mensagens de um arquivo JSON.
        
        Args:
            caminho (str, optional): Caminho do arquivo para carregar o histórico.
                                   Se não fornecido, carrega o arquivo mais recente do diretório historico.
        """
        try:
            if caminho is None:
                # Lista todos os arquivos de histórico
                arquivos = [f for f in os.listdir('historico') if f.startswith('historico_') and f.endswith('.json')]
                if not arquivos:
                    logger.warning("Nenhum arquivo de histórico encontrado")
                    return
                
                # Pega o arquivo mais recente
                arquivo_mais_recente = max(arquivos, key=lambda x: os.path.getctime(os.path.join('historico', x)))
                caminho = os.path.join('historico', arquivo_mais_recente)
            
            if os.path.exists(caminho):
                with open(caminho, 'r', encoding='utf-8') as f:
                    self.contexto_manager.historico = json.load(f)
                    
                logger.info(f"Histórico carregado com sucesso de '{caminho}'")
                
        except Exception as e:
            erro = f"Erro ao carregar histórico: {str(e)}"
            logger.error(erro)
            return erro

    def listar_historicos(self) -> List[str]:
        """
        Lista todos os arquivos de histórico disponíveis.
        
        Returns:
            List[str]: Lista com os nomes dos arquivos de histórico
        """
        try:
            if not os.path.exists('historico'):
                return []
            
            arquivos = [f for f in os.listdir('historico') if f.startswith('historico_') and f.endswith('.json')]
            arquivos.sort(reverse=True)  # Ordena do mais recente para o mais antigo
            return arquivos
        except Exception as e:
            logger.error(f"Erro ao listar históricos: {str(e)}")
            return []
