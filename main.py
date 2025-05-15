#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Ponto de entrada principal
Data: 2025-05-15
Autor: GONETWORK AI
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication

# Certifica-se que o diretório atual está no sys.path para importações relativas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar a função principal do módulo da janela principal
from ui.main_window import main

if __name__ == "__main__":
    # Configurar logging
    log_file = "gonetwork_ai.log"
    
    try:
        # Tenta criar arquivo de log na pasta de logs
        os.makedirs("logs", exist_ok=True)
        log_file = os.path.join("logs", log_file)
    except:
        # Fallback para o diretório atual
        pass
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Registrar início da aplicação
    logging.info("Iniciando GONETWORK AI")
    
    # Chamar função principal
    main()