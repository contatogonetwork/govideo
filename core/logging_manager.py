"""
GONETWORK AI - Sistema de logging centralizado
"""

import os
import sys
import logging
import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, Any, Optional

class LogManager:
    """
    Gerenciador de logs centralizado para a aplicação GONETWORK AI
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """
        Singleton pattern - garante que exista apenas uma instância do LogManager
        """
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Inicializa o LogManager
        """
        if self._initialized:
            return
            
        self.loggers = {}
        self.handlers = {}
        self._initialized = True
    
    def setup(self, log_dir: str, log_level: str = "INFO", console: bool = True, 
              max_size_mb: int = 5, backup_count: int = 5) -> None:
        """
        Configura o sistema de logs
        
        Args:
            log_dir (str): Diretório para os arquivos de log
            log_level (str): Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console (bool): Se True, também exibe logs no console
            max_size_mb (int): Tamanho máximo do arquivo de log em MB
            backup_count (int): Número máximo de arquivos de backup
        """
        # Garantir que o diretório existe
        os.makedirs(log_dir, exist_ok=True)
        
        # Converter nível de log para constante
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Configurar formatador
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Arquivo de log principal
        log_file = os.path.join(log_dir, "gonetwork_ai.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        self.handlers["file"] = file_handler
        
        # Handler para console
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.handlers["console"] = console_handler
        
        # Configurar logger raiz
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        
        # Remover handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # Adicionar novos handlers
        for handler in self.handlers.values():
            root_logger.addHandler(handler)
        
        # Registrar configuração concluída
        self.get_logger(__name__).info(f"Sistema de logs configurado em {log_dir}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Obtém um logger para o módulo especificado
        
        Args:
            name (str): Nome do módulo (geralmente __name__)
            
        Returns:
            logging.Logger: Logger configurado
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        return self.loggers[name]
    
    def add_file_handler(self, name: str, log_file: str, log_level: str = "INFO") -> None:
        """
        Adiciona um handler de arquivo específico para determinado módulo
        
        Args:
            name (str): Nome do módulo
            log_file (str): Caminho do arquivo de log
            log_level (str): Nível de log
        """
        logger = self.get_logger(name)
        
        # Converter nível de log
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Criar o handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        )
        handler.setLevel(numeric_level)
        handler.setFormatter(formatter)
        
        # Adicionar ao logger
        logger.addHandler(handler)
        
        # Registrar o handler
        handler_id = f"file_{name}"
        self.handlers[handler_id] = handler
        
        logger.info(f"Adicionado handler específico para {name} em {log_file}")

# Instância global do LogManager
log_manager = LogManager()

def setup_logging(config):
    """
    Configura o sistema de logging com base nas configurações
    
    Args:
        config: Objeto de configuração com as propriedades necessárias
    """
    log_manager.setup(
        log_dir=config.log_dir,
        log_level=config.log_level,
        console=True,
        max_size_mb=config.log_max_size_mb,
        backup_count=config.log_backup_count
    )
    
    return log_manager

def get_logger(name: str) -> logging.Logger:
    """
    Função de conveniência para obter um logger
    
    Args:
        name (str): Nome do módulo (geralmente __name__)
        
    Returns:
        logging.Logger: Logger configurado
    """
    return log_manager.get_logger(name)
