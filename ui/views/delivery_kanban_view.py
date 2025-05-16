#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Visualização Kanban para entregas
Data: 2025-05-15
Autor: GONETWORK AI
"""

import os
import logging
from datetime import datetime, timedelta

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

from core.database import Delivery, TeamMember, Activity, Event
from ui.models.delivery_kanban_model import DeliveryKanbanModel, KanbanColumnModel

logger = logging.getLogger(__name__)

class KanbanColumnWidget(QWidget):
    """Widget para exibir uma coluna do Kanban"""
    
    # Sinais
    item_dropped = pyqtSignal(int, object, int)  # ID do item, nova coluna, nova posição
    item_moved = pyqtSignal(int, int, int, int)  # ID do item, coluna antiga, coluna nova, nova posição
    item_clicked = pyqtSignal(int)              # ID do item selecionado
    item_double_clicked = pyqtSignal(int)       # ID do item com duplo clique
    
    def __init__(self, column, index, parent=None):
        super().__init__(parent)
        self.column = column
        self.column_index = index
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
                padding: 6px;
                margin: 2px;
                border-radius: 3px;
            }
            QListView::item:selected {
                background-color: #e0e0ff;
                border: 1px solid #c0c0ff;
            }
        """)
        
        # Conectar sinais
        self.list_view.clicked.connect(self.on_item_clicked)
        self.list_view.doubleClicked.connect(self.on_item_double_clicked)
        
        # Adicionar widgets ao layout
        layout.addWidget(header)
        layout.addWidget(self.list_view)
        
        # Definir cor de fundo
        palette = self.palette()
        palette.setColor(QPalette.Window, self.column.color)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        
        # Definir política de tamanho
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    
    def update_count_label(self):
        """Atualiza o rótulo com o número de itens na coluna"""
        self.count_label.setText(f"{self.column.count()}")
    
    def on_item_clicked(self, index):
        """Tratador para clique em um item"""
        if index.isValid():
            item_id = self.list_model.data(index, KanbanColumnModel.IdRole)
            if item_id:
                self.item_clicked.emit(item_id)
                self.selected_item = item_id
    
    def on_item_double_clicked(self, index):
        """Tratador para duplo clique em um item"""
        if index.isValid():
            item_id = self.list_model.data(index, KanbanColumnModel.IdRole)
            if item_id:
                self.item_double_clicked.emit(item_id)
    
    def update_data(self):
        """Atualiza os dados da coluna"""
        self.list_model.update_items()
        self.update_count_label()


