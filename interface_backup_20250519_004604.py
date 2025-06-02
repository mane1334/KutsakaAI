"""
Interface Streamlit do AgenteIA
"""

import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import json
from datetime import datetime
import requests
import subprocess
from typing import List, Tuple, Dict, Any
import os
import pandas as pd
import time
from gtts import gTTS
import tempfile
import queue
import threading
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import re

import logging
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

from agenteia import AgenteIA
from agenteia.core.config import CONFIG
from agenteia.logs import setup_logging
from agenteia.core.ferramentas import ListarUnidades, ListarArquivos

# Configurar logging
logger = setup_logging(__name__)

st.set_page_config(
    page_title="AgenteIA - Seu Assistente Inteligente",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fila global para requisições
request_queue = queue.Queue()
processing_lock = threading.Lock()
request_status = {}  # Dicionário para rastrear status das requisições
active_requests = set()  # Conjunto para rastrear requisições ativas

# Definir system_message global
system_message = """
Você é um assistente virtual inteligente.
Você pode ajudar com várias tarefas.

Ferramentas disponíveis:

1. Manipulação de Arquivos:
   - listar_arquivos - Lista arquivos e diretórios em um caminho
   - escrever_arquivo - Cria ou modifica um arquivo
   - criar_diretorio - Cria um novo diretório
   - remover_arquivo - Remove um arquivo
   - remover_diretorio - Remove um diretório
   - copiar_arquivo - Copia um arquivo
   - mover_arquivo - Move um arquivo

2. Leitura de Documentos:
   - ler_arquivo_txt - Lê o conteúdo de arquivos .txt
   - ler_arquivo_docx - Lê o conteúdo de arquivos .docx (Word)
   - ler_arquivo_pdf - Lê o conteúdo de arquivos .pdf
   - ler_arquivo_csv - Lê o conteúdo de arquivos .csv

3. Web e Internet:
   - pesquisar_web - Realiza pesquisas na web
   - obter_clima - Obtém informações sobre o clima
   - obter_noticias - Obtém as últimas notícias
   - obter_cotacao - Obtém cotações de moedas

4. Processamento de Texto:
   - traduzir_texto - Traduz texto entre idiomas
   - resumir_texto - Cria um resumo do texto
   - extrair_palavras_chave - Extrai palavras-chave do texto
   - analisar_sentimento - Analisa o sentimento em textos
   - gerar_resumo - Cria resumos automáticos
   - classificar_texto - Categoriza conteúdo
   - extrair_entidades - Identifica pessoas, lugares, datas
   - verificar_plagio - Verifica similaridade de textos

5. Manipulação de Dados:
   - converter_formato - Converte entre formatos (JSON, CSV, XML)
   - validar_dados - Valida dados estruturados
   - filtrar_dados - Filtra e ordena conjuntos de dados
   - agregar_dados - Realiza agregações e estatísticas
   - visualizar_dados - Cria visualizações básicas

6. Segurança:
   - verificar_seguranca - Realiza análise básica de segurança
   - sanitizar_input - Limpa dados de entrada
   - validar_permissao - Verifica permissões
   - criptografar_dados - Realiza criptografia básica
   - verificar_vulnerabilidades - Checa vulnerabilidades

7. Otimização:
   - otimizar_codigo - Sugere otimizações
   - analisar_performance - Analisa desempenho
   - reduzir_complexidade - Simplifica código
   - melhorar_legibilidade - Melhora legibilidade
   - refatorar_codigo - Sugere refatorações

8. Documentação:
   - gerar_documentacao - Cria documentação
   - extrair_comentarios - Analisa comentários
   - validar_documentacao - Verifica documentação
   - atualizar_docs - Atualiza documentação
   - gerar_exemplos - Cria exemplos de uso

9. Integração:
   - verificar_api - Testa APIs
   - validar_webhook - Verifica webhooks
   - testar_conexao - Testa conectividade
   - monitorar_servico - Monitora serviços
   - sincronizar_dados - Sincroniza dados

10. Desenvolvimento:
    - gerar_teste - Cria testes unitários
    - validar_codigo - Valida código
    - verificar_padrao - Verifica padrões
    - sugerir_melhorias - Sugere melhorias
    - analisar_dependencias - Analisa dependências

11. Suporte:
    - gerar_log - Gera logs estruturados
    - analisar_erro - Analisa erros
    - sugerir_solucao - Sugere soluções
    - verificar_compatibilidade - Verifica compatibilidade
    - gerar_relatorio - Gera relatórios

Para usar uma ferramenta, use o formato:
Action: nome_da_ferramenta
Action Input: {"parametro1": "valor1", "parametro2": "valor2"}

IMPORTANTE: 
1. Use barras normais (/) nos caminhos, não use barras invertidas (\\)
2. Sempre verifique se os parâmetros estão corretos
3. Trate erros adequadamente
4. Confirme a execução das ações
5. Mantenha o usuário informado
"""

class ModeloType(Enum):
    GERAL = "geral"
    CODER = "coder"

@dataclass
class ModeloConfig:
    nome: str
    descricao: str
    system_message: str
    modelos: List[str]
    max_tokens: int = 2000
    temperature: float = 0.3
    timeout: int = 300  # 5 minutos padrão

# Configuração dos modelos
MODELOS_CONFIG = {
    ModeloType.GERAL: ModeloConfig(
        nome="Modelos Gerais",
        descricao="Modelos para uso geral, conversas e tarefas básicas",
        system_message="""
        Você é um assistente virtual inteligente e versátil.
        Você pode ajudar com várias tarefas e manter conversas naturais.
        
        Capacidades Principais:
        1. Conversação Natural
           - Manter diálogos fluidos e contextuais
           - Adaptar o tom ao contexto
           - Usar linguagem apropriada
           - Demonstrar empatia
           - Manter coerência
        
        2. Processamento de Texto
           - Resumir textos
           - Extrair informações
           - Analisar sentimentos
           - Identificar tópicos
           - Gerar conteúdo
        
        3. Análise de Dados
           - Interpretar dados
           - Identificar padrões
           - Fazer inferências
           - Sugerir insights
           - Validar informações
        
        4. Resolução de Problemas
           - Analisar situações
           - Propor soluções
           - Avaliar alternativas
           - Considerar consequências
           - Recomendar ações
        
        5. Aprendizado Contínuo
           - Adaptar a novos contextos
           - Incorporar feedback
           - Melhorar respostas
           - Atualizar conhecimentos
           - Refinar abordagens
        """,
        modelos=["qwen3:1.7b", "qwen3:0.6b", "qwen3:4b"],
        max_tokens=4000,
        temperature=0.5,
        timeout=180  # 3 minutos para modelos gerais
    ),
    ModeloType.CODER: ModeloConfig(
        nome="Modelos de Programação",
        descricao="Modelos especializados em programação e desenvolvimento",
        system_message="""
        Você é um assistente virtual especializado em programação.
        Você pode ajudar com desenvolvimento de software, debugging e boas práticas.
        
        Você tem acesso à internet e pode:
        1. Buscar exemplos de código em repositórios como GitHub
        2. Consultar documentação oficial
        3. Pesquisar soluções em Stack Overflow
        4. Verificar padrões de projeto em sites especializados
        5. Buscar boas práticas e tutoriais
        6. Consultar benchmarks de performance
        7. Verificar vulnerabilidades conhecidas
        8. Pesquisar bibliotecas e frameworks
        9. Consultar guias de estilo
        10. Buscar casos de uso similares
        11. Pesquisar em repositórios de código
        12. Verificar exemplos de implementação
        13. Consultar fóruns de desenvolvimento
        14. Buscar artigos técnicos
        15. Verificar documentação de APIs
        """,
        modelos=["qwen2.5-coder:3b"],
        max_tokens=8000,  # Aumentado para permitir código mais complexo
        temperature=0.3,  # Reduzido para maior precisão
        timeout=300  # 5 minutos para modelos de programação
    )
}

def obter_modelos_disponiveis() -> List[str]:
    """
    Obtém a lista de modelos disponíveis no Ollama.
    
    Returns:
        List[str]: Lista de modelos disponíveis
    """
    try:
        # Primeiro tenta usar o comando ollama list
        try:
            resultado = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Processar saída
            linhas = resultado.stdout.strip().split("\n")
            modelos = []
            
            # Pular cabeçalho
            for linha in linhas[1:]:
                if linha.strip():
                    # Extrair nome do modelo
                    nome = linha.split()[0]
                    modelos.append(nome)
            
            if modelos:
                return modelos
                
        except Exception as e:
            logger.warning(f"Erro ao usar comando ollama list: {e}")
        
        # Se falhar, tenta a API
        try:
            response = requests.get("http://localhost:11434/api/tags")
            
            if response.status_code == 200:
                dados = response.json()
                if "models" in dados:
                    return [modelo["name"] for modelo in dados["models"]]
                    
        except Exception as e:
            logger.warning(f"Erro ao usar API do Ollama: {e}")
        
        # Se ambos falharem, retorna lista padrão
        logger.warning("Usando lista padrão de modelos")
        return [
            "qwen3:1.7b",
            "qwen3:0.6b",
            "qwen3:4b",
            "qwen2.5-coder:3b"
        ]
            
    except Exception as e:
        logger.error(f"Erro ao obter modelos: {e}")
        return ["qwen3:1.7b"]  # Modelo padrão em caso de erro

def listar_modelos_ollama() -> List[Dict[str, Any]]:
    """
    Lista os modelos disponíveis no Ollama com informações detalhadas.
    
    Returns:
        List[Dict[str, Any]]: Lista de modelos com informações
    """
    try:
        # Executar comando
        resultado = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Processar saída
        linhas = resultado.stdout.strip().split("\n")
        modelos = []
        
        # Pular cabeçalho
        for linha in linhas[1:]:
            if linha.strip():
                partes = linha.split()
                if len(partes) >= 3:
                    nome = partes[0]
                    tamanho = partes[1]
                    modificado = " ".join(partes[2:])
                    modelos.append({
                        "nome": nome,
                        "tamanho": tamanho,
                        "modificado": modificado
                    })
        
        return modelos
        
    except Exception as e:
        logger.error(f"Erro ao listar modelos: {e}")
        return []

def verificar_modelo_disponivel(modelo: str) -> bool:
    """
    Verifica se um modelo está disponível.
    
    Args:
        modelo: Nome do modelo
    
    Returns:
        bool: True se o modelo estiver disponível, False caso contrário
    """
    try:
        # Listar modelos
        modelos = obter_modelos_disponiveis()
        
        # Verificar se o modelo está na lista
        return modelo in modelos
        
    except Exception as e:
        logger.error(f"Erro ao verificar modelo: {e}")
        return False

# Funções de callback para a barra de progresso
def _progress_start(message: str):
    st.session_state.is_processing_message = True
    st.session_state.show_progress_bar = True
    st.session_state.current_progress_text = message
    st.session_state.current_progress_value = 5 # Inicia com um pequeno valor para mostrar atividade
    logger.debug(f"Progress start: {message}")

    # Directly update placeholders if they exist
    if hasattr(st.session_state, 'progress_text_placeholder') and st.session_state.progress_text_placeholder is not None:
        st.session_state.progress_text_placeholder.text(f"Status: {message}")
    if hasattr(st.session_state, 'progress_bar_placeholder') and st.session_state.progress_bar_placeholder is not None and st.session_state.show_progress_bar:
        st.session_state.progress_bar_placeholder.progress(max(0, min(100, 5)))

def _progress_update(value: int, message: str):
    st.session_state.show_progress_bar = True
    st.session_state.current_progress_text = message
    st.session_state.current_progress_value = int(value)  # Ensure value is int
    logger.debug(f"Progress update: {message} - {value}%")

    # Directly update placeholders if they exist
    if hasattr(st.session_state, 'progress_text_placeholder') and st.session_state.progress_text_placeholder is not None:
        st.session_state.progress_text_placeholder.text(f"Status: {message}")
    if hasattr(st.session_state, 'progress_bar_placeholder') and st.session_state.progress_bar_placeholder is not None and st.session_state.show_progress_bar:
        # Ensure value is clamped between 0 and 100 for st.progress
        clamped_value = max(0, min(100, int(value)))
        st.session_state.progress_bar_placeholder.progress(clamped_value)

def _progress_end():
    st.session_state.is_processing_message = False
    st.session_state.show_progress_bar = False
    st.session_state.current_progress_text = ""
    st.session_state.current_progress_value = 0
    logger.debug("Progress end")

    # Directly clear/update placeholders
    if hasattr(st.session_state, 'progress_text_placeholder') and st.session_state.progress_text_placeholder is not None:
        st.session_state.progress_text_placeholder.empty()
    if hasattr(st.session_state, 'progress_bar_placeholder') and st.session_state.progress_bar_placeholder is not None:
        st.session_state.progress_bar_placeholder.empty()

# ---- AGENT INITIALIZATION ----
logger.debug(f"SESSION_STATE_DEBUG: Pre-check for 'agente_ia'. Session keys: {list(st.session_state.keys())}")
if "agente_ia" not in st.session_state:
    logger.info("SESSION_STATE_DEBUG: 'agente_ia' NOT in session_state. Initializing AgenteIA...")
    st.session_state.agente_ia = AgenteIA(
        on_progress_start=_progress_start,
        on_progress_update=_progress_update,
        on_progress_end=_progress_end
    )
    logger.info(f"SESSION_STATE_DEBUG: AgenteIA initialized and set in session_state. Type: {type(st.session_state.agente_ia)}.")
else:
    logger.info("SESSION_STATE_DEBUG: 'agente_ia' IS ALREADY in session_state. Re-assigning callbacks.")
    # Re-assign callbacks to the existing agent instance
    if hasattr(st.session_state.agente_ia, 'on_progress_start'): # Check if agent has these attributes before assigning
        st.session_state.agente_ia.on_progress_start = _progress_start
    if hasattr(st.session_state.agente_ia, 'on_progress_update'):
        st.session_state.agente_ia.on_progress_update = _progress_update
    st.session_state.agente_ia.on_progress_end = _progress_end



agente_ia = st.session_state.agente_ia # Ensure agente_ia variable is sourced from session_state

if "modelo" not in st.session_state:
    st.session_state.modelo = "qwen3:1.7b"  # Modelo padrão

if "ferramentas" not in st.session_state:
    st.session_state.ferramentas = ["listar_arquivos", "escrever_arquivo", "criar_diretorio"]

if "verboso" not in st.session_state:
    st.session_state.verboso = False

if "show_progress_bar" not in st.session_state:
    st.session_state.show_progress_bar = False

if "current_progress_value" not in st.session_state:
    st.session_state.current_progress_value = 0

if "current_progress_text" not in st.session_state:
    st.session_state.current_progress_text = ""

if "modelos_disponiveis" not in st.session_state:
    st.session_state.modelos_disponiveis = obter_modelos_disponiveis()

if "ferramentas_disponiveis" not in st.session_state:
    st.session_state.ferramentas_disponiveis = [
        # Manipulação de Arquivos
        "listar_arquivos",
        "escrever_arquivo",
        "criar_diretorio",
        "remover_arquivo",
        "remover_diretorio",
        "copiar_arquivo",
        "mover_arquivo",
        
        # Leitura de Documentos
        "ler_arquivo_txt",
        "ler_arquivo_docx",
        "ler_arquivo_pdf",
        "ler_arquivo_csv",
        
        # Web e Internet
        "pesquisar_web",
        "obter_clima",
        "obter_noticias",
        "obter_cotacao",
        
        # Processamento de Texto
        "traduzir_texto",
        "resumir_texto",
        "extrair_palavras_chave",
        
        # Análise e Processamento
        "analisar_sentimento",
        "gerar_resumo",
        "classificar_texto",
        "extrair_entidades",
        "verificar_plagio",
        
        # Manipulação de Dados
        "converter_formato",
        "validar_dados",
        "filtrar_dados",
        "agregar_dados",
        "visualizar_dados",
        
        # Segurança
        "verificar_seguranca",
        "sanitizar_input",
        "validar_permissao",
        "criptografar_dados",
        "verificar_vulnerabilidades",
        
        # Otimização
        "otimizar_codigo",
        "analisar_performance",
        "reduzir_complexidade",
        "melhorar_legibilidade",
        "refatorar_codigo",
        
        # Documentação
        "gerar_documentacao",
        "extrair_comentarios",
        "validar_documentacao",
        "atualizar_docs",
        "gerar_exemplos",
        
        # Integração
        "verificar_api",
        "validar_webhook",
        "testar_conexao",
        "monitorar_servico",
        "sincronizar_dados",
        
        # Desenvolvimento
        "gerar_teste",
        "validar_codigo",
        "verificar_padrao",
        "sugerir_melhorias",
        "analisar_dependencias",
        
        # Suporte
        "gerar_log",
        "analisar_erro",
        "sugerir_solucao",
        "verificar_compatibilidade",
        "gerar_relatorio"
    ]

# Estilo CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTextInput > div > div > input {
        font-size: 1.2rem;
    }
    .stButton > button {
        width: 100%;
        font-size: 1.2rem;
        padding: 0.5rem 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: row;
        align-items: flex-start;
    }
    .chat-message.user {
        background-color: #2b313e;
    }
    .chat-message.assistant {
        background-color: #475063;
    }
    .chat-message .avatar {
        width: 2rem;
        height: 2rem;
        border-radius: 50%;
        margin-right: 1rem;
    }
    .chat-message .message {
        flex: 1;
    }
    </style>
