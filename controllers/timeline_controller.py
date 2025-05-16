"""
GONETWORK AI - Controlador de Cronograma
Implementa a lógica de negócio para visualização e gerenciamento de cronogramas
"""

from PyQt5.QtCore import QObject, pyqtSignal, QDate
import datetime
from sqlalchemy import or_, and_

from controllers import BaseController
from models.event import Event, Activity, Stage
from core.logging_manager import get_logger

logger = get_logger(__name__)

class TimelineController(BaseController):
    """
    Controlador para gerenciamento de timeline e cronograma de eventos
    """
    
    # Sinais
    timeline_updated = pyqtSignal(list)  # Lista de atividades atualizadas
    filter_applied = pyqtSignal(dict)    # Filtros aplicados
    
    def __init__(self, db_session):
        """
        Inicializa o controlador de timeline.
        
        Args:
            db_session: Sessão do SQLAlchemy para acesso ao banco de dados
        """
        super().__init__(db_session)
        self.current_event_id = None
        self.current_filters = {}
    
    def set_current_event(self, event_id):
        """
        Define o evento atual para o cronograma
        
        Args:
            event_id (int): ID do evento
        """
        self.current_event_id = event_id
        logger.info(f"Evento atual definido: {event_id}")
        self.reload_timeline()
        
    def reload_timeline(self):
        """
        Recarrega as atividades do cronograma com base no evento atual e filtros
        """
        if not self.current_event_id:
            logger.warning("Tentativa de carregar timeline sem evento definido")
            return
        
        try:
            activities = self.load_activities(self.current_event_id, self.current_filters)
            self.timeline_updated.emit(activities)
            logger.debug(f"Timeline atualizada: {len(activities)} atividades carregadas")
        except Exception as e:
            logger.error(f"Erro ao carregar timeline: {str(e)}", exc_info=True)
            
    def load_activities(self, event_id, filters=None):
        """
        Carrega atividades com filtros aplicados
        
        Args:
            event_id (int): ID do evento
            filters (dict): Filtros a serem aplicados
            
        Returns:
            list: Lista de objetos Activity
        """
        filters = filters or {}
        
        # Construir query base
        query = self.db.query(Activity)
        query = query.join(Stage).filter(Stage.event_id == event_id)
        
        # Aplicar filtros
        if filters.get('stage_ids'):
            query = query.filter(Activity.stage_id.in_(filters['stage_ids']))
            
        if filters.get('start_date'):
            query = query.filter(Activity.start_time >= filters['start_date'])
            
        if filters.get('end_date'):
            query = query.filter(Activity.end_time <= filters['end_date'])
            
        if filters.get('status'):
            query = query.filter(Activity.status.in_(filters['status']))
            
        if filters.get('priority'):
            query = query.filter(Activity.priority.in_(filters['priority']))
            
        if filters.get('search_text'):
            search = f"%{filters['search_text']}%"
            query = query.filter(
                or_(
                    Activity.name.like(search),
                    Activity.details.like(search)
                )
            )
        
        # Ordenar por data/hora de início
        query = query.order_by(Activity.start_time)
        
        return query.all()
    
    def apply_filters(self, filters):
        """
        Aplica filtros ao cronograma
        
        Args:
            filters (dict): Filtros a serem aplicados
        """
        self.current_filters = filters
        self.filter_applied.emit(filters)
        self.reload_timeline()
    
    def get_stages_for_event(self, event_id=None):
        """
        Obtém lista de palcos para o evento atual ou específico
        
        Args:
            event_id (int, optional): ID do evento ou None para usar o evento atual
            
        Returns:
            list: Lista de objetos Stage
        """
        if event_id is None:
            event_id = self.current_event_id
            
        if not event_id:
            return []
            
        return self.db.query(Stage).filter(Stage.event_id == event_id).all()
    
    def create_activity(self, stage_id, name, start_time, end_time, details=None, 
                      status="pending", priority=3, activity_type=None):
        """
        Cria uma nova atividade
        
        Args:
            stage_id (int): ID do palco
            name (str): Nome da atividade
            start_time (datetime): Data/hora de início
            end_time (datetime): Data/hora de término
            details (str, optional): Detalhes da atividade
            status (str, optional): Status da atividade
            priority (int, optional): Prioridade (1-5)
            activity_type (str, optional): Tipo de atividade
            
        Returns:
            Activity: Objeto de atividade criado
        """
        try:
            activity = Activity(
                stage_id=stage_id,
                name=name,
                start_time=start_time,
                end_time=end_time,
                details=details,
                status=status,
                priority=priority,
                type=activity_type
            )
            
            self.db.add(activity)
            self.db.commit()
            
            logger.info(f"Atividade criada: {activity.id} - {activity.name}")
            self.reload_timeline()
            return activity
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao criar atividade: {str(e)}", exc_info=True)
            raise
    
    def update_activity(self, activity_id, **kwargs):
        """
        Atualiza uma atividade existente
        
        Args:
            activity_id (int): ID da atividade
            **kwargs: Pares de chave-valor com os atributos a serem atualizados
            
        Returns:
            Activity: Objeto de atividade atualizado
        """
        try:
            activity = self.db.query(Activity).get(activity_id)
            
            if not activity:
                logger.warning(f"Tentativa de atualizar atividade inexistente: {activity_id}")
                return None
                
            # Atualizar os atributos fornecidos
            for key, value in kwargs.items():
                if hasattr(activity, key):
                    setattr(activity, key, value)
            
            self.db.commit()
            
            logger.info(f"Atividade atualizada: {activity.id} - {activity.name}")
            self.reload_timeline()
            return activity
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar atividade: {str(e)}", exc_info=True)
            raise
    
    def delete_activity(self, activity_id):
        """
        Remove uma atividade
        
        Args:
            activity_id (int): ID da atividade
            
        Returns:
            bool: True se a exclusão for bem-sucedida
        """
        try:
            activity = self.db.query(Activity).get(activity_id)
            
            if not activity:
                logger.warning(f"Tentativa de excluir atividade inexistente: {activity_id}")
                return False
                
            self.db.delete(activity)
            self.db.commit()
            
            logger.info(f"Atividade excluída: {activity_id}")
            self.reload_timeline()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir atividade: {str(e)}", exc_info=True)
            raise

    def update_filtered_activities(self, filters):
        """Aplica filtros complexos e atualiza a visualização
        
        Args:
            filters (dict): Dicionário com filtros a aplicar
                Chaves possíveis:
                - stage_ids: lista de IDs de palcos
                - activity_types: lista de tipos de atividade
                - responsible_ids: lista de IDs de responsáveis
                - date_range: tupla (start_date, end_date)
                - status: lista de status
                - priority: lista de prioridades
                - search_text: texto para busca
                - tag_ids: lista de IDs de tags
                - parent_ids: lista de IDs de eventos pai
                
        Returns:
            list: Lista de atividades filtradas
        """
        query = self.db.query(Activity)
        query = query.join(Stage)
        
        # Filtrar por evento (ou sub-eventos)
        if filters.get('include_sub_events', False):
            # Busca o evento atual e seus sub-eventos
            event_ids = [self.current_event_id]
            sub_events = self.db.query(Event).filter(Event.parent_id == self.current_event_id).all()
            event_ids.extend([event.id for event in sub_events])
            query = query.filter(Stage.event_id.in_(event_ids))
        else:
            # Apenas o evento atual
            query = query.filter(Stage.event_id == self.current_event_id)
        
        # Aplicar filtros complexos
        if filters.get('stage_ids'):
            query = query.filter(Activity.stage_id.in_(filters['stage_ids']))
            
        if filters.get('activity_types'):
            query = query.filter(Activity.activity_type.in_(filters['activity_types']))
            
        if filters.get('responsible_ids'):
            query = query.filter(Activity.responsible_id.in_(filters['responsible_ids']))
            
        if filters.get('date_range'):
            start_date, end_date = filters['date_range']
            query = query.filter(Activity.start_time >= start_date,
                               Activity.end_time <= end_date)
            
        if filters.get('status'):
            query = query.filter(Activity.status.in_(filters['status']))
            
        if filters.get('priority'):
            query = query.filter(Activity.priority.in_(filters['priority']))
        
        if filters.get('search_text'):
            search = f"%{filters['search_text']}%"
            query = query.filter(
                or_(
                    Activity.name.like(search),
                    Activity.details.like(search)
                )
            )
        
        # Ordenar resultados
        sort_field = filters.get('sort_by', 'start_time')
        if sort_field == 'priority':
            query = query.order_by(Activity.priority)
        elif sort_field == 'name':
            query = query.order_by(Activity.name)
        else:  # default: start_time
            query = query.order_by(Activity.start_time)
            
        activities = query.all()
        self.timeline_updated.emit(activities)
        self.current_filters = filters
        
        return activities
