#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Interface de Gestão de Eventos
"""

import logging
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QPushButton, QLabel, QTableView, QTreeView, QHeaderView, 
    QAbstractItemView, QCalendarWidget, QGroupBox, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QToolButton, QMenu, QAction,
    QMessageBox, QDialog
)
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal, QModelIndex, QDate
from PyQt5.QtGui import QIcon

from ui.models.event_list_model import EventListModel
from ui.models.activity_model import ActivityModel
from ui.widgets.timeline_view import TimelineView
from ui.dialogs.event_dialog import EventDialog
from ui.dialogs.activity_dialog import ActivityDialog

logger = logging.getLogger(__name__)

class EventManagerView(QWidget):
    """Interface para gerenciamento de eventos"""
    
    event_selected = pyqtSignal(object)
    
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.current_event = None
        self.selected_date = datetime.now().date()
        self.setup_ui()
        self.load_events()
        
    def setup_ui(self):
        """Configurar interface do usuário"""
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        
        # Barra de ferramentas
        self.toolbar_layout = QHBoxLayout()
        
        self.new_event_btn = QPushButton(self.load_icon("new_event.png"), "Novo Evento")
        self.edit_event_btn = QPushButton(self.load_icon("edit_event.png"), "Editar Evento")
        self.delete_event_btn = QPushButton(self.load_icon("delete_event.png"), "Excluir Evento")
        self.refresh_btn = QPushButton(self.load_icon("refresh.png"), "Atualizar")
        
        self.edit_event_btn.setEnabled(False)
        self.delete_event_btn.setEnabled(False)
        
        self.toolbar_layout.addWidget(self.new_event_btn)
        self.toolbar_layout.addWidget(self.edit_event_btn)
        self.toolbar_layout.addWidget(self.delete_event_btn)
        self.toolbar_layout.addStretch()
        self.toolbar_layout.addWidget(self.refresh_btn)
        
        self.main_layout.addLayout(self.toolbar_layout)
        
        # Splitter principal
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Painel esquerdo - Lista de eventos
        self.events_panel = QWidget()
        self.events_layout = QVBoxLayout(self.events_panel)
        
        self.events_label = QLabel("<b>Eventos</b>")
        self.events_table = QTableView()
        self.events_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.events_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.events_table.setSortingEnabled(True)
        self.events_table.verticalHeader().setVisible(False)
        self.events_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.events_model = EventListModel(self.db)
        self.events_table.setModel(self.events_model)
        
        self.events_layout.addWidget(self.events_label)
        self.events_layout.addWidget(self.events_table)
        
        # Painel direito - Detalhes do evento
        self.event_details_panel = QWidget()
        self.event_details_layout = QVBoxLayout(self.event_details_panel)
        
        # Informações básicas do evento
        self.event_info_group = QGroupBox("Informações do Evento")
        self.event_info_layout = QFormLayout(self.event_info_group)
        
        self.event_name_label = QLabel("Nome do Evento:")
        self.event_name_value = QLabel("-")
        self.event_name_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        self.event_date_label = QLabel("Data:")
        self.event_date_value = QLabel("-")
        self.event_date_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        self.event_location_label = QLabel("Local:")
        self.event_location_value = QLabel("-")
        self.event_location_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        self.event_status_label = QLabel("Status:")
        self.event_status_value = QLabel("-")
        self.event_status_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        self.event_desc_label = QLabel("Descrição:")
        self.event_desc_value = QTextEdit()
        self.event_desc_value.setReadOnly(True)
        self.event_desc_value.setMaximumHeight(100)
        
        self.event_info_layout.addRow(self.event_name_label, self.event_name_value)
        self.event_info_layout.addRow(self.event_date_label, self.event_date_value)
        self.event_info_layout.addRow(self.event_location_label, self.event_location_value)
        self.event_info_layout.addRow(self.event_status_label, self.event_status_value)
        self.event_info_layout.addRow(self.event_desc_label, self.event_desc_value)
        
        # Abas para diferentes visualizações de evento
        self.event_tabs = QTabWidget()
        
        # Tab de Cronograma
        self.timeline_tab = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_tab)
        
        self.timeline_toolbar = QHBoxLayout()
        self.add_activity_btn = QPushButton(self.load_icon("add.png"), "Nova Atividade")
        self.add_activity_btn.setEnabled(False)
        self.edit_activity_btn = QPushButton(self.load_icon("edit.png"), "Editar Atividade")
        self.edit_activity_btn.setEnabled(False)
        self.delete_activity_btn = QPushButton(self.load_icon("delete.png"), "Excluir Atividade")
        self.delete_activity_btn.setEnabled(False)
        
        self.timeline_toolbar.addWidget(self.add_activity_btn)
        self.timeline_toolbar.addWidget(self.edit_activity_btn)
        self.timeline_toolbar.addWidget(self.delete_activity_btn)
        self.timeline_toolbar.addStretch()
        
        self.timeline_view = TimelineView()
        self.timeline_view.activity_selected.connect(self.on_timeline_activity_selected)
        
        self.timeline_layout.addLayout(self.timeline_toolbar)
        self.timeline_layout.addWidget(self.timeline_view)
        
        # Tab de Atividades
        self.activities_tab = QWidget()
        self.activities_layout = QVBoxLayout(self.activities_tab)
        
        self.activities_model = ActivityModel()
        self.activities_table = QTableView()
        self.activities_table.setModel(self.activities_model)
        self.activities_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.activities_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.activities_table.setSortingEnabled(True)
        self.activities_table.verticalHeader().setVisible(False)
        self.activities_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.activities_layout.addWidget(self.activities_table)
        
        # Tab de Mapa
        self.map_tab = QWidget()
        self.map_layout = QVBoxLayout(self.map_tab)
        
        self.map_placeholder = QLabel("Visualização de Mapa - Em desenvolvimento")
        self.map_placeholder.setAlignment(Qt.AlignCenter)
        self.map_layout.addWidget(self.map_placeholder)
        
        # Adicionar abas
        self.event_tabs.addTab(self.timeline_tab, self.load_icon("timeline.png"), "Cronograma")
        self.event_tabs.addTab(self.activities_tab, self.load_icon("activity.png"), "Atividades")
        self.event_tabs.addTab(self.map_tab, self.load_icon("map.png"), "Mapa")
        
        # Montar o layout do painel direito
        self.event_details_layout.addWidget(self.event_info_group)
        self.event_details_layout.addWidget(self.event_tabs)
        
        # Adicionar painéis ao splitter
        self.main_splitter.addWidget(self.events_panel)
        self.main_splitter.addWidget(self.event_details_panel)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 3)
        
        # Adicionar splitter ao layout principal
        self.main_layout.addWidget(self.main_splitter)
        
        # Conectar sinais
        self.connect_signals()
    
    def load_icon(self, icon_name):
        """Carrega um ícone da pasta resources"""
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               "resources", "icons", icon_name)
        
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        else:
            logger.warning(f"Ícone não encontrado: {icon_path}")
            return QIcon()
        
    def connect_signals(self):
        """Conectar sinais aos slots"""
        # Botões de evento
        self.new_event_btn.clicked.connect(self.on_new_event)
        self.edit_event_btn.clicked.connect(self.on_edit_event)
        self.delete_event_btn.clicked.connect(self.on_delete_event)
        self.refresh_btn.clicked.connect(self.refresh)
        
        # Tabela de eventos
        self.events_table.selectionModel().selectionChanged.connect(self.on_event_selection_changed)
        self.events_table.doubleClicked.connect(self.on_event_double_clicked)
        
        # Botões de atividade
        self.add_activity_btn.clicked.connect(self.on_add_activity)
        self.edit_activity_btn.clicked.connect(self.on_edit_activity)
        self.delete_activity_btn.clicked.connect(self.on_delete_activity)
        
        # Atividades
        self.activities_table.selectionModel().selectionChanged.connect(self.on_activity_selection_changed)
        self.activities_table.doubleClicked.connect(self.on_activity_double_clicked)
        
    def load_events(self):
        """Carregar eventos do banco de dados"""
        try:
            self.events_model.load_data()
        except Exception as e:
            logger.error(f"Erro ao carregar eventos: {str(e)}")
            QMessageBox.warning(self, "Erro de Banco de Dados", 
                             f"Não foi possível carregar a lista de eventos:\n\n{str(e)}")
        
    def refresh(self):
        """Atualizar dados"""
        self.load_events()
        
        if self.current_event:
            self.update_event_details()
            
    def set_current_event(self, event):
        """Definir evento atual"""
        self.current_event = event
        self.update_event_details()
        
        # Habilitar botões relevantes
        self.add_activity_btn.setEnabled(True)
        self.edit_event_btn.setEnabled(True)
        self.delete_event_btn.setEnabled(True)
        
        # Emitir sinal de evento selecionado (apenas o ID)
        if event and hasattr(event, 'id'):
            self.event_selected.emit(event.id)
        
    def set_selected_date(self, date):
        """Definir data selecionada"""
        if isinstance(date, QDate):
            self.selected_date = date.toPyDate()
        else:
            self.selected_date = date
            
        # Se tiver um evento atual, atualizar visualização da timeline
        if self.current_event:
            self.timeline_view.go_to_date(date)
        
    def update_event_details(self):
        """Atualizar interface com detalhes do evento atual"""
        if not self.current_event:
            return
            
        try:
            # Atualizar campos de informação
            self.event_name_value.setText(self.current_event.name)
            self.event_date_value.setText(f"{self.current_event.start_date.strftime('%d/%m/%Y')} - {self.current_event.end_date.strftime('%d/%m/%Y')}")
            self.event_location_value.setText(self.current_event.location or "Não definido")
            
            # Traduzir status para português
            status_map = {
                "planning": "Planejamento",
                "active": "Ativo",
                "completed": "Concluído"
            }
            self.event_status_value.setText(status_map.get(self.current_event.status, self.current_event.status))
            self.event_desc_value.setPlainText(self.current_event.description or "")
            
            # Atualizar modelo de atividades
            self.activities_model.load_data(self.current_event.id, self.db)
            
            # Atualizar timeline
            activities = []
            for stage in self.current_event.stages:
                for activity in stage.activities:
                    activities.append({
                        'id': activity.id,
                        'name': activity.name,
                        'start_time': activity.start_time,
                        'end_time': activity.end_time,
                        'stage': stage.name,
                        'type': activity.type,
                        'priority': activity.priority
                    })
            
            self.timeline_view.set_activities(activities)
            self.timeline_view.set_date_range(self.current_event.start_date, self.current_event.end_date)
            
            # Se já temos uma data selecionada, ir para ela
            if self.selected_date:
                self.timeline_view.go_to_date(self.selected_date)
                
        except Exception as e:
            logger.error(f"Erro ao atualizar detalhes do evento: {str(e)}", exc_info=True)
            QMessageBox.warning(self, "Erro", f"Ocorreu um erro ao carregar os detalhes do evento:\n\n{str(e)}")
        
    def on_event_selection_changed(self, selected, deselected):
        """Manipular mudança na seleção de eventos"""
        if not selected.indexes():
            return
            
        # Obter índice do modelo
        index = selected.indexes()[0]
        event_id = self.events_model.data(index, role=EventListModel.EventIDRole)
        
        # Buscar evento completo no banco
        from core.database import Event
        try:
            event = self.db.query(Event).get(event_id)
            if event:
                self.set_current_event(event)
        except Exception as e:
            logger.error(f"Erro ao buscar evento selecionado: {str(e)}")
        
    def on_event_double_clicked(self, index):
        """Manipular duplo clique em evento"""
        self.on_edit_event()
        
    def on_timeline_activity_selected(self, activity):
        """Manipular seleção de atividade na timeline"""
        # Buscar atividade na tabela e selecioná-la
        for row in range(self.activities_model.rowCount()):
            idx = self.activities_model.index(row, 0)
            act_id = self.activities_model.data(idx, role=ActivityModel.ActivityIDRole)
            if act_id == activity['id']:
                self.activities_table.selectRow(row)
                # Mudar para a tab de atividades
                self.event_tabs.setCurrentIndex(1)
                break
        
    def on_new_event(self):
        """Criar novo evento"""
        try:
            dialog = EventDialog(self.db)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                self.refresh()
                # Selecionar o evento recém-criado na tabela
                self.select_event_by_id(dialog.event_id)
        except Exception as e:
            logger.error(f"Erro ao criar evento: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao criar o evento:\n\n{str(e)}")
            
    def select_event_by_id(self, event_id):
        """Selecionar evento na tabela pelo ID"""
        if not event_id:
            return
            
        for row in range(self.events_model.rowCount()):
            index = self.events_model.index(row, 0)
            if self.events_model.data(index, role=EventListModel.EventIDRole) == event_id:
                self.events_table.selectRow(row)
                break
            
    def on_edit_event(self):
        """Editar evento selecionado"""
        if not self.current_event:
            QMessageBox.warning(self, "Aviso", "Selecione um evento para editar.")
            return
            
        try:
            dialog = EventDialog(self.db, event=self.current_event)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                self.refresh()
                # Reselecionar o evento na tabela
                self.select_event_by_id(self.current_event.id)
        except Exception as e:
            logger.error(f"Erro ao editar evento: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao editar o evento:\n\n{str(e)}")
            
    def on_delete_event(self):
        """Excluir evento selecionado"""
        if not self.current_event:
            QMessageBox.warning(self, "Aviso", "Selecione um evento para excluir.")
            return
            
        reply = QMessageBox.question(
            self, 'Confirmação',
            f"Tem certeza que deseja excluir o evento '{self.current_event.name}'?\n\n"
            f"Esta ação excluirá também todas as atividades, atribuições e entregas associadas.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete(self.current_event)
                self.db.commit()
                self.current_event = None
                self.refresh()
                
                # Resetar a interface de detalhes
                self.event_name_value.setText("-")
                self.event_date_value.setText("-")
                self.event_location_value.setText("-")
                self.event_status_value.setText("-")
                self.event_desc_value.setPlainText("")
                
                # Desabilitar botões
                self.edit_event_btn.setEnabled(False)
                self.delete_event_btn.setEnabled(False)
                self.add_activity_btn.setEnabled(False)
                self.edit_activity_btn.setEnabled(False)
                self.delete_activity_btn.setEnabled(False)
                
                # Limpar atividades
                self.activities_model.clear()
                self.timeline_view.clear()
                
                QMessageBox.information(self, "Sucesso", "Evento excluído com sucesso!")
                
            except Exception as e:
                logger.error(f"Erro ao excluir evento: {str(e)}", exc_info=True)
                QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao excluir o evento:\n\n{str(e)}")
                self.db.rollback()
                
    def on_add_activity(self):
        """Adicionar nova atividade"""
        if not self.current_event:
            QMessageBox.warning(self, "Aviso", "Selecione um evento para adicionar atividades.")
            return
            
        try:
            dialog = ActivityDialog(self.db, event=self.current_event)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                self.update_event_details()
        except Exception as e:
            logger.error(f"Erro ao adicionar atividade: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao adicionar a atividade:\n\n{str(e)}")
            
    def on_edit_activity(self):
        """Editar atividade selecionada"""
        selected_indexes = self.activities_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Aviso", "Selecione uma atividade para editar.")
            return
            
        index = selected_indexes[0]
        activity_id = self.activities_model.data(index, role=ActivityModel.ActivityIDRole)
        
        # Buscar atividade no banco
        from core.database import Activity
        try:
            activity = self.db.query(Activity).get(activity_id)
            
            if activity:
                dialog = ActivityDialog(self.db, event=self.current_event, activity=activity)
                result = dialog.exec_()
                
                if result == QDialog.Accepted:
                    self.update_event_details()
        except Exception as e:
            logger.error(f"Erro ao editar atividade: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao editar a atividade:\n\n{str(e)}")
                
    def on_delete_activity(self):
        """Excluir atividade selecionada"""
        selected_indexes = self.activities_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Aviso", "Selecione uma atividade para excluir.")
            return
            
        index = selected_indexes[0]
        activity_id = self.activities_model.data(index, role=ActivityModel.ActivityIDRole)
        activity_name = self.activities_model.data(index, role=Qt.DisplayRole)
        
        # Confirmar exclusão
        reply = QMessageBox.question(
            self, 'Confirmação',
            f"Tem certeza que deseja excluir a atividade '{activity_name}'?\n\n"
            f"Esta ação excluirá também todas as atribuições de equipe associadas.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Buscar atividade no banco
                from core.database import Activity
                activity = self.db.query(Activity).get(activity_id)
                
                if activity:
                    self.db.delete(activity)
                    self.db.commit()
                    self.update_event_details()
                    
                    QMessageBox.information(self, "Sucesso", "Atividade excluída com sucesso!")
                    
            except Exception as e:
                logger.error(f"Erro ao excluir atividade: {str(e)}", exc_info=True)
                QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao excluir a atividade:\n\n{str(e)}")
                self.db.rollback()
                
    def on_activity_selection_changed(self, selected, deselected):
        """Manipular mudança na seleção de atividades"""
        has_selection = len(selected.indexes()) > 0
        self.edit_activity_btn.setEnabled(has_selection)
        self.delete_activity_btn.setEnabled(has_selection)
        
    def on_activity_double_clicked(self, index):
        """Manipular duplo clique em atividade"""
        self.on_edit_activity()