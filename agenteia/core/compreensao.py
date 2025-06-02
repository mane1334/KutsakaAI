import re
from typing import Dict, Any

INTENCOES = {
    "consulta": {
        "palavras_chave": ["como", "o que", "qual", "quando", "onde", "por que", "quem", "explique", "diga", "fale", "conte", "pesquise", "busque", "procure", "encontre"],
        "contextos": ["pergunta", "dúvida", "curiosidade", "informação", "pesquisa", "busca"],
        "ferramentas": ["pesquisar_web"],
        "exemplos": [
            "Como funciona o Python?",
            "O que é inteligência artificial?",
            "Qual a diferença entre Python e JavaScript?",
            "Quando foi criado o Python?",
            "Onde posso aprender programação?",
            "Por que usar Python?",
            "Quem criou o Python?",
            "Explique o que é machine learning",
            "Diga-me sobre blockchain",
            "Fale sobre as últimas novidades em IA",
            "Conte sobre a história da computação",
            "Pesquise sobre frameworks Python",
            "Busque informações sobre Docker",
            "Procure tutoriais de programação",
            "Encontre exemplos de código Python"
        ]
    },
    "listar": {
        "palavras_chave": ["liste", "mostre", "veja", "exiba", "apresente", "enumere", "conte", "quantos", "quais"],
        "contextos": ["arquivos", "diretórios", "conteúdo", "lista", "enumeração"],
        "ferramentas": ["listar_arquivos"],
        "exemplos": [
            "Liste os arquivos do desktop",
            "Mostre o conteúdo da pasta Downloads",
            "Veja os arquivos da área de trabalho",
            "Exiba os arquivos do diretório atual",
            "Apresente os arquivos da pasta Documentos",
            "Enumere os arquivos da pasta Projetos",
            "Conte quantos arquivos tem na pasta",
            "Quais arquivos existem no diretório?",
            "Liste os arquivos .txt do desktop",
            "Mostre as pastas do diretório atual"
        ]
    },
    "criar": {
        "palavras_chave": ["crie", "faça", "gere", "produza", "elabore", "desenvolva", "construa", "monte", "prepare"],
        "contextos": ["arquivo", "documento", "código", "estrutura", "projeto"],
        "ferramentas": ["criar_arquivo_codigo", "criar_estrutura_pastas", "criar_word", "criar_excel", "criar_ppt"],
        "exemplos": [
            "Crie um arquivo Python para calcular médias",
            "Faça um documento Word com o resumo do projeto",
            "Gere uma planilha Excel com os dados de vendas",
            "Produza uma apresentação PowerPoint sobre IA",
            "Elabore um script para automatizar tarefas",
            "Desenvolva uma estrutura de pastas para o projeto",
            "Construa um arquivo de configuração",
            "Monte um template de relatório",
            "Prepare um documento com as instruções",
            "Crie um arquivo README para o projeto"
        ]
    },
    "editar": {
        "palavras_chave": ["edite", "modifique", "altere", "atualize", "mude", "ajuste", "corrija", "revise"],
        "contextos": ["arquivo", "código", "documento", "texto", "conteúdo"],
        "ferramentas": ["ler_arquivo", "escrever_arquivo"],
        "exemplos": [
            "Edite o arquivo config.py",
            "Modifique o código do script",
            "Altere o conteúdo do documento",
            "Atualize o arquivo README",
            "Mude o texto do relatório",
            "Ajuste as configurações do projeto",
            "Corrija os erros no código",
            "Revise o documento Word",
            "Edite a planilha Excel",
            "Modifique a apresentação PowerPoint"
        ]
    },
    "executar": {
        "palavras_chave": ["execute", "rode", "inicie", "lance", "dispare", "processe", "calcule", "resolva"],
        "contextos": ["comando", "script", "programa", "cálculo", "processo"],
        "ferramentas": ["executar_comando", "calcular"],
        "exemplos": [
            "Execute o script Python",
            "Rode o comando dir",
            "Inicie o servidor local",
            "Lance o programa de teste",
            "Dispare o processo de backup",
            "Processe os dados do arquivo",
            "Calcule a média dos números",
            "Resolva a equação matemática",
            "Execute o comando pip install",
            "Rode o teste unitário"
        ]
    },
    "ajuda": {
        "palavras_chave": ["ajuda", "socorro", "auxílio", "suporte", "como usar", "tutorial", "guia", "manual"],
        "contextos": ["dúvida", "problema", "orientação", "instrução", "assistência"],
        "ferramentas": ["pesquisar_web"],
        "exemplos": [
            "Como usar o agente?",
            "Preciso de ajuda com Python",
            "Socorro com erro no código",
            "Auxílio para configurar o projeto",
            "Suporte para instalar dependências",
            "Como usar as ferramentas?",
            "Tutorial de programação Python",
            "Guia de instalação do projeto",
            "Manual de uso do agente",
            "Ajuda com comandos disponíveis"
        ]
    }
}

