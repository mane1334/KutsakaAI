# patch_openrouter.py
"""
Patch para corrigir problemas de compatibilidade com o OpenRouter
"""

import os
import sys
from pathlib import Path
import site
import subprocess
import importlib.util
from typing import Sequence

# Adicionado: Importações necessárias para bind_tools
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.runnables import Runnable

def find_site_packages():
    """Encontra o diretório site-packages."""
    # Primeiro tenta encontrar no ambiente virtual
    venv_path = os.getenv('VIRTUAL_ENV')
    if venv_path:
        venv_site_packages = Path(venv_path) / 'Lib' / 'site-packages'
        if venv_site_packages.exists():
            return str(venv_site_packages)
    
    # Se não encontrar no venv, usa o site-packages global
    return site.getsitepackages()[0]

def find_openrouter_file():
    """Encontra o arquivo do OpenRouter."""
    site_packages = find_site_packages()
    possible_paths = [
        Path(site_packages) / "langchain_openrouter" / "chat_models.py",
        Path(site_packages) / "langchain_openrouter" / "openrouter.py",
        Path(site_packages) / "langchain_openrouter" / "__init__.py"
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
            
    return None

def apply_patch():
    """Aplica o patch no arquivo do OpenRouter."""
    try:
        # Encontrar o arquivo
        openrouter_path = find_openrouter_file()
        
        if not openrouter_path:
            print("Arquivo do OpenRouter não encontrado. Tentando instalar...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "langchain-openrouter"], check=True)
                openrouter_path = find_openrouter_file()
                if not openrouter_path:
                    print("Não foi possível encontrar o arquivo mesmo após a instalação.")
                    return False
            except Exception as e:
                print(f"Erro ao instalar langchain-openrouter: {e}")
                return False
            
        print(f"Arquivo encontrado em: {openrouter_path}")
            
        # Ler o conteúdo atual
        with open(openrouter_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Verificar se o patch já foi aplicado
        if "def _generate" in content and "import openai" in content:
            print("Patch já foi aplicado anteriormente.")
            return True
            
        # Aplicar o patch
        new_content = """import os
from typing import Any, Dict, List, Optional, Union, cast

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
import openai

class ChatOpenRouter(BaseChatModel):
    \"\"\"ChatOpenRouter chat model integration.\"\"\"

    client: Any = None
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

    def __init__(self, **kwargs: Any):
        \"\"\"Initialize the ChatOpenRouter.\"\"\"
        super().__init__(**kwargs)
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers=self.headers
        )

    def _convert_message_to_dict(self, message: BaseMessage) -> Dict[str, Any]:
        \"\"\"Convert a message to a dictionary.\"\"\"
        if isinstance(message, HumanMessage):
            return {"role": "user", "content": message.content}
        elif isinstance(message, AIMessage):
            return {"role": "assistant", "content": message.content}
        elif isinstance(message, SystemMessage):
            return {"role": "system", "content": message.content}
        elif isinstance(message, ChatMessage):
            return {"role": message.role, "content": message.content}
        else:
            raise ValueError(f"Unknown message type: {type(message)}")

    def _convert_messages_to_dicts(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        \"\"\"Convert a list of messages to a list of dictionaries.\"\"\"
        return [self._convert_message_to_dict(message) for message in messages]

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        \"\"\"Generate a response from the model.\"\"\"
        message_dicts = self._convert_messages_to_dicts(messages)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=message_dicts,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stop=stop,
            **kwargs
        )
        
        message = response.choices[0].message
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(content=message.content),
                    generation_info=dict(finish_reason=response.choices[0].finish_reason),
                )
            ],
            llm_output=dict(
                model_name=self.model,
                token_usage=dict(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                ),
            ),
        )

    @property
    def _llm_type(self) -> str:
        \"\"\"Return the type of LLM.\"\"\"
        return "openrouter"

    # PATCHED_BIND_TOOLS_START
    
    # Implementação básica do método bind_tools para compatibilidade com create_tool_calling_agent
    def bind_tools(self, tools: Sequence[BaseTool], **kwargs) -> Runnable:
        # Esta é uma simulação. Em uma implementação real, isso configuraria o LLM
        # para entender e usar as ferramentas, possivelmente modificando o prompt ou
        # habilitando o modo de tool calling na chamada da API.
        print(f"DEBUG: bind_tools chamado com {len(tools)} ferramentas.")
        # Retornamos o próprio objeto LLM (self) encadeado de alguma forma para indicar as ferramentas.
        # Uma implementação mais completa precisaria converter BaseTool para o formato da API OpenRouter
        # e configurar a chamada da API para usar essas ferramentas.
        # Por enquanto, apenas anexamos as ferramentas para que possam ser acessadas posteriormente se necessário.
        self._bound_tools = tools
        
        # Em um cenário ideal, a resposta do invoke/stream seria formatada para tool_calls
        # pela própria LLM, após bind_tools ser chamado.
        # Como isso não acontece nativamente em muitos LLMs, o agente rely na saída formatada
        # pelo próprio modelo ou tenta inferir.
        
        # Retorna o próprio objeto LLM como um Runnable com as ferramentas "associadas"
        return self
        
    # PATCHED_BIND_TOOLS_END
"""
        
        # Salvar as alterações
        with open(openrouter_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("Patch aplicado com sucesso!")
        return True
        
    except Exception as e:
        print(f"Erro ao aplicar patch: {e}")
        return False

if __name__ == "__main__":
    apply_patch()