"""
Módulo de monitoramento de progresso para tarefas assíncronas.

Este módulo fornece funcionalidades para monitorar e gerenciar tarefas assíncronas
com suporte a tempo limite, cancelamento e tratamento de erros.
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
from ..exceptions import AgenteError, LoggingError

# Configuração de logging
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Exceção lançada quando uma tarefa atinge o tempo limite."""
    pass

class TarefaCanceladaError(Exception):
    """Exceção lançada quando uma tarefa é cancelada."""
    pass

@dataclass
class Tarefa:
    """Classe que representa uma tarefa em andamento.
    
    Atributos:
        id: Identificador único da tarefa
        descricao: Descrição da tarefa
        total_passos: Número total de passos para conclusão
        passos_concluidos: Número de passos concluídos
        status: Status atual da tarefa (pendente, em_andamento, concluida, falha, cancelada)
        inicio: Timestamp de início da tarefa
        fim: Timestamp de conclusão da tarefa
        mensagem: Mensagem de status atual
        resultado: Resultado da tarefa (se concluída com sucesso)
        erros: Lista de erros ocorridos
        timeout_seconds: Tempo máximo de execução em segundos (None para sem limite)
        cancelar_event: Evento para sinalizar cancelamento
    """
    id: str
    descricao: str
    total_passos: int
    passos_concluidos: int = 0
    status: str = "pendente"  # pendente, em_andamento, concluida, falha, cancelada
    inicio: Optional[float] = None
    fim: Optional[float] = None
    mensagem: str = ""
    resultado: Any = None
    erros: List[str] = field(default_factory=list)
    timeout_seconds: Optional[float] = None
    cancelar_event: threading.Event = field(default_factory=threading.Event)
    
    def verificar_cancelamento(self) -> None:
        """Verifica se a tarefa foi cancelada."""
        if self.cancelar_event.is_set():
            self.status = "cancelada"
            self.fim = time.time()
            raise TarefaCanceladaError("Tarefa cancelada pelo usuário")
    
    def verificar_timeout(self) -> None:
        """Verifica se a tarefa atingiu o tempo limite."""
        if self.timeout_seconds and self.inicio:
            tempo_decorrido = time.time() - self.inicio
            if tempo_decorrido > self.timeout_seconds:
                self.status = "falha"
                self.fim = time.time()
                self.erros.append(f"Tempo limite de {self.timeout_seconds} segundos excedido")
                raise TimeoutError(f"Tarefa excedeu o tempo limite de {self.timeout_seconds} segundos")

