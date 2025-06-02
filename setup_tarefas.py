"""
Script de configuração para o sistema de gerenciamento de tarefas.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def verificar_instalacao(pacote):
    """Verifica se um pacote está instalado."""
    return importlib.util.find_spec(pacote) is not None

def instalar_pacote(pacote):
    """Instala um pacote usando pip."""
    print(f"Instalando {pacote}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])

def verificar_instalar_pacotes():
    """Verifica e instala pacotes necessários."""
    pacotes_necessarios = [
        'streamlit',
        'streamlit-option-menu',
        'pandas',
        'numpy',
        'matplotlib',
        'seaborn',
        'plotly',
        'gtts',
        'python-docx',
        'python-pptx',
        'openpyxl',
        'pyyaml',
        'requests',
        'python-multipart',
        'pydantic',
        'typing-extensions',
        'duckduckgo-search',
        'beautifulsoup4',
        'lxml',
        'html5lib',
        'tqdm',
        'python-dateutil',
        'pytz',
        'tzlocal',
        'pillow',
        'pyautogui',
        'pyperclip',
        'psutil',
        'pywin32',
        'python-dotenv',
        'colorama',
        'loguru',
        'tqdm',
        'pyyaml',
        'pytest',
        'pytest-cov',
        'black',
        'isort',
        'mypy',
        'pylint',
        'flake8',
        'pre-commit',
        'ipykernel',
        'jupyter',
        'jupyterlab',
        'notebook',
        'ipywidgets',
        'nbconvert',
        'nbformat',
        'jedi',
        'rope',
        'python-lsp-server',
        'python-lsp-jsonrpc',
        'python-lsp-black',
        'pyls-isort',
        'pylsp-mypy',
        'python-lsp-ruff',
        'pyls-flake8',
        'pyls-mypy',
        'python-lsp-black',
        'pyls-isort',
        'pylsp-mypy',
        'python-lsp-ruff',
        'pyls-flake8',
        'pyls-mypy',
        'python-lsp-black',
        'pyls-isort',
        'pylsp-mypy',
        'python-lsp-ruff',
        'pyls-flake8',
        'pyls-mypy',
    ]
    
    for pacote in pacotes_necessarios:
        if not verificar_instalacao(pacote.split('==')[0]):
            instalar_pacote(pacote)

def criar_estrutura_diretorios():
    """Cria a estrutura de diretórios necessária."""
    diretorios = [
        "dados",
        "logs",
        "cache",
        "templates",
        "static",
        "static/css",
        "static/js",
        "static/img",
        "uploads",
        "downloads",
        "config",
        "models",
        "scripts",
        "tests",
        "notebooks",
        "docs",
        "backups",
        "temp",
        "reports",
        "reports/figures",
        "reports/tables",
        "data/raw",
        "data/processed",
        "data/interim",
        "data/external",
        "src/data",
        "src/features",
        "src/models",
        "src/visualization",
        "src/utils",
    ]
    
    for diretorio in diretorios:
        try:
            os.makedirs(diretorio, exist_ok=True)
            print(f"Diretório criado: {diretorio}")
        except Exception as e:
            print(f"Erro ao criar diretório {diretorio}: {e}")

def criar_arquivos_configuracao():
    """Cria arquivos de configuração iniciais."""
    # Arquivo .env
    if not os.path.exists(".env"):
        with open(".env", "w", encoding="utf-8") as f:
            f.write("""# Configurações de ambiente

# Configurações do Ollama
OLLAMA_API_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=300

# Configurações de Log
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_MAX_SIZE=10  # MB
LOG_BACKUP_COUNT=5

# Configurações de Segurança
SECRET_KEY=chave_secreta_aqui
DEBUG=False

# Configurações de API (se aplicável)
API_KEY=sua_chave_aqui
API_BASE_URL=https://api.exemplo.com
""")
        print("Arquivo .env criado com sucesso!")
    
    # Arquivo .gitignore
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write("""# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
.env
.venv

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Dados
*.csv
*.xlsx
*.db
*.sqlite3

# Configurações
.env
config/secrets.yaml

# Arquivos temporários
*.tmp
*.bak
*.swp
*~

# Arquivos gerados
*.pyc
__pycache__/

# Streamlit
.streamlit/

# Jupyter Notebook
.ipynb_checkpoints

# VS Code
.vscode/

# Pycharm
.idea/

# MacOS
.DS_Store
""")
        print("Arquivo .gitignore criado com sucesso!")

def main():
    """Função principal de configuração."""
    print("=" * 50)
    print("Configuração do Sistema de Gerenciamento de Tarefas")
    print("=" * 50)
    
    # Criar estrutura de diretórios
    print("\nCriando estrutura de diretórios...")
    criar_estrutura_diretorios()
    
    # Verificar e instalar dependências
    print("\nVerificando dependências...")
    verificar_instalar_pacotes()
    
    # Criar arquivos de configuração
    print("\nCriando arquivos de configuração...")
    criar_arquivos_configuracao()
    
    print("\n" + "=" * 50)
    print("Configuração concluída com sucesso!")
    print("=" * 50)
    print("\nPara iniciar o sistema de gerenciamento de tarefas, execute:")
    print("  streamlit run tarefas.py")

if __name__ == "__main__":
    main()
