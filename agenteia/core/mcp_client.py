"""
Dummy MCPClient to allow tests to run.
"""

class MCPClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        # Add any other methods that are called in web.py with a pass or dummy return
        pass

    def distribuir_tarefa(self, tarefa: str, agente_id: str):
        # This method is used in agenteia/core/gerenciador_modelos.py,
        # though not directly by web.py, it's good to have a placeholder
        # if other parts of the system might try to use a client.
        print(f"Dummy MCPClient: distribuir_tarefa called with tarefa='{tarefa}', agente_id='{agente_id}'")
        return {"resultado": "dummy_mcp_client_response"}

    # Add other methods if import errors show they are needed by web.py or other files during test collection
    def some_other_method(self, *args, **kwargs):
        print(f"Dummy MCPClient: some_other_method called with args={args}, kwargs={kwargs}")
        return None
