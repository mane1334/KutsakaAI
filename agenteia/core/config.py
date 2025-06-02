"""
Configurações do Agente IA no estilo ChatGPT
"""

import os
import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ModeloConfig:
    """Configuração de um modelo de linguagem."""
    nome: str
    descricao: str
    max_tokens: int
    temperatura_padrao: float
    top_p_padrao: float
    frequencia_padrao: float
    presenca_padrao: float
    stop_padrao: Optional[List[str]] = None

@dataclass
class PerfilConfig:
    """Configuração de um perfil de conversa."""
    nome: str
    descricao: str
    instrucoes: str
    temperatura: float
    top_p: float
    frequencia: float
    presenca: float
    stop: Optional[List[str]] = None

# Modelos disponíveis
MODELOS = {
    "qwen3-4b": ModeloConfig(
        nome="Qwen3:4B",
        descricao="Modelo geral para conversas e tarefas diversas",
        max_tokens=4096,
        temperatura_padrao=0.7,
        top_p_padrao=0.9,
        frequencia_padrao=0.0,
        presenca_padrao=0.0,
        stop_padrao=None
    ),
    "qwen2.5-coder-3b-instruct": ModeloConfig(
        nome="Qwen2.5-Coder-3B-Instruct",
        descricao="Modelo especializado em programação e código",
        max_tokens=2048,
        temperatura_padrao=0.2,
        top_p_padrao=0.95,
        frequencia_padrao=0.0,
        presenca_padrao=0.0,
        stop_padrao=["```"]
    )
}

# Perfis de conversa
PERFIS = {
    "padrao": PerfilConfig(
        nome="Padrão",
        descricao="Perfil equilibrado para conversas gerais",
        instrucoes="Você é um assistente IA útil, honesto e conciso.",
        temperatura=0.7,
        top_p=0.9,
        frequencia=0.0,
        presenca=0.0
    ),
    "coder": PerfilConfig(
        nome="Programador",
        descricao="Perfil especializado em programação",
        instrucoes="""Você é um assistente de programação especializado. 
        Forneça código limpo, bem documentado e seguindo as melhores práticas.
        Explique suas decisões de código de forma clara e concisa.""",
        temperatura=0.2,
        top_p=0.95,
        frequencia=0.0,
        presenca=0.0,
        stop=["```"]
    ),
    "criativo": PerfilConfig(
        nome="Criativo",
        descricao="Perfil para respostas mais elaboradas e criativas",
        instrucoes="""Você é um assistente criativo e elaborado.
        Forneça respostas detalhadas e bem estruturadas.
        Use analogias e exemplos quando apropriado.""",
        temperatura=0.9,
        top_p=0.9,
        frequencia=0.1,
        presenca=0.1
    ),
    "preciso": PerfilConfig(
        nome="Preciso",
        descricao="Perfil para respostas diretas e precisas",
        instrucoes="""Você é um assistente direto e preciso.
        Forneça respostas concisas e objetivas.
        Foque em fatos e evite especulações.""",
        temperatura=0.3,
        top_p=0.9,
        frequencia=0.0,
        presenca=0.0
    )
}

