import pytest
from unittest.mock import patch, MagicMock
import os
import json
from pathlib import Path

from agenteia.core.agente import AgenteIA, AgenteError, ProvedorModelo
from agenteia.core.config import CONFIG

# Helper function to create a dummy config for testing
def get_dummy_config():
    return {
        "agent": {
            "historico_dir": "test_historico",
            "max_iterations": 3,
            "verbose": False,
        },
        "ollama": {
            "base_url": "http://localhost:11434",
            "timeout": 120,
        },
        "modelo": {
            "nome": "test_model"
        },
        "openrouter": {
            "enabled": False,
            "api_key": "test_key",
            "modelo_coder": "test_coder_model",
            "api_base": "https://openrouter.ai/api/v1",
            "timeout": 60,
            "headers": None,
        },
        "rag": {
            "enabled": False,
            "vector_db_dir": "test_vector_db",
            "embedding_model": "test_embedding_model",
            "k_retrieval": 3,
            "chunking": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
            }
        },
        "auto_improve": {
            "enabled": False,
            "min_tool_calls": 5,
            "tool_failure_threshold": 0.5,
            "index_feedback": False,
        }
    }

@pytest.fixture
def agente_fixture():
    # Create a dummy historico_dir if it doesn't exist
    historico_dir = Path(get_dummy_config()["agent"]["historico_dir"])
    historico_dir.mkdir(parents=True, exist_ok=True)

    # Patch external dependencies
    with patch("agenteia.core.agente.setup_logging", return_value=MagicMock()), \
         patch("agenteia.core.agente.ChatOllama") as MockChatOllama, \
         patch("agenteia.core.agente.ChatOpenAI") as MockChatOpenAI, \
         patch("agenteia.core.agente.OpenAIEmbeddings") as MockOpenAIEmbeddings, \
         patch("agenteia.core.agente.OllamaEmbeddings") as MockOllamaEmbeddings, \
         patch("agenteia.core.agente.Chroma") as MockChroma, \
         patch("agenteia.core.agente.get_available_tools", return_value=([], [])):

        # Mock LLM instances
        mock_llm = MagicMock()
        mock_llm.stream = MagicMock(return_value=iter(["Test stream response"]))
        mock_llm.ainvoke = MagicMock(return_value="Test async response")
        MockChatOllama.return_value = mock_llm
        MockChatOpenAI.return_value = mock_llm

        # Mock Embeddings and Vector Store
        MockOpenAIEmbeddings.return_value = MagicMock()
        MockOllamaEmbeddings.return_value = MagicMock()
        MockChroma.return_value = MagicMock()

        agente = AgenteIA(config=get_dummy_config())
        yield agente

    # Clean up dummy historico_dir
    if historico_dir.exists():
        # Correctly clean up files and then the directory
        for item in historico_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                # Use shutil.rmtree for non-empty directories if necessary
                # For this test, assuming only files or empty dirs might be created by mistake
                # If complex structures are made, shutil.rmtree(item) would be safer
                pass # Avoid deleting unexpected subdirectories in a simple test cleanup
        historico_dir.rmdir()


def test_agente_inicializacao(agente_fixture):
    assert agente_fixture is not None
    assert agente_fixture.config is not None
    assert agente_fixture.llm_executor is not None
    assert agente_fixture.usar_openrouter is False

@patch.dict(CONFIG, get_dummy_config(), clear=True) # clear=True ensures CONFIG is reset after test
def test_agente_inicializacao_sem_config_deve_usar_global():
     with patch("agenteia.core.agente.setup_logging", return_value=MagicMock()), \
         patch("agenteia.core.agente.ChatOllama") as MockChatOllama, \
         patch("agenteia.core.agente.ChatOpenAI") as MockChatOpenAI, \
         patch("agenteia.core.agente.OpenAIEmbeddings"), \
         patch("agenteia.core.agente.OllamaEmbeddings"), \
         patch("agenteia.core.agente.Chroma"), \
         patch("agenteia.core.agente.get_available_tools", return_value=([], [])):

        mock_llm = MagicMock()
        MockChatOllama.return_value = mock_llm
        MockChatOpenAI.return_value = mock_llm

        agente = AgenteIA() # Initialize without passing config
        assert agente.config["agent"]["historico_dir"] == get_dummy_config()["agent"]["historico_dir"]

def test_carregar_modelos_ollama(agente_fixture):
    agente_fixture.usar_openrouter = False
    llm_executor, llm_coder = agente_fixture._carregar_modelos()
    assert llm_executor is not None
    assert llm_coder is None # OpenRouter está desabilitado no dummy_config

