#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Atualização do banco de dados com novos modelos
Data: 2025-05-15
Autor: GONETWORK AI
"""

import os
import logging
import datetime
import enum
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float, Table, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy_utils import database_exists, create_database

# Importando a base existente
from core.database import Base, setup_database

logger = logging.getLogger(__name__)

# Definição dos novos enums para status
class ActivationStatus(enum.Enum):
    pending = "pending"
    filmed = "filmed"
    failed = "failed"

class AssignmentStatus(enum.Enum):
    ativo = "ativo"
    pausa = "pausa"
    finalizado = "finalizado"

# Novos modelos - movidos para database.py
# class Sponsor foi movida para database.py
    logo_path = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relacionamentos
    activations = relationship("Activation", back_populates="sponsor", cascade="all, delete-orphan")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<Sponsor {self.name}>"


# class Activation foi movida para database.py com estrutura atualizada


def update_database():
    """Atualiza o banco de dados com os novos modelos"""
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gonetwork.db"))
    engine_url = f"sqlite:///{db_path}"
    
    # Criar engine
    engine = create_engine(engine_url)
    
    # Verificar se o banco de dados existe
    if not database_exists(engine.url):
        print(f"Banco de dados não encontrado em {db_path}")
        return
    
    # Criar tabelas para os novos modelos
    # Isso criará apenas as tabelas que não existem ainda
    try:
        Base.metadata.create_all(engine)
        print("Banco de dados atualizado com sucesso!")
        
        # Atualizar a tabela TeamAssignment com os novos campos
        from sqlalchemy import text
        
        # Verificar se a coluna status já existe
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(team_assignments)"))
            columns = [row[1] for row in result]
              # Adicionar colunas que não existem
            if "location" not in columns:
                conn.execute(text("ALTER TABLE team_assignments ADD COLUMN location VARCHAR"))
                print("Coluna 'location' adicionada à tabela team_assignments")
                
            if "status" not in columns:
                # SQLite não suporta ALTER TABLE ADD COLUMN com tipos enum, então usamos VARCHAR
                conn.execute(text("ALTER TABLE team_assignments ADD COLUMN status VARCHAR"))
                print("Coluna 'status' adicionada à tabela team_assignments")
                
            # Verificar se já existem as colunas start_time e end_time
            if "start_time" not in columns:
                conn.execute(text("ALTER TABLE team_assignments ADD COLUMN start_time DATETIME"))
                print("Coluna 'start_time' adicionada à tabela team_assignments")
                
            if "end_time" not in columns:
                conn.execute(text("ALTER TABLE team_assignments ADD COLUMN end_time DATETIME"))
                print("Coluna 'end_time' adicionada à tabela team_assignments")
                
            print("Atualização concluída com sucesso!")
            
    except Exception as e:
        print(f"Erro ao atualizar o banco de dados: {str(e)}")
        logger.error(f"Erro na atualização do banco de dados: {str(e)}")


if __name__ == "__main__":
    update_database()
