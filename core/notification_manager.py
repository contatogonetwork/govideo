#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Gerenciador de Notificações
Data: 2025-05-15
"""

import time
import logging
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class NotificationManager(QObject):
    """
    Gerencia as notificações do sistema, servindo como ponto central para criação,
    armazenamento e distribuição de notificações para diferentes componentes.
    """
    
    # Sinais
    notification_added = pyqtSignal(dict)  # Nova notificação adicionada
    notification_removed = pyqtSignal(dict)  # Notificação removida
    notification_updated = pyqtSignal(dict)  # Notificação atualizada
    
    def __init__(self, max_size=100):
        """
        Inicializa o gerenciador de notificações
        
        Args:
            max_size (int): Número máximo de notificações a manter em memória
        """
        super().__init__()
        self.max_size = max_size
        self.notifications = []
        
    def add_notification(self, title, message, level=0, type_="system", data=None):
        """
        Adiciona uma nova notificação
        
        Args:
            title (str): Título da notificação
            message (str): Mensagem detalhada
            level (int): Nível da notificação (0=info, 1=warning, 2=error)
            type_ (str): Tipo da notificação (system, delivery, activation, etc)
            data (dict): Dados adicionais para ação contextual (opcional)
            
        Returns:
            dict: A notificação criada
        """
        notification = {
            "id": self._generate_id(),
            "title": title,
            "message": message,
            "level": level,
            "type": type_,
            "timestamp": time.time(),
            "read": False
        }
        
        if data:
            notification["data"] = data
            
        # Adicionar à lista
        self.notifications.append(notification)
        
        # Limitar tamanho da lista
        if len(self.notifications) > self.max_size:
            removed = self.notifications.pop(0)
            self.notification_removed.emit(removed)
            
        # Emitir sinal de nova notificação
        self.notification_added.emit(notification)
        
        # Registrar no log
        log_methods = {
            0: logger.info,
            1: logger.warning,
            2: logger.error
        }
        log_methods.get(level, logger.info)(f"Notificação: {title} - {message}")
        
        return notification
        
    def remove_notification(self, notification_id):
        """
        Remove uma notificação por ID
        
        Args:
            notification_id (str): ID da notificação
            
        Returns:
            bool: True se foi removida, False se não encontrada
        """
        for notification in self.notifications:
            if notification["id"] == notification_id:
                self.notifications.remove(notification)
                self.notification_removed.emit(notification)
                return True
                
        return False
        
    def mark_as_read(self, notification_id):
        """
        Marca uma notificação como lida
        
        Args:
            notification_id (str): ID da notificação
            
        Returns:
            bool: True se foi atualizada, False se não encontrada
        """
        for notification in self.notifications:
            if notification["id"] == notification_id and not notification["read"]:
                notification["read"] = True
                self.notification_updated.emit(notification)
                return True
                
        return False
        
    def mark_all_as_read(self):
        """Marca todas as notificações como lidas"""
        updated = False
        for notification in self.notifications:
            if not notification["read"]:
                notification["read"] = True
                self.notification_updated.emit(notification)
                updated = True
                
        return updated
        
    def clear_all(self):
        """Remove todas as notificações"""
        old_notifications = self.notifications.copy()
        self.notifications = []
        
        for notification in old_notifications:
            self.notification_removed.emit(notification)
            
    def get_unread_count(self):
        """Retorna o número de notificações não lidas"""
        return sum(1 for n in self.notifications if not n.get("read", False))
        
    def get_all_notifications(self):
        """Retorna todas as notificações"""
        return self.notifications.copy()
        
    def get_notification(self, notification_id):
        """Retorna uma notificação específica por ID"""
        for notification in self.notifications:
            if notification["id"] == notification_id:
                return notification
        return None
        
    def _generate_id(self):
        """Gera um ID único para a notificação"""
        return str(int(time.time() * 1000))  # Timestamp em milissegundos
