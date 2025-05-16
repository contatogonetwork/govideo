#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Janela principal da aplicação
Data: 2025-05-15
Autor: GONETWORK AI
"""

import os
import sys
import logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QTabWidget, QMessageBox, QDockWidget,
    QAction, QToolBar, QStatusBar, QMenu, QSplashScreen, QFileDialog,
    QSizePolicy, QLabel, QProgressBar, QDialog
)
from PyQt5.QtGui import QIcon, QPixmap, QCloseEvent, QFontDatabase, QColor
from PyQt5.QtCore import Qt, QSettings, QSize, QTimer, QFileInfo

# Importação dos módulos necessários
from core.database import init_database, Base, create_session
from core.config import DEFAULT_DB_PATH, UPLOAD_DIR
from core.pdf_report import EventReportGenerator, PDFReport

# Views da aplicação
from ui.views.event_manager_view import EventManagerView
from ui.views.team_view import TeamView
from ui.views.delivery_view import DeliveryView
from ui.views.dashboard_view import DashboardView
from ui.views.asset_library_view import AssetLibraryView
# # from ui.views.activation_view import ActivationView # Temporariamente comentado
from ui.views.team_schedule_view import TeamScheduleView
from ui.views.delivery_kanban_view import DeliveryKanbanView

# Diálogos
from ui.dialogs.event_browser_dialog import EventBrowserDialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.about_dialog import AboutDialog

# Configurar logger
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Janela principal da aplicação GONETWORK AI"""
    
    def __init__(self, db_session):
        """Inicializar a janela principal
        
        Args:
            db_session: Sessão do banco de dados SQLAlchemy
        """
        super().__init__()
        
        # Configuração básica
        self.db = db_session
        self.current_event = None
        self.settings = QSettings("GONETWORK", "GONETWORK AI")
        
        # Configurar interface
        self.setup_ui()
        
        # Carregar configurações do usuário
        self.load_settings()
        
        # Status inicial
        self.status_bar.showMessage("Pronto", 5000)
        
    def setup_ui(self):
        """Configurar a interface da janela principal"""
        # Configurar janela
        self.setWindowTitle("GONETWORK AI - Gerenciamento de Produção Audiovisual")
        self.setWindowIcon(QIcon("resources/icons/app_icon.png"))
        self.setMinimumSize(1024, 768)
        
        # Widget central com abas
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(True)
        
        # Criar views principais
        self.dashboard_view = DashboardView(self.db, self)
        
        self.event_manager_view = EventManagerView(self.db, self)
        
        self.team_view = TeamView(self.db, self)
        
        self.delivery_view = DeliveryView(self.db, self)
        
        self.asset_library_view = AssetLibraryView(self.db, self)
        
        # Nova view de ativações patrocinadas
        # self.activation_view = None # Temporariamente desabilitado
        
        # Nova view de escala da equipe
        self.team_schedule_view = TeamScheduleView(self.db, self)
        
        # Nova view de Kanban para entregas
        self.delivery_kanban_view = DeliveryKanbanView(self.db, self)
        
        # Conectar sinais
        self.delivery_kanban_view.delivery_double_clicked.connect(self.on_delivery_edit)
        self.team_schedule_view.assignment_updated.connect(self.on_assignment_updated)
        
        # Adicionar abas
        self.tabs.addTab(self.dashboard_view, self.load_icon("dashboard.png"), "Dashboard")
        self.tabs.addTab(self.event_manager_view, self.load_icon("event.png"), "Eventos")
        self.tabs.addTab(self.team_view, self.load_icon("team.png"), "Equipe")
        self.tabs.addTab(self.team_schedule_view, self.load_icon("calendar.png"), "Escala")
        self.tabs.addTab(self.delivery_view, self.load_icon("delivery.png"), "Entregas")
        self.tabs.addTab(self.delivery_kanban_view, self.load_icon("kanban.png"), "Kanban")
        # self.tabs.addTab(self.activation_view, self.load_icon("analyze.png"), "Ativações") # Temporariamente desabilitado
        self.tabs.addTab(self.asset_library_view, self.load_icon("media.png"), "Assets")
        
        self.setCentralWidget(self.tabs)
        
        # Conectar sinais
        self.event_manager_view.event_selected.connect(self.on_event_selected)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Criar barras de ferramentas e menus
        self.create_menus()
        self.create_toolbars()
        self.create_status_bar()
        
    def load_icon(self, icon_name):
        """Carregar um ícone da pasta resources
        
        Args:
            icon_name (str): Nome do arquivo de ícone
            
        Returns:
            QIcon: Objeto de ícone
        """
        icon_path = os.path.join("resources", "icons", icon_name)
        return QIcon(icon_path)
        
    def create_menus(self):
        """Criar menus da janela principal"""
        # Menu Arquivo
        menu_file = self.menuBar().addMenu("Arquivo")
        
        # Ações do menu Arquivo
        action_new_event = QAction(self.load_icon("new_event.png"), "Novo Evento", self)
        action_new_event.setShortcut("Ctrl+N")
        action_new_event.setStatusTip("Criar um novo evento")
        action_new_event.triggered.connect(self.on_new_event)
        
        action_open_event = QAction(self.load_icon("open_event.png"), "Abrir Evento", self)
        action_open_event.setShortcut("Ctrl+O")
        action_open_event.setStatusTip("Abrir um evento existente")
        action_open_event.triggered.connect(self.on_open_event)
        
        action_export = QAction(self.load_icon("export.png"), "Exportar Dados", self)
        action_export.setShortcut("Ctrl+E")
        action_export.setStatusTip("Exportar dados brutos do evento")
        action_export.triggered.connect(self.on_export_raw_data)
        
        action_report = QAction(self.load_icon("document.png"), "Gerar Relatório PDF", self)
        action_report.setShortcut("Ctrl+R")
        action_report.setStatusTip("Gerar relatório PDF do evento")
        action_report.triggered.connect(self.on_export_pdf_report)
        
        action_settings = QAction(self.load_icon("settings.png"), "Configurações", self)
        action_settings.setStatusTip("Alterar configurações da aplicação")
        action_settings.triggered.connect(self.on_settings)
        
        action_exit = QAction(self.load_icon("exit.png"), "Sair", self)
        action_exit.setShortcut("Ctrl+Q")
        action_exit.setStatusTip("Sair da aplicação")
        action_exit.triggered.connect(self.close)
        
        # Adicionar ações ao menu
        menu_file.addAction(action_new_event)
        menu_file.addAction(action_open_event)
        menu_file.addSeparator()
        menu_file.addAction(action_export)
        menu_file.addAction(action_report)
        menu_file.addSeparator()
        menu_file.addAction(action_settings)
        menu_file.addSeparator()
        menu_file.addAction(action_exit)
        
        # Menu Editar
        menu_edit = self.menuBar().addMenu("Editar")
        
        action_undo = QAction(self.load_icon("undo.png"), "Desfazer", self)
        action_undo.setShortcut("Ctrl+Z")
        action_undo.setEnabled(False)
        
        action_redo = QAction(self.load_icon("redo.png"), "Refazer", self)
        action_redo.setShortcut("Ctrl+Y")
        action_redo.setEnabled(False)
        
        menu_edit.addAction(action_undo)
        menu_edit.addAction(action_redo)
        menu_edit.addSeparator()
        
        # Ações de copiar, cortar, colar
        action_cut = QAction(self.load_icon("cut.png"), "Recortar", self)
        action_cut.setShortcut("Ctrl+X")
        action_cut.setEnabled(False)
        
        action_copy = QAction(self.load_icon("copy.png"), "Copiar", self)
        action_copy.setShortcut("Ctrl+C")
        action_copy.setEnabled(False)
        
        action_paste = QAction(self.load_icon("paste.png"), "Colar", self)
        action_paste.setShortcut("Ctrl+V")
        action_paste.setEnabled(False)
        
        menu_edit.addAction(action_cut)
        menu_edit.addAction(action_copy)
        menu_edit.addAction(action_paste)
        
        # Menu Visualizar
        menu_view = self.menuBar().addMenu("Visualizar")
        
        # Alternar entre visualizações
        action_dashboard = QAction(self.load_icon("dashboard.png"), "Dashboard", self)
        action_dashboard.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        
        action_events = QAction(self.load_icon("event.png"), "Eventos", self)
        action_events.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        
        action_team = QAction(self.load_icon("team.png"), "Equipe", self)
        action_team.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        
        action_deliveries = QAction(self.load_icon("delivery.png"), "Entregas", self)
        action_deliveries.triggered.connect(lambda: self.tabs.setCurrentIndex(3))
        
        action_activations = QAction(self.load_icon("analyze.png"), "Ativações", self)
        action_activations.triggered.connect(lambda: self.tabs.setCurrentIndex(4))
        
        action_assets = QAction(self.load_icon("media.png"), "Assets", self)
        action_assets.triggered.connect(lambda: self.tabs.setCurrentIndex(5))
        
        menu_view.addAction(action_dashboard)
        menu_view.addAction(action_events)
        menu_view.addAction(action_team)
        menu_view.addAction(action_deliveries)
        menu_view.addAction(action_activations)
        menu_view.addAction(action_assets)
        
        menu_view.addSeparator()
        
        # Opções de tema
        menu_theme = menu_view.addMenu("Tema")
        
        action_theme_dark = QAction("Tema Escuro", self)
        action_theme_dark.setCheckable(True)
        action_theme_dark.setChecked(True)
        action_theme_dark.triggered.connect(lambda: self.change_theme("dark"))
        
        action_theme_light = QAction("Tema Claro", self)
        action_theme_light.setCheckable(True)
        action_theme_light.triggered.connect(lambda: self.change_theme("light"))
        
        menu_theme.addAction(action_theme_dark)
        menu_theme.addAction(action_theme_light)
        
        # Menu Ferramentas
        menu_tools = self.menuBar().addMenu("Ferramentas")
        
        action_backup = QAction(self.load_icon("backup.png"), "Backup de Dados", self)
        action_backup.setStatusTip("Fazer backup do banco de dados")
        action_backup.triggered.connect(self.on_backup)
        
        action_restore = QAction(self.load_icon("restore.png"), "Restaurar Backup", self)
        action_restore.setStatusTip("Restaurar backup do banco de dados")
        action_restore.triggered.connect(self.on_restore)
        
        action_analyze_video = QAction(self.load_icon("analyze.png"), "Analisar Vídeo", self)
        action_analyze_video.setStatusTip("Analisar vídeo com IA")
        action_analyze_video.triggered.connect(self.on_analyze_video)
        
        menu_tools.addAction(action_backup)
        menu_tools.addAction(action_restore)
        menu_tools.addSeparator()
        menu_tools.addAction(action_analyze_video)
        
        # Menu Ajuda
        menu_help = self.menuBar().addMenu("Ajuda")
        
        action_about = QAction(self.load_icon("about.png"), "Sobre", self)
        action_about.setStatusTip("Informações sobre o GONETWORK AI")
        action_about.triggered.connect(self.on_about)
        
        action_help = QAction(self.load_icon("help.png"), "Ajuda", self)
        action_help.setShortcut("F1")
        action_help.setStatusTip("Mostrar ajuda")
        action_help.triggered.connect(self.on_help)
        
        menu_help.addAction(action_help)
        menu_help.addSeparator()
        menu_help.addAction(action_about)
        
    def create_toolbars(self):
        """Criar barras de ferramentas"""
        # Barra de ferramentas principal
        main_toolbar = QToolBar("Principal")
        main_toolbar.setObjectName("main_toolbar")
        main_toolbar.setIconSize(QSize(24, 24))
        main_toolbar.setMovable(True)
        
        # Adicionar ações à barra de ferramentas
        main_toolbar.addAction(QAction(self.load_icon("new_event.png"), "Novo Evento", self,
                                     triggered=self.on_new_event))
        main_toolbar.addAction(QAction(self.load_icon("open_event.png"), "Abrir Evento", self,
                                     triggered=self.on_open_event))
        main_toolbar.addSeparator()
        
        # Navegação rápida
        main_toolbar.addAction(QAction(self.load_icon("dashboard.png"), "Dashboard", self,
                                     triggered=lambda: self.tabs.setCurrentIndex(0)))
        main_toolbar.addAction(QAction(self.load_icon("event.png"), "Eventos", self,
                                     triggered=lambda: self.tabs.setCurrentIndex(1)))
        main_toolbar.addAction(QAction(self.load_icon("team.png"), "Equipe", self,
                                     triggered=lambda: self.tabs.setCurrentIndex(2)))
        main_toolbar.addAction(QAction(self.load_icon("delivery.png"), "Entregas", self,
                                     triggered=lambda: self.tabs.setCurrentIndex(3)))
        main_toolbar.addAction(QAction(self.load_icon("analyze.png"), "Ativações", self,
                                     triggered=lambda: self.tabs.setCurrentIndex(4)))
        main_toolbar.addAction(QAction(self.load_icon("media.png"), "Assets", self,
                                     triggered=lambda: self.tabs.setCurrentIndex(5)))
        
        self.addToolBar(main_toolbar)
        
        # Barra de ferramentas secundária
        second_toolbar = QToolBar("Ferramentas")
        second_toolbar.setObjectName("second_toolbar")
        second_toolbar.setIconSize(QSize(24, 24))
        second_toolbar.setMovable(True)
        
        # Ações de ferramentas
        second_toolbar.addAction(QAction(self.load_icon("backup.png"), "Backup", self,
                                      triggered=self.on_backup))
        second_toolbar.addAction(QAction(self.load_icon("document.png"), "Gerar Relatório", self,
                                      triggered=self.on_export_pdf_report))
        second_toolbar.addAction(QAction(self.load_icon("export.png"), "Exportar Dados", self,
                                      triggered=self.on_export_raw_data))
        second_toolbar.addAction(QAction(self.load_icon("analyze.png"), "Analisar Vídeo", self,
                                      triggered=self.on_analyze_video))
        second_toolbar.addAction(QAction(self.load_icon("settings.png"), "Configurações", self,
                                      triggered=self.on_settings))
        
        self.addToolBar(Qt.TopToolBarArea, second_toolbar)
        
    def create_status_bar(self):
        """Configurar barra de status"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Componentes da barra de status
        self.status_event_label = QLabel("Nenhum evento selecionado")
        self.status_bar.addPermanentWidget(self.status_event_label)
        
        self.status_user_label = QLabel(f"Usuário: {os.getenv('USER', 'contatogonetwork')}")
        self.status_bar.addPermanentWidget(self.status_user_label)
        
        self.status_date_label = QLabel(datetime.now().strftime("%d/%m/%Y %H:%M"))
        self.status_bar.addPermanentWidget(self.status_date_label)
        
        # Timer para atualizar o relógio
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(30000)  # Atualiza a cada 30 segundos
        
    def update_clock(self):
        """Atualizar o relógio na barra de status"""
        self.status_date_label.setText(datetime.now().strftime("%d/%m/%Y %H:%M"))
        
    def load_settings(self):
        """Carregar configurações salvas"""
        # Geometria da janela
        if self.settings.contains("mainwindow/geometry"):
            self.restoreGeometry(self.settings.value("mainwindow/geometry"))
        else:
            # Tamanho padrão
            screen_size = QApplication.primaryScreen().size()
            self.resize(int(screen_size.width() * 0.8), int(screen_size.height() * 0.8))
            
        # Estado da janela
        if self.settings.contains("mainwindow/state"):
            self.restoreState(self.settings.value("mainwindow/state"))
            
        # Tema
        theme = self.settings.value("appearance/theme", "dark")
        self.change_theme(theme)
        
        # Última aba selecionada
        last_tab = self.settings.value("mainwindow/last_tab", 0, type=int)
        if 0 <= last_tab < self.tabs.count():
            self.tabs.setCurrentIndex(last_tab)
            
        # Último evento selecionado
        last_event_id = self.settings.value("mainwindow/last_event_id", None)
        if last_event_id is not None:
            self.load_last_event(last_event_id)
            
    def save_settings(self):
        """Salvar configurações"""
        # Geometria e estado
        self.settings.setValue("mainwindow/geometry", self.saveGeometry())
        self.settings.setValue("mainwindow/state", self.saveState())
        
        # Última aba
        self.settings.setValue("mainwindow/last_tab", self.tabs.currentIndex())
        
        # Último evento
        if self.current_event:
            # Verificar se é um objeto ou um ID
            if isinstance(self.current_event, int):
                self.settings.setValue("mainwindow/last_event_id", self.current_event)
            else:
                self.settings.setValue("mainwindow/last_event_id", self.current_event.id)
            
        # Sincronizar
        self.settings.sync()
        
    def change_theme(self, theme):
        """Mudar o tema da aplicação
        
        Args:
            theme (str): "dark" ou "light"
        """
        stylesheet = ""
        
        if theme == "dark":
            # Tema escuro
            stylesheet = """
            QMainWindow, QDialog {
                background-color: #252525;
                color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #5c5c5c;
                background-color: #2d2d2d;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #d0d0d0;
                padding: 8px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #4c4c4c;
                color: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #454545;
            }
            QToolBar {
                background-color: #2a2a2a;
                border: none;
                spacing: 3px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 3px;
            }
            QToolButton:hover {
                background-color: #3a3a3a;
                border: 1px solid #5a5a5a;
            }
            QToolButton:pressed {
                background-color: #505050;
            }
            QMenuBar {
                background-color: #2a2a2a;
                color: #f0f0f0;
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 12px;
            }
            QMenuBar::item:selected {
                background-color: #3a3a3a;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #5c5c5c;
            }
            QMenu::item {
                padding: 6px 25px 6px 25px;
                border: 1px solid transparent;
            }
            QMenu::item:selected {
                background-color: #3a3a3a;
            }
            QStatusBar {
                background-color: #2a2a2a;
                color: #c0c0c0;
            }
            QLabel, QCheckBox, QRadioButton {
                color: #f0f0f0;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #353535;
                color: #f0f0f0;
                border: 1px solid #5c5c5c;
                border-radius: 3px;
                padding: 2px;
            }
            QPushButton {
                background-color: #424242;
                color: #f0f0f0;
                border: 1px solid #5c5c5c;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #4e4e4e;
            }
            QPushButton:pressed {
                background-color: #383838;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #7f7f7f;
            }
            QGroupBox {
                border: 1px solid #5c5c5c;
                border-radius: 5px;
                margin-top: 1.5ex;
                color: #d0d0d0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
            """
        else:
            # Tema claro
            stylesheet = """
            QMainWindow, QDialog {
                background-color: #f5f5f5;
                color: #202020;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: #ffffff;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: #404040;
                padding: 8px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #f0f0f0;
                color: #202020;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d8d8d8;
            }
            QToolBar {
                background-color: #f0f0f0;
                border: none;
                spacing: 3px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 3px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
            }
            QToolButton:pressed {
                background-color: #d0d0d0;
            }
            QMenuBar {
                background-color: #f0f0f0;
                color: #202020;
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 12px;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
            QMenu {
                background-color: #ffffff;
                color: #202020;
                border: 1px solid #c0c0c0;
            }
            QMenu::item {
                padding: 6px 25px 6px 25px;
                border: 1px solid transparent;
            }
            QMenu::item:selected {
                background-color: #e0e0e0;
            }
            QStatusBar {
                background-color: #f0f0f0;
                color: #505050;
            }
            QLabel, QCheckBox, QRadioButton {
                color: #202020;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #ffffff;
                color: #202020;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                padding: 2px;
            }
            QPushButton {
                background-color: #e0e0e0;
                color: #202020;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #a0a0a0;
            }
            QGroupBox {
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                margin-top: 1.5ex;
                color: #303030;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
            """
            
        # Aplicar folha de estilo
        QApplication.instance().setStyleSheet(stylesheet)
        
        # Salvar configuração
        self.settings.setValue("appearance/theme", theme)
        
    def load_last_event(self, event_id):
        """Carregar último evento selecionado
        
        Args:
            event_id: ID do último evento
        """
        from core.database import Event
        
        try:
            event = self.db.query(Event).get(event_id)
            if event:
                self.on_event_selected(event)
                
        except Exception as e:
            logger.error(f"Erro ao carregar último evento: {str(e)}")
            
    def on_event_selected(self, event_id):
        """Atualiza a interface quando um evento é selecionado
        
        Args:
            event_id (int): ID do evento selecionado
        """
        self.current_event = event_id
        self.team_view.set_event(event_id)
        self.delivery_view.set_event(event_id)
        # self.activation_view.set_event(event_id) # Temporariamente desabilitado
        self.team_schedule_view.set_event(event_id)
        self.delivery_kanban_view.set_event(event_id)
            
    def on_tab_changed(self, index):
        """Manipulador para mudança de aba
        
        Args:
            index (int): Índice da nova aba
        """
        # Atualizar título da janela
        tab_title = self.tabs.tabText(index)
        self.setWindowTitle(f"GONETWORK AI - {tab_title}")
        
    def on_new_event(self):
        """Criar novo evento"""
        # Navegar para a aba de eventos
        self.tabs.setCurrentIndex(1)  # Índice da aba de eventos
        
        # Delegar para a view de eventos
        self.event_manager_view.on_new_event()
        
    def on_open_event(self):
        """Abrir diálogo para selecionar evento existente"""
        dialog = EventBrowserDialog(self.db, self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted and dialog.selected_event:
            self.on_event_selected(dialog.selected_event)
            
    def on_export(self):
        """Função legada - redireciona para a exportação de dados brutos"""
        self.on_export_raw_data()
    
    def on_export_raw_data(self):
        """Exportar dados brutos do evento para CSV/Excel"""
        if not hasattr(self, "current_event") or not self.current_event:
            QMessageBox.warning(self, "Exportar Dados", "Nenhum evento selecionado para exportação.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Dados Como", "", "Arquivos Excel (*.xlsx);;Arquivos CSV (*.csv)"
        )
        
        if not file_path:
            return  # Usuário cancelou
            
        try:
            # Determinar o tipo de arquivo pela extensão
            extension = os.path.splitext(file_path)[1].lower()
            
            if extension == '.xlsx':
                self.export_to_excel(file_path)
            elif extension == '.csv':
                self.export_to_csv(file_path)
            else:
                # Adicionar extensão padrão se não foi especificada
                if not extension:
                    file_path += '.xlsx'
                    self.export_to_excel(file_path)
            
            QMessageBox.information(self, "Exportação Concluída", 
                                 f"Dados exportados com sucesso para:\n{file_path}")
        except Exception as e:
            logger.error(f"Erro ao exportar dados: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar dados:\n{str(e)}")

    def on_export_pdf_report(self):
        """Abrir diálogo de geração de relatório em PDF"""
        if not hasattr(self, "current_event") or not self.current_event:
            QMessageBox.warning(self, "Gerar Relatório", "Nenhum evento selecionado para gerar relatório.")
            return
            
        if not self.check_pdf_dependencies():
            return
            
        try:
            # Importar módulo apenas quando necessário
            from ui.dialogs.report_dialog import ReportGeneratorDialog
            
            # Criar e exibir o diálogo de configuração do relatório
            dialog = ReportGeneratorDialog(self.session, self.current_event.id, parent=self)
            dialog.exec_()
            
        except ImportError as e:
            logger.error(f"Erro ao importar módulo de relatórios: {str(e)}")
            QMessageBox.critical(self, "Erro", "Módulo de relatórios não disponível.\nVerifique se todas as dependências estão instaladas.")
        except Exception as e:
            logger.error(f"Erro ao gerar relatório PDF: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório:\n{str(e)}")

    def check_pdf_dependencies(self):
        """Verifica se as dependências para geração de PDF estão instaladas
        
        Returns:
            bool: True se todas as dependências estiverem disponíveis
        """
        try:
            # Verificar ReportLab
            import reportlab
            
            # Verificar Pandas para dados
            import pandas
            
            return True
        except ImportError as e:
            package = "reportlab" if "reportlab" in str(e) else "pandas"
            QMessageBox.warning(
                self, 
                "Dependências Ausentes", 
                f"A biblioteca {package} não está instalada.\n\n"
                f"Por favor, execute o comando:\n"
                f"pip install {package}"
            )
            return False

    def export_to_excel(self, file_path):
        """Exporta dados do evento atual para Excel"""
        # Verificar se pandas está disponível
        try:
            import pandas as pd
        except ImportError:
            QMessageBox.critical(self, "Erro", "Biblioteca pandas não está instalada.\nInstale com: pip install pandas openpyxl")
            return
            
        # Extrair dados do evento em DataFrame
        event_data = {
            "Nome": [self.current_event.name],
            "Data Inicial": [self.current_event.start_date],
            "Data Final": [self.current_event.end_date],
            "Local": [self.current_event.location],
            "Responsável": [self.current_event.responsible_person],
            "Orçamento": [self.current_event.budget],
            "Status": [self.current_event.status]
        }
        
        # Criar um objeto ExcelWriter
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Exportar informações gerais do evento
            pd.DataFrame(event_data).to_excel(writer, sheet_name='Evento', index=False)
            
            # Exportar atividades
            if hasattr(self.current_event, 'activities') and self.current_event.activities:
                activities_df = pd.DataFrame([
                    {
                        "Nome": a.name,
                        "Descrição": a.description, 
                        "Início": a.start_time,
                        "Fim": a.end_time,
                        "Responsável": a.responsible,
                        "Status": a.status
                    } for a in self.current_event.activities
                ])
                activities_df.to_excel(writer, sheet_name='Atividades', index=False)
                
            # Exportar entregas
            if hasattr(self.current_event, 'deliveries') and self.current_event.deliveries:
                deliveries_df = pd.DataFrame([
                    {
                        "Nome": d.name,
                        "Descrição": d.description,
                        "Data de Entrega": d.delivery_date,
                        "Responsável": d.responsible,
                        "Status": d.status
                    } for d in self.current_event.deliveries
                ])
                deliveries_df.to_excel(writer, sheet_name='Entregas', index=False)
                
            # Exportar equipe
            if hasattr(self.current_event, 'team_assignments') and self.current_event.team_assignments:
                team_df = pd.DataFrame([
                    {
                        "Membro": t.member_name,
                        "Função": t.role,
                        "Data Início": t.start_date,
                        "Data Fim": t.end_date,
                        "Observações": t.notes
                    } for t in self.current_event.team_assignments
                ])
                team_df.to_excel(writer, sheet_name='Equipe', index=False)

    def export_to_csv(self, file_path):
        """Exporta dados do evento atual para CSV"""
        try:
            import pandas as pd
            import csv
        except ImportError:
            QMessageBox.critical(self, "Erro", "Biblioteca pandas não está instalada.\nInstale com: pip install pandas")
            return
            
        # Exportar apenas os dados principais do evento para CSV
        event_data = {
            "Nome": [self.current_event.name],
            "Data Inicial": [self.current_event.start_date],
            "Data Final": [self.current_event.end_date],
            "Local": [self.current_event.location],
            "Responsável": [self.current_event.responsible_person],
            "Orçamento": [self.current_event.budget],
            "Status": [self.current_event.status]
        }
        
        df = pd.DataFrame(event_data)
        df.to_csv(file_path, index=False)
            
    def on_backup(self):
        """Fazer backup do banco de dados"""
        # Determinar nome e local do arquivo de backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"gonetwork_backup_{timestamp}.db"
        
        backup_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Salvar Backup",
            os.path.join(os.path.expanduser("~"), default_name),
            "Arquivos de Banco de Dados (*.db);;Todos os Arquivos (*.*)"
        )
        
        if not backup_path:
            return
            
        try:
            self.status_bar.showMessage("Fazendo backup do banco de dados...")
            
            # Caminho do banco atual
            db_path = self.settings.value("database/path", DEFAULT_DB_PATH)
            
            # Copiar arquivo
            import shutil
            shutil.copy2(db_path, backup_path)
            
            QMessageBox.information(self, "Backup Concluído",
                                 f"Backup do banco de dados criado com sucesso em:\n{backup_path}")
                                 
        except Exception as e:
            logger.error(f"Erro no backup: {str(e)}")
            QMessageBox.critical(self, "Erro de Backup",
                              f"Ocorreu um erro ao criar o backup:\n\n{str(e)}")
            
        finally:
            self.status_bar.showMessage("Pronto", 5000)
            
    def on_restore(self):
        """Restaurar backup do banco de dados"""
        # Aviso importante
        reply = QMessageBox.warning(
            self,
            "Confirmação de Restauração",
            "ATENÇÃO: Restaurar um backup substituirá TODOS os dados atuais!\n\n"
            "Recomendamos fazer um backup antes de continuar.\n\n"
            "Deseja continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # Selecionar arquivo de backup
        backup_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Selecionar Arquivo de Backup",
            os.path.expanduser("~"),
            "Arquivos de Banco de Dados (*.db);;Todos os Arquivos (*.*)"
        )
        
        if not backup_path or not os.path.exists(backup_path):
            return
            
        try:
            self.status_bar.showMessage("Restaurando backup...")
            
            # Caminho do banco atual
            db_path = self.settings.value("database/path", DEFAULT_DB_PATH)
            
            # Backup do arquivo atual antes de substituir
            temp_backup = f"{db_path}.before_restore.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            import shutil
            shutil.copy2(db_path, temp_backup)
            
            # Aguardar todas as operações do banco terminarem
            self.db.close()
            
            # Substituir arquivo
            shutil.copy2(backup_path, db_path)
            
            QMessageBox.information(self, "Restauração Concluída",
                                 "Backup restaurado com sucesso!\n"
                                 "A aplicação será reiniciada para aplicar as mudanças.")
                                 
            # Reiniciar aplicação
            self.restart_application()
            
        except Exception as e:
            logger.error(f"Erro na restauração: {str(e)}")
            QMessageBox.critical(self, "Erro de Restauração",
                              f"Ocorreu um erro ao restaurar o backup:\n\n{str(e)}")
            
            # Tentar reconectar ao banco
            try:
                self.db = create_session()
            except Exception:
                QMessageBox.critical(self, "Erro Crítico",
                                  "Não foi possível reconectar ao banco de dados.\n"
                                  "A aplicação será encerrada.")
                self.close()
                
        finally:
            self.status_bar.showMessage("Pronto", 5000)
            
    def on_analyze_video(self):
        """Abrir ferramenta de análise de vídeo com IA"""
        # Selecionar vídeo para análise
        video_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Vídeo para Análise",
            os.path.expanduser("~"),
            "Arquivos de Vídeo (*.mp4 *.avi *.mov *.mkv *.webm);;Todos os Arquivos (*.*)"
        )
        
        if not video_path or not os.path.exists(video_path):
            return
            
        try:
            # Importar módulo de análise
            from modules.ai.video_analyzer import VideoAnalyzer
            
            # Mostrar feedback na interface
            self.status_bar.showMessage("Analisando vídeo, aguarde...")
            
            # Criar instância do analisador
            analyzer = VideoAnalyzer()
            
            # Executar análise (simplificado - em uma aplicação real, isso seria assíncrono)
            summary = analyzer.summarize_video(video_path)
            
            if summary:
                # Em uma implementação completa, abriríamos uma tela de resultados
                QMessageBox.information(self, "Análise Concluída", 
                                     f"Análise do vídeo '{os.path.basename(video_path)}' concluída.")
            else:
                QMessageBox.warning(self, "Análise Incompleta", 
                                 "Não foi possível concluir a análise completa do vídeo.")
                
        except ImportError:
            QMessageBox.critical(self, "Erro", "Módulo de análise de vídeo não disponível.")
        except Exception as e:
            logger.error(f"Erro na análise de vídeo: {str(e)}")
            QMessageBox.critical(self, "Erro de Análise", 
                              f"Ocorreu um erro ao analisar o vídeo:\n\n{str(e)}")
            
        finally:
            self.status_bar.showMessage("Pronto", 5000)
            
    def on_settings(self):
        """Abrir diálogo de configurações"""
        dialog = SettingsDialog(self)
        dialog.exec_()
        
    def on_help(self):
        """Mostrar ajuda"""
        # Em uma implementação completa, abriríamos um manual detalhado
        QMessageBox.information(self, "Ajuda", 
                             "O manual de ajuda completo está disponível online em:\n"
                             "https://gonetwork.com/support/gonetwork-ai-manual")
            
    def on_about(self):
        """Mostrar diálogo 'Sobre'"""
        dialog = AboutDialog(self)
        dialog.exec_()
        
    def closeEvent(self, event: QCloseEvent):
        """Manipulador para evento de fechamento da janela
        
        Args:
            event: Evento de fechamento
        """
        # Verificar se precisa confirmar
        confirm_exit = self.settings.value("general/confirm_exit", True, type=bool)
        
        if confirm_exit:
            reply = QMessageBox.question(
                self, 
                "Confirmação de Saída",
                "Tem certeza que deseja sair do GONETWORK AI?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                event.ignore()
                return
                
        # Salvar configurações
        self.save_settings()
        
        # Fechar sessão do banco de dados
        if self.db:
            self.db.close()
            
        # Aceitar evento de fechamento
        event.accept()
        
    def restart_application(self):
        """Reiniciar a aplicação"""
        # Salvar configurações
        self.save_settings()
        
        # Executar novo processo
        QApplication.quit()
        os.execl(sys.executable, sys.executable, *sys.argv)
        
    def on_delivery_edit(self, delivery_id):
        """Editar entrega quando for clicada no Kanban
        
        Args:
            delivery_id (int): ID da entrega a ser editada
        """
        try:
            # Encontrar entrega no banco de dados
            from core.database import Delivery
            delivery = self.db.query(Delivery).get(delivery_id)
            
            if delivery:
                from ui.dialogs.delivery_dialog import DeliveryDialog
                dialog = DeliveryDialog(self.db, delivery.event_id, delivery=delivery, parent=self)
                
                if dialog.exec_() == QDialog.Accepted:
                    # Atualizar visualizações
                    self.delivery_kanban_view.refresh_data()
                    self.delivery_view.refresh_data()
            else:
                QMessageBox.warning(self, "Erro", f"Entrega com ID {delivery_id} não encontrada")
        
        except Exception as e:
            logger.error(f"Erro ao editar entrega: {str(e)}")
            QMessageBox.warning(self, "Erro", f"Não foi possível editar a entrega: {str(e)}")
            
    def on_assignment_updated(self, assignment_id):
        """Atualiza a visualização da equipe quando uma atribuição é modificada
        
        Args:
            assignment_id (int): ID da atribuição atualizada
        """
        # Notificar a view principal de equipe sobre a atualização
        self.team_view.refresh_data()
        
def show_splash_screen():
    """Mostrar tela de splash durante inicialização"""
    # Criar pixmap para a tela de splash
    splash_pixmap = QPixmap("resources/images/splash.png")
    if splash_pixmap.isNull():
        # Fallback se a imagem não existir
        splash_pixmap = QPixmap(500, 300)
        splash_pixmap.fill(QColor(41, 128, 185))  # Azul
        
    # Criar e mostrar splash screen
    splash = QSplashScreen(splash_pixmap, Qt.WindowStaysOnTopHint)
    splash.show()
    
    # Mensagem de carregamento
    splash.showMessage(
        "Carregando componentes...",
        Qt.AlignBottom | Qt.AlignCenter,
        Qt.white
    )
    QApplication.processEvents()
    
    return splash

def main():
    """Função principal da aplicação"""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='gonetwork_ai.log'
    )
    
    # Criar aplicação
    app = QApplication(sys.argv)
    app.setApplicationName("GONETWORK AI")
    app.setOrganizationName("GONETWORK")
    
    # Mostrar tela de splash
    splash = show_splash_screen()
    
    try:
        # Garantir que diretórios necessários existam
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Carregar configurações
        settings = QSettings("GONETWORK", "GONETWORK AI")
        db_path = settings.value("database/path", DEFAULT_DB_PATH)
        
        # Criar pasta pai do banco de dados se não existir
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            
        # Configurar banco de dados
        splash.showMessage("Configurando banco de dados...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        QApplication.processEvents()
        
        # Usar a função init_database que inicializa o banco com dados padrão
        db_session = init_database()
        
        # Carregar fontes personalizadas
        splash.showMessage("Carregando recursos...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        QApplication.processEvents()
        
        # Criar e mostrar janela principal
        splash.showMessage("Iniciando aplicação...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        QApplication.processEvents()
        
        main_window = MainWindow(db_session)
        main_window.show()
        
        # Fechar splash
        splash.finish(main_window)
        
        # Executar ciclo de eventos
        sys.exit(app.exec_())
        
    except Exception as e:
        # Tratar erros de inicialização
        logging.critical(f"Erro fatal durante inicialização: {str(e)}", exc_info=True)
        
        # Fechar splash se estiver ativo
        if 'splash' in locals():
            splash.close()
            
        # Mostrar erro ao usuário
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("Erro Fatal")
        error_box.setText("Ocorreu um erro ao inicializar a aplicação.")
        error_box.setDetailedText(str(e))
        error_box.exec_()
        
        sys.exit(1)

if __name__ == "__main__":
    main()
