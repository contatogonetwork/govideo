"""
GONETWORK AI - Inicialização da aplicação com arquitetura MVC
Este arquivo demonstra como inicializar e integrar os controllers com as views
usando a nova arquitetura MVC
"""

import sys
import os
import logging
from datetime import datetime
import sqlalchemy

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QStatusBar, 
    QWidget, QVBoxLayout, QAction, QMenu, QToolBar, 
    QMessageBox, QFileDialog, QLabel, QComboBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

# Importar controladores MVC
from controllers.timeline_controller import TimelineController
from controllers.delivery_controller import DeliveryKanbanController
from controllers.team_controller import TeamController 
from controllers.asset_controller import AssetController
from controllers.sponsor_controller import SponsorController

# Importar views MVC
from ui.views.delivery_kanban_view_mvc import DeliveryKanbanMVC
from ui.views.asset_library_view_mvc import AssetLibraryMVC

# Importar módulos necessários
from core.database import create_session, Base, engine
from core.config import Settings
from core.logging_manager import LogManager, get_logger
from models.event import Event

# Configurar logging
logger = get_logger(__name__)

class ApplicationMVC(QMainWindow):
    """Aplicação principal do GONETWORK AI com arquitetura MVC"""
    
    def __init__(self):
        super().__init__()
        
        # Carregar configurações
        self.settings = Settings.load_from_file("c:/govideo/settings.json")
        
        # Configurar banco de dados
        self.setup_database()
        
        # Inicializar controladores
        self.init_controllers()
        
        # Configurar interface
        self.setup_ui()
        
        # Configuração inicial
        self.setup_initial_state()
        
        # Carregar dados iniciais
        self.load_initial_data()
        
        # Conectar sinais e slots
        self.connect_signals()
    
    def setup_database(self):
        """Configura conexão com banco de dados"""
        try:
            # Criar sessão de banco de dados
            self.session = create_session(self.settings.database_path)
            logger.info(f"Conectado ao banco de dados: {self.settings.database_path}")
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self, 
                "Erro de Banco de Dados", 
                f"Não foi possível conectar ao banco de dados.\nErro: {str(e)}"
            )
            sys.exit(1)
    
    def init_controllers(self):
        """Inicializa os controladores MVC"""
        # Inicializar controladores com a sessão de banco de dados
        self.timeline_controller = TimelineController(self.session)
        self.delivery_controller = DeliveryKanbanController(self.session)
        self.team_controller = TeamController(self.session)
        self.asset_controller = AssetController(self.session)
        self.sponsor_controller = SponsorController(self.session)
        
        logger.info("Controladores MVC inicializados")
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        self.setWindowTitle("GONETWORK AI - Demonstração MVC")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon("resources/icons/logo.png"))
        
        # Criar barra de menus
        self.create_menus()
        
        # Criar barra de ferramentas
        self.create_toolbar()
        
        # Criar widget central com abas
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        
        # Inicializar views
        self.init_views()
        
        # Definir widget central
        self.setCentralWidget(self.tabs)
        
        # Barra de status
        self.statusBar = QStatusBar()
        self.event_selector = QComboBox()
        self.event_selector.setMinimumWidth(200)
        self.event_selector.currentIndexChanged.connect(self.on_event_changed)
        
        status_label = QLabel("Evento atual:")
        self.statusBar.addWidget(status_label)
        self.statusBar.addWidget(self.event_selector)
        
        # Adicionar info da sessão
        self.db_status_label = QLabel()
        self.statusBar.addPermanentWidget(self.db_status_label)
        
        self.setStatusBar(self.statusBar)
    
    def create_menus(self):
        """Cria a barra de menus"""
        # Menu Arquivo
        file_menu = self.menuBar().addMenu("&Arquivo")
        
        new_event_action = QAction("&Novo Evento", self)
        new_event_action.triggered.connect(self.on_new_event)
        file_menu.addAction(new_event_action)
        
        file_menu.addSeparator()
        
        backup_action = QAction("Criar &Backup", self)
        backup_action.triggered.connect(self.on_create_backup)
        file_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("&Sair", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Editar
        edit_menu = self.menuBar().addMenu("&Editar")
        
        preferences_action = QAction("&Preferências", self)
        preferences_action.triggered.connect(self.on_preferences)
        edit_menu.addAction(preferences_action)
        
        # Menu Visão
        view_menu = self.menuBar().addMenu("&Visão")
        
        for i, tab_name in enumerate(["Kanban", "Assets", "Timeline", "Equipe", "Patrocinadores"]):
            action = QAction(tab_name, self)
            action.setCheckable(True)
            action.setChecked(i < 2)  # Primeiras duas abas ativas por padrão
            action.triggered.connect(lambda checked, idx=i: self.toggle_tab(idx, checked))
            view_menu.addAction(action)
            
        # Menu Ajuda
        help_menu = self.menuBar().addMenu("A&juda")
        
        about_action = QAction("&Sobre", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Cria a barra de ferramentas"""
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setMovable(False)
        
        # Botões da barra de ferramentas
        new_event_btn = QAction(QIcon("resources/icons/event.png"), "Novo Evento", self)
        new_event_btn.triggered.connect(self.on_new_event)
        self.toolbar.addAction(new_event_btn)
        
        refresh_btn = QAction(QIcon("resources/icons/refresh.png"), "Atualizar", self)
        refresh_btn.triggered.connect(self.refresh_data)
        self.toolbar.addAction(refresh_btn)
        
        # Adicionar barra de ferramentas
        self.addToolBar(self.toolbar)
    
    def init_views(self):
        """Inicializa as views MVC"""
        # View do Kanban de Entregas
        self.delivery_kanban_view = DeliveryKanbanMVC(self.session)
        self.tabs.addTab(self.delivery_kanban_view, "Kanban de Entregas")
        
        # View da Biblioteca de Assets
        self.asset_library_view = AssetLibraryMVC(self.session)
        self.tabs.addTab(self.asset_library_view, "Biblioteca de Mídia")
        
        # Aqui seriam adicionadas as outras views (por enquanto só temos as duas implementadas)
    
    def setup_initial_state(self):
        """Configura o estado inicial da aplicação"""
        # Definir o título da janela principal
        self.setWindowTitle(f"GONETWORK AI - {self.settings.app_name} v{self.settings.app_version}")
        
        # Atualizar mensagem na barra de status
        self.db_status_label.setText(
            f"Banco de dados: {os.path.basename(self.settings.database_path)}"
        )
    
    def load_initial_data(self):
        """Carrega dados iniciais para a aplicação"""
        # Carregar eventos
        self.load_events()
        
        # Carregar dados para views
        self.asset_library_view.load_events()
    
    def connect_signals(self):
        """Conecta sinais e slots entre componentes"""
        # Conectar eventos de controllers às views
        # (A maior parte já está conectada nos construtores das views)
        
        # Exemplo de conexão entre controllers
        # Quando um asset é selecionado, podemos filtrá-lo em outras views
        self.asset_library_view.asset_selected.connect(self.on_asset_selected)
    
    def load_events(self):
        """Carrega a lista de eventos"""
        try:
            # Limpar e recarregar selector de eventos
            self.event_selector.clear()
            self.event_selector.addItem("Selecione um evento...", None)
            
            events = self.session.query(Event).order_by(Event.start_date.desc()).all()
            
            for event in events:
                self.event_selector.addItem(event.name, event.id)
                
            logger.info(f"Carregados {len(events)} eventos")
        
        except Exception as e:
            logger.error(f"Erro ao carregar eventos: {str(e)}", exc_info=True)
    
    def on_event_changed(self, index):
        """
        Manipulador para mudança de evento selecionado
        
        Args:
            index: Índice do item selecionado
        """
        event_id = self.event_selector.currentData()
        
        if event_id:
            # Informar às views e controllers sobre a mudança de evento
            self.delivery_kanban_view.set_event(event_id)
            # As demais views seriam atualizadas aqui
            
            logger.info(f"Evento atual alterado para: {self.event_selector.currentText()} (ID: {event_id})")
    
    def on_asset_selected(self, asset):
        """
        Manipulador para seleção de asset
        
        Args:
            asset (Asset): Asset selecionado
        """
        # Exemplo de interação entre views via controllers
        # Poderíamos filtar o Kanban para mostrar entregas relacionadas ao asset
        pass
    
    def toggle_tab(self, tab_index, is_visible):
        """
        Alterna visibilidade de uma aba
        
        Args:
            tab_index (int): Índice da aba
            is_visible (bool): Se deve estar visível
        """
        # Não implementado completamente, pois envolve remover/adicionar tabs
        pass
    
    def refresh_data(self):
        """Atualiza dados de todas as views"""
        # Recarregar dados nas views ativas
        current_tab_index = self.tabs.currentIndex()
        
        if current_tab_index == 0:  # Kanban
            self.delivery_kanban_view.refresh_data()
        elif current_tab_index == 1:  # Assets
            self.asset_library_view.refresh_data()
        # outras tabs seriam tratadas aqui
    
    def on_new_event(self):
        """Cria um novo evento"""
        # Aqui abriria um diálogo para criar novo evento
        # Exemplo de interação com controllers
        QMessageBox.information(
            self, 
            "Criar Evento", 
            "Aqui abriria o diálogo para criar um novo evento.\n\n"
            "Esta funcionalidade seria implementada utilizando o TimelineController."
        )
    
    def on_create_backup(self):
        """Cria um backup do banco de dados"""
        try:
            # Exemplo de como seria a implementação
            import shutil
            from datetime import datetime
            
            # Definir nome do arquivo de backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.db"
            backup_path = os.path.join(self.settings.backup_dir, backup_filename)
            
            # Garantir que o diretório de backup existe
            os.makedirs(self.settings.backup_dir, exist_ok=True)
            
            # Criar backup
            shutil.copy2(self.settings.database_path, backup_path)
            
            QMessageBox.information(
                self,
                "Backup Criado",
                f"Backup do banco de dados criado com sucesso em:\n{backup_path}"
            )
            
            logger.info(f"Backup criado em: {backup_path}")
            
        except Exception as e:
            logger.error(f"Erro ao criar backup: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self,
                "Erro de Backup",
                f"Erro ao criar backup do banco de dados:\n{str(e)}"
            )
    
    def on_preferences(self):
        """Abre diálogo de preferências"""
        QMessageBox.information(
            self, 
            "Preferências", 
            "Aqui abriria o diálogo de preferências da aplicação.\n\n"
            "Esta funcionalidade poderia utilizar as configurações do settings.json."
        )
    
    def on_about(self):
        """Mostra informações sobre o aplicativo"""
        QMessageBox.about(
            self,
            "Sobre GONETWORK AI",
            f"<h2>GONETWORK AI</h2>"
            f"<p>Versão: {self.settings.app_version}</p>"
            f"<p>Sistema para gerenciamento de eventos e produção de vídeo</p>"
            f"<p>Desenvolvido por equipe GONETWORK</p>"
            f"<p>&copy; 2025 GONETWORK</p>"
        )
    
    def closeEvent(self, event):
        """
        Manipulador para fechamento da aplicação
        
        Args:
            event: Evento de fechamento
        """
        # Perguntar ao usuário se deseja realmente sair
        reply = QMessageBox.question(
            self, 
            'Confirmação', 
            'Deseja realmente sair do aplicativo?',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Fechar sessão do banco de dados
            if self.session:
                self.session.close()
                logger.info("Sessão de banco de dados fechada")
                
            event.accept()
        else:
            event.ignore()


def main():
    """Função principal para iniciar a aplicação"""
    try:
        # Inicializar aplicação Qt
        app = QApplication(sys.argv)
        
        # Configurar estilo
        app.setStyle("Fusion")
        
        # Criar janela principal
        main_window = ApplicationMVC()
        main_window.show()
        
        # Executar loop principal
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.critical(f"Erro fatal na aplicação: {str(e)}", exc_info=True)
        QMessageBox.critical(
            None,
            "Erro Fatal",
            f"Ocorreu um erro fatal ao iniciar a aplicação:\n\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