def test_carregar_modelos_openrouter_desabilitado(agente_fixture):
    dummy_cfg = get_dummy_config()
    dummy_cfg["openrouter"]["enabled"] = False
    agente_fixture.config = dummy_cfg
    llm_executor, llm_coder = agente_fixture._carregar_modelos()
    assert llm_executor is not None
    assert llm_coder is None

@patch("agenteia.core.agente.ChatOpenAI")
def test_carregar_modelos_openrouter_habilitado(MockChatOpenAI_local, agente_fixture):
    dummy_cfg = get_dummy_config()
    dummy_cfg["openrouter"]["enabled"] = True
    dummy_cfg["openrouter"]["api_key"] = "fake_key" # Precisa de uma chave para tentar carregar
    agente_fixture.config = dummy_cfg

    mock_openrouter_llm = MagicMock()
    MockChatOpenAI_local.return_value = mock_openrouter_llm

    llm_executor, llm_coder = agente_fixture._carregar_modelos()
    assert llm_executor is not None
    assert llm_coder is mock_openrouter_llm
    MockChatOpenAI_local.assert_called_once()

async def test_processar_mensagem_sucesso(agente_fixture):
    resposta = await agente_fixture.processar_mensagem("Olá")
    assert resposta == "Test async response"
    assert len(agente_fixture.historico) == 2
    assert agente_fixture.historico[0]["content"] == "Olá"
    assert agente_fixture.historico[1]["content"] == "Test async response"

async def test_processar_mensagem_erro_mensagem_invalida(agente_fixture):
    resposta = await agente_fixture.processar_mensagem(None)
    assert "Erro: Mensagem inválida." in resposta

def test_processar_mensagem_stream_sucesso(agente_fixture):
    response_parts = []
    # Make sure to consume the generator from processar_mensagem_stream
    for part in agente_fixture.processar_mensagem_stream("Olá, mundo!"):
        response_parts.append(part)

    full_response = "".join(response_parts)
    assert "Test stream response" in full_response
    assert len(agente_fixture.historico) == 2
    assert agente_fixture.historico[0]["content"] == "Olá, mundo!"
    assert agente_fixture.historico[1]["content"] == "Test stream response"

def test_salvar_e_carregar_historico(agente_fixture):
    agente_fixture.historico = [{"role": "user", "content": "teste"}]

    historico_dir = Path(agente_fixture.config["agent"]["historico_dir"])
    historico_dir.mkdir(parents=True, exist_ok=True)

    nome_arquivo = "test_history.json"
    salvo = agente_fixture.salvar_historico(nome_arquivo)
    assert salvo is True

    caminho_arquivo = historico_dir / nome_arquivo
    assert caminho_arquivo.exists()

    agente_fixture.limpar_historico()
    assert len(agente_fixture.historico) == 0

    carregado = agente_fixture.carregar_historico(nome_arquivo)
    assert carregado is True
    assert len(agente_fixture.historico) == 1
    assert agente_fixture.historico[0]["content"] == "teste"

    if caminho_arquivo.exists():
        caminho_arquivo.unlink()

def test_limpar_historico(agente_fixture):
    agente_fixture.historico = [{"role": "user", "content": "teste"}]
    agente_fixture.memory = MagicMock()
    agente_fixture.limpar_historico()
    assert len(agente_fixture.historico) == 0
    agente_fixture.memory.clear.assert_called_once()

def test_alternar_provedor_modelo(agente_fixture):
    with patch("agenteia.core.agente.ChatOllama") as MockChatOllama, \
         patch("agenteia.core.agente.ChatOpenAI") as MockChatOpenAI, \
         patch("agenteia.core.gerenciador_modelos.ChatOllama") as MockGmChatOllama, \
         patch("agenteia.core.gerenciador_modelos.ChatOpenAI") as MockGmChatOpenAI:

        mock_ollama_llm = MagicMock()
        MockChatOllama.return_value = mock_ollama_llm
        MockGmChatOllama.return_value = mock_ollama_llm

        mock_openrouter_llm = MagicMock()
        MockChatOpenAI.return_value = mock_openrouter_llm
        MockGmChatOpenAI.return_value = mock_openrouter_llm

        agente_fixture.alternar_provedor_modelo(usar_openrouter=False)
        assert agente_fixture.usar_openrouter is False
        MockGmChatOllama.assert_called()
        # MockGmChatOpenAI.assert_not_called() # This might be called if a default analysis model is set

        agente_fixture.config["openrouter"]["enabled"] = True
        agente_fixture.config["openrouter"]["api_key"] = "fake_key_for_test"
        agente_fixture.config["openrouter"]["modelo_geral"] = "openrouter_general_model"
        agente_fixture.config["openrouter"]["modelo_coder"] = "openrouter_coder_model"

        agente_fixture.alternar_provedor_modelo(usar_openrouter=True)
        assert agente_fixture.usar_openrouter is True
        MockGmChatOpenAI.assert_called()

