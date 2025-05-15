#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Diálogo Sobre
Data: 2025-05-15
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QDialogButtonBox, QWidget, QSpacerItem,
    QSizePolicy, QTabWidget
)
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt, QSize

class AboutDialog(QDialog):
    """Diálogo de informações sobre a aplicação"""
    
    def __init__(self, parent=None):
        """Inicializar diálogo
        
        Args:
            parent (QWidget, opcional): Widget pai
        """
        super().__init__(parent)
        self.setWindowTitle("Sobre o GONETWORK AI")
        self.setWindowIcon(QIcon("resources/icons/about.png"))
        self.setFixedSize(550, 450)
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface do usuário"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Criar abas
        tab_widget = QTabWidget()
        
        # Aba Sobre
        about_tab = QWidget()
        about_layout = self.create_about_tab(about_tab)
        
        # Aba Bibliotecas
        libraries_tab = QWidget()
        libraries_layout = self.create_libraries_tab(libraries_tab)
        
        # Aba Licença
        license_tab = QWidget()
        license_layout = self.create_license_tab(license_tab)
        
        # Adicionar abas ao widget
        tab_widget.addTab(about_tab, "Sobre")
        tab_widget.addTab(libraries_tab, "Bibliotecas")
        tab_widget.addTab(license_tab, "Licença")
        
        # Adicionar tab widget ao layout principal
        main_layout.addWidget(tab_widget)
        
        # Botão de fechar
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        
        main_layout.addWidget(button_box)
        
    def create_about_tab(self, tab_widget):
        """Criar conteúdo da aba Sobre
        
        Args:
            tab_widget (QWidget): Widget da aba
            
        Returns:
            QLayout: Layout da aba
        """
        # Layout da aba
        layout = QVBoxLayout(tab_widget)
        layout.setSpacing(15)
        
        # Logo
        logo_layout = QHBoxLayout()
        logo_label = QLabel()
        logo_pixmap = QPixmap("resources/images/logo.png")
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Fallback caso a imagem não seja encontrada
            logo_label.setText("GONETWORK AI")
            logo_label.setFont(QFont("Arial", 24, QFont.Bold))
            logo_label.setAlignment(Qt.AlignCenter)
        
        logo_layout.addStretch()
        logo_layout.addWidget(logo_label)
        logo_layout.addStretch()
        
        # Título
        title_label = QLabel("GONETWORK AI")
        title_font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        
        # Versão
        version_label = QLabel("Versão 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        
        # Descrição
        description = (
            "<p align='center'>Plataforma avançada de gerenciamento de produção audiovisual "
            "para eventos, desenvolvida para otimizar o fluxo de trabalho de equipes "
            "criativas em ambientes dinâmicos.</p>"
            "<p align='center'>Este software integra gestão de equipes, cronogramas, assets "
            "e entregas, além de incorporar tecnologias de IA para análise de conteúdo.</p>"
        )
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        
        # Informações de copyright
        copyright_text = "© 2025 GONETWORK. Todos os direitos reservados."
        copyright_label = QLabel(copyright_text)
        copyright_label.setAlignment(Qt.AlignCenter)
        
        # Data de build
        build_label = QLabel("Build: 2025-05-15")
        build_label.setAlignment(Qt.AlignCenter)
        
        # Adicionar widgets ao layout
        layout.addLayout(logo_layout)
        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addWidget(desc_label)
        layout.addSpacing(10)
        layout.addWidget(copyright_label)
        layout.addWidget(build_label)
        layout.addStretch()
        
        return layout
        
    def create_libraries_tab(self, tab_widget):
        """Criar conteúdo da aba Bibliotecas
        
        Args:
            tab_widget (QWidget): Widget da aba
            
        Returns:
            QLayout: Layout da aba
        """
        # Layout da aba
        layout = QVBoxLayout(tab_widget)
        
        # Título
        title_label = QLabel("Bibliotecas e Tecnologias Utilizadas")
        title_font = QFont("Arial", 12, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        
        # Lista de bibliotecas
        libraries_info = (
            "<p><b>Principais bibliotecas:</b></p>"
            "<ul>"
            "<li>PyQt5: Interface gráfica</li>"
            "<li>SQLAlchemy: ORM para banco de dados</li>"
            "<li>OpenCV: Processamento de imagens e vídeos</li>"
            "<li>pymediainfo: Extração de metadados de mídia</li>"
            "<li>NumPy: Computação científica</li>"
            "<li>pandas: Análise de dados</li>"
            "</ul>"
            "<p><b>Outras tecnologias:</b></p>"
            "<ul>"
            "<li>SQLite: Banco de dados leve</li>"
            "<li>FFmpeg: Processamento de mídia (opcional)</li>"
            "<li>Python 3.8+: Linguagem de programação</li>"
            "</ul>"
        )
        libraries_label = QLabel(libraries_info)
        libraries_label.setWordWrap(True)
        libraries_label.setOpenExternalLinks(True)
        
        # Adicionar widgets ao layout
        layout.addWidget(title_label)
        layout.addSpacing(10)
        layout.addWidget(libraries_label)
        layout.addStretch()
        
        return layout
        
    def create_license_tab(self, tab_widget):
        """Criar conteúdo da aba Licença
        
        Args:
            tab_widget (QWidget): Widget da aba
            
        Returns:
            QLayout: Layout da aba
        """
        # Layout da aba
        layout = QVBoxLayout(tab_widget)
        
        # Título
        title_label = QLabel("Informações de Licença")
        title_font = QFont("Arial", 12, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        
        # Texto da licença
        license_text = (
            "<p><b>GONETWORK AI</b></p>"
            "<p>Software Proprietário - Todos os Direitos Reservados</p>"
            "<p>Este software é protegido por leis de direitos autorais e tratados internacionais.</p>"
            "<p>A utilização não autorizada deste software está sujeita a medidas civis e penais.</p>"
            "<p>O uso deste software está sujeito aos termos do contrato de licença fornecido com o software.</p>"
            "<p><b>Componentes de Código Aberto:</b></p>"
            "<p>Este software utiliza componentes licenciados sob diversas licenças de código aberto, "
            "incluindo MIT, GPL e BSD. Os avisos completos de copyright e licenças estão disponíveis "
            "na documentação do programa.</p>"
        )
        license_label = QLabel(license_text)
        license_label.setWordWrap(True)
        license_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # Adicionar widgets ao layout
        layout.addWidget(title_label)
        layout.addSpacing(10)
        layout.addWidget(license_label)
        layout.addStretch()
        
        return layout