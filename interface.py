"""
Interface principal do AgenteIA
"""

import streamlit as st
from agenteia.core.agente import AgenteIA
from agenteia.core.mcp_client import MCPClient
import asyncio

# Configuração da página
st.set_page_config(
    page_title="AgenteIA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Inicialização do cliente MCP
if 'mcp_client' not in st.session_state:
    st.session_state.mcp_client = MCPClient()

# Inicialização do agente
if 'agente_ia' not in st.session_state:
    # Obter a configuração, garantindo que esteja carregada
    try:
        from agenteia.core.config import CONFIG, carregar_configuracao
        # Garantir que CONFIG está carregado, carregar se necessário (embora deva ser carregado na importação)
        if not CONFIG:
             config_data = carregar_configuracao()
        else:
             config_data = CONFIG
             
        usar_openrouter_config = config_data.get("openrouter", {}).get("enabled", False)
        
        st.session_state.agente_ia = AgenteIA(
            mcp_client=st.session_state.mcp_client,
            usar_openrouter=usar_openrouter_config, # Passar o valor da configuração
            config=config_data
        )
    except Exception as e:
        st.error(f"❌ Erro ao inicializar AgenteIA com configurações: {e}")
        st.session_state.agente_ia = None # Definir como None para evitar erros posteriores

# Menu lateral
def exibir_menu():
    with st.sidebar:
        st.title("🤖 AgenteIA")

        # MCP Server
        st.header("🔄 MCP Server")
        if st.button("🔄 Atualizar Métricas"):
            try:
                metricas = st.session_state.mcp_client.obter_metricas()
                st.session_state.metricas = metricas
                st.success("✅ Métricas atualizadas!")
            except Exception as e:
                st.error(f"❌ Erro ao atualizar métricas: {e}")

        # Agentes Registrados
        st.header("🤖 Agentes Registrados")
        try:
            agentes = st.session_state.mcp_client.listar_agentes()
            if isinstance(agentes, dict) and 'agentes' in agentes and isinstance(agentes['agentes'], dict):
                for nome_agente, info_agente in agentes['agentes'].items():
                    if isinstance(info_agente, dict):
                        st.markdown(f"- {info_agente.get('nome', nome_agente)} ({info_agente.get('status', 'desconhecido')})")
                    else:
                        st.warning(f"Formato inesperado para o agente {nome_agente}.")
            else:
                st.warning("Formato inesperado ao listar agentes.")
        except Exception as e:
            st.error(f"❌ Erro ao listar agentes: {e}")
        
        # Menu Principal
        st.header("📋 Menu")
        if st.button("📝 Gerenciar Arquivos"):
            st.switch_page("pages/arquivos.py")
        if st.button("📋 Gerenciar Tarefas"):
            st.switch_page("pages/tarefas.py")
        if st.button("📊 Relatórios"):
            st.switch_page("pages/relatorios.py")
        if st.button("⚙️ Configurações"):
            st.switch_page("pages/configuracoes.py")
        if st.button("🔑 API Keys"):
            st.switch_page("pages/api_keys.py")
        if st.button("📚 Documentação"):
            st.switch_page("pages/docs.py")
        
        # Status do Sistema
        st.header("💻 Status do Sistema")
        try:
            if 'agente_ia' in st.session_state and st.session_state.agente_ia is not None:
                agente_status = st.session_state.agente_ia.obter_status_agente()

                # --- Ollama (Executor) Status ---
                st.subheader("🔌 Provedor Executor: Ollama")
                ollama_status = agente_status.get('ollama', {})
                st.markdown(f"- **Modelo Executor:** {ollama_status.get('loaded_model', 'N/A')}")
                st.markdown(f"- Servidor Ollama: {'🟢 Online' if ollama_status.get('online', False) else '🔴 Offline'}")
                if ollama_status.get('online', False):
                    modelos_ollama_str = ", ".join(ollama_status.get('modelos_disponiveis', ['N/A']))
                    st.markdown(f"  - Modelos disponíveis: {modelos_ollama_str}")

                st.markdown("---") # Separator

                # --- OpenRouter (Coder) Status ---
                st.subheader("☁️ Provedor Coder: OpenRouter")
                openrouter_config_status = st.session_state.agente_ia.config.get('openrouter', {}).get('enabled', False)
                openrouter_api_status = agente_status.get('openrouter', {}) # Status da API do OpenRouter
                loaded_coder_model_name = agente_status.get('loaded_coder_model', 'N/A')

                st.markdown(f"- **Modelo Coder:** {loaded_coder_model_name}")
                st.markdown(f"- OpenRouter Habilitado (Config): {'✅ Sim' if openrouter_config_status else '❌ Não'}")
                st.markdown(f"- Status da API OpenRouter: {'🟢 Online' if openrouter_api_status.get('online', False) else '🔴 Offline'}")
                st.markdown(f"  - Mensagem: {openrouter_api_status.get('message', 'N/A')}")
                if openrouter_api_status.get('online', False):
                    st.markdown(f"  - Modelos disponíveis (OpenRouter): {openrouter_api_status.get('model_count', 'N/A')}")

                st.markdown("---") # Separator
            else:
                st.warning("Agente IA não inicializado. Status indisponível.")

            # Métricas do Sistema (do MCP Server, se houver)
            # Esta parte pode permanecer se as métricas do MCP são distintas das do agente
            if 'mcp_client' in st.session_state and st.session_state.mcp_client is not None:
                status_geral_mcp = st.session_state.mcp_client.obter_status()
                st.subheader("⚙️ Métricas do Sistema (MCP)")
                st.markdown(f"- CPU: {status_geral_mcp.get('cpu_uso', 'N/A')}%")
                st.markdown(f"- Memória: {status_geral_mcp.get('memoria_uso', 'N/A')}%")
                st.markdown(f"- Disco: {status_geral_mcp.get('disco_uso', 'N/A')}%")

        except AttributeError:
             st.warning("Agente IA ou seus componentes ainda não estão totalmente inicializados. Status parcial pode ser exibido.")
        except Exception as e:
            st.error(f"❌ Erro ao obter status do sistema: {e}")

# Interface principal
def main():
    # Exibir menu lateral
    exibir_menu()

    # Título
    st.title("🤖 AgenteIA")
    
    # Chat
    st.header("💬 Chat")

    # Seleção de perfil
    perfis = ["padrao", "coder", "criativo", "preciso"]
    perfil = st.selectbox(
        "Escolha o perfil do agente:",
        options=perfis,
        index=0
    )

    # Histórico de mensagens
    if 'mensagens' not in st.session_state:
        st.session_state.mensagens = []
    
    # Exibir mensagens
    for i, mensagem in enumerate(st.session_state.mensagens):
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])
            
            # Adicionar botões de feedback para mensagens do assistente que ainda não têm feedback
            if mensagem["role"] == "assistant" and not mensagem.get("feedback"):
                # Gerar um key único para os botões Streamlit
                col1, col2 = st.columns([0.05, 1]) # Ajuste as proporções conforme necessário
                
                with col1:
                    if st.button("👍", key=f"like_msg_{i}"):
                        # Chamar método do backend para registrar feedback positivo
                        # Assumindo que o histórico agora guarda o ID gerado pelo backend
                        # Precisamos garantir que o ID está sendo passado/guardado na session_state.mensagens
                        # Se o processar_mensagem agora retorna o objeto completo com ID, podemos usar message["id"]
                        message_id = mensagem.get("id") # Tenta obter o ID da mensagem
                        if message_id:
                            try:
                                st.session_state.agente_ia.registrar_feedback_mensagem(message_id, "positivo")
                                # Atualizar a session_state.mensagens para refletir o feedback
                                st.session_state.mensagens[i]["feedback"] = {"tipo": "positivo"}
                                st.rerun() # Rerun para atualizar a interface
                            except Exception as e:
                                st.error(f"Erro ao registrar feedback: {e}")
                        else:
                             st.warning("ID da mensagem não encontrado para registrar feedback.")

                with col2:
                     if st.button("👎", key=f"dislike_msg_{i}"):
                         # Chamar método do backend para registrar feedback negativo
                         message_id = mensagem.get("id") # Tenta obter o ID da mensagem
                         if message_id:
                             try:
                                 st.session_state.agente_ia.registrar_feedback_mensagem(message_id, "negativo")
                                 # Atualizar a session_state.mensagens para refletir o feedback
                                 st.session_state.mensagens[i]["feedback"] = {"tipo": "negativo"}
                                 st.rerun() # Rerun para atualizar a interface
                             except Exception as e:
                                 st.error(f"Erro ao registrar feedback: {e}")
                         else:
                             st.warning("ID da mensagem não encontrado para registrar feedback.")

            # Opcional: Mostrar feedback registrado
            if mensagem.get("feedback"):
                 feedback_tipo = mensagem["feedback"].get("tipo")
                 if feedback_tipo == "positivo":
                      st.caption("Você marcou como útil 👍")
                 elif feedback_tipo == "negativo":
                      st.caption("Você marcou como não útil 👎")

    # Input do usuário
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Adicionar mensagem do usuário
        st.session_state.mensagens.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Resposta do agente
        with st.chat_message("assistant"):
            with st.spinner("💬 Pensando..."):
                try:
                    resposta_obj = asyncio.run(st.session_state.agente_ia.processar_mensagem(prompt, perfil=perfil))
                    # Extrair apenas o texto da resposta
                    if hasattr(resposta_obj, 'content'):
                        resposta = resposta_obj.content
                    elif isinstance(resposta_obj, dict) and 'content' in resposta_obj:
                        resposta = resposta_obj['content']
                    else:
                        resposta = str(resposta_obj)
                    st.markdown(resposta)
                    st.session_state.mensagens.append({"role": "assistant", "content": resposta})
                except Exception as e:
                    st.error(f"❌ Erro ao processar mensagem: {e}")

if __name__ == "__main__":
    main() 