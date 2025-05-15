#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Script de instalação
Data: 2025-05-15
Autor: GONETWORK AI
"""

import os
import sys
import shutil
import platform
import subprocess
from setuptools import setup, find_packages

# Metadados do projeto
NAME = "gonetwork-ai"
VERSION = "1.0.0"
DESCRIPTION = "Sistema de gerenciamento de produção audiovisual para eventos"
AUTHOR = "GONETWORK AI"
AUTHOR_EMAIL = "contato@gonetwork.com"
URL = "https://www.gonetwork.com/ai"

# Dependências principais
INSTALL_REQUIRES = [
    "PyQt5>=5.15.0",
    "sqlalchemy>=1.4.0",
    "numpy>=1.20.0",
    "opencv-python>=4.5.0",
    "Pillow>=8.0.0",
    "pymediainfo>=5.1.0",
    "requests>=2.25.0",
    "pandas>=1.3.0",
]

# Dependências extras para desenvolvimento
EXTRAS_REQUIRE = {
    "dev": [
        "pytest>=6.0.0",
        "black>=21.5b2",
        "flake8>=3.9.0",
        "sphinx>=4.0.0"
    ]
}

# Arquivos de pacote Python
packages = find_packages(exclude=["tests", "tests.*"])

# Cria diretórios necessários
def create_directories():
    """Criar estrutura de diretórios necessária para a aplicação"""
    directories = [
        "resources/icons",
        "resources/images",
        "resources/models",
        "uploads/assets",
        "uploads/deliveries",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        
    print(f"✓ Estrutura de diretórios criada")

# Verifica requisitos externos
def check_external_dependencies():
    """Verificar dependências externas (como FFmpeg)"""
    missing = []
    
    # Verificar FFmpeg
    try:
        subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            check=True
        )
        print("✓ FFmpeg encontrado")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("⚠️ FFmpeg não encontrado - alguns recursos podem não funcionar")
        missing.append("ffmpeg")
        
    # Verificar MediaInfo
    try:
        import pymediainfo
        version = pymediainfo.__version__
        print(f"✓ pymediainfo encontrado (versão {version})")
    except ImportError:
        print("⚠️ pymediainfo não encontrado - alguns recursos podem não funcionar")
        missing.append("pymediainfo")
        
    return missing

# Gera arquivo de configuração
def generate_config():
    """Gerar arquivo de configuração inicial"""
    config_path = "core/config.py"
    
    # Verificar se já existe (não sobrescrever)
    if os.path.exists(config_path):
        print(f"ℹ️ Arquivo de configuração já existe: {config_path}")
        return
        
    # Sistema operacional
    system = platform.system()
    
    # Caminhos padrão por SO
    if system == "Windows":
        db_path = os.path.expanduser(r"~\AppData\Local\GONETWORK AI\gonetwork.db")
        upload_dir = os.path.expanduser(r"~\AppData\Local\GONETWORK AI\uploads")
    elif system == "Darwin":  # macOS
        db_path = os.path.expanduser("~/Library/Application Support/GONETWORK AI/gonetwork.db")
        upload_dir = os.path.expanduser("~/Library/Application Support/GONETWORK AI/uploads")
    else:  # Linux e outros
        db_path = os.path.expanduser("~/.local/share/gonetwork-ai/gonetwork.db")
        upload_dir = os.path.expanduser("~/.local/share/gonetwork-ai/uploads")
        
    # Garantir que as pastas pais existam
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Conteúdo do arquivo de configuração
    config_content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
GONETWORK AI - Configurações
Gerado automaticamente durante instalação
\"\"\"

# Caminho do banco de dados padrão
DEFAULT_DB_PATH = r"{db_path}"

# Diretório para uploads
UPLOAD_DIR = r"{upload_dir}"

# Configurações da aplicação
APP_NAME = "GONETWORK AI"
APP_VERSION = "{VERSION}"

# Configurações de logging
LOG_LEVEL = "INFO"
"""
    
    # Criar o arquivo
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
        
    print(f"✓ Arquivo de configuração gerado: {config_path}")
    print(f"  - Banco de dados: {db_path}")
    print(f"  - Diretório de uploads: {upload_dir}")

# Função principal de configuração
def main():
    """Configurar e instalar o GONETWORK AI"""
    print("\n" + "=" * 60)
    print(f"INSTALAÇÃO DO {NAME.upper()} v{VERSION}")
    print("=" * 60)
    
    # Criar diretórios
    create_directories()
    
    # Verificar dependências
    missing_deps = check_external_dependencies()
    
    # Gerar configuração
    generate_config()
    
    # Exibir informações de conclusão
    print("\nInstalação configurada com sucesso!")
    
    if missing_deps:
        print("\nAtenção: As seguintes dependências externas não foram encontradas:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nAlgumas funcionalidades podem não estar disponíveis.")
        
    print("\nPara iniciar a aplicação, execute:")
    print("  python main.py")
    print("=" * 60 + "\n")
    
    return missing_deps

# Configuração padrão do setuptools
setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    packages=packages,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "gonetwork-ai=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Video",
        "Topic :: Office/Business :: Scheduling",
    ],
)

# Executar configuração adicional quando executado diretamente
if __name__ == "__main__":
    main()