"""
Página de gerenciamento de tarefas
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path

st.set_page_config(
    page_title="Tarefas - AgenteIA",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Gerenciamento de Tarefas")

# Carregar tarefas
def carregar_tarefas():
    try:
        arquivo = Path("data/tarefas.json")
        if arquivo.exists():
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"❌ Erro ao carregar tarefas: {e}")
        return []

# Salvar tarefas
def salvar_tarefas(tarefas):
    try:
        arquivo = Path("data/tarefas.json")
        arquivo.parent.mkdir(exist_ok=True)
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(tarefas, f, indent=2, ensure_ascii=False)
        st.success("✅ Tarefas salvas com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao salvar tarefas: {e}")

# Interface principal
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📝 Lista de Tarefas")
    
    # Carregar tarefas existentes
    tarefas = carregar_tarefas()
    
    # Exibir tarefas
    for i, tarefa in enumerate(tarefas):
        with st.expander(f"📌 {tarefa['titulo']}"):
            st.markdown(f"**Descrição:** {tarefa['descricao']}")
            st.markdown(f"**Status:** {tarefa['status']}")
            st.markdown(f"**Data:** {tarefa['data']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Concluir", key=f"concluir_{i}"):
                    tarefa['status'] = "Concluída"
                    salvar_tarefas(tarefas)
                    st.rerun()
            with col2:
                if st.button("🗑️ Excluir", key=f"excluir_{i}"):
                    tarefas.pop(i)
                    salvar_tarefas(tarefas)
                    st.rerun()

with col2:
    st.header("➕ Nova Tarefa")
    
    # Formulário de nova tarefa
    titulo = st.text_input("Título")
    descricao = st.text_area("Descrição")
    prioridade = st.selectbox(
        "Prioridade",
        ["Baixa", "Média", "Alta"]
    )
    
    if st.button("➕ Adicionar Tarefa"):
        if titulo and descricao:
            nova_tarefa = {
                "titulo": titulo,
                "descricao": descricao,
                "prioridade": prioridade,
                "status": "Pendente",
                "data": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            tarefas.append(nova_tarefa)
            salvar_tarefas(tarefas)
            st.rerun()
        else:
            st.warning("⚠️ Preencha todos os campos!")

# Estatísticas
st.markdown("---")
st.header("📊 Estatísticas")

col1, col2, col3 = st.columns(3)

with col1:
    total = len(tarefas)
    st.metric("Total de Tarefas", total)
    
with col2:
    concluidas = sum(1 for t in tarefas if t['status'] == "Concluída")
    st.metric("Tarefas Concluídas", concluidas)
    
with col3:
    pendentes = total - concluidas
    st.metric("Tarefas Pendentes", pendentes)

# Instruções
st.markdown("---")
st.markdown("""
### 📝 Instruções
1. Adicione novas tarefas usando o formulário
2. Gerencie tarefas existentes na lista
3. Marque tarefas como concluídas
4. Exclua tarefas quando necessário
""")
