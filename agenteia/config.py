"""
Configurações do Agente IA
Centraliza todas as configurações do sistema em um único arquivo
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# Configuração inicial de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """Configuração do modelo de linguagem."""
    url: str = "http://localhost:11434"
    endpoint: str = "/api/chat"
    model: str = "qwen3:1.7b"
    temperature: float = 0.7
    top_p: float = 0.95
    max_tokens: int = 4000
    timeout: int = 3000
    max_retries: int = 3
    streaming: bool = True

@dataclass
class SecurityConfig:
    """Configurações de segurança."""
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    request_timeout: int = 30
    allowed_commands: List[str] = None
    allowed_extensions: List[str] = None
    allowed_dirs: List[str] = None

    def __post_init__(self):
        if self.allowed_commands is None:
            self.allowed_commands = ["python", "pip", "git", "ls", "dir", "echo"]
        if self.allowed_extensions is None:
            self.allowed_extensions = [
    # Arquivos de texto
    '.txt', '.md', '.log', '.csv', '.json', '.xml', '.yaml', '.yml',
    # Arquivos de código
    '.py', '.js', '.html', '.css', '.php', '.java', '.cpp', '.c', '.h',
    '.ts', '.jsx', '.tsx', '.vue', '.svelte',
    # Arquivos de configuração
    '.env', '.ini', '.conf', '.config',
    # Documentos
    '.docx', '.xlsx', '.pptx', '.pdf',
    # Imagens
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
    # Outros
    '.zip', '.rar', '.7z', '.tar', '.gz'
]
        if self.allowed_dirs is None:
            self.allowed_dirs = [
                str(Path.cwd()),  # Diretório do projeto
                str(Path.home()),  # Diretório home do usuário
                str(Path.home() / "Desktop"),  # Desktop
                str(Path.home() / "Documents"),  # Documentos
                str(Path.home() / "Downloads"),  # Downloads
                "C:\\",  # Raiz do C:
                str(Path.home() / "Desktop" / "ai"),  # Diretório do projeto
            ]

@dataclass
class LoggingConfig:
    """Configurações de logging."""
    log_file: str = "logs/agente.log"
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class UIConfig:
    """Configurações da interface do usuário."""
    tema_escuro: bool = True
    tamanho_fonte: int = 16
    mostrar_sidebar: bool = True
    mostrar_ferramentas: bool = True
    idioma: str = "pt_BR"
    modo_compacto: bool = False

@dataclass
class AgentConfig:
    """Configurações do agente."""
    verbose: bool = True
    max_iterations: int = 3
    handle_parsing_errors: bool = True
    historico_dir: str = "historico"
    temp_dir: str = "temp"
    default_code_output_dir: str = str(Path.home() / "AgenteIA_Projetos")
    mostrar_historico: bool = True
    auto_salvar_historico: bool = True
    max_historico_mensagens: int = 100

# Configurações padrão
DEFAULT_CONFIG = {
    "llm": {
        "provider": "ollama",
        "model": "qwen3:1.7b",
        "url": "http://localhost:11434",
        "temperature": 0.7,
        "top_p": 0.9
    },
    "rag": {
        "enabled": True,
        "k_retrieval": 3,
        "similarity_threshold": 0.7,
        "embedding_model": "qwen3:1.7b",
        "vector_db_dir": "vector_db",
        "chunking": {
            "chunk_size": 1000,
            "chunk_overlap": 200
        }
    },
    "agent": {
        "max_iterations": 3,
        "early_stopping": True,
        "historico_dir": "historico",
        "temp_dir": "temp",
        "default_code_output_dir": "projetos"
    },
    "auto_improve": {
        "enabled": True,
        "min_tool_calls": 5,
        "tool_failure_threshold": 0.3,
        "index_feedback": True
    },
    "logging": {
        "level": "INFO",
        "file": "agenteia.log",
        "max_size": 10485760,
        "backup_count": 5
    },
    "posthog": {
        "enabled": False,
        "api_key": "",
        "host": "https://app.posthog.com"
    },
    "openrouter": {
        "enabled": False,
        "api_key": "",
        "api_base": "https://openrouter.ai/api/v1",
        "modelo_coder": "qwen/qwen-2.5-coder-32b-instruct:free",
        "timeout": 60
    },
    "ollama": {
        "base_url": "http://localhost:11434",
        "timeout": 120
    },
    "available_models": {
        "geral": ["qwen3:1.7b", "qwen2.5-coder-3b-instruct"],
        "coder": ["qwen2.5-coder-3b-instruct", "qwen3:1.7b"],
        "assistente": ["qwen3:1.7b"]
    }
}

# Carregar configurações do arquivo JSON
CONFIG_PATH = Path(__file__).parent / "config.json"

def carregar_config() -> Dict[str, Any]:
    """Carrega as configurações do arquivo JSON."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning(f"Arquivo de configuração não encontrado em {CONFIG_PATH}. Usando configurações padrão.")
            return DEFAULT_CONFIG.copy()
            
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            
        # Mesclar com configurações padrão
        merged_config = DEFAULT_CONFIG.copy()
        for key, value in config.items():
            if isinstance(value, dict) and key in merged_config:
                merged_config[key].update(value)
            else:
                merged_config[key] = value
                
        return merged_config
        
    except Exception as e:
        logger.error(f"Erro ao carregar configurações: {e}")
        return DEFAULT_CONFIG.copy()

# Carregar configurações
CONFIG = carregar_config()

# Configurar variáveis de ambiente
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = CONFIG.get("langchain", {}).get("api_key", "")
os.environ["LANGCHAIN_PROJECT"] = CONFIG.get("langchain", {}).get("project", "agenteia")

# Configurar PostHog se habilitado
if CONFIG.get("posthog", {}).get("enabled", False):
    os.environ["POSTHOG_API_KEY"] = CONFIG["posthog"]["api_key"]
    os.environ["POSTHOG_HOST"] = CONFIG["posthog"]["host"]

def salvar_config(config_file: str = None) -> bool:
    """Salva configurações em um arquivo JSON."""
    try:
        if config_file is None:
            config_file = CONFIG_PATH
            
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(CONFIG, f, indent=4, ensure_ascii=False)
        logger.info(f"Configurações salvas em {config_file}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar configurações: {e}")
        return False

def reset_config() -> bool:
    """Restaura as configurações para os valores padrão."""
    try:
        global CONFIG
        CONFIG = DEFAULT_CONFIG.copy()
        logger.info("Configurações restauradas para valores padrão")
        return salvar_config()
    except Exception as e:
        logger.error(f"Erro ao restaurar configurações: {e}")
        return False

def validar_configuracoes() -> bool:
    """Valida todas as configurações do sistema."""
    try:
        # Criar diretórios necessários
        for dir_path in [
            CONFIG["agent"]["historico_dir"],
            CONFIG["agent"]["temp_dir"],
            CONFIG["agent"]["default_code_output_dir"],
            CONFIG["rag"]["vector_db_dir"]
        ]:
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Diretório {dir_path} verificado/criado")

        # Validar configurações do LLM
        if not CONFIG["llm"]["url"]:
            raise ValueError("URL do LLM é obrigatória")

        # Validar modelos disponíveis
        if not CONFIG["available_models"]["geral"] or not CONFIG["available_models"]["coder"]:
            raise ValueError("Lista de modelos não pode estar vazia")

        logger.info("Todas as configurações validadas com sucesso")
        return True

    except Exception as e:
        logger.error(f"Erro ao validar configurações: {e}")
        raise

# Validar configurações ao importar
validar_configuracoes()
