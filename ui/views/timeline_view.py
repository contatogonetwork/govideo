#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Visualização de linha do tempo (Timeline) com filtros avançados
Data: 2025-05-15
Autor: GONETWORK AI
"""

import os
import logging
from datetime import datetime, timedelta, time

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, 
    QCalendarWidget, QLabel, QPushButton, QComboBox, 
    QToolBar, QAction, QLineEdit, QFrame, QCheckBox,
    QScrollArea, QDateEdit, QGroupBox, QFormLayout,
    QSpinBox, QSlider, QSplitter, QHeaderView
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QSize, QDate, QDateTime,
    QItemSelectionModel, QSortFilterProxyModel, QModelIndex
)
from PyQt5.QtGui import QIcon, QBrush, QColor, QPainter, QPen, QCursor

from core.database import Event, Activity, Delivery, TeamAssignment, Stage
from ui.models.timeline_model import TimelineModel, TimelineItem

logger = logging.getLogger(__name__)

class TimelineView(QWidget):
    """Visualização de linha do tempo (timeline) com filtros avançados"""
    
    # Sinais
    item_clicked = pyqtSignal(object, str)  # item, tipo
    
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.current_event = None
        self.timeline_model = TimelineModel()
        
        # Configurar interface
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interface do usuário"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Barra de ferramentas
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        
        # Ações da barra de ferramentas
        today_action = QAction(QIcon("resources/icons/event.png"), "Hoje", self)
        today_action.triggered.connect(self.go_to_today)
        toolbar.addAction(today_action)
        
        prev_day_action = QAction(QIcon("resources/icons/undo.png"), "Dia Anterior", self)
        prev_day_action.triggered.connect(self.go_to_previous_day)
        toolbar.addAction(prev_day_action)
        
        next_day_action = QAction(QIcon("resources/icons/redo.png"), "Próximo Dia", self)
        next_day_action.triggered.connect(self.go_to_next_day)
        toolbar.addAction(next_day_action)
        
        toolbar.addSeparator()
        
        zoom_in_action = QAction(QIcon("resources/icons/add.png"), "Aumentar Zoom", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction(QIcon("resources/icons/delete.png"), "Diminuir Zoom", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        toolbar.addSeparator()
        
        refresh_action = QAction(QIcon("resources/icons/refresh.png"), "Atualizar", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
        
        main_layout.addWidget(toolbar)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        
        # Lado esquerdo - Controles
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Adicionar calendário
        calendar_group = QGroupBox("Calendário")
        calendar_layout = QVBoxLayout(calendar_group)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.clicked.connect(self.on_date_selected)
        calendar_layout.addWidget(self.calendar)
        
        left_layout.addWidget(calendar_group)
        
        # Controles de intervalo de data
        date_range_group = QGroupBox("Intervalo de Visualização")
        date_range_layout = QFormLayout(date_range_group)
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.dateChanged.connect(self.on_date_range_changed)
        date_range_layout.addRow("De:", self.start_date_edit)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate().addDays(1))
        self.end_date_edit.dateChanged.connect(self.on_date_range_changed)
        date_range_layout.addRow("Até:", self.end_date_edit)
        
        self.interval_combo = QComboBox()
        self.interval_combo.addItem("15 minutos", 15)
        self.interval_combo.addItem("30 minutos", 30)
        self.interval_combo.addItem("1 hora", 60)
        self.interval_combo.addItem("2 horas", 120)
        self.interval_combo.addItem("6 horas", 360)
        self.interval_combo.setCurrentIndex(2)  # 1 hora como padrão
        self.interval_combo.currentIndexChanged.connect(self.on_interval_changed)
        date_range_layout.addRow("Intervalo:", self.interval_combo)
        
        left_layout.addWidget(date_range_group)
        
        # Filtros
        filters_group = QGroupBox("Filtros")
        filters_layout = QVBoxLayout(filters_group)
        
        # Filtro por tipo
        type_layout = QHBoxLayout()
        type_layout.setSpacing(10)
        
        self.activity_check = QCheckBox("Atividades")
        self.activity_check.setChecked(True)
        self.activity_check.stateChanged.connect(lambda state: self.on_type_filter_changed("activity", state))
        type_layout.addWidget(self.activity_check)
        
        self.delivery_check = QCheckBox("Entregas")
        self.delivery_check.setChecked(True)
        self.delivery_check.stateChanged.connect(lambda state: self.on_type_filter_changed("delivery", state))
        type_layout.addWidget(self.delivery_check)
        
        self.assignment_check = QCheckBox("Equipe")
        self.assignment_check.setChecked(True)
        self.assignment_check.stateChanged.connect(lambda state: self.on_type_filter_changed("assignment", state))
        type_layout.addWidget(self.assignment_check)
        
        self.activation_check = QCheckBox("Ativações")
        self.activation_check.setChecked(True)
        self.activation_check.stateChanged.connect(lambda state: self.on_type_filter_changed("activation", state))
        type_layout.addWidget(self.activation_check)
        
        filters_layout.addLayout(type_layout)
        
        # Filtro por texto
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar por palavra-chave...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        
        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.apply_filters)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        
        filters_layout.addLayout(search_layout)
        
        left_layout.addWidget(filters_group)
        
        # Detalhes do evento
        event_group = QGroupBox("Evento Atual")
        event_layout = QFormLayout(event_group)
        
        self.event_name_label = QLabel("-")
        event_layout.addRow("Nome:", self.event_name_label)
        
        self.event_date_label = QLabel("-")
        event_layout.addRow("Data:", self.event_date_label)
        
        self.event_stages_label = QLabel("-")
        event_layout.addRow("Palcos:", self.event_stages_label)
        
        left_layout.addWidget(event_group)
        
        # Adicionar espaçador
        left_layout.addStretch(1)
        
        # Lado direito - Timeline
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Título da timeline
        self.timeline_title = QLabel("Timeline")
        self.timeline_title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.timeline_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.timeline_title)
        
        # Visualização da timeline
        self.timeline_table = QTableView()
        self.timeline_table.setModel(self.timeline_model)
        self.timeline_table.setShowGrid(True)
        self.timeline_table.setAlternatingRowColors(True)
        self.timeline_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.timeline_table.verticalHeader().setDefaultSectionSize(40)
        self.timeline_table.setSelectionBehavior(QTableView.SelectItems)
        self.timeline_table.setSelectionMode(QTableView.SingleSelection)
        self.timeline_table.clicked.connect(self.on_timeline_clicked)
        self.timeline_table.setStyleSheet("""
            QTableView {
                border: 1px solid #ccc;
                gridline-color: #ddd;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #ccc;
                font-weight: bold;
            }
        """)
        
        right_layout.addWidget(self.timeline_table)
        
        # Legenda das cores
        legend_group = QGroupBox("Legenda")
        legend_layout = QHBoxLayout(legend_group)
        
        self.add_legend_item(legend_layout, "Atividades", QColor(100, 149, 237))
        self.add_legend_item(legend_layout, "Entregas", QColor(255, 165, 0))
        self.add_legend_item(legend_layout, "Equipe", QColor(60, 179, 113))
        self.add_legend_item(legend_layout, "Ativações", QColor(219, 112, 147))
        
        legend_layout.addStretch(1)
        
        right_layout.addWidget(legend_group)
        
        # Adicionar painéis ao splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Definir tamanhos iniciais
        splitter.setSizes([250, 750])
        
        main_layout.addWidget(splitter)
        
        # Inicializar com a data atual
        self.on_date_range_changed()
    
    def add_legend_item(self, layout, text, color):
        """Adiciona um item à legenda de cores"""
        frame = QFrame()
        frame.setFixedSize(16, 16)
        frame.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #888;")
        
        label = QLabel(text)
        
        item_layout = QHBoxLayout()
        item_layout.setSpacing(5)
        item_layout.addWidget(frame)
        item_layout.addWidget(label)
        
        layout.addLayout(item_layout)
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
                    
                from core.database import Event
                event = self.db.query(Event).get(event_id)
                if event:
                    self.current_event = event
                    
                    # Atualizar informações do evento
                    self.event_name_label.setText(event.name)
                    date_range = f"{event.start_date.strftime('%d/%m/%Y')} - {event.end_date.strftime('%d/%m/%Y')}"
                    self.event_date_label.setText(date_range)
                    
                    # Contar palcos
                    stages_count = len(event.stages)
                    self.event_stages_label.setText(f"{stages_count} palco{'s' if stages_count != 1 else ''}")
                    
                    # Definir intervalo de datas
                    self.start_date_edit.setDate(QDate(event.start_date.year, event.start_date.month, event.start_date.day))
                    self.end_date_edit.setDate(QDate(event.end_date.year, event.end_date.month, event.end_date.day))
                    
                    # Atualizar título
                    self.timeline_title.setText(f"Timeline - {event.name}")
                    
                    # Carregar dados da timeline
                    self.load_timeline_data()
                    
            else:
                self.current_event = None
                self.event_name_label.setText("-")
                self.event_date_label.setText("-")
                self.event_stages_label.setText("-")
                self.timeline_title.setText("Timeline")
                
                # Limpar timeline
                self.timeline_model.set_items([])
                
        except Exception as e:
            logger.error(f"Erro ao definir evento para timeline: {str(e)}")
    
    def load_timeline_data(self):
        """Carrega os dados do evento atual para a timeline"""
        if not self.current_event:
            return
            
        try:
            timeline_items = []
            
            # Carregar atividades do evento
            if self.activity_check.isChecked():
                activities = (
                    self.db.query(Activity)
                    .join(Stage)
                    .filter(Stage.event_id == self.current_event.id)
                    .all()
                )
                
                for activity in activities:
                    item = TimelineItem(
                        item_id=activity.id,
                        title=activity.name,
                        start_time=activity.start_time,
                        end_time=activity.end_time,
                        item_type='activity',
                        data={
                            'location': activity.stage.name if activity.stage else 'Sem local',
                            'details': activity.details or '',
                            'type': activity.type or 'Genérica'
                        }
                    )
                    timeline_items.append(item)
            
            # Carregar entregas do evento
            if self.delivery_check.isChecked():
                deliveries = (
                    self.db.query(Delivery)
                    .filter(Delivery.event_id == self.current_event.id)
                    .all()
                )
                
                for delivery in deliveries:
                    # Para entregas sem horário específico, usar o prazo como hora
                    if delivery.deadline:
                        start_time = delivery.deadline - timedelta(hours=2)  # 2 horas antes do prazo
                        end_time = delivery.deadline
                        
                        item = TimelineItem(
                            item_id=delivery.id,
                            title=delivery.title,
                            start_time=start_time,
                            end_time=end_time,
                            item_type='delivery',
                            data={
                                'status': delivery.status or 'Indefinido',
                                'responsible': delivery.responsible.name if delivery.responsible else 'Não atribuído',
                                'priority': str(delivery.priority) if delivery.priority else '3'
                            }
                        )
                        timeline_items.append(item)
            
            # Carregar atribuições da equipe
            if self.assignment_check.isChecked():
                assignments = (
                    self.db.query(TeamAssignment)
                    .join(Activity)
                    .join(Stage)
                    .filter(Stage.event_id == self.current_event.id)
                    .all()
                )
                
                for assignment in assignments:
                    if assignment.activity and assignment.activity.start_time:
                        # Se a atribuição tiver horários específicos, usar eles
                        start_time = assignment.start_time if assignment.start_time else assignment.activity.start_time
                        end_time = assignment.end_time if assignment.end_time else assignment.activity.end_time
                        
                        item = TimelineItem(
                            item_id=assignment.id,
                            title=f"{assignment.member.name if assignment.member else 'Membro'} - {assignment.activity.name if assignment.activity else 'Atividade'}",
                            start_time=start_time,
                            end_time=end_time,
                            item_type='assignment',
                            data={
                                'member': assignment.member.name if assignment.member else 'Não atribuído',
                                'role': assignment.member.role if assignment.member else '',
                                'location': assignment.location or (assignment.activity.stage.name if assignment.activity and assignment.activity.stage else 'Local indefinido'),
                                'status': assignment.status or 'ativo'
                            }
                        )
                        timeline_items.append(item)
            
            # Carregar ativações
            if self.activation_check.isChecked():
                from core.database import Activation
                
                activations = (
                    self.db.query(Activation)
                    .filter(Activation.event_id == self.current_event.id)
                    .all()
                )
                
                for activation in activations:
                    if activation.activity and activation.activity.start_time:
                        item = TimelineItem(
                            item_id=activation.id,
                            title=f"Ativação: {activation.sponsor.name if activation.sponsor else 'Patrocinador'} - {activation.activity.name if activation.activity else 'Atividade'}",
                            start_time=activation.activity.start_time,
                            end_time=activation.activity.end_time,
                            item_type='activation',
                            data={
                                'sponsor': activation.sponsor.name if activation.sponsor else 'Não definido',
                                'status': activation.status.name if activation.status else 'pending'
                            }
                        )
                        timeline_items.append(item)
            
            # Atualizar modelo
            self.timeline_model.set_items(timeline_items)
            
            # Ajustar intervalo de datas
            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().toPyDate()
            interval = self.interval_combo.currentData()
            self.timeline_model.set_date_range(start_date, end_date, interval)
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados da timeline: {str(e)}")
    
    def go_to_today(self):
        """Ir para a data atual"""
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self.start_date_edit.setDate(today)
        self.end_date_edit.setDate(today.addDays(1))
        self.on_date_range_changed()
    
    def go_to_previous_day(self):
        """Ir para o dia anterior"""
        current_date = self.start_date_edit.date()
        new_date = current_date.addDays(-1)
        self.start_date_edit.setDate(new_date)
        self.end_date_edit.setDate(current_date)  # O fim passa a ser o início anterior
        self.calendar.setSelectedDate(new_date)
        self.on_date_range_changed()
    
    def go_to_next_day(self):
        """Ir para o próximo dia"""
        current_end = self.end_date_edit.date()
        new_end = current_end.addDays(1)
        self.start_date_edit.setDate(current_end)  # O início passa a ser o fim anterior
        self.end_date_edit.setDate(new_end)
        self.calendar.setSelectedDate(current_end)
        self.on_date_range_changed()
    
    def on_date_selected(self, date):
        """Quando uma data é selecionada no calendário"""
        self.start_date_edit.setDate(date)
        self.end_date_edit.setDate(date.addDays(1))
        self.on_date_range_changed()
    
    def on_date_range_changed(self):
        """Quando o intervalo de datas é alterado"""
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        interval = self.interval_combo.currentData()
        
        # Verificar se o fim não é anterior ao início
        if end_date < start_date:
            self.end_date_edit.setDate(self.start_date_edit.date().addDays(1))
            end_date = start_date + timedelta(days=1)
        
        # Atualizar modelo
        self.timeline_model.set_date_range(start_date, end_date, interval)
        
        # Se houver um evento selecionado, recarregar os dados
        if self.current_event:
            self.load_timeline_data()
    
    def on_interval_changed(self, index):
        """Quando o intervalo de tempo é alterado"""
        # Atualizar modelo com o novo intervalo
        self.on_date_range_changed()
    
    def on_type_filter_changed(self, item_type, state):
        """Quando um filtro de tipo é alterado"""
        visible = state == Qt.Checked
        self.timeline_model.set_type_visibility(item_type, visible)
        
        # Se houver um evento selecionado, recarregar os dados
        if self.current_event:
            self.load_timeline_data()
    
    def on_search_text_changed(self, text):
        """Quando o texto de pesquisa é alterado"""
        self.timeline_model.set_keyword_filter(text)
    
    def apply_filters(self):
        """Aplica os filtros selecionados"""
        # Recarregar dados da timeline com os filtros atuais
        if self.current_event:
            self.load_timeline_data()
    
    def zoom_in(self):
        """Aumentar o nível de zoom (diminuir intervalo)"""
        current_index = self.interval_combo.currentIndex()
        if current_index > 0:
            self.interval_combo.setCurrentIndex(current_index - 1)
    
    def zoom_out(self):
        """Diminuir o nível de zoom (aumentar intervalo)"""
        current_index = self.interval_combo.currentIndex()
        if current_index < self.interval_combo.count() - 1:
            self.interval_combo.setCurrentIndex(current_index + 1)
    
    def on_timeline_clicked(self, index):
        """Quando um item da timeline é clicado"""
        if not index.isValid():
            return
            
        item = self.timeline_model.data(index, self.timeline_model.ItemRole)
        if item:
            self.item_clicked.emit(item, item.item_type)
    
    def refresh_data(self):
        """Atualiza os dados da timeline"""
        # Recarregar dados da timeline
        if self.current_event:
            self.load_timeline_data()
