#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Modelo de dados para lista de atividades
Data: 2025-05-15
"""

import logging
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, QDateTime
from PyQt5.QtGui import QColor, QBrush

from core.database import Activity, Stage

logger = logging.getLogger(__name__)

class ActivityModel(QAbstractTableModel):
    """Modelo para exibição de atividades em QTableView"""
    
    # Papéis personalizados
    ActivityIDRole = Qt.UserRole + 1
    ActivityObjectRole = Qt.UserRole + 2
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.activities = []
        self.headers = ["Nome", "Palco/Área", "Início", "Término", "Tipo"]
        
    def load_data(self, event_id, db_session=None):
        """Carrega os dados de atividades de um evento
        
        Args:
            event_id (int): ID do evento
            db_session: Sessão do banco de dados (opcional)
        """
        if not db_session:
            logger.error("Sessão de banco de dados não fornecida")
            return
            
        try:
            # Consultar atividades do evento, ordenadas por data e hora de início
            query = db_session.query(Activity).join(Activity.stage)
            query = query.filter(Stage.event_id == event_id)
            query = query.order_by(Activity.start_time)
            
            self.activities = query.all()
            
            # Notificar view que dados foram alterados
            self.layoutChanged.emit()
            
        except Exception as e:
            logger.error(f"Erro ao carregar atividades: {str(e)}")
            self.activities = []
            
    def clear(self):
        """Limpar dados do modelo"""
        self.activities = []
        self.layoutChanged.emit()
        
    def rowCount(self, parent=QModelIndex()):
        """Retorna número de linhas no modelo
        
        Args:
            parent (QModelIndex, opcional): Índice pai (ignorado)
            
        Returns:
            int: Número de linhas (atividades)
        """
        return len(self.activities)
        
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
        if not index.isValid() or not (0 <= index.row() < len(self.activities)):
            return QVariant()
            
        activity = self.activities[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if col == 0:
                return activity.name
            elif col == 1:
                return activity.stage.name if activity.stage else ""
            elif col == 2:
                # Hora de início
                return activity.start_time.strftime('%d/%m/%Y %H:%M')
            elif col == 3:
                # Hora de término
                return activity.end_time.strftime('%d/%m/%Y %H:%M')
            elif col == 4:
                # Tipo de atividade
                type_map = {
                    "show": "Show",
                    "activation": "Ativação", 
                    "interview": "Entrevista",
                    "photo": "Sessão Foto",
                    "setup": "Setup/Montagem",
                    "other": "Outros"
                }
                return type_map.get(activity.type, activity.type or "Outros")
                
        elif role == Qt.TextAlignmentRole:
            # Centralizar colunas de data/hora e tipo
            if col in [2, 3, 4]:
                return Qt.AlignCenter
                
        elif role == Qt.BackgroundRole:
            # Cores por tipo
            if col == 4:
                type_colors = {
                    'show': QColor(41, 128, 185),      # Azul
                    'activation': QColor(39, 174, 96), # Verde
                    'interview': QColor(142, 68, 173), # Roxo
                    'photo': QColor(211, 84, 0),       # Laranja
                    'setup': QColor(127, 140, 141),    # Cinza
                    'other': QColor(44, 62, 80),       # Azul escuro
                }
                return QBrush(type_colors.get(activity.type, type_colors['other']))
                
        elif role == Qt.ForegroundRole:
            # Texto branco para coluna de tipo
            if col == 4:
                return QBrush(QColor(255, 255, 255))
                
            # Alta prioridade em negrito vermelho
            if activity.priority == 1:
                return QBrush(QColor(231, 76, 60))
                
        elif role == self.ActivityIDRole:
            # Retornar ID da atividade
            return activity.id
            
        elif role == self.ActivityObjectRole:
            # Retornar objeto completo
            return activity
            
        elif role == Qt.ToolTipRole:
            # Tooltip com detalhes da atividade
            if col == 0:  # Coluna do nome
                tooltip = f"<b>{activity.name}</b>"
                if activity.details:
                    tooltip += f"<br><br>{activity.details}"
                return tooltip
            elif col == 1:  # Coluna do palco/área
                if activity.stage and activity.stage.location:
                    return f"{activity.stage.name}<br>Local: {activity.stage.location}"
                return activity.stage.name if activity.stage else ""
            
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
            0: lambda a: a.name.lower(),                   # Nome
            1: lambda a: a.stage.name.lower() if a.stage else "",  # Palco/Área
            2: lambda a: a.start_time,                     # Início
            3: lambda a: a.end_time,                       # Término
            4: lambda a: a.type if a.type else ""          # Tipo
        }
        
        # Se coluna fora do intervalo, não ordenar
        if column < 0 or column >= len(key_funcs):
            return
            
        # Ordenar usando a função apropriada
        self.layoutAboutToBeChanged.emit()
        
        self.activities.sort(
            key=key_funcs[column],
            reverse=(order == Qt.DescendingOrder)
        )
        
        self.layoutChanged.emit()