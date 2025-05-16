#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Diálogo para gerenciar atribuições de equipe
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
    QMessageBox, QGroupBox, QCheckBox, QSpinBox,
    QTimeEdit
)
from PyQt5.QtCore import Qt, QDateTime, QDate, QTime, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

from core.database import Activity, TeamMember, TeamAssignment, Event, Stage
from core.database_upgrade import AssignmentStatus

logger = logging.getLogger(__name__)

class TeamAssignmentDialog(QDialog):
    """Diálogo para criar ou editar atribuições de equipe"""
    
    def __init__(self, db_session, event_id, date=None, assignment=None, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.event_id = event_id
        self.assignment = assignment
        self.selected_date = date or QDate.currentDate()
        self.editing_mode = assignment is not None
        
        # Configurar UI
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Configurar interface do usuário"""
        # Configurar janela
        self.setWindowTitle("Atribuição de Equipe" if not self.editing_mode else "Editar Atribuição")
        self.setMinimumWidth(480)
        self.setMinimumHeight(500)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Grupo de informações básicas
        basic_group = QGroupBox("Informações Básicas")
        basic_layout = QFormLayout(basic_group)
        
        # Data de atribuição
        self.date_edit = QDateTimeEdit(QDateTime(self.selected_date, QTime(9, 0)))
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        basic_layout.addRow("Data:", self.date_edit)
        
        # Membro da equipe
        self.member_combo = QComboBox()
        basic_layout.addRow("Membro da equipe:", self.member_combo)
        
        # Atividade
        self.activity_combo = QComboBox()
        basic_layout.addRow("Atividade:", self.activity_combo)
        self.activity_combo.currentIndexChanged.connect(self.on_activity_changed)
        
        # Horário de início
        self.start_time_edit = QTimeEdit(QTime(9, 0))
        self.start_time_edit.setDisplayFormat("HH:mm")
        basic_layout.addRow("Horário de início:", self.start_time_edit)
        
        # Horário de fim
        self.end_time_edit = QTimeEdit(QTime(18, 0))
        self.end_time_edit.setDisplayFormat("HH:mm")
        basic_layout.addRow("Horário de fim:", self.end_time_edit)
        
        # Local
        self.location_edit = QLineEdit()
        basic_layout.addRow("Local específico:", self.location_edit)
        
        # Grupo de detalhes
        detail_group = QGroupBox("Detalhes da Função")
        detail_layout = QFormLayout(detail_group)
        
        # Função detalhada
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "Câmera",
            "Áudio",
            "Iluminação",
            "Direção",
            "Produção",
            "Outro"
        ])
        detail_layout.addRow("Função:", self.role_combo)
        
        # Detalhes da função
        self.role_details_edit = QTextEdit()
        self.role_details_edit.setPlaceholderText("Detalhes específicos sobre a função...")
        self.role_details_edit.setMaximumHeight(80)
        detail_layout.addRow("Detalhes:", self.role_details_edit)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItem("Ativo", "ativo")
        self.status_combo.addItem("Em Pausa", "pausa")
        self.status_combo.addItem("Finalizado", "finalizado")
        detail_layout.addRow("Status:", self.status_combo)
        
        # Equipamento
        self.equipment_edit = QTextEdit()
        self.equipment_edit.setPlaceholderText("Lista de equipamentos necessários...")
        detail_layout.addRow("Equipamentos:", self.equipment_edit)
        
        # Botões
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Adicionar grupos ao layout principal
        main_layout.addWidget(basic_group)
        main_layout.addWidget(detail_group)
        main_layout.addWidget(button_box)
    
    def load_data(self):
        """Carregar dados para os combos e preencher campos se estiver editando"""
        try:
            # Carregar membros da equipe
            members = self.db.query(TeamMember).order_by(TeamMember.name).all()
            for member in members:
                self.member_combo.addItem(f"{member.name} ({member.role})", member.id)
            
            # Carregar atividades do evento
            activities = (
                self.db.query(Activity)
                .join(Stage)
                .filter(Stage.event_id == self.event_id)
                .order_by(Activity.start_time)
                .all()
            )
            
            # Organizar atividades por data
            activity_dict = {}
            for activity in activities:
                date_key = activity.start_time.strftime('%Y-%m-%d')
                if date_key not in activity_dict:
                    activity_dict[date_key] = []
                activity_dict[date_key].append(activity)
            
            # Adicionar atividades ao combo agrupadas por data
            for date_key, date_activities in sorted(activity_dict.items()):
                date_obj = datetime.strptime(date_key, '%Y-%m-%d')
                date_str = date_obj.strftime('%d/%m/%Y')
                
                # Adicionar separador com a data
                self.activity_combo.addItem(f"--- {date_str} ---", None)
                
                # Adicionar atividades dessa data
                for activity in date_activities:
                    start_time = activity.start_time.strftime('%H:%M')
                    end_time = activity.end_time.strftime('%H:%M') if activity.end_time else start_time
                    
                    item_text = f"{activity.name} ({start_time} - {end_time})"
                    self.activity_combo.addItem(item_text, activity.id)
            
            # Se estiver editando, preencher os campos com os dados da atribuição
            if self.editing_mode and self.assignment:
                # Definir membro da equipe
                if self.assignment.member_id:
                    member_index = self.member_combo.findData(self.assignment.member_id)
                    if member_index >= 0:
                        self.member_combo.setCurrentIndex(member_index)
                
                # Definir atividade
                if self.assignment.activity_id:
                    activity_index = self.activity_combo.findData(self.assignment.activity_id)
                    if activity_index >= 0:
                        self.activity_combo.setCurrentIndex(activity_index)
                
                # Definir horários
                if self.assignment.start_time:
                    qdate = QDate(self.assignment.start_time.year, 
                                self.assignment.start_time.month, 
                                self.assignment.start_time.day)
                    qtime = QTime(self.assignment.start_time.hour, 
                                self.assignment.start_time.minute)
                    self.date_edit.setDate(qdate)
                    self.start_time_edit.setTime(qtime)
                
                if self.assignment.end_time:
                    qtime = QTime(self.assignment.end_time.hour, 
                                self.assignment.end_time.minute)
                    self.end_time_edit.setTime(qtime)
                
                # Definir localização
                if self.assignment.location:
                    self.location_edit.setText(self.assignment.location)
                
                # Definir status
                if self.assignment.status:
                    status_index = self.status_combo.findData(self.assignment.status)
                    if status_index >= 0:
                        self.status_combo.setCurrentIndex(status_index)
                
                # Definir equipamento
                if self.assignment.equipment:
                    self.equipment_edit.setText(self.assignment.equipment)
                
                # Definir função
                if self.assignment.role_details:
                    # Tentar encontrar a função principal no combo
                    role_found = False
                    for i in range(self.role_combo.count()):
                        role = self.role_combo.itemText(i)
                        if role.lower() in self.assignment.role_details.lower():
                            self.role_combo.setCurrentIndex(i)
                            role_found = True
                            break
                    
                    # Se não encontrou, selecionar "Outro"
                    if not role_found:
                        self.role_combo.setCurrentText("Outro")
                    
                    # Definir detalhes da função
                    self.role_details_edit.setText(self.assignment.role_details)
        
        except Exception as e:
            logger.error(f"Erro ao carregar dados para o diálogo: {str(e)}")
            QMessageBox.warning(self, "Erro", f"Não foi possível carregar os dados: {str(e)}")
    
    def on_activity_changed(self, index):
        """Chamado quando uma atividade é selecionada"""
        try:
            activity_id = self.activity_combo.currentData()
            if not activity_id:
                return
            
            activity = self.db.query(Activity).get(activity_id)
            if not activity:
                return
            
            # Atualizar data e horários com base na atividade
            qdate = QDate(activity.start_time.year, 
                        activity.start_time.month, 
                        activity.start_time.day)
            
            self.date_edit.setDate(qdate)
            
            start_time = QTime(activity.start_time.hour, activity.start_time.minute)
            self.start_time_edit.setTime(start_time)
            
            if activity.end_time:
                end_time = QTime(activity.end_time.hour, activity.end_time.minute)
                self.end_time_edit.setTime(end_time)
            
            # Atualizar local se a atividade tiver um palco com localização definida
            if activity.stage and activity.stage.location:
                self.location_edit.setText(activity.stage.location)
        
        except Exception as e:
            logger.error(f"Erro ao atualizar dados da atividade: {str(e)}")
    
    def accept(self):
        """Salvar a atribuição de equipe"""
        try:
            # Validar campos obrigatórios
            member_id = self.member_combo.currentData()
            activity_id = self.activity_combo.currentData()
            
            if not member_id:
                QMessageBox.warning(self, "Erro", "Selecione um membro da equipe.")
                return
            
            if not activity_id:
                QMessageBox.warning(self, "Erro", "Selecione uma atividade válida.")
                return
            
            # Obter os valores dos campos
            selected_date = self.date_edit.date().toPyDate()
            start_time = self.start_time_edit.time().toPyTime()
            end_time = self.end_time_edit.time().toPyTime()
            
            start_datetime = datetime.combine(selected_date, start_time)
            end_datetime = datetime.combine(selected_date, end_time)
            
            location = self.location_edit.text().strip()
            role_details = self.role_details_edit.toPlainText().strip()
            equipment = self.equipment_edit.toPlainText().strip()
            status = self.status_combo.currentData()
            
            # Se o campo de detalhes da função estiver vazio, usar o valor do combo
            if not role_details:
                role_details = self.role_combo.currentText()
            elif not role_details.startswith(self.role_combo.currentText()):
                # Se não começar com a função do combo, adicionar como prefixo
                role_details = f"{self.role_combo.currentText()}: {role_details}"
            
            # Criar nova atribuição ou atualizar existente
            if not self.editing_mode:
                assignment = TeamAssignment(
                    member_id=member_id,
                    activity_id=activity_id,
                    start_time=start_datetime,
                    end_time=end_datetime,
                    location=location,
                    role_details=role_details,
                    equipment=equipment,
                    status=status
                )
                self.db.add(assignment)
                
            else:
                # Atualizar atribuição existente
                self.assignment.member_id = member_id
                self.assignment.activity_id = activity_id
                self.assignment.start_time = start_datetime
                self.assignment.end_time = end_datetime
                self.assignment.location = location
                self.assignment.role_details = role_details
                self.assignment.equipment = equipment
                self.assignment.status = status
            
            # Salvar no banco de dados
            self.db.commit()
            
            # Fechar o diálogo
            super().accept()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao salvar atribuição de equipe: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar a atribuição: {str(e)}")
