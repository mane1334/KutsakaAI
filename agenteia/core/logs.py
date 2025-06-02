"""
Módulo para configuração de logging.
"""

import os
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logging(name: str) -> logging.Logger:
    """
    Configura o logging para um módulo.
    
    Args:
        name: Nome do módulo para o logger
        
    Returns:
        Logger configurado
    """
    # Criar logger
    logger = logging.getLogger(name)
    
    # Se já estiver configurado, retornar
    if logger.handlers:
        return logger
        
    # Configurar nível
    logger.setLevel(logging.INFO)
    
    # Criar diretório de logs se não existir
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar formato
    formato = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Handler para arquivo
    arquivo_handler = RotatingFileHandler(
        log_dir / f"{name}.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    arquivo_handler.setFormatter(formato)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formato)
    
    # Adicionar handlers
    logger.addHandler(arquivo_handler)
    logger.addHandler(console_handler)
    
    return logger 