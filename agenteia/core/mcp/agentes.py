"""
Módulo de gerenciamento de agentes para o MCP Server.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import json

from ..logs import setup_logging
from ..exceptions import AgenteError
from .monitor import MonitorProgresso
from ..agente import ProvedorModelo

class GerenciadorAgentes:
    """Gerencia o registro e execução de agentes."""
    
    def __init__(self, monitor: MonitorProgresso):
        """Inicializa o gerenciador de agentes."""
        self.logger = setup_logging(__name__)
        self.monitor = monitor
        self._agentes: Dict[str, Dict[str, Any]] = {}
        self._historico_tarefas: Dict[str, List[Dict[str, Any]]] = {}
        
    def registrar(self, nome: str, agente: Any) -> bool:
        """Registra um novo agente."""
        try:
            if nome in self._agentes:
                self.logger.warning(f"Agente {nome} já registrado, atualizando...")
                
            self._agentes[nome] = {
                'objeto': agente,
                'registro': datetime.now(),
                'tarefas': 0,
                'erros': 0,
                'ultima_tarefa': None,
                'especialidades': getattr(agente, 'especialidades', []),
                'status': 'ativo',
                'provedor_modelo': getattr(agente, 'provedor_atual', None),
                'modelo_geral': getattr(getattr(agente, 'llm_geral', None), 'model_name', None) if getattr(agente, 'provedor_atual', None) == ProvedorModelo.OPENROUTER else getattr(getattr(agente, 'llm_geral', None), 'model', None),
                'modelo_coder': getattr(getattr(agente, 'llm_coder', None), 'model_name', None) if getattr(agente, 'provedor_atual', None) == ProvedorModelo.OPENROUTER else getattr(getattr(agente, 'llm_coder', None), 'model', None)
            }
            
            self._historico_tarefas[nome] = []
            self.logger.info(f"Agente {nome} registrado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar agente {nome}: {e}")
            return False
            
    def registrar_info(self, nome: str, agente_info: Dict[str, Any]) -> bool:
        """Registra as informações básicas de um agente. Não requer o objeto agente completo."""
        try:
            if nome in self._agentes:
                self.logger.warning(f"Informações do agente {nome} já registradas, atualizando...")
                
            # Armazenar as informações fornecidas pelo agente_info
            self._agentes[nome] = {
                'registro': datetime.now(),
                'tarefas': self._agentes.get(nome, {}).get('tarefas', 0), # Manter contadores se já existirem
                'erros': self._agentes.get(nome, {}).get('erros', 0),
                'ultima_tarefa': self._agentes.get(nome, {}).get('ultima_tarefa', None),
                **agente_info, # Adicionar/sobrescrever com as informações do agente_info (nome, especialidades, status, etc.)
                'objeto': self._agentes.get(nome, {}).get('objeto', None), # Manter a referência ao objeto agente se já existir
            }
            
            if nome not in self._historico_tarefas:
                 self._historico_tarefas[nome] = []
                 
            self.logger.info(f"Informações do agente {nome} registradas/atualizadas com sucesso.")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar informações do agente {nome}: {e}")
            return False
            
    def distribuir_tarefa(self, tarefa: str, agente_id: Optional[str] = None) -> Any:
        """Distribui uma tarefa para um agente específico ou escolhe o mais adequado."""
        if not self._agentes:
            raise AgenteError("Nenhum agente registrado")
            
        tarefa_id = str(uuid.uuid4())
        
        try:
            # Iniciar monitoramento
            self.monitor.iniciar_tarefa(tarefa_id, f"Distribuindo tarefa: {tarefa[:100]}...")
            
            # Selecionar agente
            if agente_id:
                if agente_id not in self._agentes:
                    raise AgenteError(f"Agente {agente_id} não encontrado")
                agente = self._agentes[agente_id]
            else:
                agente = self._selecionar_agente(tarefa)
                
            # Executar tarefa
            inicio = datetime.now()
            resultado = agente['objeto'].processar(tarefa)
            duracao = (datetime.now() - inicio).total_seconds()
            
            # Atualizar estatísticas
            agente['tarefas'] += 1
            agente['ultima_tarefa'] = datetime.now()
            
            # Registrar no histórico
            self._historico_tarefas[agente_id or agente['objeto'].id].append({
                'tarefa_id': tarefa_id,
                'tarefa': tarefa,
                'inicio': inicio.isoformat(),
                'duracao': duracao,
                'status': 'concluida'
            })
            
            # Registrar métricas
            self.monitor.registrar_metrica('tempo_resposta', duracao)
            self.monitor.finalizar_tarefa(tarefa_id)
            
            return resultado
            
        except Exception as e:
            self.logger.error(f"Erro ao distribuir tarefa: {e}")
            self.monitor.finalizar_tarefa(tarefa_id, 'erro')
            
            if agente_id:
                self._agentes[agente_id]['erros'] += 1
                self._historico_tarefas[agente_id].append({
                    'tarefa_id': tarefa_id,
                    'tarefa': tarefa,
                    'inicio': datetime.now().isoformat(),
                    'erro': str(e),
                    'status': 'erro'
                })
                
            raise AgenteError(f"Falha ao distribuir tarefa: {e}")
            
    def _selecionar_agente(self, tarefa: str) -> Dict[str, Any]:
        """Seleciona o agente mais adequado para uma tarefa."""
        # Implementar lógica de seleção baseada em especialidades
        # Por enquanto, retorna o primeiro agente ativo
        for agente_id, agente in self._agentes.items():
            if agente['status'] == 'ativo':
                return agente
                
        raise AgenteError("Nenhum agente ativo disponível")
        
    def contar_ativos(self) -> int:
        """Retorna o número de agentes ativos."""
        return sum(1 for a in self._agentes.values() if a['status'] == 'ativo')
        
    def gerar_relatorio(self) -> Dict[str, Any]:
        """Gera relatório de uso dos agentes."""
        return {
            'total': len(self._agentes),
            'ativos': self.contar_ativos(),
            'agentes': {
                nome: {
                    'tarefas': info['tarefas'],
                    'erros': info['erros'],
                    'especialidades': info['especialidades'],
                    'status': info['status'],
                    'ultima_tarefa': info['ultima_tarefa'].isoformat() if info['ultima_tarefa'] else None
                }
                for nome, info in self._agentes.items()
            }
        }
        
    def salvar_historico(self, arquivo: str) -> bool:
        """Salva o histórico de tarefas em um arquivo."""
        try:
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(self._historico_tarefas, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar histórico: {e}")
            return False 