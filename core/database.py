#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Configuração e modelos do banco de dados
"""

import os
import logging
import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Float,
    Table,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy_utils import database_exists, create_database

logger = logging.getLogger(__name__)

# Criar base para os modelos
Base = declarative_base()

# Tabelas associativas
event_tags = Table(
    "event_tags",
    Base.metadata,
    Column("event_id", Integer, ForeignKey("events.id", ondelete="CASCADE")),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE")),
)

asset_tags = Table(
    "asset_tags",
    Base.metadata,
    Column("asset_id", Integer, ForeignKey("assets.id", ondelete="CASCADE")),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE")),
)


# Modelos
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    profile_picture = Column(String(255))

    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    created_deliveries = relationship("Delivery", foreign_keys="[Delivery.created_by]", back_populates="creator")
    comments = relationship("DeliveryComment", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    location = Column(String(200))
    description = Column(Text)
    client = Column(String(100))
    status = Column(String(20), default="planning")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

    stages = relationship("Stage", back_populates="event", cascade="all, delete-orphan")
    deliveries = relationship("Delivery", back_populates="event", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="event")
    tags = relationship("Tag", secondary=event_tags, back_populates="events")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Event {self.name}>"


class Stage(Base):
    __tablename__ = "stages"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    description = Column(Text)

    event = relationship("Event", back_populates="stages")
    activities = relationship("Activity", back_populates="stage", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Stage {self.name}>"


class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    stage_id = Column(Integer, ForeignKey("stages.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    details = Column(Text)
    type = Column(String(50))
    priority = Column(Integer, default=3)

    stage = relationship("Stage", back_populates="activities")
    team_assignments = relationship("TeamAssignment", back_populates="activity", cascade="all, delete-orphan")
    deliveries = relationship("Delivery", back_populates="activity")

    def __repr__(self):
        return f"<Activity {self.name}>"


class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    skills = Column(Text)
    contact_info = Column(String(200))
    equipment = Column(Text)
    hourly_rate = Column(Float)

    user = relationship("User", back_populates="team_memberships")
    assignments = relationship("TeamAssignment", back_populates="member", cascade="all, delete-orphan")
    deliveries = relationship("Delivery", back_populates="responsible")

    def __repr__(self):
        return f"<TeamMember {self.name} ({self.role})>"


class TeamAssignment(Base):
    __tablename__ = "team_assignments"
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("team_members.id", ondelete="CASCADE"))
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"))
    equipment = Column(Text)
    role_details = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    member = relationship("TeamMember", back_populates="assignments")
    activity = relationship("Activity", back_populates="team_assignments")

    def __repr__(self):
        return f"<TeamAssignment {self.member_id} to {self.activity_id}>"


class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    deadline = Column(DateTime, nullable=False)
    format_specs = Column(Text)
    responsible_id = Column(Integer, ForeignKey("team_members.id"))
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="SET NULL"), nullable=True)
    priority = Column(Integer, default=3)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    published_at = Column(DateTime)

    files = relationship("DeliveryFile", back_populates="delivery", cascade="all, delete-orphan")
    comments = relationship("DeliveryComment", back_populates="delivery", cascade="all, delete-orphan")
    responsible = relationship("TeamMember", back_populates="deliveries")
    event = relationship("Event", back_populates="deliveries")
    activity = relationship("Activity", back_populates="deliveries")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_deliveries")

    def __repr__(self):
        return f"<Delivery {self.title}>"


class DeliveryFile(Base):
    __tablename__ = "delivery_files"
    id = Column(Integer, primary_key=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id", ondelete="CASCADE"))
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    file_type = Column(String(50))
    version = Column(Integer, default=1)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    file_size = Column(Integer)
    duration = Column(Integer, nullable=True)
    is_final = Column(Boolean, default=False)
    technical_metadata = Column(Text)  # JSON com metadados técnicos

    delivery = relationship("Delivery", back_populates="files")
    uploader = relationship("User")

    def __repr__(self):
        return f"<DeliveryFile {self.filename} v{self.version}>"


class DeliveryComment(Base):
    __tablename__ = "delivery_comments"
    id = Column(Integer, primary_key=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    comment = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    timecode = Column(String(12), nullable=True)

    delivery = relationship("Delivery", back_populates="comments")
    user = relationship("User", back_populates="comments")

    def __repr__(self):
        return f"<DeliveryComment by {self.user_id} on {self.timestamp}>"


class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    file_path = Column(String(512), nullable=False)
    asset_type = Column(String(50), nullable=False)
    description = Column(Text)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    folder_id = Column(Integer, ForeignKey("asset_folders.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    file_size = Column(Integer)
    duration = Column(Integer, nullable=True)
    technical_metadata = Column(Text)  # JSON com metadados técnicos

    event = relationship("Event", back_populates="assets")
    folder = relationship("AssetFolder", back_populates="assets")
    creator = relationship("User")
    tags = relationship("Tag", secondary=asset_tags, back_populates="assets")

    def __repr__(self):
        return f"<Asset {self.name}>"


class AssetFolder(Base):
    __tablename__ = "asset_folders"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("asset_folders.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relacionamentos corrigidos
    subfolders = relationship(
        "AssetFolder",
        back_populates="parent",
        remote_side=[id],
        cascade="all, delete-orphan",
        single_parent=True  # Correção para o erro de cascade delete-orphan
    )
    parent = relationship(
        "AssetFolder", back_populates="subfolders", remote_side=[parent_id]
    )
    assets = relationship("Asset", back_populates="folder")
    creator = relationship("User")

    def __repr__(self):
        return f"<AssetFolder {self.name}>"


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    color = Column(String(7), default="#cccccc")

    events = relationship("Event", secondary=event_tags, back_populates="tags")
    assets = relationship("Asset", secondary=asset_tags, back_populates="tags")

    def __repr__(self):
        return f"<Tag {self.name}>"


def setup_database(engine_url, base):
    """
    Configura e inicializa o banco de dados se ele ainda não existir.
    
    Args:
        engine_url: URL de conexão com o banco de dados
        base: Base declarativa do SQLAlchemy que contém os modelos
    
    Returns:
        Engine do SQLAlchemy
    """
    from sqlalchemy import create_engine
    
    engine = create_engine(engine_url)
    
    # Cria o banco de dados se não existir
    if not database_exists(engine.url):
        create_database(engine.url)
        print(f"Banco de dados criado em {engine.url}")
    
    # Cria as tabelas
    base.metadata.create_all(engine)
    print("Tabelas criadas/verificadas com sucesso")
    
    return engine


def create_session(engine):
    """
    Cria e retorna uma nova sessão de banco de dados.
    
    Args:
        engine: Engine do SQLAlchemy
        
    Returns:
        Sessão do SQLAlchemy
    """
    from sqlalchemy.orm import sessionmaker
    
    Session = sessionmaker(bind=engine)
    return Session()


def init_database():
    """Inicializa o banco de dados e retorna uma sessão"""
    db_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "gonetwork.db")
    )
    engine_url = f"sqlite:///{db_path}"
    
    # Criar engine
    engine = create_engine(engine_url)
    
    # Criar banco de dados se não existir
    if not database_exists(engine.url):
        create_database(engine.url)
    
    # Criar tabelas
    Base.metadata.create_all(engine)
    
    # Criar sessão
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Verificar se já existem dados básicos
    if session.query(User).count() == 0:
        try:
            # Criar usuário admin padrão
            from werkzeug.security import generate_password_hash
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                full_name="Admin User",
                email="admin@gonetwork.ai",
                role="admin"
            )
            session.add(admin)
            
            # Criar algumas tags básicas
            default_tags = [
                Tag(name="Urgente", color="#ff0000"),
                Tag(name="Show", color="#00ff00"),
                Tag(name="Entrevista", color="#0000ff"),
                Tag(name="Backstage", color="#ffff00"),
                Tag(name="Aprovado", color="#00ffff")
            ]
            session.add_all(default_tags)
            
            # Criar pastas básicas de assets
            root_folders = [
                AssetFolder(name="Logos", created_by=1),
                AssetFolder(name="Templates", created_by=1),
                AssetFolder(name="Música", created_by=1),
                AssetFolder(name="Efeitos Sonoros", created_by=1),
                AssetFolder(name="Imagens de Stock", created_by=1)
            ]
            session.add_all(root_folders)
            
            session.commit()
            logger.info("Banco de dados inicializado com dados padrão")
        except ImportError:
            logger.error("Módulo werkzeug não encontrado. Instale-o com: pip install werkzeug")
            raise Exception("Dependência não satisfeita: werkzeug")
        except Exception as e:
            session.rollback()
            logger.error(f"Erro ao inicializar dados padrão: {str(e)}")
            raise
    
    return session