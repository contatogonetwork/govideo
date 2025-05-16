#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Configurações
Sistema de configurações centralizado com suporte a configurações personalizáveis
"""

import os
import json
import logging
import datetime
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

@dataclass
class Settings:
    """Classe de configurações centralizadas"""
    # Caminhos de arquivos e diretórios
    database_path: str = r"C:\govideo\data\gonetwork.db"
    upload_dir: str = r"C:\govideo\uploads"
    backup_dir: str = r"C:\govideo\backup"
    log_dir: str = r"C:\govideo\logs"
    
    # Configurações da aplicação
    app_name: str = "GONETWORK AI"
    app_version: str = "1.0.1"
    
    # Configurações de interface
    theme: str = "default"
    recent_events_count: int = 5
    
    # Configurações de logging
    log_level: str = "INFO"
    log_max_size_mb: int = 5
    log_backup_count: int = 5
    
    # Configurações de backup
    auto_backup_on_start: bool = True
    auto_backup_on_exit: bool = True
    keep_backups_days: int = 30
    
    # Extensões permitidas para uploads
    allowed_extensions: Dict[str, List[str]] = field(default_factory=lambda: {
        "video": ["mp4", "mov", "avi", "mkv", "wmv"],
        "audio": ["mp3", "wav", "ogg", "flac", "aac"],
        "image": ["jpg", "jpeg", "png", "gif", "bmp"],
        "document": ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt"]
    })
    
    @classmethod
    def load_from_file(cls, path: str) -> 'Settings':
        """Carrega configurações a partir de um arquivo JSON"""
        if not os.path.exists(path):
            logger.warning(f"Arquivo de configuração não encontrado em {path}. Usando configurações padrão.")
            return cls()
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Criar instância com valores padrão
            settings = cls()
            
            # Atualizar apenas os valores presentes no arquivo
            for key, value in data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
                else:
                    logger.warning(f"Configuração desconhecida no arquivo: {key}")
            
            logger.info(f"Configurações carregadas de {path}")
            return settings
            
        except Exception as e:
            logger.error(f"Erro ao carregar configurações de {path}: {str(e)}")
            return cls()
    
    def save_to_file(self, path: str) -> bool:
        """Salva configurações em um arquivo JSON"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=4, ensure_ascii=False)
            
            logger.info(f"Configurações salvas em {path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar configurações em {path}: {str(e)}")
            return False
    
    def get_database_url(self) -> str:
        """Retorna a URL do banco de dados para SQLAlchemy"""
        return f"sqlite:///{self.database_path}"
    
    def ensure_directories(self) -> None:
        """Garante que todos os diretórios necessários existam"""
        for path_name in ['upload_dir', 'backup_dir', 'log_dir']:
            path = getattr(self, path_name)
            os.makedirs(path, exist_ok=True)
            logger.debug(f"Diretório garantido: {path}")
        
        # Garantir subdiretórios de upload
        for subdir in ['assets', 'deliveries', 'evidences', 'logos']:
            os.makedirs(os.path.join(self.upload_dir, subdir), exist_ok=True)

# Localização padrão do arquivo de configuração
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'settings.json')

# Carregar configurações
settings = Settings.load_from_file(DEFAULT_CONFIG_PATH)

# Para compatibilidade com código existente
DEFAULT_DB_PATH = settings.database_path
UPLOAD_DIR = settings.upload_dir
APP_NAME = settings.app_name
APP_VERSION = settings.app_version
LOG_LEVEL = settings.log_level
