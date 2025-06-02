"""
Página de configurações
"""

import streamlit as st
import os
from pathlib import Path
from agenteia.core.config import CONFIG
from agenteia.core.agente import AgenteIA
import json

# Funções de callback para progresso
def _progress_start(total: int):
    st.session_state.progress_bar = st.progress(0)
    st.session_state.progress_text = st.empty()

def _progress_update(current: int, total: int, status: str):
    if 'progress_bar' in st.session_state:
        st.session_state.progress_bar.progress(current / total)
    if 'progress_text' in st.session_state:
        st.session_state.progress_text.text(f"{status} ({current}/{total})")

def _progress_end():
    if 'progress_bar' in st.session_state:
        st.session_state.progress_bar.empty()
    if 'progress_text' in st.session_state:
        st.session_state.progress_text.empty()

st.set_page_config(
    page_title="Configurações - AgenteIA",
    page_icon="⚙️",
    layout="wide"
)

# Carregar configurações explicitamente para garantir que sejam as mais recentes
try:
    from agenteia.core.config import carregar_configuracao
    config_atualizada = carregar_configuracao()
except Exception as e:
    st.error(f"❌ Erro ao carregar configurações: {e}")
    st.stop() # Parar a execução se não conseguir carregar as configs

# Garantir que a chave 'ui' existe no config_atualizada
if "ui" not in config_atualizada:
    config_atualizada["ui"] = {
        "tema_escuro": False,
        "tamanho_fonte": 16,
        "idioma": "pt_BR",
        "modo_compacto": False
    }

st.title("⚙️ Configurações")

# Abas para diferentes seções de configuração
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🤖 Modelos", "🔧 Geral", "📝 Logs", "🔄 Sistema", "🔐 Segurança"])

with tab1:
    st.header("🤖 Configuração de Modelos")
    
    # Provedor de Modelo
    st.subheader("Provedor")
    usar_openrouter = st.toggle(
        "Usar OpenRouter",
        value=config_atualizada["openrouter"].get("usar_openrouter", False)
    )
    
    if usar_openrouter:
        st.markdown("Configure suas chaves e modelos do OpenRouter.")
        # API Key do OpenRouter
        api_key = st.text_input(
            "API Key do OpenRouter",
            type="password",
            value=config_atualizada["openrouter"].get("api_key", "")
        )
        
        # Modelo geral OpenRouter
        openrouter_modelo_geral = st.text_input(
            "Modelo Geral OpenRouter (Ex: 'meta-llama/llama-3.3-70b-instruct:free')",
            value=config_atualizada["openrouter"].get("modelo_geral", "")
        )

        # Modelo coder OpenRouter
        openrouter_modelo_coder = st.text_input(
            "Modelo Coder OpenRouter (Ex: 'deepcoder-14b-preview:free')",
            value=config_atualizada["openrouter"].get("modelo_coder", "")
        )
    
    # Modelo Geral
    st.subheader("Modelo Geral")
    col1, col2 = st.columns(2)
    
    with col1:
        modelo_geral = st.selectbox(
            "Modelo",
            options=["qwen3:1.7b", "qwen3:0.6b", "qwen3:4b"],
            index=0
        )
        
        temperatura_geral = st.slider(
            "Temperatura",
            min_value=0.0,
            max_value=1.0,
            value=config_atualizada["modelo"]["temperature"],
            step=0.1
        )
        
    with col2:
        max_tokens_geral = st.number_input(
            "Máximo de Tokens",
            min_value=100,
            max_value=8000,
            value=config_atualizada["modelo"]["max_tokens"],
            step=100
        )
        
        timeout_geral = st.number_input(
            "Timeout (segundos)",
            min_value=30,
            max_value=600,
            value=config_atualizada["modelo"].get("timeout", 300),
            step=30
        )
    
    # Modelo Coder
    st.subheader("Modelo Coder")
    col1, col2 = st.columns(2)
    
    with col1:
        modelo_coder = st.selectbox(
            "Modelo Coder",
            options=["qwen2.5-coder:3b"],
            index=0
        )
        
        temperatura_coder = st.slider(
            "Temperatura Coder",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1
        )
        
    with col2:
        max_tokens_coder = st.number_input(
            "Máximo de Tokens Coder",
            min_value=100,
            max_value=8000,
            value=8000,
            step=100
        )
        
        timeout_coder = st.number_input(
            "Timeout Coder (segundos)",
            min_value=30,
            max_value=600,
            value=300,
            step=30
        )

