import ast
import time
import cProfile
import pstats
import io
from typing import Dict, List, Optional, Union
import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

def otimizar_codigo(codigo: str) -> Dict:
    """Sugere otimizações para o código."""
    try:
        sugestoes = []
        
        # Analisar o código
        tree = ast.parse(codigo)
        
        # Verificar loops
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Verificar loops aninhados
                if any(isinstance(child, ast.For) for child in ast.walk(node)):
                    sugestoes.append({
                        "tipo": "Loop Aninhado",
                        "severidade": "Média",
                        "descricao": "Loop aninhado detectado. Considere usar list comprehension ou funções map/filter.",
                        "linha": node.lineno
                    })
            
            # Verificar uso de listas
            elif isinstance(node, ast.List):
                if isinstance(node.ctx, ast.Store):
                    sugestoes.append({
                        "tipo": "Lista Mutável",
                        "severidade": "Baixa",
                        "descricao": "Considere usar tuple se a lista não precisar ser modificada.",
                        "linha": node.lineno
                    })
            
            # Verificar strings
            elif isinstance(node, ast.Str):
                if len(node.s) > 100:
                    sugestoes.append({
                        "tipo": "String Longa",
                        "severidade": "Baixa",
                        "descricao": "String muito longa. Considere usar constantes ou arquivos de configuração.",
                        "linha": node.lineno
                    })
        
        # Verificar imports
        imports = [node for node in ast.walk(tree) if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom)]
        if len(imports) > 10:
            sugestoes.append({
                "tipo": "Muitos Imports",
                "severidade": "Média",
                "descricao": "Muitos imports detectados. Considere organizar em módulos.",
                "linha": imports[0].linho
            })
        
        return {
            "total_sugestoes": len(sugestoes),
            "sugestoes": sugestoes,
            "recomendacoes": [
                "Use list comprehension ao invés de loops quando possível",
                "Evite loops aninhados",
                "Use generators para grandes conjuntos de dados",
                "Prefira funções built-in do Python",
                "Use sets para operações de conjunto",
                "Evite criar listas desnecessárias"
            ]
        }
    except Exception as e:
        logger.error(f"Erro ao otimizar código: {e}")
        raise

def analisar_performance(codigo: str, entrada: str = None) -> Dict:
    """Analisa o desempenho do código."""
    try:
        resultado = {
            "tempo_execucao": 0,
            "memoria_uso": 0,
            "complexidade": "O(1)",
            "bottlenecks": [],
            "metricas": {}
        }
        
        # Medir tempo de execução
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Executar código
        if entrada:
            exec(codigo, {"entrada": entrada})
        else:
            exec(codigo)
        
        profiler.disable()
        
        # Analisar resultados
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats()
        
        # Extrair métricas
        output = s.getvalue()
        for linha in output.split('\n'):
            if 'function calls' in linha:
                resultado["metricas"]["chamadas"] = int(linha.split()[0])
            elif 'seconds' in linha:
                resultado["tempo_execucao"] = float(linha.split()[0])
        
        # Identificar bottlenecks
        for linha in output.split('\n'):
            if 'seconds' in linha and float(linha.split()[0]) > 0.1:
                resultado["bottlenecks"].append({
                    "funcao": linha.split()[-1],
                    "tempo": float(linha.split()[0])
                })
        
        # Estimar complexidade
        tree = ast.parse(codigo)
        loops = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While)))
        if loops > 1:
            resultado["complexidade"] = f"O(n^{loops})"
        
        return resultado
    except Exception as e:
        logger.error(f"Erro ao analisar performance: {e}")
        raise

def reduzir_complexidade(codigo: str) -> Dict:
    """Sugere maneiras de reduzir a complexidade do código."""
    try:
        sugestoes = []
        
        # Analisar o código
        tree = ast.parse(codigo)
        
        # Contar complexidade ciclomática
        complexidade = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.ExceptHandler)):
                complexidade += 1
        
        # Verificar funções longas
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.body) > 20:
                    sugestoes.append({
                        "tipo": "Função Longa",
                        "severidade": "Média",
                        "descricao": f"Função {node.name} muito longa. Considere dividir em funções menores.",
                        "linha": node.lineno
                    })
        
        # Verificar condicionais aninhadas
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                aninhamento = 0
                current = node
                while isinstance(current, ast.If):
                    aninhamento += 1
                    if len(current.body) > 0 and isinstance(current.body[0], ast.If):
                        current = current.body[0]
                    else:
                        break
                
                if aninhamento > 2:
                    sugestoes.append({
                        "tipo": "Condicionais Aninhadas",
                        "severidade": "Alta",
                        "descricao": f"Condicionais muito aninhadas ({aninhamento} níveis). Considere refatorar.",
                        "linha": node.lineno
                    })
        
        return {
            "complexidade_ciclomatica": complexidade,
            "total_sugestoes": len(sugestoes),
            "sugestoes": sugestoes,
            "recomendacoes": [
                "Mantenha funções pequenas e focadas",
                "Evite condicionais aninhadas",
                "Use early returns",
                "Extraia lógica complexa para funções separadas",
                "Use padrões de design apropriados"
            ]
        }
    except Exception as e:
        logger.error(f"Erro ao reduzir complexidade: {e}")
        raise

