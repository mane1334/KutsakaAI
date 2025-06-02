"""
Sistema de Gatilhos para o Agente IA
Gerencia diferentes tipos de respostas baseadas em padrões e contextos
"""

from typing import Dict, List, Callable, Optional, Tuple
import re
from dataclasses import dataclass
from enum import Enum

class TipoGatilho(Enum):
    """Tipos de gatilhos disponíveis"""
    CUMPRIMENTO = "cumprimento"
    PERGUNTA_SIMPLES = "pergunta_simples"
    COMANDO = "comando"
    FERRAMENTA = "ferramenta"
    CONVERSA = "conversa"
    DESENVOLVIMENTO = "desenvolvimento"
    DOCUMENTO = "documento"
    PESQUISA = "pesquisa"
    CODIGO = "codigo"
    SISTEMA_ARQUIVOS = "sistema_arquivos"  # Novo tipo para comandos de sistema de arquivos

@dataclass
class Gatilho:
    """Estrutura para definir um gatilho de resposta"""
    tipo: TipoGatilho
    padrao: str
    prioridade: int = 0
    descricao: str = ""
    exemplo_resposta: str = ""

class GerenciadorGatilhos:
    """Gerencia os gatilhos de resposta do agente"""
    
    def __init__(self):
        self.gatilhos: Dict[TipoGatilho, List[Gatilho]] = {
            tipo: [] for tipo in TipoGatilho
        }
        self._inicializar_gatilhos_padrao()
    
    def _inicializar_gatilhos_padrao(self):
        """Inicializa os gatilhos padrão do sistema"""
        
        # Gatilhos de cumprimento
        self.adicionar_gatilho(
            Gatilho(
                tipo=TipoGatilho.CUMPRIMENTO,
                padrao=r"^(oi|olá|bom dia|boa tarde|boa noite|hey|hi|hello)$",
                prioridade=100,
                descricao="Cumprimentos simples",
                exemplo_resposta="Olá! Como posso ajudar você hoje?"
            )
        )
        
        # Gatilhos de pergunta simples
        self.adicionar_gatilho(
            Gatilho(
                tipo=TipoGatilho.PERGUNTA_SIMPLES,
                padrao=r"^(como você está|tudo bem|como vai)$",
                prioridade=90,
                descricao="Perguntas sobre o estado do agente",
                exemplo_resposta="Estou muito bem, obrigado por perguntar! Como posso ajudar você?"
            )
        )
        
        # Gatilhos de comando
        self.adicionar_gatilho(
            Gatilho(
                tipo=TipoGatilho.COMANDO,
                padrao=r"^(limpar|resetar|reiniciar|começar de novo)$",
                prioridade=80,
                descricao="Comandos para limpar o histórico",
                exemplo_resposta="Histórico limpo com sucesso! Podemos começar uma nova conversa."
            )
        )
        
        # Gatilhos de ferramenta
        self.adicionar_gatilho(
            Gatilho(
                tipo=TipoGatilho.FERRAMENTA,
                padrao=r"(criar|editar|ler|deletar|mover|copiar)\s+(arquivo|pasta|documento)",
                prioridade=70,
                descricao="Comandos para manipulação de arquivos",
                exemplo_resposta="Vou ajudar você a manipular os arquivos. Qual arquivo você gostaria de trabalhar?"
            )
        )
        
        # Gatilhos de conversa
        self.adicionar_gatilho(
            Gatilho(
                tipo=TipoGatilho.CONVERSA,
                padrao=r".*",  # Padrão genérico para conversas
                prioridade=10,
                descricao="Conversas gerais",
                exemplo_resposta="Entendi! Vamos conversar sobre isso."
            )
        )
        
        # Gatilhos de desenvolvimento
        self.adicionar_gatilho(
            Gatilho(
                tipo=TipoGatilho.DESENVOLVIMENTO,
                padrao=r"(criar|desenvolver|fazer)\s+(app|aplicativo|site|website|web app|página web)",
                prioridade=85,
                descricao="Comandos para desenvolvimento de aplicações",
                exemplo_resposta="Vou ajudar você a criar essa aplicação. Primeiro, vamos definir a estrutura do projeto."
            )
        )
        
        # Gatilhos de documento
        self.adicionar_gatilho(
            Gatilho(
                tipo=TipoGatilho.DOCUMENTO,
                padrao=r"(criar|escrever|editar|resumir)\s+(documento|relatório|texto|word|doc)",
                prioridade=80,
                descricao="Comandos para manipulação de documentos",
                exemplo_resposta="Vou ajudar você com o documento. Podemos criar, editar ou resumir conforme necessário."
            )
        )
        
        # Gatilhos de pesquisa
        self.adicionar_gatilho(
            Gatilho(
                tipo=TipoGatilho.PESQUISA,
                padrao=r"(pesquisar|buscar|procurar|encontrar)\s+(informação|dados|sobre)",
                prioridade=75,
                descricao="Comandos para pesquisa na web",
                exemplo_resposta="Vou pesquisar essa informação na web para você."
            )
        )
        
        # Gatilhos de código
        self.adicionar_gatilho(
            Gatilho(
                tipo=TipoGatilho.CODIGO,
                padrao=r"(analisar|revisar|corrigir|otimizar|explicar)\s+(código|programa|script|função|classe)",
                prioridade=70,
                descricao="Comandos para análise e manipulação de código",
                exemplo_resposta="Vou analisar seu código e ajudar com as melhorias necessárias."
            )
        )
        
        # Gatilhos de sistema de arquivos
        self.adicionar_gatilho(
            Gatilho(
                tipo=TipoGatilho.SISTEMA_ARQUIVOS,
                padrao=r"^(liste|listar|mostre|mostrar)\s+(?:os\s+)?(?:arquivos|arquivo|diretorio|pasta|conteudo)\s+(?:do|da|em|no|na)?\s*([^\s].*?)(?:\s*$|\s+com\s+|\s+para\s+)",
                prioridade=95,
                descricao="Comandos para listar conteúdo de diretórios",
                exemplo_resposta="Vou listar o conteúdo do diretório solicitado."
            )
        )
        
        self.adicionar_gatilho(
            Gatilho(
                tipo=TipoGatilho.SISTEMA_ARQUIVOS,
                padrao=r"^(crie|criar|nova|novo)\s+(?:um\s+)?(?:arquivo|pasta|diretorio)\s+(?:chamado|nomeado|com\s+nome)?\s*([^\s].*?)(?:\s*$|\s+com\s+|\s+para\s+)",
                prioridade=95,
                descricao="Comandos para criar arquivos e diretórios",
                exemplo_resposta="Vou criar o arquivo/diretório solicitado."
            )
        )
        
        self.adicionar_gatilho(
            Gatilho(
                tipo=TipoGatilho.SISTEMA_ARQUIVOS,
                padrao=r"^(delete|deletar|remova|remover|apague|apagar)\s+(?:o\s+)?(?:arquivo|pasta|diretorio)\s+(?:chamado|nomeado|com\s+nome)?\s*([^\s].*?)(?:\s*$|\s+com\s+|\s+para\s+)",
                prioridade=95,
                descricao="Comandos para remover arquivos e diretórios",
                exemplo_resposta="Vou remover o arquivo/diretório solicitado."
            )
        )
        
        self.adicionar_gatilho(
            Gatilho(
                tipo=TipoGatilho.SISTEMA_ARQUIVOS,
                padrao=r"^(copie|copiar|mova|mover)\s+(?:o\s+)?(?:arquivo|pasta|diretorio)\s+([^\s].*?)\s+(?:para|to)\s+([^\s].*?)(?:\s*$|\s+com\s+|\s+para\s+)",
                prioridade=95,
                descricao="Comandos para copiar e mover arquivos",
                exemplo_resposta="Vou copiar/mover o arquivo para o destino solicitado."
            )
        )
    
    def adicionar_gatilho(self, gatilho: Gatilho):
        """Adiciona um novo gatilho ao sistema"""
        self.gatilhos[gatilho.tipo].append(gatilho)
        # Ordena por prioridade (maior prioridade primeiro)
        self.gatilhos[gatilho.tipo].sort(key=lambda x: x.prioridade, reverse=True)
    
    def identificar_gatilho(self, mensagem: str) -> Tuple[Optional[Gatilho], TipoGatilho]:
        """
        Identifica qual gatilho corresponde à mensagem
        
        Returns:
            Tuple[Optional[Gatilho], TipoGatilho]: O gatilho encontrado e seu tipo
        """
        mensagem = mensagem.lower().strip()
        
        # Verifica cada tipo de gatilho em ordem de prioridade
        for tipo in [
            TipoGatilho.SISTEMA_ARQUIVOS,  # Movido para o topo da lista
            TipoGatilho.CUMPRIMENTO,
            TipoGatilho.PERGUNTA_SIMPLES,
            TipoGatilho.COMANDO,
            TipoGatilho.DESENVOLVIMENTO,
            TipoGatilho.DOCUMENTO,
            TipoGatilho.PESQUISA,
            TipoGatilho.CODIGO,
            TipoGatilho.FERRAMENTA,
            TipoGatilho.CONVERSA
        ]:
            for gatilho in sorted(self.gatilhos[tipo], key=lambda x: x.prioridade, reverse=True):
                if re.match(gatilho.padrao, mensagem, re.IGNORECASE):
                    return gatilho, tipo
        
        # Se nenhum gatilho específico for encontrado, retorna o gatilho de conversa
        return self.gatilhos[TipoGatilho.CONVERSA][0], TipoGatilho.CONVERSA
    
    def obter_resposta_padrao(self, gatilho: Gatilho) -> str:
        """Retorna a resposta padrão para um gatilho"""
        return gatilho.exemplo_resposta
    
    def listar_gatilhos(self) -> Dict[TipoGatilho, List[Dict]]:
        """Lista todos os gatilhos registrados"""
        return {
            tipo: [
                {
                    "padrao": g.padrao,
                    "prioridade": g.prioridade,
                    "descricao": g.descricao,
                    "exemplo": g.exemplo_resposta
                }
                for g in gatilhos
            ]
            for tipo, gatilhos in self.gatilhos.items()
        }

# Instância global do gerenciador de gatilhos
gerenciador_gatilhos = GerenciadorGatilhos() 