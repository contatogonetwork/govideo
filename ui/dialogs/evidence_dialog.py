#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Diálogo para gestão de evidências de ativações
Data: 2025-05-15
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QFileDialog, QMessageBox, QLineEdit,
    QGridLayout, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QImage

from models.activation_evidence import ActivationEvidence

class EvidenceDialog(QDialog):
    """Diálogo para adicionar uma evidência de ativação"""
    
    def __init__(self, activation, file_path=None, parent=None):
        """
        Inicializa o diálogo
        
        Args:
            activation: Objeto SponsorActivation
            file_path: Caminho do arquivo (opcional)
            parent: Widget pai (opcional)
        """
        super().__init__(parent)
        self.activation = activation
        self.file_path = file_path
        self.file_type = self._get_file_type(file_path) if file_path else None
        
        self.setWindowTitle("Adicionar Evidência")
        self.resize(500, 400)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do diálogo"""
        layout = QVBoxLayout(self)
        
        # Cabeçalho
        header = QHBoxLayout()
        title = QLabel(f"Evidência para: {self.activation.name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        layout.addLayout(header)
        
        # Informações da ativação
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px; padding: 10px;")
        
        info_layout = QVBoxLayout(info_frame)
        info_layout.addWidget(QLabel(f"<b>Patrocinador:</b> {self.activation.sponsor.name if self.activation.sponsor else ''}"))
        info_layout.addWidget(QLabel(f"<b>Data:</b> {self.activation.scheduled_date.strftime('%d/%m/%Y') if self.activation.scheduled_date else ''}"))
        info_layout.addWidget(QLabel(f"<b>Local:</b> {self.activation.location or ''}"))
        
        layout.addWidget(info_frame)
        
        # Prévia do arquivo
        if self.file_path:
            preview_frame = QFrame()
            preview_frame.setFrameShape(QFrame.StyledPanel)
            preview_frame.setStyleSheet("border: 1px solid #ddd; padding: 10px;")
            preview_layout = QVBoxLayout(preview_frame)
            
            # Título do arquivo
            file_name = os.path.basename(self.file_path)
            file_label = QLabel(f"<b>Arquivo:</b> {file_name}")
            preview_layout.addWidget(file_label)
            
            # Prévia de imagem
            if self.file_type == "image":
                image = QImage(self.file_path)
                if not image.isNull():
                    pixmap = QPixmap.fromImage(image)
                    pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    image_label = QLabel()
                    image_label.setPixmap(pixmap)
                    image_label.setAlignment(Qt.AlignCenter)
                    preview_layout.addWidget(image_label)
                else:
                    preview_layout.addWidget(QLabel("Não foi possível carregar a imagem"))
            
            # Ícone para vídeo
            elif self.file_type == "video":
                video_icon = QIcon(":/icons/video_file.png").pixmap(64, 64)
                
                icon_label = QLabel()
                icon_label.setPixmap(video_icon)
                icon_label.setAlignment(Qt.AlignCenter)
                
                preview_layout.addWidget(icon_label)
                preview_layout.addWidget(QLabel("Arquivo de vídeo"))
            
            # Ícone para documento
            elif self.file_type == "document":
                doc_icon = QIcon(":/icons/document_file.png").pixmap(64, 64)
                
                icon_label = QLabel()
                icon_label.setPixmap(doc_icon)
                icon_label.setAlignment(Qt.AlignCenter)
                
                preview_layout.addWidget(icon_label)
                preview_layout.addWidget(QLabel("Arquivo de documento"))
                
            # Botão para trocar arquivo
            change_btn = QPushButton("Trocar Arquivo")
            change_btn.clicked.connect(self.on_change_file)
            preview_layout.addWidget(change_btn)
            
            layout.addWidget(preview_frame)
        else:
            # Se não houver arquivo, mostrar botão para selecionar
            select_btn = QPushButton("Selecionar Arquivo")
            select_btn.clicked.connect(self.on_select_file)
            layout.addWidget(select_btn)
        
        # Campo para descrição
        layout.addWidget(QLabel("Descrição da evidência:"))
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Descreva detalhes sobre esta evidência...")
        layout.addWidget(self.description_edit)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Salvar")
        self.save_btn.setEnabled(bool(self.file_path))
        self.save_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
    def on_select_file(self):
        """Abre diálogo para selecionar arquivo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo",
            "",
            "Todos os Arquivos (*.jpg *.jpeg *.png *.gif *.mp4 *.mov *.pdf *.doc *.docx)"
        )
        
        if file_path:
            self.file_path = file_path
            self.file_type = self._get_file_type(file_path)
            
            # Recriar interface
            self._clear_layout(self.layout())
            self.setup_ui()
            
    def on_change_file(self):
        """Troca o arquivo atual"""
        self.on_select_file()
        
    def get_description(self):
        """Retorna a descrição inserida"""
        return self.description_edit.toPlainText()
        
    def _get_file_type(self, file_path):
        """Determina o tipo de arquivo com base na extensão"""
        if not file_path:
            return None
            
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return "image"
        elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv']:
            return "video"
        elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
            return "document"
        else:
            return "other"
            
    def _clear_layout(self, layout):
        """Limpa todos os widgets de um layout"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())


class EvidenceGalleryDialog(QDialog):
    """Galeria de evidências de uma ativação"""
    
    evidence_removed = pyqtSignal(int)
    
    def __init__(self, activation, controller, parent=None):
        """
        Inicializa o diálogo
        
        Args:
            activation: Objeto SponsorActivation
            controller: Controlador SponsorActivationController
            parent: Widget pai (opcional)
        """
        super().__init__(parent)
        self.activation = activation
        self.controller = controller
        
        self.setWindowTitle(f"Galeria de Evidências - {activation.name}")
        self.resize(800, 600)
        self.setup_ui()
        self.load_evidences()
        
    def setup_ui(self):
        """Configura a interface do diálogo"""
        layout = QVBoxLayout(self)
        
        # Cabeçalho
        header = QHBoxLayout()
        title = QLabel(f"Evidências para: {self.activation.name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        
        # Botão para adicionar nova evidência
        add_btn = QPushButton("Adicionar Evidência")
        add_btn.clicked.connect(self.on_add_evidence)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # Informações da ativação
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px; padding: 10px;")
        
        info_grid = QGridLayout(info_frame)
        info_grid.addWidget(QLabel("<b>Patrocinador:</b>"), 0, 0)
        info_grid.addWidget(QLabel(self.activation.sponsor.name if self.activation.sponsor else ""), 0, 1)
        
        info_grid.addWidget(QLabel("<b>Data:</b>"), 0, 2)
        info_grid.addWidget(QLabel(self.activation.scheduled_date.strftime("%d/%m/%Y") if self.activation.scheduled_date else ""), 0, 3)
        
        info_grid.addWidget(QLabel("<b>Status:</b>"), 1, 0)
        status_label = QLabel(self.activation.status.capitalize())
        status_color = {
            "pending": "#FFC107",      # Amarelo
            "in_progress": "#2196F3",  # Azul
            "completed": "#4CAF50",    # Verde
            "canceled": "#9E9E9E",     # Cinza
        }.get(self.activation.status, "#000000")
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        info_grid.addWidget(status_label, 1, 1)
        
        info_grid.addWidget(QLabel("<b>Local:</b>"), 1, 2)
        info_grid.addWidget(QLabel(self.activation.location or ""), 1, 3)
        
        layout.addWidget(info_frame)
        
        # Área de rolagem para evidências
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # Conteúdo da galeria
        self.gallery_content = QWidget()
        self.gallery_layout = QGridLayout(self.gallery_content)
        
        scroll.setWidget(self.gallery_content)
        layout.addWidget(scroll)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.accept)
        
        self.export_btn = QPushButton("Exportar Evidências")
        self.export_btn.clicked.connect(self.on_export_evidences)
        
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
    def load_evidences(self):
        """Carrega evidências da ativação"""
        # Limpar layout
        self._clear_layout(self.gallery_layout)
        
        # Obter evidências do banco
        evidences = self.controller.db.query(ActivationEvidence).filter(
            ActivationEvidence.activation_id == self.activation.id
        ).order_by(
            ActivationEvidence.created_at.desc()
        ).all()
        
        if not evidences:
            label = QLabel("Nenhuma evidência registrada para esta ativação")
            label.setAlignment(Qt.AlignCenter)
            self.gallery_layout.addWidget(label, 0, 0)
            return
            
        # Adicionar evidências à galeria
        row, col = 0, 0
        max_cols = 3
        
        for evidence in evidences:
            item = self._create_evidence_item(evidence)
            self.gallery_layout.addWidget(item, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
    def _create_evidence_item(self, evidence):
        """Cria um item para a galeria de evidências"""
        item = QFrame()
        item.setFrameShape(QFrame.StyledPanel)
        item.setStyleSheet("border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 5px;")
        item.setMinimumSize(230, 250)
        item.setMaximumSize(250, 350)
        
        layout = QVBoxLayout(item)
        
        # Tipo de evidência
        type_label = QLabel(evidence.type_name)
        type_label.setStyleSheet("font-weight: bold; color: #666;")
        layout.addWidget(type_label)
        
        # Prévia da evidência
        preview_frame = QFrame()
        preview_layout = QVBoxLayout(preview_frame)
        
        file_type = evidence.file_type
        
        # Mostrar prévia baseada no tipo
        if file_type == "image":
            image = QImage(evidence.file_path)
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                pixmap = pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                image_label = QLabel()
                image_label.setPixmap(pixmap)
                image_label.setAlignment(Qt.AlignCenter)
                preview_layout.addWidget(image_label)
            else:
                preview_layout.addWidget(QLabel("Imagem não disponível"))
                
        elif file_type == "video":
            video_icon = QIcon(":/icons/video_file.png").pixmap(64, 64)
            icon_label = QLabel()
            icon_label.setPixmap(video_icon)
            icon_label.setAlignment(Qt.AlignCenter)
            preview_layout.addWidget(icon_label)
            
        elif file_type == "document":
            doc_icon = QIcon(":/icons/document_file.png").pixmap(64, 64)
            icon_label = QLabel()
            icon_label.setPixmap(doc_icon)
            icon_label.setAlignment(Qt.AlignCenter)
            preview_layout.addWidget(icon_label)
        
        # Nome do arquivo
        file_name = os.path.basename(evidence.file_path)
        if len(file_name) > 25:
            file_name = file_name[:22] + "..."
        preview_layout.addWidget(QLabel(file_name))
        
        layout.addWidget(preview_frame)
        
        # Descrição
        if evidence.description:
            description = evidence.description
            if len(description) > 100:
                description = description[:97] + "..."
                
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #333;")
            layout.addWidget(desc_label)
            
        # Data de criação
        date_label = QLabel(f"Adicionado em: {evidence.created_at.strftime('%d/%m/%Y %H:%M')}")
        date_label.setStyleSheet("font-size: 10px; color: #999;")
        layout.addWidget(date_label)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        view_btn = QPushButton("Abrir")
        view_btn.clicked.connect(lambda: self.on_view_evidence(evidence))
        
        delete_btn = QPushButton("Excluir")
        delete_btn.clicked.connect(lambda: self.on_delete_evidence(evidence))
        
        button_layout.addWidget(view_btn)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        
        return item
        
    def on_add_evidence(self):
        """Adiciona nova evidência"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo",
            "",
            "Todos os Arquivos (*.jpg *.jpeg *.png *.gif *.mp4 *.mov *.pdf *.doc *.docx)"
        )
        
        if not file_path:
            return
            
        dialog = EvidenceDialog(self.activation, file_path, self)
        if dialog.exec_():
            file_type = dialog._get_file_type(file_path)
            type_id = {"image": 1, "video": 2, "document": 3}.get(file_type, 1)
            
            evidence = self.controller.add_evidence(
                self.activation.id,
                file_path,
                dialog.get_description(),
                type_id
            )
            
            if evidence:
                self.load_evidences()
                
    def on_view_evidence(self, evidence):
        """Abre o arquivo de evidência"""
        if not os.path.exists(evidence.file_path):
            QMessageBox.warning(self, "Arquivo não encontrado", 
                               "O arquivo de evidência não foi encontrado no caminho especificado.")
            return
            
        # Abrir arquivo com aplicativo padrão do sistema (usar QDesktopServices)
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl
        
        QDesktopServices.openUrl(QUrl.fromLocalFile(evidence.file_path))
        
    def on_delete_evidence(self, evidence):
        """Remove uma evidência"""
        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            "Deseja realmente excluir esta evidência?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.controller.remove_evidence(evidence.id)
            if success:
                self.evidence_removed.emit(evidence.id)
                self.load_evidences()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível remover a evidência")
                
    def on_export_evidences(self):
        """Exporta todas as evidências para um diretório"""
        # Selecionar diretório de destino
        directory = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Diretório para Exportação"
        )
        
        if not directory:
            return
            
        # Obter evidências
        evidences = self.controller.db.query(ActivationEvidence).filter(
            ActivationEvidence.activation_id == self.activation.id
        ).all()
        
        if not evidences:
            QMessageBox.information(self, "Informação", "Não há evidências para exportar")
            return
            
        # Criar relatório e copiar arquivos
        # Esta é uma versão simplificada, uma implementação real
        # poderia criar um PDF ou ZIP com as evidências
        try:
            import shutil
            from datetime import datetime
            
            # Criar subdiretório com nome da ativação
            safe_name = "".join(c for c in self.activation.name if c.isalnum() or c in " _-").strip()
            safe_name = safe_name.replace(" ", "_")
            
            # Adicionar timestamp para evitar sobrescrever
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_dir = os.path.join(directory, f"{safe_name}_{timestamp}")
            
            os.makedirs(export_dir, exist_ok=True)
            
            # Copiar cada arquivo
            copied_count = 0
            for evidence in evidences:
                if os.path.exists(evidence.file_path):
                    dest_file = os.path.join(export_dir, os.path.basename(evidence.file_path))
                    shutil.copy2(evidence.file_path, dest_file)
                    copied_count += 1
                    
            QMessageBox.information(
                self, 
                "Exportação Concluída", 
                f"{copied_count} de {len(evidences)} arquivos foram exportados para:\n{export_dir}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro na Exportação",
                f"Ocorreu um erro durante a exportação:\n{str(e)}"
            )
            
    def _clear_layout(self, layout):
        """Limpa todos os widgets de um layout"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())
