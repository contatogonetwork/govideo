"""
GONETWORK AI - Modelo de usuário
"""

import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from . import Base

class User(Base):
    """
    Modelo de usuário do sistema
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(20), nullable=False)  # admin, manager, editor, viewer
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    profile_picture = Column(String(255))

    # Relacionamentos
    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    created_deliveries = relationship("Delivery", foreign_keys="[Delivery.created_by]", back_populates="creator")
    comments = relationship("DeliveryComment", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"
    
    @classmethod
    def get_by_username(cls, session, username):
        """
        Obtém um usuário pelo nome de usuário
        
        Args:
            session: Sessão do SQLAlchemy
            username (str): Nome de usuário
            
        Returns:
            User: Objeto de usuário ou None
        """
        return session.query(cls).filter(cls.username == username).first()
    
    @classmethod
    def get_active_users(cls, session):
        """
        Obtém todos os usuários ativos
        
        Args:
            session: Sessão do SQLAlchemy
            
        Returns:
            list: Lista de objetos User
        """
        return session.query(cls).filter(cls.is_active == True).all()
    
    def check_password(self, password):
        """
        Verifica se a senha está correta
        
        Args:
            password (str): Senha em texto plano
            
        Returns:
            bool: True se a senha estiver correta
        """
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """
        Define a senha do usuário
        
        Args:
            password (str): Senha em texto plano
        """
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
