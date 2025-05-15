# GONETWORK AI - Sistema de Gerenciamento de Produção Audiovisual

![GONETWORK AI Logo](resources/images/logo.png)

## Visão Geral

O GONETWORK AI é uma plataforma avançada de gerenciamento de produção audiovisual para eventos, desenvolvida para otimizar o fluxo de trabalho de equipes criativas em ambientes dinâmicos. Este software integra gestão de equipes, cronogramas, assets e entregas, além de incorporar tecnologias de IA para análise de conteúdo.

### Funcionalidades Principais

- **Gerenciamento de Eventos**: Crie e gerencie eventos com palcos/áreas múltiplos, organize atividades e controle cronogramas.
- **Controle de Equipe**: Gerencie membros da equipe, atribuições e disponibilidade.
- **Controle de Entregas**: Acompanhe entregas audiovisuais com sistema de status e versionamento.
- **Biblioteca de Assets**: Organize e pesquise seu acervo de arquivos de mídia.
- **Análise de Vídeo**: Utilize tecnologia de IA para analisar conteúdo de vídeo e extrair insights.
- **Dashboard Intuitivo**: Visualize em tempo real o andamento de projetos e entregas.

## Requisitos do Sistema

### Requisitos de Software
- Python 3.8+
- PyQt5 5.15+
- SQLAlchemy 1.4+
- OpenCV 4.5+
- FFmpeg (opcional, para funcionalidades avançadas de vídeo)
- Werkzeug (para gerenciamento de senhas)

### Requisitos de Hardware
- Processador: Intel Core i5 ou equivalente (mínimo)
- Memória RAM: 8GB (mínimo), 16GB (recomendado)
- Armazenamento: 500MB para instalação, espaço adicional para arquivos de mídia
- GPU: Recomendada para processamento de vídeo com IA

### Sistemas Operacionais Suportados
- Windows 10/11
- macOS 11+ (Big Sur ou superior)
- Ubuntu 20.04 LTS ou superior

## Instalação

### Método 1: Instalação via pip
```bash
pip install -r requirements.txt
python main.py
```

### Método 2: Instalação direta do repositório
```bash
git clone https://github.com/seu-usuario/gonetwork-ai.git
cd gonetwork-ai
pip install -e .
python main.py
```

## Correções Recentes

Este repositório contém as seguintes melhorias recentes:

1. Implementação do componente `asset_library_view.py`
2. Correção de bugs relacionados à falta de importação QColor
3. Correção na configuração do banco de dados SQLAlchemy
4. Correção do relacionamento entre classes Tag e Asset
5. Adição do método `set_current_event()` em todas as views
6. Implementação da função `update_status()` no `DeliveryTracker`
7. Adição dos ícones necessários para o correto funcionamento
8. Correção na inicialização do banco de dados com usuário admin

## Contribuição

Contribuições são bem-vindas! Por favor, siga os seguintes passos:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Contato

Para dúvidas ou suporte, entre em contato através de [seu-email@exemplo.com].