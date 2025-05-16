"""
GONETWORK AI - View de Kanban de Entregas usando padrão MVC
Implementa a visualização Kanban para entregas usando o controller
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListView, QPushButton, QMenu, QAction, 
    QToolBar, QComboBox, QLineEdit, QMessageBox,
    QDialog, QScrollArea, QSizePolicy, QFrame,
    QToolButton, QSpacerItem
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QSize, QPoint, QRect, 
    QModelIndex, QEvent
)
from PyQt5.QtGui import QIcon, QColor, QPalette, QPen, QPainter

import logging
from controllers.delivery_controller import DeliveryKanbanController 
from models.delivery import Delivery
from models.team import TeamMember
from models.event import Activity, Event
from ui.models.delivery_kanban_model import DeliveryKanbanModel, KanbanColumnModel
from core.logging_manager import get_logger

logger = get_logger(__name__)

class KanbanColumnWidget(QWidget):
    """Widget para exibir uma coluna do Kanban"""
    
    # Sinais
    item_dropped = pyqtSignal(int, str, int)  # ID do item, nova coluna, nova posição
    item_clicked = pyqtSignal(int)           # ID do item selecionado
    item_double_clicked = pyqtSignal(int)    # ID do item com duplo clique
    
    def __init__(self, column, column_id, parent=None):
        """
        Inicializa o widget de coluna
        
        Args:
            column: Modelo de coluna
            column_id: Identificador da coluna (usado para movimento)
            parent: Widget pai
        """
        super().__init__(parent)
        self.column = column
        self.column_id = column_id
        self.list_model = KanbanColumnModel(column)
        self.selected_item = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface da coluna"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Cabeçalho da coluna
        header = QWidget()
        header.setFixedHeight(40)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 2, 10, 2)
        
        # Título da coluna
        title_label = QLabel(self.column.title)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 14px;
            color: #333;
            background-color: {self.column.color.name()};
            border-radius: 3px;
            padding: 4px;
        """)
        
        # Contador de itens
        self.count_label = QLabel(f"{self.column.count()}")
        self.count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.count_label.setStyleSheet("""
            font-weight: bold;
            font-size: 12px;
            color: #666;
            background-color: white;
            border-radius: 10px;
            padding: 2px 6px;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(self.count_label)
        
        # Lista de entregas
        self.list_view = QListView()
        self.list_view.setModel(self.list_model)
        self.list_view.setSelectionMode(QListView.SingleSelection)
        self.list_view.setDragEnabled(True)
        self.list_view.setAcceptDrops(True)
        self.list_view.setDropIndicatorShown(True)
        self.list_view.setDragDropMode(QListView.DragDrop)
        self.list_view.setDefaultDropAction(Qt.MoveAction)
        self.list_view.setStyleSheet("""
            QListView {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                padding: 2px;
            }
            QListView::item {
                border-bottom: 1px solid #eee;
                padding: 4px;
            }
            QListView::item:selected {
                background-color: #e0f0ff;
                border: 1px solid #99ccff;
            }
            QListView::item:hover {
                background-color: #f0f9ff;
            }
        """)
        
        self.list_view.clicked.connect(self.on_item_clicked)
        self.list_view.doubleClicked.connect(self.on_item_double_clicked)
        
        # Adicionar widgets ao layout
        layout.addWidget(header)
        layout.addWidget(self.list_view)
    
    def on_item_clicked(self, index):
        """
        Manipulador para clique em item
        
        Args:
            index: Índice do item clicado
        """
        item = self.list_model.data(index, Qt.UserRole)
        if item:
            self.selected_item = item
            self.item_clicked.emit(item.id)
    
    def on_item_double_clicked(self, index):
        """
        Manipulador para duplo clique em item
        
        Args:
            index: Índice do item com duplo clique
        """
        item = self.list_model.data(index, Qt.UserRole)
        if item:
            self.item_double_clicked.emit(item.id)
    
    def update_data(self):
        """Atualiza os dados da coluna"""
        self.list_model.layoutChanged.emit()
        self.count_label.setText(f"{self.column.count()}")
    
    def add_delivery(self, delivery):
        """
        Adiciona uma entrega à coluna
        
        Args:
            delivery: Objeto Delivery
        """
        self.column.add_item(delivery)
        self.update_data()


class DeliveryKanbanMVC(QWidget):
    """
    Visualização Kanban para entregas usando padrão MVC
    
    Esta classe implementa o padrão MVC usando o DeliveryKanbanController
    para gerenciar as operações de negócio relacionadas às entregas.
    """
    
    # Sinais
    delivery_selected = pyqtSignal(object)  # Objeto Delivery selecionado
    delivery_double_clicked = pyqtSignal(object)  # Delivery com duplo clique
    
    def __init__(self, db_session=None, parent=None):
        """
        Inicializa a view do Kanban
        
        Args:
            db_session: Sessão do SQLAlchemy para acesso ao banco de dados
            parent: Widget pai
        """
        super().__init__(parent)
        self.db = db_session
        
        # Controlador - será configurado em set_database se não for passado direto
        self.controller = DeliveryKanbanController(db_session) if db_session else None
        
        # Configurar modelo Kanban
        self.kanban_model = DeliveryKanbanModel()
        self.column_widgets = []
        
        # Filtros
        self.filtered_responsible = None
        self.filtered_activity = None
        self.search_text = ""
        
        self.setup_ui()
        self.connect_signals()
    
    def set_database(self, db_session):
        """
        Define a sessão de banco de dados e inicializa o controlador
        
        Args:
            db_session: Sessão do SQLAlchemy
        """
        self.db = db_session
        self.controller = DeliveryKanbanController(db_session)
        self.connect_signals()
    
    def setup_ui(self):
        """Configura a interface da view"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Barra de ferramentas
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        
        # Botão de nova entrega
        new_delivery_btn = QAction(QIcon("resources/icons/add.png"), "Nova Entrega", self)
        new_delivery_btn.triggered.connect(self.on_new_delivery)
        toolbar.addAction(new_delivery_btn)
        
        # Botão de atualizar
        refresh_btn = QAction(QIcon("resources/icons/refresh.png"), "Atualizar", self)
        refresh_btn.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_btn)
        
        toolbar.addSeparator()
        
        # Filtro por responsável
        self.responsible_filter = QComboBox()
        self.responsible_filter.setMinimumWidth(150)
        self.responsible_filter.addItem("Todos os Responsáveis", None)
        self.responsible_filter.currentIndexChanged.connect(self.apply_filters)
        toolbar.addWidget(QLabel("Responsável:"))
        toolbar.addWidget(self.responsible_filter)
        
        toolbar.addSeparator()
        
        # Filtro por atividade
        self.activity_filter = QComboBox()
        self.activity_filter.setMinimumWidth(150)
        self.activity_filter.addItem("Todas as Atividades", None)
        self.activity_filter.currentIndexChanged.connect(self.apply_filters)
        toolbar.addWidget(QLabel("Atividade:"))
        toolbar.addWidget(self.activity_filter)
        
        toolbar.addSeparator()
        
        # Caixa de pesquisa
        self.search_box = QLineEdit()
        self.search_box.setMinimumWidth(200)
        self.search_box.setPlaceholderText("Pesquisar entregas...")
        self.search_box.textChanged.connect(self.on_search_text_changed)
        search_label = QLabel("Buscar:")
        toolbar.addWidget(search_label)
        toolbar.addWidget(self.search_box)
        
        # Adicionar barra de ferramentas ao layout
        main_layout.addWidget(toolbar)
        
        # Área de rolagem horizontal para as colunas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Widget contêiner para as colunas
        columns_widget = QWidget()
        self.columns_layout = QHBoxLayout(columns_widget)
        self.columns_layout.setSpacing(10)
        
        # Adicionar colunas
        for i in range(self.kanban_model.column_count()):
            column = self.kanban_model.get_column(i)
            if column:
                column_widget = KanbanColumnWidget(column, column.id)
                column_widget.item_double_clicked.connect(self.on_delivery_double_clicked)
                column_widget.item_clicked.connect(self.on_delivery_selected)
                column_widget.item_dropped.connect(self.on_item_dropped)
                
                self.columns_layout.addWidget(column_widget)
                self.column_widgets.append(column_widget)
        
        # Adicionar área de rolagem ao layout principal
        scroll_area.setWidget(columns_widget)
        main_layout.addWidget(scroll_area)
    
    def connect_signals(self):
        """Conecta os sinais do controlador aos slots da view"""
        if not self.controller:
            return
            
        self.controller.deliveries_updated.connect(self.on_deliveries_updated)
        self.controller.delivery_moved.connect(self.on_delivery_moved)
        self.controller.delivery_created.connect(self.on_delivery_created)
        self.controller.notification_created.connect(self.show_notification)
    
    def set_event(self, event_id):
        """
        Define o evento atual e carrega as entregas
        
        Args:
            event_id (int): ID do evento
        """
        if not self.controller:
            logger.warning("Tentativa de definir evento sem controlador inicializado")
            return
            
        # Definir evento atual no controlador
        self.controller.set_current_event(event_id)
        
        # Carregar filtros de responsáveis e atividades
        self.load_filter_options(event_id)
    
    def load_filter_options(self, event_id):
        """
        Carrega as opções para os filtros (responsáveis e atividades)
        
        Args:
            event_id (int): ID do evento
        """
        try:
            # Limpar e recarregar filtro de responsáveis
            self.responsible_filter.clear()
            self.responsible_filter.addItem("Todos os Responsáveis", None)
            
            team_members = self.db.query(TeamMember).order_by(TeamMember.name).all()
            for member in team_members:
                self.responsible_filter.addItem(member.name, member.id)
            
            # Limpar e recarregar filtro de atividades
            self.activity_filter.clear()
            self.activity_filter.addItem("Todas as Atividades", None)
            
            activities = (self.db.query(Activity)
                        .join(Activity.stage)
                        .filter(Activity.stage.has(event_id=event_id))
                        .order_by(Activity.name)
                        .all())
            
            for activity in activities:
                self.activity_filter.addItem(activity.name, activity.id)
        
        except Exception as e:
            logger.error(f"Erro ao carregar opções de filtro: {str(e)}", exc_info=True)
    
    def on_deliveries_updated(self, deliveries):
        """
        Manipulador para atualização da lista de entregas
        
        Args:
            deliveries (list): Lista de entregas
        """
        # Limpar todas as colunas
        for i in range(self.kanban_model.column_count()):
            column = self.kanban_model.get_column(i)
            column.clear_items()
        
        # Distribuir entregas nas colunas corretas usando o mapeamento do controller
        for delivery in deliveries:
            column_id = self.controller.map_status_to_column(delivery.status)
            column = self.kanban_model.get_column_by_id(column_id)
            if column:
                column.add_item(delivery)
        
        # Atualizar widgets de coluna
        self.update_column_widgets()
    
    def update_column_widgets(self):
        """Atualiza os widgets de coluna com os novos dados"""
        for widget in self.column_widgets:
            widget.update_data()
    
    def on_search_text_changed(self, text):
        """
        Manipulador para mudança no texto de pesquisa
        
        Args:
            text (str): Texto de pesquisa
        """
        self.search_text = text.strip()
        self.apply_filters()
    
    def apply_filters(self):
        """Aplica os filtros selecionados"""
        # Construir dicionário de filtros
        filters = {}
        
        # Filtro de responsável
        responsible_id = self.responsible_filter.currentData()
        if responsible_id:
            filters['responsible_id'] = responsible_id
        
        # Filtro de atividade
        activity_id = self.activity_filter.currentData()
        if activity_id:
            filters['activity_id'] = activity_id
        
        # Texto de pesquisa
        if self.search_text:
            filters['search_text'] = self.search_text
        
        # Aplicar filtros através do controlador
        self.controller.current_filters = filters
        self.controller.reload_deliveries()
    
    def refresh_data(self):
        """Recarrega os dados do Kanban"""
        if self.controller:
            self.controller.reload_deliveries()
    
    def on_item_dropped(self, delivery_id, to_column, position):
        """
        Manipulador para quando uma entrega é movida entre colunas
        
        Args:
            delivery_id (int): ID da entrega
            to_column (str): Identificador da coluna de destino
            position (int): Posição na coluna
        """
        if self.controller:
            # Mover entrega para nova coluna usando o controlador
            self.controller.move_delivery(delivery_id, to_column)
    
    def on_delivery_selected(self, delivery_id):
        """
        Manipulador para seleção de entrega
        
        Args:
            delivery_id (int): ID da entrega
        """
        if self.controller:
            delivery = self.controller.get_delivery(delivery_id)
            if delivery:
                self.delivery_selected.emit(delivery)
    
    def on_delivery_double_clicked(self, delivery_id):
        """
        Manipulador para duplo clique em uma entrega
        
        Args:
            delivery_id (int): ID da entrega
        """
        if self.controller:
            delivery = self.controller.get_delivery(delivery_id)
            if delivery:
                self.delivery_double_clicked.emit(delivery)
    
    def on_new_delivery(self):
        """Manipulador para criação de nova entrega"""
        # Aqui você pode abrir um diálogo para criar nova entrega
        # e usar o controller.create_delivery com os dados fornecidos
        pass
    
    def on_delivery_moved(self, delivery_id, to_column):
        """
        Manipulador para quando uma entrega é movida pelo controlador
        
        Args:
            delivery_id (int): ID da entrega
            to_column (str): Identificador da coluna de destino
        """
        # Recarregar as entregas após movimento
        self.refresh_data()
    
    def on_delivery_created(self, delivery):
        """
        Manipulador para quando uma nova entrega é criada
        
        Args:
            delivery (Delivery): Objeto de entrega criada
        """
        # Recarregar as entregas após criação
        self.refresh_data()
    
    def show_notification(self, title, message, level=0):
        """
        Exibe uma notificação
        
        Args:
            title (str): Título da notificação
            message (str): Mensagem da notificação
            level (int): Nível da notificação (0=info, 1=warning, 2=error)
        """
        icon_map = {
            0: QMessageBox.Information,
            1: QMessageBox.Warning,
            2: QMessageBox.Critical
        }
        
        QMessageBox.information(self, title, message, icon_map.get(level, QMessageBox.Information))
