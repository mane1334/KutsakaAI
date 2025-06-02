import re
import hashlib
import jwt
import bcrypt
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta
import requests
import ssl
import socket
import OpenSSL
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def verificar_seguranca(url: str) -> Dict:
    """Realiza uma análise básica de segurança de uma URL."""
    try:
        resultado = {
            "url": url,
            "ssl": False,
            "certificado": None,
            "vulnerabilidades": [],
            "headers_seguranca": {},
            "recomendacoes": []
        }
        
        # Verificar SSL
        try:
            parsed_url = urlparse(url)
            hostname = parsed_url.netloc
            
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    resultado["ssl"] = True
                    resultado["certificado"] = {
                        "valido_ate": cert["notAfter"],
                        "emissor": cert["issuer"],
                        "versao": cert["version"]
                    }
        except Exception as e:
            resultado["vulnerabilidades"].append("SSL não configurado ou inválido")
            resultado["recomendacoes"].append("Implementar SSL/TLS")
        
        # Verificar headers de segurança
        try:
            response = requests.get(url)
            headers = response.headers
            
            # Verificar headers importantes
            headers_seguranca = {
                "Strict-Transport-Security": headers.get("Strict-Transport-Security"),
                "X-Frame-Options": headers.get("X-Frame-Options"),
                "X-Content-Type-Options": headers.get("X-Content-Type-Options"),
                "X-XSS-Protection": headers.get("X-XSS-Protection"),
                "Content-Security-Policy": headers.get("Content-Security-Policy")
            }
            
            resultado["headers_seguranca"] = headers_seguranca
            
            # Verificar headers ausentes
            for header, valor in headers_seguranca.items():
                if not valor:
                    resultado["vulnerabilidades"].append(f"Header {header} ausente")
                    resultado["recomendacoes"].append(f"Implementar header {header}")
        
        except Exception as e:
            resultado["vulnerabilidades"].append(f"Erro ao verificar headers: {str(e)}")
        
        return resultado
    except Exception as e:
        logger.error(f"Erro ao verificar segurança: {e}")
        raise

def sanitizar_input(texto: str, tipo: str = "texto") -> str:
    """Limpa e sanitiza dados de entrada."""
    try:
        if tipo == "texto":
            # Remover caracteres especiais e scripts
            texto = re.sub(r'<[^>]*>', '', texto)  # Remover HTML
            texto = re.sub(r'javascript:', '', texto, flags=re.IGNORECASE)  # Remover JavaScript
            texto = re.sub(r'[^\w\s\-.,]', '', texto)  # Manter apenas caracteres seguros
            
        elif tipo == "email":
            # Validar e sanitizar email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, texto):
                raise ValueError("Email inválido")
            texto = texto.lower()
            
        elif tipo == "url":
            # Validar e sanitizar URL
            parsed = urlparse(texto)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError("URL inválida")
            texto = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
        elif tipo == "numero":
            # Validar e sanitizar número
            if not texto.isdigit():
                raise ValueError("Valor não é um número válido")
            
        return texto
    except Exception as e:
        logger.error(f"Erro ao sanitizar input: {e}")
        raise

def validar_permissao(usuario: str, recurso: str, acao: str) -> bool:
    """Verifica se um usuário tem permissão para realizar uma ação em um recurso."""
    try:
        # Aqui você pode integrar com seu sistema de permissões
        # Este é um exemplo básico
        permissoes = {
            "admin": {
                "arquivos": ["ler", "escrever", "deletar"],
                "usuarios": ["ler", "escrever", "deletar"],
                "configuracoes": ["ler", "escrever"]
            },
            "usuario": {
                "arquivos": ["ler"],
                "perfil": ["ler", "escrever"]
            }
        }
        
        if usuario not in permissoes:
            return False
            
        if recurso not in permissoes[usuario]:
            return False
            
        return acao in permissoes[usuario][recurso]
    except Exception as e:
        logger.error(f"Erro ao validar permissão: {e}")
        raise

def criptografar_dados(dados: str, chave: str) -> str:
    """Realiza criptografia básica de dados."""
    try:
        # Gerar salt
        salt = bcrypt.gensalt()
        
        # Criptografar dados
        dados_bytes = dados.encode('utf-8')
        hash_bytes = bcrypt.hashpw(dados_bytes, salt)
        
        return hash_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Erro ao criptografar dados: {e}")
        raise

def verificar_vulnerabilidades(codigo: str) -> Dict:
    """Verifica vulnerabilidades comuns no código."""
    try:
        vulnerabilidades = []
        
        # Verificar injeção SQL
        if re.search(r'SELECT.*FROM.*WHERE.*=.*["\']', codigo, re.IGNORECASE):
            vulnerabilidades.append({
                "tipo": "SQL Injection",
                "severidade": "Alta",
                "descricao": "Possível vulnerabilidade de injeção SQL detectada",
                "linha": codigo.find("SELECT")
            })
        
        # Verificar XSS
        if re.search(r'<script.*>.*</script>', codigo, re.IGNORECASE):
            vulnerabilidades.append({
                "tipo": "XSS",
                "severidade": "Alta",
                "descricao": "Possível vulnerabilidade XSS detectada",
                "linha": codigo.find("<script")
            })
        
        # Verificar senhas hardcoded
        if re.search(r'password\s*=\s*["\'].*["\']', codigo, re.IGNORECASE):
            vulnerabilidades.append({
                "tipo": "Hardcoded Password",
                "severidade": "Média",
                "descricao": "Senha hardcoded detectada no código",
                "linha": codigo.find("password")
            })
        
        # Verificar uso de eval
        if "eval(" in codigo:
            vulnerabilidades.append({
                "tipo": "Dangerous Function",
                "severidade": "Alta",
                "descricao": "Uso da função eval() detectado",
                "linha": codigo.find("eval")
            })
        
        return {
            "total_vulnerabilidades": len(vulnerabilidades),
            "vulnerabilidades": vulnerabilidades,
            "recomendacoes": [
                "Usar prepared statements para queries SQL",
                "Sanitizar inputs do usuário",
                "Evitar hardcoding de credenciais",
                "Usar alternativas seguras para eval()"
            ]
        }
    except Exception as e:
        logger.error(f"Erro ao verificar vulnerabilidades: {e}")
        raise 