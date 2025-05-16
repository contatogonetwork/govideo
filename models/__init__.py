"""
GONETWORK AI - Modelos de dados
Importações centralizadas para simplificar o acesso aos modelos
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Base declarativa para todos os modelos
Base = declarative_base()

# Importações de modelos individuais
from .base import *
from .user import User
from .event import Event, Stage, Activity, Tag
from .team import TeamMember, TeamAssignment
from .delivery import Delivery, DeliveryFile, DeliveryComment
from .asset import Asset, AssetFolder
from .sponsor import Sponsor, Activation, ActivationType, ActivationEvidence

def init_database(engine_url):
    """
    Inicializa o banco de dados e cria as tabelas
    
    Args:
        engine_url (str): URL do banco de dados para SQLAlchemy
        
    Returns:
        tuple: (engine, Session)
    """
    from sqlalchemy_utils import database_exists, create_database
    
    # Criar engine
    engine = create_engine(engine_url)
    
    # Criar banco de dados se não existir
    if not database_exists(engine.url):
        create_database(engine.url)
    
    # Criar tabelas
    Base.metadata.create_all(engine)
    
    # Criar classe de sessão
    Session = sessionmaker(bind=engine)
    
    return engine, Session

def create_session(engine):
    """
    Cria uma nova sessão do banco de dados
    
    Args:
        engine: Engine do SQLAlchemy
        
    Returns:
        Session: Sessão do SQLAlchemy
    """
    Session = sessionmaker(bind=engine)
    return Session()

# Funções para migração de schema
def update_schema(engine):
    """
    Atualiza o schema do banco de dados para incluir novos modelos/campos
    
    Args:
        engine: Engine do SQLAlchemy
    """
    Base.metadata.create_all(engine)
