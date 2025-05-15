#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Diálogo para criar/editar atividades
Data: 2025-05-15
"""

import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QDateTimeEdit, QComboBox,
    QTextEdit, QPushButton, QMessageBox, QDialogButtonBox,
    QGroupBox, QSpinBox
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QIcon
from sqlalchemy.exc import SQLAlchemyError

from core.database import Activity, Stage

logger = logging.getLogger(__name__)

class ActivityDialog(QDialog):
    """Diálogo para criar ou editar atividades de eventos"""
    
    def __init__(self, db_session, event, activity=None, parent=None):
        """Inicializar diálogo
        
        Args:
            db_session: Sessão do banco de dados
            event: Evento ao qual a atividade pertence
            activity (Activity, opcional): Atividade a editar (None para criar nova)
            parent (QWidget, opcional): Widget pai
        """
        super().__init__(parent)
        self.db = db_session
        self.event = event
        self.activity = activity
        self.activity_id = activity.id if activity else None
        self.setup_ui()
        
        if activity:
            self.setWindowTitle("Editar Atividade")
            self.populate_fields()
        else:
            self.setWindowTitle("Nova Atividade")
            self.set_default_values()
        
        # Configurar diálogo
        self.setMinimumWidth(500)
        self.setModal(True)
            
    def setup_ui(self):
        """Configurar interface do usuário"""
        self.setWindowIcon(QIcon("resources/icons/activity.png"))
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Formulário principal
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # Nome da atividade
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nome da atividade")
        form_layout.addRow("Nome:", self.name_edit)
        
        # Palco/Área
        self.stage_combo = QComboBox()
        self.populate_stages()
        form_layout.addRow("Palco/Área:", self.stage_combo)
        
        # Data/hora de início
        self.start_datetime = QDateTimeEdit()
        self.start_datetime.setCalendarPopup(True)
        self.start_datetime.setDisplayFormat("dd/MM/yyyy HH:mm")
        form_layout.addRow("Início:", self.start_datetime)
        
        # Data/hora de término
        self.end_datetime = QDateTimeEdit()
        self.end_datetime.setCalendarPopup(True)
        self.end_datetime.setDisplayFormat("dd/MM/yyyy HH:mm")
        form_layout.addRow("Término:", self.end_datetime)
        
        # Tipo de atividade
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "show", "activation", "interview", "photo", "setup", "other"
        ])
        form_layout.addRow("Tipo:", self.type_combo)
        
        # Prioridade
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 5)
        self.priority_spin.setValue(3)
        self.priority_spin.setToolTip("1 = Mais alta, 5 = Mais baixa")
        form_layout.addRow("Prioridade:", self.priority_spin)
        
        # Detalhes
        self.details_edit = QTextEdit()
        self.details_edit.setPlaceholderText("Detalhes ou descrição da atividade")
        form_layout.addRow("Detalhes:", self.details_edit)
        
        # Adicionar formulário ao layout principal
        main_layout.addLayout(form_layout)
        
        # Botões
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Save).setText("Salvar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        # Conectar sinais
        self.start_datetime.dateTimeChanged.connect(self.update_end_datetime)
        
    def populate_stages(self):
        """Preencher combobox de palcos/áreas"""
        if not self.event:
            return
            
        for stage in self.event.stages:
            self.stage_combo.addItem(stage.name, stage.id)
            
    def set_default_values(self):
        """Definir valores padrão para uma nova atividade"""
        # Definir hora atual arredondada para próxima meia hora
        now = QDateTime.currentDateTime()
        minutes = now.time().minute()
        if minutes < 30:
            now = now.addSecs((30 - minutes) * 60)
        else:
            now = now.addSecs((60 - minutes) * 60)
            
        # Definir data/hora padrão (dentro do período do evento)
        if self.event:
            event_start = QDateTime(self.event.start_date)
            event_end = QDateTime(self.event.end_date)
            
            # Se "agora" estiver dentro do período do evento, usar como início
            if event_start <= now <= event_end:
                self.start_datetime.setDateTime(now)
            else:
                # Caso contrário, usar início do evento
                self.start_datetime.setDateTime(event_start)
                
            # Definir limite de datas
            self.start_datetime.setMinimumDateTime(event_start)
            self.start_datetime.setMaximumDateTime(event_end)
            self.end_datetime.setMinimumDateTime(event_start)
            self.end_datetime.setMaximumDateTime(event_end)
        else:
            self.start_datetime.setDateTime(now)
            
        # Término padrão 1 hora depois
        self.end_datetime.setDateTime(self.start_datetime.dateTime().addSecs(3600))
        
        # Tipo padrão
        self.type_combo.setCurrentText("other")
        
        # Prioridade média
        self.priority_spin.setValue(3)
        
    def update_end_datetime(self, datetime):
        """Atualizar data/hora final quando a inicial mudar"""
        # Manter duração atual ao mudar início
        if self.end_datetime.dateTime() <= datetime:
            # Se fim for anterior ou igual ao novo início, definir 1h depois
            self.end_datetime.setDateTime(datetime.addSecs(3600))
        elif self.activity is None:
            # Se for nova atividade, manter diferença de 1h
            current_diff = self.start_datetime.dateTime().secsTo(self.end_datetime.dateTime())
            # Se a diferença for muito pequena ou muito grande, ajustar para 1h
            if current_diff < 900 or current_diff > 14400:  # 15min a 4h
                self.end_datetime.setDateTime(datetime.addSecs(3600))
        
    def populate_fields(self):
        """Preencher campos com dados da atividade existente"""
        if not self.activity:
            return
            
        # Informações básicas
        self.name_edit.setText(self.activity.name)
        self.details_edit.setText(self.activity.details or "")
        
        # Encontrar palco no combo
        for i in range(self.stage_combo.count()):
            if self.stage_combo.itemData(i) == self.activity.stage_id:
                self.stage_combo.setCurrentIndex(i)
                break
                
        # Data e hora
        start_datetime = QDateTime(self.activity.start_time)
        self.start_datetime.setDateTime(start_datetime)
        
        end_datetime = QDateTime(self.activity.end_time)
        self.end_datetime.setDateTime(end_datetime)
        
        # Limitar datas ao período do evento
        if self.event:
            event_start = QDateTime(self.event.start_date)
            event_end = QDateTime(self.event.end_date)
            self.start_datetime.setMinimumDateTime(event_start)
            self.start_datetime.setMaximumDateTime(event_end)
            self.end_datetime.setMinimumDateTime(event_start)
            self.end_datetime.setMaximumDateTime(event_end)
        
        # Tipo e prioridade
        if self.activity.type:
            self.type_combo.setCurrentText(self.activity.type)
        else:
            self.type_combo.setCurrentText("other")
            
        self.priority_spin.setValue(self.activity.priority)
        
    def accept(self):
        """Processar o formulário quando o usuário clica em Salvar"""
        # Validar campos obrigatórios
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Campos Obrigatórios", "Por favor, informe o nome da atividade.")
            self.name_edit.setFocus()
            return
            
        if self.stage_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Campos Obrigatórios", "Por favor, selecione um palco/área.")
            self.stage_combo.setFocus()
            return
            
        # Verificar datas
        start_datetime = self.start_datetime.dateTime().toPyDateTime()
        end_datetime = self.end_datetime.dateTime().toPyDateTime()
        
        if end_datetime <= start_datetime:
            QMessageBox.warning(self, "Datas Inválidas", 
                             "A data/hora de término deve ser posterior à data/hora de início.")
            return
            
        try:
            # Obter ID do palco selecionado
            stage_id = self.stage_combo.currentData()
            
            if self.activity:
                # Atualizar atividade existente
                self.activity.name = self.name_edit.text().strip()
                self.activity.stage_id = stage_id
                self.activity.start_time = start_datetime
                self.activity.end_time = end_datetime
                self.activity.type = self.type_combo.currentText()
                self.activity.priority = self.priority_spin.value()
                self.activity.details = self.details_edit.toPlainText()
                
                self.db.commit()
                logger.info(f"Atividade ID {self.activity.id} atualizada: '{self.activity.name}'")
                
            else:
                # Criar nova atividade
                new_activity = Activity(
                    name=self.name_edit.text().strip(),
                    stage_id=stage_id,
                    start_time=start_datetime,
                    end_time=end_datetime,
                    type=self.type_combo.currentText(),
                    priority=self.priority_spin.value(),
                    details=self.details_edit.toPlainText()
                )
                
                self.db.add(new_activity)
                self.db.commit()
                self.activity_id = new_activity.id
                logger.info(f"Nova atividade criada: '{new_activity.name}' (ID: {new_activity.id})")
                
            # Fechar o diálogo
            super().accept()
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao salvar atividade: {str(e)}")
            QMessageBox.critical(self, "Erro de Banco de Dados", 
                               f"Ocorreu um erro ao salvar a atividade:\n\n{str(e)}")