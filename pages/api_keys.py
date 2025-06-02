"""
Página de gerenciamento de API Keys
"""

import streamlit as st
import os
from agenteia.core.config import CONFIG

st.set_page_config(
    page_title="API Keys - AgenteIA",
    page_icon="🔑",
    layout="wide"
)

st.title("🔑 Gerenciamento de API Keys")

# OpenRouter API Key
st.header("🌐 OpenRouter")
openrouter_key = st.text_input(
    "API Key do OpenRouter",
    value=CONFIG["openrouter"].get("api_key", ""),
    type="password"
)

if st.button("💾 Salvar OpenRouter Key"):
    try:
        CONFIG["openrouter"]["api_key"] = openrouter_key
        os.environ["OPENROUTER_API_KEY"] = openrouter_key
        st.success("✅ API Key do OpenRouter salva com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao salvar API Key: {e}")

# Outras APIs podem ser adicionadas aqui
st.header("🔐 Outras APIs")
st.info("""
### APIs Disponíveis:
- OpenRouter (para modelos de linguagem)
- OpenAI (em breve)
- Anthropic (em breve)
- Google AI (em breve)
""")

# Instruções
st.markdown("---")
st.markdown("""
### 📝 Instruções
1. Obtenha suas API Keys nos respectivos sites
2. Cole as keys nos campos acima
3. Clique em Salvar para cada API
4. As keys são armazenadas localmente e de forma segura
""") 