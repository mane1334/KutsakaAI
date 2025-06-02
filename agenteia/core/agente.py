"""
Classe principal do Agente IA
"""

import logging
from typing import Dict, List, Optional, Any, Callable, Generator, Tuple
from pathlib import Path
import json
from datetime import datetime
import requests
import os
import shutil
import re
import time
from enum import Enum
import glob # Importar glob
from collections import defaultdict # Importar defaultdict
import uuid # Importar uuid

from langchain.agents import AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.tools import BaseTool, Tool, StructuredTool
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain_ollama import ChatOllama
from langchain.agents import AgentType, initialize_agent
from langchain.agents import create_tool_calling_agent
from duckduckgo_search import DDGS
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain.memory import ConversationBufferMemory
from langchain_openai.embeddings import OpenAIEmbeddings

from .config import CONFIG, validar_configuracoes, obter_perfil
from .exceptions import AgenteError
from .ferramentas import get_available_tools
from ..logs import setup_logging
from .gerenciador_modelos import GerenciadorModelos

# Importar componentes para RAG
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# Importar loaders e splitters para documentos
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configuração de logging
logger = setup_logging(__name__)

class ProvedorModelo(Enum):
    """Enum para os provedores de modelo disponíveis."""
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"

class AgenteCallbackHandler(BaseCallbackHandler):
    """Handler de callbacks personalizado para o agente."""
    
    def __init__(self, on_progress_update: Optional[Callable] = None):
        """Inicializa o handler com callbacks opcionais."""
        self.tokens = []
        self.current_chain = None
        self.on_progress_update = on_progress_update
        self.tool_log_file = None
        self._initialize_tool_log()
        
    def _initialize_tool_log(self):
        """Inicializa o arquivo de log de uso de ferramentas."""
        try:
            log_dir = Path(CONFIG["agent"]["historico_dir"]) / "tool_logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file_path = log_dir / f"tool_usage_{timestamp}.jsonl"
            self.tool_log_file = open(log_file_path, "a", encoding="utf-8")
            logger.info(f"Arquivo de log de ferramentas inicializado em {log_file_path}")
        except Exception as e:
            logger.error(f"Erro ao inicializar arquivo de log de ferramentas: {e}")
            self.tool_log_file = None # Garantir que é None se houver erro
        
    def _log_tool_event(self, event_type: str, data: Dict[str, Any]):
        """Escreve um evento de ferramenta no arquivo de log."""
        if self.tool_log_file:
            try:
                log_entry = {"timestamp": datetime.now().isoformat(), "event_type": event_type, **data}
                json.dump(log_entry, self.tool_log_file, ensure_ascii=False)
                self.tool_log_file.write('\n') # JSON Lines format
                self.tool_log_file.flush() # Garantir que o evento seja escrito imediatamente
            except Exception as e:
                logger.error(f"Erro ao escrever no arquivo de log de ferramentas: {e}")
        
    def __del__(self):
        """Garante que o arquivo de log de ferramentas seja fechado."""
        if self.tool_log_file and not self.tool_log_file.closed:
            try:
                self.tool_log_file.close()
                logger.info("Arquivo de log de ferramentas fechado.")
            except Exception as e:
                logger.error(f"Erro ao fechar arquivo de log de ferramentas: {e}")
        
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """Chamado quando o LLM inicia."""
        model_name = serialized.get("name", "LLM")
        logger.debug(f"{model_name} iniciado com prompts: {prompts}")
        if self.on_progress_update:
            self.on_progress_update(60, f"Processando com {model_name}...")
        
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Chamado quando o LLM termina."""
        logger.debug(f"LLM finalizado com resposta: {response}")
        
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Chamado quando ocorre erro no LLM."""
        logger.error(f"Erro no LLM: {error}")
        
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        """Chamado quando uma chain inicia."""
        if serialized:
            self.current_chain = serialized.get("name", "unknown")
        else:
            self.current_chain = "unknown_serialized_was_none"
            logger.warning("'serialized' parameter was None in on_chain_start")
        logger.debug(f"Chain {self.current_chain} iniciada com inputs: {inputs}")
        
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Chamado quando uma chain termina."""
        logger.debug(f"Chain {self.current_chain} finalizada com outputs: {outputs}")
        self.current_chain = None
        
    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Chamado quando ocorre erro em uma chain."""
        logger.error(f"Erro na chain {self.current_chain}: {error}")
        
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """Chamado quando uma ferramenta inicia."""
        tool_name = serialized.get('name', 'unknown')
        self.current_tool_name = tool_name # Armazenar o nome da ferramenta atual
        logger.debug(f"Ferramenta {tool_name} iniciada com input: {input_str}")
        if self.on_progress_update:
            self.on_progress_update(30, f"Iniciando ferramenta: {tool_name}...")
        self._log_tool_event("tool_start", {"tool_name": tool_name, "input": input_str})
        
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Chamado quando uma ferramenta termina."""
        tool_name = getattr(self, 'current_tool_name', 'unknown') # Recuperar o nome da ferramenta
        logger.debug(f"Ferramenta {tool_name} finalizada com output: {output}")
        # TODO: Registrar o sucesso da ferramenta 'tool_name' com output 'output'
        if self.on_progress_update:
            self.on_progress_update(50, f"Ferramenta {tool_name} concluída. Continuando processamento...")
        self._log_tool_event("tool_end", {"tool_name": tool_name, "output": output})
        
    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Chamado quando ocorre erro em uma ferramenta."""
        tool_name = getattr(self, 'current_tool_name', 'unknown') # Recuperar o nome da ferramenta
        logger.error(f"Erro na ferramenta {tool_name}: {error}")
        # TODO: Registrar o erro da ferramenta 'tool_name' com erro 'error'
        if self.on_progress_update:
            self.on_progress_update(50, f"Ferramenta {tool_name} falhou.")
        self._log_tool_event("tool_error", {"tool_name": tool_name, "error": str(error)})

