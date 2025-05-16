"""
GONETWORK AI - View de Biblioteca de Assets usando padrão MVC
Implementa a visualização da biblioteca de assets (mídia) usando o controller
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListView, QTreeView, QSplitter, QToolBar, QAction, 
    QComboBox, QLineEdit, QFileDialog, QMessageBox,
    QMenu, QDialog, QGridLayout, QScrollArea, 
    QFrame, QSizePolicy, QTableView, QHeaderView
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QSize, QPoint, QSortFilterProxyModel, QModelIndex
)
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QPixmap

import logging
import os
import datetime

from controllers.asset_controller import AssetController
from models.asset import Asset, AssetFolder
from models.event import Tag
from ui.models.asset_library_model import AssetLibraryModel, AssetFolderModel
from core.logging_manager import get_logger

logger = get_logger(__name__)

class AssetThumbnailWidget(QFrame):
    """Widget para exibir um thumbnail de asset com informações"""
    
    # Sinais
    clicked = pyqtSignal(object)  # Asset clicado
    double_clicked = pyqtSignal(object)  # Asset com duplo clique
    
    def __init__(self, asset, parent=None):
        """
        Inicializa o widget de thumbnail
        
        Args:
            asset (Asset): Objeto de asset
            parent: Widget pai
        """
        super().__init__(parent)
        self.asset = asset
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface do widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Frame para o thumbnail
        thumbnail_frame = QFrame()
        thumbnail_frame.setFixedSize(128, 128)
        thumbnail_frame.setFrameShape(QFrame.StyledPanel)
        thumbnail_frame.setFrameShadow(QFrame.Sunken)
        thumbnail_frame.setStyleSheet("""
            background-color: #f5f5f5;
            border: 1px solid #ddd;
        """)
        
        thumbnail_layout = QVBoxLayout(thumbnail_frame)
        thumbnail_layout.setAlignment(Qt.AlignCenter)
        
        # Imagem do thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        
        if self.asset.thumbnail_path and os.path.exists(self.asset.thumbnail_path):
            pixmap = QPixmap(self.asset.thumbnail_path)
            pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumbnail_label.setPixmap(pixmap)
        else:
            # Ícone padrão baseado no tipo
            icon_map = {
                'video': 'resources/icons/video.png',
                'image': 'resources/icons/image.png',
                'audio': 'resources/icons/audio.png',
                'document': 'resources/icons/document.png',
                'other': 'resources/icons/file.png'
            }
            
            icon_path = icon_map.get(self.asset.asset_type, icon_map['other'])
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.thumbnail_label.setPixmap(pixmap)
            else:
                self.thumbnail_label.setText(self.asset.asset_type.upper())
        
        thumbnail_layout.addWidget(self.thumbnail_label)
        
        # Nome do asset
        self.name_label = QLabel(self.asset.name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-weight: bold;")
        
        # Informações adicionais
        self.info_label = QLabel(f"{self.asset.asset_type.capitalize()}")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #666; font-size: 9pt;")
        
        # Adicionar widgets ao layout
        layout.addWidget(thumbnail_frame)
        layout.addWidget(self.name_label)
        layout.addWidget(self.info_label)
        
        # Configurar estilo do widget
        self.setStyleSheet("""
            QFrame {
                border: 1px solid transparent;
                border-radius: 4px;
                background-color: white;
            }
            QFrame:hover {
                border: 1px solid #99ccff;
                background-color: #f0f9ff;
            }
        """)
        
        # Configurar eventos de mouse
        self.setMouseTracking(True)
        
    def mousePressEvent(self, event):
        """
        Manipulador para clique do mouse
        
        Args:
            event: Evento de mouse
        """
        super().mousePressEvent(event)
        self.clicked.emit(self.asset)
    
    def mouseDoubleClickEvent(self, event):
        """
        Manipulador para duplo clique do mouse
        
        Args:
            event: Evento de mouse
        """
        super().mouseDoubleClickEvent(event)
        self.double_clicked.emit(self.asset)


class AssetLibraryMVC(QWidget):
    """
    View para biblioteca de assets usando padrão MVC
    
    Esta classe implementa o padrão MVC usando o AssetController
    para gerenciar as operações de negócio relacionadas aos assets.
    """
    
    # Sinais
    asset_selected = pyqtSignal(object)  # Asset selecionado
    asset_double_clicked = pyqtSignal(object)  # Asset com duplo clique
    folder_selected = pyqtSignal(object)  # Pasta selecionada
    
    def __init__(self, db_session=None, parent=None):
        """
        Inicializa a view da biblioteca de assets
        
        Args:
            db_session: Sessão do SQLAlchemy para acesso ao banco de dados
            parent: Widget pai
        """
        super().__init__(parent)
        self.db = db_session
        
        # Controlador - será configurado em set_database se não for passado direto
        self.controller = AssetController(db_session) if db_session else None
        
        # Estado atual
        self.current_folder_id = None
        self.current_event_id = None
        self.current_assets = []
        
        # Modelos
        self.folder_model = AssetFolderModel()
        
        self.setup_ui()
        self.connect_signals()
    
    def set_database(self, db_session):
        """
        Define a sessão de banco de dados e inicializa o controlador
        
        Args:
            db_session: Sessão do SQLAlchemy
        """
        self.db = db_session
        self.controller = AssetController(db_session)
        self.connect_signals()
    
    def setup_ui(self):
        """Configura a interface da view"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Barra de ferramentas
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        
        # Botão de importar asset
        import_btn = QAction(QIcon("resources/icons/add.png"), "Importar Assets", self)
        import_btn.triggered.connect(self.on_import_assets)
        toolbar.addAction(import_btn)
        
        # Botão de nova pasta
        new_folder_btn = QAction(QIcon("resources/icons/folder_add.png"), "Nova Pasta", self)
        new_folder_btn.triggered.connect(self.on_new_folder)
        toolbar.addAction(new_folder_btn)
        
        # Botão de atualizar
        refresh_btn = QAction(QIcon("resources/icons/refresh.png"), "Atualizar", self)
        refresh_btn.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_btn)
        
        toolbar.addSeparator()
        
        # Seletor de eventos
        self.event_filter = QComboBox()
        self.event_filter.addItem("Todos os Eventos", None)
        self.event_filter.currentIndexChanged.connect(self.on_event_filter_changed)
        toolbar.addWidget(QLabel("Evento:"))
        toolbar.addWidget(self.event_filter)
        
        toolbar.addSeparator()
        
        # Filtro por tipo de asset
        self.type_filter = QComboBox()
        self.type_filter.addItem("Todos os Tipos", None)
        self.type_filter.addItem("Imagens", ["image"])
        self.type_filter.addItem("Vídeos", ["video"])
        self.type_filter.addItem("Áudios", ["audio"])
        self.type_filter.addItem("Documentos", ["document"])
        self.type_filter.addItem("Outros", ["other"])
        self.type_filter.addItem("Mídia (Imagens/Vídeos)", ["image", "video"])
        self.type_filter.currentIndexChanged.connect(self.apply_filters)
        toolbar.addWidget(QLabel("Tipo:"))
        toolbar.addWidget(self.type_filter)
        
        toolbar.addSeparator()
        
        # Caixa de pesquisa
        self.search_box = QLineEdit()
        self.search_box.setMinimumWidth(200)
        self.search_box.setPlaceholderText("Pesquisar assets...")
        self.search_box.textChanged.connect(self.on_search_text_changed)
        toolbar.addWidget(QLabel("Buscar:"))
        toolbar.addWidget(self.search_box)
        
        # Adicionar barra de ferramentas ao layout
        main_layout.addWidget(toolbar)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        
        # Painel esquerdo - Árvore de pastas
        self.folder_tree = QTreeView()
        self.folder_tree.setModel(self.folder_model)
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.setMinimumWidth(200)
        self.folder_tree.clicked.connect(self.on_folder_clicked)
        
        # Estilizar a árvore de pastas
        self.folder_tree.setStyleSheet("""
            QTreeView {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
            }
            QTreeView::item {
                padding: 4px;
            }
            QTreeView::item:selected {
                background-color: #e0f0ff;
                border: 1px solid #99ccff;
            }
            QTreeView::item:hover {
                background-color: #f0f9ff;
            }
        """)
        
        # Painel direito - Grid de assets
        self.assets_container = QWidget()
        self.assets_layout = QGridLayout(self.assets_container)
        self.assets_layout.setSpacing(10)
        
        # Scroll area para a grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.assets_container)
        
        # Adicionar painéis ao splitter
        splitter.addWidget(self.folder_tree)
        splitter.addWidget(scroll_area)
        
        # Definir proporções iniciais do splitter
        splitter.setSizes([200, 800])
        
        # Adicionar splitter ao layout principal
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)
    
    def connect_signals(self):
        """Conecta os sinais do controlador aos slots da view"""
        if not self.controller:
            return
            
        self.controller.assets_updated.connect(self.on_assets_updated)
        self.controller.folder_created.connect(self.on_folder_created)
        self.controller.asset_imported.connect(self.on_asset_imported)
        self.controller.import_progress.connect(self.on_import_progress)
    
    def load_events(self):
        """Carrega os eventos para o filtro"""
        try:
            from models.event import Event
            
            # Limpar e recarregar filtro de eventos
            self.event_filter.clear()
            self.event_filter.addItem("Todos os Eventos", None)
            
            events = self.db.query(Event).order_by(Event.start_date.desc()).all()
            
            for event in events:
                self.event_filter.addItem(event.name, event.id)
        
        except Exception as e:
            logger.error(f"Erro ao carregar eventos: {str(e)}", exc_info=True)
    
    def load_folders(self):
        """Carrega a estrutura de pastas para a árvore"""
        try:
            # Limpar modelo de pastas
            self.folder_model.clear()
            
            # Adicionar item raiz
            root_item = QStandardItem(QIcon("resources/icons/folder.png"), "Todos os Assets")
            root_item.setData(None, Qt.UserRole)  # ID da pasta (None para raiz)
            self.folder_model.appendRow(root_item)
            
            if self.controller:
                # Obter pastas raiz (sem parent)
                root_folders = self.controller.get_folders()
                
                # Adicionar pastas à árvore
                for folder in root_folders:
                    self.add_folder_to_tree(root_item, folder)
                
                # Expandir raiz
                self.folder_tree.expand(self.folder_model.indexFromItem(root_item))
        
        except Exception as e:
            logger.error(f"Erro ao carregar estrutura de pastas: {str(e)}", exc_info=True)
    
    def add_folder_to_tree(self, parent_item, folder, expand=True):
        """
        Adiciona uma pasta à árvore de forma recursiva
        
        Args:
            parent_item (QStandardItem): Item pai na árvore
            folder (AssetFolder): Objeto de pasta
            expand (bool): Se deve expandir a subárvore
        """
        # Criar item para a pasta
        folder_item = QStandardItem(QIcon("resources/icons/folder.png"), folder.name)
        folder_item.setData(folder.id, Qt.UserRole)
        
        # Adicionar ao pai
        parent_item.appendRow(folder_item)
        
        # Adicionar subpastas recursivamente
        if self.controller:
            subfolders = self.controller.get_folders(folder.id)
            
            for subfolder in subfolders:
                self.add_folder_to_tree(folder_item, subfolder, False)
            
            # Expandir se solicitado e houver subpastas
            if expand and subfolders:
                self.folder_tree.expand(self.folder_model.indexFromItem(folder_item))
    
    def on_folder_clicked(self, index):
        """
        Manipulador para clique em pasta
        
        Args:
            index: Índice do item clicado na árvore
        """
        folder_id = self.folder_model.data(index, Qt.UserRole)
        self.current_folder_id = folder_id
        
        # Atualizar filtros e carregar assets da pasta
        self.apply_filters()
    
    def on_event_filter_changed(self, index):
        """
        Manipulador para mudança no filtro de eventos
        
        Args:
            index: Índice do item selecionado
        """
        self.current_event_id = self.event_filter.currentData()
        self.apply_filters()
    
    def on_search_text_changed(self, text):
        """
        Manipulador para mudança no texto de pesquisa
        
        Args:
            text (str): Texto de pesquisa
        """
        self.apply_filters()
    
    def apply_filters(self):
        """Aplica os filtros selecionados aos assets"""
        if not self.controller:
            return
            
        # Construir dicionário de filtros
        filters = {}
        
        # Filtro de pasta
        filters['folder_id'] = self.current_folder_id
        
        # Filtro de evento
        if self.current_event_id:
            filters['event_id'] = self.current_event_id
        
        # Filtro de tipo
        asset_types = self.type_filter.currentData()
        if asset_types:
            filters['asset_types'] = asset_types
        
        # Texto de pesquisa
        search_text = self.search_box.text().strip()
        if search_text:
            filters['search_text'] = search_text
        
        # Aplicar filtros e carregar assets
        self.controller.current_filters = filters
        self.controller.load_assets(filters)
    
    def refresh_data(self):
        """Recarrega os dados da biblioteca"""
        self.load_folders()
        self.apply_filters()
    
    def on_assets_updated(self, assets):
        """
        Manipulador para atualização da lista de assets
        
        Args:
            assets (list): Lista de assets
        """
        self.current_assets = assets
        self.display_assets()
    
    def display_assets(self):
        """Exibe os assets na grid"""
        # Limpar grid atual
        self.clear_assets_grid()
        
        if not self.current_assets:
            # Mostrar mensagem de sem assets
            empty_label = QLabel("Nenhum asset encontrado")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #666; font-size: 14pt;")
            self.assets_layout.addWidget(empty_label, 0, 0)
            return
        
        # Configurar grid
        col_count = max(1, self.assets_container.width() // 150)  # Estimar quantas colunas cabem
        
        # Adicionar assets à grid
        for i, asset in enumerate(self.current_assets):
            row = i // col_count
            col = i % col_count
            
            thumbnail = AssetThumbnailWidget(asset)
            thumbnail.clicked.connect(self.on_asset_clicked)
            thumbnail.double_clicked.connect(self.on_asset_double_clicked)
            
            self.assets_layout.addWidget(thumbnail, row, col)
        
        # Atualizar barra de status
        self.status_label.setText(f"{len(self.current_assets)} assets encontrados")
    
    def clear_assets_grid(self):
        """Limpa a grid de assets"""
        # Remover todos os widgets da grid
        while self.assets_layout.count():
            item = self.assets_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def on_asset_clicked(self, asset):
        """
        Manipulador para clique em asset
        
        Args:
            asset (Asset): Asset clicado
        """
        self.asset_selected.emit(asset)
    
    def on_asset_double_clicked(self, asset):
        """
        Manipulador para duplo clique em asset
        
        Args:
            asset (Asset): Asset com duplo clique
        """
        self.asset_double_clicked.emit(asset)
    
    def on_import_assets(self):
        """Abre diálogo para importar assets"""
        if not self.controller:
            return
            
        # Abrir diálogo de seleção de arquivo
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Todos os arquivos (*)")
        
        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()
            
            if file_paths:
                # Importar arquivos selecionados usando o controlador
                # em uma operação em lote
                self.controller.batch_import_assets(
                    file_paths=file_paths,
                    folder_id=self.current_folder_id,
                    event_id=self.current_event_id
                )
    
    def on_new_folder(self):
        """Cria uma nova pasta"""
        if not self.controller:
            return
            
        # Implementação simplificada - na prática, abriria um diálogo
        from PyQt5.QtWidgets import QInputDialog
        
        folder_name, ok = QInputDialog.getText(
            self, 
            "Nova Pasta", 
            "Nome da pasta:"
        )
        
        if ok and folder_name.strip():
            # Criar pasta usando o controlador
            self.controller.create_folder(
                name=folder_name.strip(),
                parent_id=self.current_folder_id
            )
    
    def on_folder_created(self, folder):
        """
        Manipulador para criação de nova pasta
        
        Args:
            folder (AssetFolder): Pasta criada
        """
        # Atualizar estrutura de pastas
        self.load_folders()
        
        # Se a pasta foi criada na pasta atual, atualizar visualização
        if folder.parent_id == self.current_folder_id:
            self.apply_filters()
    
    def on_asset_imported(self, asset):
        """
        Manipulador para importação de asset
        
        Args:
            asset (Asset): Asset importado
        """
        # Se o asset foi importado na pasta atual, atualizar visualização
        if asset.folder_id == self.current_folder_id:
            # O controller já deve ter atualizado a lista de assets
            pass
    
    def on_import_progress(self, current, total):
        """
        Manipulador para progresso de importação em lote
        
        Args:
            current (int): Progresso atual
            total (int): Total de arquivos
        """
        # Atualizar barra de status
        self.status_label.setText(f"Importando assets: {current}/{total}")
    
    def resizeEvent(self, event):
        """
        Manipulador para redimensionamento da view
        
        Args:
            event: Evento de redimensionamento
        """
        super().resizeEvent(event)
        
        # Redesenhar a grid de assets se necessário
        if self.current_assets:
            self.display_assets()
