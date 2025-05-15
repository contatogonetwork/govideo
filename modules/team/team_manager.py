#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Gerenciamento de Equipe Audiovisual
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from core.database import TeamMember, TeamAssignment, Activity, User, Stage

logger = logging.getLogger(__name__)

class TeamManager:
    """Classe para gerenciar equipe de produção audiovisual"""
    
    def __init__(self, db_session):
        """Inicializa o gerenciador de equipe
        
        Args:
            db_session: Sessão do SQLAlchemy para acesso ao banco de dados
        """
        self.db = db_session
        
    def get_all_members(self):
        """Retorna todos os membros da equipe
        
        Returns:
            list: Lista de objetos TeamMember
        """
        try:
            return self.db.query(TeamMember).order_by(TeamMember.name).all()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar membros da equipe: {str(e)}")
            return []
            
    def get_member(self, member_id):
        """Retorna membro específico da equipe
        
        Args:
            member_id (int): ID do membro
            
        Returns:
            TeamMember: Objeto do membro ou None se não encontrado
        """
        try:
            return self.db.query(TeamMember).get(member_id)
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar membro id={member_id}: {str(e)}")
            return None
            
    def add_team_member(self, name, role, skills=None, contact_info=None, equipment=None, hourly_rate=None, user_id=None):
        """Adicionar novo membro à equipe
        
        Args:
            name (str): Nome completo do membro
            role (str): Função principal (camera, editor, etc)
            skills (str, opcional): Habilidades específicas
            contact_info (str, opcional): Informações de contato
            equipment (str, opcional): Equipamentos do membro
            hourly_rate (float, opcional): Taxa horária
            user_id (int, opcional): ID do usuário associado
            
        Returns:
            TeamMember: Objeto do novo membro criado
            
        Raises:
            ValueError: Se dados obrigatórios estiverem faltando
            SQLAlchemyError: Se houver erro no banco de dados
        """
        if not name or not role:
            raise ValueError("Nome e função são campos obrigatórios")
            
        try:
            member = TeamMember(
                name=name,
                role=role,
                skills=skills,
                contact_info=contact_info,
                equipment=equipment,
                hourly_rate=hourly_rate,
                user_id=user_id
            )
            
            self.db.add(member)
            self.db.commit()
            logger.info(f"Novo membro da equipe adicionado: {name} ({role})")
            return member
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao adicionar membro da equipe: {str(e)}")
            raise
            
    def update_team_member(self, member_id, name=None, role=None, skills=None, 
                          contact_info=None, equipment=None, hourly_rate=None):
        """Atualizar informações de membro da equipe
        
        Args:
            member_id (int): ID do membro
            name (str, opcional): Novo nome
            role (str, opcional): Nova função
            skills (str, opcional): Novas habilidades
            contact_info (str, opcional): Novas informações de contato
            equipment (str, opcional): Novos equipamentos
            hourly_rate (float, opcional): Nova taxa horária
            
        Returns:
            TeamMember: Objeto do membro atualizado
            
        Raises:
            ValueError: Se o membro não for encontrado
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            member = self.db.query(TeamMember).get(member_id)
            
            if not member:
                raise ValueError(f"Membro com ID {member_id} não encontrado")
                
            if name:
                member.name = name
            if role:
                member.role = role
            if skills is not None:
                member.skills = skills
            if contact_info is not None:
                member.contact_info = contact_info
            if equipment is not None:
                member.equipment = equipment
            if hourly_rate is not None:
                member.hourly_rate = hourly_rate
                
            self.db.commit()
            logger.info(f"Membro da equipe atualizado: {member.name} (ID: {member_id})")
            return member
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar membro da equipe: {str(e)}")
            raise
            
    def delete_team_member(self, member_id):
        """Excluir membro da equipe
        
        Args:
            member_id (int): ID do membro
            
        Returns:
            bool: True se excluído com sucesso
            
        Raises:
            ValueError: Se o membro não for encontrado
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            member = self.db.query(TeamMember).get(member_id)
            
            if not member:
                raise ValueError(f"Membro com ID {member_id} não encontrado")
                
            self.db.delete(member)
            self.db.commit()
            logger.info(f"Membro da equipe excluído: {member.name} (ID: {member_id})")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir membro da equipe: {str(e)}")
            raise
            
    def assign_to_activity(self, member_id, activity_id, role_details=None, equipment=None, 
                          start_time=None, end_time=None):
        """Atribuir membro à atividade específica
        
        Args:
            member_id (int): ID do membro
            activity_id (int): ID da atividade
            role_details (str, opcional): Detalhes específicos da função
            equipment (str, opcional): Equipamento para esta atividade
            start_time (datetime, opcional): Início específico (default: início da atividade)
            end_time (datetime, opcional): Fim específico (default: fim da atividade)
            
        Returns:
            TeamAssignment: Objeto da atribuição criada
            
        Raises:
            ValueError: Se o membro ou atividade não forem encontrados
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            member = self.db.query(TeamMember).get(member_id)
            activity = self.db.query(Activity).get(activity_id)
            
            if not member:
                raise ValueError(f"Membro com ID {member_id} não encontrado")
                
            if not activity:
                raise ValueError(f"Atividade com ID {activity_id} não encontrada")
                
            # Se horários não forem especificados, usar os da atividade
            assignment_start = start_time if start_time else activity.start_time
            assignment_end = end_time if end_time else activity.end_time
            
            # Verificar conflitos
            conflicts = self.check_member_conflicts(member_id, assignment_start, assignment_end)
            if conflicts:
                conflict_details = ", ".join([f"{c.activity.name} ({c.activity.start_time:%H:%M} - {c.activity.end_time:%H:%M})" for c in conflicts])
                raise ValueError(f"Conflito de horário com: {conflict_details}")
            
            assignment = TeamAssignment(
                member_id=member_id,
                activity_id=activity_id,
                role_details=role_details,
                equipment=equipment,
                start_time=assignment_start,
                end_time=assignment_end
            )
            
            self.db.add(assignment)
            self.db.commit()
            logger.info(f"Membro {member.name} atribuído à atividade {activity.name}")
            return assignment
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao atribuir membro à atividade: {str(e)}")
            raise
            
    def remove_from_activity(self, assignment_id):
        """Remover atribuição de membro a uma atividade
        
        Args:
            assignment_id (int): ID da atribuição
            
        Returns:
            bool: True se removido com sucesso
            
        Raises:
            ValueError: Se a atribuição não for encontrada
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            assignment = self.db.query(TeamAssignment).get(assignment_id)
            
            if not assignment:
                raise ValueError(f"Atribuição com ID {assignment_id} não encontrada")
                
            member_name = assignment.member.name
            activity_name = assignment.activity.name
            
            self.db.delete(assignment)
            self.db.commit()
            logger.info(f"Removida atribuição de {member_name} da atividade {activity_name}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao remover atribuição: {str(e)}")
            raise
            
    def get_schedule(self, event_id, member_id=None, role=None, date=None):
        """Obter agenda de trabalho filtrada
        
        Args:
            event_id (int): ID do evento
            member_id (int, opcional): Filtrar por membro específico
            role (str, opcional): Filtrar por função
            date (datetime.date, opcional): Filtrar por data específica
            
        Returns:
            list: Lista de atribuições filtradas
        """
        try:
            # Query base com joins necessários
            query = self.db.query(TeamAssignment) \
                .join(TeamAssignment.activity) \
                .join(Activity.stage) \
                .join(TeamAssignment.member) \
                .filter(Stage.event_id == event_id)
            
            # Aplicar filtros opcionais
            if member_id:
                query = query.filter(TeamAssignment.member_id == member_id)
                
            if role:
                query = query.filter(TeamMember.role == role)
                
            if date:
                # Filtrar por data específica
                start_of_day = datetime.combine(date, datetime.min.time())
                end_of_day = datetime.combine(date, datetime.max.time())
                query = query.filter(Activity.start_time >= start_of_day,
                                   Activity.start_time <= end_of_day)
                
            # Eager loading para reduzir queries
            query = query.options(
                joinedload(TeamAssignment.member),
                joinedload(TeamAssignment.activity).joinedload(Activity.stage)
            )
            
            # Ordenar por horário de início
            return query.order_by(Activity.start_time).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao obter agenda: {str(e)}")
            return []
            
    def check_member_conflicts(self, member_id, start_time, end_time, exclude_assignment_id=None):
        """Verificar conflitos de horário para um membro
        
        Args:
            member_id (int): ID do membro
            start_time (datetime): Horário de início a verificar
            end_time (datetime): Horário de fim a verificar
            exclude_assignment_id (int, opcional): ID de atribuição a ignorar na verificação
            
        Returns:
            list: Lista de atribuições conflitantes
        """
        try:
            query = self.db.query(TeamAssignment) \
                .join(TeamAssignment.activity) \
                .filter(
                    TeamAssignment.member_id == member_id,
                    # Sobreposição de horários
                    # (start_time <= existing.end_time) AND (end_time >= existing.start_time)
                    start_time < TeamAssignment.end_time,
                    end_time > TeamAssignment.start_time
                )
                
            if exclude_assignment_id:
                query = query.filter(TeamAssignment.id != exclude_assignment_id)
                
            # Eager loading
            query = query.options(joinedload(TeamAssignment.activity))
            
            return query.all()
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao verificar conflitos: {str(e)}")
            return []
            
    def check_conflicts(self, event_id):
        """Verificar conflitos de agenda na equipe para um evento
        
        Args:
            event_id (int): ID do evento
            
        Returns:
            dict: Dicionário com conflitos por membro
        """
        conflicts = {}
        
        try:
            # Obter todas as atribuições para o evento
            assignments = self.get_schedule(event_id)
            
            # Agrupar por membro
            member_assignments = {}
            for assignment in assignments:
                member_id = assignment.member_id
                if member_id not in member_assignments:
                    member_assignments[member_id] = []
                member_assignments[member_id].append(assignment)
                
            # Verificar conflitos para cada membro
            for member_id, assignments in member_assignments.items():
                member_conflicts = []
                
                # Comparar cada par de atribuições
                for i, a1 in enumerate(assignments):
                    for a2 in assignments[i+1:]:
                        # Verificar sobreposição
                        if a1.start_time < a2.end_time and a1.end_time > a2.start_time:
                            member_conflicts.append((a1, a2))
                
                if member_conflicts:
                    member = self.get_member(member_id)
                    conflicts[member.name] = member_conflicts
            
            return conflicts
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao verificar conflitos no evento: {str(e)}")
            return {}
            
    def get_members_by_role(self, role):
        """Retorna membros da equipe por função
        
        Args:
            role (str): Função a filtrar
            
        Returns:
            list: Lista de objetos TeamMember
        """
        try:
            return self.db.query(TeamMember).filter(TeamMember.role == role).all()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar membros por função {role}: {str(e)}")
            return []
            
    def get_members_available(self, event_id, start_time, end_time, role=None):
        """Retorna membros disponíveis em um horário específico
        
        Args:
            event_id (int): ID do evento
            start_time (datetime): Horário de início
            end_time (datetime): Horário de fim
            role (str, opcional): Filtrar por função
            
        Returns:
            list: Lista de objetos TeamMember disponíveis
        """
        try:
            # Obter todos os membros (com filtro de função opcional)
            query = self.db.query(TeamMember)
            if role:
                query = query.filter(TeamMember.role == role)
            all_members = query.all()
            
            # Lista para membros ocupados no período
            busy_member_ids = set()
            
            # Obter atribuições que se sobrepõem ao período solicitado
            busy_assignments = self.db.query(TeamAssignment) \
                .join(TeamAssignment.activity) \
                .join(Activity.stage) \
                .filter(
                    Stage.event_id == event_id,
                    TeamAssignment.start_time < end_time,
                    TeamAssignment.end_time > start_time
                ).all()
            
            # Adicionar os IDs dos membros ocupados
            for assignment in busy_assignments:
                busy_member_ids.add(assignment.member_id)
            
            # Retornar apenas membros que não estão na lista de ocupados
            return [member for member in all_members if member.id not in busy_member_ids]
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar membros disponíveis: {str(e)}")
            return []
            
    def get_roles(self):
        """Retorna lista de funções existentes na equipe
        
        Returns:
            list: Lista de funções únicas
        """
        try:
            roles = self.db.query(TeamMember.role).distinct().all()
            return [role[0] for role in roles]
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar funções: {str(e)}")
            return []