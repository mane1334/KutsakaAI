import ast
import re
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime
import os
import json

logger = logging.getLogger(__name__)

def gerar_documentacao(codigo: str, formato: str = "markdown",
    mcp_client: Optional[Any] = None
) -> str:
    """Gera documentação para o código."""
    try:
        # Refatoração para usar MCP Client se disponível
        if mcp_client:
            logger.info("Delegando gerar_documentacao para MCP Server")
            tarefa_execucao = {
                "tipo": "executar_ferramenta",
                "nome_ferramenta": "gerar_documentacao",
                "parametros": {"codigo": codigo, "formato": formato}
            }
            resultado = mcp_client.distribuir_tarefa(
                tarefa=json.dumps(tarefa_execucao),
                agente_id="Agente Local"
            )
            # O resultado esperado é uma string com a documentação gerada
            return resultado.get("resultado", "Erro: Resultado vazio do MCP Server.")

        # Lógica existente (fallback local)
        # Analisar o código
        tree = ast.parse(codigo)
        
        # Extrair informações
        modulos = []
        classes = []
        funcoes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Module):
                modulos.append({
                    "nome": "Módulo Principal",
                    "docstring": ast.get_docstring(node),
                    "imports": [n.names[0].name for n in node.body if isinstance(n, ast.Import)],
                    "from_imports": [f"{n.module}.{n.names[0].name}" for n in node.body if isinstance(n, ast.ImportFrom)]
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    "nome": node.name,
                    "docstring": ast.get_docstring(node),
                    "bases": [base.id for base in node.bases if isinstance(base, ast.Name)],
                    "metodos": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                })
            elif isinstance(node, ast.FunctionDef):
                funcoes.append({
                    "nome": node.name,
                    "docstring": ast.get_docstring(node),
                    "args": [arg.arg for arg in node.args.args],
                    "returns": node.returns.id if isinstance(node.returns, ast.Name) else None
                })
        
        # Gerar documentação no formato especificado
        if formato == "markdown":
            doc = "# Documentação do Código\n\n"
            
            # Documentar módulos
            for modulo in modulos:
                doc += f"## {modulo['nome']}\n\n"
                if modulo['docstring']:
                    doc += f"{modulo['docstring']}\n\n"
                if modulo['imports']:
                    doc += "### Imports\n\n"
                    for imp in modulo['imports']:
                        doc += f"- {imp}\n"
                    doc += "\n"
                if modulo['from_imports']:
                    doc += "### From Imports\n\n"
                    for imp in modulo['from_imports']:
                        doc += f"- {imp}\n"
                    doc += "\n"
            
            # Documentar classes
            if classes:
                doc += "## Classes\n\n"
                for classe in classes:
                    doc += f"### {classe['nome']}\n\n"
                    if classe['docstring']:
                        doc += f"{classe['docstring']}\n\n"
                    if classe['bases']:
                        doc += f"**Herda de:** {', '.join(classe['bases'])}\n\n"
                    if classe['metodos']:
                        doc += "**Métodos:**\n\n"
                        for metodo in classe['metodos']:
                            doc += f"- {metodo}\n"
                        doc += "\n"
            
            # Documentar funções
            if funcoes:
                doc += "## Funções\n\n"
                for funcao in funcoes:
                    doc += f"### {funcao['nome']}\n\n"
                    if funcao['docstring']:
                        doc += f"{funcao['docstring']}\n\n"
                    if funcao['args']:
                        doc += "**Parâmetros:**\n\n"
                        for arg in funcao['args']:
                            doc += f"- {arg}\n"
                        doc += "\n"
                    if funcao['returns']:
                        doc += f"**Retorna:** {funcao['returns']}\n\n"
        
        return doc
    except Exception as e:
        logger.error(f"Erro ao gerar documentação: {e}")
        raise

def extrair_comentarios(codigo: str) -> Dict:
    """Extrai e analisa comentários do código."""
    try:
        comentarios = {
            "docstrings": [],
            "comentarios_linha": [],
            "comentarios_bloco": [],
            "tags": {}
        }
        
        # Extrair docstrings
        tree = ast.parse(codigo)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                docstring = ast.get_docstring(node)
                if docstring:
                    comentarios["docstrings"].append({
                        "tipo": type(node).__name__,
                        "nome": getattr(node, "name", "Módulo"),
                        "conteudo": docstring,
                        "linha": node.lineno
                    })
        
        # Extrair comentários de linha e bloco
        linhas = codigo.split('\n')
        i = 0
        while i < len(linhas):
            linha = linhas[i].strip()
            
            # Comentário de linha
            if linha.startswith('#'):
                comentarios["comentarios_linha"].append({
                    "conteudo": linha[1:].strip(),
                    "linha": i + 1
                })
            
            # Comentário de bloco
            elif linha.startswith('"""') or linha.startswith("'''"):
                inicio = i
                fim = i
                while fim < len(linhas) and not (linhas[fim].strip().endswith('"""') or linhas[fim].strip().endswith("'''")):
                    fim += 1
                
                if fim < len(linhas):
                    conteudo = '\n'.join(linhas[inicio:fim+1])
                    comentarios["comentarios_bloco"].append({
                        "conteudo": conteudo,
                        "linha_inicio": inicio + 1,
                        "linha_fim": fim + 1
                    })
                    i = fim
            
            i += 1
        
        # Extrair tags especiais
        tags = {
            "TODO": [],
            "FIXME": [],
            "HACK": [],
            "NOTE": []
        }
        
        for comentario in comentarios["comentarios_linha"]:
            for tag in tags.keys():
                if tag in comentario["conteudo"]:
                    tags[tag].append({
                        "conteudo": comentario["conteudo"],
                        "linha": comentario["linha"]
                    })
        
        comentarios["tags"] = tags
        
        return comentarios
    except Exception as e:
        logger.error(f"Erro ao extrair comentários: {e}")
        raise

