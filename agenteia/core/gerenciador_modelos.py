"""
Gerenciador de Modelos - Coordena a comunicação entre diferentes modelos de IA
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
import json

from ..config import CONFIG
from ..logs import setup_logging
from .exceptions import AgenteError

logger = setup_logging(__name__)

class GerenciadorModelos:
    """Gerencia a comunicação e coordenação entre diferentes modelos."""
    
    def __init__(self, modelo_executor: str = "qwen3:1.7b", modelo_analise: str = None, mcp_client: Optional[Any] = None):
        """Inicializa o gerenciador de modelos."""
        self.logger = logger
        self.mcp_client = mcp_client
        
        # Configurar modelo executor (Qwen)
        self.modelo_executor = ChatOllama(
            model=modelo_executor,
            temperature=0.7,
            top_p=0.9
        )
        
        # Configurar modelo de análise (OpenRouter ou fallback para Qwen)
        self.modelo_analise = None
        if modelo_analise:
            if CONFIG.get("openrouter", {}).get("enabled", False):
                self.modelo_analise = self._configurar_openrouter(modelo_analise)
            else:
                self.modelo_analise = ChatOllama(
                    model=modelo_analise,
                    temperature=0.3,
                    top_p=0.9
                )
        
        self.historico_interacao = []
        self.logger.info(f"GerenciadorModelos inicializado com modelos: Executor={modelo_executor}, Análise={modelo_analise}")
        
    def _configurar_openrouter(self, modelo: str) -> ChatOpenAI:
        """Configura o modelo OpenRouter."""
        return ChatOpenAI(
            model_name=modelo,
            openai_api_base=CONFIG["openrouter"]["api_base"],
            openai_api_key=CONFIG["openrouter"]["api_key"],
            temperature=0.3
        )
        
    async def processar_tarefa(self, tarefa: str) -> str:
        """Processa uma tarefa usando ambos os modelos."""
        try:
            # Análise e planejamento com OpenRouter
            if self.modelo_analise:
                analise = await self.modelo_analise.ainvoke(
                    f"""Analise a seguinte tarefa e forneça um plano detalhado de execução:
                    
                    1. Estrutura necessária (pastas, arquivos)
                    2. Códigos necessários (se aplicável)
                    3. Explicações e documentação
                    4. Passos de execução
                    
                    Tarefa: {tarefa}
                    
                    Forneça a resposta em formato estruturado e detalhado."""
                )
                
                # Execução com Qwen via MCP
                if self.mcp_client:
                    # Preparar tarefa para o MCP
                    tarefa_mcp = {
                        "tipo": "execucao_qwen",
                        "plano": analise.content,
                        "tarefa_original": tarefa,
                        "instrucoes": """Execute a seguinte tarefa baseada no plano fornecido.
                        Sua função é criar a estrutura e os arquivos necessários.
                        Use as ferramentas disponíveis no MCP para executar as ações.
                        
                        Forneça apenas o resultado da execução, sem explicações adicionais."""
                    }
                    
                    # Enviar para o MCP
                    resultado = self.mcp_client.distribuir_tarefa(
                        tarefa=json.dumps(tarefa_mcp),
                        agente_id="Qwen Executor"
                    )
                    return resultado.get("resultado", "Erro ao executar tarefa via MCP")
                else:
                    # Fallback para execução direta se MCP não disponível
                    resultado = await self.modelo_executor.ainvoke(
                        f"""Execute a seguinte tarefa baseada no plano fornecido.
                        Sua função é criar a estrutura e os arquivos necessários.
                        
                        Plano de Execução:
                        {analise.content}
                        
                        Tarefa Original: {tarefa}
                        
                        Forneça apenas o resultado da execução, sem explicações adicionais."""
                    )
                    return resultado.content
            else:
                # Se não houver modelo de análise, usa apenas o executor
                return await self.modelo_executor.ainvoke(tarefa)
                
        except Exception as e:
            self.logger.error(f"Erro ao processar tarefa: {e}")
            raise
            
    def registrar_interacao(self, modelo: str, mensagem: str, resposta: str):
        """Registra interações entre modelos para aprendizado."""
        self.historico_interacao.append({
            "timestamp": datetime.now().isoformat(),
            "modelo": modelo,
            "mensagem": mensagem,
            "resposta": resposta
        })
        
    def obter_historico(self) -> list:
        """Retorna o histórico de interações."""
        return self.historico_interacao 