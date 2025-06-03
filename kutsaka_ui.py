import streamlit as st
import requests
import json
from datetime import datetime
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="KutsakaAI - ChatGPT-Style",
    layout="wide",
    initial_sidebar_state="collapsed" # Start collapsed, user can open it
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* ... (CSS as defined in previous step - ensure it's complete and correct) ... */
    .stApp { background-color: #f0f2f6; }
    .message-user-container { display: flex; justify-content: flex-end; margin-bottom: 8px; padding-right: 10px; }
    .message-user { background-color: #dbeafe; border-radius: 18px 18px 5px 18px; padding: 10px 15px; max-width: 75%; color: #1f2937; word-wrap: break-word; box-shadow: 0 1px 1px rgba(0,0,0,0.03); }
    .message-assistant-container { display: flex; justify-content: flex-start; margin-bottom: 8px; padding-left: 10px; }
    .message-assistant { background-color: #ffffff; border-radius: 18px 18px 18px 5px; padding: 10px 15px; max-width: 75%; color: #374151; box-shadow: 0 1px 2px rgba(0,0,0,0.05); word-wrap: break-word; }
    .stChatInputContainer { background-color: #f0f2f6; border-top: 1px solid #d1d5db; }
    .main .block-container { padding-bottom: 5rem; padding-top: 2rem; } /* Added padding-top */
    .stButton>button { /* Basic button styling example */
        border-radius: 8px;
        padding: 0.5em 1em;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize session state variables ---
if 'messages' not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Olá! Sou o KutsakaAI, como posso ajudar?"}]
if 'api_key' not in st.session_state: # Loaded from secrets
    try: st.session_state.api_key = st.secrets["API_KEY"]
    except (FileNotFoundError, KeyError): st.session_state.api_key = None
if 'selected_provider' not in st.session_state:
    st.session_state.selected_provider = "OpenRouter"
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "mistralai/mistral-7b-instruct"
if 'last_response_data' not in st.session_state:
    st.session_state.last_response_data = None # To store full API response for moderation check etc.
if 'total_tokens_session' not in st.session_state:
    st.session_state.total_tokens_session = 0
if 'total_cost_session' not in st.session_state:
    st.session_state.total_cost_session = 0.0


# --- Backend API URL ---
BACKEND_API_URL = st.secrets.get("BACKEND_API_URL", "http://localhost:3000/api/chat")

# --- Input Sanitization Function ---
def sanitize_input(text: str) -> str:
    if not isinstance(text, str): return ""
    cleaned = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE)
    return cleaned[:2000]

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Configurações")

    OPENAI_MODELS = ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"] # Example models
    OPENROUTER_MODELS = [
        "mistralai/mistral-7b-instruct", "google/gemini-pro",
        "anthropic/claude-2", "openai/gpt-4-turbo"
    ]

    current_provider_index = ["OpenRouter", "OpenAI"].index(st.session_state.selected_provider)
    model_options_for_current_provider = OPENAI_MODELS if st.session_state.selected_provider == "OpenAI" else OPENROUTER_MODELS

    try: current_model_index_for_render = model_options_for_current_provider.index(st.session_state.selected_model)
    except ValueError:
        st.session_state.selected_model = model_options_for_current_provider[0]
        current_model_index_for_render = 0

    def provider_changed_callback():
        st.session_state.selected_provider = st.session_state.provider_selectbox_key
        if st.session_state.selected_provider == "OpenAI":
            st.session_state.selected_model = OPENAI_MODELS[0]
        else:
            st.session_state.selected_model = OPENROUTER_MODELS[0]

    st.selectbox("Provedor IA", ["OpenRouter", "OpenAI"], index=current_provider_index, key="provider_selectbox_key", on_change=provider_changed_callback)

    # Re-evaluate options for model_selectbox after provider might have changed
    model_options_display = OPENAI_MODELS if st.session_state.selected_provider == "OpenAI" else OPENROUTER_MODELS
    try:
        current_model_idx_display = model_options_display.index(st.session_state.selected_model)
    except ValueError: # Fallback if current model not in new list (should be handled by callback)
        current_model_idx_display = 0
        st.session_state.selected_model = model_options_display[0]


    st.selectbox("Modelo", model_options_display, index=current_model_idx_display, key="model_selectbox_key")
    st.session_state.selected_model = st.session_state.model_selectbox_key

    # --- Cost Panel (Premium Feature) ---
    st.divider()
    st.subheader("📊 Métricas da Sessão")
    st.metric("Total Tokens (Sessão)", f"{st.session_state.total_tokens_session}")
    st.metric("Custo Estimado (Sessão)", f"${st.session_state.total_cost_session:.6f}")

    # --- Export Chat Button (Premium Feature) ---
    st.divider()
    # Prepare data for download
    chat_export_data = json.dumps(st.session_state.messages, indent=2)
    st.download_button(
        label="📥 Exportar Chat (.json)",
        data=chat_export_data,
        file_name=f"kutsaka_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

    st.divider()
    st.caption(f"🔄 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")


# --- Main Chat Area (Message Display) ---
chat_display_container = st.container()

# --- Content Moderation Warning (Premium Feature) ---
if st.session_state.last_response_data:
    # Assuming the backend response 'data' (stored in last_response_data)
    # might have a 'moderation_info' or similar field.
    # This is a placeholder for how such a flag would be checked.
    # The actual flag name and structure depend on your backend API.
    if st.session_state.last_response_data.get('moderation_info', {}).get('flagged', False):
        st.warning("⚠️ Conteúdo da última resposta foi filtrado ou sinalizado por políticas de moderação.", icon="🛡️")
    # Example: if your backend returns something like: "quality_warnings": ["moderate_toxicity"]
    if st.session_state.last_response_data.get('quality_warnings'):
         warnings_str = ", ".join(st.session_state.last_response_data.get('quality_warnings'))
         st.info(f"🔍 Avisos de qualidade da IA: {warnings_str}", icon="ℹ️")


with chat_display_container:
    # ... (message display loop as in previous step) ...
    for msg_idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            content_to_display = msg.get("content", "")
            if msg["role"] == "user":
                st.markdown(f'<div class="message-user-container"><div class="message-user">{st.markdown(content_to_display)}</div></div>', unsafe_allow_html=True)
            else: # Assistant
                st.markdown(f'<div class="message-assistant-container"><div class="message-assistant">{st.markdown(content_to_display)}</div></div>', unsafe_allow_html=True)

            if msg["role"] == "assistant":
                cost_val = msg.get('cost', 0.0); tokens_val = msg.get('tokens', 0)
                try: cost_val = float(cost_val if cost_val is not None else 0.0)
                except ValueError: cost_val = 0.0
                try:
                    if isinstance(tokens_val, dict):
                        tokens_val = int(tokens_val.get('total_tokens',0))
                    else:
                        tokens_val = int(tokens_val if tokens_val is not None else 0)
                except (ValueError, TypeError): tokens_val = 0

                if cost_val > 0 or tokens_val > 0:
                    st.caption(f"🪙 Tokens: {tokens_val} | 💰 Custo: ${cost_val:.6f}")


# --- User Input and API Call Logic ---
user_input_text = st.chat_input("Digite sua mensagem...")

if user_input_text:
    sanitized_input = sanitize_input(user_input_text)

    if not st.session_state.api_key:
        st.error("API Key não configurada. Não é possível enviar a mensagem.")
    elif not sanitized_input.strip():
        st.warning("Por favor, digite uma mensagem.")
    else:
        st.session_state.messages.append({"role": "user", "content": sanitized_input})

        api_payload = {
            "messages": st.session_state.messages[-10:],
            "provider": st.session_state.selected_provider.lower(),
            "model": st.session_state.selected_model,
            "max_tokens": 1000
        }
        api_headers = {"Authorization": f"Bearer {st.session_state.api_key}", "Content-Type": "application/json"}

        try:
            with st.spinner("KutsakaAI está pensando..."):
                response = requests.post(BACKEND_API_URL, json=api_payload, headers=api_headers, timeout=60)

            st.session_state.last_response_data = None # Clear previous response data initially
            if response.status_code == 200:
                data = response.json()
                st.session_state.last_response_data = data # Store new response

                assistant_msg_content = "Desculpe, não consegui processar a resposta."
                if data.get("choices") and isinstance(data["choices"], list) and len(data["choices"]) > 0:
                    first_choice = data["choices"][0]
                    if first_choice.get("message") and isinstance(first_choice["message"], dict):
                        assistant_msg_content = first_choice["message"].get("content", assistant_msg_content)

                usage_data = data.get("usage", {})
                tokens_data = usage_data.get("total_tokens") if isinstance(usage_data, dict) else None
                cost_data = data.get("cost")

                try: current_tokens = int(tokens_data if tokens_data is not None else 0)
                except (ValueError, TypeError): current_tokens = 0
                try: current_cost = float(cost_data if cost_data is not None else 0.0)
                except (ValueError, TypeError): current_cost = 0.0

                # Update session totals
                st.session_state.total_tokens_session += current_tokens
                st.session_state.total_cost_session += current_cost

                st.session_state.messages.append({
                    "role": "assistant", "content": assistant_msg_content,
                    "tokens": current_tokens, "cost": current_cost
                })
            else: # Error from API
                error_details_msg = f"Erro da API: {response.status_code}"
                try:
                    error_json = response.json()
                    specific_error = error_json.get("error", {}).get("message") or error_json.get("message") or response.reason
                    error_details_msg += f" - {specific_error}"
                except json.JSONDecodeError: # If response is not JSON
                    error_details_msg += f" - {response.text or response.reason}" # Show text or reason

                st.error(error_details_msg)
                st.session_state.messages.append({"role": "assistant", "content": f"Erro: {response.status_code}. Consulte o log de erros para detalhes."})

            st.rerun() # Rerun to display new messages and update sidebar metrics

        except requests.exceptions.Timeout:
            st.error("Timeout: A requisição demorou muito para responder.")
            st.session_state.messages.append({"role": "assistant", "content": "Erro: Timeout ao tentar comunicar com o backend."})
            st.rerun()
        except requests.exceptions.RequestException as e:
            st.error(f"Erro de conexão: {e}")
            st.session_state.messages.append({"role": "assistant", "content": "Erro de conexão ao tentar falar com o backend."})
            st.rerun()
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")
            st.session_state.messages.append({"role": "assistant", "content": "Ocorreu um erro inesperado."})
            st.rerun()

# --- Display API Key Error ---
if not st.session_state.api_key and 'warning_api_key_shown' not in st.session_state:
    st.error("Backend API Key is not configured...")
    st.session_state.warning_api_key_shown = True
