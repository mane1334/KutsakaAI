"""
Página de gerenciamento de arquivos
"""

import streamlit as st
import os
from pathlib import Path
from agenteia.core.ferramentas import ListarArquivos, ListarUnidades

st.set_page_config(
    page_title="Arquivos - AgenteIA",
    page_icon="📁",
    layout="wide"
)

st.title("📁 Gerenciamento de Arquivos")

# Listar unidades
st.header("💿 Unidades")
try:
    ferramenta = ListarUnidades()
    unidades = ferramenta._run()
    st.text(unidades)
except Exception as e:
    st.error(f"❌ Erro ao listar unidades: {e}")

# Navegação de diretórios
st.header("📂 Navegador de Arquivos")
diretorio_atual = st.text_input(
    "Caminho do diretório",
    value=os.getcwd()
)

if st.button("🔍 Listar Arquivos"):
    try:
        ferramenta = ListarArquivos()
        arquivos = ferramenta._run(diretorio_atual)
        
        # Exibir arquivos em colunas
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("### 📋 Arquivos e Pastas")
            st.text(arquivos)
            
        with col2:
            st.markdown("### 📊 Informações")
            st.info(f"""
            - Total de itens: {len(arquivos.split('\\n'))}
            - Diretório atual: {diretorio_atual}
            """)
            
    except Exception as e:
        st.error(f"❌ Erro ao listar arquivos: {e}")

# Ações
st.header("⚡ Ações")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📝 Novo Arquivo"):
        st.info("Funcionalidade em desenvolvimento")
        
with col2:
    if st.button("📁 Nova Pasta"):
        st.info("Funcionalidade em desenvolvimento")
        
with col3:
    if st.button("🗑️ Excluir"):
        st.info("Funcionalidade em desenvolvimento")

# Instruções
st.markdown("---")
st.markdown("""
### 📝 Instruções
1. Digite o caminho do diretório desejado
2. Clique em Listar Arquivos para ver o conteúdo
3. Use as ações para manipular arquivos e pastas
4. Arquivos grandes são marcados com ⚠️
""") 