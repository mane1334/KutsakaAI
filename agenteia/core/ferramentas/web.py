"""
Ferramentas para pesquisa na web
"""

import requests
import json # Manter caso outras funções o usem
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup # Manter caso outras funções o usem
from duckduckgo_search import DDGS
from ..exceptions import WebError
from ...logs import setup_logging
from ..mcp_client import MCPClient # Importar MCPClient
from pydantic import BaseModel, Field # Importar BaseModel e Field para PesquisarWebArgs

logger = setup_logging(__name__, 'web.log')

# Definir o esquema de argumentos para a ferramenta pesquisar_web
class PesquisarWebArgs(BaseModel):
    """Argumentos para a ferramenta pesquisar_web."""
    query: str = Field(..., description="O termo de busca para pesquisar na web.")
    max_resultados: int = Field(5, description="O número máximo de resultados a retornar (padrão é 5).", ge=1, le=10)

def pesquisar_web(mcp_client: Optional[Any] = None, query: str = "", max_resultados: int = 5) -> str:
    """
    Pesquisa Zero-Click (informações instantâneas) no DuckDuckGo.
    
    Args:
        mcp_client: Instância do MCPClient (opcional)
        query: Termo de busca
        max_resultados: Número máximo de resultados (máx 10)
        
    Returns:
        Informações estruturadas em formato de texto
    """
    try:
        # Se tiver MCP Client, tenta usar o servidor
        if mcp_client:
            try:
                resultado_do_servidor = mcp_client.executar_ferramenta_no_servidor(
                    "pesquisar_web", 
                    query=query, 
                    max_resultados=max_resultados
                )
                return resultado_do_servidor
            except Exception as e:
                logger.warning(f"Falha ao usar MCP Server, usando implementação local: {e}")
        
        # Implementação local usando DuckDuckGo
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_resultados))
            
        if not results:
            return "Nenhum resultado encontrado."
            
        # Formatar resultados
        output = []
        for i, result in enumerate(results, 1):
            output.append(f"{i}. {result['title']}")
            output.append(f"   {result['body']}")
            output.append(f"   Fonte: {result['link']}\n")
            
        return "\n".join(output)
        
    except Exception as e:
        logger.error(f"Erro na pesquisa web: {str(e)}")
        return f"Erro ao realizar pesquisa: {str(e)}"

def extrair_texto(url: str,
    mcp_client: Optional[Any] = None
) -> str:
    """
    Extrai o texto principal de uma página web.
    
    Args:
        url: URL da página
        mcp_client: Instância do MCPClient para delegar a tarefa
        
    Returns:
        Texto extraído
    """
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info(f"Delegando extrair_texto para MCP Server para URL: {url}")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "extrair_texto",
                "parametros": {"url": url}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")

        # Faz requisição
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Extrai texto
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove scripts e estilos
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extrai texto
        texto = soup.get_text()
        
        # Limpa texto
        linhas = (linha.strip() for linha in texto.splitlines())
        chunks = (frase.strip() for linha in linhas for frase in linha.split("  "))
        texto = '\n'.join(chunk for chunk in chunks if chunk)
        
        return texto
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao extrair texto: {str(e)}")
        raise WebError(f"Erro ao extrair texto: {str(e)}")

def verificar_url(url: str) -> Dict[str, bool]:
    """
    Verifica se uma URL está acessível.
    
    Args:
        url: URL para verificar
        
    Returns:
        Dicionário com status da verificação
    """
    try:
        # Faz requisição
        response = requests.head(url, timeout=5, allow_redirects=True)
        
        return {
            "acessivel": response.status_code == 200,
            "redireciona": len(response.history) > 0,
            "https": url.startswith("https://"),
            "status_code": response.status_code
        }
        
    except requests.exceptions.RequestException:
        return {
            "acessivel": False,
            "redireciona": False,
            "https": url.startswith("https://"),
            "status_code": None
        } 