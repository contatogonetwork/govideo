# GONETWORK AI - Sistema de Gerenciamento de Produção Audiovisual

![GONETWORK AI Logo](resources/images/logo.png)

## Visão Geral

**GONETWORK AI** é uma plataforma inteligente de gerenciamento de produção audiovisual para eventos. Desenvolvido com foco em agilidade, organização e tecnologia, o sistema centraliza o controle de cronogramas, equipes, entregas e assets de mídia, além de integrar recursos de inteligência artificial para análise de conteúdo.

### Funcionalidades Principais

- 🎤 **Gerenciamento de Eventos**  
  Crie e organize eventos com múltiplos palcos ou áreas, definindo horários, descrições e fluxos.

- 👥 **Gestão de Equipes**  
  Atribua funções, controle disponibilidade e visualize a escala de cada membro.

- 🎬 **Rastreamento de Entregas**  
  Acompanhe o status e a evolução de entregas audiovisuais com controle de versões.

- 🎞️ **Biblioteca de Assets**  
  Armazene e classifique vídeos, imagens, áudios e documentos em uma biblioteca centralizada.

- 🧠 **Análise de Vídeo com IA**  
  Use inteligência artificial para detectar padrões, insights ou falhas em conteúdos capturados.

- 📊 **Dashboard Intuitivo**  
  Tenha uma visão em tempo real do andamento de todos os projetos e tarefas do evento.

---

## Requisitos do Sistema

### Requisitos de Software

- Python 3.8 ou superior  
- PyQt5 5.15+  
- SQLAlchemy 1.4+  
- OpenCV 4.5+  
- Werkzeug (gestão de senhas e autenticação)  
- FFmpeg (opcional, recomendado para análises de vídeo)

### Requisitos de Hardware

- CPU: Intel Core i5 ou equivalente (mínimo)  
- RAM: 8 GB (mínimo) — 16 GB recomendado  
- Armazenamento: 500 MB para instalação, espaço adicional para mídias  
- GPU: Recomendado para aceleração de IA e vídeo

### Sistemas Operacionais Suportados

- Windows 10 ou 11  
- macOS 11+ (Big Sur ou superior)  
- Ubuntu 20.04 LTS ou superior

---

## Instalação

### Opção 1: Instalação via `pip`
```bash
pip install -r requirements.txt
python main.py

## Histórico de Atualizações

### 15 de maio de 2025 - Correção de bugs (v1.1.1)
- Corrigido erro ao salvar comentários em entregas (`is_system` inválido em `DeliveryComment`)
- Corrigido erro de NoneType ao editar entregas na interface
- Adicionado script de manutenção automática do sistema
- Implementada rotação de logs (5MB por arquivo, máximo 5 backups)

Para mais detalhes, consulte os relatórios:
- Correções de bugs: [bug_fix_report_20250515.md](bug_fix_report_20250515.md)
- Manutenção: [maintenance_report_20250515.md](maintenance_report_20250515.md)