with tab2:
    st.header("🔧 Configurações Gerais")
    
    # Interface
    st.subheader("Interface")
    col1, col2 = st.columns(2)
    
    with col1:
        tema = st.selectbox(
            "Tema",
            options=["Claro", "Escuro", "Sistema"],
            index=0
        )
        
        idioma = st.selectbox(
            "Idioma",
            options=["Português", "English", "Español"],
            index=0
        )
        
    with col2:
        tamanho_fonte = st.slider(
            "Tamanho da Fonte",
            min_value=12,
            max_value=24,
            value=16,
            step=1
        )
        
        mostrar_metricas = st.toggle(
            "Mostrar Métricas",
            value=True
        )
    
    # Comportamento
    st.subheader("Comportamento")
    col1, col2 = st.columns(2)
    
    with col1:
        auto_salvar = st.toggle(
            "Auto-salvar",
            value=True
        )
        
        confirmar_acoes = st.toggle(
            "Confirmar Ações",
            value=True
        )
        
        verboso = st.toggle(
            "Modo verboso (Logging detalhado)",
            value=config_atualizada["agente_ia"].get("verboso", False)
        )
        
    with col2:
        max_historico = st.number_input(
            "Máximo de Mensagens no Histórico",
            min_value=10,
            max_value=1000,
            value=100,
            step=10
        )
        
        tempo_atualizacao = st.number_input(
            "Tempo de Atualização (segundos)",
            min_value=1,
            max_value=60,
            value=5,
            step=1
        )
        
        modo_compacto = st.toggle(
            "Modo Compacto",
            value=config_atualizada["ui"]["modo_compacto"]
        )

with tab3:
    st.header("📝 Configuração de Logs")
    
    # Níveis de Log
    st.subheader("Níveis de Log")
    col1, col2 = st.columns(2)
    
    with col1:
        nivel_log = st.selectbox(
            "Nível de Log",
            options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            index=1
        )
        
        formato_log = st.selectbox(
            "Formato do Log",
            options=["Simples", "Detalhado", "JSON"],
            index=0
        )
        
    with col2:
        rotacao_log = st.number_input(
            "Rotação de Log (MB)",
            min_value=1,
            max_value=100,
            value=10,
            step=1
        )
        
        manter_logs = st.number_input(
            "Manter Logs (dias)",
            min_value=1,
            max_value=365,
            value=30,
            step=1
        )
    
    # Arquivos de Log
    st.subheader("Arquivos de Log")
    logs_habilitados = st.multiselect(
        "Logs Habilitados",
        options=["Sistema", "Agente", "API", "Interface", "Erros"],
        default=["Sistema", "Erros"]
    )

with tab4:
    st.header("🔄 Configurações do Sistema")
    
    # MCP Server
    st.subheader("MCP Server")
    col1, col2 = st.columns(2)
    
    with col1:
        host_mcp = st.text_input(
            "Host MCP",
            value="localhost"
        )
        
        porta_mcp = st.number_input(
            "Porta MCP",
            min_value=1,
            max_value=65535,
            value=8000,
            step=1
        )
        
    with col2:
        timeout_mcp = st.number_input(
            "Timeout MCP (segundos)",
            min_value=1,
            max_value=300,
            value=30,
            step=1
        )
        
        retry_mcp = st.number_input(
            "Tentativas MCP",
            min_value=1,
            max_value=10,
            value=3,
            step=1
        )
    
    # Diretórios
    st.subheader("Diretórios")
    col1, col2 = st.columns(2)
    
    with col1:
        dir_dados = st.text_input(
            "Diretório de Dados",
            value="data"
        )
        
        dir_logs = st.text_input(
            "Diretório de Logs",
            value="logs"
        )
        
    with col2:
        dir_cache = st.text_input(
            "Diretório de Cache",
            value="cache"
        )
        
        dir_temp = st.text_input(
            "Diretório Temporário",
            value="temp"
        )

with tab5:
    st.header("🔐 Configurações de Segurança")
    
    # Segurança
    st.subheader("Segurança")
    col1, col2 = st.columns(2)
    
    with col1:
        max_tamanho_arquivo = st.number_input(
            "Tamanho Máximo de Arquivo (MB)",
            min_value=1,
            max_value=1000,
            value=10,
            step=1
        )
        
        timeout_requisicao = st.number_input(
            "Timeout de Requisição (segundos)",
            min_value=1,
            max_value=300,
            value=30,
            step=1
        )
        
    with col2:
        comandos_permitidos = st.text_area(
            "Comandos Permitidos",
            value=",".join(config_atualizada.get("security", {}).get("allowed_commands", [])),
            help="Lista de comandos permitidos, separados por vírgula"
        )
        
        diretorios_permitidos = st.text_area(
            "Diretórios Permitidos",
            value="\n".join(config_atualizada.get("security", {}).get("allowed_dirs", [])),
            help="Lista de diretórios permitidos, um por linha"
        )

