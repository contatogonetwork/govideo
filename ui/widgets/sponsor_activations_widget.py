#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Widget de Visualização de Ativações Patrocinadas
Data: 2025-05-15
"""

import os
import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QFrame, QSizePolicy, QToolBar, QAction,
    QComboBox, QLineEdit, QMenu, QToolButton, QTableView,
    QHeaderView, QStyledItemDelegate, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QModelIndex, QAbstractTableModel, QSortFilterProxyModel
from PyQt5.QtGui import QIcon, QPixmap, QColor, QBrush, QPainter

from models.sponsor import Sponsor, SponsorActivation
from models.activation_evidence import ActivationEvidence
from controllers.sponsor_activation_controller import SponsorActivationController
from ui.dialogs.evidence_dialog import EvidenceDialog

class SponsorActivationStatusDelegate(QStyledItemDelegate):
    """Delegate personalizado para exibição de status com cores e ícones"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_colors = {
            "pending": QColor(255, 193, 7),      # Amarelo
            "in_progress": QColor(33, 150, 243), # Azul
            "completed": QColor(76, 175, 80),    # Verde
            "canceled": QColor(158, 158, 158),   # Cinza
            "failed": QColor(244, 67, 54)        # Vermelho
        }
        
        self.status_names = {
            "pending": "Pendente",
            "in_progress": "Em andamento",
            "completed": "Concluído",
            "canceled": "Cancelado",
            "failed": "Falhou"
        }
        
        self.status_icons = {
            "pending": QIcon(":/icons/clock.png"),
            "in_progress": QIcon(":/icons/in_progress.png"),
            "completed": QIcon(":/icons/check.png"),
            "canceled": QIcon(":/icons/cancel.png"),
            "failed": QIcon(":/icons/error.png")
        }
        
    def paint(self, painter, option, index):
        """Personaliza a pintura do item"""
        status = index.data(Qt.DisplayRole)
        
        if status in self.status_colors:
            # Salvar o estado do painter
            painter.save()
            
            # Desenhar o fundo com cor baseada no status
            color = self.status_colors.get(status)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color.lighter(150)))
            painter.drawRoundedRect(option.rect.adjusted(2, 2, -2, -2), 5, 5)
            
            # Desenhar o ícone se disponível
            if status in self.status_icons:
                icon_rect = option.rect.adjusted(4, 4, -option.rect.width() + 24, -4)
                self.status_icons[status].paint(painter, icon_rect)
                
            # Desenhar o texto do status
            text = self.status_names.get(status, status)
            painter.setPen(Qt.black)
            text_rect = option.rect.adjusted(28, 0, -4, 0)
            painter.drawText(text_rect, Qt.AlignVCenter, text)
            
            # Restaurar o estado do painter
            painter.restore()
        else:
            # Usar o comportamento padrão para status desconhecidos
            super().paint(painter, option, index)
            
    def sizeHint(self, option, index):
        """Define o tamanho preferido para o item"""
        default_size = super().sizeHint(option, index)
        return QSize(default_size.width(), 30)


