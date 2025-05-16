# GONETWORK AI - Implementação de arquitetura MVC

## Visão Geral

Este projeto implementa uma refatoração da aplicação GONETWORK AI para utilizar o padrão de arquitetura Model-View-Controller (MVC). A refatoração visa melhorar a organização do código, separação de responsabilidades, testabilidade e manutenibilidade do sistema.

## Estrutura do Projeto

O projeto segue a seguinte estrutura de diretórios:

```
govideo/
  ├── models/              # Camada de modelo (classes de dados)
  │    ├── __init__.py     # Inicializador do pacote
  │    ├── base.py         # Classes e tipos base compartilhados
  │    ├── asset.py        # Modelos para assets de mídia
  │    ├── delivery.py     # Modelos para entregas
  │    ├── event.py        # Modelos para eventos e atividades
  │    ├── sponsor.py      # Modelos para patrocinadores e ativações
  │    └── team.py         # Modelos para equipe
  │
  ├── controllers/         # Camada de controladores (lógica de negócio)
  │    ├── __init__.py     # Classe base de controladores
  │    ├── asset_controller.py     # Controlador de biblioteca de mídia
  │    ├── delivery_controller.py  # Controlador de kanban de entregas
  │    ├── sponsor_controller.py   # Controlador de patrocinadores
  │    ├── team_controller.py      # Controlador de equipe
  │    └── timeline_controller.py  # Controlador de cronograma
  │
  ├── ui/                  # Interface do usuário
  │    ├── models/         # Modelos de view (para visualização)
  │    └── views/          # Views da aplicação
  │         ├── delivery_kanban_view_mvc.py  # View MVC para kanban
  │         └── asset_library_view_mvc.py    # View MVC para biblioteca
  │
  ├── core/                # Funcionalidades centrais
  │    ├── config.py       # Sistema de configuração
  │    ├── database.py     # Conexão com banco de dados
  │    └── logging_manager.py  # Sistema de logging
  │
  ├── application_mvc.py   # Aplicação principal usando MVC
  └── settings.json        # Arquivo de configuração
```

## O Padrão MVC Implementado

### Model (Modelos)

Os modelos representam os dados da aplicação e são implementados como classes SQLAlchemy. Eles definem:
- Estrutura das tabelas do banco de dados
- Relacionamentos entre entidades
- Propriedades calculadas e métodos de utilidade específicos dos dados

### Controller (Controladores)

Os controladores encapsulam a lógica de negócio e fazem a mediação entre os modelos e as views. Eles são responsáveis por:
- Carregar e manipular dados dos modelos
- Implementar a lógica das operações de negócio
- Validar entradas e manter a consistência dos dados
- Notificar as views sobre mudanças nos dados usando sinais

### View (Visualizações)

As views são responsáveis por exibir os dados ao usuário e capturar interações. Elas:
- Exibem informações ao usuário de forma apropriada
- Capturam entradas e interações
- Delegam o processamento aos controladores correspondentes
- Atualizam a interface quando os controladores emitem sinais

## Como Funciona

1. **Inicialização**: A aplicação cria os componentes necessários:
   - Configurações são carregadas
   - Conexão com banco de dados é estabelecida
   - Controladores são inicializados
   - Views são criadas e conectadas aos controladores

2. **Fluxo de Operação**:
   - O usuário interage com uma view
   - A view chama métodos do controlador correspondente
   - O controlador processa a lógica de negócio, manipulando os modelos
   - O controlador emite sinais informando sobre alterações nos dados
   - As views conectadas a esses sinais atualizam sua interface

3. **Comunicação entre Componentes**:
   - De View para Controller: Chamadas diretas de métodos
   - De Controller para View: Sinais PyQt (pyqtSignal)
   - Entre Controllers: Chamadas diretas ou através de eventos compartilhados

## Controladores Implementados

### BaseController (`controllers/__init__.py`)
Classe base que define comportamentos comuns a todos os controladores.

### DeliveryKanbanController (`controllers/delivery_controller.py`)
Gerencia a lógica de negócio para o quadro Kanban de entregas:
- Carregamento das entregas com filtros
- Movimentação de entregas entre colunas
- Criação, edição e exclusão de entregas
- Gerenciamento de status e progresso
- Adição de comentários

### TeamController (`controllers/team_controller.py`)
Gerencia equipes e atribuições:
- Carregamento de membros da equipe e suas atribuições
- Criação e edição de membros da equipe
- Gerenciamento de escalas e verificação de conflitos
- Visualização da agenda da equipe

### AssetController (`controllers/asset_controller.py`)
Gerencia a biblioteca de mídia:
- Importação e organização de arquivos
- Criação e navegação em estrutura de pastas
- Geração de thumbnails
- Extração de metadados
- Pesquisa e filtros

