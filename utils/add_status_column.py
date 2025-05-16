#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Ferramenta para adicionar coluna status na tabela team_assignments
Data: 2025-05-15
Autor: GONETWORK AI
"""

import os
import sys
import sqlite3
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_status_column():
    """Adicionar coluna status à tabela team_assignments"""
    # Importar a configuração para obter o caminho do banco de dados
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from core.config import Settings
        main_db_path = Settings().database_path
        logger.info(f"Caminho do banco de dados principal: {main_db_path}")
    except ImportError:
        logger.warning("Não foi possível importar as configurações. Usando caminhos padrão.")
        main_db_path = None
    
    # Possíveis localizações do banco de dados
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    possible_paths = [
        main_db_path,  # Caminho do banco de dados principal
        os.path.join(base_path, 'data', 'gonetwork.db'),
        os.path.join(base_path, 'gonetwork.db'),
    ]
    
    db_paths = []
    
    # Encontrar todos os bancos de dados existentes
    for path in possible_paths:
        if path and os.path.exists(path):
            db_paths.append(path)
            logger.info(f"Banco de dados encontrado em: {path}")
    
    if not db_paths:
        logger.error("Banco de dados não encontrado em nenhum local esperado")
        return False
        
    # Aplicar atualização em todos os bancos de dados encontrados
    success = True
    for db_path in db_paths:
        if not update_database(db_path):
            success = False
            
    return success

def update_database(db_path):
    """Atualiza um banco de dados específico"""
    try:
        # Conectar ao banco de dados
        logger.info(f"Conectando ao banco de dados {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(team_assignments)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "status" in columns:
            logger.info(f"A coluna 'status' já existe na tabela team_assignments em {db_path}")
            conn.close()
            return True
        
        # Adicionar coluna
        logger.info(f"Adicionando coluna 'status' à tabela team_assignments em {db_path}")
        cursor.execute("ALTER TABLE team_assignments ADD COLUMN status TEXT DEFAULT 'ativo'")
        
        # Commit e fechar
        conn.commit()
        conn.close()
        
        logger.info(f"Coluna 'status' adicionada com sucesso em {db_path}!")
        return True
    
    except sqlite3.Error as e:
        logger.error(f"Erro ao adicionar coluna em {db_path}: {e}")
        return False
    
    try:
        # Conectar ao banco de dados
        logger.info(f"Conectando ao banco de dados {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(team_assignments)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "status" in columns:
            logger.info("A coluna 'status' já existe na tabela team_assignments")
            conn.close()
            return True
        
        # Adicionar coluna
        logger.info("Adicionando coluna 'status' à tabela team_assignments")
        cursor.execute("ALTER TABLE team_assignments ADD COLUMN status TEXT DEFAULT 'ativo'")
        
        # Commit e fechar
        conn.commit()
        conn.close()
        
        logger.info("Coluna 'status' adicionada com sucesso!")
        return True
    
    except sqlite3.Error as e:
        logger.error(f"Erro ao adicionar coluna: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando atualização do banco de dados...")
    result = add_status_column()
    
    if result:
        print("Atualização concluída com sucesso!")
        sys.exit(0)
    else:
        print("Falha na atualização do banco de dados.")
        sys.exit(1)