class DeliveryKanbanView(QWidget):
    """Visualização Kanban para entregas"""
    
    # Sinais
    delivery_status_changed = pyqtSignal(int, str)  # ID da entrega, novo status
    delivery_selected = pyqtSignal(int)            # ID da entrega selecionada
    delivery_double_clicked = pyqtSignal(int)      # ID da entrega para editar
    
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.current_event = None
        self.kanban_model = DeliveryKanbanModel()
        self.column_widgets = []
        self.filtered_responsible = None
        self.filtered_activity = None
        self.search_text = ""
        
        # Configurar interface
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interface do usuário"""
        main_layout = QVBoxLayout(self)
        
        # Barra de ferramentas
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # Ações da barra de ferramentas
        add_action = QAction(QIcon("resources/icons/add.png"), "Nova Entrega", self)
        add_action.triggered.connect(self.on_add_delivery)
        toolbar.addAction(add_action)
        
        refresh_action = QAction(QIcon("resources/icons/refresh.png"), "Atualizar", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # Filtro por responsável
        self.responsible_filter = QComboBox()
        self.responsible_filter.addItem("Todos os Responsáveis", None)
        self.responsible_filter.currentIndexChanged.connect(self.apply_filters)
        toolbar.addWidget(QLabel("Responsável:"))
        toolbar.addWidget(self.responsible_filter)
        
        toolbar.addSeparator()
        
        # Filtro por atividade
        self.activity_filter = QComboBox()
        self.activity_filter.addItem("Todas as Atividades", None)
        self.activity_filter.currentIndexChanged.connect(self.apply_filters)
        toolbar.addWidget(QLabel("Atividade:"))
        toolbar.addWidget(self.activity_filter)
        
        toolbar.addSeparator()
        
        # Caixa de pesquisa
        self.search_box = QLineEdit()
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
                column_widget = KanbanColumnWidget(column, i)
                column_widget.item_double_clicked.connect(self.on_delivery_double_clicked)
                column_widget.item_clicked.connect(self.on_delivery_selected)
                column_widget.item_dropped.connect(self.on_item_dropped)
                
                self.columns_layout.addWidget(column_widget)
                self.column_widgets.append(column_widget)
          # Adicionar área de rolagem ao layout principal
        scroll_area.setWidget(columns_widget)
        main_layout.addWidget(scroll_area)
    
    def set_event(self, event_id):
        """Define o evento atual e atualiza a interface
        
        Args:
            event_id (int): ID do evento
        """
        try:
            if event_id:
                # Verificar se o parâmetro já é um ID (inteiro)
                if not isinstance(event_id, int) and hasattr(event_id, 'id'):
                    event_id = event_id.id
                    
                event = self.db.query(Event).get(event_id)
                if event:
                    self.current_event = event
                    # Carregar filtros relacionados ao evento
                    self.load_filter_options()
                    # Carregar entregas do evento
                    self.load_deliveries()
            else:
                self.current_event = None
                self.kanban_model.clear_all()
                self.update_column_widgets()
        
        except Exception as e:
            logger.error(f"Erro ao definir evento para o Kanban: {str(e)}")
            QMessageBox.warning(self, "Erro", f"Não foi possível carregar o evento: {str(e)}")
    
    def load_filter_options(self):
        """Carregar opções de filtro para o evento atual"""
        try:
            if not self.current_event:
                return
            
            # Limpar filtros atuais
            self.responsible_filter.clear()
            self.activity_filter.clear()
            
            self.responsible_filter.addItem("Todos os Responsáveis", None)
            self.activity_filter.addItem("Todas as Atividades", None)
            
            # Carregar responsáveis das entregas do evento atual
            responsibles = (
                self.db.query(TeamMember)
                .join(Delivery, TeamMember.id == Delivery.responsible_id)
                .filter(Delivery.event_id == self.current_event.id)
                .distinct()
                .all()
            )
            
            for responsible in sorted(responsibles, key=lambda x: x.name):
                self.responsible_filter.addItem(
                    f"{responsible.name} ({responsible.role})", 
                    responsible.id
                )
            
            # Carregar atividades do evento atual
            activities = (
                self.db.query(Activity)
                .join(Delivery, Activity.id == Delivery.activity_id)
                .filter(Delivery.event_id == self.current_event.id)
                .distinct()
                .all()
            )
            
            for activity in sorted(activities, key=lambda x: x.name):
                self.activity_filter.addItem(activity.name, activity.id)
        
        except Exception as e:
            logger.error(f"Erro ao carregar opções de filtro: {str(e)}")
    
    def load_deliveries(self):
        """Carregar entregas para o evento atual"""
        try:
            if not self.current_event:
                return
            
            # Limpar dados anteriores
            self.kanban_model.clear_all()
            
            # Construir consulta base
            query = self.db.query(Delivery).filter(Delivery.event_id == self.current_event.id)
            
            # Aplicar filtro de responsável
            if self.filtered_responsible:
                query = query.filter(Delivery.responsible_id == self.filtered_responsible)
            
            # Aplicar filtro de atividade
            if self.filtered_activity:
                query = query.filter(Delivery.activity_id == self.filtered_activity)
            
            # Aplicar filtro de texto
            if self.search_text:
                query = query.filter(
                    Delivery.title.like(f"%{self.search_text}%") |
                    Delivery.description.like(f"%{self.search_text}%")
                )
            
            # Obter todas as entregas
            deliveries = query.all()
            
            # Distribuir entregas nas colunas corretas
            for delivery in deliveries:
                column = self.kanban_model.get_column_by_status(delivery.status)
                if not column:
                    # Se não encontrar coluna para o status, colocar na primeira coluna (pendente)
                    column = self.kanban_model.get_column(0)
                
                if column:
                    column.add_item(delivery)
            
            # Atualizar widgets de coluna
            self.update_column_widgets()
        
        except Exception as e:
            logger.error(f"Erro ao carregar entregas: {str(e)}")
    
    def update_column_widgets(self):
        """Atualiza os widgets de coluna com os novos dados"""
        for widget in self.column_widgets:
            widget.update_data()
    
    def apply_filters(self):
        """Aplicar filtros selecionados"""
        # Obter valor do filtro de responsável
        self.filtered_responsible = self.responsible_filter.currentData()
        
        # Obter valor do filtro de atividade
        self.filtered_activity = self.activity_filter.currentData()
        
        # Recarregar entregas com os filtros aplicados
        self.load_deliveries()
    
    def on_search_text_changed(self, text):
        """Manipulador para mudança no texto de pesquisa"""
        self.search_text = text.strip()
        # Recarregar entregas após um pequeno atraso
        # Aqui poderia ser usado um QTimer para debounce,
        # mas para simplicidade, recarregamos imediatamente
        self.load_deliveries()
    
    def on_delivery_selected(self, delivery_id):
        """Manipulador para seleção de entrega"""
        self.delivery_selected.emit(delivery_id)
    
    def on_delivery_double_clicked(self, delivery_id):
        """Manipulador para duplo clique em uma entrega"""
        self.delivery_double_clicked.emit(delivery_id)
    
    def on_add_delivery(self):
        """Manipulador para adicionar nova entrega"""
        if not self.current_event:
            QMessageBox.warning(self, "Aviso", "Selecione um evento primeiro.")
            return
        
        from ui.dialogs.delivery_dialog import DeliveryDialog
        dialog = DeliveryDialog(self.db, self.current_event.id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_data()
    
    def on_item_dropped(self, delivery_id, column_widget, position):
        """Manipulador para quando um item é solto em uma coluna"""
        try:
            # Encontrar a entrega no banco de dados
            delivery = self.db.query(Delivery).get(delivery_id)
            if not delivery:
                logger.warning(f"Entrega não encontrada: {delivery_id}")
                return
            
            # Obter o status da coluna de destino
            target_column = self.kanban_model.get_column(column_widget.column_index)
            if not target_column:
                logger.warning(f"Coluna não encontrada: {column_widget.column_index}")
                return
            
            # Atualizar status da entrega
            old_status = delivery.status
            delivery.status = target_column.status
            
            # Salvar alteração no banco de dados
            self.db.commit()
            
            # Emitir sinal de alteração de status
            self.delivery_status_changed.emit(delivery_id, target_column.status)
            
            # Recarregar dados
            self.load_deliveries()
            
            logger.info(f"Entrega {delivery_id} movida de '{old_status}' para '{target_column.status}'")
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao processar item solto: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Não foi possível mover a entrega: {str(e)}")
    
    def refresh_data(self):
        """Atualiza os dados da visualização"""
        self.load_filter_options()
        self.load_deliveries()
