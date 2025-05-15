#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Diálogo para criar/editar eventos
Data: 2025-05-15
"""

import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QDateEdit, QTimeEdit, QComboBox,
    QTextEdit, QPushButton, QMessageBox, QDialogButtonBox,
    QGroupBox, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QIcon, QFont
from sqlalchemy.exc import SQLAlchemyError

from core.database import Event, Stage

logger = logging.getLogger(__name__)

class EventDialog(QDialog):
    """Diálogo para criar ou editar eventos"""
    
    def __init__(self, db_session, event=None, parent=None):
        """Inicializar diálogo
        
        Args:
            db_session: Sessão do banco de dados
            event (Event, opcional): Evento a editar (None para criar novo)
            parent (QWidget, opcional): Widget pai
        """
        super().__init__(parent)
        self.db = db_session
        self.event = event
        self.event_id = event.id if event else None
        self.setup_ui()
        
        if event:
            self.setWindowTitle("Editar Evento")
            self.populate_fields()
        else:
            self.setWindowTitle("Novo Evento")
            self.set_default_values()
        
        # Configurar diálogo    
        self.setMinimumSize(600, 500)
        self.setModal(True)
            
    def setup_ui(self):
        """Configurar interface do usuário"""
        icon_path = "resources/icons/event.png"
        self.setWindowIcon(QIcon(icon_path))
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Área com scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # Formulário de informações básicas
        basic_group = QGroupBox("Informações Básicas")
        basic_group.setFont(QFont("Arial", 10, QFont.Bold))
        form_layout = QFormLayout(basic_group)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # Nome do evento
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Digite o nome do evento")
        self.name_edit.setToolTip("Nome do evento que será exibido em toda a aplicação")
        form_layout.addRow("Nome:", self.name_edit)
        
        # Data e hora de início
        start_layout = QHBoxLayout()
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setToolTip("Data de início do evento")
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setToolTip("Hora de início do evento")
        start_layout.addWidget(self.start_date_edit, 3)
        start_layout.addWidget(self.start_time_edit, 2)
        form_layout.addRow("Início:", start_layout)
        
        # Data e hora de término
        end_layout = QHBoxLayout()
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setToolTip("Data de término do evento")
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setToolTip("Hora de término do evento")
        end_layout.addWidget(self.end_date_edit, 3)
        end_layout.addWidget(self.end_time_edit, 2)
        form_layout.addRow("Término:", end_layout)
        
        # Local
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("Local do evento")
        self.location_edit.setToolTip("Local onde o evento será realizado")
        form_layout.addRow("Local:", self.location_edit)
        
        # Cliente
        self.client_edit = QLineEdit()
        self.client_edit.setPlaceholderText("Empresa ou cliente")
        self.client_edit.setToolTip("Cliente ou empresa responsável pelo evento")
        form_layout.addRow("Cliente:", self.client_edit)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["planning", "active", "completed"])
        self.status_combo.setToolTip("Status atual do evento")
        form_layout.addRow("Status:", self.status_combo)
        
        # Descrição
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Descrição ou notas sobre o evento")
        self.description_edit.setToolTip("Descrição detalhada ou notas sobre o evento")
        self.description_edit.setMinimumHeight(100)
        form_layout.addRow("Descrição:", self.description_edit)
        
        # Adicionar grupo de informações básicas ao layout de scroll
        scroll_layout.addWidget(basic_group)
        
        # Grupo de palcos/áreas 
        self.stages_group = QGroupBox("Palcos / Áreas")
        self.stages_group.setFont(QFont("Arial", 10, QFont.Bold))
        stages_layout = QVBoxLayout(self.stages_group)
        
        # Explicação para o usuário
        stages_help = QLabel("Adicione os palcos ou áreas que fazem parte do evento. "
                           "Cada palco pode conter atividades específicas.")
        stages_help.setWordWrap(True)
        stages_help.setStyleSheet("color: #6c757d; font-style: italic;")
        stages_layout.addWidget(stages_help)
        
        # Lista de palcos existentes
        self.stages_layout = QVBoxLayout()
        stages_layout.addLayout(self.stages_layout)
        
        # Botão para adicionar novo palco
        add_stage_btn = QPushButton(QIcon("resources/icons/add.png"), "Adicionar Palco/Área")
        add_stage_btn.clicked.connect(self.add_new_stage)
        stages_layout.addWidget(add_stage_btn)
        
        scroll_layout.addWidget(self.stages_group)
        
        # Se for um novo evento, adicionar pelo menos um palco inicial
        if not self.event:
            self.add_stage_row()
            
        # Adicionar espaçador para empurrar conteúdo para cima
        scroll_layout.addStretch()
        
        # Configurar área de rolagem
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
            
        # Botões de ação
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Save).setText("Salvar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        # Conexões
        self.start_date_edit.dateChanged.connect(self.update_end_date)
        
    def set_default_values(self):
        """Definir valores padrão para um novo evento"""
        today = QDate.currentDate()
        now = QTime.currentTime()
        
        # Arredondar para hora inteira seguinte
        if now.minute() > 0:
            now = QTime(now.hour() + 1, 0)
        
        # Datas padrão: hoje até amanhã
        self.start_date_edit.setDate(today)
        self.start_time_edit.setTime(now)
        
        tomorrow = today.addDays(1)
        self.end_date_edit.setDate(tomorrow)
        self.end_time_edit.setTime(now)
        
        # Status padrão: planejamento
        self.status_combo.setCurrentText("planning")
        
    def update_end_date(self, date):
        """Atualizar data final quando a inicial mudar"""
        current_end = self.end_date_edit.date()
        
        # Se data final for anterior à inicial, ajustar
        if current_end < date:
            self.end_date_edit.setDate(date)
            
    def populate_fields(self):
        """Preencher campos com dados do evento existente"""
        if not self.event:
            return
            
        # Informações básicas
        self.name_edit.setText(self.event.name)
        self.location_edit.setText(self.event.location or "")
        self.client_edit.setText(self.event.client or "")
        self.description_edit.setText(self.event.description or "")
        self.status_combo.setCurrentText(self.event.status)
        
        # Data e hora
        start_date = QDate(self.event.start_date.year, self.event.start_date.month, self.event.start_date.day)
        start_time = QTime(self.event.start_date.hour, self.event.start_date.minute)
        self.start_date_edit.setDate(start_date)
        self.start_time_edit.setTime(start_time)
        
        end_date = QDate(self.event.end_date.year, self.event.end_date.month, self.event.end_date.day)
        end_time = QTime(self.event.end_date.hour, self.event.end_date.minute)
        self.end_date_edit.setDate(end_date)
        self.end_time_edit.setTime(end_time)
        
        # Preencher palcos existentes
        if hasattr(self, 'stages_layout'):
            for stage in self.event.stages:
                self.add_stage_row(stage)
                
    def add_new_stage(self):
        """Adicionar linha para novo palco"""
        self.add_stage_row()
        
    def add_stage_row(self, stage=None):
        """Adicionar linha para palco na interface
        
        Args:
            stage (Stage, opcional): Objeto de palco existente
        """
        row_layout = QHBoxLayout()
        
        # Nome do palco
        stage_name = QLineEdit()
        if stage:
            stage_name.setText(stage.name)
        stage_name.setPlaceholderText("Nome do palco/área")
        
        # Localização do palco
        stage_location = QLineEdit()
        if stage and stage.location:
            stage_location.setText(stage.location)
        stage_location.setPlaceholderText("Localização")
        
        # Botão de remover
        remove_btn = QPushButton(QIcon("resources/icons/delete.png"), "")
        remove_btn.setFixedWidth(30)
        remove_btn.setToolTip("Remover este palco")
        
        # Adicionar ao layout
        row_layout.addWidget(stage_name, 3)
        row_layout.addWidget(stage_location, 2)
        row_layout.addWidget(remove_btn)
        
        # Tag para guardar referência ao palco
        if stage:
            row_layout.setProperty("stage_id", stage.id)
            
        # Conectar botão de remover
        remove_btn.clicked.connect(lambda: self.remove_stage_row(row_layout))
        
        # Adicionar ao layout de palcos
        self.stages_layout.addLayout(row_layout)
        
    def remove_stage_row(self, row_layout):
        """Remover linha de palco da interface
        
        Args:
            row_layout (QLayout): Layout da linha a remover
        """
        # Verificar se é um palco existente
        stage_id = row_layout.property("stage_id")
        
        if stage_id is not None:
            # Confirmar exclusão
            confirm = QMessageBox.question(
                self, "Confirmar Exclusão",
                "Excluir este palco removerá também todas as atividades associadas. Continuar?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if confirm != QMessageBox.Yes:
                return
                
        # Remover todos os widgets do layout
        while row_layout.count():
            item = row_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Remover o próprio layout
        self.stages_layout.removeItem(row_layout)
        
    def get_stage_data(self):
        """Obter dados dos palcos da interface
        
        Returns:
            dict: Dicionário com dados de palcos novos e existentes
        """
        stages = {
            'existing': [],  # palcos existentes para manter
            'new': [],       # novos palcos para criar
            'removed': []    # IDs de palcos removidos
        }
        
        if not hasattr(self, 'stages_layout'):
            return stages
            
        # Lista de todos os IDs de palcos existentes
        existing_ids = [stage.id for stage in self.event.stages] if self.event else []
        found_ids = []
        
        # Percorrer layouts de palcos
        for i in range(self.stages_layout.count()):
            item = self.stages_layout.itemAt(i)
            if not item or not item.layout():
                continue
                
            row_layout = item.layout()
            
            # Obter widgets
            name_edit = row_layout.itemAt(0).widget()
            location_edit = row_layout.itemAt(1).widget()
            
            # Pular se o nome estiver vazio
            if not name_edit.text().strip():
                continue
                
            # Verificar se é palco existente
            stage_id = row_layout.property("stage_id")
            
            if stage_id is not None:
                # Palco existente
                stages['existing'].append({
                    'id': stage_id,
                    'name': name_edit.text().strip(),
                    'location': location_edit.text().strip()
                })
                found_ids.append(stage_id)
            else:
                # Novo palco
                stages['new'].append({
                    'name': name_edit.text().strip(),
                    'location': location_edit.text().strip()
                })
                
        # Identificar palcos removidos (que existiam mas não estão mais na interface)
        stages['removed'] = [id for id in existing_ids if id not in found_ids]
        
        return stages
        
    def validate_fields(self):
        """Validar campos obrigatórios
        
        Returns:
            bool: True se os campos são válidos
        """
        # Validar nome
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Campos Obrigatórios", "Por favor, informe o nome do evento.")
            self.name_edit.setFocus()
            return False
            
        # Preparar datas
        start_date = self.start_date_edit.date().toPyDate()
        start_time = self.start_time_edit.time().toPyTime()
        start_datetime = datetime.combine(start_date, start_time)
        
        end_date = self.end_date_edit.date().toPyDate()
        end_time = self.end_time_edit.time().toPyTime()
        end_datetime = datetime.combine(end_date, end_time)
        
        # Validar datas
        if end_datetime <= start_datetime:
            QMessageBox.warning(self, "Datas Inválidas", 
                             "A data e hora de término deve ser posterior à data e hora de início.")
            return False
            
        # Validar palcos - pelo menos um é obrigatório
        has_stage = False
        for i in range(self.stages_layout.count()):
            item = self.stages_layout.itemAt(i)
            if not item or not item.layout():
                continue
                
            row_layout = item.layout()
            name_edit = row_layout.itemAt(0).widget()
            
            if name_edit.text().strip():
                has_stage = True
                break
                
        if not has_stage:
            QMessageBox.warning(self, "Campos Obrigatórios", 
                             "Adicione pelo menos um palco ou área para o evento.")
            return False
            
        return True
        
    def accept(self):
        """Processar o formulário quando o usuário clica em Salvar"""
        # Validar campos obrigatórios
        if not self.validate_fields():
            return
            
        # Preparar datas
        start_date = self.start_date_edit.date().toPyDate()
        start_time = self.start_time_edit.time().toPyTime()
        start_datetime = datetime.combine(start_date, start_time)
        
        end_date = self.end_date_edit.date().toPyDate()
        end_time = self.end_time_edit.time().toPyTime()
        end_datetime = datetime.combine(end_date, end_time)
            
        try:
            if self.event:
                # Atualizar evento existente
                self.event.name = self.name_edit.text().strip()
                self.event.start_date = start_datetime
                self.event.end_date = end_datetime
                self.event.location = self.location_edit.text().strip()
                self.event.client = self.client_edit.text().strip()
                self.event.description = self.description_edit.toPlainText()
                self.event.status = self.status_combo.currentText()
                
                # Processar palcos
                stage_data = self.get_stage_data()
                
                # Atualizar palcos existentes
                for stage_info in stage_data['existing']:
                    stage = self.db.query(Stage).get(stage_info['id'])
                    if stage:
                        stage.name = stage_info['name']
                        stage.location = stage_info['location']
                        
                # Criar novos palcos
                for stage_info in stage_data['new']:
                    new_stage = Stage(
                        event_id=self.event.id,
                        name=stage_info['name'],
                        location=stage_info['location']
                    )
                    self.db.add(new_stage)
                    
                # Remover palcos excluídos
                for stage_id in stage_data['removed']:
                    stage = self.db.query(Stage).get(stage_id)
                    if stage:
                        self.db.delete(stage)
                        
                self.db.commit()
                logger.info(f"Evento ID {self.event.id} atualizado: '{self.event.name}'")
                
            else:
                # Criar novo evento
                new_event = Event(
                    name=self.name_edit.text().strip(),
                    start_date=start_datetime,
                    end_date=end_datetime,
                    location=self.location_edit.text().strip(),
                    client=self.client_edit.text().strip(),
                    description=self.description_edit.toPlainText(),
                    status=self.status_combo.currentText(),
                    created_at=datetime.utcnow(),
                    created_by=1  # ID do usuário atual (implementação futura)
                )
                
                self.db.add(new_event)
                self.db.flush()  # Obter ID do novo evento
                
                # Adicionar palcos
                stage_data = self.get_stage_data()
                
                for stage_info in stage_data['new']:
                    new_stage = Stage(
                        event_id=new_event.id,
                        name=stage_info['name'],
                        location=stage_info['location']
                    )
                    self.db.add(new_stage)
                
                self.db.commit()
                self.event_id = new_event.id
                logger.info(f"Novo evento criado: '{new_event.name}' (ID: {new_event.id})")
                
            # Fechar o diálogo
            super().accept()
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao salvar evento: {str(e)}")
            QMessageBox.critical(self, "Erro de Banco de Dados", 
                               f"Ocorreu um erro ao salvar o evento:\n\n{str(e)}")