""", unsafe_allow_html=True)

def inicializar_agente(modelo: str = None, ferramentas: list = None, verboso: bool = None) -> None:
    """
    Inicializa o agente.
    
    Args:
        modelo: Nome do modelo
        ferramentas: Lista de ferramentas
        verboso: Modo verboso
    """
    try:
        # Verificar modelo
        if modelo:
            if modelo not in st.session_state.modelos_disponiveis:
                st.error(f"Modelo não encontrado: {modelo}")
                return
            st.session_state.modelo = modelo
        
        # Verificar ferramentas
        if ferramentas:
            for ferramenta in ferramentas:
                if ferramenta not in st.session_state.ferramentas_disponiveis:
                    st.error(f"Ferramenta não encontrada: {ferramenta}")
                    return
            st.session_state.ferramentas = ferramentas
        
        # Verificar modo verboso
        if verboso is not None:
            st.session_state.verboso = verboso
        
        # Verificar se o modelo está disponível
        if not verificar_modelo_disponivel(st.session_state.modelo):
            st.error(f"Modelo não disponível: {st.session_state.modelo}")
            return
        
        # Verificar se as ferramentas estão disponíveis
        for ferramenta in st.session_state.ferramentas:
            if not verificar_ferramenta_disponivel(ferramenta):
                st.error(f"Ferramenta não disponível: {ferramenta}")
                return
        
        # Inicializar agente
        st.success("Agente inicializado com sucesso")
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "system",
            "content": f"Agente inicializado com o modelo {st.session_state.modelo} e as ferramentas {', '.join(st.session_state.ferramentas)}"
        })
        
    except Exception as e:
        st.error(f"Erro ao inicializar agente: {e}")

def verificar_ferramenta_disponivel(ferramenta: str) -> bool:
    """
    Verifica se uma ferramenta está disponível.
    
    Args:
        ferramenta: Nome da ferramenta
    
    Returns:
        True se a ferramenta estiver disponível, False caso contrário
    """
    try:
        # TODO: Implementar verificação da ferramenta
        return True
        
    except Exception as e:
        st.error(f"Erro ao verificar ferramenta: {e}")
        return False

def inicializar_historico() -> None:
    """
    Inicializa o histórico de mensagens.
    """
    try:
        # Verificar se o histórico já existe
        if "historico" in st.session_state:
            return
        
        # Inicializar histórico
        st.session_state.historico = []
        
        # Adicionar mensagem inicial
        st.session_state.historico.append({
            "role": "system",
            "content": "Bem-vindo ao AgenteIA! Estou aqui para ajudar com qualquer coisa que você precise.",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        logger.error(f"Erro ao inicializar histórico: {e}")

def limpar_historico() -> None:
    """
    Limpa o histórico de mensagens.
    """
    try:
        # Verificar se o histórico existe
        if "historico" not in st.session_state:
            st.warning("Histórico não inicializado")
            return
        
        # Limpar histórico
        st.session_state.historico = []
        
        # Adicionar mensagem de confirmação
        st.session_state.historico.append({
            "role": "system",
            "content": "Histórico limpo",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Exibir mensagem de sucesso
        st.success("Histórico limpo com sucesso")
        
    except Exception as e:
        st.error(f"Erro ao limpar histórico: {e}")

def salvar_historico(caminho: str) -> None:
    """
    Salva o histórico de mensagens em um arquivo.
    
    Args:
        caminho: Caminho do arquivo
    """
    try:
        # Verificar se o histórico existe
        if "historico" not in st.session_state:
            st.warning("Histórico não inicializado")
            return
        
        # Salvar histórico
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(st.session_state.historico, f, indent=4, ensure_ascii=False)
        
        # Adicionar mensagem de confirmação
        st.session_state.historico.append({
            "role": "system",
            "content": f"Histórico salvo em {caminho}",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Exibir mensagem de sucesso
        st.success(f"Histórico salvo em {caminho}")
        
    except Exception as e:
        st.error(f"Erro ao salvar histórico: {e}")

def carregar_historico(caminho: str) -> None:
    """
    Carrega o histórico de mensagens de um arquivo.
    
    Args:
        caminho: Caminho do arquivo
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(caminho):
            st.error(f"Arquivo não encontrado: {caminho}")
            return
        
        # Carregar histórico
        with open(caminho, "r", encoding="utf-8") as f:
            st.session_state.historico = json.load(f)
        
        # Adicionar mensagem de confirmação
        st.session_state.historico.append({
            "role": "system",
            "content": f"Histórico carregado de {caminho}",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Exibir mensagem de sucesso
        st.success(f"Histórico carregado de {caminho}")
        
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")

def exibir_mensagem(role: str, content: str) -> None:
    """
    Exibe uma mensagem.
    
    Args:
        role: Papel da mensagem (user, assistant, system, error, success, info, warning)
        content: Conteúdo da mensagem
    """
    try:
        # Verificar se o histórico existe
        if "historico" not in st.session_state:
            st.warning("Histórico não inicializado")
            return
        
        # Adicionar mensagem ao histórico
        st.session_state.historico.append({
            "role": role,
            "content": content,
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Exibir mensagem
        if role == "user":
            st.write(f"👤 **Você:** {content}")
        elif role == "assistant":
            st.write(f"🤖 **Assistente:** {content}")
        elif role == "system":
            st.write(f"⚙️ **Sistema:** {content}")
        elif role == "error":
            st.error(content)
        elif role == "success":
            st.success(content)
        elif role == "info":
            st.info(content)
        elif role == "warning":
            st.warning(content)
        else:
            st.write(f"**{role}:** {content}")
        
    except Exception as e:
        st.error(f"Erro ao exibir mensagem: {e}")

def exibir_mensagem_erro(mensagem: str) -> None:
    """
    Exibe uma mensagem de erro.
    
    Args:
        mensagem: Mensagem de erro
    """
    try:
        exibir_mensagem("error", mensagem)
        
    except Exception as e:
        st.error(f"Erro ao exibir mensagem de erro: {e}")

def exibir_mensagem_sucesso(mensagem: str) -> None:
    """
    Exibe uma mensagem de sucesso.
    
    Args:
        mensagem: Mensagem de sucesso
    """
    try:
        exibir_mensagem("success", mensagem)
        
    except Exception as e:
        st.error(f"Erro ao exibir mensagem de sucesso: {e}")

def exibir_mensagem_info(mensagem: str) -> None:
    """
    Exibe uma mensagem informativa.
    
    Args:
        mensagem: Mensagem informativa
    """
    try:
        exibir_mensagem("info", mensagem)
        
    except Exception as e:
        st.error(f"Erro ao exibir mensagem informativa: {e}")

def exibir_mensagem_aviso(mensagem: str) -> None:
    """
    Exibe uma mensagem de aviso.
    
    Args:
        mensagem: Mensagem de aviso
    """
    try:
        exibir_mensagem("warning", mensagem)
        
    except Exception as e:
        st.error(f"Erro ao exibir mensagem de aviso: {e}")

def exibir_ajuda() -> None:
    """Exibe a ajuda da interface."""
    try:
        # Título
        st.title("📚 Ajuda")
        
        # Introdução
        st.markdown("""
        Bem-vindo ao AgenteIA! Este é um assistente virtual inteligente que pode ajudar você com diversas tarefas.
        
        ### Funcionalidades
        
        - **Chat**: Converse com o agente sobre qualquer assunto
        - **Programação**: Peça ajuda para criar códigos e programas
        - **Arquivos**: Manipule arquivos e diretórios
        - **Documentos**: Crie e edite documentos
        - **Web**: Pesquise informações na internet
        
        ### Como Usar
        
        1. Digite sua mensagem na caixa de texto
        2. Aguarde a resposta do agente
        3. Use os botões da barra lateral para:
           - Selecionar o modelo
           - Atualizar a lista de modelos
           - Baixar o modelo coder
           - Limpar o histórico
        
        ### Dicas
        
        - Para tarefas de programação, use o modelo coder
        - Use caminhos completos do Windows (ex: C:\\Users\\Usuario\\Desktop)
        - Seja específico em suas solicitações
        - Em caso de erro, tente reformular sua pergunta
        
        ### Exemplos
        
        - "Crie um jogo snake em Python"
        - "Crie uma pasta chamada 'projetos' no desktop"
        - "Pesquise sobre inteligência artificial"
        - "Crie um documento Word com um relatório"
        
        ### Suporte
        
        Se precisar de ajuda, entre em contato com o suporte.
        """)
        
    except Exception as e:
        st.error(f"Erro ao exibir ajuda: {e}")

def exibir_sobre() -> None:
    """
    Exibe informações sobre a aplicação.
    """
    try:
        st.title("Sobre")
        
        # Exibir informações
        st.write("""
        ## AgenteIA
        
        Um agente de IA inteligente que pode ajudar você com várias tarefas.
        
        ### Funcionalidades
        
        - 🤖 Processamento de linguagem natural
        - 📁 Manipulação de arquivos
        - 📂 Gerenciamento de diretórios
        - 📜 Histórico de mensagens
        - ⚙️ Configurações personalizáveis
        - 🛠️ Ferramentas extensíveis
        
        ### Modelos Disponíveis
        
        - **Geral**
            - qwen3:1.7b
            - qwen3:0.6b
            - qwen3:4b
        
        - **Coder**
            - qwen2.5-coder:3b
        
        ### Ferramentas Disponíveis
        
        - **Arquivos**
            - Criar arquivo
            - Ler arquivo
            - Escrever arquivo
            - Copiar arquivo
            - Mover arquivo
            - Remover arquivo
        
        - **Diretórios**
            - Criar diretório
            - Listar diretório
            - Remover diretório
        
        ### Versão
        
        Versão atual: 1.0.0
        
        ### Desenvolvedor
        
        Desenvolvido por Sr.Africano
        
        ### Licença
        
        Este projeto está licenciado sob a licença MIT.
        
        ### Código Fonte
        
        O código fonte está disponível em: [GitHub](https://github.com/Sr.Africano/agenteia)
        """)
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "system",
            "content": "Informações sobre a aplicação exibidas"
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir informações sobre a aplicação: {e}")

def exibir_configuracoes() -> None:
    """Exibe as configurações do sistema."""
    st.title("⚙️ Configurações")
    
    # Abas para diferentes tipos de configurações
    tab1, tab2, tab3 = st.tabs(["Modelos", "Ferramentas", "Avançado"])
    
    with tab1:
        st.header("Configurações de Modelos")
        
        # Seleção de categoria de modelo
        categoria = st.selectbox(
            "Categoria do Modelo",
            options=list(ModeloType),
            format_func=lambda x: MODELOS_CONFIG[x].nome
        )
        
        # Exibir descrição da categoria
        st.info(MODELOS_CONFIG[categoria].descricao)
        
        # Lista de modelos disponíveis
        modelos_disponiveis = obter_modelos_disponiveis()
        modelos_categoria = [
            m for m in modelos_disponiveis 
            if m in MODELOS_CONFIG[categoria].modelos
        ]
        
        if not modelos_categoria:
            st.warning(f"Nenhum modelo da categoria {MODELOS_CONFIG[categoria].nome} encontrado.")
            if st.button("Baixar Modelos"):
                for modelo in MODELOS_CONFIG[categoria].modelos:
                    try:
                        subprocess.run(["ollama", "pull", modelo], check=True)
                        st.success(f"Modelo {modelo} baixado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao baixar modelo {modelo}: {e}")
        else:
            # Seleção do modelo
            modelo_selecionado = st.selectbox(
                "Modelo",
                options=modelos_categoria,
                index=0
            )
            
            # Configurações específicas do modelo
            st.subheader("Configurações do Modelo")
            max_tokens = st.slider(
                "Máximo de Tokens",
                min_value=1000,
                max_value=8000,
                value=MODELOS_CONFIG[categoria].max_tokens,
                step=1000
            )
            
            temperature = st.slider(
                "Temperature",
                min_value=0.1,
                max_value=1.0,
                value=MODELOS_CONFIG[categoria].temperature,
                step=0.1
            )
            
            if st.button("Aplicar Configurações"):
                st.session_state.modelo = modelo_selecionado
                st.session_state.system_message = MODELOS_CONFIG[categoria].system_message
                st.session_state.max_tokens = max_tokens
                st.session_state.temperature = temperature
                st.success("Configurações aplicadas com sucesso!")
    
    with tab2:
        st.header("Configurações de Ferramentas")
        ferramentas = st.multiselect(
            "Ferramentas Disponíveis",
            options=st.session_state.ferramentas_disponiveis,
            default=st.session_state.ferramentas
        )
        
        if st.button("Aplicar Ferramentas"):
            st.session_state.ferramentas = ferramentas
            st.success("Ferramentas atualizadas com sucesso!")
    
    with tab3:
        st.header("Configurações Avançadas")
        verboso = st.checkbox("Modo Verboso", value=st.session_state.verboso)
        
        if st.button("Aplicar Configurações Avançadas"):
            st.session_state.verboso = verboso
            st.success("Configurações avançadas aplicadas com sucesso!")

def exibir_audio(texto, lang='pt'):
    """
    Gera e exibe áudio da resposta usando gTTS.
    """
    try:
        tts = gTTS(text=texto, lang=lang)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            st.audio(fp.name, format='audio/mp3')
    except Exception as e:
        st.error(f"Erro ao gerar áudio: {e}")

def exibir_menu() -> None:
    """
    Exibe o menu principal da aplicação com navegação e interface aprimoradas.
    """
    try:
        # Configuração da barra lateral
        st.sidebar.title("🤖 AgenteIA")
        
        # Menu principal
        menu = st.sidebar.selectbox(
            "Menu",
            ["Chat", "Tarefas", "Arquivos", "Configurações", "Ajuda", "Sobre"],
            key="menu_principal"
        )
        
        # Seção de gerenciamento na barra lateral
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Gerenciamento")
        
        # Botão para gerenciar tarefas
        if st.sidebar.button("📋 Gerenciar Tarefas", use_container_width=True, key="btn_tarefas"):
            st.switch_page("pages/tarefas.py")
        
        # Seção de status na barra lateral
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Status do Sistema")
        
        # Verificar status do Ollama
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                st.sidebar.success("✅ Ollama está rodando")
            else:
                st.sidebar.error("❌ Ollama não está respondendo")
        except requests.exceptions.RequestException:
            st.sidebar.error("❌ Ollama não está rodando")
        
        # Exibir informações do sistema
        st.sidebar.markdown(f"**Versão:** 1.0.0")
        st.sidebar.markdown(f"**Usuário:** {os.getlogin()}")
        
        # Seção de chat
        if menu == "Chat":
            st.title("💬 Chat com AgenteIA")
            
            # Inicializar histórico se não existir
            inicializar_historico()
            
            # Inicializar estado de processamento se não existir
            if 'is_processing' not in st.session_state:
                st.session_state.is_processing = False
            
            # Container para o chat
            chat_container = st.container()
            
            # Exibir histórico de mensagens
            with chat_container:
                for mensagem in st.session_state.historico:
                    if mensagem["role"] == "user":
                        with st.chat_message("user"):
                            st.markdown(mensagem["content"])
                    elif mensagem["role"] == "assistant":
                        with st.chat_message("assistant"):
                            st.markdown(mensagem["content"])
            
            # Área de entrada de mensagem
            with st.form("chat_form", clear_on_submit=True):
                col1, col2 = st.columns([6, 1])
                with col1:
                    prompt = st.text_input(
                        "Digite sua mensagem:",
                        key="user_input",
                        label_visibility="collapsed",
                        placeholder="Digite sua mensagem aqui..."
                    )
                with col2:
                    submit_button = st.form_submit_button("Enviar", use_container_width=True)
            
            # Processar mensagem quando o formulário for enviado
            if submit_button and prompt:
                if st.session_state.get('is_processing', False):
                    st.warning("⏳ Aguarde, já estou processando uma mensagem...")
                    st.stop()
                
                try:
                    # Adicionar mensagem do usuário ao histórico
                    st.session_state.historico.append({
                        "role": "user",
                        "content": prompt,
                        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    # Exibir a mensagem do usuário imediatamente
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    
                    # Exibir indicador de processamento
                    with st.chat_message("assistant"):
                        with st.spinner("🧠 Processando sua solicitação..."):
                            # Processar a mensagem
                            resposta = processar_mensagem(prompt)
                            
                            # Atualizar o histórico com a resposta
                            st.session_state.historico.append({
                                "role": "assistant",
                                "content": resposta,
                                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            
                            # Exibir a resposta
                            st.markdown(resposta)
                    
                    # Rolar para baixo e forçar atualização
                    scroll_down()
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Erro ao processar mensagem: {str(e)}", exc_info=True)
                    st.error(f"⚠️ Ocorreu um erro ao processar sua mensagem: {str(e)}")
                    st.rerun()
            
            # Adicionar botões de ação rápida
            st.markdown("---")
            st.markdown("### 🚀 Ações Rápidas")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Limpar Chat", use_container_width=True):
                    st.session_state.historico = []
                    st.rerun()
            
            with col2:
                if st.button("📋 Copiar Histórico", use_container_width=True):
                    # Implementar lógica para copiar histórico
                    st.toast("Histórico copiado para a área de transferência!")
            
            with col3:
                if st.button("📥 Exportar Chat", use_container_width=True):
                    # Implementar lógica para exportar chat
                    st.toast("Chat exportado com sucesso!")
        
        # Outras seções do menu
        elif menu == "Arquivos":
            st.title("📁 Gerenciador de Arquivos")
            
            # Criar colunas para o layout
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Seletor de diretório
                diretorio = st.text_input(
                    "Digite o caminho do diretório:", 
                    key="input_diretorio",
                    placeholder="Ex: C:\\Users\\SeuUsuario\\Documentos"
                )
                
                if st.button("📂 Listar Arquivos", use_container_width=True) and diretorio:
                    listar_arquivos_diretorio(diretorio)
            
            with col2:
                st.markdown("### 📌 Atalhos")
                diretorio_projetos = str(Path.home() / "AgenteIA_Projetos")
                documentos = str(Path.home() / "Documents")
                imagens = str(Path.home() / "Pictures")
                downloads = str(Path.home() / "Downloads")
                
                # Usar uma chave única para cada botão para evitar conflitos
                if st.button("📁 Diretório de Projetos", use_container_width=True, key="btn_projetos"):
                    if 'input_diretorio' not in st.session_state or st.session_state.input_diretorio != diretorio_projetos:
                        st.session_state.input_diretorio = diretorio_projetos
                        st.rerun()
                    listar_arquivos_diretorio(diretorio_projetos)
                
                st.markdown("### 📂 Pastas Especiais")
                if st.button("📝 Documentos", use_container_width=True, key="btn_documentos"):
                    if 'input_diretorio' not in st.session_state or st.session_state.input_diretorio != documentos:
                        st.session_state.input_diretorio = documentos
                        st.rerun()
                    listar_arquivos_diretorio(documentos)
                
                if st.button("🖼️ Imagens", use_container_width=True, key="btn_imagens"):
                    if 'input_diretorio' not in st.session_state or st.session_state.input_diretorio != imagens:
                        st.session_state.input_diretorio = imagens
                        st.rerun()
                    listar_arquivos_diretorio(imagens)
                
                if st.button("📊 Downloads", use_container_width=True, key="btn_downloads"):
                    if 'input_diretorio' not in st.session_state or st.session_state.input_diretorio != downloads:
                        st.session_state.input_diretorio = downloads
                        st.rerun()
                    listar_arquivos_diretorio(downloads)
        
        # Adicionar outras seções do menu aqui
        elif menu == "Tarefas":
            st.title("📋 Gerenciador de Tarefas")
            st.info("Esta funcionalidade foi movida para uma página separada. Use o botão na barra lateral para acessar.")
            
        elif menu == "Configurações":
            st.title("⚙️ Configurações")
            st.write("Ajustes e preferências do sistema")
            
            # Adicionar mais opções de configuração aqui
            st.subheader("Configurações Gerais")
            modo_escuro = st.toggle("Modo Escuro", value=False)
            notificacoes = st.toggle("Ativar Notificações", value=True)
            
            st.subheader("Preferências de Exibição")
            tema = st.selectbox(
                "Tema da Interface",
                ["Claro", "Escuro", "Sistema"]
            )
            
            if st.button("Salvar Configurações", type="primary"):
                st.success("Configurações salvas com sucesso!")
            
        elif menu == "Ajuda":
            st.title("❓ Ajuda")
            
            tab1, tab2, tab3 = st.tabs(["📚 Documentação", "❓ FAQ", "📞 Suporte"])
            
            with tab1:
                st.header("Documentação")
                st.markdown("""
                ### Como usar o AgenteIA
                
                1. **Chat**: Converse com o assistente inteligente
                2. **Arquivos**: Gerencie arquivos e pastas
                3. **Tarefas**: Gerencie suas tarefas diárias
                4. **Configurações**: Personalize sua experiência
                
                ### Atalhos Úteis
                - `Ctrl + N`: Nova conversa
                - `Ctrl + S`: Salvar conversa
                - `Esc`: Cancelar operação
                """)
            
            with tab2:
                st.header("Perguntas Frequentes")
                
                with st.expander("Como alterar o modelo de IA?"):
                    st.write("Vá para Configurações > Modelo e selecione o modelo desejado.")
                
                with st.expander("Como exportar o histórico de conversas?"):
                    st.write("Use o botão 'Exportar Chat' na parte inferior da tela de chat.")
                
                with st.expander("O que fazer se o assistente não responder?"):
                    st.write("Tente os seguintes passos:")
                    st.write("1. Verifique sua conexão com a internet")
                    st.write("2. Recarregue a página")
                    st.write("3. Entre em contato com o suporte")
            
            with tab3:
                st.header("Suporte")
                st.write("Entre em contato com nossa equipe de suporte:")
                
                st.markdown("""
                - 📧 Email: suporte@agenteia.com
                - 🌐 Site: [www.agenteia.com/suporte](https://www.agenteia.com/suporte)
                - 📞 Telefone: (11) 1234-5678
                
                **Horário de Atendimento:**
                Segunda a Sexta, das 9h às 18h
                """)
                
        elif menu == "Sobre":
            st.title("ℹ️ Sobre o AgenteIA")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image("https://via.placeholder.com/200", width=200)
            
            with col2:
                st.markdown("""
                ### Versão 1.0.0
                
                **AgenteIA** é um assistente virtual inteligente projetado para ajudar
                em diversas tarefas do dia a dia, desde gerenciamento de arquivos até
                automação de tarefas complexas.
                
                ### Recursos Principais
                - Chat inteligente com IA avançada
                - Gerenciamento de arquivos integrado
                - Automação de tarefas
                - Suporte a múltiplos modelos de linguagem
                
                ### Desenvolvido por
                [Sua Empresa](https://www.suaempresa.com)
                """)
                
                st.markdown("---")
                st.markdown("🔗 [Termos de Uso](https://www.suaempresa.com/termos) | [Política de Privacidade](https://www.suaempresa.com/privacidade)")
        
    except Exception as e:
        logger.error(f"Erro ao exibir menu: {str(e)}", exc_info=True)
        st.error(f"⚠️ Ocorreu um erro ao carregar a interface: {str(e)}")

def exibir_progresso(mensagem: str, progresso: float = None) -> st.delta_generator.DeltaGenerator:
    """
    Exibe uma barra de progresso personalizada.
    
    Args:
        mensagem: Mensagem de progresso a ser exibida
        progresso: Valor do progresso (0-100)
        
    Returns:
        st.delta_generator.DeltaGenerator: Container Streamlit para atualizações futuras
    """
    # Criar container para a barra de progresso
    progress_container = st.empty()
    
    # Atualizar a barra de progresso se o valor for fornecido
    if progresso is not None:
        # Garantir que o progresso está entre 0 e 100
        progresso = max(0, min(100, progresso))
        
        # Criar barra de progresso personalizada com mensagem
        progress_bar = f"""
        <div style='margin: 10px 0;'>
            <div style='display: flex; justify-content: space-between; margin-bottom: 5px;'>
                <span>{mensagem}</span>
                <span>{int(progresso)}%</span>
            </div>
            <div style='width: 100%; background-color: #f0f2f6; border-radius: 4px; overflow: hidden;'>
                <div style='width: {progresso}%; height: 10px; background-color: #1f77b4; 
                             transition: width 0.3s ease-in-out;'></div>
            </div>
        </div>
        """
        progress_container.markdown(progress_bar, unsafe_allow_html=True)
    elif mensagem:
        # Apenas exibir a mensagem se não houver valor de progresso
        progress_container.info(mensagem)
    
    # Retornar o container para atualizações futuras
    return progress_container

def exibir_spinner(mensagem: str) -> None:
    """
    Exibe um spinner de carregamento.
    
    Args:
        mensagem: Mensagem de carregamento
    """
    try:
        # Exibir spinner
        with st.spinner(mensagem):
            time.sleep(0.1)
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "system",
            "content": f"Carregando: {mensagem}",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir spinner: {e}")

def exibir_loading(mensagem: str) -> None:
    """
    Exibe um indicador de carregamento.
    
    Args:
        mensagem: Mensagem de carregamento
    """
    try:
        # Exibir loading
        st.write(f"⏳ {mensagem}")
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "system",
            "content": f"Carregando: {mensagem}",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir loading: {e}")

def exibir_done(mensagem: str) -> None:
    """
    Exibe uma mensagem de conclusão.
    
    Args:
        mensagem: Mensagem de conclusão
    """
    try:
        # Exibir done
        st.write(f"✅ {mensagem}")
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "system",
            "content": f"Concluído: {mensagem}",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir done: {e}")

def exibir_codigo(codigo: str, linguagem: str = "python") -> None:
    """
    Exibe um código.
    
    Args:
        codigo: Código a ser exibido
        linguagem: Linguagem do código
    """
    try:
        # Exibir código
        st.code(codigo, language=linguagem)
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "system",
            "content": f"Código ({linguagem}):\n```{linguagem}\n{codigo}\n```",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir código: {e}")

def exibir_json(json_data: dict) -> None:
    """
    Exibe um objeto JSON.
    
    Args:
        json_data: Objeto JSON a ser exibido
    """
    try:
        # Exibir JSON
        st.json(json_data)
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "system",
            "content": f"JSON:\n```json\n{json.dumps(json_data, indent=4)}\n```",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir JSON: {e}")

def exibir_tabela(dados: pd.DataFrame) -> None:
    """
    Exibe uma tabela.
    
    Args:
        dados: Dados da tabela
    """
    try:
        # Exibir tabela
        st.dataframe(dados)
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "system",
            "content": f"Tabela:\n{dados.to_string()}",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir tabela: {e}")

def exibir_grafico(dados: pd.DataFrame, tipo: str = "linha", x: str = None, y: str = None) -> None:
    """
    Exibe um gráfico.
    
    Args:
        dados: Dados do gráfico
        tipo: Tipo do gráfico (linha, barra, pizza)
        x: Coluna do eixo x
        y: Coluna do eixo y
    """
    try:
        # Exibir gráfico
        if tipo == "linha":
            st.line_chart(dados)
        elif tipo == "barra":
            st.bar_chart(dados)
        elif tipo == "pizza":
            st.pie_chart(dados)
        else:
            st.error(f"Tipo de gráfico não suportado: {tipo}")
            return
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "system",
            "content": f"Gráfico ({tipo}):\nEixo X: {x}\nEixo Y: {y}",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir gráfico: {e}")

def exibir_arquivo(caminho: str) -> None:
    """
    Exibe o conteúdo de um arquivo.
    
    Args:
        caminho: Caminho do arquivo
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(caminho):
            st.error(f"Arquivo não encontrado: {caminho}")
            return
        
        # Ler o arquivo
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
        
        # Exibir o conteúdo
        st.text_area("Conteúdo do arquivo", conteudo, height=400)
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "system",
            "content": f"Arquivo: {caminho}\n```\n{conteudo}\n```",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir arquivo: {e}")

def exibir_arquivo_binario(caminho: str) -> None:
    """
    Exibe um arquivo binário.
    
    Args:
        caminho: Caminho do arquivo
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(caminho):
            st.error(f"Arquivo não encontrado: {caminho}")
            return
        
        # Ler arquivo
        with open(caminho, "rb") as f:
            conteudo = f.read()
        
        # Exibir conteúdo
        st.download_button(
            label="Baixar Arquivo",
            data=conteudo,
            file_name=os.path.basename(caminho),
            mime="application/octet-stream"
        )
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "assistant",
            "content": f"Arquivo binário {caminho} disponível para download"
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir arquivo binário: {e}")

def exibir_arquivo_texto(caminho: str) -> None:
    """
    Exibe um arquivo de texto.
    
    Args:
        caminho: Caminho do arquivo
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(caminho):
            st.error(f"Arquivo não encontrado: {caminho}")
            return
        
        # Ler arquivo
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
        
        # Exibir conteúdo
        st.text_area(
            label="Conteúdo do Arquivo",
            value=conteudo,
            height=400
        )
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "assistant",
            "content": f"Conteúdo do arquivo de texto {caminho}:\n{conteudo}"
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir arquivo de texto: {e}")

def exibir_arquivo_imagem(caminho: str) -> None:
    """
    Exibe uma imagem.
    
    Args:
        caminho: Caminho da imagem
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(caminho):
            st.error(f"Imagem não encontrada: {caminho}")
            return
        
        # Exibir imagem
        st.image(caminho)
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "assistant",
            "content": f"Imagem {caminho} exibida"
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir imagem: {e}")

def exibir_diretorio(caminho: str) -> None:
    """
    Exibe o conteúdo de um diretório.
    
    Args:
        caminho: Caminho do diretório
    """
    try:
        # Verificar se o diretório existe
        if not os.path.exists(caminho):
            st.error(f"Diretório não encontrado: {caminho}")
            return
        
        # Listar arquivos e diretórios
        arquivos = []
        diretorios = []
        
        for item in os.listdir(caminho):
            item_path = os.path.join(caminho, item)
            if os.path.isfile(item_path):
                arquivos.append(item)
            else:
                diretorios.append(item)
        
        # Exibir diretórios
        if diretorios:
            st.subheader("Diretórios")
            for diretorio in sorted(diretorios):
                st.write(f"📁 {diretorio}")
        
        # Exibir arquivos
        if arquivos:
            st.subheader("Arquivos")
            for arquivo in sorted(arquivos):
                st.write(f"📄 {arquivo}")
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "system",
            "content": f"Diretório: {caminho}\nDiretórios: {', '.join(diretorios)}\nArquivos: {', '.join(arquivos)}",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir diretório: {e}")

def exibir_diretorio_arvore(caminho: str) -> None:
    """
    Exibe a estrutura de diretórios em formato de árvore.
    
    Args:
        caminho: Caminho do diretório raiz
    """
    try:
        # Verificar se o diretório existe
        if not os.path.exists(caminho):
            st.error(f"Diretório não encontrado: {caminho}")
            return
        
        # Função auxiliar para gerar árvore
        def gerar_arvore(dir_path, prefix=""):
            tree = []
            items = os.listdir(dir_path)
            items.sort(key=str.lower)
            
            for i, item in enumerate(items):
                item_path = os.path.join(dir_path, item)
                is_last = i == len(items) - 1
                
                if os.path.isfile(item_path):
                    tree.append(f"{prefix}{'└── ' if is_last else '├── '}📄 {item}")
                else:
                    tree.append(f"{prefix}{'└── ' if is_last else '├── '}📁 {item}")
                    if os.path.isdir(item_path):
                        tree.extend(gerar_arvore(item_path, prefix + ("    " if is_last else "│   ")))
            
            return tree
        
        # Gerar e exibir árvore
        arvore = gerar_arvore(caminho)
        st.code("\n".join(arvore))
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "assistant",
            "content": f"Estrutura de diretórios em {caminho}:\n```\n" + "\n".join(arvore) + "\n```"
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir estrutura de diretórios: {e}")

def exibir_diretorio_tabela(caminho: str) -> None:
    """
    Exibe o conteúdo de um diretório em formato de tabela.
    
    Args:
        caminho: Caminho do diretório
    """
    try:
        # Verificar se o diretório existe
        if not os.path.exists(caminho):
            st.error(f"Diretório não encontrado: {caminho}")
            return
        
        # Listar arquivos e diretórios
        items = []
        
        for item in os.listdir(caminho):
            item_path = os.path.join(caminho, item)
            items.append({
                "Nome": item,
                "Tipo": "Diretório" if os.path.isdir(item_path) else "Arquivo",
                "Tamanho": "-" if os.path.isdir(item_path) else f"{os.path.getsize(item_path)} bytes",
                "Modificado": datetime.fromtimestamp(os.path.getmtime(item_path)).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Ordenar por nome
        items.sort(key=lambda x: x["Nome"].lower())
        
        # Exibir tabela
        st.dataframe(items)
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "assistant",
            "content": f"Conteúdo do diretório {caminho} em formato de tabela"
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir diretório em formato de tabela: {e}")

def exibir_historico() -> None:
    """
    Exibe o histórico de mensagens.
    """
    try:
        # Verificar se há histórico
        if not st.session_state.historico:
            st.info("Nenhuma mensagem no histórico")
            return
        
        # Exibir histórico
        for msg in st.session_state.historico:
            if msg["role"] == "user":
                st.write(f"👤 **Você:** {msg['content']}")
            elif msg["role"] == "assistant":
                st.write(f"🤖 **Assistente:** {msg['content']}")
            elif msg["role"] == "system":
                st.write(f"⚙️ **Sistema:** {msg['content']}")
            elif msg["role"] == "error":
                st.error(msg["content"])
            elif msg["role"] == "success":
                st.success(msg["content"])
            elif msg["role"] == "info":
                st.info(msg["content"])
            elif msg["role"] == "warning":
                st.warning(msg["content"])
            else:
                st.write(f"**{msg['role']}:** {msg['content']}")
            
            st.markdown("---")
        
    except Exception as e:
        st.error(f"Erro ao exibir histórico: {e}")

def exibir_historico_filtrado(filtro: str) -> None:
    """
    Exibe o histórico de mensagens filtrado.
    
    Args:
        filtro: Filtro para as mensagens
    """
    try:
        # Verificar se há histórico
        if not st.session_state.historico:
            st.info("Nenhuma mensagem no histórico")
            return
        
        # Filtrar histórico
        historico_filtrado = [
            msg for msg in st.session_state.historico
            if filtro.lower() in msg["content"].lower()
        ]
        
        # Verificar se há mensagens filtradas
        if not historico_filtrado:
            st.info(f"Nenhuma mensagem encontrada com o filtro: {filtro}")
            return
        
        # Exibir histórico filtrado
        for msg in historico_filtrado:
            if msg["role"] == "user":
                st.write(f"👤 **Você:** {msg['content']}")
            elif msg["role"] == "assistant":
                st.write(f"🤖 **Assistente:** {msg['content']}")
            elif msg["role"] == "system":
                st.write(f"⚙️ **Sistema:** {msg['content']}")
            elif msg["role"] == "error":
                st.error(msg["content"])
            elif msg["role"] == "success":
                st.success(msg["content"])
            elif msg["role"] == "info":
                st.info(msg["content"])
            elif msg["role"] == "warning":
                st.warning(msg["content"])
            else:
                st.write(f"**{msg['role']}:** {msg['content']}")
            
            st.markdown("---")
        
    except Exception as e:
        st.error(f"Erro ao exibir histórico filtrado: {e}")

def exibir_historico_por_tipo(tipo: str) -> None:
    """
    Exibe o histórico de mensagens por tipo.
    
    Args:
        tipo: Tipo de mensagem (user, assistant, system, error, success, info, warning)
    """
    try:
        # Verificar se há histórico
        if not st.session_state.historico:
            st.info("Nenhuma mensagem no histórico")
            return
        
        # Filtrar histórico por tipo
        historico_filtrado = [
            msg for msg in st.session_state.historico
            if msg["role"] == tipo
        ]
        
        # Verificar se há mensagens do tipo
        if not historico_filtrado:
            st.info(f"Nenhuma mensagem do tipo: {tipo}")
            return
        
        # Exibir histórico filtrado
        for msg in historico_filtrado:
            if tipo == "user":
                st.write(f"👤 **Você:** {msg['content']}")
            elif tipo == "assistant":
                st.write(f"🤖 **Assistente:** {msg['content']}")
            elif tipo == "system":
                st.write(f"⚙️ **Sistema:** {msg['content']}")
            elif tipo == "error":
                st.error(msg["content"])
            elif tipo == "success":
                st.success(msg["content"])
            elif tipo == "info":
                st.info(msg["content"])
            elif tipo == "warning":
                st.warning(msg["content"])
            else:
                st.write(f"**{tipo}:** {msg['content']}")
            
            st.markdown("---")
        
    except Exception as e:
        st.error(f"Erro ao exibir histórico por tipo: {e}")

def exibir_historico_por_data(data: str) -> None:
    """
    Exibe o histórico de mensagens por data.
    
    Args:
        data: Data no formato YYYY-MM-DD
    """
    try:
        # Verificar se há histórico
        if not st.session_state.historico:
            st.info("Nenhuma mensagem no histórico")
            return
        
        # Filtrar histórico por data
        historico_filtrado = [
            msg for msg in st.session_state.historico
            if msg.get("data", "").startswith(data)
        ]
        
        # Verificar se há mensagens da data
        if not historico_filtrado:
            st.info(f"Nenhuma mensagem da data: {data}")
            return
        
        # Exibir histórico filtrado
        for msg in historico_filtrado:
            if msg["role"] == "user":
                st.write(f"👤 **Você:** {msg['content']}")
            elif msg["role"] == "assistant":
                st.write(f"🤖 **Assistente:** {msg['content']}")
            elif msg["role"] == "system":
                st.write(f"⚙️ **Sistema:** {msg['content']}")
            elif msg["role"] == "error":
                st.error(msg["content"])
            elif msg["role"] == "success":
                st.success(msg["content"])
            elif msg["role"] == "info":
                st.info(msg["content"])
            elif msg["role"] == "warning":
                st.warning(msg["content"])
            else:
                st.write(f"**{msg['role']}:** {msg['content']}")
            
            st.markdown("---")
        
    except Exception as e:
        st.error(f"Erro ao exibir histórico por data: {e}")

def exibir_versao() -> None:
    """
    Exibe a versão da aplicação.
    """
    try:
        st.title("Versão")
        
        # Exibir informações da versão
        st.write("""
        ## AgenteIA
        
        ### Versão Atual
        
        - **Versão**: 1.0.0
        - **Data**: 2024-03-20
        - **Autor**: Sr.Africano
        
        ### Histórico de Versões
        
        #### Versão 1.0.0 (2024-03-20)
        
        - 🎉 Lançamento inicial
        - 🤖 Suporte a modelos de linguagem
        - 📁 Manipulação de arquivos
        - 📂 Gerenciamento de diretórios
        - 📜 Histórico de mensagens
        - ⚙️ Configurações personalizáveis
        - 🛠️ Ferramentas extensíveis
        
        ### Próximas Versões
        
        #### Versão 1.1.0 (Em desenvolvimento)
        
        - 🔄 Atualização dos modelos
        - 🎨 Interface aprimorada
        - 📊 Estatísticas de uso
        - 🔍 Busca avançada
        - 📱 Suporte a dispositivos móveis
        
        #### Versão 1.2.0 (Planejada)
        
        - 🌐 Suporte a múltiplos idiomas
        - 🎯 Modos de operação
        - 📈 Gráficos e visualizações
        - 🔐 Autenticação e autorização
        - 📦 Pacotes e extensões
        
        ### Tecnologias
        
        - **Python**: 3.10.0
        - **Streamlit**: 1.31.0
        - **Ollama**: 0.1.0
        - **LangChain**: 0.1.0
        
        ### Requisitos
        
        - Python 3.10 ou superior
        - 4GB de RAM
        - 1GB de espaço em disco
        - Conexão com a internet
        
        ### Instalação
        
        ```bash
        pip install agenteia
        ```
        
        ### Atualização
        
        ```bash
        pip install --upgrade agenteia
        ```
        
        ### Desinstalação
        
        ```bash
        pip uninstall agenteia
        ```
        """)
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "system",
            "content": "Informações da versão exibidas"
        })
        
    except Exception as e:
        st.error(f"Erro ao exibir informações da versão: {e}")

def verificar_ollama() -> bool:
    """
    Verifica se o serviço Ollama está disponível.
    
    Returns:
        bool: True se o serviço estiver disponível, False caso contrário
    """
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def log_request(mensagem: str, modelo: str, status: str, detalhes: str = None) -> None:
    """
    Registra informações detalhadas sobre uma requisição.
    
    Args:
        mensagem: Mensagem original
        modelo: Modelo usado
        status: Status da requisição (inicio, sucesso, erro)
        detalhes: Detalhes adicionais
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "mensagem": mensagem[:100] + "..." if len(mensagem) > 100 else mensagem,
        "modelo": modelo,
        "status": status,
        "detalhes": detalhes
    }
    logger.info(f"Requisição: {json.dumps(log_entry, ensure_ascii=False)}")

def processar_fila() -> None:
    """
    Processa a fila de requisições em uma thread separada.
    """
    while True:
        try:
            # Obter próxima requisição da fila
            request = request_queue.get()
            if request is None:
                break
                
            request_id, mensagem, modelo, callback = request
            
            # Verificar se a requisição ainda é válida
            if request_id not in request_status:
                request_queue.task_done()
                continue
            
            # Verificar se já existe uma requisição ativa para esta mensagem
            if mensagem in active_requests:
                logger.info(f"Requisição duplicada ignorada: {mensagem[:50]}...")
                request_queue.task_done()
                continue
                
            # Processar requisição
            with processing_lock:
                try:
                    # Marcar requisição como ativa
                    active_requests.add(mensagem)
                    
                    # Registrar início da requisição
                    log_request(mensagem, modelo, "inicio")
                    
                    # Processar mensagem
                    resposta = processar_mensagem_modelo(mensagem, modelo)
                    
                    # Registrar sucesso
                    log_request(mensagem, modelo, "sucesso")
                    
                    # Executar callback se a requisição ainda existir
                    if request_id in request_status:
                        callback(resposta)
                        del request_status[request_id]
                        
                except Exception as e:
                    # Registrar erro
                    log_request(mensagem, modelo, "erro", str(e))
                    
                    # Executar callback com erro se a requisição ainda existir
                    if request_id in request_status:
                        callback(f"Erro ao processar mensagem: {e}")
                        del request_status[request_id]
                        
                finally:
                    # Remover requisição da lista de ativas
                    active_requests.discard(mensagem)
                    
            # Marcar tarefa como concluída
            request_queue.task_done()
            
        except Exception as e:
            logger.error(f"Erro ao processar fila: {e}")
            time.sleep(1)  # Esperar um pouco antes de tentar novamente

# Iniciar thread de processamento
queue_thread = threading.Thread(target=processar_fila, daemon=True)
queue_thread.start()

def verificar_status_modelo(modelo: str) -> dict:
    """
    Verifica o status do modelo no Ollama.
    
    Args:
        modelo: Nome do modelo
    
    Returns:
        dict: Status do modelo
    """
    try:
        # Primeiro tenta verificar via API de tags
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=5
        )
        
        if response.status_code == 200:
            dados = response.json()
            if "models" in dados:
                for m in dados["models"]:
                    if m["name"] == modelo:
                        return {"status": "ok", "model": m}
        
        # Se não encontrar, tenta via API de show
        response = requests.get(
            f"http://localhost:11434/api/show",
            json={"name": modelo},
            timeout=5
        )
        
        if response.status_code == 200:
            return {"status": "ok", "model": response.json()}
            
        return {"status": "error", "message": "Modelo não encontrado"}
    except Exception as e:
        logger.error(f"Erro ao verificar status do modelo: {e}")
        return {"status": "error", "message": str(e)}

def verificar_modelo_ocupado(modelo: str) -> bool:
    """
    Verifica se o modelo está ocupado processando outra requisição.
    
    Args:
        modelo: Nome do modelo
    
    Returns:
        bool: True se o modelo estiver ocupado
    """
    try:
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=5
        )
        
        if response.status_code == 200:
            dados = response.json()
            if "models" in dados:
                for m in dados["models"]:
                    if m["name"] == modelo:
                        return m.get("status", "") == "generating"
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar se modelo está ocupado: {e}")
        return False

def aguardar_modelo_disponivel(modelo: str, timeout: int = 300) -> bool:
    """
    Aguarda até que o modelo esteja disponível.
    
    Args:
        modelo: Nome do modelo
        timeout: Tempo máximo de espera em segundos
    
    Returns:
        bool: True se o modelo ficou disponível
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not verificar_modelo_ocupado(modelo):
            return True
        time.sleep(1)
    return False

def obter_clima(cidade: str, pais: str) -> str:
    """
    Obtém informações sobre o clima de uma cidade.
    
    Args:
        cidade: Nome da cidade
        pais: Nome do país
    
    Returns:
        str: Informações sobre o clima
    """
    try:
        # Usar a API OpenWeatherMap
        api_key = "80ede01e72d10ce73fa940c4dcfb929dc"  # Substitua pela sua chave API
        url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade},{pais}&appid={api_key}&units=metric&lang=pt_br"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            
            # Extrair informações relevantes
            temperatura = dados["main"]["temp"]
            descricao = dados["weather"][0]["description"]
            umidade = dados["main"]["humidity"]
            vento = dados["wind"]["speed"]
            
            return f"""
            🌡️ Clima em {cidade}, {pais}:
            
            Temperatura: {temperatura}°C
            Condição: {descricao}
            Umidade: {umidade}%
            Velocidade do vento: {vento} m/s
            """
        else:
            return f"Erro ao obter informações do clima: {response.status_code}"
    except Exception as e:
        logger.error(f"Erro ao obter clima: {e}")
        return f"Erro ao obter informações do clima: {e}"

def sanitizar_json(input_str: str) -> str:
    """
    Sanitiza uma string JSON para garantir que seja válida.
    
    Args:
        input_str: String JSON a ser sanitizada
    
    Returns:
        str: String JSON sanitizada
    """
    try:
        # Primeira tentativa: parse direto
        json.loads(input_str)
        return input_str
    except json.JSONDecodeError:
        # Segunda tentativa: substituições básicas
        sanitized = input_str
        sanitized = sanitized.replace("'", '"')  # Aspas simples para duplas
        sanitized = sanitized.replace("\n", "\\n")  # Quebras de linha
        sanitized = sanitized.replace("\r", "\\r")  # Retornos
        sanitized = sanitized.replace("\t", "\\t")  # Tabs
        sanitized = sanitized.replace("/n", "\\n")  # Quebras de linha no formato /n
        sanitized = sanitized.replace("/r", "\\r")  # Retornos no formato /r
        sanitized = sanitized.replace("/t", "\\t")  # Tabs no formato /t
        
        # Escapar aspas dentro de strings
        sanitized = re.sub(r'(?<!\\)"([^"]*?)(?<!\\)"', r'"\1"', sanitized)
        
        # Remover caracteres de controle
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
        
        try:
            # Tentar parse novamente
            json.loads(sanitized)
            return sanitized
        except json.JSONDecodeError:
            # Terceira tentativa: reconstruir o JSON
            try:
                # Extrair caminho e conteúdo
                caminho_match = re.search(r'"caminho"\s*:\s*"([^"]+)"', sanitized)
                conteudo_match = re.search(r'"conteudo"\s*:\s*"([^"]+)"', sanitized)
                
                if caminho_match and conteudo_match:
                    caminho = caminho_match.group(1)
                    conteudo = conteudo_match.group(1)
                    
                    # Reconstruir JSON
                    return json.dumps({
                        "caminho": caminho,
                        "conteudo": conteudo
                    })
            except Exception:
                pass
            
            # Se todas as tentativas falharem, retornar None
            return None

# def processar_mensagem_modelo(mensagem: str, modelo: str) -> str:
#     """
#     Processa uma mensagem com um modelo específico.
#     
#     Args:
#         mensagem: Mensagem do usuário
#         modelo: Nome do modelo
#     
#     Returns:
#         Resposta do modelo
#     """
#     # Configurações de retry
#     max_retries = 3
#     retry_delay = 5  # Aumentado para 5 segundos
#     request_timeout = 180  # Será sobrescrito pelo timeout do modelo
#     
#     try:
#         # Verificar se o Ollama está disponível
#         if not verificar_ollama():
#             log_request(mensagem, modelo, "erro", "Ollama não disponível")
#             return "Erro: O serviço Ollama não está disponível. Por favor, verifique se o Ollama está rodando e tente novamente."
#         
#         # Verificar status do modelo
#         status = verificar_status_modelo(modelo)
#         if status["status"] == "error":
#             logger.warning(f"Modelo {modelo} não encontrado, tentando continuar mesmo assim")
#         
#         # Determinar categoria e configuração do modelo
#         categoria = None
#         for cat, config in MODELOS_CONFIG.items():
#             if modelo in config.modelos:
#                 categoria = cat
#                 request_timeout = config.timeout
#                 break
#         
#         if categoria is None:
#             logger.warning(f"Modelo {modelo} não encontrado nas configurações, usando timeout padrão")
#         
#         # Verificar se é uma solicitação de criação de código
#         is_programming = any(keyword in mensagem.lower() for keyword in ["criar", "desenvolver", "fazer", "implementar", "código", "programa", "site", "aplicação"])
#         
#         if is_programming:
#             # Usar o modelo coder
#             modelo = "qwen2.5-coder:3b"
#             request_timeout = MODELOS_CONFIG[ModeloType.CODER].timeout
#             
#             # Criar diretório do projeto usando Path para lidar corretamente com caminhos
#             diretorio_projeto = Path.home() / "AgenteIA_Projetos" / f"projeto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
#             diretorio_projeto = str(diretorio_projeto).replace("\\\\", "/")
#             os.makedirs(diretorio_projeto, exist_ok=True)
#             
#             # Preparar mensagem para o Ollama com instruções mais claras sobre JSON
#             prompt = f"""
#             {system_message}
#             
#             Usuário: {mensagem}
#             
#             Por favor, crie um projeto completo em {diretorio_projeto} com todos os arquivos necessários.
#             Você DEVE usar o formato de ações para criar os arquivos e diretórios.
#             NÃO apenas descreva o código, CRIE os arquivos usando as ações.
#             
#             IMPORTANTE: 
#             1. Use barras normais (/) nos caminhos, não use barras invertidas (\\\\)
#             2. O JSON deve ser válido e bem formatado
#             3. Escape caracteres especiais no conteúdo dos arquivos
#             4. Use aspas duplas para strings no JSON
#             5. Não use quebras de linha no JSON
#             6. Use \\\\n para quebras de linha no conteúdo
#             7. Escape todas as aspas dentro do conteúdo com \\\\\\\
#             """
#         else:
#             prompt = f"{system_message}\\n\\nUsuário: {mensagem}"
#         
#         logger.info(f"Usando timeout de {request_timeout} segundos para o modelo {modelo}")
#         
#         # Chamar o Ollama com retry
#         last_error = None
#         for attempt in range(max_retries):
#             try:
#                 start_time = datetime.now()
#                 response = requests.post(
#                     "http://localhost:11434/api/generate",
#                     json={
#                         "model": modelo,
#                         "prompt": prompt,
#                         "stream": False
#                     },
#                     timeout=request_timeout
#                 )
#                 end_time = datetime.now()
#                 duration = (end_time - start_time).total_seconds()
#                 
#                 logger.info(f"Requisição concluída em {duration:.2f} segundos")
#                 
#                 if response.status_code == 200:
#                     resposta = response.json()["response"]
#                     logger.info(f"Resposta do modelo: {resposta[:200]}...")
#                     
#                     # Se for uma solicitação de código, processar ações
#                     if is_programming:
#                         # Processar ações na resposta
#                         linhas = resposta.split("\\n")
#                         arquivos_criados = []
#                         diretorios_criados = []
#                         
#                         for i, linha in enumerate(linhas):
#                             if linha.startswith("Action:"):
#                                 acao = linha.split("Action:")[1].strip()
#                                 if i + 1 < len(linhas) and linhas[i + 1].startswith("Action Input:"):
#                                     try:
#                                         # Extrair e limpar o JSON
#                                         input_str = linhas[i + 1].split("Action Input:")[1].strip()
#                                         input_str = input_str.replace("\\\\", "/")
#                                         
#                                         # Sanitizar JSON
#                                         sanitized_json_str = sanitizar_json(input_str) # Renamed to avoid conflict
#                                         if sanitized_json_str is None:
#                                             logger.error(f"Não foi possível sanitizar o JSON: {input_str}")
#                                             continue
#                                             
#                                         parametros = json.loads(sanitized_json_str)
#                                         
#                                         # Validar parâmetros obrigatórios
#                                         if acao == "criar_diretorio":
#                                             if "caminho" not in parametros:
#                                                 logger.error("Parâmetro 'caminho' não encontrado para criar_diretorio")
#                                                 continue
#                                             
#                                             os.makedirs(parametros["caminho"], exist_ok=True)
#                                             diretorios_criados.append(parametros["caminho"])
#                                             logger.info(f"Diretório criado: {parametros['caminho']}")
#                                             
#                                         elif acao == "escrever_arquivo":
#                                             if "caminho" not in parametros or "conteudo" not in parametros:
#                                                 logger.error("Parâmetros 'caminho' ou 'conteudo' não encontrados para escrever_arquivo")
#                                                 continue
#                                             
#                                             # Criar diretório pai se não existir
#                                             os.makedirs(os.path.dirname(parametros["caminho"]), exist_ok=True)
#                                             
#                                             # Escrever arquivo
#                                             with open(parametros["caminho"], "w", encoding="utf-8") as f:
#                                                 f.write(parametros["conteudo"])
#                                             arquivos_criados.append(parametros["caminho"])
#                                             logger.info(f"Arquivo criado: {parametros['caminho']}")
#                                             
#                                     except Exception as e:
#                                         logger.error(f"Erro ao executar ação {acao}: {str(e)}")
#                                         continue
#                         
#                         # Adicionar informações do projeto
#                         resposta = f"""
#                         Projeto criado com sucesso em: {diretorio_projeto}
# 
#                         Diretórios criados:
#                         {chr(10).join(f'- {d}' for d in diretorios_criados)}
# 
#                         Arquivos criados:
#                         {chr(10).join(f'- {f}' for f in arquivos_criados)}
# 
#                         Para executar o projeto, siga as instruções no arquivo README.md
#                         """
#                     
#                     log_request(mensagem, modelo, "sucesso", resposta) # Logar sucesso
#                     return resposta
#                     
#             except Exception as e:
#                 last_error = e
#                 logger.error(f"Erro na tentativa {attempt + 1}: {str(e)}")
#                 if attempt < max_retries - 1:
#                     time.sleep(retry_delay)
#         
#         # Se todas as tentativas falharem, retornar o último erro
#         error_msg = f"Falha ao processar mensagem após {max_retries} tentativas: {str(last_error)}"
#         logger.critical(error_msg)
#         log_request(mensagem, modelo, "erro", error_msg)
#         return f"Erro ao processar mensagem: {error_msg}\\n"
#     
#     Args:
#         mensagem: Mensagem do usuário
#         modelo: Nome do modelo
#     
#     Returns:
#         Resposta do modelo
#     """
#     # Configurações de retry
#     max_retries = 3
#     retry_delay = 5  # Aumentado para 5 segundos
#     request_timeout = 180  # Será sobrescrito pelo timeout do modelo
#     
#     try:
#         # Verificar se o Ollama está disponível
#         if not verificar_ollama():
#             log_request(mensagem, modelo, "erro", "Ollama não disponível")
#             return "Erro: O serviço Ollama não está disponível. Por favor, verifique se o Ollama está rodando e tente novamente."
#         
#         # Verificar status do modelo
#         status = verificar_status_modelo(modelo)
#         if status["status"] == "error":
#             logger.warning(f"Modelo {modelo} não encontrado, tentando continuar mesmo assim")
#         
#         # Determinar categoria e configuração do modelo
#         categoria = None
#         for cat, config in MODELOS_CONFIG.items():
#             if modelo in config.modelos:
#                 categoria = cat
#                 request_timeout = config.timeout
#                 break
#         
#         if categoria is None:
#             logger.warning(f"Modelo {modelo} não encontrado nas configurações, usando timeout padrão")
#         
#         # Verificar se é uma solicitação de criação de código
#         is_programming = any(keyword in mensagem.lower() for keyword in ["criar", "desenvolver", "fazer", "implementar", "código", "programa", "site", "aplicação"])
#         
#         if is_programming:
#             # Usar o modelo coder
#             modelo = "qwen2.5-coder:3b"
#             request_timeout = MODELOS_CONFIG[ModeloType.CODER].timeout
#             
#             # Criar diretório do projeto usando Path para lidar corretamente com caminhos
#             diretorio_projeto = Path.home() / "AgenteIA_Projetos" / f"projeto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
#             diretorio_projeto = str(diretorio_projeto).replace("\\\\", "/")
#             os.makedirs(diretorio_projeto, exist_ok=True)
#             
#             # Preparar mensagem para o Ollama com instruções mais claras sobre JSON
#             prompt = f"""
#             {system_message}
#             
#             Usuário: {mensagem}
#             
#             Por favor, crie um projeto completo em {diretorio_projeto} com todos os arquivos necessários.
#             Você DEVE usar o formato de ações para criar os arquivos e diretórios.
#             NÃO apenas descreva o código, CRIE os arquivos usando as ações.
#             
#             IMPORTANTE: 
#             1. Use barras normais (/) nos caminhos, não use barras invertidas (\\\\)
#             2. O JSON deve ser válido e bem formatado
#             3. Escape caracteres especiais no conteúdo dos arquivos
#             4. Use aspas duplas para strings no JSON
#             5. Não use quebras de linha no JSON
#             6. Use \\\\n para quebras de linha no conteúdo
#             7. Escape todas as aspas dentro do conteúdo com \\\\\\\
#             """
#         else:
#             prompt = f"{system_message}\\n\\nUsuário: {mensagem}"
#         
#         logger.info(f"Usando timeout de {request_timeout} segundos para o modelo {modelo}")
#         
#         # Chamar o Ollama com retry
#         last_error = None
#         for attempt in range(max_retries):
#             try:
#                 start_time = datetime.now()
#                 response = requests.post(
#                     "http://localhost:11434/api/generate",
#                     json={
#                         "model": modelo,
#                         "prompt": prompt,
#                         "stream": False
#                     },
#                     timeout=request_timeout
#                 )
#                 end_time = datetime.now()
#                 duration = (end_time - start_time).total_seconds()
#                 
#                 logger.info(f"Requisição concluída em {duration:.2f} segundos")
#                 
#                 if response.status_code == 200:
#                     resposta = response.json()["response"]
#                     logger.info(f"Resposta do modelo: {resposta[:200]}...")
#                     
#                     # Se for uma solicitação de código, processar ações
#                     if is_programming:
#                         # Processar ações na resposta
#                         linhas = resposta.split("\\n")
#                         arquivos_criados = []
#                         diretorios_criados = []
#                         
#                         for i, linha in enumerate(linhas):
#                             if linha.startswith("Action:"):
#                                 acao = linha.split("Action:")[1].strip()
#                                 if i + 1 < len(linhas) and linhas[i + 1].startswith("Action Input:"):
#                                     try:
#                                         # Extrair e limpar o JSON
#                                         input_str = linhas[i + 1].split("Action Input:")[1].strip()
#                                         input_str = input_str.replace("\\\\", "/")
#                                         
#                                         # Sanitizar JSON
#                                         sanitized_json_str = sanitizar_json(input_str) # Renamed to avoid conflict
#                                         if sanitized_json_str is None:
#                                             logger.error(f"Não foi possível sanitizar o JSON: {input_str}")
#                                             continue
#                                             
#                                         parametros = json.loads(sanitized_json_str)
#                                         
#                                         # Validar parâmetros obrigatórios
#                                         if acao == "criar_diretorio":
#                                             if "caminho" not in parametros:
#                                                 logger.error("Parâmetro 'caminho' não encontrado para criar_diretorio")
#                                                 continue
#                                             
#                                             os.makedirs(parametros["caminho"], exist_ok=True)
#                                             diretorios_criados.append(parametros["caminho"])
#                                             logger.info(f"Diretório criado: {parametros['caminho']}")
#                                             
#                                         elif acao == "escrever_arquivo":
#                                             if "caminho" not in parametros or "conteudo" not in parametros:
#                                                 logger.error("Parâmetros 'caminho' ou 'conteudo' não encontrados para escrever_arquivo")
#                                                 continue
#                                             
#                                             # Criar diretório pai se não existir
#                                             os.makedirs(os.path.dirname(parametros["caminho"]), exist_ok=True)
#                                             
#                                             # Escrever arquivo
#                                             with open(parametros["caminho"], "w", encoding="utf-8") as f:
#                                                 f.write(parametros["conteudo"])
#                                             arquivos_criados.append(parametros["caminho"])
#                                             logger.info(f"Arquivo criado: {parametros['caminho']}")
#                                             
#                                     except Exception as e:
#                                         logger.error(f"Erro ao executar ação {acao}: {str(e)}")
#                                         continue
#                         
#                         # Adicionar informações do projeto
#                         resposta = f"""
#                         Projeto criado com sucesso em: {diretorio_projeto}
# 
#                         Diretórios criados:
#                         {chr(10).join(f'- {d}' for d in diretorios_criados)}
# 
#                         Arquivos criados:
#                         {chr(10).join(f'- {f}' for f in arquivos_criados)}
# 
#                         Para executar o projeto, siga as instruções no arquivo README.md
#                         """
#                     
#                     log_request(mensagem, modelo, "sucesso", resposta) # Logar sucesso
#                     return resposta
#                     
#             except Exception as e:
#                 last_error = e
#                 logger.error(f"Erro na tentativa {attempt + 1}: {str(e)}")
#                 if attempt < max_retries - 1:
#                     time.sleep(retry_delay)
#         
#         # Se todas as tentativas falharem, retornar o último erro
#         error_msg = f"Falha ao processar mensagem após {max_retries} tentativas: {str(last_error)}"
#         logger.critical(error_msg)
#         log_request(mensagem, modelo, "erro", error_msg)
#         return f"Erro ao processar mensagem: {error_msg}\\n"

def processar_mensagem(mensagem: str) -> str:
    """
    Processa uma mensagem do usuário usando AgenteIA.
    
    Args:
        mensagem: Mensagem do usuário
    
    Returns:
        str: Resposta processada pelo AgenteIA
    """
    # Inicializar estado de processamento e progresso se não existirem
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False
    if 'progresso' not in st.session_state:
        st.session_state.progresso = 0
    if 'mensagem_progresso' not in st.session_state:
        st.session_state.mensagem_progresso = ""
    
    # Inicializar logger
    logger.info("=== INÍCIO processar_mensagem (interface) ===")
    logger.info(f"Tipo de mensagem: {type(mensagem)}, Tamanho: {len(mensagem) if mensagem else 0}")
    
    # Verificar se já está processando
    if st.session_state.is_processing:
        logger.warning("Tentativa de processamento concorrente detectada")
        return "🔁 Já estou processando uma mensagem. Por favor, aguarde a conclusão antes de enviar uma nova solicitação."
    
    # Atualizar estado de processamento
    st.session_state.is_processing = True
    st.session_state.progresso = 10
    st.session_state.mensagem_progresso = "Validando mensagem..."
    
    # Exibir barra de progresso inicial
    progress_bar = exibir_progresso("Iniciando processamento...", 10)
    
    # Forçar atualização da interface
    time.sleep(0.1)
    
    try:
        # Validar mensagem de entrada
        if not mensagem or not isinstance(mensagem, str) or not mensagem.strip():
            error_msg = "Por favor, insira uma mensagem válida."
            logger.warning(f"Mensagem inválida recebida: {mensagem}")
            return error_msg
        
        st.session_state.progresso = 20
        st.session_state.mensagem_progresso = "Verificando agente..."
        progress_bar = exibir_progresso(st.session_state.mensagem_progresso, st.session_state.progresso)
        time.sleep(0.1)
        
        # Verificar se o agente está pronto
        if "agente_ia" not in st.session_state or st.session_state.agente_ia is None:
            error_msg = "❌ O AgenteIA não está pronto. Por favor, tente novamente em alguns instantes."
            logger.error(error_msg)
            return error_msg

        # Determinar se o modo coder deve ser sugerido ao AgenteIA
        programming_keywords = [
            "criar", "crie", "cria", "desenvolver", "desenvolva", "desenvolve", 
            "fazer", "faça", "faz", "implementar", "implemente", "implementa",
            "código", "codigo", "programa", "programar", "site", "aplicação", "aplicativo", 
            "jogo", "script", "python", "javascript", "java", "html", "css",
            "função", "funcao", "classe", "arquivo"
        ]
        
        code_file_extensions = [
            ".py", ".js", ".java", ".html", ".css", ".cpp", ".c", ".cs", ".go", ".php", ".rb", ".swift", ".kt", ".ts"
        ]

        st.session_state.progresso = 30
        st.session_state.mensagem_progresso = "Analisando mensagem..."
        progress_bar = exibir_progresso(st.session_state.mensagem_progresso, st.session_state.progresso)
        time.sleep(0.1)
        
        logger.info("Analisando mensagem para determinar se é uma solicitação de programação...")
        lower_mensagem = mensagem.lower()
        
        is_keyword_match = any(keyword in lower_mensagem for keyword in programming_keywords)
        is_extension_match = any(ext in lower_mensagem for ext in code_file_extensions)
        is_programming_request = is_keyword_match or is_extension_match
        
        logger.info(f"Detecção de programação - Palavras-chave: {is_keyword_match}, Extensões: {is_extension_match}")
        logger.info(f"Mensagem: '{mensagem[:100]}...'")
        logger.info(f"Sugestão para usar coder: {is_programming_request}")
        
        # Usar st.spinner para feedback visual
        with st.spinner("🔍 Processando sua solicitação..."):
            try:
                # Atualizar progresso
                st.session_state.progresso = 40
                st.session_state.mensagem_progresso = "Preparando processamento..."
                progress_bar = exibir_progresso(st.session_state.mensagem_progresso, st.session_state.progresso)
                time.sleep(0.1)
                
                # Chamar o método processar_mensagem do AgenteIA
                logger.info(f"Chamando processar_mensagem com usar_coder={is_programming_request}")
                
                # Configurar callbacks de progresso
                def atualizar_progresso(progresso: int, mensagem: str):
                    progresso_atual = 40 + int(progresso * 0.6)  # 40% a 100%
                    st.session_state.progresso = progresso_atual
                    st.session_state.mensagem_progresso = mensagem
                    nonlocal progress_bar
                    progress_bar = exibir_progresso(mensagem, progresso_atual)
                    time.sleep(0.05)  # Pequena pausa para atualização da UI
                
                # Configurar o agente com os callbacks de progresso
                st.session_state.agente_ia.on_progress_update = atualizar_progresso
                
                # Processar a mensagem
                resposta = st.session_state.agente_ia.processar_mensagem(
                    mensagem=mensagem, 
                    usar_coder=is_programming_request
                )
                
                # Validar a resposta
                if not resposta or not isinstance(resposta, str):
                    error_msg = "❌ Desculpe, não consegui processar sua solicitação. A resposta foi inválida ou vazia."
                    logger.warning(f"Resposta inválida do AgenteIA. Tipo: {type(resposta)}, Valor: {resposta}")
                    return error_msg
                
                # Limpar mensagens de erro anteriores, se houver
                if "error_message" in st.session_state:
                    del st.session_state.error_message
                
                # Atualizar progresso para concluído
                st.session_state.progresso = 100
                st.session_state.mensagem_progresso = "Processamento concluído!"
                progress_bar = exibir_progresso(st.session_state.mensagem_progresso, st.session_state.progresso)
                time.sleep(0.5)  # Mostrar mensagem de conclusão
                
                logger.info(f"Resposta recebida. Tamanho: {len(resposta)} caracteres")
                logger.debug(f"Primeiros 200 caracteres da resposta: {resposta[:200]}...")
                
                return resposta
                
            except requests.exceptions.ConnectionError as ce:
                error_msg = "🔌 Erro de conexão: Não foi possível conectar ao serviço de IA. Verifique sua conexão com a internet."
                logger.error(f"Erro de conexão: {str(ce)}")
                st.session_state.progresso = 0
                st.session_state.mensagem_progresso = "Erro de conexão"
                return error_msg
                
            except requests.exceptions.Timeout as te:
                error_msg = "⏱️ A operação demorou muito para ser concluída. Por favor, tente novamente com uma solicitação mais específica."
                logger.error(f"Timeout ao processar mensagem: {str(te)}")
                st.session_state.progresso = 0
                st.session_state.mensagem_progresso = "Tempo esgotado"
                return error_msg
                
            except Exception as agent_error:
                error_msg = f"⚠️ Ocorreu um erro ao processar sua mensagem: {str(agent_error)}"
                logger.error(f"Erro durante o processamento pelo AgenteIA: {str(agent_error)}", exc_info=True)
                st.session_state.progresso = 0
                st.session_state.mensagem_progresso = "Erro no processamento"
                return error_msg
            
    except Exception as e:
        logger.error(f"Erro crítico ao processar mensagem: {str(e)}", exc_info=True)
        error_type = type(e).__name__
        
        # Resetar estado de processamento
        st.session_state.progresso = 0
        st.session_state.mensagem_progresso = "Erro crítico"
        
        # Mensagem amigável para o usuário
        error_msgs = {
            "TimeoutError": "⏱️ A operação demorou muito para ser concluída. Tente novamente mais tarde.",
            "ConnectionError": "🔌 Erro de conexão. Verifique sua internet e tente novamente.",
            "RuntimeError": "⚠️ Ocorreu um erro inesperado. Tente novamente ou entre em contato com o suporte.",
            "default": f"❌ Ocorreu um erro inesperado: {str(e)}. Por favor, tente novamente mais tarde."
        }
        
        return error_msgs.get(error_type, error_msgs["default"])
        
    finally:
        # Sempre marcar como não processando, mesmo em caso de erro
        st.session_state.is_processing = False
        
        # Limpar mensagem de progresso após um curto período
        def limpar_mensagem():
            time.sleep(3)
            if 'mensagem_progresso' in st.session_state:
                st.session_state.mensagem_progresso = ""
        
        # Iniciar thread para limpar mensagem
        import threading
        threading.Thread(target=limpar_mensagem, daemon=True).start()
        
        logger.info("=== FIM processar_mensagem (interface) ===\n")

def limpar_fila() -> None:
    """
    Limpa a fila de requisições pendentes.
    """
    try:
        with processing_lock:
            # Limpar fila
            while not request_queue.empty():
                try:
                    request_queue.get_nowait()
                    request_queue.task_done()
                except queue.Empty:
                    break
            
            # Limpar status e requisições ativas
            request_status.clear()
            active_requests.clear()
            
            logger.info("Fila de requisições limpa")
        
    except Exception as e:
        logger.error(f"Erro ao limpar fila: {e}")

def listar_unidades() -> None:
    """
    Lista as unidades disponíveis no sistema.
    """
    try:
        ferramenta = ListarUnidades()
        unidades = ferramenta._run()
        
        # Criar colunas para melhor visualização
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📁 Unidades Disponíveis")
            st.text(unidades)
        
        with col2:
            st.markdown("### 📊 Informações")
            st.info("""
            - Clique em uma unidade para listar seus arquivos
            - O diretório de projetos é criado automaticamente
            - Arquivos grandes são marcados com ⚠️
            """)
            
    except Exception as e:
        st.error(f"Erro ao listar unidades: {e}")

def listar_arquivos_diretorio(diretorio: str) -> None:
    """
    Lista os arquivos em um diretório.
    
    Args:
        diretorio: Caminho do diretório
    """
    try:
        # Normalizar caminho
        diretorio = diretorio.strip('"\'')  # Remove aspas extras
        diretorio = os.path.normpath(diretorio)
        
        ferramenta = ListarArquivos()
        arquivos = ferramenta._run(diretorio)
        
        # Criar colunas para melhor visualização
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### 📂 Conteúdo de {diretorio}")
            st.text(arquivos)
        
        with col2:
            st.markdown("### 🔍 Ações")
            if st.button("📋 Copiar Caminho"):
                st.code(diretorio)
            
            if st.button("🔄 Atualizar"):
                st.rerun()
            
            st.markdown("### ℹ️ Dicas")
            st.info("""
            - Use o botão 'Copiar Caminho' para facilitar a navegação
            - Clique em 'Atualizar' para ver as últimas alterações
            - Arquivos grandes são marcados com ⚠️
            - Não use aspas nos caminhos
            """)
            
    except Exception as e:
        st.error(f"Erro ao listar arquivos: {e}")

def scroll_down() -> None:
    """Rola a página para baixo automaticamente."""
    js = """
    <script>
        // Rola para o final da página
        window.parent.document.querySelector('.main').scrollTo(0, window.parent.document.querySelector('.main').scrollHeight);
    </script>
    """
    components.html(js, height=0)

def main():
    """Função principal da interface."""
    try:
        # Exibir menu
        exibir_menu()
        
    except Exception as e:
        st.error(f"Erro na interface: {e}")

if __name__ == "__main__":
    main() 