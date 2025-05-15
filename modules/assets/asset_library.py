#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Biblioteca de Assets Audiovisuais
Data: 2025-05-15
"""

import os
import logging
import shutil
import json
import mimetypes
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Union, Set, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_, func, desc
from sqlalchemy.orm import joinedload

from core.database import Asset, AssetFolder, Tag, asset_tags, User, Event

logger = logging.getLogger(__name__)

class AssetLibrary:
    """Classe para gerenciamento da biblioteca de assets audiovisuais"""
    
    # Definição dos tipos de asset suportados
    ASSET_TYPES = {
        "video": [".mp4", ".mov", ".avi", ".wmv", ".mkv", ".webm", ".m4v", ".mpg", ".mpeg"],
        "audio": [".mp3", ".wav", ".ogg", ".aac", ".flac", ".m4a", ".wma"],
        "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg", ".psd"],
        "document": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
        "graphic": [".ai", ".eps", ".cdr", ".indd", ".afdesign", ".sketch"],
        "subtitle": [".srt", ".vtt", ".ass", ".sub"],
        "project": [".prproj", ".aep", ".drp", ".fcpxml", ".dav"],
        "template": [".mogrt", ".aep", ".prproj", ".drp"]
    }
    
    def __init__(self, db_session, storage_path="uploads/assets"):
        """Inicializa a biblioteca de assets
        
        Args:
            db_session: Sessão do SQLAlchemy para acesso ao banco de dados
            storage_path (str): Caminho para armazenamento de arquivos
        """
        self.db = db_session
        self.storage_path = storage_path
        
        # Garantir que o diretório de armazenamento existe
        os.makedirs(storage_path, exist_ok=True)
        
        # Inicializar mimetypes
        mimetypes.init()
        
    def add_asset(self, 
                 name: str, 
                 file_path: str, 
                 asset_type: Optional[str] = None, 
                 description: Optional[str] = None, 
                 event_id: Optional[int] = None, 
                 folder_id: Optional[int] = None, 
                 created_by: Optional[int] = None, 
                 tags: Optional[List] = None) -> Asset:
        """Adicionar novo asset à biblioteca
        
        Args:
            name: Nome do asset
            file_path: Caminho do arquivo original
            asset_type: Tipo de asset (inferido do arquivo se None)
            description: Descrição do asset
            event_id: ID do evento relacionado
            folder_id: ID da pasta onde armazenar
            created_by: ID do usuário que está adicionando
            tags: Lista de tags ou IDs de tags
            
        Returns:
            Objeto do novo asset criado
            
        Raises:
            ValueError: Se o arquivo não existir ou dados forem inválidos
            IOError: Se houver erro no processamento do arquivo
            SQLAlchemyError: Se houver erro no banco de dados
        """
        if not name or not file_path:
            raise ValueError("Nome e caminho do arquivo são obrigatórios")
            
        if not os.path.exists(file_path):
            raise ValueError(f"Arquivo não encontrado: {file_path}")
            
        # Verificar usuário
        if created_by:
            user = self.db.query(User).get(created_by)
            if not user:
                raise ValueError(f"Usuário com ID {created_by} não encontrado")
                
        # Verificar evento
        if event_id:
            event = self.db.query(Event).get(event_id)
            if not event:
                raise ValueError(f"Evento com ID {event_id} não encontrado")
                
        # Verificar pasta
        if folder_id:
            folder = self.db.query(AssetFolder).get(folder_id)
            if not folder:
                raise ValueError(f"Pasta com ID {folder_id} não encontrada")
                
        try:
            # Determinar tipo de asset se não fornecido
            if not asset_type:
                asset_type = self._determine_asset_type(file_path)
            
            # Preparar nome de arquivo para armazenamento
            original_filename = os.path.basename(file_path)
            filename_parts = os.path.splitext(original_filename)
            unique_id = uuid.uuid4().hex[:8]
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            safe_filename = f"{timestamp}_{unique_id}_{filename_parts[0].replace(' ', '_')}{filename_parts[1]}"
            
            # Definir diretório de destino
            if event_id:
                storage_dir = os.path.join(self.storage_path, f"event_{event_id}")
            else:
                storage_dir = os.path.join(self.storage_path, "general")
                
            os.makedirs(storage_dir, exist_ok=True)
            
            # Destino final do arquivo
            destination_path = os.path.join(storage_dir, safe_filename)
            
            # Copiar arquivo para destino final
            shutil.copy2(file_path, destination_path)
            
            # Obter tamanho do arquivo
            file_size = os.path.getsize(destination_path)
            
            # Extrair metadados do arquivo
            metadata = self._extract_metadata(destination_path, asset_type)
            
            # Criar asset no banco de dados
            asset = Asset(
                name=name,
                file_path=destination_path,
                asset_type=asset_type,
                description=description,
                event_id=event_id,
                folder_id=folder_id,
                created_at=datetime.utcnow(),
                created_by=created_by,
                file_size=file_size,
                technical_metadata=json.dumps(metadata) if metadata else None
            )
            
            # Extrair duração para arquivos de mídia
            if metadata and 'duration' in metadata:
                asset.duration = int(float(metadata['duration']))
            
            self.db.add(asset)
            self.db.flush()  # Para obter o ID do asset
            
            # Processar tags
            if tags:
                self._add_tags_to_asset(asset, tags)
                
            self.db.commit()
            logger.info(f"Asset '{name}' adicionado com sucesso (ID: {asset.id})")
            return asset
            
        except IOError as e:
            logger.error(f"Erro de I/O ao processar arquivo: {str(e)}")
            if 'destination_path' in locals() and os.path.exists(destination_path):
                os.remove(destination_path)
            raise IOError(f"Erro ao processar arquivo: {str(e)}")
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro de banco de dados: {str(e)}")
            if 'destination_path' in locals() and os.path.exists(destination_path):
                os.remove(destination_path)
            raise
            
    def update_asset(self, 
                    asset_id: int, 
                    name: Optional[str] = None, 
                    description: Optional[str] = None, 
                    folder_id: Optional[int] = None, 
                    tags: Optional[List] = None) -> Asset:
        """Atualizar informações de um asset
        
        Args:
            asset_id: ID do asset
            name: Novo nome
            description: Nova descrição
            folder_id: Nova pasta
            tags: Nova lista de tags
            
        Returns:
            Objeto do asset atualizado
            
        Raises:
            ValueError: Se o asset não for encontrado
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            asset = self.db.query(Asset).get(asset_id)
            
            if not asset:
                raise ValueError(f"Asset com ID {asset_id} não encontrado")
            
            # Verificar pasta
            if folder_id is not None and folder_id:
                folder = self.db.query(AssetFolder).get(folder_id)
                if not folder:
                    raise ValueError(f"Pasta com ID {folder_id} não encontrada")
                
            # Atualizar campos básicos
            if name:
                asset.name = name
            if description is not None:
                asset.description = description
            if folder_id is not None:
                asset.folder_id = folder_id
                
            # Atualizar tags se fornecidas
            if tags is not None:
                # Limpar tags existentes
                asset.tags = []
                self.db.flush()
                # Adicionar novas tags
                self._add_tags_to_asset(asset, tags)
                
            self.db.commit()
            logger.info(f"Asset ID {asset_id} atualizado")
            return asset
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar asset: {str(e)}")
            raise
            
    def delete_asset(self, asset_id: int) -> bool:
        """Excluir asset
        
        Args:
            asset_id: ID do asset
            
        Returns:
            True se excluído com sucesso
            
        Raises:
            ValueError: Se o asset não for encontrado
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            asset = self.db.query(Asset).get(asset_id)
            
            if not asset:
                raise ValueError(f"Asset com ID {asset_id} não encontrado")
                
            # Excluir arquivo físico
            file_path = asset.file_path
            file_deleted = False
            
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    file_deleted = True
                except OSError as e:
                    logger.warning(f"Não foi possível excluir o arquivo físico {file_path}: {str(e)}")
                
            # Excluir do banco
            self.db.delete(asset)
            self.db.commit()
            
            logger.info(f"Asset ID {asset_id} excluído" + 
                      (", arquivo físico removido" if file_deleted else ", arquivo físico não encontrado"))
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir asset: {str(e)}")
            raise
            
    def get_asset(self, asset_id: int) -> Optional[Asset]:
        """Obter asset específico
        
        Args:
            asset_id: ID do asset
            
        Returns:
            Asset: Objeto do asset ou None se não encontrado
        """
        try:
            return self.db.query(Asset).options(
                joinedload(Asset.tags),
                joinedload(Asset.folder),
                joinedload(Asset.event)
            ).get(asset_id)
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar asset id={asset_id}: {str(e)}")
            return None
    
    def get_assets(self, 
                  folder_id: Optional[int] = None, 
                  event_id: Optional[int] = None, 
                  asset_type: Optional[str] = None, 
                  tags: Optional[List] = None, 
                  sort_by: str = "created_at",
                  descending: bool = True,
                  limit: Optional[int] = None,
                  offset: Optional[int] = None) -> List[Asset]:
        """Obter assets com filtros
        
        Args:
            folder_id: Filtrar por pasta
            event_id: Filtrar por evento
            asset_type: Filtrar por tipo
            tags: Filtrar por tags
            sort_by: Campo para ordenar
            descending: Se True, ordena em ordem descendente
            limit: Limitar número de resultados
            offset: Offset para paginação
            
        Returns:
            Lista de objetos Asset
        """
        try:
            query = self.db.query(Asset).options(
                joinedload(Asset.tags),
                joinedload(Asset.folder)
            )
            
            # Aplicar filtros
            if folder_id is not None:
                query = query.filter(Asset.folder_id == folder_id)
            if event_id is not None:
                query = query.filter(Asset.event_id == event_id)
            if asset_type:
                query = query.filter(Asset.asset_type == asset_type)
                
            # Filtrar por tags
            if tags:
                for tag in tags:
                    # Pode ser ID ou nome da tag
                    if isinstance(tag, int) or (isinstance(tag, str) and tag.isdigit()):
                        tag_id = int(tag)
                        query = query.filter(Asset.tags.any(Tag.id == tag_id))
                    else:
                        query = query.filter(Asset.tags.any(Tag.name == tag))
            
            # Aplicar ordenação
            if sort_by == "created_at":
                order_col = Asset.created_at
            elif sort_by == "name":
                order_col = Asset.name
            elif sort_by == "type":
                order_col = Asset.asset_type
            elif sort_by == "size":
                order_col = Asset.file_size
            else:
                order_col = Asset.created_at
                
            if descending:
                query = query.order_by(desc(order_col))
            else:
                query = query.order_by(order_col)
            
            # Aplicar limite e offset
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
                
            return query.all()
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar assets: {str(e)}")
            return []
            
    def search_assets(self, 
                     query_text: str, 
                     asset_type: Optional[str] = None, 
                     tags: Optional[List] = None, 
                     event_id: Optional[int] = None,
                     folder_id: Optional[int] = None,
                     limit: Optional[int] = 50) -> List[Asset]:
        """Buscar assets com filtros
        
        Args:
            query_text: Texto para busca
            asset_type: Filtrar por tipo
            tags: Filtrar por tags
            event_id: Filtrar por evento
            folder_id: Filtrar por pasta
            limit: Limitar número de resultados
            
        Returns:
            Lista de objetos Asset
        """
        try:
            search_query = self.db.query(Asset).options(
                joinedload(Asset.tags),
                joinedload(Asset.folder)
            )
            
            # Aplicar busca por texto
            if query_text:
                search_pattern = f"%{query_text}%"
                search_query = search_query.filter(
                    or_(
                        Asset.name.ilike(search_pattern),
                        Asset.description.ilike(search_pattern)
                    )
                )
                
            # Aplicar filtros adicionais
            if asset_type:
                search_query = search_query.filter(Asset.asset_type == asset_type)
            if event_id is not None:
                search_query = search_query.filter(Asset.event_id == event_id)
            if folder_id is not None:
                search_query = search_query.filter(Asset.folder_id == folder_id)
                
            # Filtrar por tags
            if tags:
                for tag in tags:
                    if isinstance(tag, int) or (isinstance(tag, str) and tag.isdigit()):
                        tag_id = int(tag)
                        search_query = search_query.filter(Asset.tags.any(Tag.id == tag_id))
                    else:
                        search_query = search_query.filter(Asset.tags.any(Tag.name == tag))
            
            # Ordenar por relevância para a busca por texto
            if query_text:
                # Primeiro os que têm match exato no nome
                # Depois os que começam com o termo
                # Depois os mais recentes
                search_query = search_query.order_by(
                    (Asset.name == query_text.strip()).desc(),  
                    Asset.name.ilike(f"{query_text.strip()}%").desc(),
                    Asset.created_at.desc()
                )
            else:
                # Se não há busca por texto, ordenar por data mais recente
                search_query = search_query.order_by(Asset.created_at.desc())
                
            # Limitar resultados
            search_query = search_query.limit(limit)
                
            return search_query.all()
            
        except SQLAlchemyError as e:
            logger.error(f"Erro na busca de assets: {str(e)}")
            return []
            
    def create_folder(self, name: str, parent_id: Optional[int] = None, created_by: Optional[int] = None) -> AssetFolder:
        """Criar pasta organizacional
        
        Args:
            name: Nome da pasta
            parent_id: ID da pasta pai
            created_by: ID do usuário criador
            
        Returns:
            AssetFolder: Objeto da pasta criada
            
        Raises:
            ValueError: Se o nome não for fornecido ou pasta pai não existir
            SQLAlchemyError: Se houver erro no banco de dados
        """
        if not name:
            raise ValueError("Nome da pasta é obrigatório")
            
        try:
            # Verificar se pasta pai existe (se especificado)
            if parent_id and not self.db.query(AssetFolder).get(parent_id):
                raise ValueError(f"Pasta pai com ID {parent_id} não encontrada")
                
            # Verificar se já existe pasta com mesmo nome no mesmo nível
            existing_folder = self.db.query(AssetFolder).filter(
                AssetFolder.name == name,
                AssetFolder.parent_id == parent_id
            ).first()
            
            if existing_folder:
                raise ValueError(f"Já existe uma pasta chamada '{name}' neste local")
                
            # Criar pasta
            folder = AssetFolder(
                name=name,
                parent_id=parent_id,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            self.db.add(folder)
            self.db.commit()
            logger.info(f"Pasta '{name}' criada (ID: {folder.id})")
            return folder
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao criar pasta: {str(e)}")
            raise
            
    def update_folder(self, folder_id: int, name: Optional[str] = None, parent_id: Optional[int] = None) -> AssetFolder:
        """Atualizar informações da pasta
        
        Args:
            folder_id: ID da pasta
            name: Novo nome
            parent_id: Nova pasta pai
            
        Returns:
            AssetFolder: Objeto da pasta atualizada
            
        Raises:
            ValueError: Se a pasta não for encontrada
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            folder = self.db.query(AssetFolder).get(folder_id)
            
            if not folder:
                raise ValueError(f"Pasta com ID {folder_id} não encontrada")
                
            if name:
                # Verificar se o novo nome já existe no mesmo nível
                existing_folder = self.db.query(AssetFolder).filter(
                    AssetFolder.name == name,
                    AssetFolder.parent_id == folder.parent_id,
                    AssetFolder.id != folder_id
                ).first()
                
                if existing_folder:
                    raise ValueError(f"Já existe uma pasta chamada '{name}' neste local")
                    
                folder.name = name
                
            # Verificar se não está tentando mover para um filho dela mesma
            if parent_id is not None and parent_id != folder.parent_id:
                # Verificar se a pasta pai existe
                if parent_id and not self.db.query(AssetFolder).get(parent_id):
                    raise ValueError(f"Pasta pai com ID {parent_id} não encontrada")
                    
                # Verificar se não está tentando mover para um descendente
                if self._is_descendant(folder_id, parent_id):
                    raise ValueError("Não é possível mover uma pasta para dentro de si mesma ou para um de seus descendentes")
                    
                folder.parent_id = parent_id
                
            self.db.commit()
            logger.info(f"Pasta ID {folder_id} atualizada")
            return folder
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar pasta: {str(e)}")
            raise
            
    def delete_folder(self, folder_id: int, recursive: bool = False) -> bool:
        """Excluir pasta
        
        Args:
            folder_id: ID da pasta
            recursive: Se True, exclui subpastas e todos os assets
            
        Returns:
            True se excluída com sucesso
            
        Raises:
            ValueError: Se a pasta não for encontrada ou tiver conteúdo e recursive=False
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            folder = self.db.query(AssetFolder).get(folder_id)
            
            if not folder:
                raise ValueError(f"Pasta com ID {folder_id} não encontrada")
                
            # Verificar se a pasta está vazia
            has_subfolders = self.db.query(AssetFolder).filter(AssetFolder.parent_id == folder_id).count() > 0
            has_assets = self.db.query(Asset).filter(Asset.folder_id == folder_id).count() > 0
            
            if (has_subfolders or has_assets) and not recursive:
                raise ValueError("Pasta não está vazia. Use recursive=True para excluir todo o conteúdo")
                
            if recursive:
                # Excluir assets da pasta
                assets = self.db.query(Asset).filter(Asset.folder_id == folder_id).all()
                for asset in assets:
                    self.delete_asset(asset.id)
                    
                # Excluir subpastas recursivamente
                subfolders = self.db.query(AssetFolder).filter(AssetFolder.parent_id == folder_id).all()
                for subfolder in subfolders:
                    self.delete_folder(subfolder.id, recursive=True)
                    
            # Excluir a pasta
            self.db.delete(folder)
            self.db.commit()
            
            logger.info(f"Pasta ID {folder_id} excluída" + (" com todo o conteúdo" if recursive else ""))
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir pasta: {str(e)}")
            raise
            
    def get_folder_structure(self, only_root: bool = False) -> List[AssetFolder]:
        """Obter estrutura de pastas
        
        Args:
            only_root: Se True, retorna apenas pastas raiz
            
        Returns:
            Lista de objetos AssetFolder
        """
        try:
            query = self.db.query(AssetFolder)
            
            if only_root:
                query = query.filter(AssetFolder.parent_id == None)
                
            query = query.order_by(AssetFolder.name)
            
            return query.all()
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao obter estrutura de pastas: {str(e)}")
            return []
            
    def get_folder_contents(self, folder_id: Optional[int] = None) -> Dict[str, List]:
        """Obter conteúdo de uma pasta (subpastas e assets)
        
        Args:
            folder_id: ID da pasta ou None para pastas raiz
            
        Returns:
            Dicionário com 'folders' e 'assets'
        """
        try:
            # Buscar subpastas
            subfolders = self.db.query(AssetFolder).filter(
                AssetFolder.parent_id == folder_id
            ).order_by(AssetFolder.name).all()
            
            # Buscar assets na pasta
            assets = self.db.query(Asset).filter(
                Asset.folder_id == folder_id
            ).order_by(Asset.created_at.desc()).all()
            
            return {
                'folders': subfolders,
                'assets': assets
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao obter conteúdo da pasta: {str(e)}")
            return {'folders': [], 'assets': []}
    
    def create_tag(self, name: str, color: str = "#cccccc") -> Tag:
        """Criar nova tag
        
        Args:
            name: Nome da tag
            color: Código de cor (hex)
            
        Returns:
            Tag: Objeto da tag criada
            
        Raises:
            ValueError: Se o nome não for fornecido ou já existir
            SQLAlchemyError: Se houver erro no banco de dados
        """
        if not name:
            raise ValueError("Nome da tag é obrigatório")
            
        # Validar formato de cor
        if not color.startswith("#") or len(color) != 7:
            raise ValueError("Cor deve estar no formato hexadecimal #RRGGBB")
            
        try:
            # Verificar se já existe tag com mesmo nome
            existing = self.db.query(Tag).filter(Tag.name == name).first()
            if existing:
                return existing
                
            # Criar tag
            tag = Tag(
                name=name,
                color=color
            )
            
            self.db.add(tag)
            self.db.commit()
            logger.info(f"Tag '{name}' criada (ID: {tag.id})")
            return tag
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao criar tag: {str(e)}")
            raise
    
    def update_tag(self, tag_id: int, name: Optional[str] = None, color: Optional[str] = None) -> Tag:
        """Atualizar informações de tag
        
        Args:
            tag_id: ID da tag
            name: Novo nome
            color: Nova cor
            
        Returns:
            Tag: Objeto da tag atualizada
            
        Raises:
            ValueError: Se a tag não for encontrada
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            tag = self.db.query(Tag).get(tag_id)
            
            if not tag:
                raise ValueError(f"Tag com ID {tag_id} não encontrada")
                
            if name:
                # Verificar se já existe outra tag com este nome
                existing = self.db.query(Tag).filter(Tag.name == name, Tag.id != tag_id).first()
                if existing:
                    raise ValueError(f"Já existe uma tag com o nome '{name}'")
                    
                tag.name = name
                
            if color:
                # Validar formato de cor
                if not color.startswith("#") or len(color) != 7:
                    raise ValueError("Cor deve estar no formato hexadecimal #RRGGBB")
                    
                tag.color = color
                
            self.db.commit()
            logger.info(f"Tag ID {tag_id} atualizada")
            return tag
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar tag: {str(e)}")
            raise
            
    def delete_tag(self, tag_id: int) -> bool:
        """Excluir tag
        
        Args:
            tag_id: ID da tag
            
        Returns:
            True se excluída com sucesso
            
        Raises:
            ValueError: Se a tag não for encontrada
            SQLAlchemyError: Se houver erro no banco de dados
        """
        try:
            tag = self.db.query(Tag).get(tag_id)
            
            if not tag:
                raise ValueError(f"Tag com ID {tag_id} não encontrada")
                
            self.db.delete(tag)
            self.db.commit()
            logger.info(f"Tag ID {tag_id} excluída")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir tag: {str(e)}")
            raise
            
    def get_all_tags(self) -> List[Tag]:
        """Obter todas as tags
        
        Returns:
            list: Lista de objetos Tag
        """
        try:
            return self.db.query(Tag).order_by(Tag.name).all()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar tags: {str(e)}")
            return []
            
    def get_tag(self, tag_id: int) -> Optional[Tag]:
        """Obter tag específica
        
        Args:
            tag_id: ID da tag
            
        Returns:
            Tag: Objeto da tag ou None se não encontrada
        """
        try:
            return self.db.query(Tag).get(tag_id)
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar tag id={tag_id}: {str(e)}")
            return None
            
    def get_assets_by_tag(self, tag_id: int, limit: Optional[int] = None) -> List[Asset]:
        """Obter assets com uma tag específica
        
        Args:
            tag_id: ID da tag
            limit: Limitar número de resultados
            
        Returns:
            Lista de objetos Asset
        """
        try:
            query = self.db.query(Asset).filter(Asset.tags.any(Tag.id == tag_id))
            
            if limit:
                query = query.limit(limit)
                
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar assets por tag: {str(e)}")
            return []
            
    def get_popular_tags(self, limit: int = 10) -> List[Dict]:
        """Obter tags mais populares
        
        Args:
            limit: Número máximo de tags para retornar
            
        Returns:
            Lista de dicionários com {id, name, color, count}
        """
        try:
            # Usando SQLAlchemy para contar associações tag-asset
            result = self.db.query(
                Tag.id, Tag.name, Tag.color, func.count(asset_tags.c.asset_id).label('count')
            ).outerjoin(
                asset_tags, Tag.id == asset_tags.c.tag_id
            ).group_by(
                Tag.id
            ).order_by(
                desc('count')
            ).limit(limit).all()
            
            return [{'id': id, 'name': name, 'color': color, 'count': count} for id, name, color, count in result]
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar tags populares: {str(e)}")
            return []
    
    def _add_tags_to_asset(self, asset: Asset, tags: List) -> bool:
        """Adicionar tags a um asset
        
        Args:
            asset: Objeto do asset
            tags: Lista de tags (IDs, nomes ou objetos)
            
        Returns:
            bool: True se operação foi bem sucedida
        """
        try:
            for tag_item in tags:
                # Tag já é um objeto Tag
                if isinstance(tag_item, Tag):
                    asset.tags.append(tag_item)
                    continue
                    
                # Tag é um ID
                if isinstance(tag_item, int) or (isinstance(tag_item, str) and tag_item.isdigit()):
                    tag_id = int(tag_item)
                    tag = self.db.query(Tag).get(tag_id)
                    if tag:
                        asset.tags.append(tag)
                    continue
                    
                # Tag é um nome - buscar ou criar
                tag_name = str(tag_item)
                tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
                
                if not tag:
                    # Criar nova tag
                    tag = Tag(name=tag_name)
                    self.db.add(tag)
                    self.db.flush()
                    
                asset.tags.append(tag)
                
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar tags: {str(e)}")
            return False
            
    def _is_descendant(self, ancestor_id: int, folder_id: int) -> bool:
        """Verificar se uma pasta é descendente de outra
        
        Args:
            ancestor_id: ID da pasta ancestral potencial
            folder_id: ID da pasta a verificar
            
        Returns:
            True se folder_id é descendente de ancestor_id
        """
        if folder_id is None:
            return False
            
        if ancestor_id == folder_id:
            return True
            
        # Obter pasta pai
        folder = self.db.query(AssetFolder).get(folder_id)
        
        if not folder or folder.parent_id is None:
            return False
            
        # Verificar recursivamente
        return self._is_descendant(ancestor_id, folder.parent_id)
    
    def _determine_asset_type(self, file_path: str) -> str:
        """Determinar o tipo de asset baseado na extensão do arquivo
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Tipo do asset (video, audio, image, document, etc.)
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        # Procurar extensão nas categorias de tipo
        for asset_type, extensions in self.ASSET_TYPES.items():
            if ext in extensions:
                return asset_type
                
        # Tentar inferir pelo mime type
        mime_type = mimetypes.guess_type(file_path)[0]
        if mime_type:
            if mime_type.startswith('video/'):
                return 'video'
            elif mime_type.startswith('audio/'):
                return 'audio'
            elif mime_type.startswith('image/'):
                return 'image'
            elif mime_type.startswith('application/pdf'):
                return 'document'
                
        # Padrão como documento
        return 'document'
            
    def _extract_metadata(self, file_path: str, asset_type: str) -> Dict[str, Any]:
        """Extrair metadados do arquivo
        
        Args:
            file_path: Caminho do arquivo
            asset_type: Tipo de asset
            
        Returns:
            Dicionário com metadados ou dicionário vazio em caso de erro
        """
        metadata = {}
        
        try:
            # Obter propriedades básicas do arquivo
            stat_info = os.stat(file_path)
            metadata['file_size'] = stat_info.st_size
            metadata['created'] = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
            metadata['modified'] = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
            
            # Para arquivos de mídia, usar pymediainfo se disponível
            if asset_type in ['video', 'audio', 'image']:
                try:
                    import pymediainfo
                    media_info = pymediainfo.MediaInfo.parse(file_path)
                    
                    for track in media_info.tracks:
                        if track.track_type == 'General':
                            if hasattr(track, 'format'):
                                metadata['format'] = track.format
                            if hasattr(track, 'duration'):
                                metadata['duration'] = track.duration / 1000.0  # Converter para segundos
                            if hasattr(track, 'overall_bit_rate'):
                                metadata['bit_rate'] = track.overall_bit_rate
                            if hasattr(track, 'encoded_date'):
                                metadata['encoded_date'] = track.encoded_date
                                
                        elif track.track_type == 'Video':
                            metadata['width'] = getattr(track, 'width', None)
                            metadata['height'] = getattr(track, 'height', None)
                            metadata['aspect_ratio'] = getattr(track, 'display_aspect_ratio', None)
                            metadata['frame_rate'] = getattr(track, 'frame_rate', None)
                            metadata['codec'] = getattr(track, 'codec', None)
                            metadata['bit_depth'] = getattr(track, 'bit_depth', None)
                            
                        elif track.track_type == 'Audio':
                            metadata['channels'] = getattr(track, 'channel_s', None)
                            metadata['sample_rate'] = getattr(track, 'sampling_rate', None)
                            metadata['audio_codec'] = getattr(track, 'codec', None)
                            metadata['audio_bit_depth'] = getattr(track, 'bit_depth', None)
                            
                        elif track.track_type == 'Image':
                            metadata['width'] = getattr(track, 'width', None)
                            metadata['height'] = getattr(track, 'height', None)
                            metadata['color_space'] = getattr(track, 'color_space', None)
                            
                except ImportError:
                    logger.warning("Módulo pymediainfo não encontrado, metadados limitados.")
                except Exception as e:
                    logger.warning(f"Erro ao extrair metadados com pymediainfo: {str(e)}")
                    
        except Exception as e:
            logger.warning(f"Erro ao extrair metadados: {str(e)}")
            
        return metadata