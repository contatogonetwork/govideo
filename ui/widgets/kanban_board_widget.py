#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Widget do Kanban de Entregas
Data: 2025-05-15
"""

import os
import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QFrame, QSizePolicy, QToolBar, QAction,
    QComboBox, QLineEdit, QMenu, QToolButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QMimeData, QByteArray, QPoint
from PyQt5.QtGui import QIcon, QDrag, QPixmap, QPainter, QColor, QBrush

from ui.models.kanban_board_model import KanbanBoardModel

class DeliveryCardWidget(QFrame):
    """Widget de card para o Kanban de entregas"""
    
    clicked = pyqtSignal(object)
    edit_requested = pyqtSignal(object)
    view_requested = pyqtSignal(object)
    
    def __init__(self, delivery, parent=None):
        super().__init__(parent)
        self.delivery = delivery
        self.setObjectName("deliveryCard")
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do card"""
        # Estilo do card
        priority_colors = {
            1: "#4CAF50",  # Verde - baixa
            2: "#FFC107",  # Amarelo - média
            3: "#FF5722",  # Laranja - alta
            4: "#F44336"   # Vermelho - urgente
        }
        
        priority_color = priority_colors.get(self.delivery.priority, priority_colors[2])
        
        self.setStyleSheet(f"""
            #deliveryCard {{
                background-color: #ffffff;
                border-radius: 8px;
                border-left: 5px solid {priority_color};
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                margin: 8px;
                padding: 12px;
            }}
            #cardTitle {{
                font-weight: bold;
                font-size: 14px;
            }}
            #cardDeadline {{
                color: {"#F44336" if self.delivery.is_overdue else "#4CAF50"};
                font-size: 12px;
            }}
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Título
        title_layout = QHBoxLayout()
        self.title_label = QLabel(self.delivery.title)
        self.title_label.setObjectName("cardTitle")
        title_layout.addWidget(self.title_label)
        
        # Badge de prioridade
        priority_label = QLabel()
        priority_text = ["", "Baixa", "Média", "Alta", "Urgente"]
        priority_label.setText(priority_text[self.delivery.priority])
        priority_label.setStyleSheet(f"background-color: {priority_color}; color: white; border-radius: 4px; padding: 2px 5px;")
        title_layout.addWidget(priority_label)
        
        layout.addLayout(title_layout)
        
        # Informações adicionais
        info_layout = QVBoxLayout()
        
        # Editor responsável
        if hasattr(self.delivery, 'responsible') and self.delivery.responsible:
            responsible_label = QLabel(f"Editor: {self.delivery.responsible.name}")
            info_layout.addWidget(responsible_label)
        
        # Prazo
        if self.delivery.deadline:
            days_remaining = self.delivery.days_remaining
            deadline_text = self.delivery.deadline.strftime("%d/%m/%Y")
            
            if days_remaining < 0:
                deadline_text += f" (Atrasado há {abs(int(days_remaining))} dias)"
            elif days_remaining < 1:
                deadline_text += " (Hoje!)"
            else:
                deadline_text += f" (Em {int(days_remaining)} dias)"
                
            deadline_label = QLabel(f"Prazo: {deadline_text}")
            deadline_label.setObjectName("cardDeadline")
            info_layout.addWidget(deadline_label)
        
        layout.addLayout(info_layout)
        
        # Barra de progresso customizada
        if hasattr(self.delivery, 'progress') and self.delivery.progress is not None:
            progress_bg = QFrame()
            progress_bg.setStyleSheet("background-color: #f0f0f0; border-radius: 3px;")
            progress_bg.setFixedHeight(6)
            
            progress_layout = QHBoxLayout(progress_bg)
            progress_layout.setContentsMargins(0, 0, 0, 0)
            progress_layout.setSpacing(0)
            
            progress_bar = QFrame()
            width_pct = int(self.delivery.progress * 100)
            progress_bar.setStyleSheet(f"background-color: {priority_color}; border-radius: 3px;")
            progress_bar.setFixedWidth(width_pct * progress_bg.width() // 100)
            
            progress_layout.addWidget(progress_bar)
            progress_layout.addStretch()
            
            layout.addWidget(progress_bg)
        
        # Abrir espaço
        layout.addStretch()
        
        # Botões de ação
        action_layout = QHBoxLayout()
        
        self.view_btn = QPushButton(QIcon(":/icons/view.png"), "")
        self.view_btn.setToolTip("Ver detalhes")
        self.view_btn.setMaximumWidth(30)
        self.view_btn.clicked.connect(self._on_view_clicked)
        
        self.edit_btn = QPushButton(QIcon(":/icons/edit.png"), "")
        self.edit_btn.setToolTip("Editar entrega")
        self.edit_btn.setMaximumWidth(30)
        self.edit_btn.clicked.connect(self._on_edit_clicked)
        
        action_layout.addWidget(self.view_btn)
        action_layout.addWidget(self.edit_btn)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        # Configurações do frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.setMinimumWidth(250)
        self.setMaximumWidth(300)
        
        # Permitir mouse tracking
        self.setMouseTracking(True)
        
    def mousePressEvent(self, event):
        """Evento de clique do mouse"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.delivery)
            self._start_drag_pos = event.pos()
            
    def mouseMoveEvent(self, event):
        """Evento de movimento do mouse"""
        if hasattr(self, '_start_drag_pos'):
            if (event.pos() - self._start_drag_pos).manhattanLength() < 10:
                return
                
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setData("application/x-deliverycard", QByteArray(str(self.delivery.id).encode()))
            drag.setMimeData(mime_data)
            
            # Criar uma imagem do card para mostrar durante o arrastar
            pixmap = QPixmap(self.size())
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            self.render(painter)
            painter.end()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            
            # Executar a operação de arrastar
            drag.exec_(Qt.MoveAction)
            
    def _on_view_clicked(self):
        """Manipulador de evento para botão de visualização"""
        self.view_requested.emit(self.delivery)
        
    def _on_edit_clicked(self):
        """Manipulador de evento para botão de edição"""
        self.edit_requested.emit(self.delivery)


class KanbanColumn(QFrame):
    """Coluna do Kanban que aceita cards via drag & drop"""
    
    card_dropped = pyqtSignal(int, str)  # ID da entrega, ID da coluna
    
    def __init__(self, title, column_id, parent=None):
        super().__init__(parent)
        self.title = title
        self.column_id = column_id
        self.setup_ui()
        self.setAcceptDrops(True)
        
    def setup_ui(self):
        """Configura a interface da coluna"""
        self.setObjectName(f"kanbanColumn_{self.column_id}")
        self.setStyleSheet(f"""
            #kanbanColumn_{self.column_id} {{
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #dee2e6;
                margin: 5px;
            }}
            #columnHeader {{
                font-weight: bold;
                font-size: 16px;
                padding: 8px;
                background-color: #e9ecef;
                border-radius: 8px 8px 0 0;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Cabeçalho da coluna
        header = QLabel(self.title)
        header.setObjectName("columnHeader")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Área de scroll para cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        # Conteúdo da coluna
        self.content = QWidget()
        self.content.setObjectName(f"columnContent_{self.column_id}")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(8)
        
        scroll.setWidget(self.content)
        layout.addWidget(scroll)
        
        # Esticar para ocupar espaço disponível
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def add_card(self, card):
        """Adiciona um card à coluna"""
        self.content_layout.addWidget(card)
        
    def clear_cards(self):
        """Remove todos os cards da coluna"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def dragEnterEvent(self, event):
        """Evento de entrada de drag"""
        if event.mimeData().hasFormat("application/x-deliverycard"):
            event.acceptProposedAction()
            self.setStyleSheet(f"""
                #kanbanColumn_{self.column_id} {{
                    background-color: rgba(0, 123, 255, 0.1);
                    border-radius: 8px;
                    border: 2px dashed #007bff;
                    margin: 5px;
                }}
                #columnHeader {{
                    font-weight: bold;
                    font-size: 16px;
                    padding: 8px;
                    background-color: #e9ecef;
                    border-radius: 8px 8px 0 0;
                }}
            """)
        
    def dragLeaveEvent(self, event):
        """Evento de saída de drag"""
        self.setStyleSheet(f"""
            #kanbanColumn_{self.column_id} {{
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #dee2e6;
                margin: 5px;
            }}
            #columnHeader {{
                font-weight: bold;
                font-size: 16px;
                padding: 8px;
                background-color: #e9ecef;
                border-radius: 8px 8px 0 0;
            }}
        """)
        
    def dropEvent(self, event):
        """Evento de drop"""
        if event.mimeData().hasFormat("application/x-deliverycard"):
            delivery_id = int(event.mimeData().data("application/x-deliverycard").data().decode())
            self.card_dropped.emit(delivery_id, self.column_id)
            event.acceptProposedAction()
            
            self.setStyleSheet(f"""
                #kanbanColumn_{self.column_id} {{
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    border: 1px solid #dee2e6;
                    margin: 5px;
                }}
                #columnHeader {{
                    font-weight: bold;
                    font-size: 16px;
                    padding: 8px;
                    background-color: #e9ecef;
                    border-radius: 8px 8px 0 0;
                }}
            """)


class KanbanBoardWidget(QWidget):
    """Widget principal do Kanban de entregas"""
    
    card_view_requested = pyqtSignal(object)
    card_edit_requested = pyqtSignal(object)
    card_moved = pyqtSignal(int, str, int)  # delivery_id, column_id, user_id
    
    def __init__(self, controller, user_id, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.user_id = user_id
        self.setup_ui()
        
        # Conectar sinais do controlador
        self.controller.deliveries_updated.connect(self.refresh_cards)
        self.controller.delivery_moved.connect(self.on_delivery_moved)
        
    def setup_ui(self):
        """Configura a interface do Kanban"""
        layout = QVBoxLayout(self)
        
        # Barra de ferramentas
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        # Botão de atualizar
        refresh_action = QAction(QIcon(":/icons/refresh.png"), "Atualizar", self)
        refresh_action.triggered.connect(self.refresh_cards)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # Filtros
        toolbar.addWidget(QLabel("Filtrar:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Todos")
        self.filter_combo.addItem("Minhas Entregas")
        self.filter_combo.addItem("Atrasados")
        self.filter_combo.addItem("Alta Prioridade")
        self.filter_combo.currentIndexChanged.connect(self.apply_filter)
        toolbar.addWidget(self.filter_combo)
        
        toolbar.addSeparator()
        
        # Campo de busca
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar entregas...")
        self.search_edit.setMinimumWidth(200)
        self.search_edit.textChanged.connect(self.apply_search)
        toolbar.addWidget(self.search_edit)
        
        toolbar.addSeparator()
        
        # Botão de adicionar
        add_action = QAction(QIcon(":/icons/add.png"), "Nova Entrega", self)
        add_action.triggered.connect(self.on_add_delivery)
        toolbar.addAction(add_action)
        
        # Menu de opções
        options_button = QToolButton()
        options_button.setIcon(QIcon(":/icons/settings.png"))
        options_button.setPopupMode(QToolButton.InstantPopup)
        
        options_menu = QMenu(options_button)
        options_menu.addAction("Exportar Kanban", self.on_export_kanban)
        options_menu.addAction("Configurar Colunas", self.on_configure_columns)
        options_button.setMenu(options_menu)
        
        toolbar.addWidget(options_button)
        
        layout.addWidget(toolbar)
        
        # Layout de colunas do Kanban
        kanban_layout = QHBoxLayout()
        
        # Criar colunas
        self.columns = {}
        column_ids = ["pending", "editing", "reviewing", "completed"]
        column_titles = ["Pendente", "Em Edição", "Em Revisão", "Concluído"]
        
        for i, (col_id, title) in enumerate(zip(column_ids, column_titles)):
            column = KanbanColumn(title, col_id, self)
            column.card_dropped.connect(self.on_card_dropped)
            kanban_layout.addWidget(column)
            self.columns[col_id] = column
        
        layout.addLayout(kanban_layout)
    
    def refresh_cards(self):
        """Atualiza os cards do Kanban"""
        # Limpar todas as colunas
        for column in self.columns.values():
            column.clear_cards()
        
        # Recarregar entregas do controlador
        deliveries = self.controller.load_deliveries(
            self.controller.current_event_id, 
            self.controller.current_filters
        )
        
        # Mapear entregas para colunas
        column_mapping = {
            "pending": [],
            "in_progress": [],
            "review": [],
            "approved": [],
            "published": []
        }
        
        for delivery in deliveries:
            status = delivery.status or "pending"
            column_mapping[status].append(delivery)
        
        # Adicionar cards às colunas
        for delivery in column_mapping["pending"]:
            self._add_card_to_column(delivery, "pending")
            
        for delivery in column_mapping["in_progress"]:
            self._add_card_to_column(delivery, "editing")
            
        for delivery in column_mapping["review"]:
            self._add_card_to_column(delivery, "reviewing")
            
        for delivery in column_mapping["approved"] + column_mapping["published"]:
            self._add_card_to_column(delivery, "completed")
    
    def _add_card_to_column(self, delivery, column_id):
        """Adiciona um card à coluna especificada"""
        if column_id not in self.columns:
            return
            
        card = DeliveryCardWidget(delivery, self)
        card.view_requested.connect(self.card_view_requested)
        card.edit_requested.connect(self.card_edit_requested)
        
        self.columns[column_id].add_card(card)
    
    def on_delivery_moved(self, delivery_id, column_id):
        """Manipulador para quando uma entrega é movida no controlador"""
        self.refresh_cards()
    
    def on_card_dropped(self, delivery_id, column_id):
        """Manipulador para quando um card é solto em uma coluna"""
        self.card_moved.emit(delivery_id, column_id, self.user_id)
        
        # O controlador irá emitir um sinal de delivery_moved quando a operação for concluída
        # que por sua vez chamará refresh_cards
    
    def apply_filter(self, index):
        """Aplica um filtro predefinido"""
        filters = self.controller.current_filters.copy()
        
        # Resetar filtros específicos
        filters.pop('responsible_id', None)
        filters.pop('priority', None)
        filters.pop('status', None)
        
        if index == 1:  # Minhas Entregas
            filters['responsible_id'] = self.user_id
        elif index == 2:  # Atrasados
            filters['status'] = ["pending", "in_progress", "review"]
            # O filtro de data precisa ser implementado no controlador
        elif index == 3:  # Alta Prioridade
            filters['priority'] = [3, 4]  # Alta e Urgente
        
        self.controller.current_filters = filters
        self.controller.reload_deliveries()
    
    def apply_search(self, text):
        """Aplica filtro de texto de busca"""
        if len(text) >= 3 or text == "":
            filters = self.controller.current_filters.copy()
            if text:
                filters['search_text'] = text
            else:
                filters.pop('search_text', None)
                
            self.controller.current_filters = filters
            self.controller.reload_deliveries()
    
    def on_add_delivery(self):
        """Abre diálogo para adicionar nova entrega"""
        pass  # Implementar
        
    def on_export_kanban(self):
        """Exporta o Kanban atual para PDF"""
        pass  # Implementar
        
    def on_configure_columns(self):
        """Abre diálogo para configurar colunas"""
        pass  # Implementar
