"""
GONETWORK AI - Modelos relacionados a patrocinadores e ativações
"""

import datetime
import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float, Enum
from sqlalchemy.orm import relationship

from . import Base

class SponsorTier(enum.Enum):
    """Níveis de patrocinadores"""
    platinum = "platinum"
    gold = "gold"
    silver = "silver"
    bronze = "bronze"

class ActivationStatus(enum.Enum):
    """Status possíveis de ativações"""
    pending = "pending"
    in_progress = "in_progress"
    filmed = "filmed"
    failed = "failed"
    approved = "approved"

class EvidenceFileType(enum.Enum):
    """Tipos de arquivos de evidência"""
    image = "image"
    video = "video"
    audio = "audio"
    document = "document"

class Sponsor(Base):
    """
    Modelo para patrocinadores de eventos
    """
    __tablename__ = "sponsors"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    contact_name = Column(String(100))
    contact_email = Column(String(100))
    contact_phone = Column(String(20))
    logo_path = Column(String(512))
    description = Column(Text)
    website = Column(String(255))
    tier = Column(Enum(SponsorTier), default=SponsorTier.silver)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relacionamentos
    activations = relationship("Activation", back_populates="sponsor", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Sponsor {self.name}>"


class ActivationType(Base):
    """
    Modelo para tipos de ativação de patrocinadores
    """
    __tablename__ = "activation_types"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon_path = Column(String(255))
    
    # Relacionamentos
    activations = relationship("Activation", back_populates="activation_type")
    
    def __repr__(self):
        return f"<ActivationType {self.name}>"


class Activation(Base):
    """
    Modelo para ativações de patrocinadores
    """
    __tablename__ = "activations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    sponsor_id = Column(Integer, ForeignKey("sponsors.id", ondelete="CASCADE"))
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    activation_type_id = Column(Integer, ForeignKey("activation_types.id"))
    status = Column(Enum(ActivationStatus), default=ActivationStatus.pending)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    location = Column(String(255))
    location_description = Column(Text)
    budget = Column(Float)
    completed_time = Column(DateTime, nullable=True)
    public_url = Column(String(512))  # URL compartilhável para cliente
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relacionamentos
    sponsor = relationship("Sponsor", back_populates="activations")
    event = relationship("Event", back_populates="activations")
    activity = relationship("Activity", back_populates="activations")
    activation_type = relationship("ActivationType", back_populates="activations")
    approved_by = relationship("User")
    evidence_items = relationship("ActivationEvidence", back_populates="activation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Activation {self.name} - {self.sponsor.name if self.sponsor else 'No sponsor'}>"


class ActivationEvidence(Base):
    """
    Modelo para evidências de ativações de patrocinadores
    """
    __tablename__ = "activation_evidences"
    
    id = Column(Integer, primary_key=True)
    activation_id = Column(Integer, ForeignKey("activations.id", ondelete="CASCADE"))
    file_path = Column(String(512), nullable=False)
    file_type = Column(Enum(EvidenceFileType))
    approved = Column(Boolean, default=False)
    notes = Column(Text)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relacionamentos
    activation = relationship("Activation", back_populates="evidence_items")
    uploaded_by = relationship("User")
    
    def __repr__(self):
        return f"<ActivationEvidence {self.id} for {self.activation_id}>"
