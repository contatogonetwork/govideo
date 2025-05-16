#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Diálogo de geração de relatórios
Data: 2025-05-15
Autor: GONETWORK AI
"""

import os
import logging
import tempfile
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QCheckBox, QComboBox, QRadioButton, QLineEdit, 
    QPushButton, QFileDialog, QProgressDialog, 
    QMessageBox, QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QSize
from PyQt5.QtGui import QDesktopServices

from core.pdf_report import EventReportGenerator
from reportlab.lib.pagesizes import A4, letter, A3

logger = logging.getLogger(__name__)

class ReportGeneratorDialog(QDialog):
    """Interface para geração de relatórios personalizáveis"""
    
    # Sinais para comunicação entre threads
    update_progress_signal = pyqtSignal(int)
    report_finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, session, event_id, parent=None):
        """Inicializa o diálogo de geração de relatórios
        
        Args:
            session: Sessão do banco de dados SQLAlchemy
            event_id (int): ID do evento
            parent (QWidget, opcional): Widget pai
        """
        super().__init__(parent)
        self.session = session
        self.event_id = event_id
        
        # Carregar evento
        from core.database import Event
        self.event = self.session.query(Event).get(event_id)
        if not self.event:
            raise ValueError(f"Evento com ID {event_id} não encontrado")
        
        # Configurar diálogo
        self.setWindowTitle("Gerador de Relatórios")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do usuário"""
        layout = QVBoxLayout(self)
        
        # Título e descrição
        title_label = QLabel(f"Relatório: {self.event.name}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        subtitle_label = QLabel(
            f"{self.event.location or 'Local não definido'} • "
            f"{self.event.start_date.strftime('%d/%m/%Y')} a "
            f"{self.event.end_date.strftime('%d/%m/%Y')}"
        )
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(10)
        
        # Seções para incluir no relatório
        sections_group = QGroupBox("Seções para incluir")
        sections_layout = QVBoxLayout(sections_group)
        
        self.include_summary = QCheckBox("Sumário Executivo")
        self.include_summary.setChecked(True)
        sections_layout.addWidget(self.include_summary)
        
        self.include_stats = QCheckBox("Estatísticas e Gráficos")
        self.include_stats.setChecked(True)
        sections_layout.addWidget(self.include_stats)
        
        self.include_activities = QCheckBox("Programação e Cronograma")
        self.include_activities.setChecked(True)
        sections_layout.addWidget(self.include_activities)
        
        self.include_deliveries = QCheckBox("Entregas e Produtos Finais")
        self.include_deliveries.setChecked(True)
        sections_layout.addWidget(self.include_deliveries)
        
        self.include_team = QCheckBox("Equipe e Atuação")
        self.include_team.setChecked(True)
        sections_layout.addWidget(self.include_team)
        
        self.include_sponsors = QCheckBox("Ativações de Patrocinadores")
        self.include_sponsors.setChecked(True)
        sections_layout.addWidget(self.include_sponsors)
        
        self.include_notes = QCheckBox("Observações Finais")
        self.include_notes.setChecked(True)
        sections_layout.addWidget(self.include_notes)
        
        layout.addWidget(sections_group)
        
        # Opções de formato
        format_group = QGroupBox("Opções de Formato")
        format_layout = QGridLayout(format_group)
        
        # Tipo de relatório
        format_layout.addWidget(QLabel("Tipo de Relatório:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItem("PDF", "pdf")
        self.format_combo.addItem("Excel (Apenas Dados)", "xlsx")
        self.format_combo.setCurrentIndex(0)  # PDF como padrão
        format_layout.addWidget(self.format_combo, 0, 1)
        
        # Opção de logo
        format_layout.addWidget(QLabel("Incluir Logo:"), 1, 0)
        
        logo_layout = QHBoxLayout()
        self.logo_path_edit = QLineEdit()
        self.logo_path_edit.setPlaceholderText("Caminho para o arquivo de logo")
        logo_layout.addWidget(self.logo_path_edit)
        
        self.logo_browse_btn = QPushButton("Procurar...")
        self.logo_browse_btn.clicked.connect(self.browse_logo)
        logo_layout.addWidget(self.logo_browse_btn)
        
        format_layout.addLayout(logo_layout, 1, 1)
        
        layout.addWidget(format_group)
        
        # Opções avançadas
        self.advanced_btn = QPushButton("Opções Avançadas")
        self.advanced_btn.setCheckable(True)
        self.advanced_btn.clicked.connect(self.toggle_advanced_options)
        layout.addWidget(self.advanced_btn)
        
        self.advanced_group = QGroupBox("Opções Avançadas")
        self.advanced_group.setVisible(False)
        advanced_layout = QFormLayout(self.advanced_group)
        
        # Tamanho da página
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItem("A4", "A4")
        self.page_size_combo.addItem("Carta (Letter)", "LETTER")
        self.page_size_combo.addItem("A3", "A3")
        advanced_layout.addRow("Tamanho da Página:", self.page_size_combo)
        
        # Orientação
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItem("Retrato", "portrait")
        self.orientation_combo.addItem("Paisagem", "landscape")
        advanced_layout.addRow("Orientação:", self.orientation_combo)
        
        # Opções adicionais
        self.include_page_numbers = QCheckBox()
        self.include_page_numbers.setChecked(True)
        advanced_layout.addRow("Incluir Números de Página:", self.include_page_numbers)
        
        self.include_toc = QCheckBox()
        self.include_toc.setChecked(True)
        advanced_layout.addRow("Incluir Sumário:", self.include_toc)
        
        layout.addWidget(self.advanced_group)
        
        # Destino do relatório
        output_group = QGroupBox("Destino do Relatório")
        output_layout = QVBoxLayout(output_group)
        
        # Salvar como arquivo
        self.save_file_radio = QRadioButton("Salvar como arquivo")
        self.save_file_radio.setChecked(True)
        output_layout.addWidget(self.save_file_radio)
        
        file_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Caminho para salvar o relatório")
        file_layout.addWidget(self.output_path_edit)
        
        self.output_browse_btn = QPushButton("Procurar...")
        self.output_browse_btn.clicked.connect(self.browse_output)
        file_layout.addWidget(self.output_browse_btn)
        
        output_layout.addLayout(file_layout)
        
        # Enviar por e-mail
        self.email_radio = QRadioButton("Enviar por e-mail")
        output_layout.addWidget(self.email_radio)
        
        email_layout = QHBoxLayout()
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Endereço de e-mail")
        self.email_edit.setEnabled(False)
        email_layout.addWidget(self.email_edit)
        
        output_layout.addLayout(email_layout)
        
        # Conectar alteração de opção
        self.save_file_radio.toggled.connect(self.toggle_output_option)
        self.email_radio.toggled.connect(self.toggle_output_option)
        
        layout.addWidget(output_group)
        
        # Botões de ação
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.generate_report)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Ok).setText("Gerar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        
        # Conectar sinais
        self.report_finished_signal.connect(self.handle_report_finished)
    
    def toggle_advanced_options(self, checked):
        """Mostra/oculta opções avançadas
        
        Args:
            checked (bool): Estado do botão
        """
        self.advanced_group.setVisible(checked)
        self.adjustSize()
    
    def toggle_output_option(self, checked):
        """Alterna entre opções de saída
        
        Args:
            checked (bool): Estado do botão
        """
        # Habilitar entrada de e-mail somente se a opção estiver selecionada
        self.email_edit.setEnabled(self.email_radio.isChecked())
        # Habilitar seleção de arquivo somente se a opção estiver selecionada
        self.output_path_edit.setEnabled(self.save_file_radio.isChecked())
        self.output_browse_btn.setEnabled(self.save_file_radio.isChecked())
    
    def browse_logo(self):
        """Abre um diálogo para selecionar um arquivo de logo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Selecionar Logo", 
            "", 
            "Imagens (*.png *.jpg *.jpeg *.gif);;Todos os arquivos (*.*)"
        )
        
        if file_path:
            self.logo_path_edit.setText(file_path)
    
    def browse_output(self):
        """Abre diálogo para selecionar destino do arquivo"""
        file_format = self.format_combo.currentData()
        
        # Definir filtro de arquivo com base no formato selecionado
        if file_format == "pdf":
            file_filter = "PDF (*.pdf)"
        else:
            file_filter = "Excel (*.xlsx)"
            
        file_extension = ".pdf" if file_format == "pdf" else ".xlsx"
        
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Relatório",
            os.path.expanduser("~") + f"/Relatório_{self.event.name.replace(' ', '_')}{file_extension}",
            file_filter
        )
        
        if file_name:
            self.output_path_edit.setText(file_name)
    
    def generate_report(self):
        """Gera o relatório com as opções selecionadas"""
        # Validar entradas
        if self.save_file_radio.isChecked() and not self.output_path_edit.text():
            QMessageBox.warning(
                self,
                "Caminho Inválido",
                "Por favor, selecione um destino para o relatório."
            )
            return
            
        if self.email_radio.isChecked() and not self.email_edit.text():
            QMessageBox.warning(
                self,
                "E-mail Inválido",
                "Por favor, informe um endereço de e-mail válido."
            )
            return
        
        # Verificar dependências
        if not self.check_dependencies():
            return
        
        # Configurar gerador de relatório
        report_generator = EventReportGenerator(self.session, self.event_id)
        
        # Caminho de saída
        if self.save_file_radio.isChecked():
            output_path = self.output_path_edit.text()
        else:
            # Para e-mail, usar arquivo temporário
            file_format = self.format_combo.currentData()
            ext = ".pdf" if file_format == "pdf" else ".xlsx"
            output_path = tempfile.mktemp(suffix=ext)
        
        # Obter tamanho da página
        page_size_map = {
            "A4": A4,
            "LETTER": letter,
            "A3": A3
        }
        page_size = page_size_map.get(self.page_size_combo.currentData(), A4)
        
        # Definir orientação
        orientation = self.orientation_combo.currentData()
        
        # Definir seções a incluir
        include_sections = {
            'summary': self.include_summary.isChecked(),
            'activities': self.include_activities.isChecked(),
            'deliveries': self.include_deliveries.isChecked(),
            'team': self.include_team.isChecked(),
            'sponsors': self.include_sponsors.isChecked(),
            'notes': self.include_notes.isChecked()
        }
        
        # Mostrar diálogo de progresso
        progress_dialog = QProgressDialog("Gerando relatório...", "Cancelar", 0, 100, self)
        progress_dialog.setWindowTitle("Gerando Relatório")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setValue(0)
        progress_dialog.show()
        
        # Gerar relatório em thread separada para não travar a UI
        def generate_thread():
            try:
                # Atualizar progresso
                self.update_progress_signal.emit(10)
                
                # Gerar relatório
                success = report_generator.generate_complete_report(
                    output_path=output_path,
                    logo_path=self.logo_path_edit.text() if self.logo_path_edit.text() else None,
                    include_charts=self.include_stats.isChecked(),
                    include_sections=include_sections,
                    page_size=page_size,
                    orientation=orientation
                )
                
                self.update_progress_signal.emit(80)
                
                # Se for para enviar por e-mail
                if success and self.email_radio.isChecked():
                    # Aqui seria implementado o envio de e-mail
                    self.send_email(output_path, self.email_edit.text())
                
                self.update_progress_signal.emit(100)
                
                # Mostrar resultado
                if success:
                    self.report_finished_signal.emit(True, output_path)
                else:
                    self.report_finished_signal.emit(False, "Erro ao gerar relatório")
            except Exception as e:
                logger.error(f"Erro ao gerar relatório: {str(e)}")
                self.report_finished_signal.emit(False, str(e))
        
        # Conectar sinal de progresso
        self.update_progress_signal.connect(progress_dialog.setValue)
        
        # Iniciar thread
        threading.Thread(target=generate_thread).start()
    
    def handle_report_finished(self, success, message):
        """Manipula o resultado da geração do relatório
        
        Args:
            success (bool): True se o relatório foi gerado com sucesso
            message (str): Mensagem de resultado ou caminho do arquivo
        """
        if success:
            if self.save_file_radio.isChecked():
                QMessageBox.information(
                    self,
                    "Relatório Gerado",
                    f"O relatório foi gerado com sucesso em:\n{message}"
                )
                # Abrir o arquivo gerado
                QDesktopServices.openUrl(QUrl.fromLocalFile(message))
            else:
                QMessageBox.information(
                    self,
                    "Relatório Enviado",
                    f"O relatório foi enviado com sucesso para {self.email_edit.text()}"
                )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Erro",
                f"Ocorreu um erro ao gerar o relatório:\n{message}"
            )
    
    def send_email(self, file_path, email):
        """Envia o relatório por e-mail
        
        Args:
            file_path (str): Caminho do arquivo a ser enviado
            email (str): Endereço de e-mail do destinatário
            
        Note:
            Esta é uma implementação simplificada. Uma implementação completa
            usaria bibliotecas como smtplib ou uma API de e-mail.
        """
        # TODO: Implementar envio de e-mail real
        # Esta é apenas uma simulação para a interface
        logger.info(f"Enviando e-mail para {email} com o arquivo {file_path}")
        # Simular atraso de envio
        import time
        time.sleep(1)
    
    def check_dependencies(self):
        """Verifica se todas as dependências para geração de relatórios estão instaladas
        
        Returns:
            bool: True se todas as dependências estiverem presentes
        """
        try:
            # Verificar ReportLab
            import reportlab
            logger.info(f"ReportLab versão {reportlab.Version} instalada")
            
            # Verificar Pandas (para gráficos e análise de dados)
            try:
                import pandas
                logger.info(f"Pandas versão {pandas.__version__} instalada")
            except ImportError:
                QMessageBox.warning(
                    self, 
                    "Dependência Faltante", 
                    "A biblioteca pandas não está instalada. Alguns recursos de gráficos e análises estatísticas podem não funcionar corretamente.\n\n" +
                    "Recomendamos instalar com o comando:\npip install pandas"
                )
                # Não é crítica, então continuamos
            
            # Verificar matplotlib (para gráficos adicionais)
            try:
                import matplotlib
                logger.info(f"Matplotlib versão {matplotlib.__version__} instalada")
            except ImportError:
                # Não é crítica, então apenas logamos
                logger.warning("Matplotlib não está instalada. Alguns gráficos avançados não estarão disponíveis.")
            
            return True
            
        except ImportError:
            QMessageBox.critical(
                self, 
                "Dependência Crítica Faltante", 
                "A biblioteca ReportLab, necessária para geração de PDFs, não está instalada.\n\n" +
                "Por favor, instale com o comando:\npip install reportlab"
            )
            return False
