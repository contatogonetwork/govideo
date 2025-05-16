#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - View para gerenciamento de ativações patrocinadas
Data: 2025-05-15
Autor: GONETWORK AI
"""

import os
import logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, QComboBox,
    QLabel, QLineEdit, QTextEdit, QFileDialog, QToolBar, QAction, QDialog,
    QMessageBox, QFrame, QSplitter, QHeaderView, QMenu, QToolButton, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QDesktopServices

from ui.models.activation_model import ActivationModel
from core.database import Sponsor, Activation, Event
from core.database_upgrade import ActivationStatus

logger = logging.getLogger(__name__)

class ActivationView(QWidget):
    """View para gerenciamento de ativações patrocinadas"""
    
    # Sinais
    activation_updated = pyqtSignal(int)  # ID da ativação atualizada
    
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.current_event_id = None
        
        # Configurar interface
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar a interface da view"""
        main_layout = QVBoxLayout(self)
        
        # Barra de ferramentas de ações
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        
        # Ação para adicionar nova ativação
        action_add = QAction(QIcon("resources/icons/add.png"), "Nova Ativação", self)
        action_add.triggered.connect(self.on_add_activation)
        toolbar.addAction(action_add)
        
        # Ação para editar ativação selecionada
        action_edit = QAction(QIcon("resources/icons/edit.png"), "Editar Ativação", self)
        action_edit.triggered.connect(self.on_edit_activation)
        toolbar.addAction(action_edit)
        
        # Ação para remover ativação
        action_delete = QAction(QIcon("resources/icons/delete.png"), "Remover Ativação", self)
        action_delete.triggered.connect(self.on_delete_activation)
        toolbar.addAction(action_delete)
        
        toolbar.addSeparator()
        
        # Ação para adicionar evidência
        action_evidence = QAction(QIcon("resources/icons/upload.png"), "Adicionar Evidência", self)
        action_evidence.triggered.connect(self.on_add_evidence)
        toolbar.addAction(action_evidence)
        
        # Ação para marcar como filmado
        action_filmed = QAction(QIcon("resources/icons/analyze.png"), "Marcar como Filmado", self)
        action_filmed.triggered.connect(lambda: self.on_update_status("filmed"))
        toolbar.addAction(action_filmed)
        
        # Ação para marcar como falhou
        action_failed = QAction(QIcon("resources/icons/delete_event.png"), "Marcar como Falhou", self)
        action_failed.triggered.connect(lambda: self.on_update_status("failed"))
        toolbar.addAction(action_failed)
        
        toolbar.addSeparator()
        
        # Ação para atualizar lista
        action_refresh = QAction(QIcon("resources/icons/refresh.png"), "Atualizar Lista", self)
        action_refresh.triggered.connect(self.refresh_activations)
        toolbar.addAction(action_refresh)
        
        main_layout.addWidget(toolbar)
        
        # Filtros
        filter_layout = QHBoxLayout()
        
        # Filtro de patrocinador
        filter_layout.addWidget(QLabel("Patrocinador:"))
        self.sponsor_filter = QComboBox()
        self.sponsor_filter.setMinimumWidth(150)
        self.sponsor_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.sponsor_filter)
        
        # Filtro de status
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos", None)
        self.status_filter.addItem("⏳ Pendente", "pending")
        self.status_filter.addItem("✅ Filmado", "filmed")
        self.status_filter.addItem("❌ Falhou", "failed")
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_filter)
        
        # Filtro de palco
        filter_layout.addWidget(QLabel("Palco:"))
        self.stage_filter = QComboBox()
        self.stage_filter.setMinimumWidth(150)
        self.stage_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.stage_filter)
        
        # Espaçador
        filter_layout.addStretch()
        
        # Campo de busca
        filter_layout.addWidget(QLabel("Buscar:"))
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Digite para buscar...")
        self.search_field.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_field)
        
        main_layout.addLayout(filter_layout)
        
        # Tabela de ativações
        self.activations_table = QTableView()
        self.activations_table.setSelectionBehavior(QTableView.SelectRows)
        self.activations_table.setSelectionMode(QTableView.SingleSelection)
        self.activations_table.setAlternatingRowColors(True)
        self.activations_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.activations_table.customContextMenuRequested.connect(self.show_context_menu)
        self.activations_table.doubleClicked.connect(self.on_activation_double_clicked)
        
        # Configurar o cabeçalho da tabela
        self.activations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Modelo de dados
        self.activation_model = ActivationModel()
        self.activations_table.setModel(self.activation_model)
        
        main_layout.addWidget(self.activations_table)
        
        # Área de detalhes
        details_group = QGroupBox("Detalhes da Ativação")
        details_layout = QVBoxLayout(details_group)
        
        # Informações básicas
        info_layout = QHBoxLayout()
        
        # Logo do patrocinador
        self.sponsor_logo = QLabel()
        self.sponsor_logo.setFixedSize(100, 100)
        self.sponsor_logo.setScaledContents(True)
        self.sponsor_logo.setFrameShape(QFrame.Box)
        info_layout.addWidget(self.sponsor_logo)
        
        # Detalhes textuais
        text_info_layout = QVBoxLayout()
        
        self.activation_title = QLabel()
        self.activation_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        text_info_layout.addWidget(self.activation_title)
        
        self.activation_details = QLabel()
        text_info_layout.addWidget(self.activation_details)
        
        self.activation_status = QLabel()
        self.activation_status.setStyleSheet("font-weight: bold;")
        text_info_layout.addWidget(self.activation_status)
        
        info_layout.addLayout(text_info_layout)
        info_layout.addStretch()
        
        # Miniatura da evidência
        self.evidence_preview = QLabel("Sem Evidência")
        self.evidence_preview.setAlignment(Qt.AlignCenter)
        self.evidence_preview.setFixedSize(120, 90)
        self.evidence_preview.setFrameShape(QFrame.Box)
        self.view_evidence_btn = QPushButton("Ver Evidência")
        self.view_evidence_btn.setEnabled(False)
        self.view_evidence_btn.clicked.connect(self.on_view_evidence)
        
        evidence_layout = QVBoxLayout()
        evidence_layout.addWidget(self.evidence_preview)
        evidence_layout.addWidget(self.view_evidence_btn)
        info_layout.addLayout(evidence_layout)
        
        details_layout.addLayout(info_layout)
        
        # Notas
        details_layout.addWidget(QLabel("Observações:"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setReadOnly(False)
        self.notes_edit.setMaximumHeight(100)
        self.save_notes_btn = QPushButton("Salvar Observações")
        self.save_notes_btn.clicked.connect(self.on_save_notes)
        
        details_layout.addWidget(self.notes_edit)
        details_layout.addWidget(self.save_notes_btn)
        
        main_layout.addWidget(details_group)
          # Definir proporção do splitter
        main_layout.setStretch(2, 3)  # Tabela ocupa mais espaço
        main_layout.setStretch(3, 1)  # Área de detalhes ocupa menos espaço
    
    def set_event(self, event_id):
        """Define o evento atual e atualiza a interface
        
        Args:
            event_id (int): ID do evento
        """
        # Verificar se o parâmetro já é um ID (inteiro)
        if not isinstance(event_id, int) and hasattr(event_id, 'id'):
            event_id = event_id.id
            
        if event_id != self.current_event_id:
            self.current_event_id = event_id
            self.load_filters()
            self.refresh_activations()
    
    def load_filters(self):
        """Carrega os filtros com dados do evento atual"""
        if not self.current_event_id:
            return
        
        try:
            # Carregar patrocinadores
            self.sponsor_filter.clear()
            self.sponsor_filter.addItem("Todos", None)
            
            sponsors = self.db.query(Sponsor).all()
            for sponsor in sponsors:
                self.sponsor_filter.addItem(sponsor.name, sponsor.id)
            
            # Carregar palcos do evento
            self.stage_filter.clear()
            self.stage_filter.addItem("Todos", None)
            
            event = self.db.query(Event).filter_by(id=self.current_event_id).first()
            if event:
                for stage in event.stages:
                    self.stage_filter.addItem(stage.name, stage.id)
        
        except Exception as e:
            logger.error(f"Erro ao carregar filtros: {str(e)}")
            QMessageBox.warning(self, "Erro", f"Não foi possível carregar os filtros: {str(e)}")
    
    def refresh_activations(self):
        """Atualiza a lista de ativações com base nos filtros"""
        if not self.current_event_id:
            return
        
        try:
            # Consulta base
            query = self.db.query(Activation).filter_by(event_id=self.current_event_id)
            
            # Aplicar filtro de patrocinador
            sponsor_id = self.sponsor_filter.currentData()
            if sponsor_id:
                query = query.filter(Activation.sponsor_id == sponsor_id)
            
            # Aplicar filtro de status
            status = self.status_filter.currentData()
            if status:
                query = query.filter(Activation.status == status)
            
            # Aplicar filtro de busca
            search_text = self.search_field.text().strip()
            if search_text:
                query = query.join(Sponsor).filter(
                    (Sponsor.name.ilike(f"%{search_text}%")) |
                    (Activation.description.ilike(f"%{search_text}%"))
                )
            
            # Executar consulta
            activations = query.all()
            
            # Atualizar modelo
            self.activation_model.update_activations(activations)
            
            # Limpar seleção
            self.clear_details()
        
        except Exception as e:
            logger.error(f"Erro ao carregar ativações: {str(e)}")
            QMessageBox.warning(self, "Erro", f"Não foi possível carregar as ativações: {str(e)}")
    
    def apply_filters(self):
        """Aplica os filtros selecionados"""
        self.refresh_activations()
    
    def show_context_menu(self, point):
        """Exibe menu de contexto no clique direito da tabela"""
        index = self.activations_table.indexAt(point)
        if index.isValid():
            menu = QMenu(self)
            
            # Ações do menu
            edit_action = menu.addAction("Editar")
            edit_action.triggered.connect(self.on_edit_activation)
            
            menu.addSeparator()
            
            status_menu = menu.addMenu("Alterar Status")
            pending_action = status_menu.addAction("⏳ Pendente")
            filmed_action = status_menu.addAction("✅ Filmado")
            failed_action = status_menu.addAction("❌ Falhou")
            
            pending_action.triggered.connect(lambda: self.on_update_status("pending"))
            filmed_action.triggered.connect(lambda: self.on_update_status("filmed"))
            failed_action.triggered.connect(lambda: self.on_update_status("failed"))
            
            menu.addSeparator()
            
            evidence_action = menu.addAction("Adicionar Evidência")
            evidence_action.triggered.connect(self.on_add_evidence)
              
            view_evidence_action = menu.addAction("Ver Evidência")
            activation = self.activation_model.get_activation(index.row())
            # Usando location ao invés de evidence_path
            view_evidence_action.setEnabled(activation and activation.location)
            view_evidence_action.triggered.connect(self.on_view_evidence)
            
            menu.addSeparator()
            
            delete_action = menu.addAction("Remover")
            delete_action.triggered.connect(self.on_delete_activation)
            
            # Exibir menu
            menu.exec_(self.activations_table.viewport().mapToGlobal(point))
    
    def on_activation_double_clicked(self, index):
        """Manipula o duplo clique em uma ativação"""
        if index.isValid():
            activation = self.activation_model.get_activation(index.row())
            if activation:
                self.show_activation_details(activation)
    
    def show_activation_details(self, activation):
        """Exibe detalhes da ativação selecionada"""
        if not activation:
            self.clear_details()
            return
        
        # Atualizar título
        sponsor_name = activation.sponsor.name if activation.sponsor else "Desconhecido"
        
        # Extrair o nome da atividade da descrição
        activity_name = "Desconhecida"
        if activation.description:
            if "Atividade:" in activation.description:
                activity_name = activation.description.split("\n")[0].replace("Atividade:", "").strip()
            elif "Palco:" in activation.description:
                activity_name = activation.description.split("\n")[0].strip()
                
        self.activation_title.setText(f"{sponsor_name}: {activity_name}")
        
        # Atualizar detalhes
        self.activation_details.setText(f"Data: {activation.start_date.strftime('%d/%m/%Y %H:%M')} - {activation.end_date.strftime('%H:%M')}")
        
        # Atualizar status
        status_display = self.activation_model.status_display.get(activation.status, activation.status)
        self.activation_status.setText(f"Status: {status_display}")
        
        # Atualizar logo do patrocinador
        if activation.sponsor and activation.sponsor.logo_path and os.path.exists(activation.sponsor.logo_path):
            pixmap = QPixmap(activation.sponsor.logo_path)
            self.sponsor_logo.setPixmap(pixmap)
        else:
            self.sponsor_logo.setText("Sem logo")
        
        # Atualizar evidência - usando location
        if activation.location and os.path.exists(activation.location):
            from ui.utils.media_utils import generate_thumbnail
            thumb = generate_thumbnail(activation.location, (120, 90))
            if thumb:
                self.evidence_preview.setPixmap(thumb)
                self.view_evidence_btn.setEnabled(True)
            else:
                self.evidence_preview.setText("Erro na evidência")
                self.view_evidence_btn.setEnabled(False)
        else:
            self.evidence_preview.setText("Sem evidência")
            self.view_evidence_btn.setEnabled(False)
        
        # Atualizar notas - usando description para as notas
        notes_text = ""
        if activation.description:
            lines = activation.description.split("\n")
            if len(lines) > 1:  # Se tem mais de uma linha, considere a partir da segunda
                notes_text = "\n".join(lines[1:])
                
        self.notes_edit.setText(notes_text)
    
    def clear_details(self):
        """Limpa a área de detalhes"""
        self.activation_title.setText("")
        self.activation_details.setText("")
        self.activation_status.setText("")
        self.sponsor_logo.clear()
        self.evidence_preview.setText("Sem Evidência")
        self.view_evidence_btn.setEnabled(False)
        self.notes_edit.clear()
    
    def on_add_activation(self):
        """Adicionar uma nova ativação"""
        if not self.current_event_id:
            QMessageBox.warning(self, "Aviso", "Selecione um evento primeiro.")
            return
        
        from ui.dialogs.activation_dialog import ActivationDialog
        dialog = ActivationDialog(self.db, self.current_event_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_activations()
    
    def on_edit_activation(self):
        """Editar a ativação selecionada"""
        indexes = self.activations_table.selectedIndexes()
        if not indexes:
            QMessageBox.warning(self, "Aviso", "Selecione uma ativação para editar.")
            return
        
        row = indexes[0].row()
        activation = self.activation_model.get_activation(row)
        if not activation:
            return
        
        from ui.dialogs.activation_dialog import ActivationDialog
        dialog = ActivationDialog(self.db, self.current_event_id, activation, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_activations()
            self.activation_updated.emit(activation.id)
    
    def on_delete_activation(self):
        """Remover a ativação selecionada"""
        indexes = self.activations_table.selectedIndexes()
        if not indexes:
            QMessageBox.warning(self, "Aviso", "Selecione uma ativação para remover.")
            return
        
        row = indexes[0].row()
        activation = self.activation_model.get_activation(row)
        if not activation:
            return
        
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja remover a ativação '{activation.sponsor.name if activation.sponsor else 'Desconhecido'}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete(activation)
                self.db.commit()
                self.refresh_activations()
                QMessageBox.information(self, "Sucesso", "Ativação removida com sucesso.")
            except Exception as e:
                self.db.rollback()
                logger.error(f"Erro ao remover ativação: {str(e)}")
                QMessageBox.critical(self, "Erro", f"Não foi possível remover a ativação: {str(e)}")
    
    def on_update_status(self, status):
        """Atualizar o status da ativação selecionada"""
        indexes = self.activations_table.selectedIndexes()
        if not indexes:
            QMessageBox.warning(self, "Aviso", "Selecione uma ativação para atualizar o status.")
            return
        
        row = indexes[0].row()
        activation = self.activation_model.get_activation(row)
        if not activation:
            return
        
        try:
            activation.status = status if isinstance(status, ActivationStatus) else ActivationStatus(status)
            self.db.commit()
            self.refresh_activations()
            self.activation_updated.emit(activation.id)
            self.show_activation_details(activation)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar status: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Não foi possível atualizar o status: {str(e)}")
    
    def on_add_evidence(self):
        """Adicionar evidência para a ativação selecionada"""
        indexes = self.activations_table.selectedIndexes()
        if not indexes:
            QMessageBox.warning(self, "Aviso", "Selecione uma ativação para adicionar evidência.")
            return
        
        row = indexes[0].row()
        activation = self.activation_model.get_activation(row)
        if not activation:
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Evidência", "",
            "Arquivos de Mídia (*.jpg *.jpeg *.png *.gif *.mp4 *.mov *.avi)"
        )
        
        if file_path:
            try:
                # Criar pasta para evidências se não existir
                evidence_dir = os.path.join("uploads", "evidences")
                os.makedirs(evidence_dir, exist_ok=True)
                
                # Copiar arquivo para a pasta de evidências
                from shutil import copy2
                from datetime import datetime
                
                # Gerar nome único para o arquivo
                file_ext = os.path.splitext(file_path)[1]
                new_filename = f"evidence_{activation.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
                new_path = os.path.join(evidence_dir, new_filename)
                
                # Copiar arquivo
                copy2(file_path, new_path)
                
                # Atualizar caminho no banco de dados - usando location em vez de evidence_path
                activation.location = new_path
                
                # Se for a primeira evidência, marcar como filmado automaticamente
                if activation.status == ActivationStatus.pending:
                    activation.status = "Executada"
                
                self.db.commit()
                self.refresh_activations()
                self.activation_updated.emit(activation.id)
                
                QMessageBox.information(self, "Sucesso", "Evidência adicionada com sucesso.")
                
                # Mostrar detalhes atualizados
                self.show_activation_details(activation)
                
            except Exception as e:
                self.db.rollback()
                logger.error(f"Erro ao adicionar evidência: {str(e)}")
                QMessageBox.critical(self, "Erro", f"Não foi possível adicionar a evidência: {str(e)}")
    
    def on_view_evidence(self):
        """Visualizar a evidência da ativação selecionada"""
        indexes = self.activations_table.selectedIndexes()
        if not indexes:
            return
        
        row = indexes[0].row()
        activation = self.activation_model.get_activation(row)
        # Usando location em vez de evidence_path
        if not activation or not activation.location:
            return
        
        # Abrir o arquivo com o aplicativo padrão do sistema
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(activation.location))
        except Exception as e:
            logger.error(f"Erro ao abrir evidência: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir o arquivo: {str(e)}")
    
    def on_save_notes(self):
        """Salvar observações da ativação selecionada"""
        indexes = self.activations_table.selectedIndexes()
        if not indexes:
            QMessageBox.warning(self, "Aviso", "Selecione uma ativação para salvar observações.")
            return
        
        row = indexes[0].row()
        activation = self.activation_model.get_activation(row)
        if not activation:
            return
        
        try:
            # Extrair a primeira linha (identificador da atividade) e preservá-la
            description = activation.description or ""
            first_line = ""
            if description and ("\n" in description):
                first_line = description.split("\n")[0]
            else:
                first_line = description
                
            # Combinar a primeira linha com as novas notas
            new_description = f"{first_line}\n{self.notes_edit.toPlainText()}"
            activation.description = new_description
            
            self.db.commit()
            QMessageBox.information(self, "Sucesso", "Observações salvas com sucesso.")
            self.activation_updated.emit(activation.id)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao salvar observações: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar as observações: {str(e)}")
