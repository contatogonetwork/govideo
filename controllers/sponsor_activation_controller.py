#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Controlador de Ativações Patrocinadas
Data: 2025-05-15
"""

import os
import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from sqlalchemy import and_, or_, func

from models.sponsor import Sponsor, SponsorActivation, ActivationEvidence
from models.event import Event, Activity
from controllers import BaseController
from core.logging_manager import get_logger

logger = get_logger(__name__)

class SponsorActivationController(BaseController):
    """
    Controlador para gerenciamento de ativações de patrocinadores
    Implementa lógica de negócio para gerenciar status de ativações e evidências
    """
    
    # Sinais
    activation_created = pyqtSignal(int)
    activation_updated = pyqtSignal(int)
    activation_deleted = pyqtSignal(int)
    evidence_added = pyqtSignal(int, int)  # (activation_id, evidence_id)
    evidence_removed = pyqtSignal(int, int)  # (activation_id, evidence_id)
    status_changed = pyqtSignal(int, str, str)  # (activation_id, old_status, new_status)
    activation_completed = pyqtSignal(int)
    notification_created = pyqtSignal(str, str, int)  # (title, message, level)
    
    def __init__(self, db_session):
        """
        Inicializa o controlador
        
        Args:
            db_session: Sessão de banco de dados SQLAlchemy
        """
        super().__init__(db_session)
        self.current_event_id = None
        self.current_filters = {}
        
    def set_current_event(self, event_id):
        """
        Define o evento atual para o controlador
        
        Args:
            event_id (int): ID do evento
            
        Returns:
            bool: True se o evento foi encontrado, False caso contrário
        """
        event = self.db.query(Event).get(event_id)
        if not event:
            logger.error(f"Evento não encontrado: {event_id}")
            return False
            
        self.current_event_id = event_id
        logger.info(f"Evento atual definido para: {event.name} (ID: {event_id})")
        return True
        
    def load_activations(self, event_id=None, filters=None):
        """
        Carrega ativações com base nos filtros
        
        Args:
            event_id (int, opcional): ID do evento. Se não fornecido, usa o evento atual.
            filters (dict, opcional): Filtros a serem aplicados
            
        Returns:
            list: Lista de objetos SponsorActivation
        """
        event_id = event_id or self.current_event_id
        filters = filters or {}
        
        if not event_id:
            logger.error("Nenhum evento definido para carregar ativações")
            return []
            
        try:
            query = self.db.query(SponsorActivation).join(
                Sponsor, SponsorActivation.sponsor_id == Sponsor.id
            ).filter(
                SponsorActivation.event_id == event_id
            )
            
            # Aplicar filtros
            if "status" in filters:
                if isinstance(filters["status"], list):
                    query = query.filter(SponsorActivation.status.in_(filters["status"]))
                else:
                    query = query.filter(SponsorActivation.status == filters["status"])
                    
            if "sponsor_id" in filters:
                if isinstance(filters["sponsor_id"], list):
                    query = query.filter(SponsorActivation.sponsor_id.in_(filters["sponsor_id"]))
                else:
                    query = query.filter(SponsorActivation.sponsor_id == filters["sponsor_id"])
                    
            if "responsible_id" in filters:
                if isinstance(filters["responsible_id"], list):
                    query = query.filter(SponsorActivation.responsible_id.in_(filters["responsible_id"]))
                else:
                    query = query.filter(SponsorActivation.responsible_id == filters["responsible_id"])
                    
            if "search_text" in filters:
                search_text = f"%{filters['search_text']}%"
                query = query.filter(
                    or_(
                        SponsorActivation.name.ilike(search_text),
                        SponsorActivation.description.ilike(search_text),
                        Sponsor.name.ilike(search_text)
                    )
                )
                
            if "date_range" in filters:
                start_date, end_date = filters["date_range"]
                query = query.filter(
                    SponsorActivation.scheduled_date.between(start_date, end_date)
                )
                
            # Ordenar por data e prioridade
            query = query.order_by(
                SponsorActivation.scheduled_date, 
                SponsorActivation.priority.desc()
            )
            
            activations = query.all()
            logger.debug(f"Carregadas {len(activations)} ativações para o evento {event_id}")
            return activations
            
        except Exception as e:
            logger.error(f"Erro ao carregar ativações: {str(e)}", exc_info=True)
            return []
            
    def create_activation(self, sponsor_id, event_id, name, description, scheduled_date, 
                          type_id, responsible_id, priority=2, location="", target_audience="", 
                          status="pending"):
        """
        Cria uma nova ativação patrocinada
        
        Args:
            sponsor_id (int): ID do patrocinador
            event_id (int): ID do evento
            name (str): Nome da ativação
            description (str): Descrição da ativação
            scheduled_date (datetime): Data agendada
            type_id (int): ID do tipo de ativação
            responsible_id (int): ID do responsável
            priority (int): Prioridade (1-4)
            location (str): Local da ativação
            target_audience (str): Público alvo
            status (str): Status inicial (pending, in_progress, completed, canceled)
            
        Returns:
            SponsorActivation: Objeto criado ou None se houve erro
        """
        try:
            activation = SponsorActivation(
                sponsor_id=sponsor_id,
                event_id=event_id,
                name=name,
                description=description,
                scheduled_date=scheduled_date,
                type_id=type_id,
                responsible_id=responsible_id,
                priority=priority,
                location=location,
                target_audience=target_audience,
                status=status,
                created_at=datetime.datetime.utcnow()
            )
            
            self.db.add(activation)
            self.db.commit()
            
            logger.info(f"Ativação criada: {name} (ID: {activation.id})")
            self.activation_created.emit(activation.id)
            self.notification_created.emit(
                "Ativação Criada", 
                f"Nova ativação patrocinada: {name}", 
                0
            )
            
            return activation
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao criar ativação: {str(e)}", exc_info=True)
            self.notification_created.emit(
                "Erro", 
                f"Não foi possível criar a ativação: {str(e)}", 
                2
            )
            return None
            
    def update_activation(self, activation_id, **kwargs):
        """
        Atualiza uma ativação existente
        
        Args:
            activation_id (int): ID da ativação
            **kwargs: Campos a serem atualizados
            
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            activation = self.db.query(SponsorActivation).get(activation_id)
            if not activation:
                logger.error(f"Ativação não encontrada: {activation_id}")
                return False
                
            old_status = activation.status
                
            # Atualizar campos
            for key, value in kwargs.items():
                if hasattr(activation, key):
                    setattr(activation, key, value)
                    
            activation.updated_at = datetime.datetime.utcnow()
            
            # Se status mudou, emitir sinal
            if "status" in kwargs and old_status != kwargs["status"]:
                self.status_changed.emit(activation_id, old_status, kwargs["status"])
                
                # Se foi completada, emitir sinal específico
                if kwargs["status"] == "completed":
                    self.activation_completed.emit(activation_id)
            
            self.db.commit()
            
            logger.info(f"Ativação atualizada: {activation.name} (ID: {activation_id})")
            self.activation_updated.emit(activation_id)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar ativação: {str(e)}", exc_info=True)
            self.notification_created.emit(
                "Erro", 
                f"Não foi possível atualizar a ativação: {str(e)}", 
                2
            )
            return False
            
    def delete_activation(self, activation_id):
        """
        Remove uma ativação
        
        Args:
            activation_id (int): ID da ativação
            
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            activation = self.db.query(SponsorActivation).get(activation_id)
            if not activation:
                logger.error(f"Ativação não encontrada: {activation_id}")
                return False
                
            # Remover evidências relacionadas
            self.db.query(ActivationEvidence).filter(
                ActivationEvidence.activation_id == activation_id
            ).delete()
            
            # Remover a ativação
            self.db.delete(activation)
            self.db.commit()
            
            logger.info(f"Ativação removida: ID {activation_id}")
            self.activation_deleted.emit(activation_id)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao remover ativação: {str(e)}", exc_info=True)
            self.notification_created.emit(
                "Erro", 
                f"Não foi possível remover a ativação: {str(e)}", 
                2
            )
            return False
            
    def add_evidence(self, activation_id, file_path, description, type_id=1, user_id=None):
        """
        Adiciona uma evidência à ativação
        
        Args:
            activation_id (int): ID da ativação
            file_path (str): Caminho do arquivo de evidência
            description (str): Descrição da evidência
            type_id (int): Tipo de evidência (1=foto, 2=vídeo, 3=documento)
            user_id (int): ID do usuário que adicionou
            
        Returns:
            ActivationEvidence: Objeto criado ou None se houve erro
        """
        try:
            # Verificar se a ativação existe
            activation = self.db.query(SponsorActivation).get(activation_id)
            if not activation:
                logger.error(f"Ativação não encontrada: {activation_id}")
                return None
                
            # Verificar extensão do arquivo para determinar o tipo
            if type_id == 0:  # Auto-determinar
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    type_id = 1  # Foto
                elif ext in ['.mp4', '.mov', '.avi', '.wmv']:
                    type_id = 2  # Vídeo
                else:
                    type_id = 3  # Documento
            
            # Criar evidência
            evidence = ActivationEvidence(
                activation_id=activation_id,
                file_path=file_path,
                description=description,
                type_id=type_id,
                user_id=user_id,
                created_at=datetime.datetime.utcnow()
            )
            
            self.db.add(evidence)
            self.db.commit()
            
            logger.info(f"Evidência adicionada à ativação {activation_id}: {file_path}")
            self.evidence_added.emit(activation_id, evidence.id)
            
            # Se já tem evidências suficientes, atualizar status
            self._check_and_update_evidence_status(activation)
            
            return evidence
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao adicionar evidência: {str(e)}", exc_info=True)
            self.notification_created.emit(
                "Erro", 
                f"Não foi possível adicionar a evidência: {str(e)}", 
                2
            )
            return None
            
    def remove_evidence(self, evidence_id):
        """
        Remove uma evidência
        
        Args:
            evidence_id (int): ID da evidência
            
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            evidence = self.db.query(ActivationEvidence).get(evidence_id)
            if not evidence:
                logger.error(f"Evidência não encontrada: {evidence_id}")
                return False
                
            activation_id = evidence.activation_id
            
            # Remover arquivo físico se existir e for dentro da pasta de uploads
            if os.path.exists(evidence.file_path) and "uploads" in evidence.file_path:
                try:
                    os.remove(evidence.file_path)
                    logger.debug(f"Arquivo de evidência removido: {evidence.file_path}")
                except Exception as e:
                    logger.warning(f"Não foi possível remover arquivo: {str(e)}")
            
            # Remover do banco
            self.db.delete(evidence)
            self.db.commit()
            
            logger.info(f"Evidência removida: ID {evidence_id}")
            self.evidence_removed.emit(activation_id, evidence_id)
            
            # Atualizar status da ativação
            activation = self.db.query(SponsorActivation).get(activation_id)
            if activation:
                self._check_and_update_evidence_status(activation)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao remover evidência: {str(e)}", exc_info=True)
            self.notification_created.emit(
                "Erro", 
                f"Não foi possível remover a evidência: {str(e)}", 
                2
            )
            return False
            
    def _check_and_update_evidence_status(self, activation):
        """
        Verifica e atualiza o status da ativação com base nas evidências
        
        Args:
            activation (SponsorActivation): Objeto da ativação
        """
        # Verificar se a ativação já está completa
        if activation.status == "completed":
            return
            
        # Contar evidências
        evidence_count = self.db.query(func.count(ActivationEvidence.id)).filter(
            ActivationEvidence.activation_id == activation.id
        ).scalar()
        
        # Se ativação pendente e tem evidência, mudar para em andamento
        if activation.status == "pending" and evidence_count > 0:
            self.update_activation(activation.id, status="in_progress")
            
        # Se ativação em andamento e tem pelo menos 3 evidências, sugerir completar
        if activation.status == "in_progress" and evidence_count >= 3:
            self.notification_created.emit(
                "Ativação com Evidências Completas", 
                f"A ativação '{activation.name}' tem {evidence_count} evidências registradas. Deseja marcá-la como concluída?", 
                1
            )
            
    def get_evidence_counts(self, activation_ids):
        """
        Obtém contagem de evidências para múltiplas ativações
        
        Args:
            activation_ids (list): Lista de IDs de ativações
            
        Returns:
            dict: Dicionário com {activation_id: contagem}
        """
        if not activation_ids:
            return {}
            
        try:
            result = {}
            for a_id in activation_ids:
                count = self.db.query(func.count(ActivationEvidence.id)).filter(
                    ActivationEvidence.activation_id == a_id
                ).scalar()
                result[a_id] = count
                
            return result
            
        except Exception as e:
            logger.error(f"Erro ao contar evidências: {str(e)}", exc_info=True)
            return {}
            
    def get_activation_statistics(self, event_id=None):
        """
        Obtém estatísticas de ativações para um evento
        
        Args:
            event_id (int, opcional): ID do evento. Se não fornecido, usa o evento atual.
            
        Returns:
            dict: Estatísticas das ativações
        """
        event_id = event_id or self.current_event_id
        if not event_id:
            logger.error("Nenhum evento definido para estatísticas")
            return {}
            
        try:
            # Total de ativações
            total = self.db.query(func.count(SponsorActivation.id)).filter(
                SponsorActivation.event_id == event_id
            ).scalar()
            
            # Contagem por status
            status_counts = {}
            for status in ["pending", "in_progress", "completed", "canceled"]:
                count = self.db.query(func.count(SponsorActivation.id)).filter(
                    SponsorActivation.event_id == event_id,
                    SponsorActivation.status == status
                ).scalar()
                status_counts[status] = count
                
            # Contagem por patrocinador
            sponsor_counts = self.db.query(
                SponsorActivation.sponsor_id,
                Sponsor.name,
                func.count(SponsorActivation.id)
            ).join(
                Sponsor, SponsorActivation.sponsor_id == Sponsor.id
            ).filter(
                SponsorActivation.event_id == event_id
            ).group_by(
                SponsorActivation.sponsor_id,
                Sponsor.name
            ).all()
            
            sponsor_data = {
                sponsor_id: {"name": name, "count": count}
                for sponsor_id, name, count in sponsor_counts
            }
            
            # Total de evidências
            total_evidence = self.db.query(func.count(ActivationEvidence.id)).join(
                SponsorActivation, ActivationEvidence.activation_id == SponsorActivation.id
            ).filter(
                SponsorActivation.event_id == event_id
            ).scalar()
            
            # Média de evidências por ativação
            avg_evidence = total_evidence / total if total > 0 else 0
            
            return {
                "total_activations": total,
                "status_counts": status_counts,
                "sponsor_data": sponsor_data,
                "total_evidence": total_evidence,
                "avg_evidence_per_activation": avg_evidence,
                "completion_rate": (status_counts.get("completed", 0) / total) if total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}", exc_info=True)
            return {}