class EvidenceCountDelegate(QStyledItemDelegate):
    """Delegate personalizado para exibir contagem de evidências com ícones"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paint(self, painter, option, index):
        """Personaliza a pintura do item"""
        count = index.data(Qt.DisplayRole)
        
        # Salvar o estado do painter
        painter.save()
        
        # Desenhar fundo semi-transparente
        if count > 0:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(76, 175, 80, 50)))  # Verde transparente
            painter.drawRoundedRect(option.rect.adjusted(2, 2, -2, -2), 5, 5)
        
        # Ícones de tipos de evidências
        icon_photo = QIcon(":/icons/photo.png")
        icon_video = QIcon(":/icons/video.png")
        
        # Obter contadores por tipo
        # Obs: Aqui apenas demonstramos visualmente. Na implementação real,
        # precisaríamos passar esses dados separadamente ou com um papel customizado
        
        # Para fins de demonstração visual:
        photos = count // 2  # Metade são fotos
        videos = count - photos  # Metade são vídeos
        
        # Exibir ícones
        icon_width = 16
        total_width = photos * icon_width + videos * icon_width + 4
        start_x = option.rect.center().x() - (total_width // 2)
        
        y = option.rect.center().y() - (icon_width // 2)
        
        # Desenhar ícones de fotos
        for i in range(photos):
            icon_rect = QRect(start_x + i * icon_width, y, icon_width, icon_width)
            icon_photo.paint(painter, icon_rect)
            
        # Desenhar ícones de vídeos
        for i in range(videos):
            icon_rect = QRect(start_x + (photos + i) * icon_width, y, icon_width, icon_width)
            icon_video.paint(painter, icon_rect)
            
        # Desenhar contador total
        painter.setPen(Qt.black)
        painter.drawText(option.rect, Qt.AlignCenter, f"{count}")
        
        # Restaurar o estado do painter
        painter.restore()
        
    def sizeHint(self, option, index):
        """Define o tamanho preferido para o item"""
        default_size = super().sizeHint(option, index)
        return QSize(default_size.width(), 30)


class SponsorActivationTableModel(QAbstractTableModel):
    """Modelo de tabela para ativações patrocinadas"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.activations = []
        self.evidence_counts = {}
        self.headers = [
            "ID", "Patrocinador", "Nome", "Data", "Local", 
            "Responsável", "Status", "Evidências", "Última Atualização"
        ]
        
    def set_data(self, activations, evidence_counts=None):
        """Define os dados do modelo"""
        self.beginResetModel()
        self.activations = activations
        self.evidence_counts = evidence_counts or {}
        self.endResetModel()
        
    def rowCount(self, parent=QModelIndex()):
        """Retorna o número de linhas no modelo"""
        return len(self.activations)
        
    def columnCount(self, parent=QModelIndex()):
        """Retorna o número de colunas no modelo"""
        return len(self.headers)
        
    def data(self, index, role=Qt.DisplayRole):
        """Retorna dados para o índice e papel específicos"""
        if not index.isValid() or index.row() >= len(self.activations):
            return None
            
        activation = self.activations[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:
                return activation.id
            elif column == 1:
                return activation.sponsor.name if activation.sponsor else ""
            elif column == 2:
                return activation.name
            elif column == 3:
                return activation.scheduled_date.strftime("%d/%m/%Y") if activation.scheduled_date else ""
            elif column == 4:
                return activation.location
            elif column == 5:
                return activation.responsible.name if hasattr(activation, 'responsible') and activation.responsible else ""
            elif column == 6:
                return activation.status
            elif column == 7:
                return self.evidence_counts.get(activation.id, 0)
            elif column == 8:
                return activation.updated_at.strftime("%d/%m/%Y %H:%M") if activation.updated_at else ""
        elif role == Qt.BackgroundRole:
            # Cor de fundo baseada na prioridade
            if activation.priority == 4:  # Urgente
                return QBrush(QColor(255, 87, 34, 30))  # Vermelho transparente
            elif activation.priority == 3:  # Alta
                return QBrush(QColor(255, 193, 7, 30))  # Amarelo transparente
            elif activation.priority == 2:  # Média
                return QBrush(QColor(76, 175, 80, 30))  # Verde transparente
        
        return None
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Retorna dados do cabeçalho"""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        
        return None


class SponsorActivationsWidget(QWidget):
    """Widget principal de ativações patrocinadas"""
    
    activation_selected = pyqtSignal(object)
    evidence_added = pyqtSignal(int, int)  # activation_id, evidence_id
    activation_updated = pyqtSignal(int)
    
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setup_ui()
        
        # Conectar sinais do controlador
        self.controller.activation_created.connect(self.refresh_activations)
        self.controller.activation_updated.connect(self.refresh_activations)
        self.controller.activation_deleted.connect(self.refresh_activations)
        self.controller.evidence_added.connect(self.on_evidence_added)
        self.controller.evidence_removed.connect(self.refresh_activations)
        
    def setup_ui(self):
        """Configura a interface do widget"""
        layout = QVBoxLayout(self)
        
        # Barra de ferramentas
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        # Botão de atualizar
        refresh_action = QAction(QIcon(":/icons/refresh.png"), "Atualizar", self)
        refresh_action.triggered.connect(self.refresh_activations)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # Filtros
        toolbar.addWidget(QLabel("Status:"))
        
        self.status_combo = QComboBox()
        self.status_combo.addItem("Todos")
        self.status_combo.addItem("Pendentes", "pending")
        self.status_combo.addItem("Em andamento", "in_progress")
        self.status_combo.addItem("Concluídos", "completed")
        self.status_combo.addItem("Cancelados", "canceled")
        self.status_combo.currentIndexChanged.connect(self.apply_filter)
        toolbar.addWidget(self.status_combo)
        
        toolbar.addSeparator()
        
        # Patrocinadores
        toolbar.addWidget(QLabel("Patrocinador:"))
        
        self.sponsor_combo = QComboBox()
        self.sponsor_combo.addItem("Todos")
        self.sponsor_combo.currentIndexChanged.connect(self.apply_filter)
        toolbar.addWidget(self.sponsor_combo)
        
        toolbar.addSeparator()
        
        # Campo de busca
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar ativações...")
        self.search_edit.setMinimumWidth(200)
        self.search_edit.textChanged.connect(self.apply_search)
        toolbar.addWidget(self.search_edit)
        
        toolbar.addSeparator()
        
        # Botões de ação
        add_action = QAction(QIcon(":/icons/add.png"), "Nova Ativação", self)
        add_action.triggered.connect(self.on_add_activation)
        toolbar.addAction(add_action)
        
        edit_action = QAction(QIcon(":/icons/edit.png"), "Editar", self)
        edit_action.triggered.connect(self.on_edit_activation)
        toolbar.addAction(edit_action)
        
        delete_action = QAction(QIcon(":/icons/delete.png"), "Excluir", self)
        delete_action.triggered.connect(self.on_delete_activation)
        toolbar.addAction(delete_action)
        
        toolbar.addSeparator()
        
        # Menu de opções
        options_button = QToolButton()
        options_button.setIcon(QIcon(":/icons/settings.png"))
        options_button.setPopupMode(QToolButton.InstantPopup)
        
        options_menu = QMenu(options_button)
        options_menu.addAction("Exportar Lista", self.on_export_list)
        options_menu.addAction("Relatório de Ativações", self.on_generate_report)
        options_button.setMenu(options_menu)
        
        toolbar.addWidget(options_button)
        
        layout.addWidget(toolbar)
        
        # Tabela de ativações
        self.table_model = SponsorActivationTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.table_model)
        
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        
        # Configurar delegados para colunas específicas
        self.table_view.setItemDelegateForColumn(6, SponsorActivationStatusDelegate())
        self.table_view.setItemDelegateForColumn(7, EvidenceCountDelegate())
        
        # Ajustar colunas
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Patrocinador
        self.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Nome
        self.table_view.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Data
        self.table_view.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # Local
        self.table_view.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)  # Responsável
        self.table_view.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Status
        self.table_view.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Evidências
        self.table_view.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Atualização
        
        # Conectar sinal de duplo clique
        self.table_view.doubleClicked.connect(self.on_activation_double_clicked)
        
        layout.addWidget(self.table_view)
        
        # Barra de evidências
        evidence_bar = QToolBar()
        evidence_bar.setIconSize(QSize(16, 16))
        
        evidence_bar.addWidget(QLabel("Evidências:"))
        
        add_evidence_action = QAction(QIcon(":/icons/photo.png"), "Adicionar Foto/Vídeo", self)
        add_evidence_action.triggered.connect(self.on_add_photo)
        evidence_bar.addAction(add_evidence_action)
        
        add_document_action = QAction(QIcon(":/icons/document.png"), "Adicionar Documento", self)
        add_document_action.triggered.connect(self.on_add_document)
        evidence_bar.addAction(add_document_action)
        
        view_evidence_action = QAction(QIcon(":/icons/gallery.png"), "Ver Galeria", self)
        view_evidence_action.triggered.connect(self.on_view_gallery)
        evidence_bar.addAction(view_evidence_action)
        
        layout.addWidget(evidence_bar)
        
    def refresh_activations(self):
        """Atualiza a lista de ativações"""
        # Carregar ativações do controlador
        activations = self.controller.load_activations(
            self.controller.current_event_id, 
            self.controller.current_filters
        )
        
        # Obter contagem de evidências
        evidence_counts = self.controller.get_evidence_counts([act.id for act in activations])
        
        # Atualizar modelo da tabela
        self.table_model.set_data(activations, evidence_counts)
        
        # Atualizar combo de patrocinadores (apenas no primeiro carregamento)
        if self.sponsor_combo.count() <= 1:
            self.update_sponsor_combo()
            
    def update_sponsor_combo(self):
        """Atualiza o combo de patrocinadores"""
        current_event_id = self.controller.current_event_id
        if not current_event_id:
            return
            
        # Limpar combo, mantendo apenas "Todos"
        while self.sponsor_combo.count() > 1:
            self.sponsor_combo.removeItem(1)
            
        # Obter patrocinadores deste evento
        sponsors = self.controller.db.query(Sponsor).join(
            SponsorActivation, Sponsor.id == SponsorActivation.sponsor_id
        ).filter(
            SponsorActivation.event_id == current_event_id
        ).distinct().all()
        
        # Adicionar ao combo
        for sponsor in sponsors:
            self.sponsor_combo.addItem(sponsor.name, sponsor.id)
            
    def apply_filter(self, index=None):
        """Aplica filtros na lista de ativações"""
        filters = {}
        
        # Filtro de status
        if self.status_combo.currentIndex() > 0:
            status = self.status_combo.currentData()
            filters["status"] = status
            
        # Filtro de patrocinador
        if self.sponsor_combo.currentIndex() > 0:
            sponsor_id = self.sponsor_combo.currentData()
            filters["sponsor_id"] = sponsor_id
            
        # Manter filtro de texto se existir
        if hasattr(self, 'current_search_text') and self.current_search_text:
            filters["search_text"] = self.current_search_text
            
        # Aplicar filtros
        self.controller.current_filters = filters
        self.refresh_activations()
        
    def apply_search(self, text):
        """Aplica filtro de texto de busca"""
        if len(text) >= 3 or text == "":
            self.current_search_text = text if text else None
            
            filters = self.controller.current_filters.copy()
            if text:
                filters["search_text"] = text
            else:
                filters.pop("search_text", None)
                
            self.controller.current_filters = filters
            self.refresh_activations()
            
    def get_selected_activation(self):
        """Retorna a ativação selecionada ou None"""
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            return None
            
        # Obter índice no modelo original (sem proxy)
        proxy_index = indexes[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        
        # Obter ativação
        if source_index.row() < len(self.table_model.activations):
            return self.table_model.activations[source_index.row()]
            
        return None
        
    def on_activation_double_clicked(self, index):
        """Manipulador de duplo clique em ativação"""
        activation = self.get_selected_activation()
        if activation:
            self.activation_selected.emit(activation)
            
    def on_add_activation(self):
        """Abre diálogo para adicionar nova ativação"""
        # Implementar diálogo de criação de ativação
        pass
        
    def on_edit_activation(self):
        """Abre diálogo para editar ativação selecionada"""
        activation = self.get_selected_activation()
        if not activation:
            QMessageBox.warning(self, "Aviso", "Selecione uma ativação para editar")
            return
            
        # Implementar diálogo de edição de ativação
        pass
        
    def on_delete_activation(self):
        """Exclui a ativação selecionada após confirmação"""
        activation = self.get_selected_activation()
        if not activation:
            QMessageBox.warning(self, "Aviso", "Selecione uma ativação para excluir")
            return
            
        # Confirmar exclusão
        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente excluir a ativação '{activation.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.controller.delete_activation(activation.id)
            if not success:
                QMessageBox.critical(self, "Erro", "Não foi possível excluir a ativação")
                
    def on_add_photo(self):
        """Abre diálogo para adicionar foto/vídeo como evidência"""
        activation = self.get_selected_activation()
        if not activation:
            QMessageBox.warning(self, "Aviso", "Selecione uma ativação para adicionar evidência")
            return
            
        # Abrir seletor de arquivo
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Foto ou Vídeo",
            "",
            "Imagens/Vídeos (*.jpg *.jpeg *.png *.gif *.mp4 *.mov *.avi)"
        )
        
        if not file_path:
            return
            
        # Abrir diálogo para descrição e confirmação
        dialog = EvidenceDialog(activation, file_path, self)
        if dialog.exec_():
            description = dialog.get_description()
            type_id = 1 if os.path.splitext(file_path)[1].lower() in ['.jpg', '.jpeg', '.png', '.gif'] else 2
            
            # Adicionar evidência
            evidence = self.controller.add_evidence(
                activation.id, 
                file_path, 
                description, 
                type_id
            )
            
            if evidence:
                self.evidence_added.emit(activation.id, evidence.id)
                
    def on_add_document(self):
        """Abre diálogo para adicionar documento como evidência"""
        activation = self.get_selected_activation()
        if not activation:
            QMessageBox.warning(self, "Aviso", "Selecione uma ativação para adicionar documento")
            return
            
        # Abrir seletor de arquivo
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Documento",
            "",
            "Documentos (*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx)"
        )
        
        if not file_path:
            return
            
        # Abrir diálogo para descrição e confirmação
        dialog = EvidenceDialog(activation, file_path, self)
        if dialog.exec_():
            description = dialog.get_description()
            
            # Adicionar evidência
            evidence = self.controller.add_evidence(
                activation.id, 
                file_path, 
                description, 
                3  # Tipo documento
            )
            
            if evidence:
                self.evidence_added.emit(activation.id, evidence.id)
                
    def on_view_gallery(self):
        """Abre galeria de evidências da ativação selecionada"""
        activation = self.get_selected_activation()
        if not activation:
            QMessageBox.warning(self, "Aviso", "Selecione uma ativação para ver evidências")
            return
            
        # Implementar diálogo de galeria de evidências
        pass
        
    def on_evidence_added(self, activation_id, evidence_id):
        """Atualiza após adição de evidência"""
        self.refresh_activations()
        
    def on_export_list(self):
        """Exporta a lista de ativações para Excel ou PDF"""
        # Implementar exportação
        pass
        
    def on_generate_report(self):
        """Gera relatório completo de ativações"""
        # Implementar geração de relatório
        pass
