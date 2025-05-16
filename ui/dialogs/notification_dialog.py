#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Diálogo para notificações do sistema
Data: 2025-05-15
"""

import os
import time
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QWidget, QFrame
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QColor, QPalette

class NotificationItem(QFrame):
    """Item individual de notificação"""
    
    clicked = pyqtSignal(object)
    dismissed = pyqtSignal(object)
    
    def __init__(self, notification_data, parent=None):
        super().__init__(parent)
        self.notification_data = notification_data
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do item de notificação"""
        layout = QHBoxLayout(self)
        
        # Ícone baseado no tipo
        icon_name = "info"
        if self.notification_data.get("level", 0) == 1:
            icon_name = "warning"
        elif self.notification_data.get("level", 0) == 2:
            icon_name = "error"
        elif self.notification_data.get("type") == "delivery":
            icon_name = "delivery"
        elif self.notification_data.get("type") == "activation":
            icon_name = "activity"
            
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(f":/icons/{icon_name}.png").pixmap(24, 24))
        layout.addWidget(icon_label)
        
        # Conteúdo
        content = QVBoxLayout()
        
        title = QLabel(self.notification_data.get("title", "Notificação"))
        title.setStyleSheet("font-weight: bold;")
        content.addWidget(title)
        
        message = QLabel(self.notification_data.get("message", ""))
        message.setWordWrap(True)
        content.addWidget(message)
        
        # Timestamp
        if "timestamp" in self.notification_data:
            timestamp = self._format_timestamp(self.notification_data["timestamp"])
            time_label = QLabel(timestamp)
            time_label.setStyleSheet("color: gray; font-size: 10px;")
            content.addWidget(time_label)
        
        layout.addLayout(content, stretch=1)
        
        # Botão de fechar
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { border: none; border-radius: 12px; }")
        close_btn.clicked.connect(self._on_dismiss)
        layout.addWidget(close_btn)
        
        # Estilo do frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            NotificationItem {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            NotificationItem:hover {
                background-color: #f5f5f5;
                border-color: #d0d0d0;
            }
        """)
        
    def _format_timestamp(self, timestamp):
        """Formata o timestamp para exibição"""
        # Timestamp pode ser segundos desde epoch ou string ISO
        if isinstance(timestamp, (int, float)):
            time_diff = time.time() - timestamp
            
            if time_diff < 60:
                return "Agora mesmo"
            elif time_diff < 3600:
                minutes = int(time_diff / 60)
                return f"Há {minutes} minutos"
            elif time_diff < 86400:
                hours = int(time_diff / 3600)
                return f"Há {hours} horas"
            else:
                days = int(time_diff / 86400)
                return f"Há {days} dias"
        else:
            return str(timestamp)
            
    def _on_dismiss(self):
        """Manipulador do botão de fechar"""
        self.dismissed.emit(self.notification_data)
        
    def mouseReleaseEvent(self, event):
        """Evento de clique no item"""
        super().mouseReleaseEvent(event)
        self.clicked.emit(self.notification_data)


class NotificationDialog(QDialog):
    """Diálogo de notificações do sistema"""
    
    notification_clicked = pyqtSignal(object)
    notification_dismissed = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notificações")
        self.setMinimumWidth(400)
        self.setup_ui()
        self.notifications = []
        
    def setup_ui(self):
        """Configura a interface do diálogo"""
        layout = QVBoxLayout(self)
        
        # Cabeçalho
        header = QHBoxLayout()
        title = QLabel("Notificações")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        
        # Botão para limpar todas
        clear_all = QPushButton("Limpar Tudo")
        clear_all.clicked.connect(self.clear_all_notifications)
        header.addWidget(clear_all)
        
        layout.addLayout(header)
        
        # Lista de notificações
        self.notif_list = QListWidget()
        self.notif_list.setSelectionMode(QListWidget.NoSelection)
        self.notif_list.setFocusPolicy(Qt.NoFocus)
        self.notif_list.setStyleSheet("QListWidget { border: none; background-color: transparent; }")
        layout.addWidget(self.notif_list)
        
        # Label para quando não há notificações
        self.empty_label = QLabel("Nenhuma notificação no momento")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: gray; margin: 20px;")
        layout.addWidget(self.empty_label)
        
        # Botão para fechar o diálogo
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
    def add_notification(self, notification_data):
        """
        Adiciona uma notificação à lista
        
        Args:
            notification_data (dict): Dados da notificação
                - title: Título da notificação
                - message: Mensagem
                - level: Nível (0=info, 1=warning, 2=error)
                - timestamp: Timestamp (opcional)
                - type: Tipo de notificação (opcional)
                - data: Dados extras (opcional)
        """
        # Garantir timestamp
        if "timestamp" not in notification_data:
            notification_data["timestamp"] = time.time()
            
        # Adicionar à lista
        self.notifications.append(notification_data)
        
        # Criar item na lista
        item = QListWidgetItem(self.notif_list)
        notification_widget = NotificationItem(notification_data)
        notification_widget.clicked.connect(self._on_notification_clicked)
        notification_widget.dismissed.connect(self._on_notification_dismissed)
        
        item.setSizeHint(notification_widget.sizeHint())
        self.notif_list.addItem(item)
        self.notif_list.setItemWidget(item, notification_widget)
        
        # Atualizar visibilidade do label vazio
        self.empty_label.setVisible(self.notif_list.count() == 0)
        
    def clear_all_notifications(self):
        """Limpa todas as notificações"""
        self.notif_list.clear()
        self.notifications = []
        self.empty_label.setVisible(True)
        
    def _on_notification_clicked(self, notification_data):
        """Manipulador de clique em notificação"""
        self.notification_clicked.emit(notification_data)
        
    def _on_notification_dismissed(self, notification_data):
        """Manipulador de dismiss de notificação"""
        # Encontrar o item na lista
        for i in range(self.notif_list.count()):
            item = self.notif_list.item(i)
            widget = self.notif_list.itemWidget(item)
            if widget.notification_data == notification_data:
                # Remover da lista
                self.notif_list.takeItem(i)
                
                # Remover da lista interna
                if notification_data in self.notifications:
                    self.notifications.remove(notification_data)
                
                break
        
        # Atualizar visibilidade do label vazio
        self.empty_label.setVisible(self.notif_list.count() == 0)
        
        # Emitir sinal
        self.notification_dismissed.emit(notification_data)