# Configurações gerais
CONFIG = {
    "modelo": {
        "nome": "qwen3:1.7b",
        "coder": "qwen2.5-coder:3b",
        "temperature": 0.7,
        "top_p": 0.9,
        "timeout": 120,
        "max_tokens": 2048,
        "stop": ["Observation:", "Human:", "Assistant:"]
    },
    "ollama": {
        "base_url": "http://localhost:11434",
        "timeout": 120,
        "retries": 3,
        "retry_delay": 5,
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 2048
    },
    "agent": {
        "verbose": True,
        "max_iterations": 5,
        "handle_parsing_errors": True
    },
    "historico": {
        "max_mensagens": 10,
        "limpar_apos": 100
    },
    "ferramentas": {
        "timeout": 30,
        "retries": 3,
        "retry_delay": 5
    },
    "available_models": {
        "geral": [
            "qwen3:1.7b",
            "qwen3:0.6b",
            "qwen3:4b"
        ],
        "coder": [
            "qwen2.5-coder:3b"
        ]
    },
    "logging": {
        "nivel": os.getenv("AGENTEIA_LOG_LEVEL", "INFO"),
        "arquivo": os.getenv("AGENTEIA_LOG_FILE", "logs/agente.log"),
        "max_bytes": int(os.getenv("AGENTEIA_LOG_MAX_BYTES", "1048576")),  # 1MB
        "backup_count": int(os.getenv("AGENTEIA_LOG_BACKUP_COUNT", "5"))
    },
    "interface": {
        "tema": os.getenv("AGENTEIA_TEMA", "claro"),
        "idioma": os.getenv("AGENTEIA_IDIOMA", "pt_BR"),
        "timezone": os.getenv("AGENTEIA_TIMEZONE", "America/Sao_Paulo")
    },
    "openrouter": {
        "enabled": True,
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": "",  # Deve ser configurado pelo usuário
        "modelo_padrao": "anthropic/claude-3-opus-20240229",
        "timeout": 60,
        "max_tokens": 4096,
        "temperature": 0.3
    },
    "rag": {
        "enabled": True,
        "k_retrieval": 4,
        "embedding_model": "nomic-embed-text",
        "vector_db_dir": "historico/chroma_db",
        "chunking": {
            "chunk_size": 1000,
            "chunk_overlap": 200
        },
        "documents_to_index": [
            "README.md",
            "DOCS_TAREFAS.md"
        ]
    },
    "auto_improve": {
        "tool_failure_threshold": 0.5,
        "min_tool_calls": 5,
        "index_feedback": True
    }
}

# Funções auxiliares
def obter_modelo(nome: str) -> ModeloConfig:
    """Retorna a configuração de um modelo."""
    if nome not in MODELOS:
        raise ValueError(f"Modelo não encontrado: {nome}")
    return MODELOS[nome]

def obter_perfil(nome: str) -> PerfilConfig:
    """Retorna a configuração de um perfil."""
    if nome not in PERFIS:
        raise ValueError(f"Perfil não encontrado: {nome}")
    return PERFIS[nome]

def listar_modelos() -> Dict[str, str]:
    """Retorna dicionário com nome e descrição dos modelos."""
    return {nome: modelo.descricao for nome, modelo in MODELOS.items()}

def listar_perfis() -> Dict[str, str]:
    """Retorna dicionário com nome e descrição dos perfis."""
    return {nome: perfil.descricao for nome, perfil in PERFIS.items()}

def carregar_configuracao() -> Dict[str, Any]:
    """Carrega as configurações do arquivo config.json."""
    try:
        # Obter o diretório do arquivo atual (config.py)
        base_dir = Path(__file__).parent.parent # Ir para o diretório pai (agenteia/)
        config_path = base_dir / "config.json"

        print(f"[DEBUG PRINT] Tentando carregar configuração de: {config_path.absolute()}") # Adicionar print para depuração

        logger.info(f"Carregando configurações de {config_path.absolute()}")
        
        if not config_path.exists():
            logger.error(f"Arquivo de configuração não encontrado em {config_path.absolute()}")
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            logger.info(f"Configurações carregadas: {config.keys()}")
            logger.info(f"Conteúdo completo da configuração carregada: {config}")
            return config
            
    except Exception as e:
        logger.error(f"Erro ao carregar configurações: {e}")
        raise

# Carregar configurações
CONFIG = carregar_configuracao()

def validar_configuracoes(config: Dict[str, Any]) -> bool:
    """Valida as configurações carregadas."""
    try:
        # Verificar se todas as seções necessárias existem
        secoes_obrigatorias = ["llm", "openrouter", "security", "logging", "agent"]
        for secao in secoes_obrigatorias:
            if secao not in config:
                logger.error(f"Seção obrigatória não encontrada: {secao}")
                return False
        
        # Validar configurações do OpenRouter
        if "openrouter" in config:
            openrouter_config = config["openrouter"]
            logger.info(f"Validando configuração do OpenRouter: {openrouter_config}")
            campos_obrigatorios = ["api_key", "modelo_geral", "modelo_coder", "base_url", "headers"]
            for campo in campos_obrigatorios:
                if campo not in openrouter_config:
                    logger.error(f"Campo obrigatório do OpenRouter não encontrado: {campo}")
                    return False
        
        logger.info("Todas as configurações validadas com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao validar configurações: {e}")
        return False

# Validar configurações
if not validar_configuracoes(CONFIG):
    raise ValueError("Configurações inválidas") 