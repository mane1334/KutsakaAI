import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from agenteia.core.gerenciador_modelos import GerenciadorModelos
from agenteia.core.config import CONFIG

# Helper function to get a dummy config for testing
@pytest.fixture
def dummy_config_gerenciador():
    # Ensure this config is separate or merged with the main dummy_config if needed
    return {
        "openrouter": {
            "enabled": False,
            "api_base": "https://openrouter.ai/api/v1",
            "api_key": "test_openrouter_key",
            "modelo_geral": "openrouter/geral", # Add a default model for tests
        },
        "llm": { # Assuming this is where Ollama config might be, or adjust as per actual structure
            "model": "ollama/qwen3:1.7b" # Default executor model
        }
        # Add other necessary minimal configurations if GerenciadorModelos depends on them
    }

@pytest.fixture
def gerenciador_fixture(dummy_config_gerenciador):
    with patch.dict(CONFIG, dummy_config_gerenciador, clear=True), \
         patch("agenteia.core.gerenciador_modelos.ChatOllama") as MockChatOllama, \
         patch("agenteia.core.gerenciador_modelos.ChatOpenAI") as MockChatOpenAI, \
         patch("agenteia.core.gerenciador_modelos.setup_logging", return_value=MagicMock()):

        mock_ollama_llm = MagicMock()
        mock_ollama_llm.ainvoke = AsyncMock(return_value="Resultado do Ollama") # Mock async method
        MockChatOllama.return_value = mock_ollama_llm

        mock_openrouter_llm = MagicMock()
        # Mock the return of ainvoke to be an object with a 'content' attribute, like Langchain's AIMessage
        mock_ai_message = MagicMock()
        mock_ai_message.content = "Plano do OpenRouter"
        mock_openrouter_llm.ainvoke = AsyncMock(return_value=mock_ai_message)
        MockChatOpenAI.return_value = mock_openrouter_llm

        # Pass default model names, they will be used by the constructor
        gerenciador = GerenciadorModelos(
            modelo_executor=CONFIG["llm"]["model"],
            modelo_analise=CONFIG["openrouter"]["modelo_geral"] # Pass a default analysis model
        )
        gerenciador.mcp_client = MagicMock() # Mock MCP client for tests that use it
        yield gerenciador

def test_gerenciador_inicializacao_defaults(gerenciador_fixture):
    assert gerenciador_fixture.modelo_executor is not None
    # modelo_analise will be None if OpenRouter is disabled in the config by default
    if CONFIG["openrouter"]["enabled"]:
        assert gerenciador_fixture.modelo_analise is not None
    else:
        assert gerenciador_fixture.modelo_analise is None # Or specific fallback if implemented
    assert len(gerenciador_fixture.historico_interacao) == 0

@patch.dict(CONFIG["openrouter"], {"enabled": True, "api_key": "fake_key", "api_base": "fake_base", "modelo_geral": "custom/analise"})
@patch("agenteia.core.gerenciador_modelos.ChatOpenAI")
def test_gerenciador_inicializacao_com_openrouter_habilitado(MockChatOpenAI_local, gerenciador_fixture):
    # This test needs to re-initialize GerenciadorModelos with OpenRouter enabled in CONFIG
    # The fixture might run before this patch.dict, so we might need to re-instance or pass config.
    with patch("agenteia.core.gerenciador_modelos.ChatOllama"): # Keep Ollama mocked
        mock_or_instance = MagicMock()
        MockChatOpenAI_local.return_value = mock_or_instance

        gm = GerenciadorModelos(modelo_analise="custom/analise")
        assert gm.modelo_analise is mock_or_instance
        MockChatOpenAI_local.assert_called_with(
            model_name="custom/analise",
            openai_api_base=CONFIG["openrouter"]["api_base"],
            openai_api_key=CONFIG["openrouter"]["api_key"],
            temperature=0.3
        )

