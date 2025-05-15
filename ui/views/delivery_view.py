#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Interface de gerenciamento de entregas
Data: 2025-05-15
"""

import os
import logging
import shutil
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QTableView, 
    QHeaderView, QAbstractItemView, QMenu, QAction,
    QMessageBox, QDialog, QGroupBox, QFormLayout,
    QLineEdit, QComboBox, QTextEdit, QDateTimeEdit,
    QTabWidget, QListWidget, QFileDialog, QProgressBar,
    QListWidgetItem, QInputDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QSortFilterProxyModel, QDateTime, QSize
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QColor, QBrush

from modules.deliveries.delivery_tracker import DeliveryTracker
from core.database import Delivery, DeliveryFile, DeliveryComment, TeamMember, User

logger = logging.getLogger(__name__)

class DeliveryDialog(QDialog):
    """Diálogo para criar ou editar entrega"""
    
    def __init__(self, db_session, current_event, delivery=None, parent=None):
        """Inicializar diálogo
        
        Args:
            db_session: Sessão de banco de dados
            current_event: Evento atual
            delivery (Delivery, opcional): Entrega a editar
            parent (QWidget, opcional): Widget pai
        """
        super().__init__(parent)
        self.db = db_session
        self.event = current_event
        self.delivery = delivery
        
        if delivery:
            self.setWindowTitle("Editar Entrega")
        else:
            self.setWindowTitle("Nova Entrega")
            
        self.setup_ui()
        
        if delivery:
            self.populate_fields()
        else:
            self.set_default_values()
            
        # Configurações do diálogo
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
    def setup_ui(self):
        """Configurar a interface do usuário"""
        layout = QVBoxLayout(self)
        
        # Formulário principal
        form_group = QGroupBox("Informações da Entrega")
        form_layout = QFormLayout(form_group)
        
        # Título da entrega
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Título da entrega")
        form_layout.addRow("Título:", self.title_edit)
        
        # Data de prazo
        self.deadline_datetime = QDateTimeEdit()
        self.deadline_datetime.setCalendarPopup(True)
        self.deadline_datetime.setDisplayFormat("dd/MM/yyyy HH:mm")
        form_layout.addRow("Prazo:", self.deadline_datetime)
        
        # Responsável
        self.responsible_combo = QComboBox()
        self.populate_responsible_combo()
        form_layout.addRow("Responsável:", self.responsible_combo)
        
        # Atividade relacionada
        self.activity_combo = QComboBox()
        self.activity_combo.addItem("Nenhuma", None)
        self.populate_activity_combo()
        form_layout.addRow("Atividade:", self.activity_combo)
        
        # Prioridade
        self.priority_combo = QComboBox()
        self.priority_combo.addItem("1 - Alta", 1)
        self.priority_combo.addItem("2 - Média-Alta", 2)
        self.priority_combo.addItem("3 - Média", 3)
        self.priority_combo.addItem("4 - Média-Baixa", 4)
        self.priority_combo.addItem("5 - Baixa", 5)
        self.priority_combo.setCurrentIndex(2)  # Média por padrão
        form_layout.addRow("Prioridade:", self.priority_combo)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItem("Pendente", "pending")
        self.status_combo.addItem("Em Progresso", "in_progress")
        self.status_combo.addItem("Em Revisão", "review")
        self.status_combo.addItem("Aprovado", "approved")
        self.status_combo.addItem("Publicado", "published")
        self.status_combo.addItem("Rejeitado", "rejected")
        form_layout.addRow("Status:", self.status_combo)
        
        # Descrição
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Descrição detalhada da entrega")
        form_layout.addRow("Descrição:", self.description_edit)
        
        # Especificações técnicas
        self.specs_edit = QTextEdit()
        self.specs_edit.setPlaceholderText("Especificações técnicas (formato, resolução, etc.)")
        self.specs_edit.setMaximumHeight(80)
        form_layout.addRow("Especificações:", self.specs_edit)
        
        layout.addWidget(form_group)
        
        # Botões de ação
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Save).setText("Salvar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
    def populate_responsible_combo(self):
        """Preencher combo de responsáveis"""
        if not self.event:
            return
            
        # Opção vazia
        self.responsible_combo.addItem("Selecione um responsável", None)
        
        # Carregar membros da equipe
        try:
            team_members = self.db.query(TeamMember).order_by(TeamMember.name).all()
            
            for member in team_members:
                self.responsible_combo.addItem(f"{member.name} ({member.role})", member.id)
                
        except Exception as e:
            logger.error(f"Erro ao carregar membros da equipe: {str(e)}")
            
    def populate_activity_combo(self):
        """Preencher combo de atividades"""
        if not self.event:
            return
            
        # Carregar todas as atividades do evento
        try:
            from core.database import Activity, Stage
            
            activities = self.db.query(Activity) \
                .join(Activity.stage) \
                .filter(Stage.event_id == self.event.id) \
                .order_by(Activity.start_time) \
                .all()
                
            for activity in activities:
                stage_name = activity.stage.name if activity.stage else "Sem palco"
                start_time = activity.start_time.strftime("%d/%m %H:%M")
                self.activity_combo.addItem(f"{activity.name} ({stage_name} - {start_time})", activity.id)
                
        except Exception as e:
            logger.error(f"Erro ao carregar atividades: {str(e)}")
            
    def set_default_values(self):
        """Definir valores padrão para uma nova entrega"""
        # Data atual + 3 dias como prazo padrão
        default_deadline = QDateTime.currentDateTime().addDays(3)
        self.deadline_datetime.setDateTime(default_deadline)
        
        # Status inicial como pendente
        self.status_combo.setCurrentText("Pendente")
        
    def populate_fields(self):
        """Preencher campos com dados da entrega existente"""
        if not self.delivery:
            return
            
        # Dados básicos
        self.title_edit.setText(self.delivery.title)
        self.description_edit.setText(self.delivery.description or "")
        self.specs_edit.setText(self.delivery.format_specs or "")
        
        # Data de prazo
        deadline = QDateTime(self.delivery.deadline)
        self.deadline_datetime.setDateTime(deadline)
        
        # Responsável
        if self.delivery.responsible_id:
            for i in range(self.responsible_combo.count()):
                if self.responsible_combo.itemData(i) == self.delivery.responsible_id:
                    self.responsible_combo.setCurrentIndex(i)
                    break
                    
        # Atividade
        if self.delivery.activity_id:
            for i in range(self.activity_combo.count()):
                if self.activity_combo.itemData(i) == self.delivery.activity_id:
                    self.activity_combo.setCurrentIndex(i)
                    break
                    
        # Prioridade
        for i in range(self.priority_combo.count()):
            if self.priority_combo.itemData(i) == self.delivery.priority:
                self.priority_combo.setCurrentIndex(i)
                break
                
        # Status
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == self.delivery.status:
                self.status_combo.setCurrentIndex(i)
                break
                
    def accept(self):
        """Processar ao aceitar o diálogo"""
        # Validação básica
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Campos obrigatórios", "O título é obrigatório.")
            self.title_edit.setFocus()
            return
            
        if not self.event:
            QMessageBox.warning(self, "Erro", "Nenhum evento selecionado.")
            return
            
        # Processar dados
        try:
            delivery_tracker = DeliveryTracker(self.db)
            
            # Obter dados comuns
            title = self.title_edit.text().strip()
            deadline = self.deadline_datetime.dateTime().toPyDateTime()
            responsible_id = self.responsible_combo.currentData()
            description = self.description_edit.toPlainText()
            format_specs = self.specs_edit.toPlainText()
            priority = self.priority_combo.currentData()
            activity_id = self.activity_combo.currentData()
            status = self.status_combo.currentData()
            
            if self.delivery:
                # Atualizar entrega existente
                delivery_tracker.update_delivery(
                    delivery_id=self.delivery.id,
                    title=title,
                    deadline=deadline,
                    responsible_id=responsible_id,
                    description=description,
                    format_specs=format_specs,
                    priority=priority,
                    activity_id=activity_id
                )
                
                # Atualizar status se foi alterado
                if status != self.delivery.status:
                    delivery_tracker.update_status(
                        delivery_id=self.delivery.id,
                        status=status,
                        user_id=1  # ID do usuário atual (implementar autenticação futura)
                    )
                    
            else:
                # Criar nova entrega
                self.delivery = delivery_tracker.create_delivery_item(
                    title=title,
                    event_id=self.event.id,
                    deadline=deadline,
                    created_by=1,  # ID do usuário atual (implementar autenticação futura)
                    responsible_id=responsible_id,
                    description=description,
                    format_specs=format_specs,
                    priority=priority,
                    activity_id=activity_id
                )
                
                # Atualizar status se diferente do padrão
                if status != "pending":
                    delivery_tracker.update_status(
                        delivery_id=self.delivery.id,
                        status=status,
                        user_id=1  # ID do usuário atual (implementar autenticação futura)
                    )
                    
            # Fechar o diálogo
            super().accept()
            
        except Exception as e:
            logger.error(f"Erro ao salvar entrega: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao salvar a entrega:\n\n{str(e)}")

class DeliveryView(QWidget):
    """Widget de visualização e gerenciamento de entregas"""
    
    def __init__(self, db_session, parent=None):
        """Inicializar view
        
        Args:
            db_session: Sessão de banco de dados
            parent (QWidget, opcional): Widget pai
        """
        super().__init__(parent)
        self.db = db_session
        self.current_event = None
        self.current_delivery = None
        self.delivery_tracker = DeliveryTracker(db_session)
        self.setup_ui()
        
    def set_current_event(self, event):
        """Define o evento atual e atualiza a lista de entregas
        
        Args:
            event: Objeto evento selecionado
        """
        self.current_event = event
        self.add_delivery_btn.setEnabled(event is not None)
        self.refresh()
        
    def setup_ui(self):
        """Configurar interface do usuário"""
        main_layout = QVBoxLayout(self)
        
        # Barra de ferramentas
        toolbar_layout = QHBoxLayout()
        
        self.add_delivery_btn = QPushButton(self.load_icon("add.png"), "Nova Entrega")
        self.add_delivery_btn.clicked.connect(self.on_add_delivery)
        self.add_delivery_btn.setEnabled(False)  # Habilitado quando houver evento selecionado
        
        self.edit_delivery_btn = QPushButton(self.load_icon("edit.png"), "Editar")
        self.edit_delivery_btn.clicked.connect(self.on_edit_delivery)
        self.edit_delivery_btn.setEnabled(False)
        
        self.delete_delivery_btn = QPushButton(self.load_icon("delete.png"), "Excluir")
        self.delete_delivery_btn.clicked.connect(self.on_delete_delivery)
        self.delete_delivery_btn.setEnabled(False)
        
        self.refresh_btn = QPushButton(self.load_icon("refresh.png"), "Atualizar")
        self.refresh_btn.clicked.connect(self.refresh)
        
        toolbar_layout.addWidget(self.add_delivery_btn)
        toolbar_layout.addWidget(self.edit_delivery_btn)
        toolbar_layout.addWidget(self.delete_delivery_btn)
        toolbar_layout.addStretch()
        
        # Filtro de status
        toolbar_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos", None)
        self.status_filter.addItem("Pendente", "pending")
        self.status_filter.addItem("Em Progresso", "in_progress")
        self.status_filter.addItem("Em Revisão", "review")
        self.status_filter.addItem("Aprovado", "approved")
        self.status_filter.addItem("Publicado", "published")
        self.status_filter.addItem("Rejeitado", "rejected")
        self.status_filter.currentIndexChanged.connect(self.refresh)
        toolbar_layout.addWidget(self.status_filter)
        
        toolbar_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        # Divisor principal
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Lista de entregas
        self.delivery_list = QTableView()
        self.delivery_model = QStandardItemModel()
        self.delivery_model.setHorizontalHeaderLabels(["Título", "Responsável", "Prazo", "Status", "Prioridade"])
        
        self.delivery_list.setModel(self.delivery_model)
        self.delivery_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.delivery_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.delivery_list.setSortingEnabled(True)
        self.delivery_list.setAlternatingRowColors(True)
        self.delivery_list.verticalHeader().setVisible(False)
        self.delivery_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Conectar seleção de entrega
        self.delivery_list.selectionModel().selectionChanged.connect(self.on_delivery_selection_changed)
        self.delivery_list.doubleClicked.connect(self.on_delivery_double_clicked)
        
        # Área de detalhes da entrega
        self.details_tabs = QTabWidget()
        
        # Aba de detalhes gerais
        self.details_tab = QWidget()
        details_layout = QVBoxLayout(self.details_tab)
        
        # Informações da entrega
        self.delivery_info_group = QGroupBox("Detalhes da Entrega")
        info_layout = QFormLayout(self.delivery_info_group)
        
        self.title_label = QLabel("-")
        self.resp_label = QLabel("-")
        self.deadline_label = QLabel("-")
        self.status_label = QLabel("-")
        self.priority_label = QLabel("-")
        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.specs_text = QTextEdit()
        self.specs_text.setReadOnly(True)
        self.specs_text.setMaximumHeight(60)
        
        info_layout.addRow("Título:", self.title_label)
        info_layout.addRow("Responsável:", self.resp_label)
        info_layout.addRow("Prazo:", self.deadline_label)
        info_layout.addRow("Status:", self.status_label)
        info_layout.addRow("Prioridade:", self.priority_label)
        info_layout.addRow("Descrição:", self.desc_text)
        info_layout.addRow("Especificações:", self.specs_text)
        
        details_layout.addWidget(self.delivery_info_group)
        
        # Ações de status
        status_group = QGroupBox("Alterar Status")
        status_layout = QHBoxLayout(status_group)
        
        # Botões para mudar status
        self.status_pending_btn = QPushButton("Pendente")
        self.status_progress_btn = QPushButton("Em Progresso")
        self.status_review_btn = QPushButton("Em Revisão")
        self.status_approved_btn = QPushButton("Aprovado")
        self.status_published_btn = QPushButton("Publicado")
        self.status_rejected_btn = QPushButton("Rejeitado")
        
        self.status_pending_btn.clicked.connect(lambda: self.change_status("pending"))
        self.status_progress_btn.clicked.connect(lambda: self.change_status("in_progress"))
        self.status_review_btn.clicked.connect(lambda: self.change_status("review"))
        self.status_approved_btn.clicked.connect(lambda: self.change_status("approved"))
        self.status_published_btn.clicked.connect(lambda: self.change_status("published"))
        self.status_rejected_btn.clicked.connect(lambda: self.change_status("rejected"))
        
        # Definir cores para os botões de status
        self.status_pending_btn.setStyleSheet("background-color: #7f8c8d; color: white;")
        self.status_progress_btn.setStyleSheet("background-color: #2980b9; color: white;")
        self.status_review_btn.setStyleSheet("background-color: #f39c12; color: white;")
        self.status_approved_btn.setStyleSheet("background-color: #27ae60; color: white;")
        self.status_published_btn.setStyleSheet("background-color: #8e44ad; color: white;")
        self.status_rejected_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        
        # Desabilitar botões inicialmente
        for btn in [self.status_pending_btn, self.status_progress_btn, self.status_review_btn,
                   self.status_approved_btn, self.status_published_btn, self.status_rejected_btn]:
            btn.setEnabled(False)
            
        status_layout.addWidget(self.status_pending_btn)
        status_layout.addWidget(self.status_progress_btn)
        status_layout.addWidget(self.status_review_btn)
        status_layout.addWidget(self.status_approved_btn)
        status_layout.addWidget(self.status_published_btn)
        status_layout.addWidget(self.status_rejected_btn)
        
        details_layout.addWidget(status_group)
        
        # Aba de arquivos
        self.files_tab = QWidget()
        files_layout = QVBoxLayout(self.files_tab)
        
        self.files_toolbar = QHBoxLayout()
        
        self.upload_file_btn = QPushButton(self.load_icon("upload.png"), "Carregar Arquivo")
        self.upload_file_btn.clicked.connect(self.on_upload_file)
        self.upload_file_btn.setEnabled(False)
        
        self.download_file_btn = QPushButton(self.load_icon("download.png"), "Baixar")
        self.download_file_btn.clicked.connect(self.on_download_file)
        self.download_file_btn.setEnabled(False)
        
        self.delete_file_btn = QPushButton(self.load_icon("delete.png"), "Excluir")
        self.delete_file_btn.clicked.connect(self.on_delete_file)
        self.delete_file_btn.setEnabled(False)
        
        self.files_toolbar.addWidget(self.upload_file_btn)
        self.files_toolbar.addWidget(self.download_file_btn)
        self.files_toolbar.addWidget(self.delete_file_btn)
        self.files_toolbar.addStretch()
        
        self.files_list = QListWidget()
        self.files_list.itemSelectionChanged.connect(self.on_file_selection_changed)
        self.files_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        
        files_layout.addLayout(self.files_toolbar)
        files_layout.addWidget(self.files_list)
        
        # Aba de comentários
        self.comments_tab = QWidget()
        comments_layout = QVBoxLayout(self.comments_tab)
        
        self.comments_list = QListWidget()
        
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Digite seu comentário aqui...")
        self.comment_edit.setMaximumHeight(80)
        
        self.add_comment_btn = QPushButton("Adicionar Comentário")
        self.add_comment_btn.clicked.connect(self.on_add_comment)
        self.add_comment_btn.setEnabled(False)
        
        comments_layout.addWidget(self.comments_list)
        comments_layout.addWidget(self.comment_edit)
        comments_layout.addWidget(self.add_comment_btn)
        
        # Adicionar abas ao widget de abas
        self.details_tabs.addTab(self.details_tab, "Detalhes")
        self.details_tabs.addTab(self.files_tab, "Arquivos")
        self.details_tabs.addTab(self.comments_tab, "Comentários")
        
        # Adicionar widgets ao splitter
        self.main_splitter.addWidget(self.delivery_list)
        self.main_splitter.addWidget(self.details_tabs)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(self.main_splitter)
        
        # Barra de filtro
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Buscar:"))
        
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Digite para filtrar entregas...")
        self.filter_edit.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_edit)
        
        main_layout.addLayout(filter_layout)
        
    def load_icon(self, icon_name):
        """Carregar ícone da pasta resources"""
        return QIcon(f"resources/icons/{icon_name}")
        
    def refresh(self):
        """Atualizar lista de entregas"""
        # Limpar modelo atual
        self.delivery_model.removeRows(0, self.delivery_model.rowCount())
        
        if not self.current_event:
            return
            
        try:
            # Obter status filtrado
            status_filter = self.status_filter.currentData()
            
            # Carregar entregas do evento atual
            deliveries = self.delivery_tracker.get_all_deliveries(
                event_id=self.current_event.id,
                status=status_filter
            )
            
            for delivery in deliveries:
                # Criar itens para cada coluna
                title_item = QStandardItem(delivery.title)
                title_item.setData(delivery.id, Qt.UserRole)
                
                # Responsável
                resp_name = delivery.responsible.name if delivery.responsible else "-"
                resp_item = QStandardItem(resp_name)
                
                # Data de prazo formatada
                deadline_str = delivery.deadline.strftime("%d/%m/%Y %H:%M")
                deadline_item = QStandardItem(deadline_str)
                
                # Status traduzido
                status_map = {
                    "pending": "Pendente",
                    "in_progress": "Em Progresso",
                    "review": "Em Revisão",
                    "approved": "Aprovado",
                    "published": "Publicado",
                    "rejected": "Rejeitado"
                }
                status_text = status_map.get(delivery.status, delivery.status)
                status_item = QStandardItem(status_text)
                
                # Definir cor de fundo por status
                status_colors = {
                    "pending": QColor(127, 140, 141),
                    "in_progress": QColor(41, 128, 185),
                    "review": QColor(243, 156, 18),
                    "approved": QColor(39, 174, 96),
                    "published": QColor(142, 68, 173),
                    "rejected": QColor(231, 76, 60)
                }
                if delivery.status in status_colors:
                    status_item.setBackground(status_colors[delivery.status])
                    status_item.setForeground(QColor(255, 255, 255))
                    
                # Prioridade
                priority_map = {
                    1: "1 - Alta",
                    2: "2 - Média-Alta",
                    3: "3 - Média",
                    4: "4 - Média-Baixa",
                    5: "5 - Baixa"
                }
                priority_text = priority_map.get(delivery.priority, str(delivery.priority))
                priority_item = QStandardItem(priority_text)
                
                # Destacar prioridades altas
                if delivery.priority <= 2:
                    priority_item.setForeground(QColor(192, 57, 43))
                
                # Adicionar linha ao modelo
                self.delivery_model.appendRow([title_item, resp_item, deadline_item, status_item, priority_item])
                
            # Aplicar filtro de texto
            self.apply_filter(self.filter_edit.text())
                
        except Exception as e:
            logger.error(f"Erro ao carregar entregas: {str(e)}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar entregas:\n\n{str(e)}")
            
    def apply_filter(self, filter_text):
        """Aplicar filtro de texto à lista de entregas"""
        filter_text = filter_text.lower()
        
        for row in range(self.delivery_model.rowCount()):
            should_show = False
            
            # Buscar em todas as colunas
            for col in range(self.delivery_model.columnCount()):
                item = self.delivery_model.item(row, col)
                if item and filter_text in item.text().lower():
                    should_show = True
                    break
                    
            # Mostrar/ocultar linha
            self.delivery_list.setRowHidden(row, not should_show)
            
    def on_delivery_selection_changed(self, selected, deselected):
        """Manipulador para mudança na seleção de entregas"""
        # Habilitar/desabilitar botões baseado na seleção
        has_selection = len(selected.indexes()) > 0
        self.edit_delivery_btn.setEnabled(has_selection)
        self.delete_delivery_btn.setEnabled(has_selection)
        self.upload_file_btn.setEnabled(has_selection)
        self.add_comment_btn.setEnabled(has_selection)
        
        # Atualizar botões de status
        for btn in [self.status_pending_btn, self.status_progress_btn, self.status_review_btn,
                   self.status_approved_btn, self.status_published_btn, self.status_rejected_btn]:
            btn.setEnabled(has_selection)
        
        if has_selection:
            # Obter a entrega selecionada
            idx = selected.indexes()[0]
            delivery_id = self.delivery_model.data(self.delivery_model.index(idx.row(), 0), Qt.UserRole)
            
            # Carregar detalhes da entrega
            self.load_delivery_details(delivery_id)
        else:
            # Limpar detalhes
            self.clear_delivery_details()
            
    def load_delivery_details(self, delivery_id):
        """Carregar detalhes da entrega selecionada"""
        try:
            # Buscar entrega completa
            delivery = self.delivery_tracker.get_delivery(delivery_id)
            
            if not delivery:
                self.clear_delivery_details()
                return
                
            # Salvar referência à entrega atual
            self.current_delivery = delivery
                
            # Informações básicas
            self.title_label.setText(delivery.title)
            
            # Responsável
            resp_name = delivery.responsible.name if delivery.responsible else "-"
            self.resp_label.setText(resp_name)
            
            # Prazo
            deadline_str = delivery.deadline.strftime("%d/%m/%Y %H:%M")
            self.deadline_label.setText(deadline_str)
            
            # Status
            status_map = {
                "pending": "Pendente",
                "in_progress": "Em Progresso",
                "review": "Em Revisão",
                "approved": "Aprovado",
                "published": "Publicado",
                "rejected": "Rejeitado"
            }
            status_text = status_map.get(delivery.status, delivery.status)
            self.status_label.setText(status_text)
            
            # Aplicar cor ao status
            status_colors = {
                "pending": "#7f8c8d",
                "in_progress": "#2980b9",
                "review": "#f39c12",
                "approved": "#27ae60",
                "published": "#8e44ad",
                "rejected": "#e74c3c"
            }
            if delivery.status in status_colors:
                self.status_label.setStyleSheet(f"color: {status_colors[delivery.status]}; font-weight: bold;")
            else:
                self.status_label.setStyleSheet("")
                
            # Prioridade
            priority_map = {
                1: "1 - Alta",
                2: "2 - Média-Alta",
                3: "3 - Média",
                4: "4 - Média-Baixa",
                5: "5 - Baixa"
            }
            self.priority_label.setText(priority_map.get(delivery.priority, str(delivery.priority)))
            
            # Textos
            self.desc_text.setText(delivery.description or "")
            self.specs_text.setText(delivery.format_specs or "")
            
            # Carregar arquivos
            self.load_delivery_files(delivery)
            
            # Carregar comentários
            self.load_delivery_comments(delivery)
                
        except Exception as e:
            logger.error(f"Erro ao carregar detalhes da entrega: {str(e)}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar detalhes:\n\n{str(e)}")
            
    def load_delivery_files(self, delivery):
        """Carregar arquivos da entrega"""
        # Limpar lista atual
        self.files_list.clear()
        
        # Verificar se há arquivos
        if not delivery.files:
            self.files_list.addItem("Nenhum arquivo disponível")
            return
            
        # Adicionar cada arquivo à lista
        for file in delivery.files:
            item = QListWidgetItem()
            
            # Definir ícone com base no tipo de arquivo
            icon_name = "file.png"
            if file.file_type == "video":
                icon_name = "video.png"
            elif file.file_type == "image":
                icon_name = "image.png"
            elif file.file_type == "audio":
                icon_name = "audio.png"
            elif file.file_type == "document":
                icon_name = "document.png"
                
            item.setIcon(self.load_icon(icon_name))
            
            # Informações do arquivo
            # Obter nome original e tamanho formatado
            filename = file.filename
            size_str = self.format_file_size(file.file_size)
            version_str = f"v{file.version}"
            if file.is_final:
                version_str += " (Final)"
                
            # Timestamp formatado
            timestamp = file.upload_time.strftime("%d/%m/%Y %H:%M")
            
            item.setText(f"{filename} - {version_str}\n{size_str} • {timestamp}")
            
            # Armazenar ID do arquivo como dados
            item.setData(Qt.UserRole, file.id)
            
            # Destacar versão final
            if file.is_final:
                item.setBackground(QBrush(QColor(217, 234, 211)))  # Verde claro
                
            # Configurar tamanho do item
            item.setSizeHint(QSize(item.sizeHint().width(), 44))
            
            # Adicionar à lista
            self.files_list.addItem(item)
    
    def load_delivery_comments(self, delivery):
        """Carregar comentários da entrega"""
        # Limpar lista atual
        self.comments_list.clear()
        
        # Verificar se há comentários
        if not delivery.comments:
            self.comments_list.addItem("Nenhum comentário disponível")
            return
            
        # Ordenar comentários do mais recente para o mais antigo
        sorted_comments = sorted(delivery.comments, key=lambda c: c.timestamp, reverse=True)
        
        # Adicionar cada comentário à lista
        for comment in sorted_comments:
            item = QListWidgetItem()
            
            # Nome do usuário e timestamp formatado
            user_name = comment.user.username if comment.user else "Sistema"
            timestamp = comment.timestamp.strftime("%d/%m/%Y %H:%M")
            
            # Formatar texto do comentário
            header = f"{user_name} - {timestamp}"
            if comment.timecode:
                header += f" (TC: {comment.timecode})"
                
            item.setText(f"{header}\n{comment.comment}")
            
            # Destacar comentários de mudança de status
            if "[Mudança de status]" in comment.comment:
                item.setBackground(QBrush(QColor(225, 225, 225)))
                
            # Configurar tamanho do item
            item.setSizeHint(QSize(item.sizeHint().width(), 54))
            
            # Adicionar à lista
            self.comments_list.addItem(item)
    
    def format_file_size(self, size_bytes):
        """Formatar tamanho de arquivo em bytes para formato legível"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
            
    def clear_delivery_details(self):
        """Limpar detalhes da entrega"""
        self.current_delivery = None
        
        self.title_label.setText("-")
        self.resp_label.setText("-")
        self.deadline_label.setText("-")
        self.status_label.setText("-")
        self.status_label.setStyleSheet("")
        self.priority_label.setText("-")
        self.desc_text.clear()
        self.specs_text.clear()
        
        # Limpar listas
        self.files_list.clear()
        self.comments_list.clear()
        
        # Desabilitar botões relacionados
        self.upload_file_btn.setEnabled(False)
        self.download_file_btn.setEnabled(False)
        self.delete_file_btn.setEnabled(False)
        self.add_comment_btn.setEnabled(False)
        
    def on_delivery_double_clicked(self, index):
        """Manipulador para duplo clique na entrega"""
        self.on_edit_delivery()
        
    def on_add_delivery(self):
        """Manipulador para adicionar nova entrega"""
        if not self.current_event:
            QMessageBox.warning(self, "Aviso", "Selecione um evento primeiro.")
            return
            
        dialog = DeliveryDialog(self.db, self.current_event)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            self.refresh()
            
    def on_edit_delivery(self):
        """Manipulador para editar entrega selecionada"""
        if not self.current_delivery:
            QMessageBox.warning(self, "Aviso", "Selecione uma entrega primeiro.")
            return
            
        dialog = DeliveryDialog(self.db, self.current_event, self.current_delivery)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            self.refresh()
            
            # Re-selecionar a entrega atual
            self.select_delivery(self.current_delivery.id)
            
    def on_delete_delivery(self):
        """Manipulador para excluir entrega selecionada"""
        if not self.current_delivery:
            QMessageBox.warning(self, "Aviso", "Selecione uma entrega primeiro.")
            return
            
        # Confirmar exclusão
        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a entrega '{self.current_delivery.title}'?\n\n"
            f"Esta ação excluirá também todos os arquivos e comentários associados.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Excluir entrega
                self.delivery_tracker.delete_delivery(self.current_delivery.id)
                
                # Atualizar interface
                delivery_id = self.current_delivery.id
                self.current_delivery = None
                self.refresh()
                self.clear_delivery_details()
                
                QMessageBox.information(self, "Sucesso", f"Entrega excluída com sucesso.")
                
            except Exception as e:
                logger.error(f"Erro ao excluir entrega: {str(e)}")
                QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao excluir a entrega:\n\n{str(e)}")
                
    def select_delivery(self, delivery_id):
        """Selecionar entrega na tabela pelo ID"""
        for row in range(self.delivery_model.rowCount()):
            item = self.delivery_model.item(row, 0)
            if item and item.data(Qt.UserRole) == delivery_id:
                self.delivery_list.selectRow(row)
                break
                
    def change_status(self, new_status):
        """Mudar status da entrega atual
        
        Args:
            new_status (str): Novo status a definir
        """
        if not self.current_delivery:
            return
            
        # Mapear status para texto legível
        status_map = {
            "pending": "Pendente",
            "in_progress": "Em Progresso",
            "review": "Em Revisão",
            "approved": "Aprovado",
            "published": "Publicado",
            "rejected": "Rejeitado"
        }
        
        # Verificar se é o mesmo status atual
        if self.current_delivery.status == new_status:
            QMessageBox.information(
                self, 
                "Status Não Alterado", 
                f"A entrega já está com o status '{status_map.get(new_status, new_status)}'."
            )
            return
            
        # Perguntar se quer adicionar comentário (exceto para mudança para pendente)
        comment = None
        if new_status != "pending":
            comment, ok = QInputDialog.getText(
                self,
                f"Alterar Status para {status_map.get(new_status, new_status)}",
                "Comentário sobre a mudança de status (opcional):"
            )
            if not ok:
                return
                
        try:
            # Atualizar status
            self.delivery_tracker.update_status(
                delivery_id=self.current_delivery.id,
                status=new_status,
                user_id=1,  # ID do usuário atual (implementar autenticação futura)
                comment=comment
            )
            
            # Recarregar detalhes
            self.load_delivery_details(self.current_delivery.id)
            
            # Atualizar item na tabela
            self.refresh()
            self.select_delivery(self.current_delivery.id)
            
        except Exception as e:
            logger.error(f"Erro ao alterar status: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao alterar o status:\n\n{str(e)}")
            
    def on_file_selection_changed(self):
        """Manipulador para mudança na seleção de arquivos"""
        has_selection = len(self.files_list.selectedItems()) > 0
        self.download_file_btn.setEnabled(has_selection)
        self.delete_file_btn.setEnabled(has_selection)
        
    def on_file_double_clicked(self, item):
        """Manipulador para duplo clique em arquivo"""
        self.on_download_file()
        
    def on_upload_file(self):
        """Manipulador para upload de arquivo"""
        if not self.current_delivery:
            return
            
        # Abrir diálogo de seleção de arquivo
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo",
            "",
            "Todos os Arquivos (*.*)"
        )
        
        if not file_path:
            return
            
        try:
            # Perguntar se é versão final
            is_final = False
            reply = QMessageBox.question(
                self,
                "Tipo de Versão",
                "Este é um arquivo de versão final?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                is_final = True
                
            # Fazer upload
            self.delivery_tracker.upload_file(
                delivery_id=self.current_delivery.id,
                file_path=file_path,
                user_id=1,  # ID do usuário atual (implementar autenticação futura)
                is_final=is_final
            )
            
            # Recarregar detalhes
            self.load_delivery_details(self.current_delivery.id)
            
        except Exception as e:
            logger.error(f"Erro ao fazer upload de arquivo: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao fazer upload do arquivo:\n\n{str(e)}")
            
    def on_download_file(self):
        """Manipulador para download de arquivo"""
        selected_items = self.files_list.selectedItems()
        if not selected_items:
            return
            
        # Obter ID do arquivo selecionado
        file_id = selected_items[0].data(Qt.UserRole)
        
        try:
            # Buscar informações do arquivo
            file_info = self.delivery_tracker.get_file(file_id)
            
            if not file_info:
                QMessageBox.warning(self, "Erro", "Arquivo não encontrado.")
                return
                
            # Verificar se o arquivo existe
            if not os.path.exists(file_info.filepath):
                QMessageBox.warning(self, "Erro", "Arquivo físico não encontrado no servidor.")
                return
                
            # Abrir diálogo para salvar arquivo
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Arquivo",
                file_info.filename,
                "Todos os Arquivos (*.*)"
            )
            
            if not save_path:
                return
                
            # Copiar arquivo
            shutil.copy2(file_info.filepath, save_path)
            
            QMessageBox.information(self, "Sucesso", f"Arquivo '{file_info.filename}' baixado com sucesso.")
            
        except Exception as e:
            logger.error(f"Erro ao baixar arquivo: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao baixar o arquivo:\n\n{str(e)}")
            
    def on_delete_file(self):
        """Manipulador para excluir arquivo"""
        selected_items = self.files_list.selectedItems()
        if not selected_items:
            return
            
        # Obter ID do arquivo selecionado
        file_id = selected_items[0].data(Qt.UserRole)
        file_name = selected_items[0].text().split(" - ")[0]
        
        # Confirmar exclusão
        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o arquivo '{file_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Excluir arquivo
                self.delivery_tracker.delete_file(file_id)
                
                # Recarregar detalhes
                self.load_delivery_details(self.current_delivery.id)
                
            except Exception as e:
                logger.error(f"Erro ao excluir arquivo: {str(e)}")
                QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao excluir o arquivo:\n\n{str(e)}")
                
    def on_add_comment(self):
        """Manipulador para adicionar comentário"""
        if not self.current_delivery:
            return
            
        comment_text = self.comment_edit.toPlainText().strip()
        
        if not comment_text:
            QMessageBox.warning(self, "Aviso", "Digite um comentário primeiro.")
            return
            
        try:
            # Adicionar comentário
            self.delivery_tracker.add_comment(
                delivery_id=self.current_delivery.id,
                user_id=1,  # ID do usuário atual (implementar autenticação futura)
                comment=comment_text
            )
            
            # Limpar campo de texto
            self.comment_edit.clear()
            
            # Recarregar detalhes
            self.load_delivery_details(self.current_delivery.id)
            
        except Exception as e:
            logger.error(f"Erro ao adicionar comentário: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao adicionar o comentário:\n\n{str(e)}")