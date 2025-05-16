#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Modelo para visualização de linha do tempo (Timeline)
Data: 2025-05-15
Autor: GONETWORK AI
"""

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, QDate, QDateTime
from PyQt5.QtGui import QColor, QBrush, QFont
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TimelineItem:
    """Classe que representa um item na linha do tempo"""
    
    def __init__(self, item_id, title, start_time, end_time, item_type, color=None, data=None):
        self.item_id = item_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.item_type = item_type  # 'activity', 'delivery', 'assignment', etc.
        self.color = color or self._default_color_for_type(item_type)
        self.data = data or {}  # Dados adicionais para o item
        
    def _default_color_for_type(self, item_type):
        """Retorna uma cor padrão com base no tipo do item"""
        colors = {
            'activity': QColor(100, 149, 237),    # CornflowerBlue
            'delivery': QColor(255, 165, 0),      # Orange
            'assignment': QColor(60, 179, 113),   # MediumSeaGreen
            'activation': QColor(219, 112, 147),  # PaleVioletRed
            'event': QColor(138, 43, 226),        # BlueViolet
        }
        return colors.get(item_type, QColor(200, 200, 200))  # Cinza para tipos desconhecidos
        
    def overlaps(self, other_item):
        """Verifica se este item se sobrepõe a outro item no tempo"""
        return (self.start_time <= other_item.end_time and 
                self.end_time >= other_item.start_time)
                
    def duration_minutes(self):
        """Retorna a duração do item em minutos"""
        if not self.end_time or not self.start_time:
            return 60  # Valor padrão se não houver horário de término
        
        delta = self.end_time - self.start_time
        return max(30, delta.total_seconds() / 60)  # No mínimo 30 minutos


class TimelineModel(QAbstractTableModel):
    """Modelo para exibição da linha do tempo em formato de tabela"""
    
    # Papéis personalizados para exibir os dados
    ItemRole = Qt.UserRole + 1
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timeline_items = []  # Lista de TimelineItem
        self.rows = []            # Linhas organizadas do layout (cada item vai para uma linha onde não há sobreposição)
        self.date_range = []      # Lista de datas no intervalo selecionado
        self.start_date = None    # Data de início
        self.end_date = None      # Data de término
        self.interval = 60        # Intervalo em minutos (1 hora é o padrão)
        self.row_height = 40      # Altura das linhas em pixels
        self.item_types = {}      # Dicionário mapeando tipos para mostrar/esconder
        self.filtered_keyword = ""  # Palavra-chave para filtrar itens
        
    def set_date_range(self, start_date, end_date=None, interval_minutes=60):
        """Define o intervalo de datas para exibição
        
        Args:
            start_date: Data de início 
            end_date: Data de término (se None, será 1 dia após start_date)
            interval_minutes: Intervalo em minutos para as colunas
        """
        self.start_date = start_date
        self.end_date = end_date or start_date + timedelta(days=1)
        self.interval = interval_minutes
        
        # Gerar intervalo de datas
        self._generate_date_range()
        
        # Reorganizar os itens
        self._organize_items()
        
    def set_items(self, items):
        """Define os itens da linha do tempo
        
        Args:
            items: Lista de TimelineItem
        """
        self.beginResetModel()
        self.timeline_items = items
        
        # Extrair tipos de itens únicos
        self.item_types = {}
        for item in items:
            if item.item_type not in self.item_types:
                self.item_types[item.item_type] = True  # Por padrão, todos os tipos estão visíveis
                
        # Organizar itens
        self._organize_items()
        self.endResetModel()
        
    def _generate_date_range(self):
        """Gera o intervalo de datas para as colunas"""
        if not self.start_date or not self.end_date:
            self.date_range = []
            return
            
        current_time = datetime.combine(self.start_date, datetime.min.time())
        end_time = datetime.combine(self.end_date, datetime.max.time())
        
        self.date_range = []
        
        while current_time <= end_time:
            self.date_range.append(current_time)
            current_time += timedelta(minutes=self.interval)
            
    def _organize_items(self):
        """Organiza os itens em linhas sem sobreposição"""
        if not self.timeline_items or not self.date_range:
            self.rows = []
            return
            
        # Filtrar itens por tipo e palavra-chave
        filtered_items = [item for item in self.timeline_items if self._item_passes_filter(item)]
        
        # Ordenar por horário de início
        sorted_items = sorted(filtered_items, key=lambda x: x.start_time)
        
        self.rows = []
        
        # Distribuir cada item em uma linha onde não há sobreposição
        for item in sorted_items:
            # Verificar se o item está dentro do intervalo de datas
            if item.end_time < self.date_range[0] or item.start_time > self.date_range[-1]:
                continue
                
            # Encontrar uma linha existente onde o item pode ser colocado sem sobreposição
            placed = False
            
            for row_idx, row_items in enumerate(self.rows):
                # Verificar se o item se sobrepõe a algum item na linha
                overlaps = False
                for row_item in row_items:
                    if item.overlaps(row_item):
                        overlaps = True
                        break
                        
                if not overlaps:
                    # Se não há sobreposição, adicionar o item a esta linha
                    self.rows[row_idx].append(item)
                    placed = True
                    break
                    
            if not placed:
                # Se não encontrou uma linha apropriada, criar uma nova
                self.rows.append([item])
                
        # Notificar a mudança
        self.modelReset.emit()
        
    def _item_passes_filter(self, item):
        """Verifica se o item passa pelos filtros ativos
        
        Args:
            item: TimelineItem a ser verificado
            
        Returns:
            bool: True se o item passa pelos filtros
        """
        # Verificar se o tipo do item está visível
        if item.item_type in self.item_types and not self.item_types[item.item_type]:
            return False
            
        # Verificar se o item contém a palavra-chave
        if self.filtered_keyword:
            keyword = self.filtered_keyword.lower()
            if keyword not in item.title.lower():
                # Verificar dados adicionais
                found = False
                for value in item.data.values():
                    if isinstance(value, str) and keyword in value.lower():
                        found = True
                        break
                if not found:
                    return False
                    
        return True
        
    def set_type_visibility(self, item_type, visible):
        """Define a visibilidade de um tipo de item
        
        Args:
            item_type: Tipo do item
            visible: True para mostrar, False para esconder
        """
        if item_type in self.item_types and self.item_types[item_type] != visible:
            self.item_types[item_type] = visible
            self._organize_items()
            
    def set_keyword_filter(self, keyword):
        """Define a palavra-chave para filtrar os itens
        
        Args:
            keyword: Palavra-chave para filtrar
        """
        if self.filtered_keyword != keyword:
            self.filtered_keyword = keyword
            self._organize_items()
            
    def rowCount(self, parent=QModelIndex()):
        """Retorna o número de linhas no modelo"""
        if parent.isValid():
            return 0
        return len(self.rows)
        
    def columnCount(self, parent=QModelIndex()):
        """Retorna o número de colunas no modelo"""
        if parent.isValid():
            return 0
        return len(self.date_range)
        
    def data(self, index, role=Qt.DisplayRole):
        """Retorna os dados para um índice específico com um papel específico"""
        if not index.isValid() or not (0 <= index.row() < len(self.rows)):
            return QVariant()
            
        row_items = self.rows[index.row()]
        col_time = self.date_range[index.column()]
        
        # Encontrar itens que incluem este horário
        for item in row_items:
            # Verificar se o horário da coluna está dentro do intervalo do item
            if item.start_time <= col_time <= item.end_time:
                # Este item abrange esta célula
                
                # Para o papel de exibição, retornar o título apenas na primeira célula do item
                if role == Qt.DisplayRole:
                    # Verificar se esta é a primeira célula do item
                    first_col = self._find_item_first_column(item)
                    if index.column() == first_col:
                        return item.title
                    return ""
                    
                elif role == Qt.BackgroundRole:
                    return item.color
                    
                elif role == Qt.TextAlignmentRole:
                    return Qt.AlignLeft | Qt.AlignVCenter
                    
                elif role == Qt.ToolTipRole:
                    tooltip = f"{item.title}\n"
                    tooltip += f"Início: {item.start_time.strftime('%d/%m/%Y %H:%M')}\n"
                    tooltip += f"Fim: {item.end_time.strftime('%d/%m/%Y %H:%M')}\n"
                    tooltip += f"Tipo: {item.item_type.capitalize()}"
                    
                    # Adicionar dados específicos dependendo do tipo
                    if item.item_type == 'activity' and 'location' in item.data:
                        tooltip += f"\nLocal: {item.data['location']}"
                    elif item.item_type == 'delivery' and 'status' in item.data:
                        tooltip += f"\nStatus: {item.data['status']}"
                        
                    return tooltip
                    
                elif role == TimelineModel.ItemRole:
                    return item
                    
        # Nenhum item encontrado para esta célula
        if role == Qt.BackgroundRole:
            # Estilo para células vazias
            if col_time.hour < 8 or col_time.hour > 20:
                # Horário fora do comercial
                return QBrush(QColor(245, 245, 245))
            else:
                return QBrush(Qt.white)
                
        return QVariant()
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Retorna os dados de cabeçalho"""
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal and 0 <= section < len(self.date_range):
                # Mostrar horário para o cabeçalho horizontal
                time_str = self.date_range[section].strftime("%H:%M")
                
                # Adicionar data se for a primeira coluna do dia ou a primeira coluna
                if section == 0 or self.date_range[section].day != self.date_range[section-1].day:
                    date_str = self.date_range[section].strftime("%d/%m")
                    return f"{date_str}\n{time_str}"
                    
                return time_str
                
            elif orientation == Qt.Vertical and 0 <= section < len(self.rows):
                # Apenas mostrar número da linha para o cabeçalho vertical
                return str(section + 1)
                
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
            
        elif role == Qt.BackgroundRole:
            if orientation == Qt.Horizontal and 0 <= section < len(self.date_range):
                # Destacar fim de semana
                weekday = self.date_range[section].weekday()
                if weekday >= 5:  # 5 = Sábado, 6 = Domingo
                    return QBrush(QColor(230, 230, 250))  # Lavanda claro
                    
        return QVariant()
        
    def _find_item_first_column(self, item):
        """Encontra a primeira coluna (índice) onde este item aparece"""
        for col_idx, col_time in enumerate(self.date_range):
            if item.start_time <= col_time:
                return col_idx
        return 0
