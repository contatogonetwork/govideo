"""
GONETWORK AI - Modelos relacionados à equipe
"""

import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Enum
from sqlalchemy.orm import relationship

from . import Base

class TeamMember(Base):
    """
    Modelo para membros da equipe
    """
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    skills = Column(Text)
    contact_info = Column(String(200))
    equipment = Column(Text)
    hourly_rate = Column(Float)

    # Relacionamentos
    user = relationship("User", back_populates="team_memberships")
    assignments = relationship("TeamAssignment", back_populates="member", cascade="all, delete-orphan")
    deliveries = relationship("Delivery", back_populates="responsible")

    def __repr__(self):
        return f"<TeamMember {self.name} ({self.role})>"
    
    @classmethod
    def get_by_role(cls, session, role):
        """
        Obtém membros da equipe por função
        
        Args:
            session: Sessão do SQLAlchemy
            role (str): Função/cargo
            
        Returns:
            list: Lista de objetos TeamMember
        """
        return session.query(cls).filter(cls.role == role).all()


class TeamAssignment(Base):
    """
    Modelo para alocações de membros da equipe
    """
    __tablename__ = "team_assignments"
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("team_members.id", ondelete="CASCADE"))
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"))
    equipment = Column(Text)
    role_details = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String(200))
    status = Column(String(20), default="ativo")

    # Relacionamentos
    member = relationship("TeamMember", back_populates="assignments")
    activity = relationship("Activity", back_populates="team_assignments")

    def __repr__(self):
        return f"<TeamAssignment {self.member_id} to {self.activity_id}>"
    
    @classmethod
    def get_active_assignments(cls, session, member_id=None, start_date=None):
        """
        Obtém alocações ativas da equipe
        
        Args:
            session: Sessão do SQLAlchemy
            member_id (int, optional): ID do membro da equipe
            start_date (datetime, optional): Data inicial
            
        Returns:
            list: Lista de objetos TeamAssignment
        """
        query = session.query(cls).filter(cls.status != "finalizado")
        
        if member_id:
            query = query.filter(cls.member_id == member_id)
        
        if start_date:
            query = query.filter(cls.start_time >= start_date)
            
        return query.order_by(cls.start_time).all()
    
    def check_conflict(self, session):
        """
        Verifica se há conflitos com outras alocações
        
        Args:
            session: Sessão do SQLAlchemy
            
        Returns:
            list: Lista de objetos TeamAssignment com conflito
        """
        query = session.query(TeamAssignment).filter(
            TeamAssignment.member_id == self.member_id,
            TeamAssignment.id != self.id,
            TeamAssignment.status != "finalizado"
        )
        
        # Verificar sobreposição de horários
        query = query.filter(
            # Caso 1: Início está dentro de outra alocação
            ((self.start_time >= TeamAssignment.start_time) & 
             (self.start_time <= TeamAssignment.end_time)) |
            # Caso 2: Fim está dentro de outra alocação
            ((self.end_time >= TeamAssignment.start_time) & 
             (self.end_time <= TeamAssignment.end_time)) |
            # Caso 3: Abrange completamente outra alocação
            ((self.start_time <= TeamAssignment.start_time) & 
             (self.end_time >= TeamAssignment.end_time))
        )
            
        return query.all()
