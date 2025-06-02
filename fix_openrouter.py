"""
Script para corrigir problemas de compatibilidade com o OpenRouter
"""

import subprocess
import sys
from pathlib import Path
import os

def install_dependencies():
    """Instala as dependências necessárias."""
    print("Instalando dependências...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "openai", "langchain-openrouter"], check=True)
        print("Dependências instaladas com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao instalar dependências: {e}")
        return False

def main():
    """Função principal."""
    print("Iniciando correção do OpenRouter...")
    print(f"Python executável: {sys.executable}")
    print(f"Diretório atual: {os.getcwd()}")
    print(f"Ambiente virtual: {os.getenv('VIRTUAL_ENV', 'Não encontrado')}")
    
    # Instalar dependências
    if not install_dependencies():
        print("Falha ao instalar dependências. Abortando...")
        return False
    
    # Executar o patch
    patch_path = Path(__file__).parent / "patch_openrouter.py"
    if not patch_path.exists():
        print(f"Arquivo de patch não encontrado: {patch_path}")
        return False
        
    try:
        print(f"Executando patch: {patch_path}")
        result = subprocess.run([sys.executable, str(patch_path)], capture_output=True, text=True)
        print(f"Código de retorno: {result.returncode}")
        print("Saída padrão:")
        print(result.stdout)
        if result.stderr:
            print("Erro padrão:")
            print(result.stderr)
            
        if result.returncode == 0:
            print("Patch aplicado com sucesso!")
            return True
        else:
            print("Erro ao aplicar patch.")
            return False
            
    except Exception as e:
        print(f"Erro ao executar patch: {e}")
        return False

if __name__ == "__main__":
    main()