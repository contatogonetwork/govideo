#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Modelo de dados para Kanban de Entregas
Data: 2025-05-15
"""

from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex, pyqtSignal, QObject, QMimeData
from PyQt5.QtGui import QBrush, QColor

from models.delivery import Delivery

class KanbanBoardModel(QAbstractItemModel):
    """Modelo para Kanban baseado em QAbstractItemModel para performance"""
    
    # Papéis personalizados
    DeliveryIDRole = Qt.UserRole + 1
    DeliveryObjectRole = Qt.UserRole + 2
    
    # Sinais
    data_changed = pyqtSignal()
    
    def __init__(self, session, parent=None):
        """
        Inicializa o modelo de Kanban
        
        Args:
            session: Sessão SQLAlchemy
            parent: Widget pai (opcional)
        """
        super().__init__(parent)
        self.session = session
        self.columns = ["pending", "editing", "reviewing", "completed"]
        self.column_names = {
            "pending": "Pendente",
            "editing": "Em Edição",
            "reviewing": "Em Revisão",
            "completed": "Concluído"
        }
        self.cards = {col: [] for col in self.columns}
        
    def load_data(self):
        """Carrega dados do banco de dados"""
        self.beginResetModel()
        
        # Reset do modelo
        self.cards = {col: [] for col in self.columns}
        
        # Carregar entregas
        deliveries = self.session.query(Delivery).all()
        for delivery in deliveries:
            column = self._map_status_to_column(delivery.status)
            self.cards[column].append(delivery)
            
        self.endResetModel()
        self.data_changed.emit()
    
    def _map_status_to_column(self, status):
        """
        Mapeia status do banco para coluna do Kanban
        
        Args:
            status (str): Status da entrega
            
        Returns:
            str: Nome da coluna correspondente
        """
        mapping = {
            "pending": "pending",
            "in_progress": "editing",
            "review": "reviewing",
            "approved": "completed",
            "published": "completed"
        }
        return mapping.get(status, "pending")
    
    def index(self, row, column, parent=QModelIndex()):
        """Implementação obrigatória do QAbstractItemModel"""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
            
        col_name = self.columns[column] if 0 <= column < len(self.columns) else "pending"
        col_cards = self.cards[col_name]
        
        if 0 <= row < len(col_cards):
            return self.createIndex(row, column, col_cards[row])
            
        return QModelIndex()
    
    def parent(self, index):
        """Implementação obrigatória do QAbstractItemModel"""
        return QModelIndex()  # No parent-child relationship
    
    def rowCount(self, parent=QModelIndex()):
        """Retorna o número máximo de linhas (máximo entre todas as colunas)"""
        if parent.isValid():
            return 0
        
        max_rows = 0
        for col in self.columns:
            max_rows = max(max_rows, len(self.cards[col]))
            
        return max_rows
    
    def columnCount(self, parent=QModelIndex()):
        """Retorna o número de colunas no modelo"""
        return len(self.columns)
    
    def data(self, index, role=Qt.DisplayRole):
        """Retorna dados para o índice e papel específicos"""
        if not index.isValid():
            return None
            
        col = index.column()
        if col < 0 or col >= len(self.columns):
            return None
            
        col_name = self.columns[col]
        col_cards = self.cards[col_name]
        row = index.row()
        
        if row < 0 or row >= len(col_cards):
            return None
            
        delivery = col_cards[row]
        
        if role == Qt.DisplayRole:
            return delivery.title
        elif role == self.DeliveryIDRole:
            return delivery.id
        elif role == self.DeliveryObjectRole:
            return delivery
        elif role == Qt.BackgroundRole:
            # Cor de fundo baseada na prioridade
            if delivery.priority == 4:  # Urgente
                return QBrush(QColor(255, 87, 34, 50))  # Vermelho transparente
            elif delivery.priority == 3:  # Alta
                return QBrush(QColor(255, 193, 7, 50))  # Amarelo transparente
            elif delivery.priority == 2:  # Média
                return QBrush(QColor(76, 175, 80, 50))  # Verde transparente
            else:  # Baixa
                return QBrush(QColor(33, 150, 243, 50))  # Azul transparente
            
        return None
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Retorna dados do cabeçalho"""
        if role != Qt.DisplayRole:
            return None
            
        if orientation == Qt.Horizontal and 0 <= section < len(self.columns):
            col_name = self.columns[section]
            return self.column_names.get(col_name, col_name.capitalize())
            
        return str(section + 1)
    
    def flags(self, index):
        """Retorna flags para o índice específico"""
        default_flags = super().flags(index)
        
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
            
        return default_flags | Qt.ItemIsDropEnabled
    
    def supportedDropActions(self):
        """Define as ações de drop suportadas"""
        return Qt.MoveAction
    
    def mimeTypes(self):
        """Retorna os tipos MIME suportados"""
        return ["application/x-deliverycard"]
    
    def mimeData(self, indexes):
        """Cria dados MIME para os índices selecionados"""
        if not indexes:
            return None
            
        mime_data = QMimeData()
        encoded_data = str(indexes[0].data(self.DeliveryIDRole)).encode()
        mime_data.setData("application/x-deliverycard", encoded_data)
        return mime_data
    
    def canDropMimeData(self, data, action, row, column, parent):
        """Verifica se os dados MIME podem ser soltos nesta posição"""
        if not data.hasFormat("application/x-deliverycard"):
            return False
            
        if column < 0 or column >= len(self.columns):
            return False
            
        return True
    
    def dropMimeData(self, data, action, row, column, parent):
        """Processa a soltura dos dados MIME"""
        if not self.canDropMimeData(data, action, row, column, parent):
            return False
            
        if action == Qt.IgnoreAction:
            return True
            
        # Decodificar ID da entrega
        delivery_id = int(data.data("application/x-deliverycard").data().decode())
        
        # Identificar coluna de destino
        target_column = self.columns[column]
        
        # Emitir sinal para o controlador realizar a movimentação
        # Este modelo não faz a movimentação diretamente
        
        return True
        
    def get_column_for_delivery(self, delivery_id):
        """
        Retorna a coluna onde uma entrega está localizada
        
        Args:
            delivery_id (int): ID da entrega
            
        Returns:
            str or None: Nome da coluna ou None se não encontrada
        """
        for col_name, col_cards in self.cards.items():
            for card in col_cards:
                if card.id == delivery_id:
                    return col_name
        return None
