"""
GONETWORK AI - Modelos relacionados a eventos
"""

import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float, Enum
from sqlalchemy.orm import relationship

from . import Base
from .base import event_tags

class Event(Base):
    """
    Modelo para eventos
    """
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
    parent_id = Column(Integer, ForeignKey("events.id"), nullable=True)

    # Relacionamentos
    stages = relationship("Stage", back_populates="event", cascade="all, delete-orphan")
    deliveries = relationship("Delivery", back_populates="event", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="event")
    tags = relationship("Tag", secondary=event_tags, back_populates="events")
    creator = relationship("User", foreign_keys=[created_by])
    activations = relationship("Activation", back_populates="event", cascade="all, delete-orphan")
    
    # Relacionamentos hierárquicos
    parent = relationship("Event", remote_side=[id], backref="sub_events")

    def __repr__(self):
        return f"<Event {self.name}>"
    
    @classmethod
    def get_upcoming_events(cls, session, limit=5):
        """
        Obtém os próximos eventos
        
        Args:
            session: Sessão do SQLAlchemy
            limit (int): Limite de resultados
            
        Returns:
            list: Lista de objetos Event
        """
        now = datetime.datetime.now()
        return session.query(cls).filter(cls.start_date >= now).order_by(cls.start_date).limit(limit).all()
    
    @classmethod
    def get_current_events(cls, session):
        """
        Obtém eventos em andamento
        
        Args:
            session: Sessão do SQLAlchemy
            
        Returns:
            list: Lista de objetos Event
        """
        now = datetime.datetime.now()
        return session.query(cls).filter(cls.start_date <= now, cls.end_date >= now).all()


class Stage(Base):
    """
    Modelo para palcos/áreas de um evento
    """
    __tablename__ = "stages"
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    description = Column(Text)

    # Relacionamentos
    event = relationship("Event", back_populates="stages")
    activities = relationship("Activity", back_populates="stage", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Stage {self.name}>"


class Activity(Base):
    """
    Modelo para atividades de um palco/área
    """
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True)
    stage_id = Column(Integer, ForeignKey("stages.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    details = Column(Text)
    type = Column(String(50))
    priority = Column(Integer, default=3)
    status = Column(String(20), default="pending")
    
    # Relacionamentos
    stage = relationship("Stage", back_populates="activities")
    team_assignments = relationship("TeamAssignment", back_populates="activity", cascade="all, delete-orphan")
    deliveries = relationship("Delivery", back_populates="activity")
    activations = relationship("Activation", back_populates="activity")

    def __repr__(self):
        return f"<Activity {self.name}>"


class Tag(Base):
    """
    Modelo para tags categorizadoras
    """
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    color = Column(String(7), default="#cccccc")

    # Relacionamentos
    events = relationship("Event", secondary=event_tags, back_populates="tags")
    assets = relationship("Asset", secondary="asset_tags", back_populates="tags")

    def __repr__(self):
        return f"<Tag {self.name}>"