class MonitorProgresso:
    """Classe para monitorar o progresso de tarefas assíncronas.
    
    Implementa o padrão Singleton para garantir apenas uma instância global.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MonitorProgresso, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.tarefas: Dict[str, Tarefa] = {}
            self.lock = threading.RLock()  # Usando RLock para suportar chamadas aninhadas
            self._initialized = True
            logger.info("Monitor de progresso inicializado")
    
    def criar_tarefa(
        self, 
        descricao: str, 
        total_passos: int, 
        timeout_seconds: Optional[float] = None
    ) -> str:
        """Cria uma nova tarefa de monitoramento.
        
        Args:
            descricao: Descrição clara da tarefa
            total_passos: Número total de passos para conclusão
            timeout_seconds: Tempo máximo de execução em segundos (opcional)
            
        Returns:
            str: ID único da tarefa criada
        """
        task_id = str(uuid.uuid4())
        with self.lock:
            self.tarefas[task_id] = Tarefa(
                id=task_id,
                descricao=descricao,
                total_passos=max(1, total_passos),  # Garante pelo menos 1 passo
                inicio=time.time(),
                status="em_andamento",
                timeout_seconds=timeout_seconds
            )
            logger.info(f"Tarefa criada: {task_id} - {descricao} (timeout: {timeout_seconds}s)")
        return task_id
    
    def atualizar_progresso(
        self, 
        task_id: str, 
        passos: int = 1, 
        mensagem: str = ""
    ) -> bool:
        """Atualiza o progresso de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            passos: Número de passos concluídos desde a última atualização
            mensagem: Mensagem de status opcional
            
        Returns:
            bool: True se a atualização foi bem-sucedida, False caso contrário
        """
        with self.lock:
            if task_id not in self.tarefas:
                logger.warning(f"Tentativa de atualizar tarefa inexistente: {task_id}")
                return False
            
            tarefa = self.tarefas[task_id]
            
            # Verifica se a tarefa já foi finalizada
            if tarefa.status in ["concluida", "falha", "cancelada"]:
                logger.warning(f"Tentativa de atualizar tarefa {task_id} com status {tarefa.status}")
                return False
                
            try:
                # Verifica cancelamento e timeout
                tarefa.verificar_cancelamento()
                tarefa.verificar_timeout()
                
                # Atualiza o progresso
                tarefa.passos_concluidos = min(
                    tarefa.passos_concluidos + max(0, passos),  # Passos não podem ser negativos
                    tarefa.total_passos
                )
                
                if mensagem:
                    tarefa.mensagem = mensagem
                    logger.debug(f"Tarefa {task_id} - {mensagem}")
                
                # Verifica se a tarefa foi concluída
                if tarefa.passos_concluidos >= tarefa.total_passos:
                    tarefa.status = "concluida"
                    tarefa.fim = time.time()
                    logger.info(f"Tarefa concluída: {task_id}")
                
                return True
                
            except (TarefaCanceladaError, TimeoutError) as e:
                logger.warning(f"Tarefa {task_id} interrompida: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Erro ao atualizar tarefa {task_id}: {str(e)}", exc_info=True)
                self.registrar_erro(task_id, f"Erro interno: {str(e)}")
                return False
    
    def registrar_erro(self, task_id: str, erro: Union[str, Exception]) -> None:
        """Registra um erro na tarefa.
        
        Args:
            task_id: ID da tarefa
            erro: Mensagem de erro ou exceção
        """
        with self.lock:
            if task_id in self.tarefas:
                tarefa = self.tarefas[task_id]
                if task_id not in ["falha", "cancelada"]:  # Não sobrescreve status final
                    tarefa.status = "falha"
                    tarefa.fim = time.time()
                
                mensagem_erro = str(erro) if not isinstance(erro, Exception) else f"{type(erro).__name__}: {str(erro)}"
                tarefa.erros.append(mensagem_erro)
                logger.error(f"Erro na tarefa {task_id}: {mensagem_erro}", 
                            exc_info=isinstance(erro, Exception))
    
    def obter_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtém o status atual de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Optional[Dict]: Dicionário com informações da tarefa ou None se não encontrada
        """
        with self.lock:
            if task_id not in self.tarefas:
                logger.warning(f"Tentativa de obter status de tarefa inexistente: {task_id}")
                return None
            
            tarefa = self.tarefas[task_id]
            agora = time.time()
            
            # Calcula o tempo decorrido
            inicio = tarefa.inicio or agora
            fim = tarefa.fim or agora
            tempo_decorrido = fim - inicio
            
            # Estima o tempo restante (se aplicável)
            tempo_restante = None
            if tarefa.status == "em_andamento" and tarefa.passos_concluidos > 0:
                velocidade = tempo_decorrido / tarefa.passos_concluidos
                passos_restantes = tarefa.total_passos - tarefa.passos_concluidos
                tempo_restante = velocidade * passos_restantes
            
            # Verifica timeout iminente
            timeout_iminente = False
            if tarefa.timeout_seconds and tarefa.status == "em_andamento":
                tempo_decorrido_total = agora - inicio
                if tempo_decorrido_total > tarefa.timeout_seconds * 0.8:  # 80% do tempo
                    timeout_iminente = True
            
            return {
                "id": tarefa.id,
                "descricao": tarefa.descricao,
                "status": tarefa.status,
                "progresso": f"{tarefa.passos_concluidos}/{tarefa.total_passos}",
                "porcentagem": (tarefa.passos_concluidos / max(1, tarefa.total_passos)) * 100,
                "mensagem": tarefa.mensagem,
                "inicio": datetime.fromtimestamp(tarefa.inicio).isoformat() if tarefa.inicio else None,
                "fim": datetime.fromtimestamp(tarefa.fim).isoformat() if tarefa.fim else None,
                "tempo_decorrido": tempo_decorrido,
                "tempo_decorrido_formatado": str(timedelta(seconds=int(tempo_decorrido))),
                "tempo_restante": tempo_restante,
                "tempo_restante_formatado": str(timedelta(seconds=int(tempo_restante))) if tempo_restante else None,
                "timeout_seconds": tarefa.timeout_seconds,
                "timeout_iminente": timeout_iminente,
                "erros": tarefa.erros,
                "resultado": tarefa.resultado if tarefa.status == "concluida" else None,
                "timestamp": agora
            }
    
    def finalizar_tarefa(self, task_id: str, resultado: Any = None) -> bool:
        """Finaliza uma tarefa com sucesso.
        
        Args:
            task_id: ID da tarefa
            resultado: Resultado da tarefa (opcional)
            
        Returns:
            bool: True se a tarefa foi finalizada com sucesso, False caso contrário
        """
        with self.lock:
            if task_id not in self.tarefas:
                logger.warning(f"Tentativa de finalizar tarefa inexistente: {task_id}")
                return False
                
            tarefa = self.tarefas[task_id]
            
            # Não permite finalizar uma tarefa já finalizada, falha ou cancelada
            if tarefa.status in ["concluida", "falha", "cancelada"]:
                logger.warning(f"Tentativa de finalizar tarefa {task_id} com status {tarefa.status}")
                return False
                
            tarefa.status = "concluida"
            tarefa.resultado = resultado
            tarefa.fim = time.time()
            tarefa.passos_concluidos = tarefa.total_passos
            logger.info(f"Tarefa {task_id} finalizada com sucesso")
            return True
            
    def cancelar_tarefa(self, task_id: str, motivo: str = "Solicitado pelo usuário") -> bool:
        """Cancela uma tarefa em andamento.
        
        Args:
            task_id: ID da tarefa
            motivo: Motivo do cancelamento
            
        Returns:
            bool: True se a tarefa foi cancelada com sucesso, False caso contrário
        """
        with self.lock:
            if task_id not in self.tarefas:
                logger.warning(f"Tentativa de cancelar tarefa inexistente: {task_id}")
                return False
                
            tarefa = self.tarefas[task_id]
            
            # Só permite cancelar tarefas que ainda estão ativas
            if tarefa.status not in ["pendente", "em_andamento"]:
                logger.warning(f"Tentativa de cancelar tarefa {task_id} com status {tarefa.status}")
                return False
            
            # Marca a tarefa para cancelamento
            tarefa.cancelar_event.set()
            tarefa.status = "cancelada"
            tarefa.fim = time.time()
            tarefa.mensagem = f"Cancelada: {motivo}"
            tarefa.erros.append(f"Cancelada: {motivo}")
            logger.info(f"Tarefa {task_id} cancelada: {motivo}")
            return True
            
    def limpar_tarefas_antigas(self, horas: int = 24) -> int:
        """Remove tarefas concluídas ou falhas mais antigas que o tempo especificado.
        
        Args:
            horas: Número de horas para manter as tarefas no histórico
            
        Returns:
            int: Número de tarefas removidas
        """
        limite = time.time() - (horas * 3600)
        removidas = 0
        
        with self.lock:
            tarefas_para_remover = [
                task_id for task_id, tarefa in self.tarefas.items()
                if tarefa.fim and tarefa.fim < limite and 
                tarefa.status in ["concluida", "falha", "cancelada"]
            ]
            
            for task_id in tarefas_para_remover:
                del self.tarefas[task_id]
                removidas += 1
                
            if removidas > 0:
                logger.info(f"Removidas {removidas} tarefas antigas do histórico")
                
        return removidas

