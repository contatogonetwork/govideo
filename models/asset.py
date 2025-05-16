"""
GONETWORK AI - Modelos relacionados a assets (arquivos de mídia)
"""

import datetime
import os
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship

from . import Base
from .base import asset_tags

class Asset(Base):
    """
    Modelo para assets (arquivos de mídia)
    """
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    file_path = Column(String(512), nullable=False)
    asset_type = Column(String(50), nullable=False)  # video, audio, image, document
    description = Column(Text)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    folder_id = Column(Integer, ForeignKey("asset_folders.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    file_size = Column(Integer)
    duration = Column(Integer, nullable=True)
    technical_metadata = Column(Text)  # JSON com metadados técnicos
    thumbnail_path = Column(String(512))

    # Relacionamentos
    event = relationship("Event", back_populates="assets")
    folder = relationship("AssetFolder", back_populates="assets")
    creator = relationship("User")
    tags = relationship("Tag", secondary=asset_tags, back_populates="assets")

    def __repr__(self):
        return f"<Asset {self.name}>"
    
    @property
    def extension(self):
        """
        Obtém a extensão do arquivo
        
        Returns:
            str: Extensão do arquivo
        """
        _, ext = os.path.splitext(self.file_path)
        return ext.lower()[1:] if ext else ""
    
    @property
    def filename(self):
        """
        Obtém o nome do arquivo sem o caminho
        
        Returns:
            str: Nome do arquivo
        """
        return os.path.basename(self.file_path)
    
    @classmethod
    def search_by_tag(cls, session, tag_name):
        """
        Busca assets por tag
        
        Args:
            session: Sessão do SQLAlchemy
            tag_name (str): Nome da tag
            
        Returns:
            list: Lista de objetos Asset
        """
        from .event import Tag
        return session.query(cls).join(asset_tags).join(Tag).filter(Tag.name == tag_name).all()


class AssetFolder(Base):
    """
    Modelo para pastas de organização de assets
    """
    __tablename__ = "asset_folders"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("asset_folders.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relacionamentos
    subfolders = relationship(
        "AssetFolder",
        back_populates="parent",
        remote_side=[id],
        cascade="all, delete-orphan",
        single_parent=True
    )
    parent = relationship(
        "AssetFolder", 
        back_populates="subfolders", 
        remote_side=[parent_id]
    )
    assets = relationship("Asset", back_populates="folder")
    creator = relationship("User")

    def __repr__(self):
        return f"<AssetFolder {self.name}>"
    
    @property
    def full_path(self):
        """
        Obtém o caminho completo da pasta (hierarquia)
        
        Returns:
            str: Caminho completo separado por '/'
        """
        if not self.parent:
            return self.name
        
        return f"{self.parent.full_path}/{self.name}"
    
    @classmethod
    def get_root_folders(cls, session):
        """
        Obtém todas as pastas raiz
        
        Args:
            session: Sessão do SQLAlchemy
            
        Returns:
            list: Lista de objetos AssetFolder
        """
        return session.query(cls).filter(cls.parent_id == None).all()
