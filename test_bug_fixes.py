#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Script de teste para verificar correções de bugs
Data: 2025-05-15
"""

import os
import sys
import logging
import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar modelos necessários
from core.database import Base, DeliveryComment, Delivery

def verify_database_schema():
    """Verificar se o campo is_system existe na tabela delivery_comments"""
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
            
            if "is_system" in columns:
                print("✓ Campo 'is_system' existe na tabela delivery_comments")
                return True
            else:
                print("✗ Campo 'is_system' NÃO existe na tabela delivery_comments")
                return False
    except Exception as e:
        logger.error(f"Erro ao verificar o esquema do banco de dados: {str(e)}")
        print(f"Erro: {str(e)}")
        return False

def test_create_system_comment():
    """Testar a criação de um comentário com is_system=True"""
    try:
        # Obter caminho do banco de dados
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "gonetwork.db"))
        engine_url = f"sqlite:///{db_path}"
        
        # Criar engine e sessão
        engine = create_engine(engine_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Obter a primeira entrega para teste
        delivery = session.query(Delivery).first()
        if not delivery:
            print("✗ Não foi possível encontrar uma entrega para teste")
            return False
            
        # Criar um comentário de sistema
        test_comment = DeliveryComment(
            delivery_id=delivery.id,
            user_id=1,  # Admin
            comment="Teste de comentário do sistema - Correção de bug",
            timestamp=datetime.datetime.now(),
            is_system=True
        )
        
        # Adicionar e salvar
        session.add(test_comment)
        session.commit()
        
        # Verificar se foi criado
        created_comment = session.query(DeliveryComment).filter_by(comment="Teste de comentário do sistema - Correção de bug").first()
        
        if created_comment and created_comment.is_system:
            print(f"✓ Comentário com is_system=True criado com sucesso (ID: {created_comment.id})")
            return True
        else:
            print("✗ Falha ao criar comentário com is_system=True")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao testar criação de comentário: {str(e)}")
        print(f"Erro: {str(e)}")
        return False
    finally:
        if 'session' in locals():
            session.close()

def main():
    """Função principal de testes"""
    print("\n===== TESTES DE CORREÇÕES DE BUGS - GONETWORK AI =====\n")
    
    # Teste 1: Verificar estrutura do banco de dados
    print("[Teste 1] Verificando estrutura da tabela delivery_comments...")
    schema_ok = verify_database_schema()
    
    # Teste 2: Testar criação de comentário com is_system=True
    print("\n[Teste 2] Testando criação de comentário com is_system=True...")
    comment_ok = test_create_system_comment()
    
    # Resumo
    print("\n===== RESUMO DOS TESTES =====")
    print(f"1. Estrutura da tabela: {'✓ OK' if schema_ok else '✗ FALHA'}")
    print(f"2. Criação de comentário: {'✓ OK' if comment_ok else '✗ FALHA'}")
    
    if schema_ok and comment_ok:
        print("\n✓ TODOS OS TESTES PASSARAM! As correções foram aplicadas com sucesso.")
        return True
    else:
        print("\n✗ ALGUNS TESTES FALHARAM. Verifique os erros acima.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Erro inesperado nos testes: {str(e)}")
        print(f"\nErro inesperado: {str(e)}")
        sys.exit(1)
