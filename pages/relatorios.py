"""
Página de relatórios
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
from pathlib import Path

st.set_page_config(
    page_title="Relatórios - AgenteIA",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Relatórios")

# Carregar dados
def carregar_dados():
    try:
        arquivo = Path("data/tarefas.json")
        if arquivo.exists():
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return []

# Converter dados para DataFrame
def criar_dataframe(tarefas):
    df = pd.DataFrame(tarefas)
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y %H:%M')
    return df

# Carregar dados
tarefas = carregar_dados()
df = criar_dataframe(tarefas)

# Abas para diferentes relatórios
tab1, tab2, tab3 = st.tabs(["📈 Visão Geral", "📊 Status", "📅 Timeline"])

with tab1:
    st.header("📈 Visão Geral")
    
    if not df.empty:
        # Métricas principais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total = len(df)
            st.metric("Total de Tarefas", total)
            
        with col2:
            concluidas = len(df[df['status'] == "Concluída"])
            st.metric("Tarefas Concluídas", concluidas)
            
        with col3:
            pendentes = total - concluidas
            st.metric("Tarefas Pendentes", pendentes)
            
        # Gráfico de pizza - Status
        fig_status = px.pie(
            df,
            names='status',
            title='Distribuição por Status',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_status, use_container_width=True)
        
        # Gráfico de barras - Prioridade
        fig_prioridade = px.bar(
            df,
            x='prioridade',
            title='Distribuição por Prioridade',
            color='status',
            barmode='group'
        )
        st.plotly_chart(fig_prioridade, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para análise.")

with tab2:
    st.header("📊 Análise de Status")
    
    if not df.empty:
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            status_filtro = st.multiselect(
                "Filtrar por Status",
                options=df['status'].unique(),
                default=df['status'].unique()
            )
            
        with col2:
            prioridade_filtro = st.multiselect(
                "Filtrar por Prioridade",
                options=df['prioridade'].unique(),
                default=df['prioridade'].unique()
            )
            
        # Aplicar filtros
        df_filtrado = df[
            (df['status'].isin(status_filtro)) &
            (df['prioridade'].isin(prioridade_filtro))
        ]
        
        # Exibir dados filtrados
        st.dataframe(
            df_filtrado[['titulo', 'status', 'prioridade', 'data']],
            use_container_width=True
        )
    else:
        st.info("Nenhum dado disponível para análise.")

with tab3:
    st.header("📅 Timeline")
    
    if not df.empty:
        # Timeline de tarefas
        fig_timeline = px.timeline(
            df,
            x_start='data',
            y='titulo',
            color='status',
            title='Timeline de Tarefas'
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Estatísticas por período
        st.subheader("📊 Estatísticas por Período")
        
        # Agrupar por data
        df['data_dia'] = df['data'].dt.date
        stats_diarias = df.groupby('data_dia').agg({
            'titulo': 'count',
            'status': lambda x: (x == 'Concluída').sum()
        }).reset_index()
        
        stats_diarias.columns = ['Data', 'Total', 'Concluídas']
        stats_diarias['Pendentes'] = stats_diarias['Total'] - stats_diarias['Concluídas']
        
        st.dataframe(stats_diarias, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para análise.")

# Instruções
st.markdown("---")
st.markdown("""
### 📝 Instruções
1. Use as abas para navegar entre diferentes relatórios
2. Aplique filtros para análise específica
3. Exporte os dados usando os botões de download
4. Visualize as tendências e estatísticas
""") 