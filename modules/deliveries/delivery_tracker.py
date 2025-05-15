#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Sistema de Controle de Entregas Audiovisuais
Data: 2025-05-15
"""

import os
import logging
import shutil
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Tuple
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, asc, and_, or_
from sqlalchemy.orm import joinedload

from core.database import Delivery, DeliveryFile, DeliveryComment, TeamMember, User, Activity, Event

logger = logging.getLogger(__name__)

class DeliveryTracker:
    """Classe para gerenciamento de entregas audiovisuais"""
    
    VALID_STATUSES = ["pending", "in_progress", "review", "approved", "published", "rejected"]
    
    def __init__(self, db_session, upload_path="uploads/deliveries"):
        """Inicializa o rastreador de entregas
        
        Args:
            db_session: Sessão do SQLAlchemy para acesso ao banco de dados
            upload_path (str): Caminho para armazenamento de arquivos
        """
        self.db = db_session
        self.upload_path = upload_path
        
        # Garantir que o diretório de upload existe
        os.makedirs(upload_path, exist_ok=True)
        
    def get_all_deliveries(self, 
                          event_id: Optional[int] = None, 
                          status: Optional[str] = None, 
                          responsible_id: Optional[int] = None, 
                          activity_id: Optional[int] = None,
                          priority: Optional[int] = None,
                          sort_by: str = "deadline",
                          desc_order: bool = False,
                          search_term: Optional[str] = None,
                          limit: Optional[int] = None) -> List[Delivery]:
        """Obter entregas com filtros opcionais
        
        Args:
            event_id: Filtrar por evento
            status: Filtrar por status
            responsible_id: Filtrar por responsável
            activity_id: Filtrar por atividade
            priority: Filtrar por prioridade
            sort_by: Campo para ordenar
            desc_order: Se True, ordena em ordem descendente
            search_term: Termo para busca em títulos e descrições
            limit: Limitar número de resultados
            
        Returns:
            Lista de objetos Delivery
        """
        try:
            query = self.db.query(Delivery)
            
            # Aplicar filtros
            if event_id:
                query = query.filter(Delivery.event_id == event_id)
            if status:
                query = query.filter(Delivery.status == status)
            if responsible_id:
                query = query.filter(Delivery.responsible_id == responsible_id)
            if activity_id:
                query = query.filter(Delivery.activity_id == activity_id)
            if priority:
                query = query.filter(Delivery.priority == priority)
                
            # Busca por texto
            if search_term:
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    or_(
                        Delivery.title.ilike(search_pattern),
                        Delivery.description.ilike(search_pattern)
                    )
                )
                
            # Eager loading para performance
            query = query.options(
                joinedload(Delivery.responsible),
                joinedload(Delivery.activity),
                joinedload(Delivery.event)
            )
                
            # Ordenação
            order_column = None
            if sort_by == "deadline":
                order_column = Delivery.deadline
            elif sort_by == "priority":
                order_column = Delivery.priority
            elif sort_by == "status":
                order_column = Delivery.status
            elif sort_by == "title":
                order_column = Delivery.title
            elif sort_by == "created_at":
                order_column = Delivery.created_at
            
            if order_column:
                if desc_order:
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(asc(order_column))
            
            # Aplicar limite se especificado
            if limit:
                query = query.limit(limit)
                
            return query.all()
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar entregas: {str(e)}")
            return []
            
    def get_delivery(self, delivery_id: int) -> Optional[Delivery]:
        """Obter entrega específica com todos os relacionamentos
        
        Args:
            delivery_id: ID da entrega
            
        Returns:
            Objeto da entrega ou None se não encontrado
        """
        try:
            return self.db.query(Delivery) \
                .options(
                    joinedload(Delivery.responsible),
                    joinedload(Delivery.creator),
                    joinedload(Delivery.activity),
                    joinedload(Delivery.event),
                    joinedload(Delivery.files),
                    joinedload(Delivery.comments).joinedload(DeliveryComment.user)
                ) \
                .filter(Delivery.id == delivery_id) \
                .first()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar entrega id={delivery_id}: {str(e)}")
            return None
            
    def create_delivery_item(self, 
                           title: str, 
                           event_id: int, 
                           deadline: datetime, 
                           created_by: int, 
                           responsible_id: Optional[int] = None, 
                           description: Optional[str] = None, 
                           format_specs: Optional[str] = None, 
                           priority: int = 3, 
                           activity_id: Optional[int] = None) -> Delivery:
        """Criar nova entrega a ser produzida
        
        Args:
            title: Título da entrega
            event_id: ID do evento relacionado
            deadline: Prazo de entrega
            created_by: ID do usuário que está criando
            responsible_id: ID do membro responsável
            description: Descrição detalhada
            format_specs: Especificações técnicas
            priority: Prioridade (1-5, sendo 1 a mais alta)
            activity_id: ID da atividade relacionada
            
        Returns:
            Objeto da nova entrega criada
            
        Raises:
            ValueError: Se dados obrigatórios estiverem faltando
            SQLAlchemyError: Se houver erro no banco de dados
        """
        if not title or not event_id or not deadline or not created_by:
            raise ValueError("Título, evento, prazo e criador são campos obrigatórios")
            
        # Validar prioridade
        if priority < 1 or priority > 5:
            raise ValueError("Prioridade deve ser um valor entre 1 e 5")
            
        # Verificar se o evento existe
        event = self.db.query(Event).get(event_id)
        if not event:
            raise ValueError(f"Evento com ID {event_id} não encontrado")
        
        # Verificar se a atividade existe e pertence ao evento, se fornecida
        if activity_id:
            activity = self.db.query(Activity).join(Activity.stage).filter(
                Activity.id == activity_id,
                Activity.stage.has(event_id=event_id)
            ).first()
            
            if not activity:
                raise ValueError(f"Atividade com ID {activity_id} não encontrada ou não pertence ao evento")
        
        # Verificar se o responsável existe, se fornecido
        if responsible_id:
            responsible = self.db.query(TeamMember).get(responsible_id)
            if not responsible:
                raise ValueError(f"Membro responsável com ID {responsible_id} não encontrado")
            
        try:
            delivery = Delivery(
                title=title,
                event_id=event_id,
                deadline=deadline,
                created_by=created_by,
                responsible_id=responsible_id,
                description=description,
                format_specs=format_specs,
                priority=priority,
                activity_id=activity_id,
                status="pending",
                created_at=datetime.utcnow()
            )
            
            self.db.add(delivery)
            self.db.commit()
            logger.info(f"Nova entrega criada: {title} (ID: {delivery.id})")
            return delivery
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao criar entrega: {str(e)}")
            raise
            
    def update_delivery(self, 
                       delivery_id: int, 
                       title: Optional[str] = None, 
                       deadline: Optional[datetime] = None, 
                       responsible_id: Optional[int] = None, 
                       description: Optional[str] = None, 
                       format_specs: Optional[str] = None, 
                       priority: Optional[int] = None, 
                       activity_id: Optional[int] = None) -> Delivery:
        """Atualizar informações de uma entrega
        
        Args:
            delivery_id: ID da entrega
            title: Novo título
            deadline: Novo prazo
            responsible_id: Novo responsável
            description: Nova descrição
            format_specs: Novas especificações
            priority: Nova prioridade
            activity_id: Nova atividade relacionada
            
        Returns:
            Objeto da entrega atualizada
            
        Raises:
            ValueError: Se a entrega não for encontrada ou dados inválidos
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            delivery = self.db.query(Delivery).get(delivery_id)
            
            if not delivery:
                raise ValueError(f"Entrega com ID {delivery_id} não encontrada")
            
            # Validar prioridade se fornecida
            if priority is not None and (priority < 1 or priority > 5):
                raise ValueError("Prioridade deve ser um valor entre 1 e 5")
                
            # Verificar se o responsável existe, se fornecido
            if responsible_id is not None:
                if responsible_id:  # Pode ser None para remover o responsável
                    responsible = self.db.query(TeamMember).get(responsible_id)
                    if not responsible:
                        raise ValueError(f"Membro responsável com ID {responsible_id} não encontrado")
                
            # Verificar se a atividade existe e pertence ao evento, se fornecida
            if activity_id is not None:
                if activity_id:  # Pode ser None para remover a atividade
                    activity = self.db.query(Activity).join(Activity.stage).filter(
                        Activity.id == activity_id,
                        Activity.stage.has(event_id=delivery.event_id)
                    ).first()
                    
                    if not activity:
                        raise ValueError(f"Atividade com ID {activity_id} não encontrada ou não pertence ao evento")
                
            # Atualizar campos se fornecidos
            if title is not None:
                delivery.title = title
            if deadline is not None:
                delivery.deadline = deadline
            if responsible_id is not None:
                delivery.responsible_id = responsible_id
            if description is not None:
                delivery.description = description
            if format_specs is not None:
                delivery.format_specs = format_specs
            if priority is not None:
                delivery.priority = priority
            if activity_id is not None:
                delivery.activity_id = activity_id
                
            self.db.commit()
            logger.info(f"Entrega atualizada: {delivery.title} (ID: {delivery_id})")
            return delivery
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar entrega: {str(e)}")
            raise
            
    def delete_delivery(self, delivery_id: int) -> bool:
        """Excluir uma entrega e todos os arquivos associados
        
        Args:
            delivery_id: ID da entrega
            
        Returns:
            True se excluída com sucesso
            
        Raises:
            ValueError: Se a entrega não for encontrada
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            delivery = self.db.query(Delivery).get(delivery_id)
            
            if not delivery:
                raise ValueError(f"Entrega com ID {delivery_id} não encontrada")
                
            # Obter arquivos para exclusão física
            files = self.db.query(DeliveryFile).filter(DeliveryFile.delivery_id == delivery_id).all()
            
            # Excluir entrega (e em cascade os arquivos e comentários)
            self.db.delete(delivery)
            self.db.commit()
            
            # Excluir arquivos físicos
            for file in files:
                self._delete_file(file.filepath)
                
            logger.info(f"Entrega excluída: {delivery.title} (ID: {delivery_id})")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir entrega: {str(e)}")
            raise
            
    def update_status(self, 
                      delivery_id: int, 
                      status: str, 
                      user_id: int,
                      comment: Optional[str] = None) -> Optional[Delivery]:
        """Atualizar status de uma entrega
        
        Args:
            delivery_id: ID da entrega
            status: Novo status (deve ser um dos VALID_STATUSES)
            user_id: ID do usuário que está atualizando
            comment: Comentário opcional sobre a mudança
            
        Returns:
            Objeto Delivery atualizado
            
        Raises:
            ValueError: Se o status não for válido
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            # Validar se o status é válido
            if status not in self.VALID_STATUSES:
                valid_statuses = ", ".join(self.VALID_STATUSES)
                raise ValueError(f"Status inválido: {status}. Status válidos: {valid_statuses}")
                
            # Buscar a entrega
            delivery = self.db.query(Delivery).get(delivery_id)
            if not delivery:
                raise ValueError(f"Entrega com ID {delivery_id} não encontrada")
                
            # Se não houve mudança, só retornar
            if delivery.status == status:
                return delivery
                
            # Registrar status antigo para log
            old_status = delivery.status
                
            # Atualizar status
            delivery.status = status
            delivery.updated_at = datetime.now()
            
            # Adicionar comentário sobre a mudança, se fornecido
            if comment and comment.strip():
                # Criar comentário sobre a mudança
                status_map = {
                    "pending": "Pendente",
                    "in_progress": "Em Progresso",
                    "review": "Em Revisão",
                    "approved": "Aprovado",
                    "published": "Publicado",
                    "rejected": "Rejeitado"
                }
                status_note = f"Status alterado: {status_map.get(old_status, old_status)} → {status_map.get(status, status)}"
                
                delivery_comment = DeliveryComment(
                    delivery_id=delivery_id,
                    user_id=user_id,
                    comment=f"{status_note}\n\n{comment}",
                    timestamp=datetime.now(),
                    is_system=False
                )
                self.db.add(delivery_comment)
            else:
                # Criar um comentário automático sobre a mudança
                status_map = {
                    "pending": "Pendente",
                    "in_progress": "Em Progresso",
                    "review": "Em Revisão",
                    "approved": "Aprovado",
                    "published": "Publicado",
                    "rejected": "Rejeitado"
                }
                status_note = f"Status alterado: {status_map.get(old_status, old_status)} → {status_map.get(status, status)}"
                
                delivery_comment = DeliveryComment(
                    delivery_id=delivery_id,
                    user_id=user_id,
                    comment=status_note,
                    timestamp=datetime.now(),
                    is_system=True
                )
                self.db.add(delivery_comment)
                
            # Salvar alterações
            self.db.commit()
            
            logger.info(f"Status da entrega {delivery_id} atualizado: {old_status} → {status}")
            return delivery
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar status: {str(e)}")
            raise
            
    def add_comment(self, delivery_id: int, user_id: int, comment: str, timecode: Optional[str] = None) -> DeliveryComment:
        """Adicionar comentário/feedback sobre entrega
        
        Args:
            delivery_id: ID da entrega
            user_id: ID do usuário comentando
            comment: Texto do comentário
            timecode: Timecode relacionado ao comentário (formato HH:MM:SS:FF)
            
        Returns:
            Objeto do comentário criado
            
        Raises:
            ValueError: Se a entrega não for encontrada ou dados inválidos
            SQLAlchemyError: Se houver erro no banco de dados
        """
        if not comment or not comment.strip():
            raise ValueError("Comentário não pode estar vazio")
            
        # Validar formato do timecode se fornecido
        if timecode:
            import re
            if not re.match(r'^\d{2}:\d{2}:\d{2}(:\d{2})?$', timecode):
                raise ValueError("Formato de timecode inválido. Use HH:MM:SS ou HH:MM:SS:FF")
            
        try:
            # Verificar se a entrega existe
            delivery = self.db.query(Delivery).get(delivery_id)
            if not delivery:
                raise ValueError(f"Entrega com ID {delivery_id} não encontrada")
                
            # Verificar se o usuário existe
            user = self.db.query(User).get(user_id)
            if not user:
                raise ValueError(f"Usuário com ID {user_id} não encontrado")
                
            # Criar comentário
            new_comment = DeliveryComment(
                delivery_id=delivery_id,
                user_id=user_id,
                comment=comment.strip(),
                timecode=timecode,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(new_comment)
            self.db.commit()
            logger.info(f"Comentário adicionado à entrega {delivery_id}")
            return new_comment
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao adicionar comentário: {str(e)}")
            raise
            
    def get_comments(self, delivery_id: int, newest_first: bool = False) -> List[DeliveryComment]:
        """Obter comentários de uma entrega
        
        Args:
            delivery_id: ID da entrega
            newest_first: Se True, retorna comentários mais recentes primeiro
            
        Returns:
            Lista de objetos DeliveryComment
        """
        try:
            query = self.db.query(DeliveryComment) \
                .filter(DeliveryComment.delivery_id == delivery_id) \
                .options(joinedload(DeliveryComment.user))
                
            if newest_first:
                query = query.order_by(desc(DeliveryComment.timestamp))
            else:
                query = query.order_by(asc(DeliveryComment.timestamp))
                
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar comentários: {str(e)}")
            return []
            
    def upload_file(self, 
                   delivery_id: int, 
                   file_path: str, 
                   user_id: int, 
                   version: Optional[int] = None, 
                   is_final: bool = False, 
                   file_type: Optional[str] = None, 
                   metadata: Optional[Dict] = None) -> DeliveryFile:
        """Associar arquivo à entrega
        
        Args:
            delivery_id: ID da entrega
            file_path: Caminho do arquivo original
            user_id: ID do usuário que está fazendo upload
            version: Versão do arquivo (calculada automaticamente se None)
            is_final: Indica se é versão final
            file_type: Tipo de arquivo (video, image, audio, document)
            metadata: Metadados do arquivo
            
        Returns:
            Objeto do arquivo criado
            
        Raises:
            ValueError: Se a entrega não for encontrada ou arquivo inválido
            IOError: Se houver erro no processamento do arquivo
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            # Verificar se a entrega existe
            delivery = self.db.query(Delivery).get(delivery_id)
            if not delivery:
                raise ValueError(f"Entrega com ID {delivery_id} não encontrada")
                
            # Verificar se o usuário existe
            user = self.db.query(User).get(user_id)
            if not user:
                raise ValueError(f"Usuário com ID {user_id} não encontrado")
                
            # Verificar se o arquivo existe
            if not os.path.exists(file_path):
                raise ValueError(f"Arquivo não encontrado: {file_path}")
                
            # Se tipo não especificado, tentar inferir
            if not file_type:
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.mp4', '.mov', '.avi', '.wmv', '.mkv']:
                    file_type = 'video'
                elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                    file_type = 'image'
                elif ext in ['.mp3', '.wav', '.ogg', '.aac', '.flac']:
                    file_type = 'audio'
                else:
                    file_type = 'document'
                    
            # Obter próxima versão se não especificada
            if version is None:
                latest_version = self.db.query(DeliveryFile) \
                    .filter(DeliveryFile.delivery_id == delivery_id) \
                    .order_by(desc(DeliveryFile.version)) \
                    .first()
                    
                version = 1 if not latest_version else latest_version.version + 1
                
            # Preparar nome de arquivo para armazenamento
            original_filename = os.path.basename(file_path)
            filename_parts = os.path.splitext(original_filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            safe_filename = f"{delivery_id}_{version}_{timestamp}_{filename_parts[0].replace(' ', '_')}{filename_parts[1]}"
            
            # Criar estrutura de diretório
            storage_dir = os.path.join(self.upload_path, str(delivery.event_id), str(delivery_id))
            os.makedirs(storage_dir, exist_ok=True)
            
            # Destino final do arquivo
            destination_path = os.path.join(storage_dir, safe_filename)
            
            # Copiar arquivo para destino final
            shutil.copy2(file_path, destination_path)
            
            # Obter tamanho do arquivo
            file_size = os.path.getsize(destination_path)
            
            # Extrair metadados técnicos para mídia, se possível
            duration = None
            try:
                if file_type in ['video', 'audio']:
                    # Tentar extrair duração com pymediainfo se disponível
                    import pymediainfo
                    media_info = pymediainfo.MediaInfo.parse(destination_path)
                    for track in media_info.tracks:
                        if track.track_type in ['General', 'Video', 'Audio']:
                            if hasattr(track, 'duration'):
                                duration = int(track.duration / 1000)  # Converter ms para segundos
                                break
            except (ImportError, Exception) as media_error:
                logger.warning(f"Não foi possível extrair metadados técnicos: {str(media_error)}")
            
            # Converter metadata para JSON se for dict
            technical_metadata = json.dumps(metadata) if metadata else None
            
            # Criar registro no banco de dados
            delivery_file = DeliveryFile(
                delivery_id=delivery_id,
                filename=original_filename,
                filepath=destination_path,
                file_type=file_type,
                version=version,
                upload_time=datetime.utcnow(),
                uploaded_by=user_id,
                file_size=file_size,
                duration=duration,
                is_final=is_final,
                technical_metadata=technical_metadata
            )
            
            self.db.add(delivery_file)
            
            # Atualizar status da entrega se for final ou se for primeiro arquivo
            if is_final:
                if delivery.status == "pending" or delivery.status == "in_progress":
                    delivery.status = "review"
            elif delivery.status == "pending":
                delivery.status = "in_progress"
                
            self.db.commit()
            
            logger.info(f"Arquivo '{original_filename}' v{version} carregado para entrega {delivery_id}")
            return delivery_file
            
        except (IOError, OSError) as e:
            logger.error(f"Erro de I/O ao processar arquivo: {str(e)}")
            # Tentar limpar arquivo se foi criado
            if 'destination_path' in locals() and os.path.exists(destination_path):
                try:
                    os.remove(destination_path)
                except:
                    pass
                    
            raise IOError(f"Erro ao processar arquivo: {str(e)}")
            
        except SQLAlchemyError as e:
            self.db.rollback()
            # Tentar limpar arquivo se foi criado
            if 'destination_path' in locals() and os.path.exists(destination_path):
                try:
                    os.remove(destination_path)
                except:
                    pass
                    
            logger.error(f"Erro de banco de dados ao registrar arquivo: {str(e)}")
            raise
            
    def get_files(self, delivery_id: int) -> List[DeliveryFile]:
        """Obter arquivos de uma entrega
        
        Args:
            delivery_id: ID da entrega
            
        Returns:
            Lista de objetos DeliveryFile ordenados por versão (mais recente primeiro)
        """
        try:
            return self.db.query(DeliveryFile) \
                .filter(DeliveryFile.delivery_id == delivery_id) \
                .options(joinedload(DeliveryFile.uploader)) \
                .order_by(desc(DeliveryFile.version)) \
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar arquivos: {str(e)}")
            return []
            
    def get_file(self, file_id: int) -> Optional[DeliveryFile]:
        """Obter arquivo específico
        
        Args:
            file_id: ID do arquivo
            
        Returns:
            Objeto do arquivo ou None se não encontrado
        """
        try:
            return self.db.query(DeliveryFile) \
                .options(joinedload(DeliveryFile.uploader)) \
                .filter(DeliveryFile.id == file_id) \
                .first()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar arquivo id={file_id}: {str(e)}")
            return None
            
    def delete_file(self, file_id: int) -> bool:
        """Excluir arquivo
        
        Args:
            file_id: ID do arquivo
            
        Returns:
            True se excluído com sucesso
            
        Raises:
            ValueError: Se o arquivo não for encontrado
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            file = self.db.query(DeliveryFile).get(file_id)
            
            if not file:
                raise ValueError(f"Arquivo com ID {file_id} não encontrado")
                
            # Armazenar caminho do arquivo para exclusão posterior
            filepath = file.filepath
            
            # Excluir registro do banco
            self.db.delete(file)
            self.db.commit()
            
            # Excluir arquivo físico
            self._delete_file(filepath)
            
            logger.info(f"Arquivo {file.filename} (ID: {file_id}) excluído")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir arquivo: {str(e)}")
            raise
            
    def _delete_file(self, filepath: str) -> bool:
        """Excluir arquivo físico
        
        Args:
            filepath: Caminho do arquivo
            
        Returns:
            True se excluído com sucesso, False se não existir
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.debug(f"Arquivo físico excluído: {filepath}")
                return True
            logger.debug(f"Arquivo físico não encontrado para exclusão: {filepath}")
            return False
        except OSError as e:
            logger.error(f"Erro ao excluir arquivo físico {filepath}: {str(e)}")
            return False
            
    def get_pending_deliveries(self, event_id: Optional[int] = None, days_ahead: int = 7) -> List[Delivery]:
        """Obter entregas pendentes próximas do prazo
        
        Args:
            event_id: Filtrar por evento
            days_ahead: Dias à frente para considerar
            
        Returns:
            Lista de objetos Delivery
        """
        try:
            now = datetime.utcnow()
            deadline = now + timedelta(days=days_ahead)
            
            query = self.db.query(Delivery) \
                .filter(
                    Delivery.deadline <= deadline,
                    Delivery.status.in_(["pending", "in_progress", "review"])
                ) \
                .order_by(Delivery.deadline)
                
            if event_id:
                query = query.filter(Delivery.event_id == event_id)
                
            # Eager loading para performance
            query = query.options(
                joinedload(Delivery.responsible),
                joinedload(Delivery.activity),
                joinedload(Delivery.event)
            )
            
            return query.all()
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar entregas pendentes: {str(e)}")
            return []
            
    def get_late_deliveries(self, event_id: Optional[int] = None) -> List[Delivery]:
        """Obter entregas atrasadas (prazo já passou e ainda não concluídas)
        
        Args:
            event_id: Filtrar por evento
            
        Returns:
            Lista de objetos Delivery
        """
        try:
            now = datetime.utcnow()
            
            query = self.db.query(Delivery) \
                .filter(
                    Delivery.deadline < now,
                    Delivery.status.in_(["pending", "in_progress", "review"])
                ) \
                .order_by(Delivery.deadline)
                
            if event_id:
                query = query.filter(Delivery.event_id == event_id)
                
            # Eager loading para performance
            query = query.options(
                joinedload(Delivery.responsible),
                joinedload(Delivery.event)
            )
            
            return query.all()
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar entregas atrasadas: {str(e)}")
            return []
            
    def get_delivery_stats(self, event_id: int) -> Dict:
        """Obter estatísticas de entregas para um evento
        
        Args:
            event_id: ID do evento
            
        Returns:
            Dicionário com estatísticas
        """
        try:
            # Total de entregas
            total_count = self.db.query(Delivery) \
                .filter(Delivery.event_id == event_id) \
                .count()
                
            # Contagem por status
            status_counts = {}
            for status in self.VALID_STATUSES:
                count = self.db.query(Delivery) \
                    .filter(Delivery.event_id == event_id, Delivery.status == status) \
                    .count()
                status_counts[status] = count
                
            # Entregas atrasadas
            now = datetime.utcnow()
            late_count = self.db.query(Delivery) \
                .filter(
                    Delivery.event_id == event_id,
                    Delivery.deadline < now,
                    Delivery.status.in_(["pending", "in_progress", "review"])
                ) \
                .count()
                
            # Entregas próximas do prazo (próximos 3 dias)
            deadline_soon = now + timedelta(days=3)
            upcoming_count = self.db.query(Delivery) \
                .filter(
                    Delivery.event_id == event_id,
                    Delivery.deadline > now,
                    Delivery.deadline <= deadline_soon,
                    Delivery.status.in_(["pending", "in_progress", "review"])
                ) \
                .count()
                
            # Calcular taxas
            completion_rate = (status_counts.get("published", 0) + status_counts.get("approved", 0)) / total_count if total_count > 0 else 0
            problem_rate = status_counts.get("rejected", 0) / total_count if total_count > 0 else 0
            
            return {
                "total": total_count,
                "by_status": status_counts,
                "late": late_count,
                "upcoming_deadline": upcoming_count,
                "completion_rate": round(completion_rate * 100, 1),  # Porcentagem
                "problem_rate": round(problem_rate * 100, 1),  # Porcentagem
                "timestamp": datetime.utcnow()
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {
                "total": 0,
                "by_status": {},
                "late": 0,
                "upcoming_deadline": 0,
                "completion_rate": 0,
                "problem_rate": 0,
                "timestamp": datetime.utcnow(),
                "error": str(e)
            }
            
    def get_team_performance_stats(self, event_id: Optional[int] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """Obter estatísticas de performance da equipe
        
        Args:
            event_id: Filtrar por evento específico
            start_date: Data de início para o período de análise
            end_date: Data de fim para o período de análise
            
        Returns:
            Dicionário com estatísticas de performance por membro
        """
        try:
            # Base query para entregas concluídas
            query = self.db.query(
                Delivery.responsible_id,
                TeamMember.name,
                TeamMember.role,
                Delivery.status
            ).join(
                TeamMember, Delivery.responsible_id == TeamMember.id
            )
            
            # Aplicar filtros
            if event_id:
                query = query.filter(Delivery.event_id == event_id)
                
            if start_date:
                query = query.filter(Delivery.created_at >= start_date)
                
            if end_date:
                query = query.filter(Delivery.created_at <= end_date)
            
            # Executar query e processar resultado
            results = query.all()
            
            # Agrupar resultados por membro
            stats = {}
            for responsible_id, name, role, status in results:
                if not responsible_id:
                    continue
                    
                if responsible_id not in stats:
                    stats[responsible_id] = {
                        "name": name,
                        "role": role,
                        "total": 0,
                        "completed": 0,
                        "on_time": 0,
                        "late": 0,
                        "rejected": 0,
                        "in_progress": 0,
                        "completion_rate": 0
                    }
                
                stats[responsible_id]["total"] += 1
                
                if status in ["approved", "published"]:
                    stats[responsible_id]["completed"] += 1
                    
                    # Verificar se foi entregue no prazo - requer query adicional
                    delivery = self.db.query(Delivery) \
                        .filter(
                            Delivery.responsible_id == responsible_id,
                            Delivery.status == status
                        ) \
                        .first()
                        
                    if delivery and delivery.published_at and delivery.published_at <= delivery.deadline:
                        stats[responsible_id]["on_time"] += 1
                    else:
                        stats[responsible_id]["late"] += 1
                        
                elif status == "rejected":
                    stats[responsible_id]["rejected"] += 1
                else:
                    stats[responsible_id]["in_progress"] += 1
            
            # Calcular taxas
            for member_id in stats:
                if stats[member_id]["total"] > 0:
                    stats[member_id]["completion_rate"] = round(
                        (stats[member_id]["completed"] / stats[member_id]["total"]) * 100, 1
                    )
            
            return stats
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao obter estatísticas de performance: {str(e)}")
            return {}