# Instância global do monitor
monitor = MonitorProgresso()

def monitorar_tarefa(descricao: str, total_passos: int) -> Callable:
    """
    Decorador para monitorar o progresso de uma função.
    
    Exemplo de uso:
    
    @monitorar_tarefa("Processamento de dados", 100)
    def processar_dados(progress_callback):
        for i in range(100):
            # Fazer algo
            progress_callback(1, f"Processando item {i+1}/100")
    """
    def decorador(func):
        def wrapper(*args, **kwargs):
            task_id = monitor.criar_tarefa(descricao, total_passos)
            
            def progress_callback(passos=1, mensagem=""):
                return monitor.atualizar_progresso(task_id, passos, mensagem)
            
            try:
                # Adiciona o callback de progresso aos argumentos
                if 'progress_callback' in kwargs:
                    # Se já existir um callback, criamos um wrapper
                    original_cb = kwargs['progress_callback']
                    def wrapped_cb(passos=1, mensagem=""):
                        original_cb(passos, mensagem)
                        return progress_callback(passos, mensagem)
                    kwargs['progress_callback'] = wrapped_cb
                else:
                    kwargs['progress_callback'] = progress_callback
                
                # Executa a função
                resultado = func(*args, **kwargs)
                
                # Finaliza a tarefa
                monitor.finalizar_tarefa(task_id, resultado)
                return resultado
                
            except Exception as e:
                monitor.registrar_erro(task_id, str(e))
                raise
            
        return wrapper
    return decorador

def obter_status_tarefa(task_id: str) -> Optional[Dict]:
    return monitor.obter_status(task_id)

def listar_tarefas_ativas() -> List[Dict]:
    with monitor.lock:
        return [
            monitor.obter_status(task_id)
            for task_id in monitor.tarefas
            if monitor.tarefas[task_id].status in ["pendente", "em_andamento"]
        ]



# Exemplo de uso:
if __name__ == "__main__":
    # Criar uma tarefa
    task_id = monitor.criar_tarefa("Processamento de dados", 100)
    
    # Simular progresso
    import random
    for i in range(10):
        monitor.atualizar_progresso(task_id, 10, f"Processando lote {i+1}/10")
        time.sleep(0.5)
    
    # Finalizar a tarefa
    monitor.finalizar_tarefa(task_id, {"dados_processados": 1000})
    
    # Verificar status
    print(monitor.obter_status(task_id))
