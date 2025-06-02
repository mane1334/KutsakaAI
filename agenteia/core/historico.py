"""
Gerenciamento de histórico do Agente IA
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..logs import setup_logging
from .exceptions import HistoryError
import uuid

logger = setup_logging(__name__, 'historico.log')

class HistoricoManager:
    """Gerencia o histórico de conversas do agente."""
    
    def __init__(self, max_mensagens: int = 100):
        """
        Inicializa o gerenciador de histórico.
        
        Args:
            max_mensagens: Número máximo de mensagens a manter em memória
        """
        self.max_mensagens = max_mensagens
        self.historico: List[Dict[str, Any]] = []
        self.historico_dir = "historico"
        
        if not os.path.exists(self.historico_dir):
            os.makedirs(self.historico_dir)
    
    def adicionar_mensagem(self, tipo: str, conteudo: str, message_id: str = None) -> str:
        """
        Adiciona uma mensagem ao histórico.
        
        Args:
            tipo: Tipo da mensagem (ex: "usuario", "agente", "sistema")
            conteudo: Conteúdo da mensagem
            message_id: ID opcional da mensagem (se não fornecido, será gerado)
            
        Returns:
            str: ID da mensagem adicionada
        """
        try:
            # Gerar ID único se não fornecido
            if not message_id:
                message_id = str(uuid.uuid4())
                
            # Criar mensagem com ID e timestamp
            mensagem = {
                'id': message_id,
                'role': tipo,
                'content': conteudo,
                'timestamp': datetime.now().isoformat()
            }
            
            self.historico.append(mensagem)
            
            if len(self.historico) > self.max_mensagens:
                self.historico.pop(0)
                
            logger.debug(f"Mensagem adicionada ao histórico com ID: {message_id}")
            return message_id
                
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem: {str(e)}")
            raise HistoryError(f"Erro ao adicionar mensagem: {str(e)}")
    
    def obter_historico(self) -> List[Dict[str, Any]]:
        """Retorna o histórico completo."""
        return self.historico
    
    def limpar_historico(self) -> None:
        """Limpa o histórico em memória."""
        self.historico = []
    
    def salvar_historico(self, nome: str = None) -> str:
        """
        Salva o histórico em um arquivo JSON.
        
        Args:
            nome: Nome do arquivo (opcional)
            
        Returns:
            str: Caminho do arquivo salvo
        """
        try:
            if not nome:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                nome = f"historico_{timestamp}.json"
            
            caminho = os.path.join(self.historico_dir, nome)
            
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(self.historico, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Histórico salvo em: {caminho}")
            return caminho
            
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {str(e)}")
            raise HistoryError(f"Erro ao salvar histórico: {str(e)}")
    
    def carregar_historico(self, nome: str) -> None:
        """
        Carrega o histórico de um arquivo JSON.
        
        Args:
            nome: Nome do arquivo
        """
        try:
            caminho = os.path.join(self.historico_dir, nome)
            
            if not os.path.exists(caminho):
                raise HistoryError(f"Arquivo de histórico não encontrado: {caminho}")
            
            with open(caminho, 'r', encoding='utf-8') as f:
                self.historico = json.load(f)
            
            logger.info(f"Histórico carregado de: {caminho}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {str(e)}")
            raise HistoryError(f"Erro ao decodificar JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao carregar histórico: {str(e)}")
            raise HistoryError(f"Erro ao carregar histórico: {str(e)}")
    
    def listar_historicos(self) -> List[str]:
        """
        Lista todos os arquivos de histórico disponíveis.
        
        Returns:
            List[str]: Lista de nomes de arquivos
        """
        try:
            return [f for f in os.listdir(self.historico_dir) if f.endswith('.json')]
        except Exception as e:
            logger.error(f"Erro ao listar históricos: {str(e)}")
            raise HistoryError(f"Erro ao listar históricos: {str(e)}") 