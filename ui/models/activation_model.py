#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Modelo de dados para ativações patrocinadas
Data: 2025-05-15
Autor: GONETWORK AI
"""

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant


class ActivationModel(QAbstractTableModel):
    """Modelo para exibição de ativações patrocinadas em uma tabela"""
    
    def __init__(self, activations=None, parent=None):
        super().__init__(parent)
        self._activations = activations or []
        self._headers = ["ID", "Marca", "Atividade", "Status", "Evidência", "Observações"]
        
        # Mapeamento de status para ícones/texto
        self.status_display = {
            "pending": "⏳ Pendente",
            "filmed": "✅ Filmado",
            "failed": "❌ Falhou",
            "Planejada": "⏳ Planejada",
            "Executada": "✅ Executada",
            "Cancelada": "❌ Cancelada"
        }
    
    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._activations)
    
    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._activations)):
            return QVariant()
        
        activation = self._activations[index.row()]
        
        if role == Qt.DisplayRole:
            column = index.column()
            if column == 0:
                return activation.id
            elif column == 1:
                return activation.sponsor.name if activation.sponsor else "Desconhecido"
            elif column == 2:
                # Nova estrutura sem activity
                description = activation.description or ""
                if description.startswith("Atividade:"):
                    activity_name = description.split("\n")[0].replace("Atividade:", "").strip()
                    return activity_name
                elif description.startswith("Palco:"):
                    stage_name = description.split("\n")[0].replace("Palco:", "").strip()
                    return f"Palco: {stage_name}"
                else:
                    return "Geral"
            elif column == 3:
                # Status no novo formato é string
                return self.status_display.get(activation.status, activation.status)
            elif column == 4:
                # Evidence_path foi substituído pelo location
                return "Sim" if activation.location else "Não"
            elif column == 5:
                # Notes foi substituído por description
                desc = activation.description or ""
                # Remover as primeiras linhas que indicam atividade/palco
                lines = desc.split("\n")
                if len(lines) > 1 and (lines[0].startswith("Atividade:") or lines[0].startswith("Palco:")):
                    return "\n".join(lines[1:])
                return desc
        
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter
        
        return QVariant()
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return QVariant()
    
    def update_activations(self, activations):
        """Atualiza a lista de ativações no modelo"""
        self.beginResetModel()
        self._activations = activations
        self.endResetModel()
        
    def get_activation(self, row):
        """Retorna a ativação para uma determinada linha"""
        if 0 <= row < len(self._activations):
            return self._activations[row]
        return None
