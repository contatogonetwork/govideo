"""
GONETWORK AI - Controlador de Patrocinadores e Ativações
Implementa a lógica de negócio para gerenciamento de patrocinadores e suas ativações
"""

from PyQt5.QtCore import QObject, pyqtSignal
import datetime
import os
import uuid
import shutil

from controllers import BaseController
from models.sponsor import Sponsor, Activation, ActivationType, ActivationEvidence, SponsorTier, ActivationStatus, EvidenceFileType
from models.event import Event
from core.config import settings
from core.logging_manager import get_logger

logger = get_logger(__name__)

class SponsorController(BaseController):
    """
    Controlador para gerenciamento de patrocinadores e ativações
    """
    
    # Sinais
    sponsors_updated = pyqtSignal(list)  # Lista de patrocinadores atualizada
    activations_updated = pyqtSignal(list)  # Lista de ativações atualizada
    activation_created = pyqtSignal(object)  # Nova ativação criada
    evidence_added = pyqtSignal(object, object)  # Ativação, evidência
    activation_status_changed = pyqtSignal(object, str)  # Ativação, novo status
    
    def __init__(self, db_session):
        """
        Inicializa o controlador de patrocinadores
        
        Args:
            db_session: Sessão do SQLAlchemy para acesso ao banco de dados
        """
        super().__init__(db_session)
        self.current_event_id = None
        self.current_filters = {}
        
        # Garantir diretórios necessários
        self.logos_dir = os.path.join(settings.upload_dir, "logos")
        self.evidence_dir = os.path.join(settings.upload_dir, "evidences")
        os.makedirs(self.logos_dir, exist_ok=True)
        os.makedirs(self.evidence_dir, exist_ok=True)
    
    def set_current_event(self, event_id):
        """
        Define o evento atual para ativações
        
        Args:
            event_id (int): ID do evento
        """
        self.current_event_id = event_id
        logger.info(f"Evento atual definido para ativações: {event_id}")
        self.reload_activations()
    
    def reload_activations(self):
        """
        Recarrega as ativações com base no evento atual e filtros
        """
        if not self.current_event_id:
            logger.warning("Tentativa de carregar ativações sem evento definido")
            return
            
        try:
            activations = self.load_activations(self.current_event_id, self.current_filters)
            self.activations_updated.emit(activations)
            logger.debug(f"Ativações atualizadas: {len(activations)} carregadas")
        except Exception as e:
            logger.error(f"Erro ao carregar ativações: {str(e)}", exc_info=True)
    
    def load_activations(self, event_id, filters=None):
        """
        Carrega ativações com filtros aplicados
        
        Args:
            event_id (int): ID do evento
            filters (dict): Filtros a serem aplicados
            
        Returns:
            list: Lista de objetos Activation
        """
        filters = filters or {}
        
        # Construir query base
        query = self.db.query(Activation).filter(Activation.event_id == event_id)
        
        # Aplicar filtros
        if filters.get('sponsor_id'):
            query = query.filter(Activation.sponsor_id == filters['sponsor_id'])
            
        if filters.get('activity_id'):
            query = query.filter(Activation.activity_id == filters['activity_id'])
            
        if filters.get('status'):
            query = query.filter(Activation.status.in_(filters['status']))
            
        if filters.get('activation_type_id'):
            query = query.filter(Activation.activation_type_id == filters['activation_type_id'])
            
        if filters.get('search_text'):
            search = f"%{filters['search_text']}%"
            query = query.filter(
                Activation.name.like(search) | 
                Activation.description.like(search) | 
                Activation.location.like(search)
            )
            
        if filters.get('start_date'):
            query = query.filter(Activation.end_date >= filters['start_date'])
            
        if filters.get('end_date'):
            query = query.filter(Activation.start_date <= filters['end_date'])
        
        # Ordenar por data de início e nome
        query = query.order_by(Activation.start_date, Activation.name)
        
        return query.all()
    
    def get_sponsors(self, filters=None):
        """
        Obtém patrocinadores com filtros opcionais
        
        Args:
            filters (dict, optional): Filtros a serem aplicados
            
        Returns:
            list: Lista de objetos Sponsor
        """
        filters = filters or {}
        
        # Construir query base
        query = self.db.query(Sponsor)
        
        # Aplicar filtros
        if filters.get('tier'):
            query = query.filter(Sponsor.tier == filters['tier'])
            
        if filters.get('search_text'):
            search = f"%{filters['search_text']}%"
            query = query.filter(
                Sponsor.name.like(search) | 
                Sponsor.contact_name.like(search)
            )
        
        # Ordenar por tier (mais alto primeiro) e nome
        query = query.order_by(Sponsor.tier, Sponsor.name)
        
        sponsors = query.all()
        self.sponsors_updated.emit(sponsors)
        return sponsors
    
    def get_activation_types(self):
        """
        Obtém todos os tipos de ativação
        
        Returns:
            list: Lista de objetos ActivationType
        """
        return self.db.query(ActivationType).order_by(ActivationType.name).all()
    
    def get_sponsor_by_id(self, sponsor_id):
        """
        Obtém um patrocinador pelo ID
        
        Args:
            sponsor_id (int): ID do patrocinador
            
        Returns:
            Sponsor: Objeto de patrocinador ou None
        """
        return self.db.query(Sponsor).get(sponsor_id)
    
    def get_activation_by_id(self, activation_id):
        """
        Obtém uma ativação pelo ID
        
        Args:
            activation_id (int): ID da ativação
            
        Returns:
            Activation: Objeto de ativação ou None
        """
        return self.db.query(Activation).get(activation_id)
    
    def create_sponsor(self, name, contact_name=None, contact_email=None, 
                     contact_phone=None, logo_path=None, description=None, 
                     website=None, tier=SponsorTier.silver):
        """
        Cria um novo patrocinador
        
        Args:
            name (str): Nome do patrocinador
            contact_name (str, optional): Nome do contato
            contact_email (str, optional): Email do contato
            contact_phone (str, optional): Telefone do contato
            logo_path (str, optional): Caminho do logo
            description (str, optional): Descrição
            website (str, optional): Site
            tier (SponsorTier, optional): Nível do patrocinador
            
        Returns:
            Sponsor: Objeto de patrocinador criado
        """
        try:
            # Se um logo foi fornecido, copiá-lo para o diretório de logos
            stored_logo_path = None
            if logo_path and os.path.exists(logo_path):
                # Gerar nome único para o logo
                _, extension = os.path.splitext(logo_path)
                unique_name = f"{uuid.uuid4().hex}{extension}"
                stored_logo_path = os.path.join(self.logos_dir, unique_name)
                
                # Copiar logo
                shutil.copy2(logo_path, stored_logo_path)
            
            # Criar sponsor
            sponsor = Sponsor(
                name=name,
                contact_name=contact_name,
                contact_email=contact_email,
                contact_phone=contact_phone,
                logo_path=stored_logo_path,
                description=description,
                website=website,
                tier=tier,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            
            self.db.add(sponsor)
            self.db.commit()
            
            logger.info(f"Patrocinador criado: {sponsor.id} - {sponsor.name}")
            self.get_sponsors()  # Recarregar patrocinadores
            return sponsor
            
        except Exception as e:
            self.db.rollback()
            # Limpar logo copiado em caso de erro
            if stored_logo_path and os.path.exists(stored_logo_path):
                try:
                    os.remove(stored_logo_path)
                except:
                    pass
            logger.error(f"Erro ao criar patrocinador: {str(e)}", exc_info=True)
            raise
    
    def update_sponsor(self, sponsor_id, **kwargs):
        """
        Atualiza um patrocinador existente
        
        Args:
            sponsor_id (int): ID do patrocinador
            **kwargs: Pares de chave-valor com os atributos a serem atualizados
            
        Returns:
            Sponsor: Objeto de patrocinador atualizado
        """
        try:
            sponsor = self.db.query(Sponsor).get(sponsor_id)
            
            if not sponsor:
                logger.warning(f"Tentativa de atualizar patrocinador inexistente: {sponsor_id}")
                return None
            
            # Tratar logo atualizado
            if 'logo_path' in kwargs and kwargs['logo_path'] and os.path.exists(kwargs['logo_path']):
                # Remover logo antigo se existir
                if sponsor.logo_path and os.path.exists(sponsor.logo_path):
                    try:
                        os.remove(sponsor.logo_path)
                    except:
                        logger.warning(f"Não foi possível remover logo antigo: {sponsor.logo_path}")
                
                # Gerar nome único para o logo
                logo_path = kwargs['logo_path']
                _, extension = os.path.splitext(logo_path)
                unique_name = f"{uuid.uuid4().hex}{extension}"
                new_logo_path = os.path.join(self.logos_dir, unique_name)
                
                # Copiar logo
                shutil.copy2(logo_path, new_logo_path)
                kwargs['logo_path'] = new_logo_path
            
            # Atualizar os atributos fornecidos
            for key, value in kwargs.items():
                if hasattr(sponsor, key):
                    setattr(sponsor, key, value)
            
            # Atualizar timestamp
            sponsor.updated_at = datetime.datetime.now()
            
            self.db.commit()
            
            logger.info(f"Patrocinador atualizado: {sponsor.id} - {sponsor.name}")
            self.get_sponsors()  # Recarregar patrocinadores
            return sponsor
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar patrocinador: {str(e)}", exc_info=True)
            raise
    
    def delete_sponsor(self, sponsor_id, delete_logo=True):
        """
        Remove um patrocinador
        
        Args:
            sponsor_id (int): ID do patrocinador
            delete_logo (bool, optional): Se True, exclui o logo físico
            
        Returns:
            bool: True se a exclusão for bem-sucedida
        """
        try:
            sponsor = self.db.query(Sponsor).get(sponsor_id)
            
            if not sponsor:
                logger.warning(f"Tentativa de excluir patrocinador inexistente: {sponsor_id}")
                return False
            
            # Guardar caminho do logo para exclusão posterior
            logo_path = sponsor.logo_path
            
            # Excluir do banco de dados
            self.db.delete(sponsor)
            self.db.commit()
            
            # Excluir logo físico se solicitado
            if delete_logo and logo_path and os.path.exists(logo_path):
                try:
                    os.remove(logo_path)
                except Exception as e:
                    logger.error(f"Erro ao excluir logo: {str(e)}", exc_info=True)
            
            logger.info(f"Patrocinador excluído: {sponsor_id}")
            self.get_sponsors()  # Recarregar patrocinadores
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir patrocinador: {str(e)}", exc_info=True)
            raise
    
    def create_activation_type(self, name, description=None, icon_path=None):
        """
        Cria um novo tipo de ativação
        
        Args:
            name (str): Nome do tipo de ativação
            description (str, optional): Descrição
            icon_path (str, optional): Caminho do ícone
            
        Returns:
            ActivationType: Objeto de tipo de ativação criado
        """
        try:
            activation_type = ActivationType(
                name=name,
                description=description,
                icon_path=icon_path
            )
            
            self.db.add(activation_type)
            self.db.commit()
            
            logger.info(f"Tipo de ativação criado: {activation_type.id} - {activation_type.name}")
            return activation_type
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao criar tipo de ativação: {str(e)}", exc_info=True)
            raise
    
    def create_activation(self, name, description, sponsor_id, event_id, activation_type_id,
                        start_date, end_date, location=None, location_description=None, 
                        activity_id=None, budget=None):
        """
        Cria uma nova ativação
        
        Args:
            name (str): Nome da ativação
            description (str): Descrição
            sponsor_id (int): ID do patrocinador
            event_id (int): ID do evento
            activation_type_id (int): ID do tipo de ativação
            start_date (datetime): Data de início
            end_date (datetime): Data de término
            location (str, optional): Localização
            location_description (str, optional): Descrição da localização
            activity_id (int, optional): ID da atividade relacionada
            budget (float, optional): Orçamento
            
        Returns:
            Activation: Objeto de ativação criado
        """
        try:
            activation = Activation(
                name=name,
                description=description,
                sponsor_id=sponsor_id,
                event_id=event_id,
                activity_id=activity_id,
                activation_type_id=activation_type_id,
                status=ActivationStatus.pending,
                start_date=start_date,
                end_date=end_date,
                location=location,
                location_description=location_description,
                budget=budget,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            
            self.db.add(activation)
            self.db.commit()
            
            logger.info(f"Ativação criada: {activation.id} - {activation.name}")
            self.activation_created.emit(activation)
            self.reload_activations()
            return activation
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao criar ativação: {str(e)}", exc_info=True)
            raise
    
    def update_activation(self, activation_id, **kwargs):
        """
        Atualiza uma ativação existente
        
        Args:
            activation_id (int): ID da ativação
            **kwargs: Pares de chave-valor com os atributos a serem atualizados
            
        Returns:
            Activation: Objeto de ativação atualizado
        """
        try:
            activation = self.db.query(Activation).get(activation_id)
            
            if not activation:
                logger.warning(f"Tentativa de atualizar ativação inexistente: {activation_id}")
                return None
                
            # Atualizar os atributos fornecidos
            for key, value in kwargs.items():
                if hasattr(activation, key):
                    setattr(activation, key, value)
            
            # Atualizar timestamp
            activation.updated_at = datetime.datetime.now()
            
            self.db.commit()
            
            logger.info(f"Ativação atualizada: {activation.id} - {activation.name}")
            self.reload_activations()
            return activation
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar ativação: {str(e)}", exc_info=True)
            raise
    
    def update_activation_status(self, activation_id, new_status, user_id=None):
        """
        Atualiza o status de uma ativação
        
        Args:
            activation_id (int): ID da ativação
            new_status (ActivationStatus): Novo status
            user_id (int, optional): ID do usuário que aprovou (necessário para approved)
            
        Returns:
            Activation: Objeto de ativação atualizado
        """
        try:
            activation = self.db.query(Activation).get(activation_id)
            
            if not activation:
                logger.warning(f"Tentativa de atualizar status de ativação inexistente: {activation_id}")
                return None
            
            old_status = activation.status
            activation.status = new_status
            activation.updated_at = datetime.datetime.now()
            
            # Se foi aprovado, registrar quem aprovou
            if new_status == ActivationStatus.approved and user_id:
                activation.approved_by_id = user_id
                
            # Se foi concluído, registrar data de conclusão
            if new_status == ActivationStatus.filmed:
                activation.completed_time = datetime.datetime.now()
                
            self.db.commit()
            
            logger.info(f"Status de ativação atualizado: {activation.id} - {old_status} -> {new_status}")
            self.activation_status_changed.emit(activation, new_status.value)
            self.reload_activations()
            return activation
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar status de ativação: {str(e)}", exc_info=True)
            raise
    
    def delete_activation(self, activation_id):
        """
        Remove uma ativação
        
        Args:
            activation_id (int): ID da ativação
            
        Returns:
            bool: True se a exclusão for bem-sucedida
        """
        try:
            activation = self.db.query(Activation).get(activation_id)
            
            if not activation:
                logger.warning(f"Tentativa de excluir ativação inexistente: {activation_id}")
                return False
                
            self.db.delete(activation)
            self.db.commit()
            
            logger.info(f"Ativação excluída: {activation_id}")
            self.reload_activations()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir ativação: {str(e)}", exc_info=True)
            raise
    
    def add_evidence(self, activation_id, file_path, file_type, notes=None, user_id=None):
        """
        Adiciona evidência a uma ativação
        
        Args:
            activation_id (int): ID da ativação
            file_path (str): Caminho do arquivo de evidência
            file_type (EvidenceFileType): Tipo do arquivo
            notes (str, optional): Notas/observações
            user_id (int, optional): ID do usuário que fez upload
            
        Returns:
            ActivationEvidence: Objeto de evidência criado
        """
        try:
            # Verificar se a ativação existe
            activation = self.db.query(Activation).get(activation_id)
            
            if not activation:
                logger.warning(f"Tentativa de adicionar evidência a ativação inexistente: {activation_id}")
                raise ValueError(f"Ativação não encontrada: {activation_id}")
            
            # Criar diretório para evidências se não existir
            activation_evidence_dir = os.path.join(self.evidence_dir, f"activation_{activation_id}")
            os.makedirs(activation_evidence_dir, exist_ok=True)
            
            # Gerar nome de arquivo único
            original_filename = os.path.basename(file_path)
            _, extension = os.path.splitext(original_filename)
            unique_filename = f"evidence_{uuid.uuid4().hex}{extension}"
            
            # Caminho de destino
            dest_path = os.path.join(activation_evidence_dir, unique_filename)
            
            # Copiar arquivo
            shutil.copy2(file_path, dest_path)
            
            # Criar registro de evidência
            evidence = ActivationEvidence(
                activation_id=activation_id,
                file_path=dest_path,
                file_type=file_type,
                approved=False,
                notes=notes,
                uploaded_by_id=user_id,
                uploaded_at=datetime.datetime.now()
            )
            
            self.db.add(evidence)
            self.db.commit()
            
            logger.info(f"Evidência adicionada à ativação {activation_id}: {evidence.id}")
            self.evidence_added.emit(activation, evidence)
            return evidence
            
        except Exception as e:
            self.db.rollback()
            # Limpar arquivo copiado em caso de erro
            if 'dest_path' in locals() and os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except:
                    pass
            logger.error(f"Erro ao adicionar evidência: {str(e)}", exc_info=True)
            raise
    
    def approve_evidence(self, evidence_id, approved=True):
        """
        Aprova ou reprova uma evidência
        
        Args:
            evidence_id (int): ID da evidência
            approved (bool): Status de aprovação
            
        Returns:
            ActivationEvidence: Objeto de evidência atualizado
        """
        try:
            evidence = self.db.query(ActivationEvidence).get(evidence_id)
            
            if not evidence:
                logger.warning(f"Tentativa de aprovar evidência inexistente: {evidence_id}")
                return None
                
            evidence.approved = approved
            self.db.commit()
            
            action_text = "aprovada" if approved else "reprovada"
            logger.info(f"Evidência {evidence_id} {action_text}")
            return evidence
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao aprovar/reprovar evidência: {str(e)}", exc_info=True)
            raise
    
    def delete_evidence(self, evidence_id, delete_file=True):
        """
        Remove uma evidência
        
        Args:
            evidence_id (int): ID da evidência
            delete_file (bool, optional): Se True, exclui o arquivo físico
            
        Returns:
            bool: True se a exclusão for bem-sucedida
        """
        try:
            evidence = self.db.query(ActivationEvidence).get(evidence_id)
            
            if not evidence:
                logger.warning(f"Tentativa de excluir evidência inexistente: {evidence_id}")
                return False
                
            # Guardar caminho do arquivo para exclusão posterior
            file_path = evidence.file_path
            
            self.db.delete(evidence)
            self.db.commit()
            
            # Excluir arquivo físico se solicitado
            if delete_file and file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Erro ao excluir arquivo de evidência: {str(e)}", exc_info=True)
            
            logger.info(f"Evidência excluída: {evidence_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir evidência: {str(e)}", exc_info=True)
            raise
    
    def get_evidence_for_activation(self, activation_id):
        """
        Obtém todas as evidências de uma ativação
        
        Args:
            activation_id (int): ID da ativação
            
        Returns:
            list: Lista de objetos ActivationEvidence
        """
        return self.db.query(ActivationEvidence).filter(
            ActivationEvidence.activation_id == activation_id
        ).order_by(ActivationEvidence.uploaded_at.desc()).all()