async def test_processar_tarefa_sem_modelo_analise(gerenciador_fixture):
    gerenciador_fixture.modelo_analise = None # Forçar ausência do modelo de análise
    tarefa = "Teste simples"
    resultado = await gerenciador_fixture.processar_tarefa(tarefa)
    assert resultado == "Resultado do Ollama" # Fallback para executor direto
    gerenciador_fixture.modelo_executor.ainvoke.assert_called_once_with(tarefa)

async def test_processar_tarefa_com_modelo_analise_e_mcp(gerenciador_fixture):
    # Garantir que modelo_analise está configurado (o fixture já faz isso se enabled)
    CONFIG["openrouter"]["enabled"] = True # Simular OpenRouter habilitado para este teste
    # Re-setup mocks for this specific scenario if needed, or ensure fixture does it.
    # The fixture's ChatOpenAI mock already returns an object with .content

    gerenciador_fixture.mcp_client.distribuir_tarefa.return_value = {"resultado": "Resultado do MCP"}

    tarefa = "Tarefa complexa"
    resultado = await gerenciador_fixture.processar_tarefa(tarefa)

    assert resultado == "Resultado do MCP"
    gerenciador_fixture.modelo_analise.ainvoke.assert_called_once()

    # Verificar a chamada ao mcp_client
    expected_mcp_call_args = json.loads(gerenciador_fixture.mcp_client.distribuir_tarefa.call_args[1]['tarefa'])
    assert expected_mcp_call_args["tipo"] == "execucao_qwen"
    assert expected_mcp_call_args["plano"] == "Plano do OpenRouter"
    assert expected_mcp_call_args["tarefa_original"] == tarefa

async def test_processar_tarefa_com_analise_sem_mcp(gerenciador_fixture):
    CONFIG["openrouter"]["enabled"] = True # Simular OpenRouter habilitado
    gerenciador_fixture.modelo_analise = MagicMock() # Usar um novo mock para modelo_analise
    mock_ai_message_analise = MagicMock()
    mock_ai_message_analise.content = "Plano Detalhado do OpenRouter"
    gerenciador_fixture.modelo_analise.ainvoke = AsyncMock(return_value=mock_ai_message_analise)

    gerenciador_fixture.mcp_client = None # Forçar ausência do MCP client

    tarefa = "Outra tarefa"
    # Mock para o modelo executor, pois será chamado diretamente
    gerenciador_fixture.modelo_executor.ainvoke = AsyncMock(return_value=MagicMock(content="Resultado direto do executor"))

    resultado_obj = await gerenciador_fixture.processar_tarefa(tarefa) # ainvoke agora retorna um obj com .content
    resultado = resultado_obj.content

    assert resultado == "Resultado direto do executor"
    gerenciador_fixture.modelo_analise.ainvoke.assert_called_once()
    expected_executor_prompt = f"""Execute a seguinte tarefa baseada no plano fornecido.
                        Sua função é criar a estrutura e os arquivos necessários.

                        Plano de Execução:
                        {mock_ai_message_analise.content}

                        Tarefa Original: {tarefa}

                        Forneça apenas o resultado da execução, sem explicações adicionais."""
    gerenciador_fixture.modelo_executor.ainvoke.assert_called_once_with(expected_executor_prompt)

async def test_processar_tarefa_erro_na_analise(gerenciador_fixture):
    CONFIG["openrouter"]["enabled"] = True
    gerenciador_fixture.modelo_analise = MagicMock()
    gerenciador_fixture.modelo_analise.ainvoke = AsyncMock(side_effect=Exception("Erro de análise"))

    with pytest.raises(Exception, match="Erro de análise"):
        await gerenciador_fixture.processar_tarefa("Tarefa que falha na análise")

def test_registrar_e_obter_historico(gerenciador_fixture):
    gerenciador_fixture.registrar_interacao("modelo_teste", "ping", "pong")
    historico = gerenciador_fixture.obter_historico()
    assert len(historico) == 1
    assert historico[0]["modelo"] == "modelo_teste"
    assert historico[0]["mensagem"] == "ping"
    assert historico[0]["resposta"] == "pong"
    assert "timestamp" in historico[0]
