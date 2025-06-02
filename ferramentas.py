"""
Ferramentas do Agente IA
"""

import os
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests
from langchain.tools import BaseTool
from langchain.tools.base import ToolException

from agenteia.core.config import CONFIG
from agenteia.core.exceptions import (
    SecurityError,
    FileError,
    WebError,
    CommandError,
    ValidationError
)

# Configurações de segurança
MAX_FILE_SIZE = CONFIG["security"].max_file_size
ALLOWED_COMMANDS = CONFIG["security"].allowed_commands
ALLOWED_EXTENSIONS = CONFIG["security"].allowed_extensions
ALLOWED_DIRS = CONFIG["security"].allowed_dirs
REQUEST_TIMEOUT = CONFIG["security"].request_timeout

def validar_arquivo(caminho: str) -> None:
    """
    Valida um arquivo antes de operações.
    
    Args:
        caminho: Caminho do arquivo
        
    Raises:
        SecurityError: Se o arquivo não for válido
    """
    try:
        # Converter para Path
        path = Path(caminho)
        
        # Verificar extensão
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise SecurityError(f"Extensão não permitida: {path.suffix}")
        
        # Verificar diretório
        if not any(str(path.parent).startswith(d) for d in ALLOWED_DIRS):
            raise SecurityError(f"Diretório não permitido: {path.parent}")
        
        # Verificar tamanho se arquivo existir
        if path.exists() and path.stat().st_size > MAX_FILE_SIZE:
            raise SecurityError(f"Arquivo muito grande: {path}")
            
    except Exception as e:
        if not isinstance(e, SecurityError):
            raise SecurityError(f"Erro ao validar arquivo: {e}")
        raise

def validar_comando(comando: str) -> None:
    """
    Valida um comando antes de executar.
    
    Args:
        comando: Comando a ser executado
        
    Raises:
        SecurityError: Se o comando não for permitido
    """
    try:
        # Extrair primeiro comando
        cmd = comando.split()[0].lower()
        
        # Verificar se é permitido
        if cmd not in ALLOWED_COMMANDS:
            raise SecurityError(f"Comando não permitido: {cmd}")
            
    except Exception as e:
        if not isinstance(e, SecurityError):
            raise SecurityError(f"Erro ao validar comando: {e}")
        raise

class PesquisarWeb(BaseTool):
    """Ferramenta para pesquisar na web."""
    
    name = "pesquisar_web"
    description = "Pesquisa informações na web usando DuckDuckGo"
    
    def _run(self, query: str) -> str:
        try:
            # Fazer requisição
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            
            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            # Processar resposta
            data = response.json()
            
            if "Abstract" in data and data["Abstract"]:
                return data["Abstract"]
            elif "RelatedTopics" in data and data["RelatedTopics"]:
                return data["RelatedTopics"][0]["Text"]
            else:
                return "Nenhum resultado encontrado."
                
        except Exception as e:
            raise WebError(f"Erro na pesquisa web: {e}")

def criar_diretorio_projetos() -> Path:
    """
    Cria e retorna o diretório padrão para projetos.
    """
    try:
        # Criar diretório na pasta do usuário
        diretorio_projetos = Path.home() / "AgenteIA_Projetos"
        diretorio_projetos.mkdir(exist_ok=True)
        return diretorio_projetos
    except Exception as e:
        raise FileError(f"Erro ao criar diretório de projetos: {e}")

