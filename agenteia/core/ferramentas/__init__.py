"""
Módulo de ferramentas do Agente IA
"""

from .web import pesquisar_web, extrair_texto, verificar_url
from .arquivos import (
    listar_arquivos,
    ler_arquivo,
    escrever_arquivo,
    ler_json,
    escrever_json,
    criar_diretorio,
    remover_arquivo,
    remover_diretorio,
    copiar_arquivo,
    mover_arquivo,
    listar_unidades,
)
from .comandos import (
    executar_comando,
    executar_comando_async,
    verificar_processo,
    encerrar_processo,
    listar_processos,
    executar_python,
    executar_pip
)
from .office import (
    criar_word,
    ler_word,
    criar_excel,
    ler_excel,
    criar_ppt,
    ler_ppt
)
from .monitoramento import (
    monitorar_tarefa,
    obter_status_tarefa,
    listar_tarefas_ativas,
    monitor
)
from .geracao_codigo import (
    gerar_codigo,
    gerar_codigo_completo,
    obter_status_geracao_codigo,
    listar_tarefas_ativas_geracao
)
from .utils import (
    calcular,
    gerar_senha,
    converter_data,
    calcular_idade,
    enviar_email,
    gerar_relatorio
)

# Importações necessárias da LangChain para definir as ferramentas
from langchain.tools import BaseTool, Tool, StructuredTool
from typing import List, Optional, Any, Dict, Tuple
import json # Para parsing JSON para o fallback

# Classes BaseModel para StructuredTools (necessário para definir a entrada para tool calling nativo)
from pydantic import BaseModel, Field

# Adicione aqui as classes BaseModel necessárias para as ferramentas que as utilizam
class EscreverArquivoArgs(BaseModel):
    caminho_do_arquivo: str = Field(description="O caminho completo ou relativo do arquivo a ser escrito.")
    conteudo_para_escrever: str = Field(description="O conteúdo a ser escrito no arquivo. Se o arquivo existir, seu conteúdo será sobrescrito.")

class CopiarArquivoArgs(BaseModel):
    caminho_origem: str = Field(description="O caminho do arquivo a ser copiado.")
    caminho_destino: str = Field(description="O caminho para onde o arquivo será copiado.")

class MoverArquivoArgs(BaseModel):
    caminho_origem: str = Field(description="O caminho do arquivo a ser movido.")
    caminho_destino: str = Field(description="O caminho para onde o arquivo será movido.")

class CriarDocumentoWordArgs(BaseModel):
    titulo: str = Field(description="O título do documento.")
    conteudo: List[Dict[str, Any]] = Field(description="Lista de seções para o documento, cada seção é um dicionário com chaves como 'titulo', 'texto', 'itens', 'tabela'.")
    caminho_saida: str = Field(description="O caminho completo ou relativo para salvar o arquivo .docx.")

class CriarCurriculoArgs(BaseModel):
    dados: Dict[str, Any] = Field(description="Dicionário contendo os dados do currículo (nome, email, objetivo, formacao, experiencia, habilidades, etc.).")
    caminho_saida: str = Field(description="O caminho completo ou relativo para salvar o arquivo .docx do currículo.")

class CriarRelatorioArgs(BaseModel):
    titulo: str = Field(description="O título do relatório.")
    dados: Dict[str, Any] = Field(description="Dicionário contendo os dados do relatório (resumo, metodologia, resultados, tabela_dados, conclusoes, recomendacoes, etc.).")
    caminho_saida: str = Field(description="O caminho completo ou relativo para salvar o arquivo .docx do relatório.")

class ConverterParaWordArgs(BaseModel):
    arquivo_origem: str = Field(description="O caminho do arquivo de texto a ser convertido (.txt).")
    arquivo_destino: str = Field(description="O caminho para salvar o arquivo .docx convertido.")

class PesquisarWebArgs(BaseModel):
    query: str = Field(description="O termo de busca para pesquisar na web.")
    max_resultados: int = Field(default=5, description="O número máximo de resultados a retornar.")


