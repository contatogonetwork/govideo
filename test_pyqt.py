"""
Script para testar se as dependências estão funcionando corretamente.
"""
def test_dependency(name, import_statement):
    try:
        print(f"Testando {name}...")
        exec(import_statement)
        print(f"✓ {name} importado com sucesso!")
        return True
    except Exception as e:
        print(f"✗ Erro ao importar {name}: {e}")
        return False

# Teste do PyQt5
pyqt_ok = test_dependency("PyQt5", "from PyQt5.QtWidgets import QApplication; from PyQt5.QtCore import QT_VERSION_STR; print(f'Versão do Qt: {QT_VERSION_STR}')")

# Teste do SQLAlchemy e SQLAlchemy Utils
sqlalchemy_ok = test_dependency("SQLAlchemy", "import sqlalchemy; print(f'Versão do SQLAlchemy: {sqlalchemy.__version__}')")
sqlalchemy_utils_ok = test_dependency("SQLAlchemy Utils", "import sqlalchemy_utils")

print("\n--- Resultado ---")
if all([pyqt_ok, sqlalchemy_ok, sqlalchemy_utils_ok]):
    print("✓ Todas as dependências estão instaladas corretamente!")
else:
    print("✗ Algumas dependências estão faltando. Instale-as com os comandos:")
    if not pyqt_ok:
        print("   pip install --force-reinstall PyQt5")
    if not sqlalchemy_ok:
        print("   pip install sqlalchemy")
    if not sqlalchemy_utils_ok:
        print("   pip install sqlalchemy_utils")
    print("\nPara Windows, se ainda houver problemas com DLLs:")
    print("Instale o Visual C++ Redistributable: https://aka.ms/vs/16/release/vc_redist.x64.exe")