def validar_documentacao(codigo: str) -> Dict:
    """Valida a qualidade da documentação do código."""
    try:
        problemas = []
        
        # Analisar o código
        tree = ast.parse(codigo)
        
        # Verificar docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                docstring = ast.get_docstring(node)
                if not docstring:
                    problemas.append({
                        "tipo": "Docstring Ausente",
                        "severidade": "Média",
                        "descricao": f"{type(node).__name__} sem docstring",
                        "linha": node.lineno
                    })
                elif len(docstring.split()) < 5:
                    problemas.append({
                        "tipo": "Docstring Muito Curta",
                        "severidade": "Baixa",
                        "descricao": f"Docstring muito curta em {type(node).__name__}",
                        "linha": node.lineno
                    })
        
        # Verificar comentários
        linhas = codigo.split('\n')
        for i, linha in enumerate(linhas):
            if '#' in linha:
                comentario = linha[linha.find('#'):].strip()
                if len(comentario) < 10:
                    problemas.append({
                        "tipo": "Comentário Muito Curto",
                        "severidade": "Baixa",
                        "descricao": "Comentário muito curto ou vago",
                        "linha": i + 1
                    })
        
        # Verificar consistência
        docstrings = [ast.get_docstring(node) for node in ast.walk(tree) if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))]
        if docstrings:
            padrao = docstrings[0].split('\n')[0] if docstrings[0] else None
            for i, doc in enumerate(docstrings[1:], 1):
                if doc and doc.split('\n')[0] != padrao:
                    problemas.append({
                        "tipo": "Inconsistência na Documentação",
                        "severidade": "Baixa",
                        "descricao": "Formato de docstring inconsistente",
                        "linha": i
                    })
        
        return {
            "total_problemas": len(problemas),
            "problemas": problemas,
            "recomendacoes": [
                "Adicione docstrings para todos os módulos, classes e funções",
                "Mantenha a documentação atualizada",
                "Use um formato consistente para docstrings",
                "Adicione comentários explicativos para código complexo",
                "Documente parâmetros e valores de retorno"
            ]
        }
    except Exception as e:
        logger.error(f"Erro ao validar documentação: {e}")
        raise

def atualizar_docs(codigo: str, docs: str) -> str:
    """Atualiza a documentação existente com base no código."""
    try:
        # Extrair informações do código
        tree = ast.parse(codigo)
        elementos = {}
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                nome = getattr(node, "name", "Módulo")
                elementos[nome] = {
                    "tipo": type(node).__name__,
                    "docstring": ast.get_docstring(node),
                    "linha": node.lineno
                }
        
        # Atualizar documentação
        linhas = docs.split('\n')
        i = 0
        while i < len(linhas):
            linha = linhas[i].strip()
            
            # Procurar por seções de documentação
            if linha.startswith('### '):
                nome = linha[4:].strip()
                if nome in elementos:
                    # Atualizar docstring
                    if elementos[nome]["docstring"]:
                        # Encontrar próxima seção
                        j = i + 1
                        while j < len(linhas) and not linhas[j].strip().startswith('### '):
                            j += 1
                        
                        # Substituir conteúdo
                        nova_doc = elementos[nome]["docstring"].split('\n')
                        linhas[i+1:j] = [''] + nova_doc + ['']
                        i = j
                    else:
                        i += 1
                else:
                    i += 1
            else:
                i += 1
        
        return '\n'.join(linhas)
    except Exception as e:
        logger.error(f"Erro ao atualizar documentação: {e}")
        raise

def gerar_exemplos(codigo: str) -> Dict:
    """Gera exemplos de uso para o código."""
    try:
        exemplos = {}
        
        # Analisar o código
        tree = ast.parse(codigo)
        
        # Gerar exemplos para funções
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Extrair informações da função
                nome = node.name
                args = [arg.arg for arg in node.args.args]
                docstring = ast.get_docstring(node)
                
                # Gerar exemplo básico
                exemplo = f"# Exemplo de uso da função {nome}\n\n"
                
                # Adicionar imports necessários
                exemplo += "from modulo import " + nome + "\n\n"
                
                # Gerar chamada da função
                args_exemplo = []
                for arg in args:
                    if arg == 'self':
                        continue
                    if arg.endswith('_list'):
                        args_exemplo.append(f"[1, 2, 3]")  # Exemplo para listas
                    elif arg.endswith('_dict'):
                        args_exemplo.append(f"{{'chave': 'valor'}}")  # Exemplo para dicionários
                    elif arg.endswith('_str'):
                        args_exemplo.append(f"'exemplo'")  # Exemplo para strings
                    elif arg.endswith('_int'):
                        args_exemplo.append("42")  # Exemplo para inteiros
                    elif arg.endswith('_bool'):
                        args_exemplo.append("True")  # Exemplo para booleanos
                    else:
                        args_exemplo.append("valor")  # Valor genérico
                
                exemplo += f"resultado = {nome}({', '.join(args_exemplo)})\n"
                exemplo += "print(resultado)\n"
                
                exemplos[nome] = exemplo
        
        return exemplos
    except Exception as e:
        logger.error(f"Erro ao gerar exemplos: {e}")
        raise 