def get_available_tools(mcp_client: Optional[Any] = None) -> Tuple[List[BaseTool], List[BaseTool]]:
    """
    Retorna duas listas de ferramentas disponíveis para o Agente IA:
    uma para tool calling nativo e outra adaptada para o fallback (REACT).
    
    Args:
        mcp_client: Instância do MCPClient para ferramentas que precisam interagir com o servidor MCP.
        
    Returns:
        Uma tupla contendo (ferramentas_nativas, ferramentas_fallback).
    """
    # Funções wrapper para passar o mcp_client para as ferramentas originais.
    # Estas wrappers serão usadas tanto pelas ferramentas nativas quanto pelas ferramentas fallback.
    def listar_arquivos_wrapper(diretorio: str = '.') -> str:
        # Nota: A ferramenta original pode lidar com o argumento opcional.
        return listar_arquivos(diretorio=diretorio, mcp_client=mcp_client)
        
    def ler_arquivo_wrapper(caminho: str) -> str:
        return ler_arquivo(caminho=caminho, mcp_client=mcp_client)
        
    def escrever_arquivo_wrapper(caminho_do_arquivo: str, conteudo_para_escrever: str) -> str:
         return escrever_arquivo(caminho=caminho_do_arquivo, conteudo=conteudo_para_escrever, mcp_client=mcp_client)

    def criar_diretorio_wrapper(caminho: str) -> str:
        return criar_diretorio(caminho=caminho, mcp_client=mcp_client)

    def copiar_arquivo_wrapper(caminho_origem: str, caminho_destino: str) -> str:
         return copiar_arquivo(origem=caminho_origem, destino=caminho_destino, mcp_client=mcp_client)

    def mover_arquivo_wrapper(caminho_origem: str, caminho_destino: str) -> str:
        return mover_arquivo(origem=caminho_origem, destino=caminho_destino, mcp_client=mcp_client)
        
    def remover_arquivo_wrapper(caminho: str) -> str:
        return remover_arquivo(caminho=caminho, mcp_client=mcp_client)
        
    def remover_diretorio_wrapper(caminho: str) -> str:
        return remover_diretorio(caminho=caminho, mcp_client=mcp_client)

    def executar_comando_wrapper(comando: str) -> str:
        return executar_comando(comando=comando, shell=True, timeout=60.0, mcp_client=mcp_client)

    def criar_documento_word_wrapper(titulo: str, conteudo: List[Dict[str, Any]], caminho_saida: str) -> str:
         return criar_documento_word(titulo=titulo, conteudo=conteudo, caminho_saida=caminho_saida, mcp_client=mcp_client)

    def criar_curriculo_wrapper(dados: Dict[str, Any], caminho_saida: str) -> str:
        return criar_curriculo(dados=dados, caminho_saida=caminho_saida, mcp_client=mcp_client)

    def criar_relatorio_wrapper(titulo: str, dados: Dict[str, Any], caminho_saida: str) -> str:
        return criar_relatorio(titulo=titulo, dados=dados, caminho_saida=caminho_saida, mcp_client=mcp_client)

    def converter_para_word_wrapper(arquivo_origem: str, arquivo_destino: str) -> str:
        return converter_para_word(arquivo_origem=arquivo_origem, arquivo_destino=arquivo_destino, mcp_client=mcp_client)
        
    def pesquisar_web_wrapper(query: str, max_resultados: int = 5) -> str:
        # A função original já lida com argumentos nomeados.
        return pesquisar_web(mcp_client=mcp_client, query=query, max_resultados=max_resultados)

    # --- Definição das Ferramentas para Tool Calling Nativo (usando StructuredTool com args_schema) ---
    ferramentas_nativas: List[BaseTool] = [
        Tool(
            name="listar_arquivos",
            func=listar_arquivos_wrapper,
            description="Lista arquivos e diretórios em um caminho específico. Entrada: caminho do diretório (str). Use '.' para o diretório atual."
        ),
        Tool(
            name="ler_arquivo",
            func=ler_arquivo_wrapper,
            description="Lê o conteúdo de um arquivo de texto. Entrada: caminho do arquivo (str)."
        ),
        StructuredTool.from_function(
            func=escrever_arquivo_wrapper,
            name="escrever_arquivo",
            description="Escreve conteúdo em um arquivo. Cria o arquivo se não existir, sobrescreve se existir. Entradas: caminho_do_arquivo (str), conteudo_para_escrever (str).",
            args_schema=EscreverArquivoArgs
        ),
        Tool(
            name="criar_diretorio",
            func=criar_diretorio_wrapper,
            description="Cria um novo diretório. Entrada: caminho do diretório a ser criado (str)."
        ),
        StructuredTool.from_function(
            func=copiar_arquivo_wrapper,
            name="copiar_arquivo",
            description="Copia um arquivo de uma origem para um destino. Entradas: caminho_origem (str), caminho_destino (str).",
            args_schema=CopiarArquivoArgs
        ),
        StructuredTool.from_function(
            func=mover_arquivo_wrapper,
            name="mover_arquivo",
            description="Move um arquivo de uma origem para um destino. Entradas: caminho_origem (str), caminho_destino (str).",
            args_schema=MoverArquivoArgs
        ),
        Tool(
            name="remover_arquivo",
            func=remover_arquivo_wrapper,
            description="Remove (deleta) um arquivo. Entrada: caminho do arquivo (str)."
        ),
        Tool(
            name="remover_diretorio",
            func=remover_diretorio_wrapper,
            description="Remove (deleta) um diretório e todo o seu conteúdo recursivamente. Entrada: caminho do diretório (str)."
        ),
        Tool(
            name="executar_comando",
            func=executar_comando_wrapper,
            description="Executa um comando shell no sistema operacional e retorna a sua saída. Entrada: comando_a_executar (str)."
        ),
        StructuredTool.from_function(
            func=criar_documento_word_wrapper,
            name="criar_documento_word",
            description="Cria um novo documento Word (.docx). Entradas: titulo (str), conteudo (List[Dict[str, Any]] - lista de seções, cada seção é um dicionário com chaves como 'titulo', 'texto', 'itens', 'tabela'), caminho_saida (str - ex: 'documento.docx').",
            args_schema=CriarDocumentoWordArgs
        ),
         StructuredTool.from_function(
            func=criar_curriculo_wrapper,
            name="criar_curriculo",
            description="Cria um currículo profissional em formato Word. Entradas: dados (Dict[str, Any] - dicionário contendo chaves como 'nome', 'email', 'objetivo', 'formacao', 'experiencia', 'habilidades'), caminho_saida (str - ex: 'curriculo.docx').",
            args_schema=CriarCurriculoArgs
        ),
         StructuredTool.from_function(
            func=criar_relatorio_wrapper,
            name="criar_relatorio",
            description="Gera um relatório profissional em formato Word. Entradas: titulo (str), dados (Dict[str, Any] - dicionário contendo chaves como 'resumo', 'metodologia', 'resultados', 'tabela_dados', 'conclusoes', 'recomendacoes'), caminho_saida (str - ex: 'relatorio.docx').",
            args_schema=CriarRelatorioArgs
        ),
        StructuredTool.from_function(
            func=converter_para_word_wrapper,
            name="converter_para_word",
            description="Converte um arquivo de texto para um documento Word (.docx). Entradas: arquivo_origem (str), arquivo_destino (str).",
            args_schema=ConverterParaWordArgs
        ),
        StructuredTool.from_function(
            func=pesquisar_web_wrapper,
            name="pesquisar_web",
            description="Pesquisa Zero-Click (informações instantâneas) no DuckDuckGo. Entradas: query (str), max_resultados (int, opcional, padrão 5).",
            args_schema=PesquisarWebArgs
        )
        # Adicionar outras ferramentas nativas aqui...
    ]

    # --- Definição das Ferramentas para Fallback (REACT) (usando Tool com input string) ---
    # StructuredTools são adaptadas para receber uma string JSON.
    # Tools de input único usam a mesma wrapper, mas esperam a string direta.
    ferramentas_fallback: List[BaseTool] = [
        Tool(
            name="listar_arquivos",
            func=listar_arquivos_wrapper,
            description="Lista arquivos e diretórios em um caminho específico. Entrada: caminho do diretório (str). Use '.' para o diretório atual."
        ),
        Tool(
            name="ler_arquivo",
            func=ler_arquivo_wrapper,
            description="Lê o conteúdo de um arquivo de texto. Entrada: caminho do arquivo (str)."
        ),
        Tool(
            name="escrever_arquivo",
            func=lambda input_str: escrever_arquivo_wrapper(**json.loads(input_str)), # Espera JSON
            description="Escreve conteúdo em um arquivo. Cria o arquivo se não existir, sobrescreve se existir. Entrada: string JSON com chaves 'caminho_do_arquivo' (str) e 'conteudo_para_escrever' (str)."
        ),
         Tool(
            name="criar_diretorio",
            func=criar_diretorio_wrapper,
            description="Cria um novo diretório. Entrada: caminho do diretório a ser criado (str)."
        ),
        Tool(
            name="copiar_arquivo",
            func=lambda input_str: copiar_arquivo_wrapper(**json.loads(input_str)), # Espera JSON
            description="Copia um arquivo de uma origem para um destino. Entrada: string JSON com chaves 'caminho_origem' (str) e 'caminho_destino' (str)."
        ),
        Tool(
            name="mover_arquivo",
            func=lambda input_str: mover_arquivo_wrapper(**json.loads(input_str)), # Espera JSON
            description="Move um arquivo de uma origem para um destino. Entrada: string JSON com chaves 'caminho_origem' (str) e 'caminho_destino' (str)."
        ),
        Tool(
            name="remover_arquivo",
            func=remover_arquivo_wrapper,
            description="Remove (deleta) um arquivo. Entrada: caminho do arquivo (str)."
        ),
        Tool(
            name="remover_diretorio",
            func=remover_diretorio_wrapper,
            description="Remove (deleta) um diretório e todo o seu conteúdo recursivamente. Entrada: caminho do diretório (str)."
        ),
         Tool(
            name="executar_comando",
            func=executar_comando_wrapper,
            description="Executa um comando shell no sistema operacional e retorna a sua saída. Entrada: comando_a_executar (str)."
        ),
         Tool(
            name="criar_documento_word",
            func=lambda input_str: criar_documento_word_wrapper(**json.loads(input_str)), # Espera JSON
            description="Cria um novo documento Word (.docx). Entrada: string JSON com chaves 'titulo' (str), 'conteudo' (List[Dict[str, Any]]) e 'caminho_saida' (str)."
        ),
        Tool(
            name="criar_curriculo",
            func=lambda input_str: criar_curriculo_wrapper(**json.loads(input_str)), # Espera JSON
            description="Cria um currículo profissional em formato Word. Entrada: string JSON com chaves 'dados' (Dict[str, Any]) e 'caminho_saida' (str)."
        ),
         Tool(
            name="criar_relatorio",
            func=lambda input_str: criar_relatorio_wrapper(**json.loads(input_str)), # Espera JSON
            description="Gera um relatório profissional em formato Word. Entrada: string JSON com chaves 'titulo' (str), 'dados' (Dict[str, Any]) e 'caminho_saida' (str)."
        ),
        Tool(
            name="converter_para_word",
            func=lambda input_str: converter_para_word_wrapper(**json.loads(input_str)), # Espera JSON
            description="Converte um arquivo de texto para um documento Word (.docx). Entrada: string JSON com chaves 'arquivo_origem' (str) e 'arquivo_destino' (str)."
        ),
        Tool(
            name="pesquisar_web",
            func=lambda input_str: pesquisar_web_wrapper(**json.loads(input_str)), # Espera JSON
            description="Pesquisa Zero-Click (informações instantâneas) no DuckDuckGo. Entrada: string JSON com chaves 'query' (str) e opcionalmente 'max_resultados' (int)."
        )
        # Adicionar outras ferramentas de fallback aqui...
    ]

    return ferramentas_nativas, ferramentas_fallback

# Remover a definição de __all__ pois não vamos exportar funções individualmente dessa forma.
# As ferramentas serão acessadas através da função get_available_tools
# del __all__ 