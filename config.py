"""
Configurações do Agente IA
Centraliza todas as configurações do sistema em um único arquivo
"""

import os
from typing import List

# --- Configurações do Agente ---
AGENT_VERBOSE = False  # Controla o modo verbose do AgentExecutor
LLM_TEMPERATURE = 0.7  # Temperatura para geração de texto
MAX_RETRIES = 3  # Número máximo de tentativas para operações

# --- Configurações de Segurança ---
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
REQUEST_TIMEOUT = 30  # segundos
ALLOWED_COMMANDS: List[str] = ['ls', 'dir', 'echo', 'notepad', 'calc', 'start']
ALLOWED_FILE_EXTENSIONS: List[str] = ['.txt', '.py', '.json', '.md']

# --- Configurações de Logging ---
LOG_FILE = "agente.log"
LOG_LEVEL = "INFO"  # Níveis: DEBUG, INFO, WARNING, ERROR, CRITICAL

# --- Configurações de Diretórios ---
TEMP_DIR = "temp"  # Diretório para arquivos temporários
LOGS_DIR = "logs"  # Diretório para arquivos de log

# --- Configurações do LLM ---
LLM_MODEL = "gpt-4-turbo-preview"  # Modelo padrão do LLM
LLM_API_KEY = os.getenv("OPENAI_API_KEY")  # Chave da API do OpenAI

# --- Configurações de Diretórios Permitidos ---
ALLOWED_DIRS = [
    os.getcwd(),  # Diretório do projeto
    "C:\\",  # Permite acesso à raiz do C:
    "C:\\Users\\Sr.Africano\\Desktop",  # Desktop do usuário
    "C:\\Users\\Sr.Africano\\Documents",  # Documentos do usuário
    "C:\\teste"  # Diretório de teste
]

# --- Configurações de Extensões Permitidas ---
ALLOWED_FILE_EXTENSIONS = [
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

def validar_configuracoes():
    """Valida as configurações do sistema."""
    # Validar diretórios
    for diretorio in [TEMP_DIR, LOGS_DIR]:
        if not os.path.exists(diretorio):
            os.makedirs(diretorio)
    
    # Remover a validação da chave da API!
    # if not LLM_API_KEY:
    #     raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
    
    # Validar extensões permitidas
    if not ALLOWED_FILE_EXTENSIONS:
        raise ValueError("ALLOWED_FILE_EXTENSIONS não pode estar vazio")
        
    # Validar comandos permitidos
    if not ALLOWED_COMMANDS:
        raise ValueError("ALLOWED_COMMANDS não pode estar vazio")
        
    # Validar limites
    if MAX_FILE_SIZE <= 0:
        raise ValueError("MAX_FILE_SIZE deve ser maior que zero")
        
    if REQUEST_TIMEOUT <= 0:
        raise ValueError("REQUEST_TIMEOUT deve ser maior que zero")
        
    if MAX_RETRIES <= 0:
        raise ValueError("MAX_RETRIES deve ser maior que zero")