# Botão de salvar
if st.button("💾 Salvar Configurações", use_container_width=True):
    try:
        # Garantir que todas as chaves necessárias existem
        if "modelo" not in config_atualizada:
            config_atualizada["modelo"] = {}
        if "ui" not in config_atualizada:
            config_atualizada["ui"] = {}
        if "logging" not in config_atualizada:
            config_atualizada["logging"] = {}
        if "mcp" not in config_atualizada:
            config_atualizada["mcp"] = {}
        if "dirs" not in config_atualizada:
            config_atualizada["dirs"] = {}
        if "security" not in config_atualizada:
            config_atualizada["security"] = {}
        if "openrouter" not in config_atualizada:
            config_atualizada["openrouter"] = {}

        # Atualizar configurações
        config_atualizada["modelo"]["nome"] = modelo_geral
        config_atualizada["modelo"]["temperature"] = temperatura_geral
        config_atualizada["modelo"]["max_tokens"] = max_tokens_geral
        config_atualizada["modelo"]["timeout"] = timeout_geral
        
        config_atualizada["modelo"]["coder"] = modelo_coder
        config_atualizada["modelo"]["coder_temperature"] = temperatura_coder
        config_atualizada["modelo"]["coder_max_tokens"] = max_tokens_coder
        config_atualizada["modelo"]["coder_timeout"] = timeout_coder
        
        # Configurações gerais
        config_atualizada["ui"]["tema_escuro"] = tema == "Escuro"
        config_atualizada["ui"]["tamanho_fonte"] = tamanho_fonte
        config_atualizada["ui"]["idioma"] = idioma
        config_atualizada["ui"]["modo_compacto"] = modo_compacto
        
        # Configurações de log
        config_atualizada["logging"]["level"] = nivel_log
        config_atualizada["logging"]["format"] = formato_log
        config_atualizada["logging"]["rotation"] = rotacao_log
        config_atualizada["logging"]["retention"] = manter_logs
        config_atualizada["logging"]["enabled"] = logs_habilitados
        
        # Configurações do sistema
        config_atualizada["mcp"]["host"] = host_mcp
        config_atualizada["mcp"]["port"] = porta_mcp
        config_atualizada["mcp"]["timeout"] = timeout_mcp
        config_atualizada["mcp"]["retry"] = retry_mcp
        
        config_atualizada["dirs"]["data"] = dir_dados
        config_atualizada["dirs"]["logs"] = dir_logs
        config_atualizada["dirs"]["cache"] = dir_cache
        config_atualizada["dirs"]["temp"] = dir_temp
        
        # Configurações de segurança
        config_atualizada["security"]["max_file_size"] = max_tamanho_arquivo * 1024 * 1024  # Converter para bytes
        config_atualizada["security"]["request_timeout"] = timeout_requisicao
        config_atualizada["security"]["allowed_commands"] = [cmd.strip() for cmd in comandos_permitidos.split(",")]
        config_atualizada["security"]["allowed_dirs"] = [dir.strip() for dir in diretorios_permitidos.split("\n")]
        
        # OpenRouter
        if usar_openrouter:
            config_atualizada["openrouter"]["api_key"] = api_key
            config_atualizada["openrouter"]["modelo_geral"] = openrouter_modelo_geral
            config_atualizada["openrouter"]["modelo_coder"] = openrouter_modelo_coder
            os.environ["OPENROUTER_API_KEY"] = api_key
        
        # Salvar em arquivo
        config_path = Path("config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_atualizada, f, indent=2, ensure_ascii=False)
            
        # Reconfigurar o agente se necessário
        if 'agente_ia' in config_atualizada:
            if usar_openrouter != config_atualizada["agente_ia"]["usar_openrouter"]:
                config_atualizada["agente_ia"]["alternar_provedor_modelo"](usar_openrouter)
            
            config_atualizada["agente_ia"] = AgenteIA(
                on_progress_start=_progress_start,
                on_progress_update=_progress_update,
                on_progress_end=_progress_end,
                usar_openrouter=usar_openrouter,
                verboso=verboso
            )
            
        st.success("✅ Configurações salvas com sucesso!")
        
    except Exception as e:
        st.error(f"❌ Erro ao salvar configurações: {e}")

# Instruções
st.markdown("---")
st.markdown("""
### 📝 Instruções
1. Configure os modelos e parâmetros
2. Ajuste as configurações gerais
3. Configure os logs conforme necessário
4. Ajuste as configurações do sistema
5. Configure as opções de segurança
6. Clique em Salvar para aplicar as mudanças
""") 