#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Modelo para visualização Kanban de entregas
Data: 2025-05-15
Autor: GONETWORK AI
"""

import logging
from datetime import datetime
from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex, QVariant, QMimeData
from PyQt5.QtGui import QColor

logger = logging.getLogger(__name__)

class KanbanColumn:
    """Classe que representa uma coluna do Kanban"""
    
    def __init__(self, title, status, color=None):
        self.title = title
        self.status = status  # Status correspondente no banco de dados
        self.color = color or QColor(240, 240, 240)
        self.items = []  # Lista de entregas na coluna
    
    def add_item(self, item):
        """Adiciona um item à coluna"""
        self.items.append(item)
    
    def remove_item(self, item):
        """Remove um item da coluna"""
        if item in self.items:
            self.items.remove(item)
    
    def clear(self):
        """Remove todos os itens da coluna"""
        self.items.clear()
    
    def count(self):
        """Retorna o número de itens na coluna"""
        return len(self.items)


class DeliveryKanbanModel:
    """Modelo de dados para o Kanban de entregas"""
    
    def __init__(self):
        self.columns = []
        self.setup_columns()
    
    def setup_columns(self):
        """Configura as colunas padrão do Kanban"""
        self.columns = [
            KanbanColumn("Pendente", "pending", QColor(255, 235, 156)),  # Amarelo claro
            KanbanColumn("Em Andamento", "in_progress", QColor(169, 208, 142)),  # Verde claro
            KanbanColumn("Em Revisão", "in_review", QColor(180, 199, 231)),  # Azul claro
            KanbanColumn("Aprovado", "approved", QColor(198, 224, 180)),  # Verde médio
            KanbanColumn("Entregue", "delivered", QColor(155, 187, 89))   # Verde escuro
        ]
    
    def column_count(self):
        """Retorna o número de colunas do Kanban"""
        return len(self.columns)
    
    def get_column(self, index):
        """Retorna uma coluna pelo índice"""
        if 0 <= index < len(self.columns):
            return self.columns[index]
        return None
    
    def get_column_by_status(self, status):
        """Retorna uma coluna pelo status"""
        for column in self.columns:
            if column.status == status:
                return column
        return None
    
    def clear_all(self):
        """Limpa todas as colunas"""
        for column in self.columns:
            column.clear()
    
    def move_item(self, delivery, from_column_idx, to_column_idx, to_position=None):
        """Move um item entre colunas do Kanban"""
        # Verificar índices válidos
        if not (0 <= from_column_idx < len(self.columns)) or not (0 <= to_column_idx < len(self.columns)):
            return False
        
        # Remover da coluna original
        self.columns[from_column_idx].remove_item(delivery)
        
        # Adicionar na nova coluna
        if to_position is None or to_position >= len(self.columns[to_column_idx].items):
            self.columns[to_column_idx].add_item(delivery)
        else:
            self.columns[to_column_idx].items.insert(to_position, delivery)
        
        return True


class KanbanColumnModel(QAbstractListModel):
    """Modelo para uma coluna do Kanban, usando QAbstractListModel para uma lista visualizável"""
    
    # Papéis personalizados para exibir os dados
    TitleRole = Qt.UserRole + 1
    DeadlineRole = Qt.UserRole + 2
    PriorityRole = Qt.UserRole + 3
    ResponsibleRole = Qt.UserRole + 4
    IdRole = Qt.UserRole + 5
    
    def __init__(self, kanban_column, parent=None):
        super().__init__(parent)
        self.column = kanban_column
    
    def rowCount(self, parent=QModelIndex()):
        """Retorna o número de linhas no modelo"""
        if parent.isValid():
            return 0
        return len(self.column.items)
    
    def data(self, index, role=Qt.DisplayRole):
        """Retorna os dados para um índice específico com um papel específico"""
        if not index.isValid() or not (0 <= index.row() < len(self.column.items)):
            return QVariant()
        
        item = self.column.items[index.row()]
        
        if role == Qt.DisplayRole:
            return item.title
            
        elif role == KanbanColumnModel.TitleRole:
            return item.title
            
        elif role == KanbanColumnModel.DeadlineRole:
            if item.deadline:
                return item.deadline.strftime('%d/%m/%Y')
            return "Sem prazo"
            
        elif role == KanbanColumnModel.PriorityRole:
            return item.priority
            
        elif role == KanbanColumnModel.ResponsibleRole:
            if item.responsible:
                return item.responsible.name
            return "Não atribuído"
            
        elif role == KanbanColumnModel.IdRole:
            return item.id
            
        elif role == Qt.ToolTipRole:
            tooltip = f"Título: {item.title}\n"
            tooltip += f"Prazo: {item.deadline.strftime('%d/%m/%Y') if item.deadline else 'Não definido'}\n"
            if item.responsible:
                tooltip += f"Responsável: {item.responsible.name}\n"
            if item.description:
                # Limitar descrição a 100 caracteres
                desc = item.description[:100] + "..." if len(item.description) > 100 else item.description
                tooltip += f"Descrição: {desc}"
            return tooltip
            
        elif role == Qt.BackgroundRole:
            # Cores de acordo com a prioridade
            if item.priority == 1:  # Alta
                return QColor(255, 200, 200)  # Vermelho claro
            elif item.priority == 2:  # Média
                return QColor(255, 235, 156)  # Amarelo claro
            elif item.priority == 5:  # Baixa
                return QColor(220, 220, 220)  # Cinza claro
            
            # Padrão
            return QColor(255, 255, 255)  # Branco
        
        return QVariant()
    
    def flags(self, index):
        """Retorna as flags para um índice específico"""
        if not index.isValid():
            return Qt.ItemIsDropEnabled  # Permitir soltar itens mesmo em áreas vazias
        
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
    
    def supportedDragActions(self):
        """Retorna as ações de arrastar suportadas"""
        return Qt.MoveAction
    
    def supportedDropActions(self):
        """Retorna as ações de soltar suportadas"""
        return Qt.MoveAction
    
    def mimeTypes(self):
        """Retorna os tipos MIME suportados para drag & drop"""
        return ["application/x-kanbanitem"]
    
    def mimeData(self, indexes):
        """Cria dados MIME para os índices selecionados"""
        if not indexes:
            return None
        
        mime_data = QMimeData()
        encoded_data = ""
        
        for index in indexes:
            if index.isValid():
                # Formato: ID da entrega + posição na coluna
                item_id = str(self.column.items[index.row()].id)
                encoded_data += f"{item_id},"
        
        mime_data.setData("application/x-kanbanitem", encoded_data.encode())
        return mime_data
    
    def canDropMimeData(self, data, action, row, column, parent):
        """Verifica se os dados MIME podem ser soltos aqui"""
        if not data.hasFormat("application/x-kanbanitem"):
            return False
        
        if action == Qt.IgnoreAction:
            return False
            
        return True
    
    def dropMimeData(self, data, action, row, column, parent):
        """Processa os dados MIME soltos"""
        if not self.canDropMimeData(data, action, row, column, parent):
            return False
        
        if action == Qt.IgnoreAction:
            return True
        
        # Obter os IDs das entregas no mime data
        encoded_data = data.data("application/x-kanbanitem").data().decode()
        item_ids = [int(id_str) for id_str in encoded_data.split(',') if id_str]
        
        # Posição onde soltar
        beginning_row = row
        if beginning_row < 0:
            beginning_row = self.rowCount()
        
        # Este método não faz a movimentação real, apenas retorna True para indicar que o drop foi aceito
        # A movimentação real acontecerá na view, que chamará métodos específicos para isso
        
        return True
    
    def update_items(self):
        """Notifica que os itens foram alterados"""
        self.beginResetModel()
        self.endResetModel()