class CompreensaoMensagem:
    """Classe para analisar e compreender mensagens do usuário."""
    
    def __init__(self):
        """Inicializa o analisador de mensagens."""
        self.intencoes = INTENCOES
        self.diretorios_comuns = {
            "desktop": ["desktop", "área de trabalho", "área de trabalho do windows", "desktop do windows"],
            "documentos": ["documentos", "meus documentos", "pasta documentos"],
            "downloads": ["downloads", "pasta downloads", "arquivos baixados"],
            "projetos": ["projetos", "pasta projetos", "meus projetos"],
            "atual": [".", "diretório atual", "pasta atual", "local atual"]
        }
        
    def _normalizar_texto(self, texto: str) -> str:
        """
        Normaliza o texto para análise.
        
        Args:
            texto: Texto a ser normalizado
            
        Returns:
            Texto normalizado
        """
        # Converte para minúsculas
        texto = texto.lower()
        
        # Remove pontuação
        texto = re.sub(r'[^\w\s]', ' ', texto)
        
        # Remove espaços extras
        texto = ' '.join(texto.split())
        
        return texto
        
    def _extrair_parametros(self, texto: str, intencao: str) -> Dict[str, Any]:
        """
        Extrai parâmetros relevantes da mensagem.
        
        Args:
            texto: Texto da mensagem
            intencao: Intenção detectada
            
        Returns:
            Dicionário com parâmetros extraídos
        """
        params = {}
        texto_norm = self._normalizar_texto(texto)
        
        # Extrai diretório para comandos de listar
        if intencao == "listar":
            # Padrão para extrair diretório
            padrao_dir = r'(?:em|do|da|de|no|na|em|para|em diretório|na pasta|do diretório|da pasta)\s+([^\s]+(?:\s+[^\s]+)*)'
            match = re.search(padrao_dir, texto_norm)
            
            if match:
                dir_especificado = match.group(1).strip()
                # Verifica se é um diretório comum
                for dir_base, alternativas in self.diretorios_comuns.items():
                    if dir_especificado in alternativas:
                        params["diretorio"] = dir_base
                        break
                else:
                    params["diretorio"] = dir_especificado
            else:
                params["diretorio"] = "."
                
            # Extrai extensão se especificada
            padrao_ext = r'\.(\w+)(?:\s|$)'
            match_ext = re.search(padrao_ext, texto_norm)
            if match_ext:
                params["extensao"] = match_ext.group(1)
                
        # Extrai query para pesquisas
        elif intencao == "consulta":
            # Remove palavras de consulta comuns
            palavras_consulta = ["pesquise", "busque", "procure", "encontre", "como", "o que", "qual", "quando", "onde", "por que", "quem"]
            query = texto_norm
            for palavra in palavras_consulta:
                query = query.replace(palavra, "").strip()
            params["query"] = query
            
        # Extrai caminho do arquivo para edição
        elif intencao == "editar":
            padrao_arquivo = r'(?:arquivo|arquivo|código|documento|texto|conteúdo)\s+([^\s]+(?:\s+[^\s]+)*)'
            match = re.search(padrao_arquivo, texto_norm)
            if match:
                params["caminho"] = match.group(1).strip()
                
        # Extrai comando para execução
        elif intencao == "executar":
            padrao_comando = r'(?:comando|script|programa|processo)\s+([^\s]+(?:\s+[^\s]+)*)'
            match = re.search(padrao_comando, texto_norm)
            if match:
                params["comando"] = match.group(1).strip()
                
        return params
        
    def _calcular_confianca(self, texto: str, intencao: str) -> float:
        """
        Calcula o nível de confiança da intenção detectada.
        
        Args:
            texto: Texto da mensagem
            intencao: Intenção detectada
            
        Returns:
            Nível de confiança (0-1)
        """
        texto_norm = self._normalizar_texto(texto)
        palavras = set(texto_norm.split())
        
        # Pontuação base
        confianca = 0.0
        
        # Verifica palavras-chave
        palavras_chave = set(self.intencoes[intencao]["palavras_chave"])
        matches = palavras.intersection(palavras_chave)
        if matches:
            confianca += 0.4 * (len(matches) / len(palavras_chave))
            
        # Verifica contexto
        contextos = set(self.intencoes[intencao]["contextos"])
        for contexto in contextos:
            if contexto in texto_norm:
                confianca += 0.3
                break
                
        # Verifica similaridade com exemplos
        exemplos = self.intencoes[intencao]["exemplos"]
        for exemplo in exemplos:
            exemplo_norm = self._normalizar_texto(exemplo)
            # Calcula similaridade simples
            palavras_exemplo = set(exemplo_norm.split())
            similaridade = len(palavras.intersection(palavras_exemplo)) / len(palavras.union(palavras_exemplo))
            confianca += 0.3 * similaridade
            
        return min(confianca, 1.0)
        
    def analisar(self, texto: str) -> Dict[str, Any]:
        """
        Analisa uma mensagem e retorna a intenção detectada.
        
        Args:
            texto: Texto da mensagem
            
        Returns:
            Dicionário com intenção e parâmetros
        """
        if not texto:
            return {"intencao": None, "confianca": 0.0, "params": {}}
            
        # Analisa cada intenção
        melhor_intencao = None
        melhor_confianca = 0.0
        
        for intencao in self.intencoes:
            confianca = self._calcular_confianca(texto, intencao)
            if confianca > melhor_confianca:
                melhor_intencao = intencao
                melhor_confianca = confianca
                
        # Extrai parâmetros se houver intenção detectada
        params = {}
        if melhor_intencao and melhor_confianca >= 0.3:  # Limiar mínimo de confiança
            params = self._extrair_parametros(texto, melhor_intencao)
            
        return {
            "intencao": melhor_intencao,
            "confianca": melhor_confianca,
            "params": params
        } 