#!/usr/bin/env python3
"""
Script de atualização do Agente IA
Gerencia o processo de atualização do sistema, incluindo backup e verificação de versão
"""

import os
import shutil
import json
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import requests
import sys

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/update.log', maxBytes=1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)

def criar_backup():
    """Cria backup dos arquivos de configuração e dados importantes."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f'backups/backup_{timestamp}'
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        # Arquivos para backup
        arquivos = ['config.py', 'VERSION']
        
        for arquivo in arquivos:
            if os.path.exists(arquivo):
                shutil.copy2(arquivo, os.path.join(backup_dir, arquivo))
                logging.info(f'Backup criado para {arquivo}')
        
        # Backup do diretório de logs
        if os.path.exists('logs'):
            shutil.copytree('logs', os.path.join(backup_dir, 'logs'))
            logging.info('Backup criado para logs')
            
        return backup_dir
    except Exception as e:
        logging.error(f'Erro ao criar backup: {e}')
        return None

def verificar_atualizacoes():
    """Verifica se há atualizações disponíveis."""
    try:
        # Aqui você pode implementar a lógica para verificar atualizações
        # Por exemplo, verificar um repositório Git ou uma API
        return False, "Nenhuma atualização disponível"
    except Exception as e:
        logging.error(f'Erro ao verificar atualizações: {e}')
        return False, str(e)

def atualizar_sistema():
    """Executa o processo de atualização do sistema."""
    logging.info('Iniciando processo de atualização')
    
    # Criar backup
    backup_dir = criar_backup()
    if not backup_dir:
        logging.error('Falha ao criar backup. Abortando atualização.')
        return False
    
    try:
        # Aqui você implementaria a lógica de atualização
        # Por exemplo, baixar novos arquivos, atualizar dependências, etc.
        
        logging.info('Atualização concluída com sucesso')
        return True
    except Exception as e:
        logging.error(f'Erro durante a atualização: {e}')
        
        # Restaurar backup em caso de erro
        try:
            for arquivo in os.listdir(backup_dir):
                src = os.path.join(backup_dir, arquivo)
                dst = os.path.join(os.getcwd(), arquivo)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst)
            logging.info('Backup restaurado com sucesso')
        except Exception as restore_error:
            logging.error(f'Erro ao restaurar backup: {restore_error}')
        
        return False

def main():
    """Função principal do script de atualização."""
    logging.info('Iniciando verificação de atualizações')
    
    # Verificar se há atualizações
    tem_atualizacao, mensagem = verificar_atualizacoes()
    
    if not tem_atualizacao:
        logging.info(mensagem)
        return
    
    # Confirmar atualização com o usuário
    print(f'\n{mensagem}')
    resposta = input('Deseja prosseguir com a atualização? (s/N): ').lower()
    
    if resposta != 's':
        logging.info('Atualização cancelada pelo usuário')
        return
    
    # Executar atualização
    if atualizar_sistema():
        logging.info('Sistema atualizado com sucesso')
        print('\nAtualização concluída com sucesso!')
    else:
        logging.error('Falha na atualização do sistema')
        print('\nErro durante a atualização. Verifique os logs para mais detalhes.')

if __name__ == '__main__':
    main() 