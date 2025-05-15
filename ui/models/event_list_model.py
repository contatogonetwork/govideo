#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Modelo de dados para lista de eventos
Data: 2025-05-15
"""

import logging
from datetime import datetime
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QColor, QBrush

from core.database import Event

logger = logging.getLogger(__name__)

class EventListModel(QAbstractTableModel):
    """Modelo para exibição de lista de eventos em QTableView"""
    
    # Papéis personalizados
    EventIDRole = Qt.UserRole + 1
    EventObjectRole = Qt.UserRole + 2
    
    def __init__(self, db_session, parent=None):
        """Inicializa o modelo
        
        Args:
            db_session: Sessão do banco de dados SQLAlchemy
            parent (QObject, opcional): Objeto pai
        """
        super().__init__(parent)
        self.db = db_session
        self.events = []
        self.headers = ["Nome", "Data", "Local", "Status"]
        
    def load_data(self):
        """Carrega os dados do banco de dados"""
        try:
            # Consultar eventos ordenados por data de início (mais recentes primeiro)
            self.events = self.db.query(Event).order_by(Event.start_date.desc()).all()
            
            # Notificar view que dados foram alterados
            self.layoutChanged.emit()
            
        except Exception as e:
            logger.error(f"Erro ao carregar eventos: {str(e)}")
            self.events = []
            
    def rowCount(self, parent=QModelIndex()):
        """Retorna número de linhas no modelo
        
        Args:
            parent (QModelIndex, opcional): Índice pai (ignorado)
            
        Returns:
            int: Número de linhas (eventos)
        """
        return len(self.events)
        
    def columnCount(self, parent=QModelIndex()):
        """Retorna número de colunas no modelo
        
        Args:
            parent (QModelIndex, opcional): Índice pai (ignorado)
            
        Returns:
            int: Número de colunas
        """
        return len(self.headers)
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Retorna dados de cabeçalho
        
        Args:
            section (int): Índice da seção (linha ou coluna)
            orientation (Qt.Orientation): Orientação (horizontal ou vertical)
            role (int, opcional): Papel dos dados
            
        Returns:
            QVariant: Dados do cabeçalho
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.headers[section]
                
        return QVariant()
        
    def data(self, index, role=Qt.DisplayRole):
        """Retorna dados para o índice e papel especificados
        
        Args:
            index (QModelIndex): Índice do modelo
            role (int, opcional): Papel dos dados
            
        Returns:
            QVariant: Dados para o índice/papel
        """
        if not index.isValid() or not (0 <= index.row() < len(self.events)):
            return QVariant()
            
        event = self.events[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if col == 0:
                return event.name
            elif col == 1:
                # Formatar data para exibição
                start_date = event.start_date.strftime('%d/%m/%Y')
                end_date = event.end_date.strftime('%d/%m/%Y')
                
                if start_date == end_date:
                    return start_date
                else:
                    return f"{start_date} - {end_date}"
            elif col == 2:
                return event.location or ""
            elif col == 3:
                # Traduzir status
                status_map = {
                    "planning": "Planejamento",
                    "active": "Ativo", 
                    "completed": "Concluído"
                }
                return status_map.get(event.status, event.status)
                
        elif role == Qt.TextAlignmentRole:
            # Centralizar texto nas colunas de data e status
            if col in [1, 3]:
                return Qt.AlignCenter
                
        elif role == Qt.BackgroundRole:
            # Cores por status
            if col == 3:
                if event.status == "planning":
                    return QBrush(QColor(44, 62, 80))  # Azul escuro
                elif event.status == "active":
                    return QBrush(QColor(39, 174, 96))  # Verde
                elif event.status == "completed":
                    return QBrush(QColor(127, 140, 141))  # Cinza
                    
        elif role == Qt.ForegroundRole:
            # Cor de texto para coluna de status
            if col == 3:
                return QBrush(QColor(255, 255, 255))  # Branco
                
            # Destacar eventos em andamento
            now = datetime.now()
            if event.start_date <= now <= event.end_date:
                return QBrush(QColor(52, 152, 219))  # Azul claro
                
        elif role == self.EventIDRole:
            # Retornar ID do evento
            return event.id
            
        elif role == self.EventObjectRole:
            # Retornar objeto completo do evento
            return event
            
        return QVariant()
        
    def flags(self, index):
        """Retorna flags para o índice
        
        Args:
            index (QModelIndex): Índice do modelo
            
        Returns:
            Qt.ItemFlags: Flags para o índice
        """
        if not index.isValid():
            return Qt.NoItemFlags
            
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        
    def sort(self, column, order=Qt.AscendingOrder):
        """Ordena o modelo por coluna
        
        Args:
            column (int): Índice da coluna para ordenação
            order (Qt.SortOrder): Direção da ordenação
        """
        # Definir funções de ordenação por coluna
        key_funcs = {
            0: lambda e: e.name.lower(),                   # Nome
            1: lambda e: e.start_date,                     # Data
            2: lambda e: (e.location or "").lower(),       # Local
            3: lambda e: e.status                          # Status
        }
        
        # Se coluna fora do intervalo, não ordenar
        if column < 0 or column >= len(key_funcs):
            return
            
        # Ordenar usando a função apropriada
        self.layoutAboutToBeChanged.emit()
        
        self.events.sort(
            key=key_funcs[column],
            reverse=(order == Qt.DescendingOrder)
        )
        
        self.layoutChanged.emit()