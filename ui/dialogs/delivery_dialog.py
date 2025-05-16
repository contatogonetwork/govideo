#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Diálogo para criação e edição de entregas
Data: 2025-05-15
Autor: GONETWORK AI
"""

import os
import logging
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QPushButton, QComboBox, QLineEdit, 
    QTextEdit, QDateTimeEdit, QDialogButtonBox, 
    QMessageBox, QGroupBox, QListWidget, QListWidgetItem,
    QFileDialog, QSpinBox, QTabWidget, QSplitter
)
from PyQt5.QtCore import Qt, QDateTime, QDate, QTime, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont

from core.database import Delivery, TeamMember, Activity, Event, DeliveryFile, User

logger = logging.getLogger(__name__)

class DeliveryDialog(QDialog):
    """Diálogo para criar ou editar entregas"""
    
    def __init__(self, db_session, event_id, delivery=None, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.event_id = event_id
        self.delivery = delivery
        self.editing_mode = delivery is not None
        self.uploads_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                             "uploads", "deliveries")
        self.files_to_upload = []  # Lista de arquivos a serem enviados
        
        # Garantir que o diretório de uploads existe
        os.makedirs(self.uploads_directory, exist_ok=True)
        
        # Configurar UI
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Configurar interface do usuário"""
        # Configurar janela
        self.setWindowTitle("Nova Entrega" if not self.editing_mode else "Editar Entrega")
        self.setMinimumWidth(600)
        self.setMinimumHeight(600)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Tabs para organizar as seções
        tab_widget = QTabWidget()
        
        # Tab de informações básicas
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # Formulário de informações básicas
        form_group = QGroupBox("Informações da Entrega")
        form_layout = QFormLayout(form_group)
        
        # Título
        self.title_edit = QLineEdit()
        form_layout.addRow("Título:", self.title_edit)
        
        # Responsável
        self.responsible_combo = QComboBox()
        form_layout.addRow("Responsável:", self.responsible_combo)
        
        # Atividade relacionada
        self.activity_combo = QComboBox()
        self.activity_combo.addItem("Selecione uma atividade", None)
        form_layout.addRow("Atividade:", self.activity_combo)
        
        # Data de entrega
        self.deadline_edit = QDateTimeEdit(QDateTime.currentDateTime().addDays(7))
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setDisplayFormat("dd/MM/yyyy HH:mm")
        form_layout.addRow("Prazo:", self.deadline_edit)
        
        # Prioridade
        self.priority_combo = QComboBox()
        self.priority_combo.addItem("Alta", 1)
        self.priority_combo.addItem("Média-Alta", 2)
        self.priority_combo.addItem("Média", 3)
        self.priority_combo.addItem("Média-Baixa", 4)
        self.priority_combo.addItem("Baixa", 5)
        self.priority_combo.setCurrentIndex(2)  # Média por padrão
        form_layout.addRow("Prioridade:", self.priority_combo)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItem("Pendente", "pending")
        self.status_combo.addItem("Em Andamento", "in_progress")
        self.status_combo.addItem("Em Revisão", "in_review")
        self.status_combo.addItem("Aprovado", "approved")
        self.status_combo.addItem("Entregue", "delivered")
        form_layout.addRow("Status:", self.status_combo)
        
        # Descrição
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Descrição detalhada da entrega...")
        
        # Especificações de formato
        self.format_specs_edit = QTextEdit()
        self.format_specs_edit.setPlaceholderText("Especificações técnicas de formato, resolução, etc...")
        
        # Adicionar formulário ao layout
        basic_layout.addWidget(form_group)
        
        # Adicionar seção de descrição
        description_group = QGroupBox("Descrição")
        description_layout = QVBoxLayout(description_group)
        description_layout.addWidget(self.description_edit)
        basic_layout.addWidget(description_group)
        
        # Adicionar seção de especificações
        specs_group = QGroupBox("Especificações Técnicas")
        specs_layout = QVBoxLayout(specs_group)
        specs_layout.addWidget(self.format_specs_edit)
        basic_layout.addWidget(specs_group)
        
        # Tab de arquivos
        files_tab = QWidget()
        files_layout = QVBoxLayout(files_tab)
        
        # Lista de arquivos
        files_group = QGroupBox("Arquivos")
        files_group_layout = QVBoxLayout(files_group)
        
        self.files_list = QListWidget()
        self.files_list.setSelectionMode(QListWidget.ExtendedSelection)
        
        # Botões de arquivos
        files_buttons_layout = QHBoxLayout()
        
        add_file_btn = QPushButton("Adicionar Arquivo")
        add_file_btn.setIcon(QIcon("resources/icons/add.png"))
        add_file_btn.clicked.connect(self.on_add_file)
        
        remove_file_btn = QPushButton("Remover Arquivo")
        remove_file_btn.setIcon(QIcon("resources/icons/delete.png"))
        remove_file_btn.clicked.connect(self.on_remove_file)
        
        mark_final_btn = QPushButton("Marcar como Final")
        mark_final_btn.setIcon(QIcon("resources/icons/check.png"))
        mark_final_btn.clicked.connect(self.on_mark_final)
        
        files_buttons_layout.addWidget(add_file_btn)
        files_buttons_layout.addWidget(remove_file_btn)
        files_buttons_layout.addWidget(mark_final_btn)
        
        files_group_layout.addWidget(self.files_list)
        files_group_layout.addLayout(files_buttons_layout)
        
        files_layout.addWidget(files_group)
        
        # Adicionar tabs
        tab_widget.addTab(basic_tab, "Informações Básicas")
        tab_widget.addTab(files_tab, "Arquivos")
        
        main_layout.addWidget(tab_widget)
        
        # Botões de ação
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        main_layout.addWidget(button_box)
    
    def load_data(self):
        """Carregar dados para os combos e preencher campos se estiver editando"""
        try:
            # Carregar responsáveis
            responsible_query = self.db.query(TeamMember).order_by(TeamMember.name)
            
            # Adicionar opção "Não atribuído"
            self.responsible_combo.addItem("Não atribuído", None)
            
            # Adicionar membros da equipe
            for member in responsible_query:
                self.responsible_combo.addItem(f"{member.name} ({member.role})", member.id)
            
            # Carregar atividades do evento
            activities = (
                self.db.query(Activity)
                .join(Activity.stage)
                .filter(Stage.event_id == self.event_id)
                .order_by(Activity.start_time)
                .all()
            )
            
            # Adicionar atividades ao combo
            for activity in activities:
                start_time = activity.start_time.strftime('%d/%m %H:%M')
                self.activity_combo.addItem(f"{activity.name} ({start_time})", activity.id)
            
            # Se estiver no modo de edição, preencher campos com dados existentes
            if self.editing_mode and self.delivery:
                # Informações básicas
                self.title_edit.setText(self.delivery.title)
                
                # Responsável
                if self.delivery.responsible_id:
                    index = self.responsible_combo.findData(self.delivery.responsible_id)
                    if index >= 0:
                        self.responsible_combo.setCurrentIndex(index)
                
                # Atividade
                if self.delivery.activity_id:
                    index = self.activity_combo.findData(self.delivery.activity_id)
                    if index >= 0:
                        self.activity_combo.setCurrentIndex(index)
                
                # Prazo
                if self.delivery.deadline:
                    self.deadline_edit.setDateTime(QDateTime(
                        self.delivery.deadline.year,
                        self.delivery.deadline.month,
                        self.delivery.deadline.day,
                        self.delivery.deadline.hour,
                        self.delivery.deadline.minute
                    ))
                
                # Prioridade
                if self.delivery.priority:
                    index = self.priority_combo.findData(self.delivery.priority)
                    if index >= 0:
                        self.priority_combo.setCurrentIndex(index)
                
                # Status
                if self.delivery.status:
                    index = self.status_combo.findData(self.delivery.status)
                    if index >= 0:
                        self.status_combo.setCurrentIndex(index)
                
                # Descrição
                if self.delivery.description:
                    self.description_edit.setText(self.delivery.description)
                
                # Especificações
                if self.delivery.format_specs:
                    self.format_specs_edit.setText(self.delivery.format_specs)
                
                # Carregar arquivos existentes
                if self.delivery.files:
                    for file in self.delivery.files:
                        self._add_file_to_list(file.filename, file.filepath, file.is_final)
        
        except Exception as e:
            logger.error(f"Erro ao carregar dados para o diálogo: {str(e)}")
            QMessageBox.warning(self, "Erro", f"Não foi possível carregar os dados: {str(e)}")
    
    def on_add_file(self):
        """Adicionar um novo arquivo à entrega"""
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar Arquivos", "", 
            "Todos os Arquivos (*);;Vídeos (*.mp4 *.mov *.avi);;Imagens (*.jpg *.png *.gif)", 
            options=options
        )
        
        if files:
            for file_path in files:
                filename = os.path.basename(file_path)
                
                # Gerar caminho para o arquivo no diretório de uploads
                # Na verdade, o arquivo só será copiado quando o usuário salvar a entrega
                target_path = os.path.join(self.uploads_directory, filename)
                
                # Adicionar à lista de arquivos a serem enviados
                self.files_to_upload.append((file_path, target_path))
                
                # Adicionar à lista visual
                self._add_file_to_list(filename, target_path, False)
    
    def on_remove_file(self):
        """Remover arquivos selecionados"""
        selected_items = self.files_list.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            # Verificar se é um arquivo existente ou um novo arquivo
            file_path = item.data(Qt.UserRole)
            
            # Remover da lista visual
            row = self.files_list.row(item)
            self.files_list.takeItem(row)
            
            # Remover da lista de arquivos a serem enviados, se aplicável
            for i, (src, dest) in enumerate(self.files_to_upload):
                if dest == file_path:
                    self.files_to_upload.pop(i)
                    break
    
    def on_mark_final(self):
        """Marcar arquivos selecionados como versão final"""
        selected_items = self.files_list.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            # Alternar o status de "final"
            is_final = not item.data(Qt.UserRole + 1)
            
            # Atualizar o item
            item.setData(Qt.UserRole + 1, is_final)
            
            # Atualizar o texto do item
            filename = os.path.basename(item.data(Qt.UserRole))
            item_text = f"{filename} {'(FINAL)' if is_final else ''}"
            item.setText(item_text)
            
            # Atualizar o estilo
            if is_final:
                item.setTextColor(Qt.darkGreen)
                item.setFont(QFont("Arial", 9, QFont.Bold))
            else:
                item.setTextColor(Qt.black)
                item.setFont(QFont("Arial", 9))
    
    def _add_file_to_list(self, filename, filepath, is_final=False):
        """Adiciona um arquivo à lista visual"""
        item = QListWidgetItem()
        item_text = f"{filename} {'(FINAL)' if is_final else ''}"
        item.setText(item_text)
        item.setData(Qt.UserRole, filepath)  # Caminho do arquivo
        item.setData(Qt.UserRole + 1, is_final)  # Status de "final"
        
        if is_final:
            item.setTextColor(Qt.darkGreen)
            item.setFont(QFont("Arial", 9, QFont.Bold))
        
        self.files_list.addItem(item)
    
    def _upload_files(self):
        """Copia os arquivos selecionados para o diretório de uploads"""
        import shutil
        
        for src_path, dest_path in self.files_to_upload:
            try:
                # Garantir que o diretório de destino existe
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                # Copiar o arquivo
                shutil.copy2(src_path, dest_path)
                logger.info(f"Arquivo copiado: {src_path} -> {dest_path}")
                
            except Exception as e:
                logger.error(f"Erro ao copiar arquivo {src_path}: {str(e)}")
                raise
    
    def accept(self):
        """Salvar a entrega"""
        try:
            # Validar campos obrigatórios
            title = self.title_edit.text().strip()
            if not title:
                QMessageBox.warning(self, "Erro", "O título é obrigatório.")
                return
            
            responsible_id = self.responsible_combo.currentData()
            activity_id = self.activity_combo.currentData()
            deadline = self.deadline_edit.dateTime().toPyDateTime()
            priority = self.priority_combo.currentData()
            status = self.status_combo.currentData()
            description = self.description_edit.toPlainText().strip()
            format_specs = self.format_specs_edit.toPlainText().strip()
            
            # Criar nova entrega ou atualizar existente
            if not self.editing_mode:
                # Obter ID do usuário atual (considerando que está armazenado em algum lugar)
                current_user_id = 1  # Exemplo - na prática, seria o ID do usuário logado
                
                # Criar nova entrega
                self.delivery = Delivery(
                    title=title,
                    description=description,
                    deadline=deadline,
                    format_specs=format_specs,
                    responsible_id=responsible_id,
                    event_id=self.event_id,
                    activity_id=activity_id,
                    priority=priority,
                    status=status,
                    created_by=current_user_id,
                    created_at=datetime.utcnow()
                )
                
                self.db.add(self.delivery)
                self.db.flush()  # Para obter o ID da entrega
                
            else:
                # Atualizar entrega existente
                self.delivery.title = title
                self.delivery.description = description
                self.delivery.deadline = deadline
                self.delivery.format_specs = format_specs
                self.delivery.responsible_id = responsible_id
                self.delivery.activity_id = activity_id
                self.delivery.priority = priority
                self.delivery.status = status
            
            # Processar arquivos
            try:
                # Fazer upload de novos arquivos
                self._upload_files()
                
                # Adicionar novos arquivos ao banco de dados
                for _, file_path in self.files_to_upload:
                    filename = os.path.basename(file_path)
                    
                    # Verificar status de "final"
                    is_final = False
                    for i in range(self.files_list.count()):
                        item = self.files_list.item(i)
                        if item.data(Qt.UserRole) == file_path:
                            is_final = item.data(Qt.UserRole + 1)
                            break
                    
                    # Criar registro de arquivo
                    file_record = DeliveryFile(
                        delivery_id=self.delivery.id,
                        filename=filename,
                        filepath=file_path,
                        file_type=os.path.splitext(filename)[1][1:],  # Extensão sem o ponto
                        version=1,  # Por enquanto, todos são v1
                        upload_time=datetime.utcnow(),
                        uploaded_by=1,  # Exemplo - seria o ID do usuário atual
                        file_size=os.path.getsize(file_path),
                        is_final=is_final
                    )
                    
                    self.db.add(file_record)
                
                # Atualizar status de "final" dos arquivos existentes
                if self.editing_mode:
                    # Procurar por arquivos existentes na lista e atualizar seu status
                    for i in range(self.files_list.count()):
                        item = self.files_list.item(i)
                        file_path = item.data(Qt.UserRole)
                        is_final = item.data(Qt.UserRole + 1)
                        
                        # Verificar se é um arquivo existente (não está na lista de uploads)
                        is_existing = True
                        for _, upload_path in self.files_to_upload:
                            if upload_path == file_path:
                                is_existing = False
                                break
                        
                        if is_existing:
                            # Buscar o arquivo no banco de dados
                            file_record = (
                                self.db.query(DeliveryFile)
                                .filter(
                                    DeliveryFile.delivery_id == self.delivery.id,
                                    DeliveryFile.filepath == file_path
                                ).first()
                            )
                            
                            if file_record:
                                file_record.is_final = is_final
            
            except Exception as e:
                logger.error(f"Erro ao processar arquivos: {str(e)}")
                raise
            
            # Salvar no banco de dados
            self.db.commit()
            
            # Fechar o diálogo
            super().accept()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao salvar entrega: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar a entrega: {str(e)}")
            return
