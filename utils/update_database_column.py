#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Atualização da tabela de comentários para adicionar campo is_system
Data: 2025-05-15
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger(__name__)

def update_delivery_comments_table():
    """Adiciona o campo is_system à tabela delivery_comments"""
    
    try:
        # Obter caminho do banco de dados
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gonetwork.db"))
        engine_url = f"sqlite:///{db_path}"
        
        # Criar engine
        engine = create_engine(engine_url)
        
        # Verificar se a coluna já existe
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(delivery_comments)"))
            columns = [row[1] for row in result]
            
            if "is_system" not in columns:
                # Adicionar coluna is_system
                conn.execute(text("ALTER TABLE delivery_comments ADD COLUMN is_system BOOLEAN DEFAULT 0"))
                print("Coluna 'is_system' adicionada à tabela delivery_comments")
                logger.info("Coluna 'is_system' adicionada com sucesso à tabela delivery_comments")
            else:
                print("A coluna 'is_system' já existe na tabela delivery_comments")
                logger.info("A coluna 'is_system' já existe na tabela delivery_comments")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar a tabela delivery_comments: {str(e)}")
        print(f"Erro: {str(e)}")
        return False

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Iniciando atualização da tabela delivery_comments...")
    success = update_delivery_comments_table()
    
    if success:
        print("Atualização do banco de dados concluída com sucesso!")
    else:
        print("Ocorreu um erro durante a atualização do banco de dados.")
        sys.exit(1)
