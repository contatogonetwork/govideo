"""
GONETWORK AI - Controlador Base
Define a classe base para todos os controladores da aplicação
"""

from PyQt5.QtCore import QObject
from core.logging_manager import get_logger

logger = get_logger(__name__)

class BaseController(QObject):
    """
    Classe base para todos os controladores da aplicação.
    
    Os controladores são responsáveis por:
    1. Mediar a comunicação entre models e views
    2. Implementar a lógica de negócio da aplicação
    3. Processar eventos e ações do usuário
    4. Atualizar models e views conforme necessário
    """
    
    def __init__(self, db_session):
        """
        Inicializa o controlador base.
        
        Args:
            db_session: Sessão do SQLAlchemy para acesso ao banco de dados
        """
        super().__init__()
        self.db = db_session
        logger.debug(f"Controlador {self.__class__.__name__} inicializado")
        
    def shutdown(self):
        """
        Realiza limpezas necessárias antes do encerramento
        """
        logger.debug(f"Controlador {self.__class__.__name__} encerrado")
