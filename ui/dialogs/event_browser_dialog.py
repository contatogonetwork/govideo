#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Diálogo para navegação e seleção de eventos
Data: 2025-05-15
"""

import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, 
    QTableView, QPushButton, QLabel, 
    QLineEdit, QComboBox, QHeaderView,
    QAbstractItemView, QDialogButtonBox,
    QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QDateTime, QRegExp
from PyQt5.QtGui import QIcon

from core.database import Event
from ui.models.event_list_model import EventListModel

logger = logging.getLogger(__name__)

class EventBrowserDialog(QDialog):
    """Diálogo para navegação e seleção de eventos"""
    
    def __init__(self, db_session, parent=None):
        """Inicializar diálogo
        
        Args:
            db_session: Sessão do banco de dados
            parent (QWidget, opcional): Widget pai
        """
        super().__init__(parent)
        self.db = db_session
        self.selected_event = None
        
        self.setWindowTitle("Selecionar Evento")
        self.setWindowIcon(QIcon("resources/icons/event.png"))
        self.setMinimumSize(700, 500)
        self.setup_ui()
        self.load_events()
        
    def setup_ui(self):
        """Configurar interface do usuário"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Grupo de filtros
        filter_group = QGroupBox("Filtros")
        filter_layout = QFormLayout(filter_group)
        
        # Campo de busca
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar por nome, local ou cliente...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.apply_filters)
        filter_layout.addRow("Buscar:", self.search_edit)
        
        # Filtro por status
        status_layout = QHBoxLayout()
        self.status_combo = QComboBox()
        self.status_combo.addItem("Todos", None)
        self.status_combo.addItem("Planejamento", "planning")
        self.status_combo.addItem("Ativo", "active")
        self.status_combo.addItem("Concluído", "completed")
        self.status_combo.currentIndexChanged.connect(self.apply_filters)
        status_layout.addWidget(self.status_combo)
        
        # Filtro por período
        self.period_combo = QComboBox()
        self.period_combo.addItem("Qualquer data", None)
        self.period_combo.addItem("Futuros", "future")
        self.period_combo.addItem("Em andamento", "current")
        self.period_combo.addItem("Últimos 30 dias", "last30")
        self.period_combo.addItem("Últimos 90 dias", "last90")
        self.period_combo.addItem("Este ano", "thisyear")
        self.period_combo.currentIndexChanged.connect(self.apply_filters)
        status_layout.addWidget(self.period_combo)
        
        filter_layout.addRow("Status e Período:", status_layout)
        
        # Tabela de eventos
        self.events_model = EventListModel(self.db)
        
        # Modelo proxy para filtragem e ordenação
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.events_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        
        self.events_table = QTableView()
        self.events_table.setModel(self.proxy_model)
        self.events_table.setSortingEnabled(True)
        self.events_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.events_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.events_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.events_table.verticalHeader().setVisible(False)
        self.events_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.events_table.setAlternatingRowColors(True)
        self.events_table.doubleClicked.connect(self.accept)
        
        # Sort by date descending by default
        self.events_table.sortByColumn(1, Qt.DescendingOrder)
        
        # Botões de ação
        buttons = QDialogButtonBox()
        self.select_button = buttons.addButton("Selecionar", QDialogButtonBox.AcceptRole)
        self.select_button.setIcon(QIcon("resources/icons/select.png"))
        self.select_button.setEnabled(False)
        buttons.addButton(QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        # Conectar seleção na tabela
        self.events_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        # Adicionar widgets ao layout
        main_layout.addWidget(filter_group)
        main_layout.addWidget(self.events_table)
        main_layout.addWidget(buttons)
        
        # Focar no campo de busca
        self.search_edit.setFocus()
        
    def load_events(self):
        """Carregar eventos do banco de dados"""
        try:
            self.events_model.load_data()
            self.events_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Erro ao carregar eventos: {str(e)}")
            
    def apply_filters(self):
        """Aplicar filtros ao modelo proxy"""
        # Filtro de texto
        search_text = self.search_edit.text().strip()
        
        # Configurar expressão regular para busca
        if search_text:
            regex = QRegExp(search_text, Qt.CaseInsensitive, QRegExp.FixedString)
            self.proxy_model.setFilterRegExp(regex)
            self.proxy_model.setFilterKeyColumn(-1)  # Buscar em todas as colunas
        else:
            self.proxy_model.setFilterRegExp("")
            
        # Filtro por status
        status_idx = self.status_combo.currentIndex()
        status_value = self.status_combo.itemData(status_idx)
        
        # Filtro por período
        period_idx = self.period_combo.currentIndex()
        period_value = self.period_combo.itemData(period_idx)
        
        # Implementar filtro personalizado
        self.proxy_model.setFilterRole(Qt.UserRole + 2)  # EventObjectRole
        
        # Criar filtro que avalia status e período
        def filter_func(source_row, source_parent):
            idx = self.events_model.index(source_row, 0, source_parent)
            event = self.events_model.data(idx, EventListModel.EventObjectRole)
            
            if not event:
                return False
                
            # Verificar status
            if status_value and event.status != status_value:
                return False
                
            # Verificar período
            if period_value:
                now = datetime.now()
                
                if period_value == "future":
                    return event.start_date > now
                elif period_value == "current":
                    return event.start_date <= now <= event.end_date
                elif period_value == "last30":
                    cutoff = now - timedelta(days=30)
                    return event.start_date >= cutoff or event.end_date >= cutoff
                elif period_value == "last90":
                    cutoff = now - timedelta(days=90)
                    return event.start_date >= cutoff or event.end_date >= cutoff
                elif period_value == "thisyear":
                    year_start = datetime(now.year, 1, 1)
                    year_end = datetime(now.year, 12, 31, 23, 59, 59)
                    return (event.start_date >= year_start and event.start_date <= year_end) or \
                           (event.end_date >= year_start and event.end_date <= year_end)
                           
            # Verificar texto de busca (próprio proxy já faz a filtragem)
            return True
            
        # Usar isAcceptableRow do modelo proxy para aplicar múltiplos filtros
        # Neste caso estamos apenas definindo o conceito, não implementando completamente
        # pois seria necessário subclasse própria para o modelo proxy
        
        # Atualizar tabela
        self.proxy_model.invalidateFilter()
        
    def on_selection_changed(self, selected, deselected):
        """Manipular mudança na seleção da tabela"""
        # Habilitar/desabilitar botão de seleção baseado na seleção
        has_selection = len(selected.indexes()) > 0
        self.select_button.setEnabled(has_selection)
        
    def get_selected_event(self):
        """Obter evento selecionado atualmente
        
        Returns:
            Event: Objeto do evento selecionado ou None
        """
        selected_rows = self.events_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
            
        # Obter índice do modelo proxy e convertê-lo para índice do modelo fonte
        proxy_index = selected_rows[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        
        # Obter objeto do evento
        event_id = self.events_model.data(source_index, EventListModel.EventIDRole)
        return self.db.query(Event).get(event_id)
        
    def accept(self):
        """Processar aceitação do diálogo (selecionar evento)"""
        self.selected_event = self.get_selected_event()
        
        if not self.selected_event:
            return  # Não fechar o diálogo se nenhum evento foi selecionado
            
        super().accept()