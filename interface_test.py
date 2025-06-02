import streamlit as st
import sys
from agenteia.logs import setup_logging # Added

# Configure logging using AgenteIA's setup
logger = setup_logging(__name__) # Changed

logger.info(f"MINIMAL_APP_LOG: interface_test.py (with AgenteIA logging) execution started. sys.argv: {sys.argv}")

def run_minimal_app():
    st.set_page_config(
        page_title="Minimal Test App (AgenteIA Log)",
        page_icon="🧪",
        layout="wide"
    )
    st.title("Minimal Streamlit Test Page (AgenteIA Log)")
    st.write("If you see this, basic Streamlit with AgenteIA logging is working.")
    logger.info("MINIMAL_APP_LOG: Minimal Streamlit app (AgenteIA logging) has run.")

if __name__ == "__main__":
    try:
        logger.info("MINIMAL_APP_LOG: Entering __main__ block (AgenteIA logging).")
        run_minimal_app()
    except Exception as e:
        logger.critical(f"MINIMAL_APP_LOG: Error in minimal_app (AgenteIA logging): {e}", exc_info=True)
        st.error(f"A critical error occurred (AgenteIA logging): {e}")
    finally:
        logger.info("MINIMAL_APP_LOG: Exiting __main__ block (AgenteIA logging).")