def melhorar_legibilidade(codigo: str) -> Dict:
    """Sugere melhorias para a legibilidade do código."""
    try:
        sugestoes = []
        
        # Verificar nomes de variáveis
        tree = ast.parse(codigo)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if len(node.id) < 2:
                    sugestoes.append({
                        "tipo": "Nome de Variável",
                        "severidade": "Baixa",
                        "descricao": f"Nome de variável muito curto: {node.id}",
                        "linha": node.lineno
                    })
                elif not re.match(r'^[a-z_][a-z0-9_]*$', node.id):
                    sugestoes.append({
                        "tipo": "Nome de Variável",
                        "severidade": "Baixa",
                        "descricao": f"Nome de variável não segue convenção: {node.id}",
                        "linha": node.lineno
                    })
        
        # Verificar comentários
        linhas = codigo.split('\n')
        for i, linha in enumerate(linhas):
            if '#' in linha and len(linha.strip()) < 10:
                sugestoes.append({
                    "tipo": "Comentário",
                    "severidade": "Baixa",
                    "descricao": "Comentário muito curto ou vago",
                    "linha": i + 1
                })
        
        # Verificar espaçamento
        for i, linha in enumerate(linhas):
            if linha.strip() and not linha.startswith(' ') and not linha.startswith('\t'):
                if i > 0 and linhas[i-1].strip() and not linhas[i-1].startswith(' '):
                    sugestoes.append({
                        "tipo": "Espaçamento",
                        "severidade": "Baixa",
                        "descricao": "Falta espaço entre blocos de código",
                        "linha": i + 1
                    })
        
        return {
            "total_sugestoes": len(sugestoes),
            "sugestoes": sugestoes,
            "recomendacoes": [
                "Use nomes descritivos para variáveis e funções",
                "Adicione comentários explicativos",
                "Mantenha consistência no estilo de código",
                "Use espaçamento adequado",
                "Siga as convenções PEP 8"
            ]
        }
    except Exception as e:
        logger.error(f"Erro ao melhorar legibilidade: {e}")
        raise

def refatorar_codigo(codigo: str) -> Dict:
    """Sugere refatorações para melhorar a qualidade do código."""
    try:
        sugestoes = []
        
        # Analisar o código
        tree = ast.parse(codigo)
        
        # Verificar duplicação de código
        funcoes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Gerar hash do corpo da função
                corpo = ast.unparse(node.body)
                if corpo in funcoes:
                    sugestoes.append({
                        "tipo": "Código Duplicado",
                        "severidade": "Alta",
                        "descricao": f"Função {node.name} é similar a {funcoes[corpo]}",
                        "linha": node.lineno
                    })
                else:
                    funcoes[corpo] = node.name
        
        # Verificar responsabilidade única
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                responsabilidades = 0
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While)):
                        responsabilidades += 1
                
                if responsabilidades > 3:
                    sugestoes.append({
                        "tipo": "Responsabilidade Única",
                        "severidade": "Média",
                        "descricao": f"Função {node.name} tem muitas responsabilidades",
                        "linha": node.lineno
                    })
        
        # Verificar acoplamento
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module)
        
        if len(imports) > 10:
            sugestoes.append({
                "tipo": "Alto Acoplamento",
                "severidade": "Média",
                "descricao": "Muitas dependências detectadas",
                "linha": 1
            })
        
        return {
            "total_sugestoes": len(sugestoes),
            "sugestoes": sugestoes,
            "recomendacoes": [
                "Extraia código duplicado para funções reutilizáveis",
                "Aplique o princípio da responsabilidade única",
                "Reduza o acoplamento entre módulos",
                "Use padrões de design apropriados",
                "Implemente testes unitários"
            ]
        }
    except Exception as e:
        logger.error(f"Erro ao refatorar código: {e}")
        raise 