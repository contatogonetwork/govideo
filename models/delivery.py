"""
GONETWORK AI - Modelos relacionados a entregas
"""

import datetime
import os
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship

from . import Base

class Delivery(Base):
    """
    Modelo para entregas de conteúdo
    """
    __tablename__ = "deliveries"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    deadline = Column(DateTime, nullable=False)
    format_specs = Column(Text)
    responsible_id = Column(Integer, ForeignKey("team_members.id"))
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="SET NULL"), nullable=True)
    priority = Column(Integer, default=3)  # 1=Baixa, 2=Média, 3=Alta, 4=Urgente
    status = Column(String(20), default="pending")  # pending, in_progress, review, approved, published, rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    published_at = Column(DateTime)
    progress = Column(Float, default=0.0)  # 0.0 a 1.0 (0% a 100%)

    # Relacionamentos
    files = relationship("DeliveryFile", back_populates="delivery", cascade="all, delete-orphan")
    comments = relationship("DeliveryComment", back_populates="delivery", cascade="all, delete-orphan")
    responsible = relationship("TeamMember", back_populates="deliveries")
    event = relationship("Event", back_populates="deliveries")
    activity = relationship("Activity", back_populates="deliveries")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_deliveries")

    def __repr__(self):
        return f"<Delivery {self.title}>"
    
    @property
    def is_overdue(self):
        """
        Verifica se a entrega está atrasada
        
        Returns:
            bool: True se atrasada
        """
        return self.deadline < datetime.datetime.now() and self.status not in ["approved", "published"]
    
    @property
    def days_remaining(self):
        """
        Calcula dias restantes até o prazo
        
        Returns:
            float: Número de dias (negativo se atrasado)
        """
        delta = self.deadline - datetime.datetime.now()
        return delta.total_seconds() / (24 * 60 * 60)
    
    @classmethod
    def get_pending_approvals(cls, session):
        """
        Obtém entregas pendentes de aprovação
        
        Args:
            session: Sessão do SQLAlchemy
            
        Returns:
            list: Lista de objetos Delivery
        """
        return session.query(cls).filter(cls.status == "review").order_by(cls.deadline).all()


class DeliveryFile(Base):
    """
    Modelo para arquivos de entrega
    """
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
    thumbnail_path = Column(String(512))

    # Relacionamentos
    delivery = relationship("Delivery", back_populates="files")
    uploader = relationship("User")

    def __repr__(self):
        return f"<DeliveryFile {self.filename} v{self.version}>"
    
    @property
    def extension(self):
        """
        Obtém a extensão do arquivo
        
        Returns:
            str: Extensão do arquivo
        """
        _, ext = os.path.splitext(self.filename)
        return ext.lower()[1:] if ext else ""
    
    @property
    def is_video(self):
        """
        Verifica se é um arquivo de vídeo
        
        Returns:
            bool: True se for vídeo
        """
        video_exts = ["mp4", "mov", "avi", "mkv", "wmv"]
        return self.extension in video_exts
    
    @property
    def is_image(self):
        """
        Verifica se é uma imagem
        
        Returns:
            bool: True se for imagem
        """
        image_exts = ["jpg", "jpeg", "png", "gif", "bmp"]
        return self.extension in image_exts
    
    @property
    def is_audio(self):
        """
        Verifica se é um arquivo de áudio
        
        Returns:
            bool: True se for áudio
        """
        audio_exts = ["mp3", "wav", "ogg", "flac", "aac"]
        return self.extension in audio_exts


class DeliveryComment(Base):
    """
    Modelo para comentários em entregas
    """
    __tablename__ = "delivery_comments"
    
    id = Column(Integer, primary_key=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    comment = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    timecode = Column(String(12), nullable=True)  # Para comentários associados a pontos específicos do vídeo
    is_system = Column(Boolean, default=False)  # Para comentários gerados automaticamente pelo sistema

    # Relacionamentos
    delivery = relationship("Delivery", back_populates="comments")
    user = relationship("User", back_populates="comments")

    def __repr__(self):
        return f"<DeliveryComment by {self.user_id} on {self.timestamp}>"
