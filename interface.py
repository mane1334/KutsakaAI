import streamlit as st
from streamlit_chat import message
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
import os
import json
from dotenv import load_dotenv
from agente import AgenteIA
import re

# Configuração da página
st.set_page_config(
    page_title="Assistente IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carregar variáveis de ambiente
load_dotenv()

# Função para salvar histórico
def salvar_historico(messages, caminho='historico.json'):
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

# Função para carregar histórico
def carregar_historico(caminho='historico.json'):
    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Adicionar variável de loading ao estado
if "loading" not in st.session_state:
    st.session_state.loading = False

# Inicialização dos chats
if "chats" not in st.session_state:
    st.session_state.chats = {
        "Principal": {"messages": [], "context": "Chat principal para conversas gerais"}
    }

if "chat_atual" not in st.session_state:
    st.session_state.chat_atual = "Principal"

# Estilo CSS moderno e elegante com animações reforçadas e skeleton loader
st.markdown("""
    <style>
    body, .stApp {
        background-color: #181c24 !important;
        color: #f5f5f5 !important;
        font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
    }
    .stChatInput input {
        color: #fff !important;
        background: #23272f !important;
        border: 1.5px solid #4f5b6b !important;
        border-radius: 25px !important;
        padding: 0.8rem 1.2rem !important;
        font-size: 1.1rem !important;
    }
    .stButton>button {
        border-radius: 20px !important;
        background: #475063 !important;
        color: #fff !important;
        border: none !important;
        padding: 0.5rem 1.2rem !important;
        font-size: 1rem !important;
        transition: background 0.2s;
    }
    .stButton>button:hover {
        background: #6c7a89 !important;
        color: #fff !important;
    }
    .chat-message {
        padding: 1.2rem;
        border-radius: 1.5rem;
        margin-bottom: 1.2rem;
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        gap: 1rem;
        color: #f5f5f5;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        animation: fadeIn 0.7s cubic-bezier(.39,.575,.565,1.000);
        transition: background 0.3s, box-shadow 0.3s;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(40px);}
        to { opacity: 1; transform: translateY(0);}
    }
    .chat-message.new {
        background: #3a3f4b !important;
        box-shadow: 0 0 0 3px #6c7a89;
        animation: highlight 1.2s;
    }
    @keyframes highlight {
        0% { background: #6c7a89; }
        100% { background: inherit; }
    }
    .chat-message.user {
        background: linear-gradient(90deg, #2b313e 80%, #23272f 100%);
        border: 1.5px solid #4f5b6b;
    }
    .chat-message.bot {
        background: linear-gradient(90deg, #475063 80%, #23272f 100%);
        border: 1.5px solid #6c7a89;
    }
    .chat-message .avatar {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.10);
    }
    .chat-message .message {
        width: 100%;
        word-break: break-word;
        font-size: 1.08rem;
    }
    .sidebar .stSlider {
        margin-bottom: 2rem;
    }
    .stMarkdown {
        color: #aaa !important;
    }
    .skeleton-loader {
        width: 100%;
        height: 2.5rem;
        background: linear-gradient(90deg, #23272f 25%, #2b313e 50%, #23272f 75%);
        background-size: 200% 100%;
        animation: skeleton 1.2s infinite linear;
        border-radius: 1rem;
        margin-bottom: 1rem;
    }
    @keyframes skeleton {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    .typing span {
        display: inline-block;
        width: 8px; height: 8px;
        margin: 0 2px;
        background: #aaa;
        border-radius: 50%;
        animation: blink 1.4s infinite both;
    }
    .typing span:nth-child(2) { animation-delay: 0.2s; }
    .typing span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes blink {
        0%, 80%, 100% { opacity: 0.2; }
        40% { opacity: 1; }
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 #6c7a89; }
        70% { box-shadow: 0 0 0 10px rgba(108,122,137,0); }
        100% { box-shadow: 0 0 0 0 rgba(108,122,137,0); }
    }
    .avatar.pulse {
        animation: pulse 1.2s infinite;
    }
    </style>
""", unsafe_allow_html=True)

# Inicialização do agente
@st.cache_resource
def get_agent():
    return AgenteIA()

# Inicialização do histórico de chat
if "messages" not in st.session_state:
    st.session_state.messages = carregar_historico()

# Sidebar
with st.sidebar:
    st.title("🤖 Assistente IA")
    st.markdown("---")
    
    # Gerenciador de Chats
    st.subheader("📚 Gerenciador de Chats")
    
    # Criar novo chat
    novo_chat_nome = st.text_input("Nome do novo chat:")
    novo_chat_contexto = st.text_area("Contexto do chat:", height=100)
    if st.button("Criar Novo Chat") and novo_chat_nome:
        if novo_chat_nome not in st.session_state.chats:
            st.session_state.chats[novo_chat_nome] = {
                "messages": [],
                "context": novo_chat_contexto
            }
            st.success(f"Chat '{novo_chat_nome}' criado com sucesso!")
            st.rerun()
        else:
            st.error("Já existe um chat com este nome!")

    # Seletor de chat
    st.subheader("🔄 Selecionar Chat")
    chat_selecionado = st.selectbox(
        "Escolha um chat:",
        options=list(st.session_state.chats.keys()),
        index=list(st.session_state.chats.keys()).index(st.session_state.chat_atual)
    )
    
    if chat_selecionado != st.session_state.chat_atual:
        st.session_state.chat_atual = chat_selecionado
        st.rerun()

    # Mostrar contexto do chat atual
    st.subheader("📝 Contexto Atual")
    st.markdown(f"**Chat:** {st.session_state.chat_atual}")
    st.markdown(f"**Contexto:** {st.session_state.chats[st.session_state.chat_atual]['context']}")

    # Opção para excluir chat
    if st.session_state.chat_atual != "Principal":
        if st.button("🗑️ Excluir Chat Atual"):
            del st.session_state.chats[st.session_state.chat_atual]
            st.session_state.chat_atual = "Principal"
            st.rerun()
    
    st.markdown("---")
    
    # Opções de configuração
    st.subheader("⚙️ Configurações")
    temperatura = st.slider("Temperatura", 0.0, 1.0, 0.7, 0.1)
    mostrar_raciocinio = st.checkbox("Mostrar raciocínio interno do agente", value=False)

    # Adicionar barra de progresso para memória de contexto
    agent = get_agent()
    max_mensagens = agent.contexto_manager.max_mensagens
    mensagens_atuais = len(st.session_state.chats[st.session_state.chat_atual]["messages"])
    contexto_percentual = (mensagens_atuais / max_mensagens) * 100

    # Mostrar barra de progresso e informações do contexto
    st.markdown("### 📊 Memória de Contexto")
    st.progress(contexto_percentual / 100)
    st.text(f"Mensagens: {mensagens_atuais}/{max_mensagens}")
    st.text(f"Uso do Contexto: {contexto_percentual:.1f}%")
    
    # Histórico de conversas
    st.markdown("---")
    st.subheader("📜 Histórico")
    
    # Listar históricos disponíveis
    historicos = agent.listar_historicos()
    if historicos:
        st.markdown("#### Históricos Salvos")
        for historico in historicos:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(historico)
            with col2:
                if st.button("Carregar", key=f"load_{historico}"):
                    agent.carregar_historico(os.path.join('historico', historico))
                    st.session_state.chats[st.session_state.chat_atual]["messages"] = agent.contexto_manager.obter_historico()
                    st.success(f"Histórico {historico} carregado com sucesso!")
                    st.rerun()
    
    # Botões de gerenciamento de histórico
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Limpar Histórico do Chat Atual"):
            st.session_state.chats[st.session_state.chat_atual]["messages"] = []
            agent.limpar_historico()
            st.success("Histórico limpo com sucesso!")
            st.rerun()
    
    with col2:
        if st.button("Salvar Histórico Atual"):
            agent.salvar_historico()
            st.success("Histórico salvo com sucesso!")
            st.rerun()
    
    # Botão de download do histórico
    if st.session_state.chats[st.session_state.chat_atual]["messages"]:
        st.download_button(
            label="📥 Baixar Histórico (JSON)",
            data=json.dumps(st.session_state.chats[st.session_state.chat_atual], ensure_ascii=False, indent=2),
            file_name=f"historico_{st.session_state.chat_atual}.json",
            mime="application/json"
        )

# Área principal - Chat
st.title(f"💬 Chat: {st.session_state.chat_atual}")

# Exibir mensagens do chat atual
for msg in st.session_state.chats[st.session_state.chat_atual]["messages"]:
    conteudo = msg["content"]
    if "<think>" in conteudo and "</think>" in conteudo:
        conteudo = conteudo.split("</think>")[-1].strip()
    avatar = "🧑" if msg["role"] == "user" else "🤖"
    message(conteudo, is_user=(msg["role"] == "user"), key=f"{msg['role']}_{msg['id']}", avatar_style=avatar)

# Input do usuário
user_input = st.chat_input("Digite sua mensagem e pressione Enter...")

if user_input:
    # Adicionar mensagem do usuário ao chat atual
    msg_id = len(st.session_state.chats[st.session_state.chat_atual]["messages"])
    st.session_state.chats[st.session_state.chat_atual]["messages"].append({
        "role": "user",
        "content": user_input,
        "id": msg_id
    })
    
    # Processar resposta do agente
    agent = get_agent()
    response = agent.processar_mensagem(user_input, mostrar_raciocinio=mostrar_raciocinio)
    
    # Adicionar resposta do agente ao chat atual
    msg_id = len(st.session_state.chats[st.session_state.chat_atual]["messages"])
    st.session_state.chats[st.session_state.chat_atual]["messages"].append({
        "role": "assistant",
        "content": response,
        "id": msg_id
    })
    
    st.rerun()

# Skeleton loader e animação de typing dots enquanto a IA responde
if st.session_state.loading:
    st.markdown('<div class="skeleton-loader"></div>', unsafe_allow_html=True)
    st.markdown('''
    <div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:1.2rem;">
        <span style="color:#aaa;font-size:1.1rem;">🤖 Agente: pensando...</span>
        <div class="typing">
            <span></span><span></span><span></span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

# CSS para pulse no avatar do agente na última mensagem
st.markdown("""
<style>
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 #6c7a89; }
    70% { box-shadow: 0 0 0 10px rgba(108,122,137,0); }
    100% { box-shadow: 0 0 0 0 rgba(108,122,137,0); }
}
.chat-message.bot:last-child .avatar {
    animation: pulse 1.2s infinite;
}
</style>
""", unsafe_allow_html=True)

# Rodapé mais visível
st.markdown("---")
st.markdown("<center><small style='color:#aaa;'>Desenvolvido por Manuel Jose</small></center>", unsafe_allow_html=True) 