class ListarUnidades(BaseTool):
    """Ferramenta para listar unidades de disco disponíveis."""
    
    name = "listar_unidades"
    description = "Lista todas as unidades de disco disponíveis e suas informações"
    
    def _run(self) -> str:
        try:
            import win32api
            import win32file
            
            drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
            unidades_info = []
            
            for drive in drives:
                try:
                    # Obter informações da unidade
                    tipo = win32file.GetDriveType(drive)
                    tipo_str = {
                        0: "Desconhecido",
                        1: "Inexistente",
                        2: "Removível",
                        3: "Fixo",
                        4: "Rede",
                        5: "CD-ROM",
                        6: "RAM Disk"
                    }.get(tipo, "Desconhecido")
                    
                    # Verificar espaço disponível
                    try:
                        free_bytes = win32file.GetDiskFreeSpace(drive)
                        free_gb = (free_bytes[0] * free_bytes[1] * free_bytes[2]) / (1024**3)
                        espaco = f"{free_gb:.2f} GB livre"
                    except:
                        espaco = "Espaço não disponível"
                    
                    # Adicionar informações da unidade
                    unidades_info.append(f"📁 {drive} ({tipo_str}) - {espaco}")
                except:
                    continue
            
            # Adicionar informação do diretório de projetos
            diretorio_projetos = criar_diretorio_projetos()
            unidades_info.append(f"\n📁 Diretório de Projetos: {diretorio_projetos}")
            
            return "\n".join(unidades_info)
            
        except Exception as e:
            raise FileError(f"Erro ao listar unidades: {e}")

class ListarArquivos(BaseTool):
    """Ferramenta para listar arquivos."""
    
    name = "listar_arquivos"
    description = "Lista arquivos e diretórios em um caminho"
    
    def _run(self, diretorio: str = ".") -> str:
        try:
            # Validar diretório
            path = Path(diretorio)
            
            # Verificar se é a pasta do Windows
            if str(path).startswith('C:\\Windows'):
                return "Acesso à pasta do Windows não é permitido."
            
            # Listar arquivos
            if not path.exists():
                return f"Diretório não encontrado: {diretorio}"
                
            arquivos = []
            for item in path.iterdir():
                if item.is_file():
                    tamanho = item.stat().st_size / 1024  # Tamanho em KB
                    arquivos.append(f"📄 {item.name} ({tamanho:.1f} KB)")
                elif item.is_dir():
                    arquivos.append(f"📁 {item.name}/")
                    
            if not arquivos:
                return f"Nenhum arquivo encontrado em {diretorio}"
                
            return "\n".join(sorted(arquivos))
            
        except Exception as e:
            raise FileError(f"Erro ao listar arquivos: {e}")

class LerArquivo(BaseTool):
    """Ferramenta para ler arquivos."""
    
    name = "ler_arquivo"
    description = "Lê o conteúdo de um arquivo"
    
    def _run(self, caminho: str) -> str:
        try:
            # Validar arquivo
            validar_arquivo(caminho)
            
            # Ler arquivo
            path = Path(caminho)
            if not path.exists():
                return f"Arquivo não encontrado: {caminho}"
                
            with open(path, "r", encoding="utf-8") as f:
                conteudo = f.read()
                
            return conteudo
            
        except Exception as e:
            raise FileError(f"Erro ao ler arquivo: {e}")

class EscreverArquivo(BaseTool):
    """Ferramenta para escrever em arquivos."""
    
    name = "escrever_arquivo"
    description = "Escreve conteúdo em um arquivo"
    
    def _run(self, caminho: str, conteudo: str) -> str:
        try:
            # Validar arquivo
            validar_arquivo(caminho)
            
            # Escrever arquivo
            path = Path(caminho)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(conteudo)
                
            return f"Arquivo salvo: {caminho}"
            
        except Exception as e:
            raise FileError(f"Erro ao escrever arquivo: {e}")

class ExecutarComando(BaseTool):
    """Ferramenta para executar comandos."""
    
    name = "executar_comando"
    description = "Executa um comando no terminal"
    
    def _run(self, comando: str) -> str:
        try:
            # Validar comando
            validar_comando(comando)
            
            # Executar comando
            process = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                timeout=REQUEST_TIMEOUT
            )
            
            if process.returncode == 0:
                return process.stdout or "Comando executado com sucesso."
            else:
                raise CommandError(f"Erro ao executar comando: {process.stderr}")
                
        except subprocess.TimeoutExpired:
            raise CommandError("Comando excedeu o tempo limite")
        except Exception as e:
            raise CommandError(f"Erro ao executar comando: {e}")

# Lista de ferramentas disponíveis
ferramentas = [
    PesquisarWeb(),
    ListarArquivos(),
    LerArquivo(),
    EscreverArquivo(),
    ExecutarComando(),
    ListarUnidades()
] 