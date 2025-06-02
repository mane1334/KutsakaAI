"""
Interface do Agente IA
"""

import streamlit as st
import logging
from datetime import datetime
import json
import os
import pandas as pd
import streamlit.components.v1 as components
from typing import Generator, List, Dict, Any
from enum import Enum
from dataclasses import dataclass

from agenteia.core.agente import AgenteIA
from agenteia.core.config import CONFIG
from agenteia.logs import setup_logging

# Configuração de logging
logger = setup_logging(__name__)

# Configurações da página
st.set_page_config(
    page_title="Agente IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def processar_mensagem_stream(mensagem: str) -> Generator[str, None, None]:
    """
    Processa uma mensagem com streaming de resposta.
    
    Args:
        mensagem: Mensagem do usuário
        
    Yields:
        Tokens da resposta do agente
    """
    try:
        # Processar a mensagem com streaming
        for token in st.session_state.agente_ia.processar_mensagem_stream(mensagem):
            yield token
            
    except Exception as e:
        logger.error(f"Erro ao processar mensagem stream: {str(e)}", exc_info=True)
        st.error(f"⚠️ Ocorreu um erro ao processar sua mensagem: {str(e)}")
        yield f"Erro ao processar mensagem: {str(e)}"

def scroll_down() -> None:
    """Rola a página para baixo."""
    js = """
    <script>
        window.parent.document.querySelector('section.main').scrollTo(0, window.parent.document.querySelector('section.main').scrollHeight);
    </script>
    """
    components.html(js, height=0)

def exibir_menu() -> None:
    """Exibe o menu principal da interface."""
    # Sidebar
    with st.sidebar:
        st.title("🤖 Agente IA")
        
        # Menu
        menu = st.radio(
            "Menu",
            ["Chat", "Configurações", "Ajuda", "Sobre"]
        )
        
        # Configurações
        if menu == "Configurações":
            st.markdown("### ⚙️ Configurações")
            
            # Abas de configurações
            tab1, tab2 = st.tabs(["Básicas", "Avançadas"])
            
            with tab1:
                # Modelo
                modelo = st.selectbox(
                    "Modelo",
                    options=st.session_state.agente_ia.modelos_disponiveis,
                    index=0
                )
                
                # Temperatura
                temperatura = st.slider(
                    "Temperatura",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.1
                )
                
                # Máximo de tokens
                max_tokens = st.number_input(
                    "Máximo de tokens",
                    min_value=100,
                    max_value=4000,
                    value=2000,
                    step=100
                )
                
            with tab2:
                # Usar OpenRouter
                usar_openrouter = st.toggle(
                    "Usar OpenRouter",
                    value=st.session_state.agente_ia.usar_openrouter
                )
                
                if usar_openrouter:
                    # API Key do OpenRouter
                    api_key = st.text_input(
                        "API Key do OpenRouter",
                        type="password",
                        value=os.getenv("OPENROUTER_API_KEY", "")
                    )
                    
                    if api_key:
                        os.environ["OPENROUTER_API_KEY"] = api_key
                
                # Verboso
                verboso = st.toggle(
                    "Modo verboso",
                    value=False
                )
                
                # Timeout
                timeout = st.number_input(
                    "Timeout (segundos)",
                    min_value=30,
                    max_value=600,
                    value=300,
                    step=30
                )
            
            # Botão de salvar
            if st.button("💾 Salvar Configurações"):
                try:
                    # Atualizar configurações
                    CONFIG["modelo"]["nome"] = modelo
                    CONFIG["modelo"]["temperature"] = temperatura
                    CONFIG["modelo"]["max_tokens"] = max_tokens
                    CONFIG["modelo"]["timeout"] = timeout
                    
                    # Alternar provedor se necessário
                    if usar_openrouter != st.session_state.agente_ia.usar_openrouter:
                        st.session_state.agente_ia.alternar_provedor_modelo(usar_openrouter)
                    
                    st.success("✅ Configurações salvas com sucesso!")
                    
                except Exception as e:
                    st.error(f"❌ Erro ao salvar configurações: {e}")
        
        # Ajuda
        elif menu == "Ajuda":
            st.markdown("### 📚 Ajuda")
            st.markdown("""
            #### Como usar o Agente IA
            
            1. Digite sua mensagem na caixa de texto
            2. Aguarde a resposta do agente
            3. Use os comandos especiais para tarefas específicas
            
            #### Comandos especiais
            
            - `/ajuda` - Mostra esta ajuda
            - `/limpar` - Limpa o histórico
            - `/salvar` - Salva o histórico
            - `/carregar` - Carrega um histórico
            - `/exportar` - Exporta o histórico
            - `/copiar` - Copia o histórico
            - `/versao` - Mostra a versão
            - `/sobre` - Mostra informações sobre o agente
            """)
        
        # Sobre
        elif menu == "Sobre":
            st.markdown("### ℹ️ Sobre")
            st.markdown("""
            #### Agente IA
            
            Um agente de IA inteligente que pode ajudar com diversas tarefas.
            
            #### Versão
            """ + CONFIG["versao"])
    
    # Seção de chat
    st.markdown("### 💬 Chat")
    
    # Inicializar histórico se não existir
    if "historico" not in st.session_state:
        st.session_state.historico = []
    
    # Exibir histórico
    for msg in st.session_state.historico:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])
    
    # Input do usuário
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Exibir mensagem do usuário
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Adicionar ao histórico
        st.session_state.historico.append({
            "role": "user",
            "content": prompt,
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Exibir resposta do assistente
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Processar mensagem com streaming
            for token in st.session_state.agente_ia.processar_mensagem_stream(prompt):
                full_response += token
                message_placeholder.markdown(full_response + "▌")
            
            # Atualizar com resposta completa
            message_placeholder.markdown(full_response)
            
            # Adicionar ao histórico
            st.session_state.historico.append({
                "role": "assistant",
                "content": full_response,
                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Rolar para baixo
        scroll_down()

def inicializar_estado() -> None:
    """Inicializa o estado da aplicação."""
    if "agente_ia" not in st.session_state:
        st.session_state.agente_ia = AgenteIA()

def main():
    """Função principal."""
    try:
        # Inicializar estado
        inicializar_estado()
        
        # Exibir menu
        exibir_menu()
        
    except Exception as e:
        logger.error(f"Erro na aplicação: {e}", exc_info=True)
        st.error(f"❌ Ocorreu um erro na aplicação: {e}")

if __name__ == "__main__":
    main() 