class AgenteIA:
    """Classe principal do Agente IA."""
    
    @staticmethod
    def _verificar_modelos_disponiveis() -> List[str]:
        """Verifica quais modelos estão disponíveis no Ollama local."""
        try:
            response = requests.get(f"{CONFIG['ollama']['base_url']}/api/tags", timeout=5)  # Adicionado timeout de 5 segundos
            response.raise_for_status()  # Levanta HTTPError para respostas ruins (4xx ou 5xx)
            modelos = response.json().get('models', [])
            return [modelo['name'] for modelo in modelos]
        except requests.exceptions.Timeout:
            logger.error(f"Timeout ao tentar conectar com Ollama em {CONFIG['ollama']['base_url']}/api/tags")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de requisição ao verificar modelos Ollama: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado ao verificar modelos Ollama disponíveis: {e}")
            return []

    def _detectar_necessidade_codigo(self, mensagem: str) -> bool:
        """Detecta se a mensagem indica uma tarefa de programação."""
        palavras_chave_codigo = [
            "código", "programa", "site", "web", "html", "css", "javascript",
            "python", "java", "c++", "c#", "php", "ruby", "go", "rust",
            "desenvolver", "criar site", "aplicação", "app", "api",
            "frontend", "backend", "database", "banco de dados", "jogo",
            "snake", "game", "desenvolvimento", "programação", "criar",
            "gerar", "escrever", "código", "script", "py", ".py"
        ]
        # Verificar se alguma palavra-chave está na mensagem (case-insensitive)
        mensagem_lower = mensagem.lower()
        usar_coder = any(palavra.lower() in mensagem_lower for palavra in palavras_chave_codigo)
        if usar_coder:
            logger.info("Detectada tarefa de programação, usando modelo coder.")
        return usar_coder
    
    def _detectar_tipo_interacao(self, mensagem: str) -> str:
        """
        Detecta se a mensagem é uma conversa casual ou uma tarefa que requer ferramentas.
        
        Returns:
            str: 'chat' para conversa casual, 'task' para tarefa que requer ferramentas
        """
        # Palavras-chave que indicam conversa casual
        palavras_chave_chat = [
            "oi", "olá", "tudo bem", "como vai", "bom dia", "boa tarde", "boa noite",
            "obrigado", "obrigada", "valeu", "tchau", "até logo", "até mais",
            "sim", "não", "ok", "beleza", "legal", "ótimo", "excelente"
        ]
        
        # Palavras-chave que indicam tarefa
        palavras_chave_task = [
            "criar", "fazer", "desenvolver", "programar", "escrever", "ler",
            "buscar", "encontrar", "pesquisar", "procurar", "listar", "mostrar",
            "copiar", "mover", "deletar", "remover", "executar", "rodar",
            "converter", "transformar", "gerar", "produzir", "construir"
        ]
        
        # Palavras-chave para perguntas sobre as próprias ferramentas
        palavras_chave_ferramentas = [
            "quais ferramentas", "ferramentas disponiveis", "que ferramentas você tem",
            "lista de ferramentas"
        ]
        
        mensagem_lower = mensagem.lower()
        
        # Verifica se é uma conversa casual
        if any(palavra in mensagem_lower for palavra in palavras_chave_chat):
            return 'chat'
            
        # Verifica se a mensagem é uma pergunta sobre as ferramentas
        if any(frase in mensagem_lower for frase in palavras_chave_ferramentas):
            self.logger.info("Detectada pergunta sobre ferramentas, usando modo chat.")
            return 'chat'
            
        # Verifica se é uma tarefa
        if any(palavra in mensagem_lower for palavra in palavras_chave_task):
            return 'task'
            
        # Se não encontrar palavras-chave específicas, verifica o tamanho e estrutura
        if len(mensagem.split()) <= 5 and not any(c in mensagem for c in ['?', '!', '.']):
            return 'chat'
            
        return 'task'

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        mcp_client: Optional[Any] = None,
        usar_openrouter: bool = False,
        verboso: bool = False,
        on_progress_start: Optional[Callable] = None,
        on_progress_update: Optional[Callable] = None,
        on_progress_end: Optional[Callable] = None
    ):
        """Inicializa o agente com validação completa."""
        try:
            # Configuração inicial
            self.config = config or CONFIG
            self.logger = setup_logging(__name__)
            self.mcp_client = mcp_client
            self.usar_openrouter = usar_openrouter
            self.verboso = verboso if verboso is not None else self.config.get("agent", {}).get("verbose", False)
            self.on_progress_start = on_progress_start
            self.on_progress_update = on_progress_update
            self.on_progress_end = on_progress_end
            
            # Inicializar histórico e memória Langchain
            self.historico = [] # Inicializa o histórico como uma lista vazia
            self._setup_memory()
            
            # Configurar Embeddings e Vector Store para RAG
            self._setup_embeddings()
            self._setup_vector_store()
            
            # Carregar os modelos (Ollama para execução, OpenRouter para código)
            self.llm_executor, self.llm_coder = self._carregar_modelos()
            
            # Inicializar ferramentas
            # TODO: Decidir se o agente coder terá um subconjunto de ferramentas ou usará o executor para todas as ações de ferramenta.
            # Por enquanto, o agente executor terá todas as ferramentas.
            all_tools = self.configurar_ferramentas() # Assumindo que configurar_ferramentas retorna todas as ferramentas
            self.ferramentas_executor = all_tools # Ferramentas para o modelo executor
            # self.ferramentas_coder = [] # Se houver ferramentas específicas para o coder

            # Configurar o agente executor principal
            # Este agente usará o modelo local e as ferramentas para a maioria das tarefas.
            self.agente_executor = self.configurar_agente(self.llm_executor, self.ferramentas_executor, "Agente Executor")

            # O agente coder não precisa ser um AgentExecutor se apenas gerar código. Pode ser apenas a instância do LLM.
            # self.agente_coder = self.configurar_agente(self.llm_coder, self.ferramentas_coder, "Agente Coder") # Se o coder precisar de ferramentas
            # Se o coder só gerar código, usamos self.llm_coder diretamente.
            # self.llm_coder já está definido após _carregar_modelos()
            
            # Registrar agente no MCP Server se o cliente estiver disponível
            if self.mcp_client:
                self.logger.info(f"Registrando AgenteIA no MCP Server...")
                # Registrar o agente executor principal
                self.mcp_client.registrar_agente(
                    nome="Agente Executor", # Nome atualizado
                    especialidades=["execução de tarefas locais", "manipulação de arquivos", "uso de ferramentas"],
                    status="ativo"
                )
                # Se o agente coder for um agente separado no MCP, registrar também.
            
            self.logger.info("AgenteIA inicializado com sucesso!")
            self.logger.info(f"Status 'enabled' do OpenRouter na configuração do AgenteIA: {self.config.get('openrouter', {}).get('enabled', 'Chave não encontrada')}") # Log para verificar o status do OpenRouter
            
            # Rehidratar memória
            self._rehidratar_memoria()
            
            # Carregar e analisar logs de uso de ferramentas para auto-aperfeiçoamento
            self.tool_performance_metrics = self._load_and_analyze_tool_logs()
            
            # Verificar status inicial dos provedores
            self.ollama_status = self._verificar_modelos_disponiveis()
            self.openrouter_status = self._check_openrouter_status()
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar AgenteIA: {e}")
            raise AgenteError(f"Falha ao inicializar agente: {e}")

    def _setup_memory(self):
        """Configura a memória do agente."""
        try:
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            logger.info("Memória Langchain configurada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao configurar memória: {e}")
            raise AgenteError(f"Falha ao configurar memória: {str(e)}")

    def _setup_embeddings(self):
        """Configura os embeddings para RAG."""
        try:
            if CONFIG["openrouter"]["enabled"]:
                self.embeddings = OpenAIEmbeddings(
                    openai_api_base=CONFIG["openrouter"]["api_base"],
                    openai_api_key=CONFIG["openrouter"]["api_key"],
                    model=CONFIG["rag"]["embedding_model"]
                )
            else:
                self.embeddings = OllamaEmbeddings(
                    model=CONFIG["rag"]["embedding_model"],
                    base_url=CONFIG["ollama"]["base_url"]
                )
            logger.info(f"Embeddings configurados com modelo: {CONFIG['rag']['embedding_model']}")
        except Exception as e:
            logger.error(f"Erro ao configurar embeddings: {e}")
            raise AgenteError(f"Falha ao configurar embeddings: {str(e)}")

    def _setup_vector_store(self):
        """Configura o banco de dados vetorial para RAG."""
        try:
            vector_db_dir = CONFIG["rag"]["vector_db_dir"]
            self.vector_store = Chroma(
                persist_directory=vector_db_dir,
                embedding_function=self.embeddings
            )
            logger.info(f"Vector Store configurado em: {vector_db_dir}")
        except Exception as e:
            logger.error(f"Erro ao configurar Vector Store: {e}")
            raise AgenteError(f"Falha ao configurar Vector Store: {str(e)}")

    def _carregar_modelos(self) -> Tuple[Any, Any]:
        """Carrega e inicializa os modelos LLM (Executor - Ollama, Coder - OpenRouter)."""
        llm_executor = None
        llm_coder = None

        # 1. Carregar Modelo Executor (Ollama)
        try:
            ollama_config = self.config.get("llm", {})
            ollama_model_name = self.config.get("modelo", {}).get("nome", "qwen3:1.7b") # Usar nome do modelo do config
            ollama_base_url = ollama_config.get("url", "http://localhost:11434")
            ollama_timeout = ollama_config.get("timeout", 120)
            
            llm_executor = ChatOllama(
                model=ollama_model_name,
                base_url=ollama_base_url,
                timeout=ollama_timeout,
                temperature=ollama_config.get("temperature", 0.7), # Carregar temperatura e outros do config Ollama
                top_p=ollama_config.get("top_p", 0.9),
                # outros parâmetros conforme ChatOllama suporta
            )
            self.logger.info(f"Modelo Executor (Ollama: {ollama_model_name}) carregado com sucesso.")

        except Exception as e:
            self.logger.error(f"Erro ao carregar Modelo Executor (Ollama): {e}")
            # Dependendo da importância, pode levantar exceção aqui ou continuar sem o modelo executor.
            # Por enquanto, vamos registrar o erro e continuar (llm_executor será None)

        # 2. Carregar Modelo Coder (OpenRouter)
        try:
            self.logger.info(f"Configuração do OpenRouter sendo lida: {self.config.get('openrouter')}") # Adicionar log aqui
            openrouter_config = self.config.get("openrouter", {})
            openrouter_enabled = openrouter_config.get("enabled", False)
            openrouter_api_key = openrouter_config.get("api_key", os.getenv("OPENROUTER_API_KEY"))
            openrouter_model_name = openrouter_config.get("modelo_coder", "qwen/qwen-2.5-coder-32b-instruct:free") # Usar modelo_coder
            openrouter_base_url = openrouter_config.get("api_base", "https://openrouter.ai/api/v1") # Usar api_base
            openrouter_timeout = openrouter_config.get("timeout", 60)
            openrouter_headers = openrouter_config.get("headers") # Carregar headers

            if not openrouter_enabled:
                self.logger.info("OpenRouter desabilitado nas configurações.")
                llm_coder = None # Modelo coder será None se desabilitado
            elif not openrouter_api_key:
                self.logger.warning("API Key do OpenRouter não encontrada nas configurações ou variáveis de ambiente. Modelo Coder não será carregado.")
                llm_coder = None
            else:
                # Usar ChatOpenAI (compatível com OpenRouter) ou sua customização ChatOpenRouter
                # Se ChatOpenRouter customizada for necessária para bind_tools, usá-la.
                # Assumindo que ChatOpenAI base funciona com OpenRouter.
                llm_coder = ChatOpenAI(
                    model=openrouter_model_name, # Passar o nome do modelo
                    api_key=openrouter_api_key,
                    base_url=openrouter_base_url,
                    timeout=openrouter_timeout,
                    temperature=openrouter_config.get("temperature", 0.3), # Carregar temperatura do config OpenRouter
                    # Passar headers customizados se suportado pela base_url/API
                    # model_kwargs={"headers": openrouter_headers} # Pode ser necessário passar headers via model_kwargs
                    # Nota: ChatOpenAI pode não ter um parâmetro 'headers' direto. Verify API docs.
                    # Se headers forem cruciais e ChatOpenAI não suportar, sua classe ChatOpenRouter customizada será necessária.
                    # Pelo search result anterior, ChatOpenRouter customizada aceita 'headers'. Vamos usar a customizada se ela existir e for adequada.
                    # Se a customizada for 'ChatOpenRouter', usar essa classe.
                    # if 'ChatOpenRouter' in globals(): # Verificar se a classe customizada existe
                    #    llm_coder = ChatOpenRouter(...
                    # else:
                    #    llm_coder = ChatOpenAI(...
                    # Para simplicidade agora, vamos usar ChatOpenAI e assumir compatibilidade ou que headers não são estritamente necessários na inicialização.


                )
                self.logger.info(f"Modelo Coder (OpenRouter: {openrouter_model_name}) carregado com sucesso.")
                
        except Exception as e:
            self.logger.error(f"Erro ao carregar Modelo Coder (OpenRouter): {e}")
            llm_coder = None

        return llm_executor, llm_coder

    def _load_and_analyze_tool_logs(self) -> Dict[str, Any]:
        """Carrega e analisa os logs de uso de ferramentas para auto-aperfeiçoamento."""
        tool_stats = defaultdict(lambda: {"total_calls": 0, "successful_calls": 0, "failed_calls": 0})
        
        try:
            log_dir = Path(CONFIG["agent"]["historico_dir"]) / "tool_logs"
            if not log_dir.exists():
                logger.warning(f"Diretório de logs de ferramentas não encontrado: {log_dir}")
                return tool_stats

            # Carregar todos os arquivos de log
            log_files = glob.glob(str(log_dir / "tool_usage_*.jsonl"))
            for log_file in log_files:
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                event = json.loads(line.strip())
                                tool_name = event.get("tool_name")
                                if not tool_name:
                                    continue

                                if event["event_type"] == "tool_start":
                                    tool_stats[tool_name]["total_calls"] += 1
                                elif event["event_type"] == "tool_end":
                                    tool_stats[tool_name]["successful_calls"] += 1
                                elif event["event_type"] == "tool_error":
                                    tool_stats[tool_name]["failed_calls"] += 1

                            except json.JSONDecodeError as e:
                                logger.error(f"Erro ao decodificar linha do log: {e}")
                                continue

                except Exception as e:
                    logger.error(f"Erro ao processar arquivo de log {log_file}: {e}")
                    continue

            # Calcular taxas de sucesso e falha
            for tool_name, stats in tool_stats.items():
                if stats["total_calls"] >= CONFIG["auto_improve"]["min_tool_calls"]:
                    stats["success_rate"] = stats["successful_calls"] / stats["total_calls"]
                    stats["failure_rate"] = stats["failed_calls"] / stats["total_calls"]
                else:
                    stats["success_rate"] = 1.0  # Assume 100% de sucesso se não houver chamadas suficientes
                    stats["failure_rate"] = 0.0

            return dict(tool_stats)

        except Exception as e:
            logger.error(f"Erro ao analisar logs de ferramentas: {e}")
            return tool_stats

    def _check_openrouter_status(self) -> Dict[str, Any]:
        """Verifica o status da API do OpenRouter fazendo uma requisição simples."""
        status = {
            "online": False,
            "message": "API Key ou URL não configurada.",
            "model_count": 0
        }
        try:
            openrouter_config = self.config.get("openrouter", {})
            openrouter_enabled = openrouter_config.get("enabled", False)
            openrouter_api_key = openrouter_config.get("api_key", os.getenv("OPENROUTER_API_KEY"))
            openrouter_base_url = openrouter_config.get("api_base", "https://openrouter.ai/api/v1")

            if not openrouter_enabled:
                status["message"] = "OpenRouter desabilitado na configuração."
                return status

            if not openrouter_api_key:
                 status["message"] = "API Key do OpenRouter não configurada."
                 return status

            if not openrouter_base_url:
                 status["message"] = "URL base do OpenRouter não configurada."
                 return status

            # Tentar fazer uma requisição simples, como listar modelos
            models_endpoint = f"{openrouter_base_url}/models"
            headers = {
                "Authorization": f"Bearer {openrouter_api_key}"
            }
            # Incluir headers customizados se configurados
            custom_headers = openrouter_config.get("headers")
            if custom_headers:
                 headers.update(custom_headers)

            response = requests.get(models_endpoint, headers=headers, timeout=10)
            response.raise_for_status() # Levanta um erro para status codes 4xx/5xx

            models_data = response.json()
            model_count = len(models_data.get("data", []))

            status["online"] = True
            status["message"] = f"API acessível. {model_count} modelos disponíveis."
            status["model_count"] = model_count

        except requests.exceptions.Timeout:
            status["message"] = "Timeout ao conectar com a API do OpenRouter."
        except requests.exceptions.RequestException as e:
            status["message"] = f"Erro de requisição da API do OpenRouter: {e}"
        except Exception as e:
            status["message"] = f"Erro inesperado ao verificar status do OpenRouter: {e}"

        self.logger.info(f"Status do OpenRouter: {status}")
        return status

    def _load_documents(self, paths: List[str]) -> List[Any]:
        """Carrega documentos dos caminhos especificados."""
        documents = []
        for path in paths:
            try:
                if os.path.exists(path):
                    loader = TextLoader(path)
                    documents.extend(loader.load())
                else:
                    logger.warning(f"Documento não encontrado: {path}")
            except Exception as e:
                logger.error(f"Erro ao carregar documento {path}: {e}")
        return documents

    def _chunk_documents(self, documents: List[Any]) -> List[Any]:
        """Divide os documentos em chunks usando as configurações do RAG."""
        try:
            chunk_size = CONFIG["rag"]["chunking"]["chunk_size"]
            chunk_overlap = CONFIG["rag"]["chunking"]["chunk_overlap"]
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            return text_splitter.split_documents(documents)
        except Exception as e:
            logger.error(f"Erro ao dividir documentos em chunks: {e}")
            return documents

    def _index_documents(self, paths: List[str]):
        """Indexa documentos usando as configurações do RAG."""
        try:
            # Carregar e dividir documentos
            documents = self._load_documents(paths)
            chunks = self._chunk_documents(documents)
            
            # Criar ou carregar o banco de dados vetorial
            vector_db_dir = CONFIG["rag"]["vector_db_dir"]
            self.vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=vector_db_dir
            )
            logger.info(f"Documentos indexados com sucesso em {vector_db_dir}")
            
        except Exception as e:
            logger.error(f"Erro ao indexar documentos: {e}")
            raise AgenteError(f"Falha ao indexar documentos: {str(e)}")

    async def processar_mensagem(self, mensagem: str, usar_coder: bool = None, perfil: str = None) -> str:
        """Processa uma mensagem usando o modelo e ferramentas configuradas."""
        try:
            # Verificar se a mensagem é válida
            if not mensagem or not isinstance(mensagem, str):
                self.logger.error("Mensagem inválida recebida.")
                return "Erro: Mensagem inválida."

            # Verificar se RAG está habilitado e recuperar documentos relevantes
            documentos_relevantes = []
            if CONFIG["rag"]["enabled"] and self.vector_store:
                try:
                    documentos_relevantes = self.vector_store.similarity_search(
                        mensagem,
                        k=CONFIG["rag"]["k_retrieval"]
                    )
                    self.logger.info(f"Recuperados {len(documentos_relevantes)} documentos relevantes")
                except Exception as e:
                    self.logger.error(f"Erro ao recuperar documentos relevantes: {e}")

            # Verificar ferramentas com alta taxa de falha
            ferramentas_disponiveis = self.ferramentas_executor.copy()
            if CONFIG["auto_improve"]["enabled"]:
                tool_stats = self._load_and_analyze_tool_logs()
                for tool_name, stats in tool_stats.items():
                    if (stats["total_calls"] >= CONFIG["auto_improve"]["min_tool_calls"] and
                        stats["failure_rate"] > CONFIG["auto_improve"]["tool_failure_threshold"]):
                        if tool_name in ferramentas_disponiveis:
                            self.logger.warning(f"Ferramenta {tool_name} removida por alta taxa de falha: {stats['failure_rate']:.2%}")
                            ferramentas_disponiveis.pop(tool_name)

            # Configurar o modelo e perfil
            modelo, modelo_coder = self._carregar_modelos()
            modelo_atual = modelo_coder if usar_coder else modelo
            
            # Configurar o perfil
            perfil_config = obter_perfil(perfil) if perfil else None
            
            # Preparar o prompt com documentos relevantes se disponíveis
            prompt = mensagem
            if documentos_relevantes:
                context = "\n".join([doc.page_content for doc in documentos_relevantes])
                prompt = f"Contexto relevante:\n{context}\n\nPergunta: {mensagem}"

            # Processar a mensagem
            response = await modelo_atual.ainvoke(prompt)
            
            # Criar mensagens com IDs únicos
            user_message = {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": mensagem,
                "timestamp": datetime.now().isoformat()
            }
            
            assistant_message = {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            }
            
            # Adicionar mensagens ao histórico
            self.historico.append(user_message)
            self.historico.append(assistant_message)
            
            # Indexar feedback se configurado
            if CONFIG["auto_improve"]["index_feedback"]:
                self._add_message_to_vector_store(user_message)
                self._add_message_to_vector_store(assistant_message)

            return response

        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem: {e}")
            raise AgenteError(f"Falha ao processar mensagem: {str(e)}")

    def processar_mensagem_stream(self, mensagem: str, usar_coder: bool = None, perfil: str = None) -> Generator[str, None, None]:
        """
        Processa uma mensagem do usuário com streaming de tokens, aplicando RAG e lógica de seleção de modelo.

        Args:
            mensagem: Mensagem do usuário.
            usar_coder: Se deve usar o modelo coder (None para detecção automática).
            perfil: O nome do perfil selecionado (atualmente não usado diretamente aqui, mas pode ser para futuras parametrizações).

        Yields:
            Tokens da resposta do agente.
        """
        self.logger.info(f"Iniciando processar_mensagem_stream para: '{mensagem[:50]}...'")

        # 1. Determinar Target LLM
        if usar_coder is None:
            usar_coder = self._detectar_necessidade_codigo(mensagem)
            self.logger.info(f"Detecção de necessidade de código: {usar_coder}")

        selected_llm = None
        if usar_coder and self.llm_coder:
            selected_llm = self.llm_coder
            self.logger.info("Usando llm_coder para streaming.")
        elif self.llm_executor:
            selected_llm = self.llm_executor
            self.logger.info("Usando llm_executor para streaming.")

        if selected_llm is None:
            error_msg = "Nenhum modelo LLM disponível para processar a mensagem."
            self.logger.error(error_msg)
            yield f"❌ Erro: {error_msg}"
            return

        # 2. Preparar Prompt com RAG (if enabled)
        final_prompt = mensagem
        if CONFIG["rag"]["enabled"] and self.vector_store:
            try:
                self.logger.debug("RAG ativado. Buscando documentos relevantes...")
                documentos_relevantes = self.vector_store.similarity_search(
                    mensagem,
                    k=CONFIG["rag"]["k_retrieval"]
                )
                if documentos_relevantes:
                    context = "\n".join([doc.page_content for doc in documentos_relevantes])
                    final_prompt = f"Contexto relevante:\n{context}\n\nPergunta: {mensagem}"
                    self.logger.info(f"RAG: {len(documentos_relevantes)} documentos relevantes adicionados ao prompt.")
                else:
                    self.logger.info("RAG: Nenhum documento relevante encontrado.")
            except Exception as e:
                self.logger.error(f"Erro ao recuperar documentos relevantes do RAG: {e}")
                # Continuar sem RAG em caso de erro, mas logar.

        # 3. Stream LLM Response
        full_response_content = []
        try:
            self.logger.debug(f"Iniciando streaming do LLM com o prompt: {final_prompt[:100]}...")
            for chunk in selected_llm.stream(final_prompt):
                # A estrutura do chunk pode variar. Para Langchain LLMs, é geralmente um objeto AIMessageChunk.
                content_part = ""
                if hasattr(chunk, 'content'): # Comum para AIMessageChunk
                    content_part = chunk.content
                elif isinstance(chunk, str): # Alguns LLMs podem retornar strings diretamente
                    content_part = chunk
                else:
                    # Tentar converter para string como fallback, mas logar aviso
                    self.logger.warning(f"Chunk de tipo inesperado recebido: {type(chunk)}. Tentando converter para str.")
                    content_part = str(chunk)

                if content_part:
                    yield content_part
                    full_response_content.append(content_part)
            self.logger.info("Streaming do LLM concluído.")

        except Exception as e:
            error_msg = f"Erro durante o streaming da resposta do LLM: {e}"
            self.logger.error(error_msg)
            yield f"❌ Erro: {error_msg}"
            # Não atualizar histórico se o stream falhou no meio.
            return

        # 4. Update History (apenas se o stream foi bem-sucedido)
        final_assistant_response = "".join(full_response_content)
        if not final_assistant_response and not full_response_content: # Verifica se algo foi gerado
             self.logger.warning("Nenhum conteúdo foi gerado pelo LLM.")
             # Pode-se optar por não adicionar ao histórico ou adicionar uma mensagem de "sem resposta"
             # Por ora, não adicionaremos nada se a resposta for vazia.
             return

        user_message = {
            "id": str(uuid.uuid4()),
            "role": "user",
            "content": mensagem, # Mensagem original, não o final_prompt com RAG
            "timestamp": datetime.now().isoformat()
        }
        assistant_message = {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": final_assistant_response,
            "timestamp": datetime.now().isoformat()
        }

        self.historico.append(user_message)
        self.historico.append(assistant_message)
        self.logger.info("Histórico atualizado com a mensagem do usuário e a resposta do assistente.")

        if CONFIG["auto_improve"]["index_feedback"]:
            try:
                self._add_message_to_vector_store(user_message)
                self._add_message_to_vector_store(assistant_message)
                self.logger.info("Mensagens adicionadas ao vector store para auto-aperfeiçoamento.")
            except Exception as e:
                self.logger.error(f"Erro ao adicionar mensagens ao vector store: {e}")

        # Opcional: Salvar histórico automaticamente aqui, se desejado.
        # self.salvar_historico()
    
    def salvar_historico(self, arquivo: str = None) -> bool:
        """
        Salva o histórico de conversas.
        
        Args:
            arquivo: Nome do arquivo (opcional)
            
        Returns:
            True se salvou com sucesso
        """
        try:
            if arquivo is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                arquivo = f"historico_{timestamp}.json"
            
            # Garantir diretório
            arquivo = Path(self.config["agent"]["historico_dir"]) / arquivo
            arquivo.parent.mkdir(parents=True, exist_ok=True)
            
            # Salvar histórico
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(self.historico, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Histórico salvo em {arquivo}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar histórico: {e}")
            return False
    
    def carregar_historico(self, arquivo: str) -> bool:
        """
        Carrega o histórico de conversas.
        
        Args:
            arquivo: Nome do arquivo
            
        Returns:
            True se carregou com sucesso
        """
        try:
            arquivo = Path(self.config["agent"]["historico_dir"]) / arquivo
            
            if not arquivo.exists():
                self.logger.error(f"Arquivo de histórico não encontrado: {arquivo}")
                return False
            
            # Carregar histórico
            with open(arquivo, "r", encoding="utf-8") as f:
                self.historico = json.load(f)
            
            self.logger.info(f"Histórico carregado de {arquivo}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar histórico: {e}")
            return False
    
    def limpar_historico(self) -> None:
        """Limpa o histórico de conversas e a memória Langchain."""
        self.historico = []
        if self.memory:
            self.memory.clear()
        self.logger.info("Histórico limpo")
    
    def _rehidratar_memoria(self):
        """Popula a memória Langchain com o histórico do HistoricoManager."""
        self.memory.clear() # Limpa a memória antes de rehidratar
        for msg in self.historico:
            if msg.get("role") == "user":
                self.memory.chat_memory.add_user_message(msg.get("content", ""))
            elif msg.get("role") == "assistant":
                self.memory.chat_memory.add_ai_message(msg.get("content", ""))
            # Note: O ID e feedback não são adicionados à memória Langchain, apenas ao histórico interno.
            # A memória Langchain foca apenas no conteúdo da conversa para o contexto do LLM.
        self.logger.info(f"Memória Langchain reidratada com {len(self.historico)} mensagens.")

    def usar_ferramenta(self, nome: str, **kwargs) -> Any:
        """
        Usa uma ferramenta específica através do MCP Server.

        Args:
            nome: Nome da ferramenta
            **kwargs: Argumentos da ferramenta
        
        Returns:
            Resultado da ferramenta
        """
        try:
            self.logger.info(f"Solicitando execução da ferramenta '{nome}' via MCP Server com parâmetros: {kwargs}")
            
            # --- Início da Lógica de Evitar Ferramentas Falhas ---
            # Verificar as métricas de desempenho antes de usar a ferramenta
            tool_metrics = self.tool_performance_metrics.get(nome, {})
            failure_rate = tool_metrics.get("failure_rate", 0.0)
            total_calls = tool_metrics.get("total_calls", 0)
            
            # Definir thresholds (pode vir do config futuramente)
            failure_threshold = self.config.get("auto_improve", {}).get("tool_failure_threshold", 0.5) # Ex: 50% de falha
            min_calls_for_consideration = self.config.get("auto_improve", {}).get("min_tool_calls", 5) # Ex: Mínimo de 5 chamadas
            
            if total_calls >= min_calls_for_consideration and failure_rate > failure_threshold:
                self.logger.warning(f"Ferramenta '{nome}' evitada devido à alta taxa de falha ({failure_rate:.2%}) em {total_calls} chamadas.")
                # Retorna uma observação para o agente indicando que a ferramenta foi evitada
                # O agente precisará interpretar isso e tentar uma abordagem diferente
                return f"Observação: A ferramenta '{nome}' tem um histórico de alta falha ({failure_rate:.2%}) com {total_calls} chamadas anteriores. Por favor, considere usar uma ferramenta alternativa ou modificar sua abordagem para esta tarefa. Não tente usar a ferramenta '{nome}' novamente para esta solicitação."
            # --- Fim da Lógica de Evitar Ferramentas Falhas ---
            
            # A tarefa a ser distribuída é a execução da ferramenta com seus parâmetros
            # O MCP Server entenderá que esta tarefa é para executar uma ferramenta com o nome fornecido
            # Precisamos formatar a tarefa de forma que o servidor MCP consiga interpretar
            # Uma opção é enviar um dicionário com o nome da ferramenta e os parâmetros
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": nome,
                "parametros": kwargs
            }
            
            # Distribuir a tarefa de execução da ferramenta para o MCP Server
            # O MCP Server irá encontrar a ferramenta registrada e executá-la
            resultado = self.mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao), # Enviar o dicionário como uma string JSON
                agente_id="Agente Principal" # Opcional: especificar o agente que deve executar, ou deixar o servidor decidir
            )
            
            self.logger.info(f"Resultado da execução da ferramenta '{nome}' via MCP Server: {resultado}")
            return resultado.get("resultado", "Resultado vazio da ferramenta") # O resultado virá dentro do dicionário de resposta da tarefa
            
        except Exception as e:
            self.logger.error(f"Erro ao usar ferramenta {nome} via MCP Server: {e}")
            raise AgenteError(f"Falha ao usar ferramenta {nome} via MCP Server: {e}")

    def configurar_ferramentas(self):
        """Configura e retorna a lista de ferramentas do agente."""
        # Chamar a função que obtém as ferramentas disponíveis
        # Passamos self.mcp_client para ferramentas que precisam interagir com o servidor MCP
        # Retornamos as ferramentas de fallback para uso com modelos baseados em texto (REACT)
        ferramentas_nativas, ferramentas_fallback = get_available_tools(mcp_client=self.mcp_client)
        self.logger.info(f"Ferramentas configuradas: {len(ferramentas_fallback)} ferramentas de fallback disponíveis.")
        return ferramentas_fallback

    def configurar_agente(self, modelo, ferramentas: List[BaseTool], nome_agente: str):
        """Configura e retorna o agente Langchain com memória e ferramentas."""
        try:
            # Verificar se modelo e ferramentas são válidos
            if modelo is None:
                 self.logger.warning(f"Modelo não fornecido para configurar o agente {nome_agente}. Retornando None.")
                 return None
            if not isinstance(ferramentas, list) or not all(isinstance(f, BaseTool) for f in ferramentas):
                 self.logger.warning(f"Ferramentas inválidas fornecidas para configurar o agente {nome_agente}. Retornando None.")
                 return None

            # Criar o prompt do agente
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Você é um assistente IA útil. Use as ferramentas disponíveis para ajudar o usuário."),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            # Criar o agente usando LangGraph
            agente = create_tool_calling_agent(
                llm=modelo,
                tools=ferramentas,
                prompt=prompt
            )

            # Criar o executor do agente
            agente_executor = AgentExecutor(
                agent=agente,
                tools=ferramentas,
                memory=self.memory,
                verbose=self.verboso,
                handle_parsing_errors=True,
                max_iterations=self.config.get("agent", {}).get("max_iterations", 3),
                early_stopping_method="generate"
            )
            
            self.logger.info(f"Agente LangGraph '{nome_agente}' configurado com sucesso.")
            return agente_executor
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar agente LangGraph '{nome_agente}': {e}")
            raise AgenteError(f"Falha ao configurar agente '{nome_agente}': {e}") from e

    def alternar_provedor_modelo(self, usar_openrouter: bool):
        """
        Alterna o provedor de modelo entre Ollama (local) e OpenRouter (remoto) para ambos os modelos (geral e coder).
        Reconfigura o gerenciador de modelos conforme a escolha.
        """
        self.usar_openrouter = usar_openrouter
        if usar_openrouter:
            modelo_analise = self.config.get("openrouter", {}).get("modelo_geral")
            modelo_executor = self.config.get("openrouter", {}).get("modelo_coder")
        else:
            modelo_analise = None
            modelo_executor = self.config.get("llm", {}).model
        self.gerenciador_modelos = GerenciadorModelos(
            modelo_executor=modelo_executor or "qwen3:1.7b",
            modelo_analise=modelo_analise,
            mcp_client=self.mcp_client
        )

    def registrar_feedback_mensagem(self, message_id: str, feedback_tipo: str, feedback_texto: str = None):
        """
        Registra o feedback do usuário para uma mensagem específica do agente.
        
        Args:
            message_id: O ID único da mensagem do agente.
            feedback_tipo: O tipo de feedback (ex: "positivo", "negativo").
            feedback_texto: Texto de feedback adicional (opcional).
        """
        self.logger.info(f"Recebendo feedback para a mensagem {message_id}: Tipo={feedback_tipo}, Texto={feedback_texto}")
        
        # Verificar se o ID é válido
        if not message_id:
            self.logger.error("ID da mensagem não fornecido para registro de feedback.")
            return False
            
        # Verificar se o histórico existe
        if not self.historico:
            self.logger.warning("Histórico vazio. Não é possível registrar feedback.")
            return False
            
        # Log do histórico atual para debug
        self.logger.debug(f"Histórico atual: {json.dumps(self.historico, indent=2)}")
        
        # Encontrar a mensagem no histórico pelo ID
        mensagem_encontrada = None
        for msg in self.historico:
            msg_id = msg.get("id")
            self.logger.debug(f"Verificando mensagem com ID: {msg_id}")
            if msg_id == message_id and msg.get("role") == "assistant":
                mensagem_encontrada = msg
                break
        
        if mensagem_encontrada:
            # Adicionar/atualizar o campo feedback na mensagem
            mensagem_encontrada["feedback"] = {
                "tipo": feedback_tipo,
                "texto": feedback_texto,
                "timestamp": datetime.now().isoformat()
            }
            self.logger.info(f"Feedback registrado com sucesso para a mensagem {message_id}.")
            
            # Salvar o histórico automaticamente após o feedback
            try:
                self.salvar_historico()
                self.logger.info("Histórico salvo após registro de feedback.")
            except Exception as e:
                self.logger.error(f"Erro ao salvar histórico após feedback: {e}")
                
            return True
        else:
            self.logger.warning(f"Mensagem com ID {message_id} não encontrada no histórico ou não é uma mensagem do assistente.")
            return False

    def _add_message_to_vector_store(self, message: Dict[str, Any]):
         """Adiciona uma mensagem ao Vector Store para memória de longo prazo."""
         if not message or not isinstance(message, dict):
             self.logger.warning("Mensagem inválida recebida para adicionar ao Vector Store.")
             return
             
         if self.vector_store and self.embeddings:
             try:
                 # Verifica se a mensagem tem o conteúdo necessário
                 if not message.get('role') or not message.get('content'):
                     self.logger.warning("Mensagem sem role ou content. Ignorando.")
                     return
                     
                 # Cria um documento simples com o conteúdo da mensagem
                 document_content = f"{message.get('role').capitalize()}: {message.get('content', '')}"
                 metadata = {
                     "role": message.get('role'),
                     "timestamp": message.get('timestamp', datetime.now().isoformat()),
                     "message_id": message.get('id', str(uuid.uuid4())),
                     "feedback_tipo": message.get('feedback', {}).get('tipo') if message.get('feedback') else None
                 }
                 
                 # Adiciona o documento ao Vector Store
                 self.vector_store.add_texts(
                     texts=[document_content],
                     metadatas=[metadata],
                     ids=[metadata['message_id']]
                 )
                 self.logger.debug(f"Mensagem {metadata['message_id']} adicionada ao Vector Store.")
                 
                 # Salvar o Vector Store
                 try:
                     self.vector_store._collection.persist()
                     self.logger.debug("Vector Store persistido com sucesso.")
                 except Exception as e:
                     self.logger.warning(f"Não foi possível persistir o Vector Store: {e}")
                     
             except Exception as e:
                 self.logger.error(f"Erro ao adicionar mensagem ao Vector Store: {e}")
         else:
             self.logger.warning("Vector Store ou Embeddings não inicializados. Não foi possível adicionar mensagem.")

    def obter_status_agente(self) -> Dict[str, Any]:
        """Retorna o status atual do agente e seus provedores."""
        return {
            "ollama": {
                "online": bool(self.ollama_status), # True se houver modelos disponíveis
                "modelos_disponiveis": self.ollama_status,
                "loaded_model": self.llm_executor.model if self.llm_executor else "Não Carregado"
            },
            "openrouter": self.openrouter_status,
            "provedor_ativo": "openrouter" if self.usar_openrouter else "ollama",
            "loaded_coder_model": self.llm_coder.model if self.llm_coder else "Não Carregado", # Adicionar o modelo coder carregado
            # TODO: Adicionar outras métricas do agente se necessário (uso de memória interna, etc.)
        }