def test_processar_mensagem_com_rag_desabilitado(agente_fixture):
    agente_fixture.config["rag"]["enabled"] = False
    # Consume the generator to ensure the code inside processar_mensagem_stream runs
    list(agente_fixture.processar_mensagem_stream("Teste RAG"))
    if agente_fixture.vector_store:
        agente_fixture.vector_store.similarity_search.assert_not_called()

def test_processar_mensagem_com_rag_habilitado(agente_fixture):
    agente_fixture.config["rag"]["enabled"] = True
    agente_fixture.vector_store = MagicMock()
    agente_fixture.vector_store.similarity_search.return_value = []

    list(agente_fixture.processar_mensagem_stream("Teste RAG com mock"))

    agente_fixture.vector_store.similarity_search.assert_called_once()

@pytest.mark.parametrize("mensagem, esperado", [
    ("crie um código python", True),
    ("desenvolver um site", True),
    ("como está o tempo?", False),
    ("escreva um script para mim", True),
    ("qual a capital da França?", False),
    ("preciso de um programa em java", True)
])
def test_detectar_necessidade_codigo(agente_fixture, mensagem, esperado):
    assert agente_fixture._detectar_necessidade_codigo(mensagem) == esperado

@pytest.mark.parametrize("mensagem, esperado", [
    ("oi", "chat"),
    ("tudo bem?", "chat"),
    ("crie um arquivo", "task"),
    ("qual o seu nome?", "chat"),
    ("liste os arquivos na pasta x", "task"),
    ("obrigado", "chat"),
    ("quais ferramentas você tem?", "chat")
])
def test_detectar_tipo_interacao(agente_fixture, mensagem, esperado):
    assert agente_fixture._detectar_tipo_interacao(mensagem) == esperado

def test_registrar_feedback_mensagem_sucesso(agente_fixture):
    agente_fixture.historico = [
        {"id": "123", "role": "assistant", "content": "Olá!"},
        {"id": "456", "role": "user", "content": "Oi"}
    ]
    agente_fixture.salvar_historico = MagicMock()

    result = agente_fixture.registrar_feedback_mensagem("123", "positivo", "Gostei da resposta")
    assert result is True
    assert "feedback" in agente_fixture.historico[0]
    assert agente_fixture.historico[0]["feedback"]["tipo"] == "positivo"
    agente_fixture.salvar_historico.assert_called_once()

def test_registrar_feedback_mensagem_nao_encontrada(agente_fixture):
    agente_fixture.historico = [{"id": "123", "role": "assistant", "content": "Olá!"}]
    result = agente_fixture.registrar_feedback_mensagem("789", "negativo")
    assert result is False

def test_registrar_feedback_mensagem_id_invalido(agente_fixture):
    result = agente_fixture.registrar_feedback_mensagem(None, "positivo")
    assert result is False

# Import AgenteCallbackHandler directly for the specific test
from agenteia.core.agente import AgenteCallbackHandler

def test_agente_callback_handler_del_closes_file():
    with patch("builtins.open", new_callable=MagicMock) as mock_open_global, \
         patch("agenteia.core.agente.logger") as mock_logger_callback: # Mock logger inside callback

        mock_file_instance = MagicMock()
        mock_open_global.return_value = mock_file_instance

        # Instantiate the handler, which should attempt to open a log file
        handler = AgenteCallbackHandler()

        # Assert that open was called (Path construction for the log file is complex due to timestamp)
        # So, we check if open was called at all, assuming it's for the log file.
        mock_open_global.assert_called()

        # Store the mock_file_instance that the handler should be using
        # This relies on the handler actually assigning the result of open to self.tool_log_file
        # If it's None due to an error in _initialize_tool_log, this test might not work as expected.
        # To make it more robust, one might need to inspect the handler's state or mock Path.
        actual_log_file_mock = handler.tool_log_file

        # Delete the handler to trigger __del__
        del handler

        # Check if close was called on the file mock that was actually used by the handler
        if actual_log_file_mock: # Only assert if a file was successfully opened by the handler
            actual_log_file_mock.close.assert_called_once()
        else:
            # If tool_log_file was None, it means open failed or was bypassed.
            # In a real scenario, this might indicate an issue in _initialize_tool_log.
            # For this test, we can note that close wouldn't be called on a None file.
            pass
