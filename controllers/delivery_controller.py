"""
GONETWORK AI - Controlador de Kanban de Entregas
Implementa a lógica de negócio para gerenciamento de entregas no formato Kanban
"""

from PyQt5.QtCore import QObject, pyqtSignal
import datetime
from sqlalchemy import or_, and_

from controllers import BaseController
from models.delivery import Delivery, DeliveryFile, DeliveryComment
from models.event import Event, Activity
from models.team import TeamMember
from models.user import User
from core.logging_manager import get_logger

logger = get_logger(__name__)

class DeliveryKanbanController(BaseController):
    """
    Controlador para Kanban de entregas
    """
    
    # Sinais
    deliveries_updated = pyqtSignal(list)  # Lista de entregas atualizadas
    delivery_moved = pyqtSignal(int, str)  # ID da entrega e nova coluna
    delivery_created = pyqtSignal(object)  # Objeto da nova entrega
    notification_created = pyqtSignal(str, str, int)  # Título, mensagem, nível (0=info, 1=warning, 2=error)
    
    def __init__(self, db_session):
        """
        Inicializa o controlador de Kanban de entregas
        
        Args:
            db_session: Sessão do SQLAlchemy para acesso ao banco de dados
        """
        super().__init__(db_session)
        self.current_event_id = None
        self.current_filters = {}
    
    def set_current_event(self, event_id):
        """
        Define o evento atual para o Kanban
        
        Args:
            event_id (int): ID do evento
        """
        self.current_event_id = event_id
        logger.info(f"Evento atual definido para Kanban: {event_id}")
        self.reload_deliveries()
    
    def reload_deliveries(self):
        """
        Recarrega as entregas com base no evento atual e filtros
        """
        if not self.current_event_id:
            logger.warning("Tentativa de carregar entregas sem evento definido")
            return
            
        try:
            deliveries = self.load_deliveries(self.current_event_id, self.current_filters)
            self.deliveries_updated.emit(deliveries)
            logger.debug(f"Kanban atualizado: {len(deliveries)} entregas carregadas")
        except Exception as e:
            logger.error(f"Erro ao carregar entregas para Kanban: {str(e)}", exc_info=True)
    
    def load_deliveries(self, event_id, filters=None):
        """
        Carrega entregas com filtros aplicados
        
        Args:
            event_id (int): ID do evento
            filters (dict): Filtros a serem aplicados
            
        Returns:
            list: Lista de objetos Delivery
        """
        filters = filters or {}
        
        # Construir query base
        query = self.db.query(Delivery).filter(Delivery.event_id == event_id)
        
        # Aplicar filtros
        if filters.get('responsible_id'):
            query = query.filter(Delivery.responsible_id == filters['responsible_id'])
            
        if filters.get('activity_id'):
            query = query.filter(Delivery.activity_id == filters['activity_id'])
            
        if filters.get('status'):
            query = query.filter(Delivery.status.in_(filters['status']))
            
        if filters.get('priority'):
            query = query.filter(Delivery.priority.in_(filters['priority']))
            
        if filters.get('search_text'):
            search = f"%{filters['search_text']}%"
            query = query.filter(
                or_(
                    Delivery.title.like(search),
                    Delivery.description.like(search)
                )
            )
        
        # Ordenar por prioridade (maior primeiro) e depois por prazo (mais próximo primeiro)
        query = query.order_by(Delivery.priority.desc(), Delivery.deadline)
        
        return query.all()
    
    def get_delivery(self, delivery_id):
        """
        Obtém uma entrega pelo ID
        
        Args:
            delivery_id (int): ID da entrega
            
        Returns:
            Delivery: Objeto de entrega ou None
        """
        return self.db.query(Delivery).get(delivery_id)
    
    def map_status_to_column(self, status):
        """
        Mapeia status do banco para coluna do Kanban
        
        Args:
            status (str): Status da entrega no banco de dados
            
        Returns:
            str: Coluna do Kanban
        """
        mapping = {
            "pending": "pending",
            "in_progress": "in_progress",
            "review": "in_review",
            "approved": "approved",
            "published": "published",
            "rejected": "rejected"
        }
        return mapping.get(status, "pending")
    
    def map_column_to_status(self, column_id):
        """
        Mapeia identificador de coluna para status do banco
        
        Args:
            column_id (str): ID da coluna do Kanban
            
        Returns:
            str: Status para o banco de dados
        """
        mapping = {
            "pending": "pending",
            "in_progress": "in_progress",
            "in_review": "review",
            "approved": "approved",
            "published": "published",
            "rejected": "rejected"
        }
        return mapping.get(column_id, "pending")
    
    def move_delivery(self, delivery_id, to_column, user_id=None):
        """
        Move uma entrega para outra coluna
        
        Args:
            delivery_id (int): ID da entrega
            to_column (str): ID da coluna de destino
            user_id (int, optional): ID do usuário que moveu a entrega
            
        Returns:
            bool: True se a movimentação for bem-sucedida
        """
        try:
            delivery = self.db.query(Delivery).get(delivery_id)
            
            if not delivery:
                logger.warning(f"Tentativa de mover entrega inexistente: {delivery_id}")
                return False
                
            # Mapear coluna para status
            new_status = self.map_column_to_status(to_column)
            
            # Se o status não mudou, não fazer nada
            if delivery.status == new_status:
                return True
                
            # Atualizar status e progresso com base na coluna
            old_status = delivery.status
            delivery.status = new_status
            
            # Atualizar progresso com base na coluna
            progress_map = {
                "pending": 0.0,
                "in_progress": 0.3,
                "in_review": 0.7,
                "approved": 0.9,
                "published": 1.0,
                "rejected": 0.0
            }
            
            delivery.progress = progress_map.get(new_status, delivery.progress)
            
            # Se a entrega foi publicada, registrar a data
            if new_status == "published" and not delivery.published_at:
                delivery.published_at = datetime.datetime.now()
                
            self.db.commit()
            
            # Registrar movimento em log
            logger.info(f"Entrega {delivery_id} movida: {old_status} -> {new_status}")
            
            # Criar notificação para outros usuários
            if user_id:
                self.create_delivery_notification(delivery, old_status, new_status, user_id)
                
            # Emitir sinal de movimentação
            self.delivery_moved.emit(delivery_id, to_column)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao mover entrega: {str(e)}", exc_info=True)
            raise
    
    def create_delivery_notification(self, delivery, old_status, new_status, user_id):
        """
        Cria uma notificação de movimentação de entrega
        
        Args:
            delivery (Delivery): Objeto de entrega
            old_status (str): Status anterior
            new_status (str): Novo status
            user_id (int): ID do usuário que moveu a entrega
        """
        # Determinar destinatários da notificação
        recipients = set()
        
        if delivery.created_by and delivery.created_by != user_id:
            recipients.add(delivery.created_by)
            
        if delivery.responsible_id:
            # Obter ID do usuário associado ao membro da equipe, se houver
            responsible = self.db.query(TeamMember).get(delivery.responsible_id)
            if responsible and responsible.user_id and responsible.user_id != user_id:
                recipients.add(responsible.user_id)
        
        # Se não houver destinatários, não criar notificação
        if not recipients:
            return
        
        # Criar mensagem de notificação
        message_templates = {
            "in_progress": "A entrega '{title}' foi iniciada",
            "in_review": "A entrega '{title}' foi enviada para revisão",
            "approved": "A entrega '{title}' foi aprovada",
            "published": "A entrega '{title}' foi publicada",
            "rejected": "A entrega '{title}' foi rejeitada"
        }
        
        message = message_templates.get(
            new_status, 
            "A entrega '{title}' foi movida para {status}"
        ).format(
            title=delivery.title,
            status=new_status.replace('_', ' ')
        )
        
        # Nível da notificação
        level = 0  # 0 = info, 1 = warning, 2 = error
        if new_status == "rejected":
            level = 1
        
        # Emitir sinal de notificação
        self.notification_created.emit(f"Atualização de entrega", message, level)
        
        # TODO: Implementar sistema de persistência de notificações quando necessário
        
    def create_delivery(self, title, description, deadline, responsible_id, event_id,
                      activity_id=None, format_specs=None, priority=3):
        """
        Cria uma nova entrega
        
        Args:
            title (str): Título da entrega
            description (str): Descrição
            deadline (datetime): Prazo de entrega
            responsible_id (int): ID do membro da equipe responsável
            event_id (int): ID do evento
            activity_id (int, optional): ID da atividade relacionada
            format_specs (str, optional): Especificações de formato
            priority (int, optional): Prioridade (1-4)
            
        Returns:
            Delivery: Objeto de entrega criado
        """
        try:
            delivery = Delivery(
                title=title,
                description=description,
                deadline=deadline,
                responsible_id=responsible_id,
                event_id=event_id,
                activity_id=activity_id,
                format_specs=format_specs,
                priority=priority,
                status="pending",
                progress=0.0,
                created_at=datetime.datetime.now(),
                created_by=1  # TODO: Usar ID do usuário atual quando implementar autenticação
            )
            
            self.db.add(delivery)
            self.db.commit()
            
            logger.info(f"Entrega criada: {delivery.id} - {delivery.title}")
            
            # Emitir sinal de nova entrega
            self.delivery_created.emit(delivery)
            
            # Recarregar entregas
            self.reload_deliveries()
            
            return delivery
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao criar entrega: {str(e)}", exc_info=True)
            raise
    
    def update_delivery(self, delivery_id, **kwargs):
        """
        Atualiza uma entrega existente
        
        Args:
            delivery_id (int): ID da entrega
            **kwargs: Pares de chave-valor com os atributos a serem atualizados
            
        Returns:
            Delivery: Objeto de entrega atualizado
        """
        try:
            delivery = self.db.query(Delivery).get(delivery_id)
            
            if not delivery:
                logger.warning(f"Tentativa de atualizar entrega inexistente: {delivery_id}")
                return None
                
            # Atualizar os atributos fornecidos
            for key, value in kwargs.items():
                if hasattr(delivery, key):
                    setattr(delivery, key, value)
            
            self.db.commit()
            
            logger.info(f"Entrega atualizada: {delivery.id} - {delivery.title}")
            self.reload_deliveries()
            return delivery
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar entrega: {str(e)}", exc_info=True)
            raise
    
    def delete_delivery(self, delivery_id):
        """
        Remove uma entrega
        
        Args:
            delivery_id (int): ID da entrega
            
        Returns:
            bool: True se a exclusão for bem-sucedida
        """
        try:
            delivery = self.db.query(Delivery).get(delivery_id)
            
            if not delivery:
                logger.warning(f"Tentativa de excluir entrega inexistente: {delivery_id}")
                return False
                
            self.db.delete(delivery)
            self.db.commit()
            
            logger.info(f"Entrega excluída: {delivery_id}")
            self.reload_deliveries()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir entrega: {str(e)}", exc_info=True)
            raise
    
    def add_comment_to_delivery(self, delivery_id, user_id, comment, timecode=None, is_system=False):
        """
        Adiciona um comentário a uma entrega
        
        Args:
            delivery_id (int): ID da entrega
            user_id (int): ID do usuário
            comment (str): Texto do comentário
            timecode (str, optional): Timecode para vídeos
            is_system (bool, optional): Se é um comentário de sistema
            
        Returns:
            DeliveryComment: Objeto de comentário criado
        """
        try:
            delivery_comment = DeliveryComment(
                delivery_id=delivery_id,
                user_id=user_id,
                comment=comment,
                timestamp=datetime.datetime.now(),
                timecode=timecode,
                is_system=is_system
            )
            
            self.db.add(delivery_comment)
            self.db.commit()
            
            logger.info(f"Comentário adicionado à entrega {delivery_id}")
            return delivery_comment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao adicionar comentário: {str(e)}", exc_info=True)
            raise

    def move_delivery_to_column(self, delivery_id, column_id, user_id):
        """
        Move uma entrega para outra coluna do Kanban
        
        Args:
            delivery_id (int): ID da entrega
            column_id (str): ID da coluna destino (pending, editing, reviewing, completed)
            user_id (int): ID do usuário que executou a ação
            
        Returns:
            bool: True se sucesso, False caso contrário
        """
        # Mapeamento de colunas para status na base
        column_to_status = {
            "pending": "pending",
            "editing": "in_progress", 
            "reviewing": "review",
            "completed": "approved"
        }
        
        if column_id not in column_to_status:
            logger.error(f"Coluna inválida: {column_id}")
            self.notification_created.emit(
                "Erro", 
                f"Coluna inválida: {column_id}", 
                2
            )
            return False
        
        try:
            delivery = self.db.query(Delivery).get(delivery_id)
            if not delivery:
                logger.error(f"Entrega não encontrada: {delivery_id}")
                return False
            
            # Salvar status anterior para notificações
            previous_status = delivery.status
            
            # Atualizar status da entrega
            delivery.status = column_to_status[column_id]
            
            # Se a entrega estiver sendo concluída, atualizar data de publicação
            if column_id == "completed" and previous_status != "approved":
                delivery.published_at = datetime.datetime.utcnow()
            
            # Se a entrega estiver sendo enviada para revisão, atualizar progresso para 100%
            if column_id == "reviewing" and previous_status != "review":
                delivery.progress = 1.0
                
            self.db.commit()
            
            # Emitir sinal de movimentação
            self.delivery_moved.emit(delivery_id, column_id)
            
            # Criar um comentário do sistema sobre a mudança de status
            self._add_status_change_comment(delivery_id, previous_status, delivery.status, user_id)
            
            # Notificar sobre movimentação
            self._notify_delivery_moved(delivery, previous_status, column_id, user_id)
            
            logger.info(f"Entrega {delivery_id} movida para: {column_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao mover entrega: {str(e)}", exc_info=True)
            self.notification_created.emit(
                "Erro", 
                f"Não foi possível mover a entrega: {str(e)}", 
                2
            )
            return False
            
    def _add_status_change_comment(self, delivery_id, old_status, new_status, user_id):
        """
        Adiciona um comentário de sistema sobre mudança de status
        
        Args:
            delivery_id (int): ID da entrega
            old_status (str): Status anterior
            new_status (str): Novo status
            user_id (int): ID do usuário que fez a alteração
        """
        status_names = {
            "pending": "Pendente", 
            "in_progress": "Em Andamento", 
            "review": "Em Revisão", 
            "approved": "Aprovado",
            "published": "Publicado",
            "rejected": "Rejeitado"
        }
        
        old_status_name = status_names.get(old_status, old_status)
        new_status_name = status_names.get(new_status, new_status)
        
        comment_text = f"Status alterado de '{old_status_name}' para '{new_status_name}'"
        
        comment = DeliveryComment(
            delivery_id=delivery_id,
            user_id=user_id,
            comment=comment_text,
            is_system=True
        )
        
        try:
            self.db.add(comment)
            self.db.commit()
            logger.debug(f"Comentário de sistema adicionado: {comment_text}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao adicionar comentário de sistema: {str(e)}", exc_info=True)
            
    def _notify_delivery_moved(self, delivery, previous_status, column_id, user_id):
        """
        Notifica sobre movimentação de entrega
        
        Args:
            delivery (Delivery): Objeto da entrega movida
            previous_status (str): Status anterior
            column_id (str): ID da coluna destino
            user_id (int): ID do usuário que fez a alteração
        """
        column_names = {
            "pending": "Pendente",
            "editing": "Em Edição", 
            "reviewing": "Em Revisão",
            "completed": "Concluído"
        }
        
        user = self.db.query(User).get(user_id)
        user_name = user.name if user else "Usuário"
        
        notification_title = f"Entrega Atualizada: {delivery.title}"
        notification_message = f"{user_name} moveu a entrega para '{column_names.get(column_id, column_id)}'."
        
        self.notification_created.emit(notification_title, notification_message, 0)
