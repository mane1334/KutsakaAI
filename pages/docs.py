"""
Página de documentação
"""

import streamlit as st
import os
from pathlib import Path

st.set_page_config(
    page_title="Documentação - AgenteIA",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Documentação")

# Abas para diferentes seções
tab1, tab2, tab3 = st.tabs(["📖 Guia", "🔧 API", "💡 Exemplos"])

with tab1:
    st.header("📖 Guia do Usuário")
    
    st.markdown("""
    ### 🚀 Introdução
    
    O AgenteIA é um assistente virtual inteligente que pode ajudar com diversas tarefas.
    
    ### 🎯 Principais Funcionalidades
    
    1. **Chat Inteligente**
       - Conversas naturais
       - Respostas contextuais
       - Suporte a múltiplos idiomas
    
    2. **Gerenciamento de Tarefas**
       - Criação de tarefas
       - Acompanhamento de status
       - Priorização
    
    3. **Manipulação de Arquivos**
       - Navegação de diretórios
       - Criação e edição
       - Organização
    
    4. **Relatórios e Análises**
       - Métricas de uso
       - Gráficos e visualizações
       - Exportação de dados
    
    ### ⚙️ Configuração
    
    1. Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
    
    2. Configure as API Keys:
    - Acesse a página de API Keys
    - Adicione suas chaves
    - Salve as configurações
    
    3. Inicie o servidor:
    ```bash
    streamlit run interface.py
    ```
    """)

with tab2:
    st.header("🔧 API Reference")
    
    st.markdown("""
    ### 📡 Endpoints
    
    #### Agentes
    - `GET /agentes` - Lista todos os agentes
    - `POST /agentes/{nome}` - Registra um novo agente
    - `GET /agentes/{nome}` - Obtém informações de um agente
    - `DELETE /agentes/{nome}` - Remove um agente
    
    #### Tarefas
    - `GET /tarefas` - Lista todas as tarefas
    - `POST /tarefas` - Cria uma nova tarefa
    - `GET /tarefas/{id}` - Obtém detalhes de uma tarefa
    - `PUT /tarefas/{id}` - Atualiza uma tarefa
    - `DELETE /tarefas/{id}` - Remove uma tarefa
    
    #### Ferramentas
    - `GET /ferramentas` - Lista ferramentas disponíveis
    - `POST /ferramentas/{nome}` - Registra uma nova ferramenta
    - `GET /ferramentas/{nome}` - Obtém detalhes de uma ferramenta
    - `DELETE /ferramentas/{nome}` - Remove uma ferramenta
    
    ### 📦 Modelos de Dados
    
    ```python
    class AgenteInfo:
        nome: str
        especialidades: List[str]
        status: str
        
    class TarefaInfo:
        id: str
        titulo: str
        descricao: str
        status: str
        prioridade: str
        data: datetime
        
    class FerramentaInfo:
        nome: str
        descricao: str
        parametros: Dict[str, Any]
        retorno: str
    ```
    """)

with tab3:
    st.header("💡 Exemplos de Uso")
    
    st.markdown("""
    ### 📝 Exemplos de Código
    
    #### 1. Registrando um Agente
    ```python
    from agenteia import AgenteIA
    
    # Criar agente
    agente = AgenteIA(
        on_progress_start=lambda msg: print(f"Iniciando: {msg}"),
        on_progress_update=lambda val, msg: print(f"Progresso: {val}% - {msg}"),
        on_progress_end=lambda: print("Concluído!")
    )
    
    # Registrar no MCP
    agente.registrar("meu_agente")
    ```
    
    #### 2. Criando uma Tarefa
    ```python
    from agenteia.core.mcp_client import MCPClient
    
    # Inicializar cliente
    cliente = MCPClient()
    
    # Criar tarefa
    tarefa = {
        "titulo": "Análise de Dados",
        "descricao": "Analisar dados de vendas",
        "prioridade": "Alta"
    }
    
    # Enviar tarefa
    resultado = cliente.distribuir_tarefa(tarefa)
    ```
    
    #### 3. Usando Ferramentas
    ```python
    from agenteia.core.ferramentas import ListarArquivos
    
    # Criar ferramenta
    ferramenta = ListarArquivos()
    
    # Listar arquivos
    arquivos = ferramenta._run("/caminho/do/diretorio")
    print(arquivos)
    ```
    """)

# Instruções
st.markdown("---")
st.markdown("""
### 📝 Instruções
1. Use as abas para navegar entre diferentes seções
2. Consulte a documentação relevante
3. Experimente os exemplos de código
4. Entre em contato para suporte
""") 