### SponsorController (`controllers/sponsor_controller.py`)
Gerencia patrocinadores e ativações:
- Cadastro e atualização de patrocinadores
- Gerenciamento de ativações
- Registro de evidências de ativações
- Fluxo de aprovação

### TimelineController (`controllers/timeline_controller.py`)
Gerencia o cronograma de eventos:
- Visualização do cronograma em diferentes escalas
- Filtros por palco, status, etc.
- Gerenciamento de atividades e seus relacionamentos
- Detecção de conflitos

## Views MVC Implementadas

### DeliveryKanbanMVC (`ui/views/delivery_kanban_view_mvc.py`)
Implementa o quadro Kanban de entregas usando o novo padrão MVC:
- Exibição de entregas em formato Kanban
- Filtros de responsáveis, atividades, texto
- Drag & drop entre colunas
- Notificações de atualizações

### AssetLibraryMVC (`ui/views/asset_library_view_mvc.py`)
Implementa a biblioteca de mídia usando o novo padrão MVC:
- Navegação em estrutura de pastas
- Grid de thumbnails de assets
- Filtros por tipo, evento, texto
- Importação de arquivos

## Como Usar a Nova Arquitetura

### 1. Inicializando Controladores

```python
# Criar sessão de banco de dados
db_session = create_session(path_to_database)

# Inicializar controladores
timeline_controller = TimelineController(db_session)
delivery_controller = DeliveryKanbanController(db_session)
team_controller = TeamController(db_session)
asset_controller = AssetController(db_session)
sponsor_controller = SponsorController(db_session)
```

### 2. Conectando Views aos Controladores

```python
# Criar view com controlador
kanban_view = DeliveryKanbanMVC(db_session)

# Ou conectar posteriormente
asset_view = AssetLibraryMVC()
asset_view.set_database(db_session)
```

### 3. Usando os Controladores nas Views

```python
# Definir evento atual (todas as views precisam disso)
event_id = 123
delivery_kanban_view.set_event(event_id)

# Aplicar filtros
delivery_kanban_view.apply_filters()

# Criar nova entrega (exemplo)
nome = "Video abertura"
descricao = "Vídeo de abertura do evento"
prazo = datetime.datetime(2025, 5, 20, 12, 0)
responsavel_id = 42
controller = delivery_kanban_view.controller
controller.create_delivery(nome, descricao, prazo, responsavel_id, event_id)
```

### 4. Reagindo a Sinais do Controlador

```python
# Na inicialização da view:
def connect_signals(self):
    self.controller.deliveries_updated.connect(self.on_deliveries_updated)
    self.controller.delivery_moved.connect(self.on_delivery_moved)
    
def on_delivery_moved(self, delivery_id, to_column):
    # Atualizar a interface após a movimentação
    self.refresh_data()
```

## Próximos Passos

### 1. Completar a Refatoração das Views

- Refatorar as demais views existentes para usar os novos controladores:
  - `timeline_view.py` → Usar `TimelineController`
  - `team_view.py` → Usar `TeamController` 
  - `activation_view.py` → Usar `SponsorController`

### 2. Implementar Testes Unitários

Agora que a lógica de negócio está isolada em controladores, é mais fácil escrever testes:

```python
def test_delivery_kanban_controller():
    # Configurar banco em memória para testes
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Criar dados de teste
    event = Event(name="Evento Teste", start_date=datetime.now())
    session.add(event)
    session.commit()
    
    # Inicializar controlador com sessão de teste
    controller = DeliveryKanbanController(session)
    controller.set_current_event(event.id)
    
    # Testar métodos do controlador
    delivery = controller.create_delivery(
        "Teste", "Descrição", datetime.now(), 1, event.id)
    assert delivery.id is not None
    
    # Testar movimentação
    assert controller.move_delivery(delivery.id, "in_progress")
    
    # Verificar se status foi atualizado
    delivery = controller.get_delivery(delivery.id)
    assert delivery.status == "in_progress"
```

### 3. Migrar o Aplicativo Principal

Atualizar o aplicativo principal para usar a nova estrutura MVC:
- Manter compatibilidade com as views antigas durante a transição
- Garantir que os sinais sejam conectados corretamente
- Validar comportamento correto com diferentes conjuntos de dados

### 4. Documentação e Padronização

- Criar documentação detalhada para controladores e views
- Estabelecer convenções claras para:
  - Nomeação de métodos e sinais
  - Tratamento de erros
  - Padrões de codificação
  - Comunicação entre controllers

## Conclusão

A implementação do padrão MVC representa um avanço significativo na arquitetura da aplicação GONETWORK AI, proporcionando uma base sólida para o desenvolvimento futuro. A separação clara de responsabilidades entre modelos, views e controladores facilita a manutenção, testabilidade e evolução do sistema.

## Referências

- [Documentação do PyQt5](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/14/orm/)
- [Padrões de Design em Python](https://refactoring.guru/design-patterns/python)
- [Documentação interna do GONETWORK AI]
