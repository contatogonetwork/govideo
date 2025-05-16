# filepath: c:\govideo\ui\views\team_schedule_view.py
import os
import logging
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTableView,
    QCalendarWidget,
    QLabel,
    QPushButton,
    QComboBox,
    QToolBar,
    QAction,
    QHeaderView,
    QSplitter,
    QGroupBox,
    QFormLayout,
    QMenu,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QDate
from PyQt5.QtGui import QIcon

from ui.models.team_schedule_model import TeamScheduleModel
from core.database import TeamMember, TeamAssignment, Activity, Event, Stage, Activation
from core.database_upgrade import AssignmentStatus, ActivationStatus
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class TeamScheduleView(QWidget):
    """Visualização da escala da equipe em formato de calendário"""

    assignment_updated = pyqtSignal(int)

    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.current_event = None
        self.selected_date = QDate.currentDate()
        self.filtered_member = None
        self.filtered_role = None

        self.setup_ui()
        
    def setup_ui(self):
        # Layout principal
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Barra de ferramentas
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        
        # Ações da barra de ferramentas
        self.action_add = QAction(QIcon("resources/icons/add.png"), "Nova Atribuição", self)
        self.action_add.triggered.connect(self.on_add_assignment)
        toolbar.addAction(self.action_add)
        
        self.action_edit = QAction(QIcon("resources/icons/edit.png"), "Editar Atribuição", self)
        self.action_edit.triggered.connect(self.on_edit_assignment)
        toolbar.addAction(self.action_edit)
        
        self.action_delete = QAction(QIcon("resources/icons/delete.png"), "Remover Atribuição", self)
        self.action_delete.triggered.connect(self.on_delete_assignment)
        toolbar.addAction(self.action_delete)
        
        toolbar.addSeparator()
        
        # Navegação de data
        self.action_prev_day = QAction(QIcon("resources/icons/previous.png"), "Dia Anterior", self)
        self.action_prev_day.triggered.connect(self.go_to_previous_day)
        toolbar.addAction(self.action_prev_day)
        
        self.action_today = QAction(QIcon("resources/icons/today.png"), "Hoje", self)
        self.action_today.triggered.connect(self.go_to_today)
        toolbar.addAction(self.action_today)
        
        self.action_next_day = QAction(QIcon("resources/icons/next.png"), "Próximo Dia", self)
        self.action_next_day.triggered.connect(self.go_to_next_day)
        toolbar.addAction(self.action_next_day)
        
        main_layout.addWidget(toolbar)
        
        # Informações do evento
        event_box = QGroupBox("Informações do Evento")
        event_form = QFormLayout()
        event_box.setLayout(event_form)
        
        self.event_name_label = QLabel("-")
        self.event_date_label = QLabel("-")
        self.event_location_label = QLabel("-")
        
        event_form.addRow("Nome:", self.event_name_label)
        event_form.addRow("Data:", self.event_date_label)
        event_form.addRow("Local:", self.event_location_label)
        
        main_layout.addWidget(event_box)
        
        # Área principal com calendário e tabela
        splitter = QSplitter(Qt.Horizontal)
        
        # Calendário
        calendar_container = QWidget()
        calendar_layout = QVBoxLayout()
        calendar_container.setLayout(calendar_layout)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.on_date_selected)
        calendar_layout.addWidget(self.calendar)
        
        self.date_label = QLabel()
        calendar_layout.addWidget(self.date_label)
        
        calendar_layout.addStretch()
        
        # Filtros
        filter_box = QGroupBox("Filtros")
        filter_layout = QFormLayout()
        filter_box.setLayout(filter_layout)
        
        self.member_filter = QComboBox()
        self.member_filter.addItem("Todos os Membros", None)
        # Aqui você pode adicionar os membros da equipe da base de dados
        
        self.role_filter = QComboBox()
        self.role_filter.addItem("Todas as Funções", None)
        # Aqui você pode adicionar as funções/papéis da base de dados
        
        filter_apply = QPushButton("Aplicar Filtros")
        filter_apply.clicked.connect(self.apply_filters)
        
        filter_layout.addRow("Membro:", self.member_filter)
        filter_layout.addRow("Função:", self.role_filter)
        filter_layout.addRow("", filter_apply)
        
        calendar_layout.addWidget(filter_box)
        
        splitter.addWidget(calendar_container)
        
        # Tabela de escalas
        table_container = QWidget()
        table_layout = QVBoxLayout()
        table_container.setLayout(table_layout)
        
        self.schedule_table = QTableView()
        self.schedule_table.setSelectionBehavior(QTableView.SelectRows)
        self.schedule_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.schedule_table.customContextMenuRequested.connect(self.show_context_menu)
        self.schedule_table.doubleClicked.connect(self.on_cell_double_clicked)
        
        # Configurar o modelo de dados (será atualizado em refresh_data)
        self.schedule_model = TeamScheduleModel(self.db)
        self.schedule_table.setModel(self.schedule_model)
        
        # Ajustar tamanho das colunas
        header = self.schedule_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        table_layout.addWidget(self.schedule_table)
        
        splitter.addWidget(table_container)
        splitter.setStretchFactor(1, 2)  # Tabela ocupa mais espaço
        
        main_layout.addWidget(splitter)
        
        # Inicializar a data exibida
        self.update_date_display()

    def on_add_assignment(self):
        print("Ação de adicionar atribuição disparada.")

    def on_edit_assignment(self):
        print("Ação de editar atribuição disparada.")

    def on_delete_assignment(self):
        print("Ação de remover atribuição disparada.")

    def on_cell_double_clicked(self, index):
        self.on_edit_assignment()

    def show_context_menu(self, position):
        menu = QMenu(self)
        add_action = menu.addAction(QIcon("resources/icons/add.png"), "Nova Atribuição")
        edit_action = menu.addAction(
            QIcon("resources/icons/edit.png"), "Editar Atribuição"
        )
        delete_action = menu.addAction(
            QIcon("resources/icons/delete.png"), "Remover Atribuição"
        )

        index = self.schedule_table.indexAt(position)
        has_selection = index.isValid()

        edit_action.setEnabled(has_selection)
        delete_action.setEnabled(has_selection)

        action = menu.exec_(self.schedule_table.viewport().mapToGlobal(position))

        if action == add_action:
            self.on_add_assignment()
        elif action == edit_action and has_selection:
            self.on_edit_assignment()
        elif action == delete_action and has_selection:
            self.on_delete_assignment()

    def go_to_today(self):
        self.selected_date = QDate.currentDate()
        self.calendar.setSelectedDate(self.selected_date)
        self.update_date_display()

    def go_to_previous_day(self):
        self.selected_date = self.selected_date.addDays(-1)
        self.calendar.setSelectedDate(self.selected_date)
        self.update_date_display()

    def go_to_next_day(self):
        self.selected_date = self.selected_date.addDays(1)
        self.calendar.setSelectedDate(self.selected_date)
        self.update_date_display()

    def on_date_selected(self, date):
        self.selected_date = date
        self.update_date_display()

    def update_date_display(self):
        day_names = [
            "Segunda-feira",
            "Terça-feira",
            "Quarta-feira",
            "Quinta-feira",
            "Sexta-feira",
            "Sábado",
            "Domingo",
        ]
        month_names = [
            "Janeiro",
            "Fevereiro",
            "Março",
            "Abril",
            "Maio",
            "Junho",
            "Julho",
            "Agosto",
            "Setembro",
            "Outubro",
            "Novembro",
            "Dezembro",
        ]

        day = self.selected_date.day()
        month = self.selected_date.month()
        year = self.selected_date.year()
        day_of_week = self.selected_date.dayOfWeek() - 1
        if day_of_week < 0:
            day_of_week = 6

        formatted_date = (
            f"{day} de {month_names[month-1]} de {year} - {day_names[day_of_week]}"
        )
        self.date_label.setText(formatted_date)

    def apply_filters(self):
        self.filtered_member = self.member_filter.currentData()
        self.filtered_role = self.role_filter.currentData()

    def refresh_data(self):
        pass

    def set_event(self, event_id):
        """Define o evento atual e atualiza a interface"""
        if not isinstance(event_id, int) and hasattr(event_id, "id"):
            event_id = event_id.id

        try:
            event = self.db.query(Event).get(event_id)
            if event:
                self.current_event = event
                self.event_name_label.setText(event.name)
                self.event_date_label.setText(
                    f"{event.start_date.strftime('%d/%m/%Y')} - {event.end_date.strftime('%d/%m/%Y')}"
                )
                self.event_location_label.setText(event.location or "-")
                self.selected_date = QDate(
                    event.start_date.year, event.start_date.month, event.start_date.day
                )
                self.calendar.setSelectedDate(self.selected_date)
                self.update_date_display()
                self.refresh_data()
        except Exception as e:
            logger.error(f"Erro ao definir evento: {e}")
