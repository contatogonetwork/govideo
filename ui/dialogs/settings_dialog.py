#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Diálogo de configurações da aplicação
Data: 2025-05-15
"""

import os
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QWidget, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QComboBox,
    QCheckBox, QPushButton, QFileDialog,
    QDialogButtonBox, QColorDialog, QGroupBox,
    QMessageBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QSettings, QDir, pyqtSlot
from PyQt5.QtGui import QIcon, QColor

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Diálogo de configurações da aplicação"""
    
    def __init__(self, parent=None):
        """Inicializar diálogo
        
        Args:
            parent (QWidget, opcional): Widget pai
        """
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setWindowIcon(QIcon("resources/icons/settings.png"))
        self.setMinimumSize(600, 500)
        
        # Carregar configurações existentes
        self.settings = QSettings("GONETWORK", "GONETWORK AI")
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Configurar interface do usuário"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Criar abas de configurações
        self.tabs = QTabWidget()
        
        # Aba Geral
        general_tab = QWidget()
        general_layout = self.create_general_tab(general_tab)
        
        # Aba Diretórios
        dirs_tab = QWidget()
        dirs_layout = self.create_directories_tab(dirs_tab)
        
        # Aba Aparência
        appearance_tab = QWidget()
        appearance_layout = self.create_appearance_tab(appearance_tab)
        
        # Aba Avançado
        advanced_tab = QWidget()
        advanced_layout = self.create_advanced_tab(advanced_tab)
        
        # Adicionar abas ao widget de abas
        self.tabs.addTab(general_tab, "Geral")
        self.tabs.addTab(dirs_tab, "Diretórios")
        self.tabs.addTab(appearance_tab, "Aparência")
        self.tabs.addTab(advanced_tab, "Avançado")
        
        # Adicionar as abas ao layout principal
        main_layout.addWidget(self.tabs)
        
        # Botões de OK/Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        
        main_layout.addWidget(button_box)
        
    def create_general_tab(self, tab_widget):
        """Criar conteúdo para aba de configurações gerais
        
        Args:
            tab_widget (QWidget): Widget da aba
            
        Returns:
            QLayout: Layout da aba
        """
        layout = QVBoxLayout(tab_widget)
        
        # Grupo interface do usuário
        ui_group = QGroupBox("Interface do Usuário")
        ui_form = QFormLayout(ui_group)
        
        # Idioma
        self.language_combo = QComboBox()
        self.language_combo.addItem("Português (Brasil)", "pt_BR")
        self.language_combo.addItem("English (US)", "en_US")
        self.language_combo.addItem("Español", "es_ES")
        ui_form.addRow("Idioma:", self.language_combo)
        
        # Confirmar ao sair
        self.confirm_exit_check = QCheckBox("Mostrar confirmação ao sair do programa")
        self.confirm_exit_check.setChecked(True)
        ui_form.addRow("", self.confirm_exit_check)
        
        # Auto salvar
        self.autosave_check = QCheckBox("Salvar automaticamente alterações")
        self.autosave_check.setChecked(True)
        ui_form.addRow("", self.autosave_check)
        
        # Intervalo de autosave
        self.autosave_spin = QSpinBox()
        self.autosave_spin.setRange(1, 60)
        self.autosave_spin.setValue(5)
        self.autosave_spin.setSuffix(" minutos")
        ui_form.addRow("Intervalo de autosave:", self.autosave_spin)
        
        # Grupo de visualização de datas
        date_group = QGroupBox("Visualização de Datas")
        date_form = QFormLayout(date_group)
        
        # Formato de datas
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItem("DD/MM/YYYY", "dd/MM/yyyy")
        self.date_format_combo.addItem("MM/DD/YYYY", "MM/dd/yyyy")
        self.date_format_combo.addItem("YYYY-MM-DD", "yyyy-MM-dd")
        date_form.addRow("Formato de data:", self.date_format_combo)
        
        # Formato de hora
        self.time_format_combo = QComboBox()
        self.time_format_combo.addItem("24 horas (14:30)", "HH:mm")
        self.time_format_combo.addItem("12 horas (2:30 PM)", "h:mm AP")
        date_form.addRow("Formato de hora:", self.time_format_combo)
        
        # Adicionar grupos ao layout
        layout.addWidget(ui_group)
        layout.addWidget(date_group)
        layout.addStretch()
        
        return layout
        
    def create_directories_tab(self, tab_widget):
        """Criar conteúdo para aba de diretórios
        
        Args:
            tab_widget (QWidget): Widget da aba
            
        Returns:
            QLayout: Layout da aba
        """
        layout = QVBoxLayout(tab_widget)
        
        # Função auxiliar para criar linhas de diretório
        def create_dir_row(label, setting_name, default_path):
            row_layout = QHBoxLayout()
            
            # Campo de texto para o caminho
            path_edit = QLineEdit()
            path_edit.setReadOnly(True)
            path_edit.setText(self.settings.value(setting_name, default_path))
            path_edit.setObjectName(setting_name)
            
            # Botão para selecionar diretório
            browse_btn = QPushButton("Navegar...")
            browse_btn.clicked.connect(lambda: self.browse_directory(path_edit))
            
            # Botão para restaurar padrão
            reset_btn = QPushButton("Padrão")
            reset_btn.clicked.connect(lambda: path_edit.setText(default_path))
            
            row_layout.addWidget(path_edit, 3)
            row_layout.addWidget(browse_btn, 1)
            row_layout.addWidget(reset_btn, 1)
            
            form_layout.addRow(label + ":", row_layout)
            
            # Guardar referência
            return path_edit
            
        # Grupo de diretórios de projeto
        dir_group = QGroupBox("Diretórios de Projeto")
        form_layout = QFormLayout(dir_group)
        
        # Diretórios para arquivos do projeto
        base_dir = QDir.homePath() + "/GONETWORK"
        
        self.uploads_dir_edit = create_dir_row("Uploads", "paths/uploads", base_dir + "/uploads")
        self.exports_dir_edit = create_dir_row("Exportações", "paths/exports", base_dir + "/exports")
        self.temp_dir_edit = create_dir_row("Temporário", "paths/temp", base_dir + "/temp")
        self.logs_dir_edit = create_dir_row("Logs", "paths/logs", base_dir + "/logs")
        
        # Adicionar ao layout principal
        layout.addWidget(dir_group)
        
        # Grupo de configurações de banco de dados
        db_group = QGroupBox("Banco de Dados")
        db_form = QFormLayout(db_group)
        
        # Caminho do banco de dados
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setReadOnly(True)
        db_path = self.settings.value("database/path", base_dir + "/gonetwork.db")
        self.db_path_edit.setText(db_path)
        
        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_edit, 3)
        db_path_layout.addWidget(QPushButton("Navegar..."), 1)
        
        db_form.addRow("Arquivo de banco:", db_path_layout)
        
        # Backup automático
        self.db_backup_check = QCheckBox("Fazer backup automático do banco de dados ao sair")
        self.db_backup_check.setChecked(self.settings.value("database/auto_backup", True, type=bool))
        db_form.addRow("", self.db_backup_check)
        
        # Adicionar ao layout principal
        layout.addWidget(db_group)
        layout.addStretch()
        
        return layout
        
    def create_appearance_tab(self, tab_widget):
        """Criar conteúdo para aba de aparência
        
        Args:
            tab_widget (QWidget): Widget da aba
            
        Returns:
            QLayout: Layout da aba
        """
        layout = QVBoxLayout(tab_widget)
        
        # Grupo de tema
        theme_group = QGroupBox("Tema")
        theme_layout = QVBoxLayout(theme_group)
        
        # Seleção de tema (radio buttons)
        self.theme_group = QButtonGroup(self)
        
        self.dark_theme_radio = QRadioButton("Tema Escuro")
        self.light_theme_radio = QRadioButton("Tema Claro")
        self.system_theme_radio = QRadioButton("Usar tema do sistema")
        
        self.theme_group.addButton(self.dark_theme_radio, 0)
        self.theme_group.addButton(self.light_theme_radio, 1)
        self.theme_group.addButton(self.system_theme_radio, 2)
        
        # Por padrão, usar tema escuro
        self.dark_theme_radio.setChecked(True)
        
        theme_layout.addWidget(self.dark_theme_radio)
        theme_layout.addWidget(self.light_theme_radio)
        theme_layout.addWidget(self.system_theme_radio)
        
        # Grupo de fontes
        font_group = QGroupBox("Fontes")
        font_form = QFormLayout(font_group)
        
        # Tamanho da fonte
        self.font_size_combo = QComboBox()
        for size in [8, 9, 10, 11, 12, 14]:
            self.font_size_combo.addItem(f"{size} pt", size)
        self.font_size_combo.setCurrentIndex(2)  # 10pt por padrão
        font_form.addRow("Tamanho da fonte:", self.font_size_combo)
        
        # Grupo de cores
        color_group = QGroupBox("Cores Personalizadas")
        color_form = QFormLayout(color_group)
        
        # Função para criar seletor de cor
        def create_color_picker(label, setting_name, default_color):
            row_layout = QHBoxLayout()
            
            # Botão para selecionar cor
            color_btn = QPushButton()
            color_btn.setFixedSize(24, 24)
            color_btn.setObjectName(setting_name)
            
            # Cor atual
            color_str = self.settings.value(setting_name, default_color)
            color = QColor(color_str)
            
            # Definir estilo do botão com a cor
            color_btn.setStyleSheet(f"background-color: {color.name()}")
            
            # Conectar clique à seleção de cor
            color_btn.clicked.connect(lambda: self.select_color(color_btn))
            
            # Label para mostrar valor hex
            color_label = QLabel(color.name())
            color_label.setObjectName(setting_name + "_label")
            
            row_layout.addWidget(color_btn)
            row_layout.addWidget(color_label)
            row_layout.addStretch()
            
            color_form.addRow(label + ":", row_layout)
            return color_btn, color_label
        
        # Cores específicas
        self.accent_color_btn, self.accent_color_label = create_color_picker(
            "Cor de destaque", "colors/accent", "#3d8af7")
            
        self.critical_color_btn, self.critical_color_label = create_color_picker(
            "Cor de alerta", "colors/critical", "#e74c3c")
        
        # Adicionar grupos ao layout
        layout.addWidget(theme_group)
        layout.addWidget(font_group)
        layout.addWidget(color_group)
        layout.addStretch()
        
        return layout
        
    def create_advanced_tab(self, tab_widget):
        """Criar conteúdo para aba de configurações avançadas
        
        Args:
            tab_widget (QWidget): Widget da aba
            
        Returns:
            QLayout: Layout da aba
        """
        layout = QVBoxLayout(tab_widget)
        
        # Grupo de desempenho
        perf_group = QGroupBox("Desempenho")
        perf_form = QFormLayout(perf_group)
        
        # Cache de imagens
        self.image_cache_spin = QSpinBox()
        self.image_cache_spin.setRange(50, 1000)
        self.image_cache_spin.setValue(200)
        self.image_cache_spin.setSuffix(" MB")
        perf_form.addRow("Cache de imagens:", self.image_cache_spin)
        
        # Número de threads
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 16)
        self.threads_spin.setValue(4)
        perf_form.addRow("Threads de processamento:", self.threads_spin)
        
        # Limpar dados temporários ao sair
        self.clear_temp_check = QCheckBox("Limpar arquivos temporários ao sair")
        self.clear_temp_check.setChecked(True)
        perf_form.addRow("", self.clear_temp_check)
        
        # Grupo de logs
        log_group = QGroupBox("Logs e Depuração")
        log_form = QFormLayout(log_group)
        
        # Nível de log
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem("Erro", "ERROR")
        self.log_level_combo.addItem("Aviso", "WARNING")
        self.log_level_combo.addItem("Informação", "INFO")
        self.log_level_combo.addItem("Depuração", "DEBUG")
        self.log_level_combo.setCurrentIndex(2)  # INFO por padrão
        log_form.addRow("Nível de log:", self.log_level_combo)
        
        # Retenção de logs
        self.log_retention_spin = QSpinBox()
        self.log_retention_spin.setRange(1, 90)
        self.log_retention_spin.setValue(14)
        self.log_retention_spin.setSuffix(" dias")
        log_form.addRow("Manter logs por:", self.log_retention_spin)
        
        # Botões para ações avançadas
        actions_group = QGroupBox("Ações Avançadas")
        actions_layout = QVBoxLayout(actions_group)
        
        # Botões para ações avançadas
        self.clear_cache_btn = QPushButton("Limpar Todos os Caches")
        self.reset_settings_btn = QPushButton("Restaurar Configurações Padrão")
        self.reset_settings_btn.clicked.connect(self.on_reset_settings)
        
        actions_layout.addWidget(self.clear_cache_btn)
        actions_layout.addWidget(self.reset_settings_btn)
        
        # Adicionar grupos ao layout
        layout.addWidget(perf_group)
        layout.addWidget(log_group)
        layout.addWidget(actions_group)
        layout.addStretch()
        
        return layout
        
    def browse_directory(self, line_edit):
        """Abrir diálogo para selecionar diretório
        
        Args:
            line_edit (QLineEdit): Campo para exibir o caminho selecionado
        """
        current_path = line_edit.text()
        directory = QFileDialog.getExistingDirectory(
            self, "Selecionar Diretório", current_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            line_edit.setText(directory)
            
    def select_color(self, button):
        """Abrir diálogo para selecionar cor
        
        Args:
            button (QPushButton): Botão que mostra a cor
        """
        # Obter cor atual
        current_style = button.styleSheet()
        current_color = QColor(current_style.split(":")[1].strip())
        
        # Abrir diálogo de seleção de cor
        color = QColorDialog.getColor(
            current_color, self, "Selecionar Cor",
            QColorDialog.ShowAlphaChannel
        )
        
        if color.isValid():
            # Atualizar botão e label
            button.setStyleSheet(f"background-color: {color.name()}")
            
            # Buscar label associado
            setting_name = button.objectName()
            label_name = setting_name + "_label"
            
            for child in button.parent().children():
                if child.objectName() == label_name and isinstance(child, QLabel):
                    child.setText(color.name())
                    break
                    
    def load_settings(self):
        """Carregar configurações salvas"""
        # Geral - Interface
        language = self.settings.value("general/language", "pt_BR")
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == language:
                self.language_combo.setCurrentIndex(i)
                break
                
        self.confirm_exit_check.setChecked(self.settings.value("general/confirm_exit", True, type=bool))
        self.autosave_check.setChecked(self.settings.value("general/autosave", True, type=bool))
        self.autosave_spin.setValue(self.settings.value("general/autosave_interval", 5, type=int))
        
        # Geral - Formatos de data
        date_format = self.settings.value("general/date_format", "dd/MM/yyyy")
        for i in range(self.date_format_combo.count()):
            if self.date_format_combo.itemData(i) == date_format:
                self.date_format_combo.setCurrentIndex(i)
                break
                
        time_format = self.settings.value("general/time_format", "HH:mm")
        for i in range(self.time_format_combo.count()):
            if self.time_format_combo.itemData(i) == time_format:
                self.time_format_combo.setCurrentIndex(i)
                break
                
        # Aparência - Tema
        try:
            theme = self.settings.value("appearance/theme", 0)
            if isinstance(theme, str):
                theme = int(theme) if theme.isdigit() else 0
            
            if theme == 0:
                self.dark_theme_radio.setChecked(True)
            elif theme == 1:
                self.light_theme_radio.setChecked(True)
            else:
                self.system_theme_radio.setChecked(True)
        except Exception as e:
            # Em caso de erro, define o tema escuro como padrão
            self.dark_theme_radio.setChecked(True)
            
        # Aparência - Tamanho da fonte
        font_size = self.settings.value("appearance/font_size", 10, type=int)
        for i in range(self.font_size_combo.count()):
            if self.font_size_combo.itemData(i) == font_size:
                self.font_size_combo.setCurrentIndex(i)
                break
                
        # Avançado - Desempenho
        self.image_cache_spin.setValue(self.settings.value("advanced/image_cache", 200, type=int))
        self.threads_spin.setValue(self.settings.value("advanced/threads", 4, type=int))
        self.clear_temp_check.setChecked(self.settings.value("advanced/clear_temp", True, type=bool))
        
        # Avançado - Logs
        log_level = self.settings.value("advanced/log_level", "INFO")
        for i in range(self.log_level_combo.count()):
            if self.log_level_combo.itemData(i) == log_level:
                self.log_level_combo.setCurrentIndex(i)
                break
                
        self.log_retention_spin.setValue(self.settings.value("advanced/log_retention", 14, type=int))
        
    def apply_settings(self):
        """Aplicar as configurações atuais"""
        # Geral - Interface
        self.settings.setValue("general/language", self.language_combo.currentData())
        self.settings.setValue("general/confirm_exit", self.confirm_exit_check.isChecked())
        self.settings.setValue("general/autosave", self.autosave_check.isChecked())
        self.settings.setValue("general/autosave_interval", self.autosave_spin.value())
        
        # Geral - Formatos de data
        self.settings.setValue("general/date_format", self.date_format_combo.currentData())
        self.settings.setValue("general/time_format", self.time_format_combo.currentData())
        
        # Diretórios
        self.settings.setValue("paths/uploads", self.uploads_dir_edit.text())
        self.settings.setValue("paths/exports", self.exports_dir_edit.text())
        self.settings.setValue("paths/temp", self.temp_dir_edit.text())
        self.settings.setValue("paths/logs", self.logs_dir_edit.text())
        
        # Banco de dados
        self.settings.setValue("database/path", self.db_path_edit.text())
        self.settings.setValue("database/auto_backup", self.db_backup_check.isChecked())
        
        # Aparência - Tema
        self.settings.setValue("appearance/theme", self.theme_group.checkedId())
        self.settings.setValue("appearance/font_size", self.font_size_combo.currentData())
        
        # Aparência - Cores
        accent_color = self.accent_color_label.text()
        critical_color = self.critical_color_label.text()
        self.settings.setValue("colors/accent", accent_color)
        self.settings.setValue("colors/critical", critical_color)
        
        # Avançado - Desempenho
        self.settings.setValue("advanced/image_cache", self.image_cache_spin.value())
        self.settings.setValue("advanced/threads", self.threads_spin.value())
        self.settings.setValue("advanced/clear_temp", self.clear_temp_check.isChecked())
        
        # Avançado - Logs
        self.settings.setValue("advanced/log_level", self.log_level_combo.currentData())
        self.settings.setValue("advanced/log_retention", self.log_retention_spin.value())
        
        # Sincronizar configurações
        self.settings.sync()
        
        # Avisar usuário
        QMessageBox.information(self, "Configurações", "Configurações aplicadas com sucesso!")
        
        # Emitir sinal para que a aplicação principal atualize-se
        # Em uma implementação completa, seria um sinal personalizado
        
    def on_reset_settings(self):
        """Manipulador para resetar configurações"""
        reply = QMessageBox.question(
            self, "Restaurar Padrões", 
            "Tem certeza que deseja restaurar todas as configurações para os valores padrão?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Limpar todas as configurações
            self.settings.clear()
            
            # Recarregar com valores padrão
            self.load_settings()
            
            QMessageBox.information(self, "Configurações", "Configurações restauradas para valores padrão.")
        
    def accept(self):
        """Ação ao aceitar o diálogo"""
        # Aplicar configurações
        self.apply_settings()
        
        # Fechar diálogo
        super().accept()