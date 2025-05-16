"""
GONETWORK AI - Controlador de Equipe
Implementa a lógica de negócio para gerenciamento de equipe e atribuições
"""

from PyQt5.QtCore import QObject, pyqtSignal
import datetime
from sqlalchemy import or_, and_

from controllers import BaseController
from models.team import TeamMember, TeamAssignment
from models.event import Event, Activity
from core.logging_manager import get_logger

logger = get_logger(__name__)

class TeamController(BaseController):
    """
    Controlador para gerenciamento de equipe e atribuições
    """
    
    # Sinais
    team_updated = pyqtSignal(list)  # Lista de membros da equipe atualizada
    assignments_updated = pyqtSignal(list)  # Lista de atribuições atualizada
    assignment_conflict = pyqtSignal(object, list)  # Atribuição atual e lista de conflitos
    
    def __init__(self, db_session):
        """
        Inicializa o controlador de equipe
        
        Args:
            db_session: Sessão do SQLAlchemy para acesso ao banco de dados
        """
        super().__init__(db_session)
        self.current_event_id = None
        self.current_filters = {}
    
    def set_current_event(self, event_id):
        """
        Define o evento atual
        
        Args:
            event_id (int): ID do evento
        """
        self.current_event_id = event_id
        logger.info(f"Evento atual definido para equipe: {event_id}")
        self.reload_assignments()
    
    def get_team_members(self, filters=None):
        """
        Obtém todos os membros da equipe com filtros opcionais
        
        Args:
            filters (dict, optional): Filtros a serem aplicados
            
        Returns:
            list: Lista de objetos TeamMember
        """
        filters = filters or {}
        
        # Construir query base
        query = self.db.query(TeamMember)
        
        # Aplicar filtros
        if filters.get('role'):
            if isinstance(filters['role'], list):
                query = query.filter(TeamMember.role.in_(filters['role']))
            else:
                query = query.filter(TeamMember.role == filters['role'])
                
        if filters.get('search_text'):
            search = f"%{filters['search_text']}%"
            query = query.filter(
                or_(
                    TeamMember.name.like(search),
                    TeamMember.skills.like(search),
                    TeamMember.contact_info.like(search)
                )
            )
        
        # Ordenar por nome
        query = query.order_by(TeamMember.name)
        
        return query.all()
    
    def reload_assignments(self):
        """
        Recarrega as atribuições de equipe com base no evento atual e filtros
        """
        if not self.current_event_id:
            logger.warning("Tentativa de carregar atribuições sem evento definido")
            return
            
        try:
            assignments = self.load_assignments(self.current_event_id, self.current_filters)
            self.assignments_updated.emit(assignments)
            logger.debug(f"Atribuições atualizadas: {len(assignments)} carregadas")
        except Exception as e:
            logger.error(f"Erro ao carregar atribuições: {str(e)}", exc_info=True)
    
    def load_assignments(self, event_id, filters=None):
        """
        Carrega atribuições de equipe com filtros aplicados
        
        Args:
            event_id (int): ID do evento
            filters (dict): Filtros a serem aplicados
            
        Returns:
            list: Lista de objetos TeamAssignment
        """
        filters = filters or {}
        
        # Construir query base - subquery para encontrar atividades do evento
        activities_subquery = self.db.query(Activity.id).join(Stage).filter(Stage.event_id == event_id)
        query = self.db.query(TeamAssignment).filter(TeamAssignment.activity_id.in_(activities_subquery))
        
        # Aplicar filtros
        if filters.get('member_id'):
            if isinstance(filters['member_id'], list):
                query = query.filter(TeamAssignment.member_id.in_(filters['member_id']))
            else:
                query = query.filter(TeamAssignment.member_id == filters['member_id'])
        
        if filters.get('start_date'):
            query = query.filter(TeamAssignment.end_time >= filters['start_date'])
            
        if filters.get('end_date'):
            query = query.filter(TeamAssignment.start_time <= filters['end_date'])
            
        if filters.get('status'):
            query = query.filter(TeamAssignment.status.in_(filters['status']))
            
        # Ordenar por membro e data de início
        query = query.order_by(TeamAssignment.member_id, TeamAssignment.start_time)
        
        return query.all()
    
    def get_team_member_by_id(self, member_id):
        """
        Obtém um membro da equipe pelo ID
        
        Args:
            member_id (int): ID do membro da equipe
            
        Returns:
            TeamMember: Objeto de membro da equipe ou None
        """
        return self.db.query(TeamMember).get(member_id)
    
    def create_team_member(self, name, role, skills=None, contact_info=None, 
                         equipment=None, hourly_rate=None):
        """
        Cria um novo membro da equipe
        
        Args:
            name (str): Nome do membro
            role (str): Função/cargo
            skills (str, optional): Habilidades
            contact_info (str, optional): Informações de contato
            equipment (str, optional): Equipamento
            hourly_rate (float, optional): Taxa horária
            
        Returns:
            TeamMember: Objeto de membro da equipe criado
        """
        try:
            team_member = TeamMember(
                name=name,
                role=role,
                skills=skills,
                contact_info=contact_info,
                equipment=equipment,
                hourly_rate=hourly_rate
            )
            
            self.db.add(team_member)
            self.db.commit()
            
            logger.info(f"Membro de equipe criado: {team_member.id} - {team_member.name}")
            self.team_updated.emit(self.get_team_members())
            return team_member
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao criar membro de equipe: {str(e)}", exc_info=True)
            raise
    
    def update_team_member(self, member_id, **kwargs):
        """
        Atualiza um membro da equipe existente
        
        Args:
            member_id (int): ID do membro da equipe
            **kwargs: Pares de chave-valor com os atributos a serem atualizados
            
        Returns:
            TeamMember: Objeto de membro da equipe atualizado
        """
        try:
            team_member = self.db.query(TeamMember).get(member_id)
            
            if not team_member:
                logger.warning(f"Tentativa de atualizar membro de equipe inexistente: {member_id}")
                return None
                
            # Atualizar os atributos fornecidos
            for key, value in kwargs.items():
                if hasattr(team_member, key):
                    setattr(team_member, key, value)
            
            self.db.commit()
            
            logger.info(f"Membro de equipe atualizado: {team_member.id} - {team_member.name}")
            self.team_updated.emit(self.get_team_members())
            return team_member
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar membro de equipe: {str(e)}", exc_info=True)
            raise
    
    def delete_team_member(self, member_id):
        """
        Remove um membro da equipe
        
        Args:
            member_id (int): ID do membro da equipe
            
        Returns:
            bool: True se a exclusão for bem-sucedida
        """
        try:
            team_member = self.db.query(TeamMember).get(member_id)
            
            if not team_member:
                logger.warning(f"Tentativa de excluir membro de equipe inexistente: {member_id}")
                return False
                
            self.db.delete(team_member)
            self.db.commit()
            
            logger.info(f"Membro de equipe excluído: {member_id}")
            self.team_updated.emit(self.get_team_members())
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir membro de equipe: {str(e)}", exc_info=True)
            raise
    
    def create_assignment(self, member_id, activity_id, role_details=None, 
                        equipment=None, start_time=None, end_time=None, 
                        location=None):
        """
        Cria uma nova atribuição de equipe
        
        Args:
            member_id (int): ID do membro da equipe
            activity_id (int): ID da atividade
            role_details (str, optional): Detalhes da função
            equipment (str, optional): Equipamento
            start_time (datetime, optional): Hora de início (usa o da atividade se None)
            end_time (datetime, optional): Hora de término (usa o da atividade se None)
            location (str, optional): Localização
            
        Returns:
            TeamAssignment: Objeto de atribuição criado ou None se houver conflito
        """
        try:
            # Se start_time ou end_time não foram fornecidos, usar os da atividade
            if start_time is None or end_time is None:
                activity = self.db.query(Activity).get(activity_id)
                if not activity:
                    logger.warning(f"Tentativa de criar atribuição para atividade inexistente: {activity_id}")
                    return None
                    
                start_time = start_time or activity.start_time
                end_time = end_time or activity.end_time
            
            # Criar objeto de atribuição
            assignment = TeamAssignment(
                member_id=member_id,
                activity_id=activity_id,
                role_details=role_details,
                equipment=equipment,
                start_time=start_time,
                end_time=end_time,
                location=location,
                status="ativo"
            )
            
            # Verificar conflitos
            conflicts = self.check_assignment_conflicts(assignment)
            if conflicts:
                logger.warning(f"Conflito detectado ao criar atribuição: {len(conflicts)} conflitos")
                self.assignment_conflict.emit(assignment, conflicts)
                return None
            
            self.db.add(assignment)
            self.db.commit()
            
            logger.info(f"Atribuição criada: {assignment.id}")
            self.reload_assignments()
            return assignment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao criar atribuição: {str(e)}", exc_info=True)
            raise
    
    def update_assignment(self, assignment_id, **kwargs):
        """
        Atualiza uma atribuição existente
        
        Args:
            assignment_id (int): ID da atribuição
            **kwargs: Pares de chave-valor com os atributos a serem atualizados
            
        Returns:
            TeamAssignment: Objeto de atribuição atualizado ou None se houver conflito
        """
        try:
            assignment = self.db.query(TeamAssignment).get(assignment_id)
            
            if not assignment:
                logger.warning(f"Tentativa de atualizar atribuição inexistente: {assignment_id}")
                return None
                
            # Fazer uma cópia da atribuição para verificar conflitos
            modified_assignment = TeamAssignment(
                id=assignment.id,
                member_id=assignment.member_id,
                activity_id=assignment.activity_id,
                role_details=assignment.role_details,
                equipment=assignment.equipment,
                start_time=assignment.start_time,
                end_time=assignment.end_time,
                location=assignment.location,
                status=assignment.status
            )
            
            # Atualizar os atributos fornecidos na cópia
            for key, value in kwargs.items():
                if hasattr(modified_assignment, key):
                    setattr(modified_assignment, key, value)
            
            # Verificar conflitos
            conflicts = self.check_assignment_conflicts(modified_assignment)
            if conflicts:
                logger.warning(f"Conflito detectado ao atualizar atribuição: {len(conflicts)} conflitos")
                self.assignment_conflict.emit(modified_assignment, conflicts)
                return None
            
            # Aplicar as alterações à atribuição real
            for key, value in kwargs.items():
                if hasattr(assignment, key):
                    setattr(assignment, key, value)
            
            self.db.commit()
            
            logger.info(f"Atribuição atualizada: {assignment.id}")
            self.reload_assignments()
            return assignment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar atribuição: {str(e)}", exc_info=True)
            raise
    
    def delete_assignment(self, assignment_id):
        """
        Remove uma atribuição
        
        Args:
            assignment_id (int): ID da atribuição
            
        Returns:
            bool: True se a exclusão for bem-sucedida
        """
        try:
            assignment = self.db.query(TeamAssignment).get(assignment_id)
            
            if not assignment:
                logger.warning(f"Tentativa de excluir atribuição inexistente: {assignment_id}")
                return False
                
            self.db.delete(assignment)
            self.db.commit()
            
            logger.info(f"Atribuição excluída: {assignment_id}")
            self.reload_assignments()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir atribuição: {str(e)}", exc_info=True)
            raise
    
    def check_assignment_conflicts(self, assignment):
        """
        Verifica se há conflitos com a atribuição
        
        Args:
            assignment (TeamAssignment): Objeto de atribuição
            
        Returns:
            list: Lista de objetos TeamAssignment com conflito
        """
        query = self.db.query(TeamAssignment).filter(
            TeamAssignment.member_id == assignment.member_id,
            TeamAssignment.id != assignment.id,
            TeamAssignment.status != "finalizado"
        )
        
        # Verificar sobreposição de horários
        query = query.filter(
            # Caso 1: Início está dentro de outra atribuição
            ((assignment.start_time >= TeamAssignment.start_time) & 
             (assignment.start_time <= TeamAssignment.end_time)) |
            # Caso 2: Fim está dentro de outra atribuição
            ((assignment.end_time >= TeamAssignment.start_time) & 
             (assignment.end_time <= TeamAssignment.end_time)) |
            # Caso 3: Abrange completamente outra atribuição
            ((assignment.start_time <= TeamAssignment.start_time) & 
             (assignment.end_time >= TeamAssignment.end_time))
        )
            
        return query.all()
    
    def get_team_schedule(self, start_date, end_date, member_ids=None):
        """
        Obtém agenda da equipe para um período
        
        Args:
            start_date (datetime): Data de início
            end_date (datetime): Data de término
            member_ids (list, optional): Lista de IDs de membros da equipe
            
        Returns:
            dict: Dicionário de atribuições por membro
        """
        # Construir filtros
        filters = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        if member_ids:
            filters['member_id'] = member_ids
            
        # Obter atribuições
        assignments = self.load_assignments(self.current_event_id, filters)
        
        # Organizar por membro
        schedule = {}
        for assignment in assignments:
            if assignment.member_id not in schedule:
                schedule[assignment.member_id] = []
            schedule[assignment.member_id].append(assignment)
            
        return schedule
