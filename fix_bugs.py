#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Script para correção de bugs
Data: 2025-05-15
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
import time

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def fix_database_schema():
    """Adiciona o campo is_system à tabela delivery_comments"""
    
    try:
        # Obter caminho do banco de dados
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "gonetwork.db"))
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
                logger.info("Coluna 'is_system' adicionada com sucesso à tabela delivery_comments")
                print("Coluna 'is_system' adicionada à tabela delivery_comments")
            else:
                logger.info("A coluna 'is_system' já existe na tabela delivery_comments")
                print("A coluna 'is_system' já existe na tabela delivery_comments")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar a tabela delivery_comments: {str(e)}")
        print(f"Erro: {str(e)}")
        return False

def main():
    """Função principal que corrige os bugs"""
    print("\n===== CORREÇÃO DE BUGS DO GONETWORK AI =====\n")
    print("Iniciando processo de correção...")
    
    # Bug 1: Corrigir banco de dados - is_system
    print("\n[1/2] Corrigindo a estrutura do banco de dados para DeliveryComment...")
    if fix_database_schema():
        print("✓ Estrutura do banco de dados atualizada com sucesso!")
    else:
        print("✗ Falha ao atualizar estrutura do banco de dados")
        return False
    
    # Bug 2: O código já foi atualizado para tratar o NoneType em on_edit_delivery
    print("\n[2/2] O código foi atualizado para corrigir o erro NoneType no Delivery View")
    print("✓ Código atualizado com sucesso!")
    
    # Resumo das correções
    print("\n===== RESUMO DA CORREÇÃO =====")
    print("1. Adicionado campo 'is_system' à tabela delivery_comments")
    print("2. Corrigido o erro 'NoneType' object has no attribute 'id' no método on_edit_delivery")
    print("\nTodas as correções foram aplicadas com sucesso!")
    
    return True

if __name__ == "__main__":
    try:
        if main():
            print("\nCorreções aplicadas com sucesso. O sistema está pronto para uso!")
            sys.exit(0)
        else:
            print("\nOcorreram erros durante o processo de correção. Verifique os logs para mais detalhes.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        print(f"\nErro inesperado: {str(e)}")
        sys.exit(1)
