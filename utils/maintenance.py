#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Utilitário de Manutenção
Realiza várias tarefas de manutenção como:
- Limpeza de arquivos temporários
- Compactação do banco de dados
- Rotação de backups
"""

import os
import sys
import shutil
import logging
import sqlite3
import datetime
from pathlib import Path

# Adicionar o diretório pai ao PATH para importar módulos do projeto
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Importar configurações do projeto
from core.config import DEFAULT_DB_PATH, UPLOAD_DIR

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("maintenance")

def clean_temp_files():
    """Limpa arquivos temporários do projeto"""
    logger.info("Iniciando limpeza de arquivos temporários...")
    
    temp_pattern = "*.tmp"
    temp_dirs = [
        UPLOAD_DIR,
        os.path.join(parent_dir, "logs")
    ]
    
    total_removed = 0
    total_size = 0
    
    for temp_dir in temp_dirs:
        if not os.path.exists(temp_dir):
            continue
            
        try:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.tmp'):
                        file_path = os.path.join(root, file)
                        # Verificar a idade do arquivo (remover se +7 dias)
                        file_age = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_age.days > 7:
                            size = os.path.getsize(file_path)
                            total_size += size
                            os.remove(file_path)
                            total_removed += 1
                            logger.debug(f"Removido: {file_path} ({size} bytes)")
        except Exception as e:
            logger.error(f"Erro ao limpar arquivos temporários em {temp_dir}: {e}")
    
    logger.info(f"Limpeza de arquivos temporários concluída. Removidos {total_removed} arquivos ({total_size/1024:.2f} KB)")

def optimize_database():
    """Otimiza o banco de dados SQLite"""
    logger.info(f"Iniciando otimização do banco de dados: {DEFAULT_DB_PATH}")
    
    if not os.path.exists(DEFAULT_DB_PATH):
        logger.error(f"Banco de dados não encontrado: {DEFAULT_DB_PATH}")
        return False
    
    try:
        # Criar backup antes da otimização
        backup_dir = os.path.join(parent_dir, "backup")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"pre_optimize_{timestamp}_gonetwork.db")
        
        shutil.copy2(DEFAULT_DB_PATH, backup_file)
        logger.info(f"Backup criado: {backup_file}")
        
        # Conectar e otimizar o banco
        conn = sqlite3.connect(DEFAULT_DB_PATH)
        conn.execute("VACUUM")
        conn.execute("PRAGMA optimize")
        conn.execute("ANALYZE")
        conn.close()
        
        logger.info("Otimização do banco de dados concluída com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao otimizar banco de dados: {e}")
        return False

def rotate_backups():
    """Mantém apenas os 10 backups mais recentes"""
    backup_dir = os.path.join(parent_dir, "backup")
    if not os.path.exists(backup_dir):
        return
    
    logger.info("Iniciando rotação de backups...")
    
    try:
        # Listar todos os arquivos de backup
        backup_files = []
        for file in os.listdir(backup_dir):
            if file.endswith('.db'):
                file_path = os.path.join(backup_dir, file)
                backup_files.append((file_path, os.path.getmtime(file_path)))
        
        # Ordenar por data (mais antigos primeiro)
        backup_files.sort(key=lambda x: x[1])
        
        # Manter apenas os 10 mais recentes
        max_backups = 10
        if len(backup_files) > max_backups:
            files_to_delete = backup_files[:-max_backups]
            for file_path, _ in files_to_delete:
                os.remove(file_path)
                logger.info(f"Backup antigo removido: {os.path.basename(file_path)}")
            
            logger.info(f"Rotação de backups concluída. Removidos {len(files_to_delete)} backups antigos")
        else:
            logger.info(f"Rotação de backups: há apenas {len(backup_files)} backups (máximo é {max_backups})")
    except Exception as e:
        logger.error(f"Erro na rotação de backups: {e}")

def create_backup():
    """Cria um backup do banco de dados atual"""
    logger.info("Criando backup do banco de dados...")
    
    try:
        backup_dir = os.path.join(parent_dir, "backup")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}")
        
        # Criar diretório de backup com timestamp
        os.makedirs(backup_file, exist_ok=True)
        
        # Backup do banco de dados
        db_backup = os.path.join(backup_file, "gonetwork.db")
        shutil.copy2(DEFAULT_DB_PATH, db_backup)
        
        # Backup das configurações
        config_path = os.path.join(parent_dir, "core", "config.py")
        if os.path.exists(config_path):
            config_backup = os.path.join(backup_file, "config.py")
            shutil.copy2(config_path, config_backup)
        
        # Backup do log
        log_path = os.path.join(parent_dir, "logs", "gonetwork_ai.log")
        if os.path.exists(log_path):
            log_backup = os.path.join(backup_file, "gonetwork_ai.log")
            shutil.copy2(log_path, log_backup)
        
        logger.info(f"Backup criado com sucesso em: {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar backup: {e}")
        return False

def main():
    """Executa todas as tarefas de manutenção"""
    logger.info("Iniciando tarefas de manutenção...")
    
    # Criar backup antes de qualquer alteração
    create_backup()
    
    # Executar manutenção
    clean_temp_files()
    optimize_database()
    rotate_backups()
    
    logger.info("Manutenção concluída com sucesso!")

if __name__ == "__main__":
    main()
