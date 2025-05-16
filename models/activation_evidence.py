#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Modelo de Evidências de Ativações
Data: 2025-05-15
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
import os
import datetime

from models.base import Base
from models.sponsor import SponsorActivation

class ActivationEvidence(Base):
    """Modelo para evidências de ativações patrocinadas"""
    
    __tablename__ = "activation_evidences"
    
    id = Column(Integer, primary_key=True)
    activation_id = Column(Integer, ForeignKey("sponsor_activations.id"), nullable=False)
    file_path = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type_id = Column(Integer, default=1)  # 1=foto, 2=vídeo, 3=documento
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relacionamentos
    activation = relationship("SponsorActivation", back_populates="evidences")
    user = relationship("User", foreign_keys=[user_id])
    approver = relationship("User", foreign_keys=[approved_by])
    
    @property
    def file_type(self):
        """Retorna o tipo de arquivo com base na extensão"""
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return "image"
        elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv']:
            return "video"
        elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
            return "document"
        else:
            return "other"
            
    @property
    def file_name(self):
        """Retorna o nome do arquivo"""
        return os.path.basename(self.file_path)
        
    @property
    def type_name(self):
        """Retorna o nome do tipo de evidência"""
        types = {
            1: "Foto",
            2: "Vídeo",
            3: "Documento"
        }
        return types.get(self.type_id, "Outro")
        
    def approve(self, user_id):
        """Aprova a evidência"""
        self.approved = True
        self.approved_by = user_id
        self.approved_at = datetime.datetime.utcnow()
        
    def reject(self):
        """Rejeita a evidência"""
        self.approved = False
        self.approved_by = None
        self.approved_at = None
        
    def __repr__(self):
        return f"<ActivationEvidence(id={self.id}, activation_id={self.activation_id}, file={self.file_name})>"


# Adicionar relacionamento ao modelo SponsorActivation
SponsorActivation.evidences = relationship("ActivationEvidence", 
                                         back_populates="activation",
                                         cascade="all, delete-orphan")
