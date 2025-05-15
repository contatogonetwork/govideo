#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Interface de gerenciamento de equipe
Data: 2025-05-15
"""

import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QTableView, QTreeView, 
    QHeaderView, QAbstractItemView, QMenu, QAction,
    QMessageBox, QDialog, QGroupBox, QFormLayout,
    QLineEdit, QComboBox, QTextEdit, QDoubleSpinBox,
    QTabWidget, QCalendarWidget, QListWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QSortFilterProxyModel, QDate, QModelIndex
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem

from modules.team.team_manager import TeamManager
from core.database import TeamMember, TeamAssignment, Activity, Stage

logger = logging.getLogger(__name__)

class TeamMemberDialog(QDialog):
    """Diálogo para criar ou editar membro da equipe"""
    
    def __init__(self, db_session, member=None, parent=None):
        """Inicializar diálogo
        
        Args:
            db_session: Sessão de banco de dados
            member (TeamMember, opcional): Membro a editar
            parent (QWidget, opcional): Widget pai
        """
        super().__init__(parent)
        self.db = db_session
        self.member = member
        
        if member:
            self.setWindowTitle("Editar Membro da Equipe")
        else:
            self.setWindowTitle("Novo Membro da Equipe")
            
        self.setup_ui()
        self.populate_roles()
        
        if member:
            self.populate_fields()
            
        # Configurações do diálogo
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
    def setup_ui(self):
        """Configurar a interface do usuário"""
        layout = QVBoxLayout(self)
        
        # Formulário de dados básicos
        form_group = QGroupBox("Informações Básicas")
        form_layout = QFormLayout(form_group)
        
        # Nome completo
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nome completo")
        form_layout.addRow("Nome:", self.name_edit)
        
        # Função
        self.role_combo = QComboBox()
        form_layout.addRow("Função:", self.role_combo)
        
        # Habilidades
        self.skills_edit = QTextEdit()
        self.skills_edit.setPlaceholderText("Habilidades específicas e experiência")
        self.skills_edit.setMaximumHeight(80)
        form_layout.addRow("Habilidades:", self.skills_edit)
        
        # Contato
        self.contact_edit = QLineEdit()
        self.contact_edit.setPlaceholderText("Telefone, email, etc.")
        form_layout.addRow("Contato:", self.contact_edit)
        
        # Equipamento
        self.equipment_edit = QTextEdit()
        self.equipment_edit.setPlaceholderText("Equipamentos próprios")
        self.equipment_edit.setMaximumHeight(80)
        form_layout.addRow("Equipamento:", self.equipment_edit)
        
        # Valor hora
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(0, 10000)
        self.rate_spin.setDecimals(2)
        self.rate_spin.setValue(0)
        self.rate_spin.setPrefix("R$ ")
        form_layout.addRow("Valor hora:", self.rate_spin)
        
        layout.addWidget(form_group)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Salvar")
        self.save_btn.setIcon(QIcon("resources/icons/save.png"))
        self.save_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setIcon(QIcon("resources/icons/cancel.png"))
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def populate_roles(self):
        """Preencher combobox de funções"""
        standard_roles = [
            "Diretor", "Produtor", "Câmera", 
            "Editor", "Áudio", "Iluminação",
            "Apresentador", "Maquiagem", "Assistente"
        ]
        
        # Adicionar funções padrão
        self.role_combo.addItems(standard_roles)
        
        # Permitir edição para funções personalizadas
        self.role_combo.setEditable(True)
        
    def populate_fields(self):
        """Preencher campos com dados do membro existente"""
        if not self.member:
            return
            
        self.name_edit.setText(self.member.name)
        
        # Encontrar ou adicionar função
        role_index = self.role_combo.findText(self.member.role)
        if role_index >= 0:
            self.role_combo.setCurrentIndex(role_index)
        else:
            self.role_combo.addItem(self.member.role)
            self.role_combo.setCurrentText(self.member.role)
            
        self.skills_edit.setText(self.member.skills or "")
        self.contact_edit.setText(self.member.contact_info or "")
        self.equipment_edit.setText(self.member.equipment or "")
        
        if self.member.hourly_rate:
            self.rate_spin.setValue(self.member.hourly_rate)
            
    def accept(self):
        """Processar ao aceitar o diálogo"""
        # Validação básica
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Campos obrigatórios", "O nome é obrigatório.")
            self.name_edit.setFocus()
            return
            
        if not self.role_combo.currentText().strip():
            QMessageBox.warning(self, "Campos obrigatórios", "A função é obrigatória.")
            self.role_combo.setFocus()
            return
            
        # Processar dados
        try:
            team_manager = TeamManager(self.db)
            
            if self.member:
                # Atualizar membro existente
                team_manager.update_team_member(
                    self.member.id,
                    name=self.name_edit.text().strip(),
                    role=self.role_combo.currentText().strip(),
                    skills=self.skills_edit.toPlainText(),
                    contact_info=self.contact_edit.text(),
                    equipment=self.equipment_edit.toPlainText(),
                    hourly_rate=self.rate_spin.value() if self.rate_spin.value() > 0 else None
                )
            else:
                # Criar novo membro
                team_manager.add_team_member(
                    name=self.name_edit.text().strip(),
                    role=self.role_combo.currentText().strip(),
                    skills=self.skills_edit.toPlainText(),
                    contact_info=self.contact_edit.text(),
                    equipment=self.equipment_edit.toPlainText(),
                    hourly_rate=self.rate_spin.value() if self.rate_spin.value() > 0 else None
                )
                
            # Fechar o diálogo
            super().accept()
            
        except Exception as e:
            logger.error(f"Erro ao salvar membro da equipe: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao salvar o membro:\n\n{str(e)}")

class TeamView(QWidget):
    """Widget de visualização e gerenciamento de equipe"""
    
    def __init__(self, db_session, parent=None):
        """Inicializar view
        
        Args:
            db_session: Sessão de banco de dados
            parent (QWidget, opcional): Widget pai
        """
        super().__init__(parent)
        self.db = db_session
        self.current_event = None
        self.selected_date = None
        self.team_manager = TeamManager(db_session)
        self.setup_ui()
        
        # Carregar dados iniciais
        self.load_team_members()
        
    def set_current_event(self, event):
        """Define o evento atual e atualiza a interface
        
        Args:
            event: Objeto evento selecionado
        """
        self.current_event = event
        self.refresh()
        
    def setup_ui(self):
        """Configurar interface do usuário"""
        main_layout = QVBoxLayout(self)
        
        # Barra de ferramentas
        toolbar_layout = QHBoxLayout()
        
        self.add_member_btn = QPushButton(self.load_icon("add.png"), "Adicionar Membro")
        self.add_member_btn.clicked.connect(self.on_add_member)
        
        self.edit_member_btn = QPushButton(self.load_icon("edit.png"), "Editar")
        self.edit_member_btn.clicked.connect(self.on_edit_member)
        self.edit_member_btn.setEnabled(False)
        
        self.remove_member_btn = QPushButton(self.load_icon("delete.png"), "Remover")
        self.remove_member_btn.clicked.connect(self.on_remove_member)
        self.remove_member_btn.setEnabled(False)
        
        self.refresh_btn = QPushButton(self.load_icon("refresh.png"), "Atualizar")
        self.refresh_btn.clicked.connect(self.refresh)
        
        toolbar_layout.addWidget(self.add_member_btn)
        toolbar_layout.addWidget(self.edit_member_btn)
        toolbar_layout.addWidget(self.remove_member_btn)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        # Divisor principal
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Lista de membros da equipe
        self.team_list_model = QStandardItemModel()
        self.team_list_model.setHorizontalHeaderLabels(["Nome", "Função"])
        
        self.team_proxy_model = QSortFilterProxyModel()
        self.team_proxy_model.setSourceModel(self.team_list_model)
        self.team_proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        
        self.team_view = QTableView()
        self.team_view.setModel(self.team_proxy_model)
        self.team_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.team_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.team_view.setSortingEnabled(True)
        self.team_view.setAlternatingRowColors(True)
        self.team_view.verticalHeader().setVisible(False)
        self.team_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Conectar seleção de membro
        self.team_view.selectionModel().selectionChanged.connect(self.on_member_selection_changed)
        self.team_view.doubleClicked.connect(self.on_edit_member)
        
        # Detalhes do membro / Configuração de evento
        self.details_tabs = QTabWidget()
        
        # Aba de detalhes do membro
        self.details_tab = QWidget()
        details_layout = QVBoxLayout(self.details_tab)
        
        # Grupo de informações do membro
        self.member_info_group = QGroupBox("Detalhes do Membro")
        self.member_info_layout = QFormLayout(self.member_info_group)
        
        self.member_name_label = QLabel("-")
        self.member_role_label = QLabel("-")
        self.member_contact_label = QLabel("-")
        self.member_skills_text = QTextEdit()
        self.member_skills_text.setReadOnly(True)
        self.member_skills_text.setMaximumHeight(60)
        self.member_equipment_text = QTextEdit()
        self.member_equipment_text.setReadOnly(True)
        self.member_equipment_text.setMaximumHeight(60)
        self.member_rate_label = QLabel("-")
        
        self.member_info_layout.addRow("Nome:", self.member_name_label)
        self.member_info_layout.addRow("Função:", self.member_role_label)
        self.member_info_layout.addRow("Contato:", self.member_contact_label)
        self.member_info_layout.addRow("Habilidades:", self.member_skills_text)
        self.member_info_layout.addRow("Equipamento:", self.member_equipment_text)
        self.member_info_layout.addRow("Valor hora:", self.member_rate_label)
        
        details_layout.addWidget(self.member_info_group)
        
        # Lista de atribuições do membro
        self.assignments_group = QGroupBox("Atribuições no Evento Atual")
        assignments_layout = QVBoxLayout(self.assignments_group)
        
        self.assignments_list = QListWidget()
        assignments_layout.addWidget(self.assignments_list)
        
        details_layout.addWidget(self.assignments_group)
        
        # Aba de agenda do evento
        self.schedule_tab = QWidget()
        schedule_layout = QVBoxLayout(self.schedule_tab)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.on_date_selected)
        
        self.schedule_list = QListWidget()
        
        schedule_layout.addWidget(self.calendar)
        schedule_layout.addWidget(QLabel("Atividades na data:"))
        schedule_layout.addWidget(self.schedule_list)
        
        # Adicionar abas ao widget de abas
        self.details_tabs.addTab(self.details_tab, "Detalhes")
        self.details_tabs.addTab(self.schedule_tab, "Agenda")
        
        # Adicionar widgets ao splitter
        self.main_splitter.addWidget(self.team_view)
        self.main_splitter.addWidget(self.details_tabs)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(self.main_splitter)
        
        # Barra de filtro
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar:"))
        
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Digite para filtrar membros...")
        self.filter_edit.textChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.filter_edit)
        
        # Filtro por função
        self.role_filter = QComboBox()
        self.role_filter.addItem("Todas funções")
        self.role_filter.currentIndexChanged.connect(self.on_role_filter_changed)
        filter_layout.addWidget(self.role_filter)
        
        main_layout.addLayout(filter_layout)
        
    def load_icon(self, icon_name):
        """Carregar ícone da pasta resources
        
        Args:
            icon_name (str): Nome do arquivo de ícone
            
        Returns:
            QIcon: Objeto de ícone
        """
        return QIcon(f"resources/icons/{icon_name}")
        
    def load_team_members(self):
        """Carregar membros da equipe do banco"""
        try:
            # Limpar modelo atual
            self.team_list_model.removeRows(0, self.team_list_model.rowCount())
            
            # Obter membros e funções únicas
            members = self.team_manager.get_all_members()
            roles = set()
            
            for member in members:
                # Adicionar à lista
                name_item = QStandardItem(member.name)
                role_item = QStandardItem(member.role)
                
                # Armazenar o ID do membro como dado do item
                name_item.setData(member.id, Qt.UserRole)
                
                self.team_list_model.appendRow([name_item, role_item])
                
                # Adicionar função ao conjunto
                roles.add(member.role)
            
            # Atualizar filtro de funções
            self.update_role_filter(roles)
            
        except Exception as e:
            logger.error(f"Erro ao carregar membros da equipe: {str(e)}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar membros da equipe:\n\n{str(e)}")
            
    def update_role_filter(self, roles):
        """Atualizar filtro de funções
        
        Args:
            roles (set): Conjunto de funções únicas
        """
        # Preservar seleção atual
        current_text = self.role_filter.currentText()
        
        # Limpar e recriar
        self.role_filter.clear()
        self.role_filter.addItem("Todas funções")
        
        # Adicionar funções ordenadas
        for role in sorted(roles):
            self.role_filter.addItem(role)
            
        # Restaurar seleção
        index = self.role_filter.findText(current_text)
        if index >= 0:
            self.role_filter.setCurrentIndex(index)
            
    def on_member_selection_changed(self, selected, deselected):
        """Manipulador para mudança na seleção de membros"""
        # Habilitar/desabilitar botões baseado na seleção
        has_selection = len(selected.indexes()) > 0
        self.edit_member_btn.setEnabled(has_selection)
        self.remove_member_btn.setEnabled(has_selection)
        
        if has_selection:
            # Obter o membro selecionado
            proxy_index = selected.indexes()[0]
            source_index = self.team_proxy_model.mapToSource(proxy_index)
            member_id = self.team_list_model.data(source_index, Qt.UserRole)
            
            # Carregar detalhes do membro
            self.load_member_details(member_id)
        else:
            # Limpar detalhes
            self.clear_member_details()
            
    def load_member_details(self, member_id):
        """Carregar detalhes do membro selecionado
        
        Args:
            member_id (int): ID do membro
        """
        try:
            # Buscar membro no banco
            member = self.team_manager.get_member(member_id)
            
            if not member:
                self.clear_member_details()
                return
                
            # Preencher informações básicas
            self.member_name_label.setText(member.name)
            self.member_role_label.setText(member.role)
            self.member_contact_label.setText(member.contact_info or "-")
            self.member_skills_text.setText(member.skills or "")
            self.member_equipment_text.setText(member.equipment or "")
            
            if member.hourly_rate:
                self.member_rate_label.setText(f"R$ {member.hourly_rate:.2f}")
            else:
                self.member_rate_label.setText("-")
                
            # Carregar atribuições do membro no evento atual
            self.load_member_assignments(member_id)
            
        except Exception as e:
            logger.error(f"Erro ao carregar detalhes do membro: {str(e)}")
            
    def load_member_assignments(self, member_id):
        """Carregar atribuições do membro no evento atual
        
        Args:
            member_id (int): ID do membro
        """
        # Limpar lista
        self.assignments_list.clear()
        
        if not self.current_event:
            self.assignments_group.setTitle("Atribuições (Nenhum evento selecionado)")
            return
            
        self.assignments_group.setTitle(f"Atribuições em: {self.current_event.name}")
        
        try:
            # Buscar atribuições do membro no evento atual
            assignments = self.team_manager.get_schedule(
                event_id=self.current_event.id,
                member_id=member_id
            )
            
            if not assignments:
                self.assignments_list.addItem("Nenhuma atribuição neste evento")
                return
                
            # Adicionar cada atribuição à lista
            for assignment in assignments:
                activity = assignment.activity
                stage = activity.stage
                
                # Formatar data e hora
                start_time = activity.start_time.strftime("%d/%m/%Y %H:%M")
                end_time = activity.end_time.strftime("%H:%M")
                
                # Criar item com informações detalhadas
                item_text = f"{activity.name}\n{start_time} - {end_time}\nLocal: {stage.name}"
                if assignment.role_details:
                    item_text += f"\nFunção: {assignment.role_details}"
                    
                self.assignments_list.addItem(item_text)
                
        except Exception as e:
            logger.error(f"Erro ao carregar atribuições: {str(e)}")
            self.assignments_list.addItem(f"Erro: {str(e)}")
            
    def clear_member_details(self):
        """Limpar detalhes do membro"""
        self.member_name_label.setText("-")
        self.member_role_label.setText("-")
        self.member_contact_label.setText("-")
        self.member_skills_text.clear()
        self.member_equipment_text.clear()
        self.member_rate_label.setText("-")
        
        # Limpar atribuições
        self.assignments_list.clear()
        self.assignments_group.setTitle("Atribuições")
        
    def on_filter_changed(self, text):
        """Manipulador para mudança no texto do filtro"""
        self.team_proxy_model.setFilterFixedString(text)
        
    def on_role_filter_changed(self, index):
        """Manipulador para mudança no filtro de função"""
        if index <= 0:  # "Todas funções"
            # Filtrar apenas pelo texto
            self.team_proxy_model.setFilterKeyColumn(-1)
        else:
            # Filtrar pela função
            role = self.role_filter.currentText()
            self.team_proxy_model.setFilterKeyColumn(1)  # Coluna da função
            self.team_proxy_model.setFilterFixedString(role)
            
    def on_add_member(self):
        """Manipulador para adicionar novo membro"""
        dialog = TeamMemberDialog(self.db)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            self.refresh()
            
    def on_edit_member(self):
        """Manipulador para editar membro selecionado"""
        selected_indexes = self.team_view.selectionModel().selectedRows()
        if not selected_indexes:
            return
            
        proxy_index = selected_indexes[0]
        source_index = self.team_proxy_model.mapToSource(proxy_index)
        member_id = self.team_list_model.data(source_index, Qt.UserRole)
        
        # Buscar membro no banco
        member = self.team_manager.get_member(member_id)
        
        if member:
            dialog = TeamMemberDialog(self.db, member)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                self.refresh()
                # Re-selecionar o mesmo membro
                self.select_member(member_id)
                
    def on_remove_member(self):
        """Manipulador para remover membro selecionado"""
        selected_indexes = self.team_view.selectionModel().selectedRows()
        if not selected_indexes:
            return
            
        proxy_index = selected_indexes[0]
        source_index = self.team_proxy_model.mapToSource(proxy_index)
        member_id = self.team_list_model.data(source_index, Qt.UserRole)
        member_name = self.team_list_model.data(source_index)
        
        # Confirmar exclusão
        reply = QMessageBox.question(
            self, 
            "Confirmar Exclusão", 
            f"Tem certeza que deseja excluir o membro '{member_name}'?\n\n"
            f"Esta ação excluirá também todas as atribuições deste membro.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Remover membro
                self.team_manager.delete_team_member(member_id)
                
                # Atualizar UI
                self.refresh()
                
            except Exception as e:
                logger.error(f"Erro ao excluir membro: {str(e)}")
                QMessageBox.critical(self, "Erro", f"Erro ao excluir membro:\n\n{str(e)}")
                
    def select_member(self, member_id):
        """Selecionar membro na tabela pelo ID
        
        Args:
            member_id (int): ID do membro
        """
        # Percorrer o modelo para encontrar o membro
        for row in range(self.team_list_model.rowCount()):
            index = self.team_list_model.index(row, 0)
            if self.team_list_model.data(index, Qt.UserRole) == member_id:
                # Mapear para índice do modelo proxy
                proxy_index = self.team_proxy_model.mapFromSource(index)
                # Selecionar na view
                self.team_view.selectRow(proxy_index.row())
                break
                
    def set_current_event(self, event):
        """Definir evento atual
        
        Args:
            event: Objeto do evento
        """
        self.current_event = event
        
        # Atualizar interface se houver membro selecionado
        selected_indexes = self.team_view.selectionModel().selectedRows()
        if selected_indexes:
            proxy_index = selected_indexes[0]
            source_index = self.team_proxy_model.mapToSource(proxy_index)
            member_id = self.team_list_model.data(source_index, Qt.UserRole)
            self.load_member_assignments(member_id)
            
        # Atualizar calendário para o período do evento
        if event:
            min_date = QDate(event.start_date.year, event.start_date.month, event.start_date.day)
            max_date = QDate(event.end_date.year, event.end_date.month, event.end_date.day)
            
            self.calendar.setMinimumDate(min_date)
            self.calendar.setMaximumDate(max_date)
            self.calendar.setSelectedDate(min_date)
            
            # Carregar agenda para a data inicial
            self.selected_date = event.start_date
            self.load_schedule_for_date(event.start_date)
        else:
            # Limpar restrições de data
            self.calendar.setMinimumDate(QDate(2000, 1, 1))
            self.calendar.setMaximumDate(QDate(2999, 12, 31))
            self.calendar.setSelectedDate(QDate.currentDate())
            self.schedule_list.clear()
            
    def set_selected_date(self, date):
        """Definir data selecionada
        
        Args:
            date: Data selecionada (QDate ou datetime.date)
        """
        if isinstance(date, QDate):
            py_date = date.toPyDate()
        else:
            py_date = date
            date = QDate(py_date.year, py_date.month, py_date.day)
            
        self.selected_date = py_date
        self.calendar.setSelectedDate(date)
        self.load_schedule_for_date(py_date)
        
    def on_date_selected(self, date):
        """Manipulador para seleção de data no calendário
        
        Args:
            date (QDate): Data selecionada
        """
        self.set_selected_date(date)
        
    def load_schedule_for_date(self, date):
        """Carregar agenda para uma data específica
        
        Args:
            date: Data para exibir (datetime.date)
        """
        # Limpar lista atual
        self.schedule_list.clear()
        
        if not self.current_event:
            self.schedule_list.addItem("Nenhum evento selecionado")
            return
            
        try:
            # Buscar todas as atribuições para esta data
            schedule = self.team_manager.get_schedule(
                event_id=self.current_event.id,
                date=date
            )
            
            if not schedule:
                self.schedule_list.addItem("Nenhuma atividade agendada para esta data")
                return
                
            # Agrupar por atividade
            activities = {}
            
            for assignment in schedule:
                activity = assignment.activity
                activity_id = activity.id
                
                # Se primeira vez, adicionar a atividade
                if activity_id not in activities:
                    activities[activity_id] = {
                        'activity': activity,
                        'members': []
                    }
                    
                # Adicionar membro à atividade
                activities[activity_id]['members'].append(assignment.member)
                
            # Adicionar atividades à lista, ordenadas por hora
            sorted_activities = sorted(
                activities.values(), 
                key=lambda x: x['activity'].start_time
            )
            
            for item in sorted_activities:
                activity = item['activity']
                members = item['members']
                
                # Formatar horário
                start_time = activity.start_time.strftime("%H:%M")
                end_time = activity.end_time.strftime("%H:%M")
                
                # Formatar texto do item
                item_text = f"{start_time}-{end_time}: {activity.name}\n"
                item_text += f"Local: {activity.stage.name}\n"
                item_text += f"Equipe: {', '.join(m.name for m in members)}"
                
                self.schedule_list.addItem(item_text)
                
        except Exception as e:
            logger.error(f"Erro ao carregar agenda: {str(e)}")
            self.schedule_list.addItem(f"Erro: {str(e)}")
            
    def refresh(self):
        """Atualizar todos os dados"""
        self.load_team_members()
        
        # Recarregar agenda se tiver data selecionada
        if self.selected_date:
            self.load_schedule_for_date(self.selected_date)