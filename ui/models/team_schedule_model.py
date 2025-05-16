#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Modelo para visualização de escala da equipe
Data: 2025-05-15
Autor: GONETWORK AI
"""

from datetime import datetime, timedelta
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, QDate, QTime

class TeamScheduleModel(QAbstractTableModel):
    """Modelo para exibição da escala da equipe em formato de tabela/calendário"""
    
    def __init__(self, assignments=None, parent=None):
        super().__init__(parent)
        self._assignments = assignments or []
        self._team_members = []  # Lista de membros da equipe (linhas)
        self._time_slots = []    # Lista de slots de horário (colunas)
        self._data_matrix = []   # Matriz para armazenar dados [membro][horário]
        self._date = QDate.currentDate()
        
        # Status para exibição com cores
        self.status_colors = {
            "ativo": Qt.green,
            "pausa": Qt.yellow,
            "finalizado": Qt.gray,
            None: Qt.white
        }
    
    def rowCount(self, parent=QModelIndex()):
        """Retorna o número de linhas no modelo"""
        if parent.isValid():
            return 0
        return len(self._team_members)
    
    def columnCount(self, parent=QModelIndex()):
        """Retorna o número de colunas no modelo"""
        if parent.isValid():
            return 0
        return len(self._time_slots)
    
    def data(self, index, role=Qt.DisplayRole):
        """Retorna os dados para um índice específico com um papel específico"""
        if not index.isValid() or not (0 <= index.row() < len(self._team_members)):
            return QVariant()
        
        member = self._team_members[index.row()]
        time_slot = self._time_slots[index.column()]
        cell_data = self._data_matrix[index.row()][index.column()]
        
        if role == Qt.DisplayRole:
            if not cell_data:
                return ""
            
            assignment = cell_data.get("assignment")
            if assignment:
                activity_name = assignment.activity.name if assignment.activity else "Atividade"
                return f"{activity_name}\n{assignment.role_details or ''}"
            return ""
            
        elif role == Qt.BackgroundRole:
            if cell_data:
                status = cell_data.get("status")
                return self.status_colors.get(status, Qt.white)
            return Qt.white
            
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
            
        elif role == Qt.ToolTipRole:
            if cell_data:
                assignment = cell_data.get("assignment")
                if assignment and assignment.activity:
                    activity = assignment.activity
                    location = assignment.location or "Local não especificado"
                    status = assignment.status or "Sem status"
                    return (f"Atividade: {activity.name}\n"
                            f"Horário: {activity.start_time.strftime('%H:%M')} - {activity.end_time.strftime('%H:%M')}\n"
                            f"Local: {location}\n"
                            f"Status: {status}\n"
                            f"Função: {assignment.role_details or 'Não especificado'}")
            return ""
            
        elif role == Qt.UserRole:
            # Retorna os dados completos para uso personalizado
            return cell_data
        
        return QVariant()
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Retorna os dados de cabeçalho"""
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal and 0 <= section < len(self._time_slots):
                # Formato de hora para o cabeçalho horizontal
                time_slot = self._time_slots[section]
                return time_slot.toString("HH:mm")
            elif orientation == Qt.Vertical and 0 <= section < len(self._team_members):
                # Nome do membro da equipe para o cabeçalho vertical
                member = self._team_members[section]
                return f"{member.name}\n({member.role})"
        
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        
        return QVariant()
    
    def set_date(self, date):
        """Define a data para a exibição da escala"""
        if isinstance(date, QDate):
            self._date = date
        else:
            self._date = QDate(date.year, date.month, date.day)
        
        # Atualizar visualização
        self.update_data()
    
    def set_assignments(self, assignments):
        """Define as atribuições para exibição"""
        self._assignments = assignments
        self.update_data()
    
    def update_data(self):
        """Atualiza os dados do modelo com base nas atribuições e data selecionada"""
        # Limpar dados anteriores
        self.beginResetModel()
        
        # Extrair membros únicos da equipe a partir das atribuições
        member_set = set()
        for assignment in self._assignments:
            if assignment.member:
                member_set.add(assignment.member)
        
        # Ordenar membros por nome
        self._team_members = sorted(list(member_set), key=lambda m: m.name)
        
        # Criar slots de tempo para o dia selecionado (de 8:00 às 22:00 em intervalos de 30 minutos)
        self._time_slots = []
        start_hour = 8  # 8:00
        end_hour = 22   # 22:00
        interval = 30   # 30 minutos
        
        current_time = QTime(start_hour, 0)
        end_time = QTime(end_hour, 0)
        
        while current_time <= end_time:
            self._time_slots.append(current_time)
            current_time = current_time.addSecs(interval * 60)
        
        # Criar matriz de dados vazia
        self._data_matrix = [[None for _ in range(len(self._time_slots))] for _ in range(len(self._team_members))]
        
        # Preencher a matriz com as atribuições
        for assignment in self._assignments:
            # Verificar se a atribuição é para a data selecionada
            if not assignment.activity or not assignment.activity.start_time or not assignment.member:
                continue
            
            # Verificar se a data da atividade corresponde à data selecionada
            activity_date = assignment.activity.start_time.date()
            selected_date = self._date.toPyDate()
            
            if activity_date == selected_date:
                # Encontrar o índice do membro na lista
                try:
                    member_index = self._team_members.index(assignment.member)
                except ValueError:
                    continue  # Membro não está na lista
                
                # Calcular os slots de tempo da atividade
                activity_start = assignment.activity.start_time.time()
                activity_end = assignment.activity.end_time.time() if assignment.activity.end_time else activity_start
                
                # Preencher todos os slots de tempo cobertos pela atividade
                for i, time_slot in enumerate(self._time_slots):
                    slot_time = time_slot.toPyTime()
                    
                    # Verificar se o slot de tempo está dentro do intervalo da atividade
                    if activity_start <= slot_time <= activity_end:
                        self._data_matrix[member_index][i] = {
                            "assignment": assignment,
                            "status": assignment.status
                        }
        
        self.endResetModel()
    
    def get_assignment_at(self, row, column):
        """Retorna a atribuição em uma posição específica"""
        if 0 <= row < len(self._team_members) and 0 <= column < len(self._time_slots):
            cell_data = self._data_matrix[row][column]
            if cell_data:
                return cell_data.get("assignment")
        return None
