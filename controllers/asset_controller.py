"""
GONETWORK AI - Controlador de Assets
Implementa a lógica de negócio para gerenciamento da biblioteca de assets (arquivos de mídia)
"""

from PyQt5.QtCore import QObject, pyqtSignal
import os
import shutil
import datetime
import uuid
import json
from PIL import Image
import mimetypes

from controllers import BaseController
from models.asset import Asset, AssetFolder
from models.event import Tag
from models.base import asset_tags
from core.config import settings
from core.logging_manager import get_logger

logger = get_logger(__name__)

class AssetController(BaseController):
    """
    Controlador para gerenciamento de assets (biblioteca de mídia)
    """
    
    # Sinais
    assets_updated = pyqtSignal(list)  # Lista de assets atualizada
    folder_created = pyqtSignal(object)  # Nova pasta criada
    asset_imported = pyqtSignal(object)  # Novo asset importado
    import_progress = pyqtSignal(int, int)  # Progresso atual, total
    thumbnail_generated = pyqtSignal(object)  # Asset com thumbnail gerado
    
    def __init__(self, db_session):
        """
        Inicializa o controlador de assets
        
        Args:
            db_session: Sessão do SQLAlchemy para acesso ao banco de dados
        """
        super().__init__(db_session)
        self.current_filters = {}
        self.thumbnail_sizes = [(128, 128), (256, 256)]  # Tamanhos de miniaturas a gerar
        
        # Garantir diretórios necessários
        self.assets_dir = os.path.join(settings.upload_dir, "assets")
        self.thumbs_dir = os.path.join(self.assets_dir, "thumbnails")
        os.makedirs(self.assets_dir, exist_ok=True)
        os.makedirs(self.thumbs_dir, exist_ok=True)
    
    def get_asset_by_id(self, asset_id):
        """
        Obtém um asset pelo ID
        
        Args:
            asset_id (int): ID do asset
            
        Returns:
            Asset: Objeto de asset ou None
        """
        return self.db.query(Asset).get(asset_id)
    
    def load_assets(self, filters=None):
        """
        Carrega assets com filtros aplicados
        
        Args:
            filters (dict): Filtros a serem aplicados
            
        Returns:
            list: Lista de objetos Asset
        """
        filters = filters or {}
        
        # Construir query base
        query = self.db.query(Asset)
        
        # Aplicar filtros
        if filters.get('folder_id') is not None:  # Pode ser 0 para raiz
            query = query.filter(Asset.folder_id == filters['folder_id'])
            
        if filters.get('event_id'):
            query = query.filter(Asset.event_id == filters['event_id'])
            
        if filters.get('asset_types'):
            query = query.filter(Asset.asset_type.in_(filters['asset_types']))
            
        if filters.get('search_text'):
            search = f"%{filters['search_text']}%"
            query = query.filter(Asset.name.like(search))
            
        if filters.get('tags'):
            # Para cada tag, filtramos os assets que a possuem
            for tag_id in filters['tags']:
                query = query.filter(Asset.tags.any(Tag.id == tag_id))
                
        if filters.get('created_after'):
            query = query.filter(Asset.created_at >= filters['created_after'])
            
        if filters.get('created_before'):
            query = query.filter(Asset.created_at <= filters['created_before'])
            
        # Ordenar por data de criação (mais recentes primeiro)
        query = query.order_by(Asset.created_at.desc())
        
        assets = query.all()
        self.assets_updated.emit(assets)
        return assets
    
    def get_folders(self, parent_id=None):
        """
        Obtém pastas de assets
        
        Args:
            parent_id (int, optional): ID da pasta pai ou None para raiz
            
        Returns:
            list: Lista de objetos AssetFolder
        """
        query = self.db.query(AssetFolder)
        
        if parent_id is not None:
            query = query.filter(AssetFolder.parent_id == parent_id)
        else:
            query = query.filter(AssetFolder.parent_id == None)
            
        return query.order_by(AssetFolder.name).all()
    
    def create_folder(self, name, parent_id=None, creator_id=None):
        """
        Cria uma nova pasta de assets
        
        Args:
            name (str): Nome da pasta
            parent_id (int, optional): ID da pasta pai
            creator_id (int, optional): ID do usuário criador
            
        Returns:
            AssetFolder: Objeto de pasta criado
        """
        try:
            folder = AssetFolder(
                name=name,
                parent_id=parent_id,
                created_at=datetime.datetime.now(),
                created_by=creator_id
            )
            
            self.db.add(folder)
            self.db.commit()
            
            logger.info(f"Pasta de assets criada: {folder.id} - {folder.name}")
            self.folder_created.emit(folder)
            return folder
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao criar pasta de assets: {str(e)}", exc_info=True)
            raise
    
    def import_asset(self, file_path, folder_id=None, event_id=None, 
                   name=None, description=None, creator_id=None):
        """
        Importa um arquivo para a biblioteca de assets
        
        Args:
            file_path (str): Caminho do arquivo a ser importado
            folder_id (int, optional): ID da pasta
            event_id (int, optional): ID do evento
            name (str, optional): Nome personalizado ou None para usar nome do arquivo
            description (str, optional): Descrição
            creator_id (int, optional): ID do usuário criador
            
        Returns:
            Asset: Objeto de asset criado
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Arquivo não encontrado: {file_path}")
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Determinar tipo de asset
            asset_type = self._determine_asset_type(file_path)
            
            # Criar diretório específico para o tipo de asset se não existir
            type_dir = os.path.join(self.assets_dir, asset_type)
            os.makedirs(type_dir, exist_ok=True)
            
            # Gerar nome de arquivo único
            original_filename = os.path.basename(file_path)
            filename_base, extension = os.path.splitext(original_filename)
            unique_filename = f"{filename_base}_{uuid.uuid4().hex}{extension}"
            
            # Caminho de destino
            dest_path = os.path.join(type_dir, unique_filename)
            
            # Copiar arquivo
            shutil.copy2(file_path, dest_path)
            
            # Obter tamanho do arquivo
            file_size = os.path.getsize(dest_path)
            
            # Nome do asset (usar nome fornecido ou nome do arquivo)
            asset_name = name or filename_base
            
            # Metadados técnicos
            technical_metadata = self._extract_metadata(dest_path, asset_type)
            
            # Gerar thumbnail para tipos suportados
            thumbnail_path = None
            if asset_type in ["image", "video"]:
                thumbnail_path = self._generate_thumbnail(dest_path, asset_type, unique_filename)
            
            # Criar registro de asset no banco
            asset = Asset(
                name=asset_name,
                file_path=dest_path,
                asset_type=asset_type,
                description=description,
                event_id=event_id,
                folder_id=folder_id,
                created_at=datetime.datetime.now(),
                created_by=creator_id,
                file_size=file_size,
                duration=technical_metadata.get("duration"),
                technical_metadata=json.dumps(technical_metadata),
                thumbnail_path=thumbnail_path
            )
            
            self.db.add(asset)
            self.db.commit()
            
            logger.info(f"Asset importado: {asset.id} - {asset.name}")
            self.asset_imported.emit(asset)
            
            return asset
            
        except Exception as e:
            self.db.rollback()
            if os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except:
                    pass
            logger.error(f"Erro ao importar asset: {str(e)}", exc_info=True)
            raise
    
    def batch_import_assets(self, file_paths, folder_id=None, event_id=None, 
                          creator_id=None):
        """
        Importa vários arquivos em lote
        
        Args:
            file_paths (list): Lista de caminhos de arquivo a serem importados
            folder_id (int, optional): ID da pasta
            event_id (int, optional): ID do evento
            creator_id (int, optional): ID do usuário criador
            
        Returns:
            list: Lista de objetos Asset criados
        """
        imported_assets = []
        
        for i, file_path in enumerate(file_paths):
            try:
                # Emitir progresso
                self.import_progress.emit(i, len(file_paths))
                
                # Importar asset
                asset = self.import_asset(
                    file_path=file_path,
                    folder_id=folder_id,
                    event_id=event_id,
                    creator_id=creator_id
                )
                
                imported_assets.append(asset)
                
            except Exception as e:
                logger.error(f"Erro ao importar {file_path}: {str(e)}", exc_info=True)
        
        # Emitir progresso final
        self.import_progress.emit(len(file_paths), len(file_paths))
        
        # Atualizar lista de assets
        self.load_assets(self.current_filters)
        
        return imported_assets
    
    def update_asset(self, asset_id, **kwargs):
        """
        Atualiza um asset existente
        
        Args:
            asset_id (int): ID do asset
            **kwargs: Pares de chave-valor com os atributos a serem atualizados
            
        Returns:
            Asset: Objeto de asset atualizado
        """
        try:
            asset = self.db.query(Asset).get(asset_id)
            
            if not asset:
                logger.warning(f"Tentativa de atualizar asset inexistente: {asset_id}")
                return None
                
            # Atualizar os atributos fornecidos
            for key, value in kwargs.items():
                if hasattr(asset, key):
                    setattr(asset, key, value)
            
            self.db.commit()
            
            logger.info(f"Asset atualizado: {asset.id} - {asset.name}")
            self.load_assets(self.current_filters)
            return asset
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar asset: {str(e)}", exc_info=True)
            raise
    
    def delete_asset(self, asset_id, delete_file=True):
        """
        Remove um asset
        
        Args:
            asset_id (int): ID do asset
            delete_file (bool, optional): Se True, exclui o arquivo físico
            
        Returns:
            bool: True se a exclusão for bem-sucedida
        """
        try:
            asset = self.db.query(Asset).get(asset_id)
            
            if not asset:
                logger.warning(f"Tentativa de excluir asset inexistente: {asset_id}")
                return False
                
            # Guardar caminhos para exclusão posterior
            file_path = asset.file_path
            thumbnail_path = asset.thumbnail_path
            
            # Excluir do banco de dados
            self.db.delete(asset)
            self.db.commit()
            
            # Excluir arquivos físicos se solicitado
            if delete_file:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.error(f"Erro ao excluir arquivo de asset: {str(e)}", exc_info=True)
                        
                if thumbnail_path and os.path.exists(thumbnail_path):
                    try:
                        os.remove(thumbnail_path)
                    except Exception as e:
                        logger.error(f"Erro ao excluir thumbnail de asset: {str(e)}", exc_info=True)
            
            logger.info(f"Asset excluído: {asset_id}")
            self.load_assets(self.current_filters)
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao excluir asset: {str(e)}", exc_info=True)
            raise
    
    def add_tag_to_asset(self, asset_id, tag_name):
        """
        Adiciona uma tag a um asset
        
        Args:
            asset_id (int): ID do asset
            tag_name (str): Nome da tag
            
        Returns:
            bool: True se bem-sucedido
        """
        try:
            asset = self.db.query(Asset).get(asset_id)
            
            if not asset:
                logger.warning(f"Tentativa de adicionar tag a asset inexistente: {asset_id}")
                return False
            
            # Buscar tag ou criar se não existir
            tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
            
            if not tag:
                tag = Tag(name=tag_name)
                self.db.add(tag)
                self.db.commit()
            
            # Verificar se a tag já está associada ao asset
            if tag in asset.tags:
                return True
                
            # Adicionar tag ao asset
            asset.tags.append(tag)
            self.db.commit()
            
            logger.info(f"Tag '{tag_name}' adicionada ao asset {asset_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao adicionar tag: {str(e)}", exc_info=True)
            raise
    
    def remove_tag_from_asset(self, asset_id, tag_name):
        """
        Remove uma tag de um asset
        
        Args:
            asset_id (int): ID do asset
            tag_name (str): Nome da tag
            
        Returns:
            bool: True se bem-sucedido
        """
        try:
            asset = self.db.query(Asset).get(asset_id)
            
            if not asset:
                logger.warning(f"Tentativa de remover tag de asset inexistente: {asset_id}")
                return False
            
            # Buscar tag
            tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
            
            if not tag or tag not in asset.tags:
                return False
                
            # Remover tag do asset
            asset.tags.remove(tag)
            self.db.commit()
            
            logger.info(f"Tag '{tag_name}' removida do asset {asset_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao remover tag: {str(e)}", exc_info=True)
            raise
    
    def get_all_tags(self):
        """
        Obtém todas as tags disponíveis
        
        Returns:
            list: Lista de objetos Tag
        """
        return self.db.query(Tag).order_by(Tag.name).all()
    
    def get_tags_for_asset(self, asset_id):
        """
        Obtém tags associadas a um asset
        
        Args:
            asset_id (int): ID do asset
            
        Returns:
            list: Lista de objetos Tag
        """
        asset = self.db.query(Asset).get(asset_id)
        
        if not asset:
            return []
            
        return asset.tags
    
    def _determine_asset_type(self, file_path):
        """
        Determina o tipo de asset com base na extensão e no conteúdo
        
        Args:
            file_path (str): Caminho do arquivo
            
        Returns:
            str: Tipo de asset (video, audio, image, document)
        """
        # Determinar mimetype
        mime_type, _ = mimetypes.guess_type(file_path)
        
        if not mime_type:
            # Verificar extensão se mimetype não for reconhecido
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                return "image"
            elif ext in ['.mp4', '.mov', '.avi', '.wmv', '.mkv']:
                return "video"
            elif ext in ['.mp3', '.wav', '.ogg', '.flac', '.aac']:
                return "audio"
            elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']:
                return "document"
            else:
                return "other"
        
        # Determinar por mimetype
        if mime_type.startswith('image'):
            return "image"
        elif mime_type.startswith('video'):
            return "video"
        elif mime_type.startswith('audio'):
            return "audio"
        elif mime_type.startswith('application'):
            if 'pdf' in mime_type or 'office' in mime_type or 'document' in mime_type or 'text' in mime_type:
                return "document"
            else:
                return "other"
        else:
            return "other"
    
    def _extract_metadata(self, file_path, asset_type):
        """
        Extrai metadados técnicos do arquivo
        
        Args:
            file_path (str): Caminho do arquivo
            asset_type (str): Tipo de asset
            
        Returns:
            dict: Dicionário de metadados
        """
        metadata = {
            "filename": os.path.basename(file_path),
            "size_bytes": os.path.getsize(file_path),
            "size_human": self._format_size(os.path.getsize(file_path)),
            "created": datetime.datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
            "modified": datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
        }
        
        # Extrair metadados específicos por tipo
        try:
            if asset_type == "image":
                with Image.open(file_path) as img:
                    metadata["width"] = img.width
                    metadata["height"] = img.height
                    metadata["format"] = img.format
                    metadata["mode"] = img.mode
                    if hasattr(img, "info"):
                        metadata["image_info"] = img.info
            
            # TODO: Para vídeo e áudio, seria necessário usar uma biblioteca como moviepy ou ffmpeg
            # Exemplo: 
            # if asset_type == "video":
            #     import moviepy.editor as mp
            #     clip = mp.VideoFileClip(file_path)
            #     metadata["duration"] = clip.duration
            #     metadata["width"] = clip.size[0]
            #     metadata["height"] = clip.size[1]
            #     metadata["fps"] = clip.fps
            #     clip.close()
            
        except Exception as e:
            logger.warning(f"Erro ao extrair metadados específicos: {str(e)}")
            
        return metadata
    
    def _generate_thumbnail(self, file_path, asset_type, unique_name):
        """
        Gera thumbnail para o asset
        
        Args:
            file_path (str): Caminho do arquivo
            asset_type (str): Tipo de asset
            unique_name (str): Nome único para o thumbnail
            
        Returns:
            str: Caminho do thumbnail ou None
        """
        try:
            if asset_type == "image":
                # Extrair nome base
                base_name = os.path.splitext(unique_name)[0]
                thumb_path = os.path.join(self.thumbs_dir, f"{base_name}_thumb.jpg")
                
                # Criar thumbnail
                with Image.open(file_path) as img:
                    # Converter para RGB se necessário
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Criar thumbnail do tamanho maior
                    img.thumbnail(self.thumbnail_sizes[-1])
                    img.save(thumb_path, "JPEG", quality=85)
                    
                return thumb_path
                
            # TODO: Para vídeo seria necessário extrair um frame, usando ffmpeg ou moviepy
            
        except Exception as e:
            logger.error(f"Erro ao gerar thumbnail: {str(e)}", exc_info=True)
            
        return None
    
    def _format_size(self, size_bytes):
        """
        Formata o tamanho do arquivo em formato legível
        
        Args:
            size_bytes (int): Tamanho em bytes
            
        Returns:
            str: Tamanho formatado (ex: "2.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
