# Detalhamento Técnico Aprofundado das Melhorias para GoVideo/GONETWORK AI

Data: 2025-05-15

## 1. Cronograma Visual com Filtros Avançados

### Implementação Detalhada:

O cronograma visual será uma extensão avançada do atual `timeline_view.py`, utilizando uma arquitetura MVC separada para melhor manutenção:

```python
# timeline_controller.py
class TimelineController(QObject):
    def __init__(self, model, view):
        super().__init__()
        self.model = model
        self.view = view
        self._connect_signals()
        
    def _connect_signals(self):
        self.view.filter_applied.connect(self.update_filtered_activities)
        self.view.activity_clicked.connect(self.open_activity_detail)
        
    def update_filtered_activities(self, filters):
        """Aplica filtros complexos e atualiza a visualização"""
        query = self.model.session.query(Activity)
        
        if filters.get('stage_ids'):
            query = query.filter(Activity.stage_id.in_(filters['stage_ids']))
            
        if filters.get('activity_types'):
            query = query.filter(Activity.type.in_(filters['activity_types']))
            
        if filters.get('responsible_ids'):
            query = query.filter(Activity.responsible_id.in_(filters['responsible_ids']))
            
        if filters.get('date_range'):
            start_date, end_date = filters['date_range']
            query = query.filter(Activity.start_time >= start_date,
                                Activity.end_time <= end_date)
            
        if filters.get('status'):
            query = query.filter(Activity.status.in_(filters['status']))
            
        activities = query.all()
        self.view.update_timeline(activities)
```

### Componentes Visuais Avançados:

1. **Filtro MultiCombo Hierárquico**: 
   - Implementar um `QComboBox` customizado com checkboxes aninhados
   - Permitir seleção em cascata (Ex: "Todos os Palcos" > "Palco A" > "Área VIP")

2. **TimeBlocks Interativos**:
   - Cada bloco contém um indicador de status com código de cores
   - Overlay com progresso percentual
   - Miniatura do palco renderizada em tempo real
   - Ícones de alerta para conflitos ou problemas

3. **Exportação Contextual**:
   - Botão direito do mouse abre menu com opções:
     - Exportar essa visualização para PDF/PNG
     - Enviar esse cronograma por email
     - Criar QR code para acesso rápido

### Filtros Avançados Específicos:

```python
# Classe para filtros avançados
class AdvancedTimelineFilters(QWidget):
    filter_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        
    def setupUI(self):
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Filtro de data com range
        self.date_range = QDateRangeWidget()
        
        # Filtros em abas para economizar espaço
        self.filter_tabs = QTabWidget()
        
        # Tab para filtrar por palco
        self.stage_tab = QWidget()
        self.stage_filter = HierarchicalCheckList()
        # Preencher com palcos da DB
        
        # Tab para filtrar por responsável
        self.responsible_tab = QWidget()
        self.responsible_filter = AvatarCheckList()
        # Mostrar fotos/avatares dos responsáveis
        
        # Tab para filtrar por status
        self.status_tab = QWidget()
        self.status_filter = IconCheckList()
        self.status_filter.add_item("Pendente", QIcon(":/icons/pending.png"))
        self.status_filter.add_item("Em andamento", QIcon(":/icons/in-progress.png"))
        self.status_filter.add_item("Concluído", QIcon(":/icons/completed.png"))
        self.status_filter.add_item("Problema", QIcon(":/icons/issue.png"))
        
        # Presets de filtros rápidos
        self.filter_presets = QComboBox()
        self.filter_presets.addItem("Meus itens pendentes hoje")
        self.filter_presets.addItem("Problemas que precisam de atenção")
        self.filter_presets.addItem("Próximas 4 horas")
        
        # Botão para salvar preset atual
        self.save_preset_btn = QPushButton("Salvar como preset")
        
        # Conectar sinais
        self.date_range.range_changed.connect(self._emit_filter_changed)
        self.stage_filter.selection_changed.connect(self._emit_filter_changed)
        # ... outros connects
```

### Sistema de Status Avançado:

O status de cada atividade será calculado automaticamente baseado em:

1. Horário atual vs. horário planejado
2. Atividades dependentes completadas
3. Recursos alocados disponíveis
4. Problemas reportados

```python
def calculate_activity_status(activity, current_time):
    """Calcula status dinâmico baseado em múltiplos fatores"""
    if activity.completed:
        return ActivityStatus.COMPLETED
        
    # Verifica se está atrasado
    if current_time > activity.start_time and activity.status != ActivityStatus.IN_PROGRESS:
        return ActivityStatus.DELAYED
        
    # Verifica dependências
    for dependency in activity.dependencies:
        if dependency.status != ActivityStatus.COMPLETED:
            return ActivityStatus.BLOCKED
            
    # Verifica recursos
    for resource in activity.required_resources:
        if not resource.is_available(activity.start_time, activity.end_time):
            return ActivityStatus.RESOURCE_CONFLICT
            
    # Verifica próximas atividades
    if (activity.start_time - current_time).total_seconds() < 3600:  # 1 hora
        return ActivityStatus.UPCOMING
        
    return ActivityStatus.SCHEDULED
```

## 2. Kanban Interativo de Entregas

### Arquitetura Detalhada:

O Kanban utilizará uma implementação MVC que separa claramente modelo de dados, visualização e controle de interação:

```python
# delivery_kanban_model.py
class KanbanBoardModel(QAbstractItemModel):
    """Modelo para Kanban baseado em QAbstractItemModel para performance"""
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.columns = ["pending", "editing", "reviewing", "completed"]
        self.cards = {col: [] for col in self.columns}
        self.load_data()
        
    def load_data(self):
        """Carrega dados do banco de dados"""
        deliveries = self.session.query(Delivery).all()
        for delivery in deliveries:
            column = self._map_status_to_column(delivery.status)
            self.cards[column].append(delivery)
            
    def _map_status_to_column(self, status):
        """Mapeia status do banco para coluna do Kanban"""
        mapping = {
            "pending": "pending",
            "in_progress": "editing",
            "in_review": "reviewing",
            "completed": "completed",
            "archived": "completed"  # Opcional: filtrar arquivados
        }
        return mapping.get(status, "pending")
```

### Componentes Visuais do Kanban:

1. **CardWidget Avançado**:
   - Design inspirado em Material UI ou Fluent Design
   - Campos dinâmicos baseados no tipo de entrega
   - Botões de ação contextual que aparecem no hover
   - Badges para prioridade e deadline

```python
class DeliveryCardWidget(QFrame):
    def __init__(self, delivery, parent=None):
        super().__init__(parent)
        self.delivery = delivery
        self.setup_ui()
        
    def setup_ui(self):
        # Estilo do card
        self.setObjectName("deliveryCard")
        self.setStyleSheet("""
            #deliveryCard {
                background-color: #ffffff;
                border-radius: 8px;
                border-left: 5px solid %s;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                margin: 8px;
                padding: 12px;
            }
            #cardTitle {
                font-weight: bold;
                font-size: 14px;
            }
            #cardDeadline {
                color: %s;
                font-size: 12px;
            }
        """ % (self._get_priority_color(), self._get_deadline_color()))
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Título com badge de prioridade
        title_layout = QHBoxLayout()
        title = QLabel(self.delivery.title)
        title.setObjectName("cardTitle")
        title_layout.addWidget(title)
        
        # Badge de prioridade
        priority = self._create_priority_badge()
        title_layout.addWidget(priority)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Miniatura se disponível
        if self.delivery.thumbnail_path:
            thumbnail = ThumbnailWidget(self.delivery.thumbnail_path)
            thumbnail.setMaximumHeight(80)
            thumbnail.setMaximumWidth(120)
            layout.addWidget(thumbnail, alignment=Qt.AlignCenter)
        
        # Informações adicionais
        info_layout = QFormLayout()
        info_layout.setSpacing(2)
        info_layout.addRow("Cliente:", QLabel(self.delivery.client.name if self.delivery.client else ""))
        info_layout.addRow("Editor:", QLabel(self.delivery.editor.name if self.delivery.editor else ""))
        
        # Deadline com formatação especial
        deadline_label = QLabel(self._format_deadline())
        deadline_label.setObjectName("cardDeadline")
        info_layout.addRow("Prazo:", deadline_label)
        
        layout.addLayout(info_layout)
        
        # Barra de progresso
        if self.delivery.progress is not None:
            progress_bar = QProgressBar()
            progress_bar.setValue(int(self.delivery.progress * 100))
            layout.addWidget(progress_bar)
        
        # Botões de ação
        action_layout = QHBoxLayout()
        view_btn = QPushButton(QIcon(":/icons/view.png"), "")
        view_btn.setToolTip("Ver detalhes")
        view_btn.setMaximumWidth(30)
        view_btn.clicked.connect(self.view_delivery)
        
        edit_btn = QPushButton(QIcon(":/icons/edit.png"), "")
        edit_btn.setToolTip("Editar")
        edit_btn.setMaximumWidth(30)
        edit_btn.clicked.connect(self.edit_delivery)
        
        action_layout.addWidget(view_btn)
        action_layout.addWidget(edit_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
    def _get_priority_color(self):
        """Retorna cor baseada na prioridade"""
        colors = {
            "low": "#4CAF50",     # Verde
            "medium": "#FFC107",  # Amarelo
            "high": "#FF5722",    # Laranja
            "urgent": "#F44336"   # Vermelho
        }
        return colors.get(self.delivery.priority, colors["medium"])
        
    def _get_deadline_color(self):
        """Retorna cor baseada na proximidade do deadline"""
        if not self.delivery.deadline:
            return "#757575"  # Cinza
            
        days_remaining = (self.delivery.deadline - datetime.now()).days
        if days_remaining < 0:
            return "#F44336"  # Vermelho - atrasado
        elif days_remaining < 1:
            return "#FF5722"  # Laranja - hoje
        elif days_remaining < 3:
            return "#FFC107"  # Amarelo - próximo
        else:
            return "#4CAF50"  # Verde - ok
```

2. **Sistema de Drag & Drop Avançado**:
   - Implementação com QDrag e QDrop para transições suaves
   - Animação de "recuo" se a operação for inválida
   - Preview do card durante arraste
   - Feedback visual nas colunas durante drag over

```python
class KanbanColumn(QFrame):
    """Coluna do Kanban que aceita cards via drag & drop"""
    card_dropped = Signal(object, str)  # delivery, column_id
    
    def __init__(self, title, column_id, parent=None):
        super().__init__(parent)
        self.title = title
        self.column_id = column_id
        self.setAcceptDrops(True)
        self.setup_ui()
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-deliverycard"):
            event.acceptProposedAction()
            self.setStyleSheet("background-color: rgba(0, 120, 215, 0.1);")
        
    def dragLeaveEvent(self, event):
        self.setStyleSheet("")
        
    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-deliverycard"):
            delivery_id = int(event.mimeData().data("application/x-deliverycard").data())
            self.card_dropped.emit(delivery_id, self.column_id)
            event.acceptProposedAction()
            self.setStyleSheet("")
```

### Sistema Avançado de Notificações:

O Kanban será integrado com um sistema de notificações que alerta sobre:

1. Movimentação de cards
2. Aproximação de deadlines
3. Comentários adicionados 
4. Alterações de prioridade

```python
class KanbanNotificationManager:
    """Gerencia notificações relacionadas ao Kanban"""
    def __init__(self, session, notification_service):
        self.session = session
        self.notification_service = notification_service
        
    def notify_card_moved(self, delivery_id, from_col, to_col, user_id):
        """Notifica sobre movimentação de card"""
        delivery = self.session.query(Delivery).get(delivery_id)
        
        # Determina quem deve receber a notificação
        recipients = set()
        if delivery.client_id:
            recipients.add(delivery.client_id)
        if delivery.editor_id:
            recipients.add(delivery.editor_id)
        if delivery.reviewer_id:
            recipients.add(delivery.reviewer_id)
        
        # Remove o próprio usuário que fez a ação
        if user_id in recipients:
            recipients.remove(user_id)
            
        # Formato da mensagem baseado na coluna destino
        message_templates = {
            "editing": "{user} começou a editar {delivery}",
            "reviewing": "{delivery} foi enviado para revisão por {user}",
            "completed": "{delivery} foi marcado como concluído por {user}"
        }
        
        user = self.session.query(User).get(user_id)
        message = message_templates.get(to_col, "{user} moveu {delivery}").format(
            user=user.name,
            delivery=delivery.title
        )
        
        # Envia notificação para cada destinatário
        for recipient_id in recipients:
            self.notification_service.send_notification(
                recipient_id=recipient_id,
                title="Atualização de Entrega",
                message=message,
                data={
                    "delivery_id": delivery_id,
                    "action": "card_moved",
                    "from_column": from_col,
                    "to_column": to_col
                },
                icon="delivery"
            )
```

## 3. Ativações Patrocinadas com Status e Evidência

### Modelo de Dados Expandido:

```python
class Sponsor(Base):
    __tablename__ = "sponsors"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    logo_path = Column(String)
    description = Column(Text)
    contact_name = Column(String)
    contact_email = Column(String)
    contact_phone = Column(String)
    tier = Column(Enum("platinum", "gold", "silver", "bronze", name="sponsor_tier"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    activations = relationship("Activation", back_populates="sponsor")
    
class ActivationType(Base):
    """Tipos de ativação possíveis"""
    __tablename__ = "activation_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    icon_path = Column(String)
    
    # Relationships
    activations = relationship("Activation", back_populates="activation_type")

class Activation(Base):
    __tablename__ = "activations"
    id = Column(Integer, primary_key=True)
    sponsor_id = Column(Integer, ForeignKey("sponsors.id"))
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    activation_type_id = Column(Integer, ForeignKey("activation_types.id"))
    status = Column(Enum("pending", "in_progress", "filmed", "failed", "approved", name="activation_status"))
    scheduled_time = Column(DateTime, nullable=True)
    completed_time = Column(DateTime, nullable=True)
    evidence_path = Column(String)  # Path para foto/vídeo de evidência
    public_url = Column(String)  # URL compartilhável para cliente
    notes = Column(Text)
    location_description = Column(String)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sponsor = relationship("Sponsor", back_populates="activations")
    activity = relationship("Activity", back_populates="activations")
    activation_type = relationship("ActivationType", back_populates="activations")
    approved_by = relationship("User")
    evidence_items = relationship("ActivationEvidence", back_populates="activation")
    
class ActivationEvidence(Base):
    """Evidências múltiplas para cada ativação"""
    __tablename__ = "activation_evidences"
    id = Column(Integer, primary_key=True)
    activation_id = Column(Integer, ForeignKey("activations.id"))
    file_path = Column(String, nullable=False)
    file_type = Column(Enum("image", "video", "audio", "document", name="evidence_file_type"))
    approved = Column(Boolean, default=False)
    notes = Column(Text)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    activation = relationship("Activation", back_populates="evidence_items")
    uploaded_by = relationship("User")
```

### Interface de Evidências:

A captura de evidências será implementada com uma interface moderna:

```python
class EvidenceCaptureWidget(QWidget):
    """Widget para captura de evidências de ativação"""
    evidence_captured = Signal(object)  # Evidence data
    
    def __init__(self, activation_id, parent=None):
        super().__init__(parent)
        self.activation_id = activation_id
        self.camera = None
        self.video_widget = None
        self.capture_path = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Abas para diferentes tipos de captura
        self.capture_tabs = QTabWidget()
        
        # Tab de câmera
        self.camera_tab = QWidget()
        camera_layout = QVBoxLayout(self.camera_tab)
        
        # Widget de visualização da câmera
        self.video_widget = QVideoWidget()
        camera_layout.addWidget(self.video_widget)
        
        # Controles da câmera
        camera_controls = QHBoxLayout()
        self.capture_btn = QPushButton("Capturar Foto")
        self.capture_btn.setIcon(QIcon(":/icons/camera.png"))
        self.capture_btn.clicked.connect(self.capture_photo)
        
        self.record_btn = QPushButton("Gravar Vídeo")
        self.record_btn.setIcon(QIcon(":/icons/video.png"))
        self.record_btn.clicked.connect(self.toggle_recording)
        
        camera_controls.addWidget(self.capture_btn)
        camera_controls.addWidget(self.record_btn)
        camera_layout.addLayout(camera_controls)
        
        # Tab de upload de arquivo
        self.upload_tab = QWidget()
        upload_layout = QVBoxLayout(self.upload_tab)
        
        self.file_list = QListWidget()
        upload_layout.addWidget(self.file_list)
        
        upload_controls = QHBoxLayout()
        self.add_file_btn = QPushButton("Adicionar Arquivo")
        self.add_file_btn.setIcon(QIcon(":/icons/add_file.png"))
        self.add_file_btn.clicked.connect(self.add_file)
        
        self.remove_file_btn = QPushButton("Remover")
        self.remove_file_btn.setIcon(QIcon(":/icons/delete.png"))
        self.remove_file_btn.clicked.connect(self.remove_file)
        
        upload_controls.addWidget(self.add_file_btn)
        upload_controls.addWidget(self.remove_file_btn)
        upload_layout.addLayout(upload_controls)
        
        # Adicionar as abas
        self.capture_tabs.addTab(self.camera_tab, "Capturar")
        self.capture_tabs.addTab(self.upload_tab, "Arquivos")
        layout.addWidget(self.capture_tabs)
        
        # Área de preview
        self.preview_label = QLabel("Nenhuma evidência capturada")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px dashed #aaa;")
        layout.addWidget(self.preview_label)
        
        # Campos de descrição
        form_layout = QFormLayout()
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Adicione observações sobre esta evidência...")
        self.notes_edit.setMaximumHeight(100)
        form_layout.addRow("Observações:", self.notes_edit)
        layout.addLayout(form_layout)
        
        # Botão de salvar
        self.save_btn = QPushButton("Salvar Evidência")
        self.save_btn.setIcon(QIcon(":/icons/save.png"))
        self.save_btn.clicked.connect(self.save_evidence)
        layout.addWidget(self.save_btn)
        
    def initialize_camera(self):
        """Inicializa a câmera do dispositivo"""
        available_cameras = QCameraInfo.availableCameras()
        if not available_cameras:
            QMessageBox.warning(self, "Erro", "Nenhuma câmera encontrada")
            return False
        
        # Use a primeira câmera disponível
        self.camera = QCamera(available_cameras[0])
        self.camera.setViewfinder(self.video_widget)
        
        # Configurações de captura
        self.image_capture = QCameraImageCapture(self.camera)
        self.image_capture.imageCaptured.connect(self.display_captured_image)
        self.image_capture.imageSaved.connect(self.image_saved)
        
        # Iniciar câmera
        self.camera.start()
        return True
        
    def capture_photo(self):
        """Captura uma foto da câmera"""
        if not self.camera:
            if not self.initialize_camera():
                return
                
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = os.path.join(tempfile.gettempdir(), "govideo_evidence")
        os.makedirs(temp_dir, exist_ok=True)
        
        self.capture_path = os.path.join(temp_dir, f"evidence_{timestamp}.jpg")
        self.image_capture.capture(self.capture_path)
        
    # Outros métodos de captura, preview e upload...
```

### Sistema de Aprovação em Tempo Real:

Para gerenciar o processo de aprovação de ativações patrocinadas:

```python
class SponsorActivationApprovalWidget(QWidget):
    """Interface para aprovação de ativações por patrocinador"""
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.current_sponsor = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Cabeçalho com seleção de patrocinador
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Patrocinador:"))
        
        self.sponsor_combo = QComboBox()
        self.load_sponsors()
        self.sponsor_combo.currentIndexChanged.connect(self.sponsor_changed)
        header_layout.addWidget(self.sponsor_combo)
        
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("")
        self.refresh_btn.setIcon(QIcon(":/icons/refresh.png"))
        self.refresh_btn.setToolTip("Atualizar")
        self.refresh_btn.clicked.connect(self.load_activations)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Splitter para dividir lista e detalhes
        splitter = QSplitter(Qt.Horizontal)
        
        # Lista de ativações
        self.activations_list = QListWidget()
        self.activations_list.setIconSize(QSize(32, 32))
        self.activations_list.currentItemChanged.connect(self.activation_selected)
        splitter.addWidget(self.activations_list)
        
        # Detalhes da ativação
        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        
        # Informações básicas
        self.info_form = QFormLayout()
        self.activation_title = QLabel()
        self.activation_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.info_form.addRow("Ativação:", self.activation_title)
        
        self.activation_type = QLabel()
        self.info_form.addRow("Tipo:", self.activation_type)
        
        self.activation_time = QLabel()
        self.info_form.addRow("Horário:", self.activation_time)
        
        self.activation_status = QLabel()
        self.info_form.addRow("Status:", self.activation_status)
        
        details_layout.addLayout(self.info_form)
        
        # Evidências
        evidence_group = QGroupBox("Evidências")
        evidence_layout = QVBoxLayout(evidence_group)
        
        self.evidence_list = QListWidget()
        self.evidence_list.setViewMode(QListWidget.IconMode)
        self.evidence_list.setIconSize(QSize(120, 90))
        self.evidence_list.setResizeMode(QListWidget.Adjust)
        self.evidence_list.itemDoubleClicked.connect(self.view_evidence)
        evidence_layout.addWidget(self.evidence_list)
        
        details_layout.addWidget(evidence_group)
        
        # Área de comentários
        comment_group = QGroupBox("Comentários e Aprovação")
        comment_layout = QVBoxLayout(comment_group)
        
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Adicione um comentário...")
        self.comment_edit.setMaximumHeight(100)
        comment_layout.addWidget(self.comment_edit)
        
        approval_buttons = QHBoxLayout()
        self.approve_btn = QPushButton("Aprovar")
        self.approve_btn.setIcon(QIcon(":/icons/approve.png"))
        self.approve_btn.clicked.connect(self.approve_activation)
        
        self.reject_btn = QPushButton("Rejeitar")
        self.reject_btn.setIcon(QIcon(":/icons/reject.png"))
        self.reject_btn.clicked.connect(self.reject_activation)
        
        approval_buttons.addWidget(self.approve_btn)
        approval_buttons.addWidget(self.reject_btn)
        comment_layout.addLayout(approval_buttons)
        
        details_layout.addWidget(comment_group)
        
        # Botão para gerar relatório
        self.report_btn = QPushButton("Gerar Relatório de Ativações")
        self.report_btn.setIcon(QIcon(":/icons/report.png"))
        self.report_btn.clicked.connect(self.generate_report)
        details_layout.addWidget(self.report_btn)
        
        splitter.addWidget(self.details_widget)
        splitter.setSizes([200, 400])  # Proporção inicial
        
        layout.addWidget(splitter)
        
    def load_sponsors(self):
        """Carrega patrocinadores no combo"""
        self.sponsor_combo.clear()
        self.sponsor_combo.addItem("Selecione um patrocinador", -1)
        
        sponsors = self.session.query(Sponsor).order_by(Sponsor.name).all()
        for sponsor in sponsors:
            self.sponsor_combo.addItem(sponsor.name, sponsor.id)
```

## 4. Escala e Atribuições Visuais da Equipe

### Arquitetura de Modelagem Avançada:

```python
class ScheduleManager:
    """Gerencia a alocação e visualização da escala de equipe"""
    def __init__(self, session):
        self.session = session
        
    def get_team_assignments(self, start_date, end_date, team_member_ids=None, role_ids=None):
        """Obtém atribuições de equipe com filtros avançados"""
        query = self.session.query(TeamAssignment)
        
        # Filtro de data
        query = query.filter(
            or_(
                # Caso 1: Início da atribuição está dentro do período
                and_(
                    TeamAssignment.start_time >= start_date,
                    TeamAssignment.start_time <= end_date
                ),
                # Caso 2: Fim da atribuição está dentro do período
                and_(
                    TeamAssignment.end_time >= start_date,
                    TeamAssignment.end_time <= end_date
                ),
                # Caso 3: Atribuição cobre todo o período
                and_(
                    TeamAssignment.start_time <= start_date,
                    TeamAssignment.end_time >= end_date
                )
            )
        )
        
        # Filtro por membros da equipe
        if team_member_ids:
            query = query.filter(TeamAssignment.team_member_id.in_(team_member_ids))
            
        # Filtro por função
        if role_ids:
            query = query.filter(TeamAssignment.role_id.in_(role_ids))
            
        # Ordenar por horário de início e membro da equipe
        query = query.order_by(TeamAssignment.start_time, TeamAssignment.team_member_id)
        
        # Eager loading para melhor performance
        query = query.options(
            joinedload(TeamAssignment.team_member),
            joinedload(TeamAssignment.role),
            joinedload(TeamAssignment.activity)
        )
        
        return query.all()
    
    def check_conflicts(self, team_member_id, start_time, end_time, exclude_assignment_id=None):
        """Verifica conflitos de agenda para um membro da equipe"""
        query = self.session.query(TeamAssignment).filter(
            TeamAssignment.team_member_id == team_member_id,
            or_(
                # Caso 1: Nova atribuição começa durante outra
                and_(
                    TeamAssignment.start_time <= start_time,
                    TeamAssignment.end_time > start_time
                ),
                # Caso 2: Nova atribuição termina durante outra
                and_(
                    TeamAssignment.start_time < end_time,
                    TeamAssignment.end_time >= end_time
                ),
                # Caso 3: Nova atribuição cobre outra completamente
                and_(
                    TeamAssignment.start_time >= start_time,
                    TeamAssignment.end_time <= end_time
                )
            )
        )
        
        # Excluir a própria atribuição no caso de edição
        if exclude_assignment_id:
            query = query.filter(TeamAssignment.id != exclude_assignment_id)
            
        return query.all()
    
    def get_team_member_availability(self, team_member_id, date):
        """Retorna disponibilidade de um membro em um dia específico"""
        # Início e fim do dia
        start_of_day = datetime.combine(date, time.min)
        end_of_day = datetime.combine(date, time.max)
        
        # Buscar atribuições do dia
        assignments = self.session.query(TeamAssignment).filter(
            TeamAssignment.team_member_id == team_member_id,
            TeamAssignment.start_time <= end_of_day,
            TeamAssignment.end_time >= start_of_day
        ).all()
        
        # Criar timeline de disponibilidade em intervalos de 30 minutos
        availability = {}
        current_time = start_of_day
        while current_time <= end_of_day:
            availability[current_time.strftime("%H:%M")] = "available"
            current_time += timedelta(minutes=30)
        
        # Marcar slots ocupados
        for assignment in assignments:
            # Ajustar para início e fim do dia se necessário
            slot_start = max(assignment.start_time, start_of_day)
            slot_end = min(assignment.end_time, end_of_day)
            
            # Marcar slots como ocupados
            current_slot = slot_start
            while current_slot < slot_end:
                slot_key = current_slot.strftime("%H:%M")
                if slot_key in availability:
                    availability[slot_key] = "busy"
                current_slot += timedelta(minutes=30)
        
        return availability
    
    def create_team_schedule_export(self, date, team_member_ids=None, format="pdf"):
        """Cria um export da escala da equipe"""
        # Implementação depende do formato de saída desejado
        pass
```

### Interface de Calendário Avançada:

```python
class TeamScheduleCalendar(QWidget):
    """Calendário de equipe com visualização avançada"""
    assignment_clicked = Signal(int)  # assignment_id
    day_clicked = Signal(QDate)
    
    def __init__(self, schedule_manager, parent=None):
        super().__init__(parent)
        self.schedule_manager = schedule_manager
        self.current_view_mode = "week"  # "day", "week", "month"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar com controles de visualização
        toolbar = QToolBar()
        
        # Navegação de data
        self.prev_btn = QAction(QIcon(":/icons/prev.png"), "Anterior", self)
        self.prev_btn.triggered.connect(self.go_previous)
        toolbar.addAction(self.prev_btn)
        
        self.today_btn = QAction(QIcon(":/icons/today.png"), "Hoje", self)
        self.today_btn.triggered.connect(self.go_today)
        toolbar.addAction(self.today_btn)
        
        self.next_btn = QAction(QIcon(":/icons/next.png"), "Próximo", self)
        self.next_btn.triggered.connect(self.go_next)
        toolbar.addAction(self.next_btn)
        
        toolbar.addSeparator()
        
        # Seletor de data
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.date_changed)
        toolbar.addWidget(self.date_edit)
        
        toolbar.addSeparator()
        
        # Modos de visualização
        self.view_group = QActionGroup(self)
        
        self.day_view_action = QAction(QIcon(":/icons/day.png"), "Dia", self)
        self.day_view_action.setCheckable(True)
        self.day_view_action.triggered.connect(lambda: self.set_view_mode("day"))
        self.view_group.addAction(self.day_view_action)
        toolbar.addAction(self.day_view_action)
        
        self.week_view_action = QAction(QIcon(":/icons/week.png"), "Semana", self)
        self.week_view_action.setCheckable(True)
        self.week_view_action.setChecked(True)
        self.week_view_action.triggered.connect(lambda: self.set_view_mode("week"))
        self.view_group.addAction(self.week_view_action)
        toolbar.addAction(self.week_view_action)
        
        self.month_view_action = QAction(QIcon(":/icons/month.png"), "Mês", self)
        self.month_view_action.setCheckable(True)
        self.month_view_action.triggered.connect(lambda: self.set_view_mode("month"))
        self.view_group.addAction(self.month_view_action)
        toolbar.addAction(self.month_view_action)
        
        toolbar.addSeparator()
        
        # Filtros
        self.filter_btn = QAction(QIcon(":/icons/filter.png"), "Filtros", self)
        self.filter_btn.triggered.connect(self.show_filters)
        toolbar.addAction(self.filter_btn)
        
        # Exportar
        self.export_btn = QAction(QIcon(":/icons/export.png"), "Exportar", self)
        self.export_btn.triggered.connect(self.export_schedule)
        toolbar.addAction(self.export_btn)
        
        layout.addWidget(toolbar)
        
        # Stack de visualizações
        self.view_stack = QStackedWidget()
        
        # Visualização diária
        self.day_view = TeamDayScheduleView()
        self.view_stack.addWidget(self.day_view)
        
        # Visualização semanal
        self.week_view = TeamWeekScheduleView()
        self.view_stack.addWidget(self.week_view)
        
        # Visualização mensal
        self.month_view = TeamMonthScheduleView()
        self.view_stack.addWidget(self.month_view)
        
        layout.addWidget(self.view_stack)
        
        # Inicializar com visualização semanal
        self.set_view_mode("week")
        self.load_current_data()
```

### Widget de Visualização por Semana:

```python
class TeamWeekScheduleView(QWidget):
    """Visualização semanal da escala de equipe"""
    
    assignment_clicked = Signal(int)  # assignment_id
    time_slot_clicked = Signal(QDateTime, int)  # datetime, team_member_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.schedule_data = {}
        self.team_members = []
        self.week_start = None
        self.hours_range = (7, 22)  # 7:00 às 22:00
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Cabeçalho com dias da semana
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setSpacing(1)
        self.header_layout.setContentsMargins(80, 0, 0, 0)  # Espaço para cabeçalho de membros
        
        # Serão adicionados dinamicamente os labels de dias
        
        self.layout.addWidget(self.header_widget)
        
        # Área de rolagem para a grade
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Widget de conteúdo para a grade
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(1)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.grid_widget)
        self.layout.addWidget(self.scroll_area)
        
    def set_week(self, start_date):
        """Define a semana a ser exibida"""
        self.week_start = start_date
        self.update_header()
        
    def set_team_members(self, members):
        """Define os membros da equipe a serem exibidos"""
        self.team_members = members
        self.update_grid()
        
    def set_schedule_data(self, schedule_data):
        """Define os dados de agenda"""
        self.schedule_data = schedule_data
        self.update_assignments()
        
    def update_header(self):
        """Atualiza o cabeçalho com os dias da semana"""
        # Limpar cabeçalho atual
        for i in reversed(range(self.header_layout.count())):
            item = self.header_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.week_start:
            return
            
        # Adicionar labels para os dias
        for i in range(7):
            date = self.week_start.addDays(i)
            day_widget = QWidget()
            day_layout = QVBoxLayout(day_widget)
            
            # Dia da semana
            weekday_label = QLabel(date.toString("ddd"))
            weekday_label.setAlignment(Qt.AlignCenter)
            day_layout.addWidget(weekday_label)
            
            # Data
            date_label = QLabel(date.toString("dd/MM"))
            date_label.setAlignment(Qt.AlignCenter)
            date_label.setStyleSheet("font-weight: bold;")
            
            # Destacar hoje
            if date == QDate.currentDate():
                date_label.setStyleSheet("font-weight: bold; color: white; background-color: #007bff; border-radius: 10px;")
                
            day_layout.addWidget(date_label)
            
            self.header_layout.addWidget(day_widget, 1)  # Stretch para distribuir igualmente
            
    def update_grid(self):
        """Atualiza a grade com horários e membros da equipe"""
        # Limpar grade atual
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
                
        if not self.week_start or not self.team_members:
            return
            
        # Adicionar cabeçalhos de linha (membros da equipe)
        for row, member in enumerate(self.team_members):
            member_widget = TeamMemberHeaderWidget(member)
            self.grid_layout.addWidget(member_widget, row + 1, 0)  # +1 para deixar espaço para cabeçalho
            
        # Adicionar cabeçalhos de coluna (horários)
        hours_count = self.hours_range[1] - self.hours_range[0] + 1
        for hour_offset in range(hours_count):
            hour = self.hours_range[0] + hour_offset
            hour_label = QLabel(f"{hour:02d}:00")
            hour_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            hour_label.setStyleSheet("padding-right: 5px;")
            self.grid_layout.addWidget(hour_label, 0, hour_offset + 1)  # +1 para deixar espaço para cabeçalho
            
        # Criar células para cada membro/hora/dia
        for row, member in enumerate(self.team_members):
            for day in range(7):
                date = self.week_start.addDays(day)
                
                # Cria um widget de dia que conterá as atribuições
                day_widget = TeamDayScheduleCell(
                    member.id, 
                    QDateTime(date, QTime(0, 0)),
                    self.hours_range
                )
                day_widget.time_slot_clicked.connect(self.handle_time_slot_clicked)
                
                # Posição na grade: cada dia ocupa várias colunas (horas)
                col_start = day * hours_count + 1  # +1 para o cabeçalho
                col_span = hours_count
                
                self.grid_layout.addWidget(day_widget, row + 1, col_start, 1, col_span)
        
        self.update_assignments()
        
    def update_assignments(self):
        """Atualiza as atribuições na grade"""
        if not self.schedule_data or not self.week_start:
            return
            
        # Encontrar todas as células de dia
        for row in range(1, len(self.team_members) + 1):  # +1 para o cabeçalho
            for col in range(7):
                day_widget = None
                col_span = self.hours_range[1] - self.hours_range[0] + 1
                col_start = col * col_span + 1  # +1 para o cabeçalho
                
                # Encontrar o widget de dia na posição
                for i in range(col_start, col_start + col_span):
                    item = self.grid_layout.itemAtPosition(row, i)
                    if item and isinstance(item.widget(), TeamDayScheduleCell):
                        day_widget = item.widget()
                        break
                
                if not day_widget:
                    continue
                
                # Data para este dia
                date = self.week_start.addDays(col)
                
                # Encontrar atribuições para este membro neste dia
                member_id = self.team_members[row - 1].id  # -1 para ajustar pelo cabeçalho
                day_assignments = []
                
                for assignment in self.schedule_data.get(member_id, []):
                    # Verificar se a atribuição é para este dia
                    assignment_date = assignment.start_time.date()
                    if assignment_date == date.toPython():
                        day_assignments.append(assignment)
                
                # Atualizar célula com atribuições
                day_widget.set_assignments(day_assignments)
```

## 5. Geração de Relatório PDF Profissional

### Classe de Geração de Relatórios:

```python
class PDFReport:
    """Gerador de relatórios PDF profissionais usando ReportLab"""
    
    def __init__(self, title, page_size=A4, margin=0.5*inch):
        """Inicializa o gerador de relatórios."""
        self.title = title
        self.page_size = page_size
        self.margin = margin
        self.width, self.height = self.page_size
        self.content_width = self.width - 2*self.margin
        self.content_height = self.height - 2*self.margin
        
        # Cores e estilos
        self.colors = {
            "primary": colors.HexColor("#007bff"),
            "secondary": colors.HexColor("#6c757d"),
            "success": colors.HexColor("#28a745"),
            "danger": colors.HexColor("#dc3545"),
            "warning": colors.HexColor("#ffc107"),
            "info": colors.HexColor("#17a2b8"),
            "light": colors.HexColor("#f8f9fa"),
            "dark": colors.HexColor("#343a40"),
            "title": colors.HexColor("#212529"),
            "text": colors.HexColor("#495057"),
            "border": colors.HexColor("#dee2e6")
        }
        
        # Estilos para parágrafos
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name='Heading1',
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=self.colors["primary"],
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='Heading2',
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=self.colors["secondary"],
            spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='Normal',
            fontName='Helvetica',
            fontSize=10,
            textColor=self.colors["text"],
            spaceAfter=8
        ))
        self.styles.add(ParagraphStyle(
            name='Small',
            fontName='Helvetica',
            fontSize=8,
            textColor=self.colors["secondary"],
            spaceAfter=6
        ))
        
        # Inicializar documento
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer, 
            pagesize=self.page_size,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        self.elements = []
    
    def add_cover_page(self, logo_path=None, subtitle=None, description=None):
        """Adiciona uma página de capa ao relatório."""
        # Estilo para título da capa
        cover_title_style = ParagraphStyle(
            name='CoverTitle',
            fontName='Helvetica-Bold',
            fontSize=24,
            alignment=TA_CENTER,
            textColor=self.colors["primary"],
            spaceAfter=20
        )
        
        # Estilo para subtítulo da capa
        cover_subtitle_style = ParagraphStyle(
            name='CoverSubtitle',
            fontName='Helvetica',
            fontSize=16,
            alignment=TA_CENTER,
            textColor=self.colors["secondary"],
            spaceAfter=30
        )
        
        # Estilo para descrição da capa
        cover_desc_style = ParagraphStyle(
            name='CoverDescription',
            fontName='Helvetica',
            fontSize=12,
            alignment=TA_CENTER,
            textColor=self.colors["text"],
            spaceAfter=50
        )
        
        # Adicionar logo se fornecido
        if logo_path and os.path.exists(logo_path):
            img = Image(logo_path)
            # Redimensionar logo para no máximo 3 inches de largura
            img_width, img_height = img.wrap(3*inch, 3*inch)
            # Centralizar logo
            img.drawHeight = img_height
            img.drawWidth = img_width
            self.elements.append(img)
            self.elements.append(Spacer(1, 30))
        
        # Adicionar título
        self.elements.append(Paragraph(self.title, cover_title_style))
        
        # Adicionar subtítulo se fornecido
        if subtitle:
            self.elements.append(Paragraph(subtitle, cover_subtitle_style))
            
        # Adicionar descrição se fornecida
        if description:
            self.elements.append(Paragraph(description, cover_desc_style))
        
        # Adicionar data de geração
        date_text = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        self.elements.append(Paragraph(date_text, self.styles["Small"]))
        
        # Quebra de página após a capa
        self.elements.append(PageBreak())
    
    def add_heading(self, text, level=1):
        """Adiciona um título ao relatório."""
        style_name = f"Heading{level}"
        self.elements.append(Paragraph(text, self.styles[style_name]))
    
    def add_paragraph(self, text):
        """Adiciona um parágrafo ao relatório."""
        self.elements.append(Paragraph(text, self.styles["Normal"]))
    
    def add_spacer(self, height):
        """Adiciona um espaçador vertical ao relatório."""
        self.elements.append(Spacer(1, height))
    
    def add_table(self, data, headers=None, colwidths=None, style=None):
        """Adiciona uma tabela ao relatório."""
        table_data = []
        
        # Adicionar cabeçalhos se fornecidos
        if headers:
            header_row = []
            for header in headers:
                header_row.append(Paragraph(header, self.styles["Heading2"]))
            table_data.append(header_row)
        
        # Adicionar dados
        for row in data:
            table_row = []
            for cell in row:
                if isinstance(cell, str):
                    table_row.append(Paragraph(cell, self.styles["Normal"]))
                else:
                    table_row.append(cell)
            table_data.append(table_row)
        
        # Definir larguras de coluna
        if not colwidths:
            colwidths = [self.content_width / len(headers) if headers else len(data[0])] * (len(headers) if headers else len(data[0]))
        
        # Criar tabela
        table = Table(table_data, colWidths=colwidths)
        
        # Aplicar estilo à tabela
        if not style:
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors["light"]),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.colors["dark"]),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, self.colors["border"]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ])
        
        table.setStyle(style)
        self.elements.append(table)
    
    def add_chart(self, data, title, chart_type="bar", width=400, height=200):
        """Adiciona um gráfico ao relatório."""
        drawing = Drawing(width, height)
        
        if chart_type == "bar":
            chart = VerticalBarChart()
            chart.x = 50
            chart.y = 50
            chart.height = height - 100
            chart.width = width - 100
            chart.data = data
            chart.strokeColor = self.colors["primary"]
            chart.valueAxis.valueMin = 0
            chart.valueAxis.valueStep = max(1, max([max(d) for d in data]) // 10)
            chart.categoryAxis.labels.boxAnchor = 'ne'
            chart.categoryAxis.labels.dx = 8
            chart.categoryAxis.labels.dy = -2
            chart.categoryAxis.labels.angle = 30
            chart.bars[0].fillColor = self.colors["primary"]
        
        elif chart_type == "line":
            chart = LineChart()
            chart.x = 50
            chart.y = 50
            chart.height = height - 100
            chart.width = width - 100
            chart.data = data
            chart.strokeColor = self.colors["primary"]
            chart.valueAxis.valueMin = 0
            chart.valueAxis.valueStep = max(1, max([max(d) for d in data]) // 10)
            chart.categoryAxis.labels.boxAnchor = 'ne'
            chart.categoryAxis.labels.dx = 8
            chart.categoryAxis.labels.dy = -2
            chart.categoryAxis.labels.angle = 30
            chart.lines[0].strokeColor = self.colors["primary"]
            chart.lines[0].strokeWidth = 2
        
        elif chart_type == "pie":
            chart = Pie()
            chart.x = width / 2
            chart.y = height / 2
            chart.width = min(width, height) - 100
            chart.height = min(width, height) - 100
            chart.data = data[0]
            chart.labels = [str(d) for d in data[0]]
            chart.slices.strokeWidth = 0.5
            
            # Definir cores para cada fatia
            colors_list = [
                self.colors["primary"],
                self.colors["secondary"],
                self.colors["success"],
                self.colors["danger"],
                self.colors["warning"],
                self.colors["info"]
            ]
            
            for i, slice in enumerate(chart.slices):
                slice.fillColor = colors_list[i % len(colors_list)]
        
        drawing.add(chart)
        
        # Adicionar título do gráfico
        title_style = ParagraphStyle(
            name='ChartTitle',
            fontName='Helvetica-Bold',
            fontSize=12,
            alignment=TA_CENTER,
            textColor=self.colors["secondary"],
            spaceAfter=10
        )
        self.elements.append(Paragraph(title, title_style))
        
        self.elements.append(drawing)
        self.elements.append(Spacer(1, 20))
    
    def add_page_break(self):
        """Adiciona uma quebra de página ao relatório."""
        self.elements.append(PageBreak())
    
    def build(self):
        """Constrói o relatório e retorna o buffer."""
        self.doc.build(
            self.elements,
            onFirstPage=self._header_footer,
            onLaterPages=self._header_footer
        )
        self.buffer.seek(0)
        return self.buffer
    
    def save(self, filename):
        """Salva o relatório em um arquivo."""
        buffer = self.build()
        with open(filename, 'wb') as f:
            f.write(buffer.read())
    
    def _header_footer(self, canvas, doc):
        """Adiciona cabeçalho e rodapé a cada página."""
        canvas.saveState()
        
        # Cabeçalho - somente para páginas após a capa
        if doc.page > 1:
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(self.colors["secondary"])
            canvas.drawString(self.margin, self.height - 20, self.title)
            canvas.line(self.margin, self.height - 30, self.width - self.margin, self.height - 30)
        
        # Rodapé
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(self.colors["secondary"])
        canvas.drawRightString(
            self.width - self.margin, 
            20,
            f"Página {doc.page} de {doc.pageTemplate.beforeDrawPage}"
        )
        canvas.drawString(
            self.margin,
            20,
            f"GoVideo | Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        
        canvas.line(self.margin, 30, self.width - self.margin, 30)
        canvas.restoreState()
```

### Implementação do Gerador de Relatórios de Evento:

```python
class EventReportGenerator:
    """Gerador de relatórios de eventos completos"""
    
    def __init__(self, session, event_id):
        self.session = session
        self.event_id = event_id
        self.event = self.session.query(Event).get(event_id)
        if not self.event:
            raise ValueError(f"Evento com ID {event_id} não encontrado")
    
    def generate_complete_report(self, output_path, logo_path=None, include_charts=True):
        """Gera um relatório completo do evento em PDF"""
        if not self.event:
            return False
            
        # Criar relatório
        report_title = f"Relatório de Evento: {self.event.name}"
        report = PDFReport(report_title)
        
        # Página de capa
        report.add_cover_page(
            logo_path=logo_path,
            subtitle=f"{self.event.location} • {self.event.start_date.strftime('%d/%m/%Y')} a {self.event.end_date.strftime('%d/%m/%Y')}",
            description=self.event.description
        )
        
        # Sumário Executivo
        report.add_heading("Sumário Executivo", level=1)
        report.add_paragraph(f"Este relatório apresenta um resumo completo do evento {self.event.name}, realizado em {self.event.location} entre {self.event.start_date.strftime('%d/%m/%Y')} e {self.event.end_date.strftime('%d/%m/%Y')}.")
        
        # Dados gerais em formato de tabela
        event_info = [
            ["Cliente:", self.event.client.name if hasattr(self.event, 'client') and self.event.client else "N/A"],
            ["Local:", self.event.location],
            ["Data de início:", self.event.start_date.strftime("%d/%m/%Y")],
            ["Data de término:", self.event.end_date.strftime("%d/%m/%Y")],
            ["Status:", self.event.status],
            ["Responsável:", self.event.coordinator.name if hasattr(self.event, 'coordinator') and self.event.coordinator else "N/A"]
        ]
        
        report.add_table(
            event_info, 
            colwidths=[100, 400],
            style=TableStyle([
                ('GRID', (0, 0), (-1, -1), 0, colors.white),  # Sem bordas
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),  # Alinhar à direita primeira coluna
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),   # Alinhar à esquerda segunda coluna
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Negrito na primeira coluna
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ])
        )
        
        report.add_spacer(20)
        
        # Estatísticas do evento
        if include_charts:
            report.add_heading("Estatísticas do Evento", level=2)
            
            # Status das atividades
            activity_stats = self._get_activity_stats()
            if activity_stats:
                report.add_chart(
                    [activity_stats["values"]], 
                    "Status das Atividades",
                    chart_type="pie", 
                    width=400, 
                    height=300
                )
                
            # Status das entregas
            delivery_stats = self._get_delivery_stats()
            if delivery_stats:
                report.add_chart(
                    [delivery_stats["values"]], 
                    "Status das Entregas",
                    chart_type="pie", 
                    width=400, 
                    height=300
                )
                
            report.add_page_break()
        
        # Seção de Atividades
        report.add_heading("Programação e Cronograma", level=1)
        report.add_paragraph("Abaixo estão listadas todas as atividades programadas para o evento, com seus respectivos status, responsáveis e localizações.")
        
        activities = self._get_activities()
        if activities:
            activity_data = []
            for activity in activities:
                activity_data.append([
                    activity.start_time.strftime("%d/%m %H:%M"),
                    activity.name,
                    activity.stage.name if hasattr(activity, 'stage') and activity.stage else "N/A",
                    activity.responsible.name if hasattr(activity, 'responsible') and activity.responsible else "N/A",
                    activity.status
                ])
            
            report.add_table(
                activity_data,
                headers=["Horário", "Atividade", "Local", "Responsável", "Status"]
            )
        else:
            report.add_paragraph("Nenhuma atividade registrada para este evento.")
            
        report.add_page_break()
        
        # Seção de Entregas
        report.add_heading("Entregas e Produtos Finais", level=1)
        report.add_paragraph("Esta seção apresenta as entregas associadas ao evento, incluindo status de produção e prazos.")
        
        deliveries = self._get_deliveries()
        if deliveries:
            delivery_data = []
            for delivery in deliveries:
                deadline = delivery.deadline.strftime("%d/%m/%Y") if delivery.deadline else "Sem prazo"
                delivery_data.append([
                    delivery.title,
                    delivery.type if hasattr(delivery, 'type') else "N/A",
                    delivery.editor.name if hasattr(delivery, 'editor') and delivery.editor else "N/A",
                    deadline,
                    delivery.status,
                    f"{int(delivery.progress * 100)}%" if delivery.progress is not None else "N/A"
                ])
            
            report.add_table(
                delivery_data,
                headers=["Título", "Tipo", "Editor", "Prazo", "Status", "Progresso"]
            )
        else:
            report.add_paragraph("Nenhuma entrega registrada para este evento.")
            
        report.add_page_break()
        
        # Seção de Equipe
        report.add_heading("Equipe e Atuação", level=1)
        report.add_paragraph("Detalhes sobre a equipe designada para o evento e suas atribuições.")
        
        team_assignments = self._get_team_assignments()
        if team_assignments:
            team_data = []
            for assignment in team_assignments:
                team_data.append([
                    assignment.team_member.name if hasattr(assignment, 'team_member') and assignment.team_member else "N/A",
                    assignment.role.name if hasattr(assignment, 'role') and assignment.role else "N/A",
                    assignment.start_time.strftime("%d/%m %H:%M") if assignment.start_time else "N/A",
                    assignment.end_time.strftime("%d/%m %H:%M") if assignment.end_time else "N/A",
                    assignment.location if hasattr(assignment, 'location') else "N/A"
                ])
            
            report.add_table(
                team_data,
                headers=["Membro", "Função", "Início", "Término", "Localização"]
            )
        else:
            report.add_paragraph("Nenhuma atribuição de equipe registrada para este evento.")
            
        # Seção de Ativações de Patrocinadores
        report.add_page_break()
        report.add_heading("Ativações de Patrocinadores", level=1)
        report.add_paragraph("Esta seção detalha as ativações de patrocinadores realizadas durante o evento.")
        
        activations = self._get_sponsor_activations()
        if activations:
            activation_data = []
            for activation in activations:
                activation_data.append([
                    activation.sponsor.name if hasattr(activation, 'sponsor') and activation.sponsor else "N/A",
                    activation.activation_type.name if hasattr(activation, 'activation_type') and activation.activation_type else "N/A",
                    activation.scheduled_time.strftime("%d/%m %H:%M") if activation.scheduled_time else "N/A",
                    activation.status,
                    "Sim" if activation.evidence_path else "Não",
                    activation.notes[:50] + "..." if activation.notes and len(activation.notes) > 50 else (activation.notes or "")
                ])
            
            report.add_table(
                activation_data,
                headers=["Patrocinador", "Tipo de Ativação", "Horário", "Status", "Evidência", "Observações"]
            )
        else:
            report.add_paragraph("Nenhuma ativação de patrocinador registrada para este evento.")
            
        # Notas e observações finais
        report.add_page_break()
        report.add_heading("Observações Finais", level=1)
        report.add_paragraph("Observações gerais sobre o evento, lições aprendidas e recomendações para futuros eventos similares.")
        
        if self.event.notes:
            report.add_paragraph(self.event.notes)
        else:
            report.add_paragraph("Nenhuma observação registrada para este evento.")
        
        # Salvar o relatório
        report.save(output_path)
        return True
    
    def _get_activities(self):
        """Recupera atividades do evento"""
        return self.session.query(Activity).filter(
            Activity.event_id == self.event_id
        ).order_by(Activity.start_time).all()
    
    def _get_deliveries(self):
        """Recupera entregas do evento"""
        return self.session.query(Delivery).filter(
            Delivery.event_id == self.event_id
        ).all()
    
    def _get_team_assignments(self):
        """Recupera atribuições de equipe do evento"""
        return self.session.query(TeamAssignment).filter(
            TeamAssignment.event_id == self.event_id
        ).order_by(TeamAssignment.start_time).all()
    
    def _get_sponsor_activations(self):
        """Recupera ativações de patrocinadores do evento"""
        # Primeiro, encontrar todas as atividades do evento
        activity_ids = [a.id for a in self._get_activities()]
        
        # Então, encontrar ativações relacionadas a essas atividades
        return self.session.query(Activation).filter(
            Activation.activity_id.in_(activity_ids)
        ).order_by(Activation.scheduled_time).all()
    
    def _get_activity_stats(self):
        """Calcula estatísticas de atividades"""
        activities = self._get_activities()
        if not activities:
            return None
            
        status_count = {}
        for activity in activities:
            status = activity.status or "unknown"
            if status not in status_count:
                status_count[status] = 0
            status_count[status] += 1
        
        labels = list(status_count.keys())
        values = list(status_count.values())
        
        return {"labels": labels, "values": values}
    
    def _get_delivery_stats(self):
        """Calcula estatísticas de entregas"""
        deliveries = self._get_deliveries()
        if not deliveries:
            return None
            
        status_count = {}
        for delivery in deliveries:
            status = delivery.status or "unknown"
            if status not in status_count:
                status_count[status] = 0
            status_count[status] += 1
        
        labels = list(status_count.keys())
        values = list(status_count.values())
        
        return {"labels": labels, "values": values}
```

### Interface de Geração de Relatórios:

```python
class ReportGeneratorDialog(QDialog):
    """Interface para geração de relatórios personalizáveis"""
    
    def __init__(self, session, event_id, parent=None):
        super().__init__(parent)
        self.session = session
        self.event_id = event_id
        self.event = self.session.query(Event).get(event_id)
        
        self.setWindowTitle("Gerador de Relatórios")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Título e descrição
        title_label = QLabel(f"Relatório: {self.event.name}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        subtitle_label = QLabel(f"{self.event.location} • {self.event.start_date.strftime('%d/%m/%Y')} a {self.event.end_date.strftime('%d/%m/%Y')}")
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(10)
        
        # Seções para incluir no relatório
        sections_group = QGroupBox("Seções para incluir")
        sections_layout = QVBoxLayout(sections_group)
        
        self.include_summary = QCheckBox("Sumário Executivo")
        self.include_summary.setChecked(True)
        sections_layout.addWidget(self.include_summary)
        
        self.include_stats = QCheckBox("Estatísticas e Gráficos")
        self.include_stats.setChecked(True)
        sections_layout.addWidget(self.include_stats)
        
        self.include_activities = QCheckBox("Programação e Cronograma")
        self.include_activities.setChecked(True)
        sections_layout.addWidget(self.include_activities)
        
        self.include_deliveries = QCheckBox("Entregas e Produtos Finais")
        self.include_deliveries.setChecked(True)
        sections_layout.addWidget(self.include_deliveries)
        
        self.include_team = QCheckBox("Equipe e Atuação")
        self.include_team.setChecked(True)
        sections_layout.addWidget(self.include_team)
        
        self.include_sponsors = QCheckBox("Ativações de Patrocinadores")
        self.include_sponsors.setChecked(True)
        sections_layout.addWidget(self.include_sponsors)
        
        self.include_notes = QCheckBox("Observações Finais")
        self.include_notes.setChecked(True)
        sections_layout.addWidget(self.include_notes)
        
        layout.addWidget(sections_group)
        
        # Opções de formato
        format_group = QGroupBox("Opções de Formato")
        format_layout = QGridLayout(format_group)
        
        format_layout.addWidget(QLabel("Tipo de Relatório:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItem("PDF", "pdf")
        self.format_combo.addItem("Excel (Apenas Dados)", "xlsx")
        format_layout.addWidget(self.format_combo, 0, 1)
        
        format_layout.addWidget(QLabel("Incluir Logo:"), 1, 0)
        
        logo_layout = QHBoxLayout()
        self.logo_path_edit = QLineEdit()
        self.logo_path_edit.setPlaceholderText("Caminho para o arquivo de logo")
        logo_layout.addWidget(self.logo_path_edit)
        
        self.logo_browse_btn = QPushButton("Procurar...")
        self.logo_browse_btn.clicked.connect(self.browse_logo)
        logo_layout.addWidget(self.logo_browse_btn)
        
        format_layout.addLayout(logo_layout, 1, 1)
        
        layout.addWidget(format_group)
        
        # Opções avançadas
        self.advanced_btn = QPushButton("Opções Avançadas")
        self.advanced_btn.setCheckable(True)
        self.advanced_btn.clicked.connect(self.toggle_advanced_options)
        layout.addWidget(self.advanced_btn)
        
        self.advanced_group = QGroupBox("Opções Avançadas")
        self.advanced_group.setVisible(False)
        advanced_layout = QFormLayout(self.advanced_group)
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItem("A4", "A4")
        self.page_size_combo.addItem("Carta (Letter)", "LETTER")
        self.page_size_combo.addItem("A3", "A3")
        advanced_layout.addRow("Tamanho da Página:", self.page_size_combo)
        
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItem("Retrato", "portrait")
        self.orientation_combo.addItem("Paisagem", "landscape")
        advanced_layout.addRow("Orientação:", self.orientation_combo)
        
        self.include_page_numbers = QCheckBox()
        self.include_page_numbers.setChecked(True)
        advanced_layout.addRow("Incluir Números de Página:", self.include_page_numbers)
        
        self.include_toc = QCheckBox()
        self.include_toc.setChecked(True)
        advanced_layout.addRow("Incluir Sumário:", self.include_toc)
        
        layout.addWidget(self.advanced_group)
        
        # Destino do relatório
        output_group = QGroupBox("Destino do Relatório")
        output_layout = QVBoxLayout(output_group)
        
        # Salvar como arquivo
        self.save_file_radio = QRadioButton("Salvar como arquivo")
        self.save_file_radio.setChecked(True)
        output_layout.addWidget(self.save_file_radio)
        
        file_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Caminho para salvar o relatório")
        file_layout.addWidget(self.output_path_edit)
        
        self.output_browse_btn = QPushButton("Procurar...")
        self.output_browse_btn.clicked.connect(self.browse_output)
        file_layout.addWidget(self.output_browse_btn)
        
        output_layout.addLayout(file_layout)
        
        # Enviar por e-mail
        self.email_radio = QRadioButton("Enviar por e-mail")
        output_layout.addWidget(self.email_radio)
        
        email_layout = QHBoxLayout()
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Endereço de e-mail")
        self.email_edit.setEnabled(False)
        email_layout.addWidget(self.email_edit)
        
        output_layout.addLayout(email_layout)
        
        # Conectar alteração de opção
        self.save_file_radio.toggled.connect(self.toggle_output_option)
        self.email_radio.toggled.connect(self.toggle_output_option)
        
        layout.addWidget(output_group)
        
        # Botões de ação
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.generate_report)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def toggle_advanced_options(self, checked):
        """Mostra/oculta opções avançadas"""
        self.advanced_group.setVisible(checked)
        self.adjustSize()
    
    def toggle_output_option(self, checked):
        """Alterna entre opções de saída"""
        self.output_path_edit.setEnabled(self.save_file_radio.isChecked())
        self.output_browse_btn.setEnabled(self.save_file_radio.isChecked())
        self.email_edit.setEnabled(self.email_radio.isChecked())
    
    def browse_logo(self):
        """Abre diálogo para selecionar logo"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Logo",
            "",
            "Imagens (*.png *.jpg *.jpeg)"
        )
        
        if file_name:
            self.logo_path_edit.setText(file_name)
    
    def browse_output(self):
        """Abre diálogo para selecionar destino do arquivo"""
        file_format = self.format_combo.currentData()
        file_filter = "Arquivos PDF (*.pdf)" if file_format == "pdf" else "Arquivos Excel (*.xlsx)"
        file_extension = ".pdf" if file_format == "pdf" else ".xlsx"
        
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Relatório",
            f"Relatório_{self.event.name.replace(' ', '_')}{file_extension}",
            file_filter
        )
        
        if file_name:
            self.output_path_edit.setText(file_name)
    
    def generate_report(self):
        """Gera o relatório com as opções selecionadas"""
        # Validar entradas
        if self.save_file_radio.isChecked() and not self.output_path_edit.text():
            QMessageBox.warning(
                self,
                "Caminho Inválido",
                "Por favor, selecione um destino para o relatório."
            )
            return
            
        if self.email_radio.isChecked() and not self.email_edit.text():
            QMessageBox.warning(
                self,
                "E-mail Inválido",
                "Por favor, informe um endereço de e-mail válido."
            )
            return
        
        # Configurar gerador de relatório
        report_generator = EventReportGenerator(self.session, self.event_id)
        
        # Caminho de saída
        output_path = self.output_path_edit.text() if self.save_file_radio.isChecked() else tempfile.mktemp(suffix=".pdf")
        
        # Mostrar diálogo de progresso
        progress_dialog = QProgressDialog("Gerando relatório...", "Cancelar", 0, 100, self)
        progress_dialog.setWindowTitle("Gerando Relatório")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setValue(0)
        progress_dialog.show()
        
        # Gerar relatório em thread separada para não travar a UI
        def generate_thread():
            try:
                # Atualizar progresso
                self.update_progress_signal.emit(10)
                
                # Gerar relatório
                success = report_generator.generate_complete_report(
                    output_path=output_path,
                    logo_path=self.logo_path_edit.text() if self.logo_path_edit.text() else None,
                    include_charts=self.include_stats.isChecked()
                )
                
                self.update_progress_signal.emit(80)
                
                # Se for para enviar por e-mail
                if success and self.email_radio.isChecked():
                    # Implementar envio de e-mail aqui
                    self.send_email(output_path, self.email_edit.text())
                
                self.update_progress_signal.emit(100)
                
                # Mostrar resultado
                if success:
                    self.report_finished_signal.emit(True, output_path)
                else:
                    self.report_finished_signal.emit(False, "Erro ao gerar relatório")
            except Exception as e:
                self.report_finished_signal.emit(False, str(e))
        
        # Criar sinais para comunicação entre threads
        self.update_progress_signal = Signal(int)
        self.update_progress_signal.connect(progress_dialog.setValue)
        
        self.report_finished_signal = Signal(bool, str)
        self.report_finished_signal.connect(self.handle_report_finished)
        
        # Iniciar thread
        threading.Thread(target=generate_thread).start()
    
    def handle_report_finished(self, success, message):
        """Manipula o resultado da geração do relatório"""
        if success:
            if self.save_file_radio.isChecked():
                QMessageBox.information(
                    self,
                    "Relatório Gerado",
                    f"O relatório foi gerado com sucesso em:\n{message}"
                )
                # Abrir o arquivo gerado
                QDesktopServices.openUrl(QUrl.fromLocalFile(message))
            else:
                QMessageBox.information(
                    self,
                    "Relatório Enviado",
                    f"O relatório foi enviado com sucesso para {self.email_edit.text()}"
                )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Erro",
                f"Ocorreu um erro ao gerar o relatório:\n{message}"
            )
    
    def send_email(self, file_path, email):
        """Envia o relatório por e-mail"""
        # Esta é uma implementação simplificada
        # Uma implementação completa usaria bibliotecas como smtplib
        pass
```

## 6. Biblioteca de Assets com Preview e Drag & Drop

### Implementação da Biblioteca de Assets Avançada:

```python
class AssetLibrary(QWidget):
    """Biblioteca avançada de assets com preview e drag & drop"""
    
    asset_selected = Signal(object)  # Asset object
    asset_double_clicked = Signal(object)  # Asset object
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.thumbnail_cache = {}  # Cache de miniaturas para melhor desempenho
        self.current_filter = {}
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Barra de ferramentas
        toolbar = QToolBar()
        
        # Ações da barra de ferramentas
        self.import_action = QAction(QIcon(":/icons/import.png"), "Importar", self)
        self.import_action.triggered.connect(self.import_assets)
        toolbar.addAction(self.import_action)
        
        self.delete_action = QAction(QIcon(":/icons/delete.png"), "Excluir", self)
        self.delete_action.triggered.connect(self.delete_selected)
        toolbar.addAction(self.delete_action)
        
        toolbar.addSeparator()
        
        self.filter_action = QAction(QIcon(":/icons/filter.png"), "Filtrar", self)
        self.filter_action.triggered.connect(self.show_filters)
        toolbar.addAction(self.filter_action)
        
        self.view_action = QAction(QIcon(":/icons/view.png"), "Visualização", self)
        view_menu = QMenu()
        
        self.icon_view_action = QAction("Ícones", self)
        self.icon_view_action.setCheckable(True)
        self.icon_view_action.setChecked(True)
        self.icon_view_action.triggered.connect(lambda: self.change_view_mode(QListView.IconMode))
        view_menu.addAction(self.icon_view_action)
        
        self.list_view_action = QAction("Lista", self)
        self.list_view_action.setCheckable(True)
        self.list_view_action.triggered.connect(lambda: self.change_view_mode(QListView.ListMode))
        view_menu.addAction(self.list_view_action)
        
        self.view_action.setMenu(view_menu)
        toolbar.addAction(self.view_action)
        
        toolbar.addSeparator()
        
        self.refresh_action = QAction(QIcon(":/icons/refresh.png"), "Atualizar", self)
        self.refresh_action.triggered.connect(self.refresh_assets)
        toolbar.addAction(self.refresh_action)
        
        layout.addWidget(toolbar)
        
        # Barra de busca
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Digite para buscar assets...")
        self.search_edit.textChanged.connect(self.filter_assets)
        search_layout.addWidget(self.search_edit)
        
        self.clear_search_btn = QPushButton("✕")
        self.clear_search_btn.setMaximumWidth(30)
        self.clear_search_btn.clicked.connect(lambda: self.search_edit.setText(""))
        search_layout.addWidget(self.clear_search_btn)
        
        layout.addLayout(search_layout)
        
        # Splitter para filtros e visualização
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Painel de filtros
        self.filter_widget = AssetFilterWidget(self.session)
        self.filter_widget.filters_changed.connect(self.apply_filters)
        self.splitter.addWidget(self.filter_widget)
        
        # Visualização de assets
        self.assets_view = QListView()
        self.assets_view.setViewMode(QListView.IconMode)
        self.assets_view.setIconSize(QSize(128, 128))
        self.assets_view.setGridSize(QSize(160, 180))
        self.assets_view.setResizeMode(QListView.Adjust)
        self.assets_view.setMovement(QListView.Static)
        self.assets_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.assets_view.setDragEnabled(True)
        self.assets_view.setAcceptDrops(True)
        self.assets_view.setDropIndicatorShown(True)
        self.assets_view.setDragDropMode(QAbstractItemView.DragDrop)
        self.assets_view.setWordWrap(True)
        
        # Modelo de dados para os assets
        self.model = AssetListModel(self.session)
        self.assets_view.setModel(self.model)
        
        # Conectar sinais
        self.assets_view.selectionModel().selectionChanged.connect(self.handle_selection_changed)
        self.assets_view.doubleClicked.connect(self.handle_double_click)
        
        self.splitter.addWidget(self.assets_view)
        
        # Definir proporções iniciais do splitter
        self.splitter.setSizes([200, 600])
        
        layout.addWidget(self.splitter)
        
        # Painel de detalhes do asset selecionado
        self.details_widget = AssetDetailWidget()
        self.details_widget.setVisible(False)
        layout.addWidget(self.details_widget)
        
        # Carregar assets iniciais
        self.refresh_assets()
    
    def change_view_mode(self, mode):
        """Altera o modo de visualização"""
        self.assets_view.setViewMode(mode)
        
        if mode == QListView.IconMode:
            self.assets_view.setIconSize(QSize(128, 128))
            self.assets_view.setGridSize(QSize(160, 180))
            self.assets_view.setSpacing(10)
            self.icon_view_action.setChecked(True)
            self.list_view_action.setChecked(False)
        else:
            self.assets_view.setIconSize(QSize(48, 48))
            self.assets_view.setGridSize(QSize(0, 0))
            self.assets_view.setSpacing(2)
            self.icon_view_action.setChecked(False)
            self.list_view_action.setChecked(True)
    
    def refresh_assets(self):
        """Atualiza a lista de assets a partir do banco de dados"""
        self.model.load_assets(self.current_filter)
        
    def import_assets(self):
        """Abre diálogo para importar novos assets"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Importar Assets",
            "",
            "Arquivos de Mídia (*.jpg *.jpeg *.png *.gif *.mp4 *.mov *.avi *.mp3 *.wav *.doc *.docx *.pdf)"
        )
        
        if not files:
            return
        
        progress = QProgressDialog("Importando assets...", "Cancelar", 0, len(files), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        for i, file_path in enumerate(files):
            progress.setValue(i)
            QApplication.processEvents()  # Manter UI responsiva
            
            if progress.wasCanceled():
                break
            
            try:
                self.import_asset(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao importar {os.path.basename(file_path)}: {e}")
        
        progress.setValue(len(files))
        self.refresh_assets()
    
    def import_asset(self, file_path):
        """Importa um único asset para a biblioteca"""
        # Determinar o tipo de arquivo
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Determinar o tipo de asset
        asset_type = None
        if ext in ['.jpg', '.jpeg', '.png', '.gif']:
            asset_type = "image"
        elif ext in ['.mp4', '.mov', '.avi']:
            asset_type = "video"
        elif ext in ['.mp3', '.wav', '.aac']:
            asset_type = "audio"
        elif ext in ['.doc', '.docx', '.pdf', '.txt']:
            asset_type = "document"
        else:
            asset_type = "other"
        
        # Nome do arquivo
        file_name = os.path.basename(file_path)
        
        # Diretório para armazenar assets
        assets_dir = os.path.join(os.path.expanduser("~"), ".govideo", "assets")
        os.makedirs(assets_dir, exist_ok=True)
        
        # Subdiretório por tipo
        type_dir = os.path.join(assets_dir, asset_type)
        os.makedirs(type_dir, exist_ok=True)
        
        # Gerar nome de arquivo único
        dest_file = os.path.join(type_dir, file_name)
        if os.path.exists(dest_file):
            # Se já existe, adicionar timestamp
            base_name, ext = os.path.splitext(file_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_file = os.path.join(type_dir, f"{base_name}_{timestamp}{ext}")
        
        # Copiar arquivo
        shutil.copy2(file_path, dest_file)
        
        # Gerar miniatura para imagens e vídeos
        thumbnail_path = None
        if asset_type in ["image", "video"]:
            thumbnail_dir = os.path.join(assets_dir, "thumbnails")
            os.makedirs(thumbnail_dir, exist_ok=True)
            
            base_name, ext = os.path.splitext(os.path.basename(dest_file))
            thumbnail_path = os.path.join(thumbnail_dir, f"{base_name}_thumb.jpg")
            
            if asset_type == "image":
                # Redimensionar imagem para miniatura
                img = Image.open(dest_file)
                img.thumbnail((256, 256))
                img.save(thumbnail_path, "JPEG")
            else:
                # Extrair frame do vídeo para miniatura
                self._create_video_thumbnail(dest_file, thumbnail_path)
        
        # Criar registro no banco de dados
        asset = Asset(
            file_path=dest_file,
            thumbnail_path=thumbnail_path,
            type=asset_type,
            name=file_name,
            size=os.path.getsize(dest_file),
            upload_date=datetime.now()
        )
        
        self.session.add(asset)
        self.session.commit()
        
        return asset
    
    def _create_video_thumbnail(self, video_path, thumbnail_path):
        """Cria uma miniatura a partir de um vídeo usando OpenCV"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False
            
            # Ler o primeiro frame
            ret, frame = cap.read()
            if not ret:
                return False
            
            # Redimensionar frame
            height, width = frame.shape[:2]
            max_dim = 256
            if height > width:
                new_height = max_dim
                new_width = int(width * (max_dim / height))
            else:
                new_width = max_dim
                new_height = int(height * (max_dim / width))
            
            frame = cv2.resize(frame, (new_width, new_height))
            
            # Salvar como JPEG
            cv2.imwrite(thumbnail_path, frame)
            
            cap.release()
            return True
        except Exception as e:
            logger.error(f"Erro ao criar thumbnail do vídeo {video_path}: {e}")
            return False
    
    def delete_selected(self):
        """Exclui os assets selecionados"""
        selected_indexes = self.assets_view.selectionModel().selectedIndexes()
        if not selected_indexes:
            return
        
        count = len(selected_indexes)
        confirm = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir {count} asset{'s' if count > 1 else ''}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
        
        assets_to_delete = []
        for index in selected_indexes:
            asset = self.model.data(index, Qt.UserRole)
            if asset:
                assets_to_delete.append(asset)
        
        for asset in assets_to_delete:
            # Excluir arquivos físicos
            try:
                if os.path.exists(asset.file_path):
                    os.remove(asset.file_path)
                    
                if asset.thumbnail_path and os.path.exists(asset.thumbnail_path):
                    os.remove(asset.thumbnail_path)
            except Exception as e:
                logger.error(f"Erro ao excluir arquivos do asset {asset.id}: {e}")
            
            # Excluir do banco de dados
            self.session.delete(asset)
        
        self.session.commit()
        self.refresh_assets()
    
    def show_filters(self):
        """Mostra ou esconde o painel de filtros"""
        is_visible = self.filter_widget.isVisible()
        self.filter_widget.setVisible(not is_visible)
        if not is_visible:
            # Ajustar tamanhos do splitter
            sizes = self.splitter.sizes()
            sizes[0] = 200  # Largura do painel de filtros
            self.splitter.setSizes(sizes)
    
    def filter_assets(self):
        """Filtra assets com base no texto de busca"""
        search_text = self.search_edit.text()
        self.current_filter["search"] = search_text
        self.refresh_assets()
    
    def apply_filters(self, filters):
        """Aplica filtros do painel de filtros"""
        self.current_filter.update(filters)
        self.refresh_assets()
    
    def handle_selection_changed(self):
        """Manipula a alteração de seleção de assets"""
        indexes = self.assets_view.selectionModel().selectedIndexes()
        if len(indexes) == 1:
            asset = self.model.data(indexes[0], Qt.UserRole)
            self.details_widget.set_asset(asset)
            self.details_widget.setVisible(True)
            self.asset_selected.emit(asset)
        else:
            self.details_widget.setVisible(False)
    
    def handle_double_click(self, index):
        """Manipula o duplo clique em um asset"""
        asset = self.model.data(index, Qt.UserRole)
        if asset:
            self.asset_double_clicked.emit(asset)
    
    def dragEnterEvent(self, event):
        """Manipula entrada de drag & drop"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Manipula soltura de arquivos via drag & drop"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            files = [url.toLocalFile() for url in urls]
            
            # Importar arquivos
            progress = QProgressDialog("Importando assets...", "Cancelar", 0, len(files), self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            for i, file_path in enumerate(files):
                progress.setValue(i)
                QApplication.processEvents()  # Manter UI responsiva
                
                if progress.wasCanceled():
                    break
                
                if os.path.isfile(file_path):
                    try:
                        self.import_asset(file_path)
                    except Exception as e:
                        QMessageBox.warning(self, "Erro", f"Erro ao importar {os.path.basename(file_path)}: {e}")
            
            progress.setValue(len(files))
            self.refresh_assets()
            event.acceptProposedAction()
```

### Modelo de Dados para Assets:

```python
class AssetListModel(QAbstractListModel):
    """Modelo de dados para lista de assets"""
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.assets = []
        self.thumbnail_cache = {}
    
    def rowCount(self, parent=QModelIndex()):
        """Retorna o número de linhas (assets)"""
        return len(self.assets)
    
    def data(self, index, role=Qt.DisplayRole):
        """Retorna dados dos assets para diferentes papéis"""
        if not index.isValid() or index.row() >= len(self.assets):
            return None
        
        asset = self.assets[index.row()]
        
        if role == Qt.DisplayRole:
            return asset.name
        elif role == Qt.DecorationRole:
            # Usar cache para melhorar desempenho
            if asset.id in self.thumbnail_cache:
                return self.thumbnail_cache[asset.id]
                
            # Carregar thumbnail ou ícone padrão
            if asset.thumbnail_path and os.path.exists(asset.thumbnail_path):
                pixmap = QPixmap(asset.thumbnail_path)
            elif asset.type == "image" and os.path.exists(asset.file_path):
                pixmap = QPixmap(asset.file_path).scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                # Usar ícone padrão baseado no tipo
                icon_path = self._get_default_icon_path(asset.type)
                pixmap = QPixmap(icon_path)
                
            self.thumbnail_cache[asset.id] = pixmap
            return pixmap
        elif role == Qt.UserRole:
            return asset
        elif role == Qt.ToolTipRole:
            return self._generate_tooltip(asset)
        
        return None
    
    def _get_default_icon_path(self, asset_type):
        """Retorna caminho para ícone padrão baseado no tipo"""
        icons = {
            "image": ":/icons/image.png",
            "video": ":/icons/video.png",
            "audio": ":/icons/audio.png",
            "document": ":/icons/document.png",
            "other": ":/icons/file.png"
        }
        
        return icons.get(asset_type, icons["other"])
    
    def _generate_tooltip(self, asset):
        """Gera um tooltip rico para o asset"""
        # Formatar tamanho
        size = asset.size
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size/1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            size_str = f"{size/(1024*1024):.2f} MB"
        else:
            size_str = f"{size/(1024*1024*1024):.2f} GB"
        
        # Data formatada
        date_str = asset.upload_date.strftime("%d/%m/%Y %H:%M") if asset.upload_date else "N/A"
        
        # Montar tooltip
        tooltip = f"""<html>
        <h3>{asset.name}</h3>
        <p><b>Tipo:</b> {asset.type}</p>
        <p><b>Tamanho:</b> {size_str}</p>
        <p><b>Upload:</b> {date_str}</p>
        <p><b>Caminho:</b> {asset.file_path}</p>
        </html>"""
        
        return tooltip
    
    def flags(self, index):
        """Retorna flags para o item no modelo"""
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled
        return default_flags | Qt.ItemIsDropEnabled
    
    def mimeTypes(self):
        """Tipos MIME suportados para drag & drop"""
        return ["application/x-asset", "text/uri-list"]
    
    def mimeData(self, indexes):
        """Prepara dados MIME para drag & drop"""
        mime_data = QMimeData()
        
        if not indexes:
            return mime_data
        
        # Serializar assets selecionados
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.WriteOnly)
        
        assets = []
        for index in indexes:
            if index.isValid():
                assets.append(self.assets[index.row()])
        
        # Serializar IDs dos assets
        stream.writeInt(len(assets))
        for asset in assets:
            stream.writeInt(asset.id)
        
        mime_data.setData("application/x-asset", encoded_data)
        
        # Adicionar URLs para compatibilidade com outras aplicações
        urls = []
        for asset in assets:
            urls.append(QUrl.fromLocalFile(asset.file_path))
        
        if urls:
            mime_data.setUrls(urls)
        
        return mime_data
    
    def load_assets(self, filters=None):
        """Carrega assets do banco de dados com filtros opcionais"""
        query = self.session.query(Asset)
        
        if filters:
            # Filtro por texto de busca
            if "search" in filters and filters["search"]:
                search_text = filters["search"]
                query = query.filter(Asset.name.ilike(f"%{search_text}%"))
            
            # Filtro por tipo
            if "types" in filters and filters["types"]:
                query = query.filter(Asset.type.in_(filters["types"]))
            
            # Filtro por data de upload
            if "date_from" in filters and filters["date_from"]:
                query = query.filter(Asset.upload_date >= filters["date_from"])
                
            if "date_to" in filters and filters["date_to"]:
                query = query.filter(Asset.upload_date <= filters["date_to"])
                
            # Filtro por tags
            if "tags" in filters and filters["tags"]:
                # Implementação depende de como tags estão modeladas
                pass
        
        # Ordenar por data de upload (mais recentes primeiro)
        query = query.order_by(Asset.upload_date.desc())
        
        # Carregar assets
        self.beginResetModel()
        self.assets = query.all()
        self.endResetModel()
```

### Widget de Detalhes do Asset:

```python
class AssetDetailWidget(QWidget):
    """Widget para exibir detalhes de um asset selecionado"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_asset = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Área de preview
        self.preview_widget = QLabel()
        self.preview_widget.setAlignment(Qt.AlignCenter)
        self.preview_widget.setMinimumSize(250, 200)
        self.preview_widget.setMaximumWidth(300)
        self.preview_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_widget.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(self.preview_widget)
        
        # Detalhes do asset
        details_layout = QVBoxLayout()
        
        # Nome
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nome:"))
        self.name_label = QLineEdit()
        self.name_label.setReadOnly(True)
        name_layout.addWidget(self.name_label)
        details_layout.addLayout(name_layout)
        
        # Outras informações em um formulário
        form_layout = QFormLayout()
        
        self.type_label = QLabel()
        form_layout.addRow("Tipo:", self.type_label)
        
        self.size_label = QLabel()
        form_layout.addRow("Tamanho:", self.size_label)
        
        self.date_label = QLabel()
        form_layout.addRow("Data de upload:", self.date_label)
        
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        form_layout.addRow("Caminho:", self.path_label)
        
        details_layout.addLayout(form_layout)
        
        # Tags
        tags_layout = QHBoxLayout()
        tags_layout.addWidget(QLabel("Tags:"))
        self.tags_edit = QLineEdit()
        tags_layout.addWidget(self.tags_edit)
        
        self.add_tag_btn = QPushButton("Adicionar")
        self.add_tag_btn.clicked.connect(self.add_tags)
        tags_layout.addWidget(self.add_tag_btn)
        
        details_layout.addLayout(tags_layout)
        
        # Lista de tags
        self.tags_list = QListWidget()
        details_layout.addWidget(self.tags_list)
        
        # Ações
        actions_layout = QHBoxLayout()
        
        self.open_btn = QPushButton("Abrir")
        self.open_btn.setIcon(QIcon(":/icons/open.png"))
        self.open_btn.clicked.connect(self.open_asset)
        actions_layout.addWidget(self.open_btn)
        
        self.edit_btn = QPushButton("Editar")
        self.edit_btn.setIcon(QIcon(":/icons/edit.png"))
        self.edit_btn.clicked.connect(self.edit_asset)
        actions_layout.addWidget(self.edit_btn)
        
        self.copy_path_btn = QPushButton("Copiar Caminho")
        self.copy_path_btn.setIcon(QIcon(":/icons/copy.png"))
        self.copy_path_btn.clicked.connect(self.copy_path)
        actions_layout.addWidget(self.copy_path_btn)
        
        details_layout.addLayout(actions_layout)
        details_layout.addStretch()
        
        layout.addLayout(details_layout)
    
    def set_asset(self, asset):
        """Define o asset atual e atualiza a UI"""
        self.current_asset = asset
        
        if not asset:
            self.clear()
            return
        
        # Atualizar nome
        self.name_label.setText(asset.name)
        
        # Atualizar tipo
        self.type_label.setText(asset.type)
        
        # Atualizar tamanho
        size = asset.size
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size/1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            size_str = f"{size/(1024*1024):.2f} MB"
        else:
            size_str = f"{size/(1024*1024*1024):.2f} GB"
        self.size_label.setText(size_str)
        
        # Atualizar data
        self.date_label.setText(asset.upload_date.strftime("%d/%m/%Y %H:%M") if asset.upload_date else "N/A")
        
        # Atualizar caminho
        self.path_label.setText(asset.file_path)
        
        # Atualizar preview
        self.update_preview()
        
        # Atualizar tags
        self.update_tags()
    
    def update_preview(self):
        """Atualiza o preview do asset"""
        if not self.current_asset:
            return
            
        asset = self.current_asset
        
        if asset.type == "image" and os.path.exists(asset.file_path):
            pixmap = QPixmap(asset.file_path)
            pixmap = pixmap.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_widget.setPixmap(pixmap)
        elif asset.type == "video" and os.path.exists(asset.thumbnail_path):
            pixmap = QPixmap(asset.thumbnail_path)
            pixmap = pixmap.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_widget.setPixmap(pixmap)
            
            # Adicionar ícone de play sobre a imagem
            play_icon = QIcon(":/icons/play.png").pixmap(48, 48)
            painter = QPainter(pixmap)
            painter.drawPixmap(
                pixmap.width() // 2 - play_icon.width() // 2,
                pixmap.height() // 2 - play_icon.height() // 2,
                play_icon
            )
            painter.end()
            
            self.preview_widget.setPixmap(pixmap)
        else:
            # Usar ícone padrão baseado no tipo
            icon_path = {
                "image": ":/icons/image.png",
                "video": ":/icons/video.png",
                "audio": ":/icons/audio.png",
                "document": ":/icons/document.png",
                "other": ":/icons/file.png"
            }.get(asset.type, ":/icons/file.png")
            
            pixmap = QPixmap(icon_path).scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_widget.setPixmap(pixmap)
    
    def update_tags(self):
        """Atualiza a lista de tags"""
        self.tags_list.clear()
        
        if not self.current_asset or not hasattr(self.current_asset, "tags"):
            return
            
        for tag in self.current_asset.tags:
            self.tags_list.addItem(tag.name)
    
    def clear(self):
        """Limpa o widget"""
        self.name_label.clear()
        self.type_label.clear()
        self.size_label.clear()
        self.date_label.clear()
        self.path_label.clear()
        self.preview_widget.clear()
        self.tags_list.clear()
        self.tags_edit.clear()
        self.current_asset = None
    
    def add_tags(self):
        """Adiciona tags ao asset atual"""
        if not self.current_asset:
            return
            
        tags_text = self.tags_edit.text().strip()
        if not tags_text:
            return
            
        # Implementação depende de como tags estão modeladas no banco
        self.tags_edit.clear()
        self.update_tags()
    
    def open_asset(self):
        """Abre o asset atual no programa padrão"""
        if not self.current_asset or not os.path.exists(self.current_asset.file_path):
            return
            
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.current_asset.file_path))
    
    def edit_asset(self):
        """Abre diálogo para editar o asset"""
        if not self.current_asset:
            return
            
        # Implementar diálogo de edição aqui
        pass
    
    def copy_path(self):
        """Copia o caminho do asset para a área de transferência"""
        if not self.current_asset:
            return
            
        clipboard = QApplication.clipboard()
        clipboard.setText(self.current_asset.file_path)
        
        # Mostrar feedback
        QToolTip.showText(
            self.copy_path_btn.mapToGlobal(QPoint(0, -30)),
            "Caminho copiado para a área de transferência",
            self.copy_path_btn,
            QRect(),
            2000
        )
```

## 7. Modo Cliente com Permissões

### Sistema de Permissões:

```python
class Permission(Enum):
    """Permissões do sistema"""
    # Permissões gerais
    VIEW_DASHBOARD = "view_dashboard"
    
    # Permissões de evento
    VIEW_EVENT = "view_event"
    CREATE_EVENT = "create_event"
    EDIT_EVENT = "edit_event"
    DELETE_EVENT = "delete_event"
    
    # Permissões de atividades
    VIEW_ACTIVITY = "view_activity"
    CREATE_ACTIVITY = "create_activity"
    EDIT_ACTIVITY = "edit_activity"
    DELETE_ACTIVITY = "delete_activity"
    
    # Permissões de entregas
    VIEW_DELIVERY = "view_delivery"
    CREATE_DELIVERY = "create_delivery"
    EDIT_DELIVERY = "edit_delivery"
    DELETE_DELIVERY = "delete_delivery"
    APPROVE_DELIVERY = "approve_delivery"
    
    # Permissões de equipe
    VIEW_TEAM = "view_team"
    CREATE_TEAM_MEMBER = "create_team_member"
    EDIT_TEAM_MEMBER = "edit_team_member"
    DELETE_TEAM_MEMBER = "delete_team_member"
    ASSIGN_TEAM = "assign_team"
    
    # Permissões de patrocinadores
    VIEW_SPONSOR = "view_sponsor"
    CREATE_SPONSOR = "create_sponsor"
    EDIT_SPONSOR = "edit_sponsor"
    DELETE_SPONSOR = "delete_sponsor"
    
    # Permissões de ativações
    VIEW_ACTIVATION = "view_activation"
    CREATE_ACTIVATION = "create_activation"
    EDIT_ACTIVATION = "edit_activation"
    DELETE_ACTIVATION = "delete_activation"
    APPROVE_ACTIVATION = "approve_activation"
    
    # Permissões de relatórios
    VIEW_REPORT = "view_report"
    CREATE_REPORT = "create_report"
    
    # Permissões de configuração
    VIEW_SETTINGS = "view_settings"
    EDIT_SETTINGS = "edit_settings"
    
    # Permissões de usuários
    VIEW_USER = "view_user"
    CREATE_USER = "create_user"
    EDIT_USER = "edit_user"
    DELETE_USER = "delete_user"
    
    # Permissões de assets
    VIEW_ASSET = "view_asset"
    UPLOAD_ASSET = "upload_asset"
    EDIT_ASSET = "edit_asset"
    DELETE_ASSET = "delete_asset"
```

### Modelo de Dados para Usuário com Permissões:

```python
class Role(Base):
    """Papel/função de usuário no sistema"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    users = relationship("User", back_populates="role")
    
    def has_permission(self, permission):
        """Verifica se o papel tem uma permissão específica"""
        if isinstance(permission, str):
            perm_name = permission
        elif isinstance(permission, Permission):
            perm_name = permission.value
        else:
            raise ValueError("Permissão deve ser uma string ou enum Permission")
            
        return any(p.permission_name == perm_name for p in self.permissions)
    
    def add_permission(self, permission):
        """Adiciona uma permissão ao papel"""
        if isinstance(permission, str):
            perm_name = permission
        elif isinstance(permission, Permission):
            perm_name = permission.value
        else:
            raise ValueError("Permissão deve ser uma string ou enum Permission")
            
        if not any(p.permission_name == perm_name for p in self.permissions):
            perm = RolePermission(role=self, permission_name=perm_name)
            self.permissions.append(perm)
    
    def remove_permission(self, permission):
        """Remove uma permissão do papel"""
        if isinstance(permission, str):
            perm_name = permission
        elif isinstance(permission, Permission):
            perm_name = permission.value
        else:
            raise ValueError("Permissão deve ser uma string ou enum Permission")
            
        to_remove = next((p for p in self.permissions if p.permission_name == perm_name), None)
        if to_remove:
            self.permissions.remove(to_remove)

class RolePermission(Base):
    """Associação entre papel e permissão"""
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    role = relationship("Role", back_populates="permissions")
    
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_name', name='uix_role_permission'),
    )

class User(Base):
    """Usuário do sistema"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    avatar_path = Column(String)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    role = relationship("Role", back_populates="users")
    client = relationship("Client", back_populates="user", uselist=False)
    sponsor = relationship("Sponsor", back_populates="user", uselist=False)
    
    # Propriedades
    @property
    def full_name(self):
        """Nome completo do usuário"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        if parts:
            return " ".join(parts)
        return self.username
    
    @property
    def is_client(self):
        """Verifica se o usuário está associado a um cliente"""
        return self.client is not None
    
    @property
    def is_sponsor(self):
        """Verifica se o usuário está associado a um patrocinador"""
        return self.sponsor is not None
    
    # Métodos de senha
    def set_password(self, password):
        """Define a senha do usuário (hash)"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica a senha do usuário"""
        return check_password_hash(self.password_hash, password)
    
    # Métodos de permissão
    def has_permission(self, permission):
        """Verifica se o usuário tem uma permissão específica"""
        if not self.role:
            return False
        return self.role.has_permission(permission)
    
    def can(self, permission):
        """Alias para has_permission"""
        return self.has_permission(permission)
```

### Middleware de Autenticação e Autorização:

```python
class AuthManager:
    """Gerenciador de autenticação e autorização"""
    
    def __init__(self, session):
        self.session = session
        self.current_user = None
    
    def login(self, username, password):
        """Realiza login de usuário"""
        user = self.session.query(User).filter(User.username == username).first()
        
        if not user or not user.check_password(password):
            return False, "Usuário ou senha inválidos"
            
        if not user.is_active:
            return False, "Conta desativada"
            
        # Atualizar último login
        user.last_login = datetime.utcnow()
        self.session.commit()
        
        self.current_user = user
        return True, "Login realizado com sucesso"
    
    def logout(self):
        """Realiza logout do usuário atual"""
        self.current_user = None
    
    def is_authenticated(self):
        """Verifica se há um usuário autenticado"""
        return self.current_user is not None
    
    def get_user(self):
        """Retorna o usuário atual"""
        return self.current_user
    
    def check_permission(self, permission):
        """Verifica se o usuário atual tem uma permissão específica"""
        if not self.current_user:
            return False
        return self.current_user.has_permission(permission)
    
    def restrict_access(self, permission, owner_field=None, object=None):
        """
        Verifica acesso a um recurso
        :param permission: Permissão necessária
        :param owner_field: Campo que indica propriedade (ex: client_id)
        :param object: Objeto a verificar propriedade
        :return: Tuple (tem_acesso, motivo)
        """
        # Sem usuário logado
        if not self.current_user:
            return False, "Usuário não autenticado"
            
        # Usuário tem permissão direta
        if self.current_user.has_permission(permission):
            return True, "Permissão concedida"
            
        # Verificar propriedade se necessário
        if owner_field and object:
            if hasattr(object, owner_field):
                owner_id = getattr(object, owner_field)
                
                # Cliente acessando seus próprios recursos
                if self.current_user.is_client and self.current_user.client.id == owner_id:
                    return True, "Acesso do proprietário"
                
                # Patrocinador acessando seus próprios recursos
                if self.current_user.is_sponsor and self.current_user.sponsor.id == owner_id:
                    return True, "Acesso do proprietário"
        
        return False, "Acesso negado"
```

### Interface de Login e Seletor de Modo:

```python
class LoginDialog(QDialog):
    """Diálogo de login"""
    
    login_success = Signal(object)  # User object
    
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        
        self.setWindowTitle("Login - GoVideo")
        self.setFixedSize(400, 350)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(":/images/logo.png")
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_label.setAlignment(Qt.AlignCenter)
        else:
            title_label = QLabel("GoVideo")
            title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #007bff;")
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
        
        layout.addWidget(logo_label)
        layout.addSpacing(20)
        
        # Formulário de login
        form_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Usuário")
        form_layout.addRow(QIcon(":/icons/user.png"), self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Senha")
        form_layout.addRow(QIcon(":/icons/lock.png"), self.password_edit)
        
        layout.addLayout(form_layout)
        
        # Opções
        options_layout = QHBoxLayout()
        
        self.remember_check = QCheckBox("Lembrar-me")
        options_layout.addWidget(self.remember_check)
        
        options_layout.addStretch()
        
        self.forgot_btn = QPushButton("Esqueci minha senha")
        self.forgot_btn.setFlat(True)
        self.forgot_btn.setCursor(Qt.PointingHandCursor)
        self.forgot_btn.clicked.connect(self.forgot_password)
        options_layout.addWidget(self.forgot_btn)
        
        layout.addLayout(options_layout)
        layout.addSpacing(20)
        
        # Botão de login
        self.login_btn = QPushButton("Entrar")
        self.login_btn.setStyleSheet("background-color: #007bff; color: white; padding: 10px;")
        self.login_btn.clicked.connect(self.try_login)
        layout.addWidget(self.login_btn)
        
        # Mensagem de erro
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #dc3545;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
        
        # Enter para login
        self.username_edit.returnPressed.connect(self.login_btn.click)
        self.password_edit.returnPressed.connect(self.login_btn.click)
    
    def try_login(self):
        """Tenta realizar login"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        # Validação básica
        if not username or not password:
            self.show_error("Por favor, preencha todos os campos")
            return
        
        # Tentar login
        success, message = self.auth_manager.login(username, password)
        
        if not success:
            self.show_error(message)
            return
        
        # Login bem-sucedido
        self.error_label.setVisible(False)
        self.login_success.emit(self.auth_manager.get_user())
        self.accept()
    
    def show_error(self, message):
        """Exibe mensagem de erro"""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        
        # Animação de shake
        animation = QPropertyAnimation(self.error_label, b"pos")
        animation.setDuration(100)
        
        pos = self.error_label.pos()
        
        animation.setKeyValueAt(0, QPoint(pos.x(), pos.y()))
        animation.setKeyValueAt(0.1, QPoint(pos.x() + 5, pos.y()))
        animation.setKeyValueAt(0.3, QPoint(pos.x() - 5, pos.y()))
        animation.setKeyValueAt(0.5, QPoint(pos.x() + 5, pos.y()))
        animation.setKeyValueAt(0.7, QPoint(pos.x() - 5, pos.y()))
        animation.setKeyValueAt(0.9, QPoint(pos.x() + 5, pos.y()))
        animation.setKeyValueAt(1, QPoint(pos.x(), pos.y()))
        
        animation.start()
    
    def forgot_password(self):
        """Abre diálogo de recuperação de senha"""
        # Implementar recuperação de senha
        QMessageBox.information(
            self, 
            "Recuperação de Senha", 
            "Entre em contato com o administrador do sistema para resetar sua senha."
        )
```

### Interface do Seletor de Modo:

```python
class UserModeSelector(QDialog):
    """Seletor de modo de usuário (admin, cliente, etc)"""
    
    mode_selected = Signal(str)  # Mode string
    
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        
        self.setWindowTitle("Selecionar Modo - GoVideo")
        self.setFixedSize(500, 300)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Cabeçalho
        welcome_label = QLabel(f"Bem-vindo(a), {self.user.full_name}")
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)
        
        description_label = QLabel("Selecione como deseja acessar o sistema:")
        description_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(description_label)
        layout.addSpacing(20)
        
        # Container de modos
        modes_layout = QHBoxLayout()
        modes_layout.setSpacing(20)
        
        # Adicionar modos disponíveis
        if self.user.role and self.user.role.name == "admin":
            self.add_mode_button(modes_layout, "admin", "Administrador", ":/icons/admin.png")
        
        if self.user.is_client:
            self.add_mode_button(modes_layout, "client", "Cliente", ":/icons/client.png")
        
        if self.user.is_sponsor:
            self.add_mode_button(modes_layout, "sponsor", "Patrocinador", ":/icons/sponsor.png")
        
        # Sempre exibir modo operador se tiver permissão
        if self.user.has_permission(Permission.VIEW_DASHBOARD):
            self.add_mode_button(modes_layout, "operator", "Operador", ":/icons/operator.png")
        
        layout.addLayout(modes_layout)
    
    def add_mode_button(self, layout, mode, label, icon_path):
        """Adiciona um botão de modo"""
        button = QPushButton()
        button.setFixedSize(120, 120)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 10px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        
        button_layout = QVBoxLayout(button)
        button_layout.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel()
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            icon_label.setAlignment(Qt.AlignCenter)
        else:
            icon_label.setText(mode.capitalize())
            icon_label.setAlignment(Qt.AlignCenter)
        
        button_layout.addWidget(icon_label)
        
        text_label = QLabel(label)
        text_label.setAlignment(Qt.AlignCenter)
        button_layout.addWidget(text_label)
        
        # Conectar clique
        button.clicked.connect(lambda: self.select_mode(mode))
        
        layout.addWidget(button)
    
    def select_mode(self, mode):
        """Seleciona um modo e emite o sinal"""
        self.mode_selected.emit(mode)
        self.accept()
```

### Ajuste da Interface Principal para Modos de Usuário:

```python
class MainWindow(QMainWindow):
    """Janela principal da aplicação com suporte a diferentes modos de usuário"""
    
    def __init__(self, session, auth_manager):
        super().__init__()
        self.session = session
        self.auth_manager = auth_manager
        self.current_mode = None
        
        self.setWindowTitle("GoVideo")
        self.setMinimumSize(1200, 800)
        
        # Inicializar UI
        self.setup_ui()
        
        # Se não há usuário logado, mostrar login
        if not self.auth_manager.is_authenticated():
            self.show_login()
        else:
            # Se há apenas um modo possível, usá-lo
            user = self.auth_manager.get_user()
            available_modes = self.get_available_modes(user)
            
            if len(available_modes) == 1:
                self.set_mode(available_modes[0])
            else:
                self.show_mode_selector()
    
    def setup_ui(self):
        """Configura a interface de usuário base"""
        self.setCentralWidget(QWidget())
        self.main_layout = QVBoxLayout(self.centralWidget())
        
        # Barra de status
        self.status_bar = self.statusBar()
        self.status_user_label = QLabel()
        self.status_bar.addPermanentWidget(self.status_user_label)
        
        # Menu
        self.menu_bar = self.menuBar()
        self.menu_bar.setStyleSheet("QMenuBar { background-color: #f8f9fa; }")
        
        # Menu Arquivo
        self.file_menu = self.menu_bar.addMenu("Arquivo")
        
        self.switch_mode_action = QAction("Trocar Modo", self)
        self.switch_mode_action.triggered.connect(self.show_mode_selector)
        self.file_menu.addAction(self.switch_mode_action)
        
        self.logout_action = QAction("Logout", self)
        self.logout_action.triggered.connect(self.logout)
        self.file_menu.addAction(self.logout_action)
        
        self.file_menu.addSeparator()
        
        self.exit_action = QAction("Sair", self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)
        
        # Layout principal com empilhamento
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
    
    def show_login(self):
        """Exibe a tela de login"""
        login_dialog = LoginDialog(self.auth_manager)
        login_dialog.login_success.connect(self.handle_login_success)
        
        # Se o diálogo for fechado sem login, fechar aplicação
        if login_dialog.exec_() != QDialog.Accepted:
            self.close()
    
    def handle_login_success(self, user):
        """Manipula login bem-sucedido"""
        available_modes = self.get_available_modes(user)
        
        if len(available_modes) == 1:
            self.set_mode(available_modes[0])
        else:
            self.show_mode_selector()
    
    def show_mode_selector(self):
        """Exibe o seletor de modo"""
        user = self.auth_manager.get_user()
        if not user:
            self.show_login()
            return
            
        selector = UserModeSelector(user)
        selector.mode_selected.connect(self.set_mode)
        
        if selector.exec_() != QDialog.Accepted and not self.current_mode:
            # Se não selecionou modo e não há modo atual, mostrar login
            self.logout()
            self.show_login()
    
    def get_available_modes(self, user):
        """Obtém modos disponíveis para o usuário"""
        available_modes = []
        
        if user.role and user.role.name == "admin":
            available_modes.append("admin")
        
        if user.is_client:
            available_modes.append("client")
        
        if user.is_sponsor:
            available_modes.append("sponsor")
        
        if user.has_permission(Permission.VIEW_DASHBOARD):
            available_modes.append("operator")
        
        return available_modes
    
    def set_mode(self, mode):
        """Define o modo de usuário atual"""
        self.current_mode = mode
        
        # Limpar interface
        self.clear_interface()
        
        # Configurar interface para o modo
        if mode == "admin":
            self.setup_admin_interface()
        elif mode == "client":
            self.setup_client_interface()
        elif mode == "sponsor":
            self.setup_sponsor_interface()
        elif mode == "operator":
            self.setup_operator_interface()
        
        # Atualizar barra de status
        user = self.auth_manager.get_user()
        self.status_user_label.setText(f"Usuário: {user.full_name} | Modo: {mode.capitalize()}")
    
    def clear_interface(self):
        """Limpa a interface atual"""
        # Limpar widgets empilhados
        while self.stacked_widget.count() > 0:
            widget = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
        
        # Limpar dock widgets
        for dock in self.findChildren(QDockWidget):
            self.removeDockWidget(dock)
            dock.deleteLater()
        
        # Limpar menu específico do modo
        for action in self.menu_bar.actions():
            if action.text() not in ["Arquivo", "Ajuda"]:
                self.menu_bar.removeAction(action)
    
    def setup_admin_interface(self):
        """Configura interface para modo administrador"""
        # Menu Admin
        admin_menu = self.menu_bar.addMenu("Administração")
        
        users_action = QAction("Gerenciar Usuários", self)
        users_action.triggered.connect(lambda: self.show_admin_view("users"))
        admin_menu.addAction(users_action)
        
        roles_action = QAction("Papéis e Permissões", self)
        roles_action.triggered.connect(lambda: self.show_admin_view("roles"))
        admin_menu.addAction(roles_action)
        
        settings_action = QAction("Configurações", self)
        settings_action.triggered.connect(lambda: self.show_admin_view("settings"))
        admin_menu.addAction(settings_action)
        
        # Interface principal
        admin_dashboard = AdminDashboardView(self.session, self.auth_manager)
        self.stacked_widget.addWidget(admin_dashboard)
    
    def setup_client_interface(self):
        """Configura interface para modo cliente"""
        # Menu Cliente
        client_menu = self.menu_bar.addMenu("Cliente")
        
        events_action = QAction("Meus Eventos", self)
        events_action.triggered.connect(lambda: self.show_client_view("events"))
        client_menu.addAction(events_action)
        
        deliveries_action = QAction("Minhas Entregas", self)
        deliveries_action.triggered.connect(lambda: self.show_client_view("deliveries"))
        client_menu.addAction(deliveries_action)
        
        profile_action = QAction("Meu Perfil", self)
        profile_action.triggered.connect(lambda: self.show_client_view("profile"))
        client_menu.addAction(profile_action)
        
        # Interface principal
        client_dashboard = ClientDashboardView(self.session, self.auth_manager)
        self.stacked_widget.addWidget(client_dashboard)
    
    def setup_sponsor_interface(self):
        """Configura interface para modo patrocinador"""
        # Menu Patrocinador
        sponsor_menu = self.menu_bar.addMenu("Patrocinador")
        
        activations_action = QAction("Minhas Ativações", self)
        activations_action.triggered.connect(lambda: self.show_sponsor_view("activations"))
        sponsor_menu.addAction(activations_action)
        
        events_action = QAction("Eventos", self)
        events_action.triggered.connect(lambda: self.show_sponsor_view("events"))
        sponsor_menu.addAction(events_action)
        
        profile_action = QAction("Meu Perfil", self)
        profile_action.triggered.connect(lambda: self.show_sponsor_view("profile"))
        sponsor_menu.addAction(profile_action)
        
        # Interface principal
        sponsor_dashboard = SponsorDashboardView(self.session, self.auth_manager)
        self.stacked_widget.addWidget(sponsor_dashboard)
    
    def setup_operator_interface(self):
        """Configura interface para modo operador"""
        # Menu Operador
        events_menu = self.menu_bar.addMenu("Eventos")
        
        new_event_action = QAction("Novo Evento", self)
        new_event_action.triggered.connect(self.create_new_event)
        events_menu.addAction(new_event_action)
        
        events_action = QAction("Listar Eventos", self)
        events_action.triggered.connect(lambda: self.show_operator_view("events"))
        events_menu.addAction(events_action)
        
        # Menu Entregas
        deliveries_menu = self.menu_bar.addMenu("Entregas")
        
        deliveries_action = QAction("Lista de Entregas", self)
        deliveries_action.triggered.connect(lambda: self.show_operator_view("deliveries"))
        deliveries_menu.addAction(deliveries_action)
        
        # Menu Equipe
        team_menu = self.menu_bar.addMenu("Equipe")
        
        team_members_action = QAction("Membros da Equipe", self)
        team_members_action.triggered.connect(lambda: self.show_operator_view("team_members"))
        team_menu.addAction(team_members_action)
        
        team_schedule_action = QAction("Escala da Equipe", self)
        team_schedule_action.triggered.connect(lambda: self.show_operator_view("team_schedule"))
        team_menu.addAction(team_schedule_action)
        
        # Menu Patrocinadores
        sponsors_menu = self.menu_bar.addMenu("Patrocinadores")
        
        sponsors_action = QAction("Patrocinadores", self)
        sponsors_action.triggered.connect(lambda: self.show_operator_view("sponsors"))
        sponsors_menu.addAction(sponsors_action)
        
        activations_action = QAction("Ativações", self)
        activations_action.triggered.connect(lambda: self.show_operator_view("activations"))
        sponsors_menu.addAction(activations_action)
        
        # Menu Relatórios
        reports_menu = self.menu_bar.addMenu("Relatórios")
        
        new_report_action = QAction("Novo Relatório", self)
        new_report_action.triggered.connect(self.create_new_report)
        reports_menu.addAction(new_report_action)
        
        # Interface principal
        operator_dashboard = OperatorDashboardView(self.session, self.auth_manager)
        self.stacked_widget.addWidget(operator_dashboard)
    
    def show_admin_view(self, view_name):
        """Exibe uma visualização específica do modo admin"""
        # Implementar visualizações admin
        pass
    
    def show_client_view(self, view_name):
        """Exibe uma visualização específica do modo cliente"""
        # Implementar visualizações cliente
        pass
    
    def show_sponsor_view(self, view_name):
        """Exibe uma visualização específica do modo patrocinador"""
        # Implementar visualizações patrocinador
        pass
    
    def show_operator_view(self, view_name):
        """Exibe uma visualização específica do modo operador"""
        if view_name == "events":
            event_list_view = EventListView(self.session, self.auth_manager)
            self.stacked_widget.addWidget(event_list_view)
            self.stacked_widget.setCurrentWidget(event_list_view)
        elif view_name == "deliveries":
            delivery_list_view = DeliveryListView(self.session, self.auth_manager)
            self.stacked_widget.addWidget(delivery_list_view)
            self.stacked_widget.setCurrentWidget(delivery_list_view)
        elif view_name == "team_members":
            team_members_view = TeamMembersView(self.session, self.auth_manager)
            self.stacked_widget.addWidget(team_members_view)
            self.stacked_widget.setCurrentWidget(team_members_view)
        elif view_name == "team_schedule":
            team_schedule_view = TeamScheduleView(self.session, self.auth_manager)
            self.stacked_widget.addWidget(team_schedule_view)
            self.stacked_widget.setCurrentWidget(team_schedule_view)
        elif view_name == "sponsors":
            sponsors_view = SponsorsView(self.session, self.auth_manager)
            self.stacked_widget.addWidget(sponsors_view)
            self.stacked_widget.setCurrentWidget(sponsors_view)
        elif view_name == "activations":
            activations_view = ActivationsView(self.session, self.auth_manager)
            self.stacked_widget.addWidget(activations_view)
            self.stacked_widget.setCurrentWidget(activations_view)
    
    def create_new_event(self):
        """Abre diálogo para criar novo evento"""
        # Implementar diálogo de criação de evento
        pass
    
    def create_new_report(self):
        """Abre diálogo para criar novo relatório"""
        # Implementar diálogo de criação de relatório
        pass
    
    def logout(self):
        """Realiza logout do usuário atual"""
        self.auth_manager.logout()
        self.current_mode = None
        self.clear_interface()
        self.status_user_label.clear()
        self.show_login()
```

## 8. Internacionalização Total (i18n)

### Sistema de Internacionalização:

```python
class TranslationManager:
    """Gerenciador de traduções para internacionalização"""
    
    def __init__(self):
        self.app = QApplication.instance()
        self.translator = QTranslator()
        self.qt_translator = QTranslator()
        self.current_locale = QLocale()
        
        # Diretório de traduções
        self.translations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "translations"
        )
    
    def available_languages(self):
        """Retorna lista de idiomas disponíveis"""
        languages = []
        
        # Verificar arquivos de tradução
        if os.path.exists(self.translations_dir):
            for file_name in os.listdir(self.translations_dir):
                if file_name.startswith("govideo_") and file_name.endswith(".qm"):
                    lang_code = file_name[len("govideo_"):-3]
                    locale = QLocale(lang_code)
                    language_name = QLocale.languageToString(locale.language())
                    languages.append({
                        "code": lang_code,
                        "name": language_name,
                        "native_name": locale.nativeLanguageName(),
                        "locale": locale
                    })
        
        # Adicionar inglês como padrão
        if not any(lang["code"] == "en" for lang in languages):
            languages.append({
                "code": "en",
                "name": "English",
                "native_name": "English",
                "locale": QLocale("en")
            })
        
        # Ordenar por nome
        return sorted(languages, key=lambda x: x["name"])
    
    def get_current_language(self):
        """Retorna o idioma atual"""
        return self.current_locale.name().split("_")[0]
    
    def change_language(self, lang_code):
        """Muda o idioma da aplicação"""
        # Remover tradutores anteriores
        self.app.removeTranslator(self.translator)
        self.app.removeTranslator(self.qt_translator)
        
        locale = QLocale(lang_code)
        self.current_locale = locale
        QLocale.setDefault(locale)
        
        # Carregar traduções do Qt
        self.qt_translator = QTranslator()
        if self.qt_translator.load("qt_" + locale.name(), QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
            self.app.installTranslator(self.qt_translator)
        
        # Carregar traduções da aplicação
        self.translator = QTranslator()
        translations_file = os.path.join(self.translations_dir, f"govideo_{lang_code}.qm")
        
        if os.path.exists(translations_file):
            if self.translator.load(translations_file):
                self.app.installTranslator(self.translator)
                return True
                
        return False
    
    def save_language_preference(self, lang_code):
        """Salva preferência de idioma no arquivo de configuração"""
        settings = QSettings("GoNetwork", "GoVideo")
        settings.setValue("language", lang_code)
        settings.sync()
    
    def load_language_preference(self):
        """Carrega preferência de idioma do arquivo de configuração"""
        settings = QSettings("GoNetwork", "GoVideo")
        lang_code = settings.value("language", "")
        
        if lang_code:
            return self.change_language(lang_code)
        else:
            # Usar idioma do sistema
            system_locale = QLocale.system()
            system_lang = system_locale.name().split("_")[0]
            return self.change_language(system_lang)
```

### Interface para Seleção de Idioma:

```python
class LanguageSelectionDialog(QDialog):
    """Diálogo para seleção de idioma"""
    
    language_changed = Signal(str)  # lang_code
    
    def __init__(self, translation_manager, parent=None):
        super().__init__(parent)
        self.translation_manager = translation_manager
        
        self.setWindowTitle(self.tr("Selecionar Idioma"))
        self.setFixedSize(400, 300)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel(self.tr("Selecione o idioma"))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Lista de idiomas
        self.language_list = QListWidget()
        self.language_list.setIconSize(QSize(32, 32))
        layout.addWidget(self.language_list)
        
        # Carregar idiomas disponíveis
        current_lang = self.translation_manager.get_current_language()
        for lang in self.translation_manager.available_languages():
            item = QListWidgetItem()
            item.setText(f"{lang['native_name']} ({lang['name']})")
            item.setData(Qt.UserRole, lang["code"])
            
            # Tentar carregar bandeira
            flag_path = f":/flags/{lang['code']}.png"
            flag_pixmap = QPixmap(flag_path)
            if not flag_pixmap.isNull():
                item.setIcon(QIcon(flag_pixmap))
            
            self.language_list.addItem(item)
            
            # Selecionar idioma atual
            if lang["code"] == current_lang:
                self.language_list.setCurrentItem(item)
        
        # Conectar sinal de seleção
        self.language_list.itemDoubleClicked.connect(self.apply_language)
        
        # Botões
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_language)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def accept_language(self):
        """Aplica o idioma selecionado e fecha o diálogo"""
        current_item = self.language_list.currentItem()
        if current_item:
            lang_code = current_item.data(Qt.UserRole)
            self.apply_language(current_item)
            self.accept()
    
    def apply_language(self, item):
        """Aplica o idioma selecionado"""
        lang_code = item.data(Qt.UserRole)
        if self.translation_manager.change_language(lang_code):
            self.translation_manager.save_language_preference(lang_code)
            self.language_changed.emit(lang_code)
```

### Geração de Arquivo de Tradução Base:

```python
def generate_translation_source(output_file="govideo_en.ts"):
    """
    Gera arquivo de tradução base para uso com Qt Linguist
    Deve ser executado quando strings traduzíveis são modificadas
    """
    import subprocess
    import os
    
    # Diretório raiz do projeto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Diretório de traduções
    translations_dir = os.path.join(project_root, "translations")
    os.makedirs(translations_dir, exist_ok=True)
    
    # Arquivo de saída
    output_path = os.path.join(translations_dir, output_file)
    
    # Encontrar todos os arquivos Python e QML
    python_files = []
    qml_files = []
    
    for root, _, files in os.walk(project_root):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
            elif file.endswith(".qml"):
                qml_files.append(os.path.join(root, file))
    
    # Comando para pylupdate5
    pylupdate_cmd = ["pylupdate5"]
    
    # Adicionar arquivos Python
    pylupdate_cmd.extend(python_files)
    
    # Adicionar arquivo de saída
    pylupdate_cmd.extend(["-ts", output_path])
    
    # Executar comando
    try:
        subprocess.run(pylupdate_cmd, check=True)
        print(f"Arquivo de tradução base gerado em: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao gerar arquivo de tradução: {e}")
        return False
        
    # Se houver arquivos QML, usar lupdate para atualizá-los
    if qml_files:
        # Criar arquivo .pro temporário
        pro_file = os.path.join(project_root, "govideo_temp.pro")
        with open(pro_file, "w") as f:
            f.write("SOURCES = \\\n")
            f.write(" \\\n".join(qml_files))
            f.write("\n\nTRANSLATIONS = ")
            f.write(output_path)
        
        # Comando para lupdate
        lupdate_cmd = ["lupdate", pro_file]
        
        try:
            subprocess.run(lupdate_cmd, check=True)
            print(f"Arquivo de tradução atualizado com strings QML")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao atualizar traduções de QML: {e}")
        
        # Remover arquivo .pro temporário
        try:
            os.remove(pro_file)
        except:
            pass
    
    return True
```

### Integração no Sistema Principal:

```python
def initialize_i18n():
    """Inicializa sistema de internacionalização"""
    # Criar e configurar gerenciador de traduções
    translation_manager = TranslationManager()
    
    # Carregar preferência de idioma
    translation_manager.load_language_preference()
    
    return translation_manager
```

## 9. Performance e Manutenção

### Sistema de Cache e Gerenciamento de Memória:

```python
class CacheManager:
    """Gerenciador de cache para assets e outros recursos"""
    
    def __init__(self, max_size_mb=1024):
        """
        Inicializa o gerenciador de cache
        :param max_size_mb: Tamanho máximo do cache em MB
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.current_size_bytes = 0
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.access_log = {}  # Rastrear acesso aos itens
        self._lock = threading.RLock()
    
    def get(self, key, default=None):
        """
        Obtém um item do cache
        :param key: Chave do item
        :param default: Valor padrão se não encontrado
        :return: Item armazenado ou default
        """
        with self._lock:
            if key in self.cache:
                # Registrar acesso
                self.access_log[key] = time.time()
                self.cache_hits += 1
                return self.cache[key]
            
            self.cache_misses += 1
            return default
    
    def set(self, key, value, size_bytes=None):
        """
        Adiciona ou atualiza um item no cache
        :param key: Chave do item
        :param value: Valor a armazenar
        :param size_bytes: Tamanho do item em bytes (se None, estimado)
        :return: True se armazenado, False se rejeitado por ser muito grande
        """
        # Estimar tamanho se não fornecido
        if size_bytes is None:
            size_bytes = self._estimate_size(value)
        
        # Rejeitar itens muito grandes
        if size_bytes > self.max_size_bytes:
            return False
        
        with self._lock:
            # Se já existe, atualizar tamanho total
            if key in self.cache:
                old_size = self._estimate_size(self.cache[key])
                self.current_size_bytes -= old_size
            
            # Liberar espaço se necessário
            while self.current_size_bytes + size_bytes > self.max_size_bytes:
                self._evict_least_recently_used()
                
            # Armazenar item
            self.cache[key] = value
            self.current_size_bytes += size_bytes
            self.access_log[key] = time.time()
            
            return True
    
    def remove(self, key):
        """
        Remove um item do cache
        :param key: Chave do item
        :return: True se removido, False se não existia
        """
        with self._lock:
            if key in self.cache:
                size = self._estimate_size(self.cache[key])
                self.current_size_bytes -= size
                del self.cache[key]
                if key in self.access_log:
                    del self.access_log[key]
                return True
            return False
    
    def clear(self):
        """Limpa todo o cache"""
        with self._lock:
            self.cache = {}
            self.access_log = {}
            self.current_size_bytes = 0
    
    def _evict_least_recently_used(self):
        """Remove o item menos recentemente usado do cache"""
        if not self.access_log:
            return
            
        # Encontrar item menos recentemente usado
        lru_key = min(self.access_log.items(), key=lambda x: x[1])[0]
        
        # Remover do cache
        if lru_key in self.cache:
            size = self._estimate_size(self.cache[lru_key])
            self.current_size_bytes -= size
            del self.cache[lru_key]
        
        # Remover do log de acesso
        del self.access_log[lru_key]
    
    def _estimate_size(self, obj):
        """
        Estima o tamanho de um objeto em bytes
        Esta é uma estimativa aproximada, não exata
        """
        if isinstance(obj, (str, bytes, bytearray)):
            return len(obj)
        elif isinstance(obj, QPixmap):
            return obj.width() * obj.height() * 4  # RGBA, 4 bytes por pixel
        elif isinstance(obj, QImage):
            return obj.width() * obj.height() * (obj.depth() // 8)
        elif isinstance(obj, dict):
            return sum(self._estimate_size(k) + self._estimate_size(v) for k, v in obj.items())
        elif isinstance(obj, (list, tuple)):
            return sum(self._estimate_size(item) for item in obj)
        else:
            # Estimativa genérica
            return sys.getsizeof(obj)
    
    def get_stats(self):
        """
        Retorna estatísticas do cache
        :return: Dicionário com estatísticas
        """
        with self._lock:
            return {
                "max_size_bytes": self.max_size_bytes,
                "current_size_bytes": self.current_size_bytes,
                "usage_percent": (self.current_size_bytes / self.max_size_bytes * 100) if self.max_size_bytes > 0 else 0,
                "items_count": len(self.cache),
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_ratio": (self.cache_hits / (self.cache_hits + self.cache_misses) * 100) if (self.cache_hits + self.cache_misses) > 0 else 0
            }
```

### Sistema de Limpeza de Arquivos Temporários:

```python
class TempFileManager:
    """Gerenciador de arquivos temporários"""
    
    def __init__(self, temp_dir=None, max_age_days=7):
        """
        Inicializa o gerenciador de arquivos temporários
        :param temp_dir: Diretório temporário (None para usar padrão do sistema)
        :param max_age_days: Idade máxima de arquivos em dias
        """
        if temp_dir:
            self.temp_dir = temp_dir
        else:
            self.temp_dir = os.path.join(os.path.expanduser("~"), ".govideo", "temp")
        
        self.max_age_seconds = max_age_days * 24 * 60 * 60
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def create_temp_file(self, prefix="", suffix=""):
        """
        Cria um arquivo temporário
        :param prefix: Prefixo do nome do arquivo
        :param suffix: Sufixo do nome do arquivo (extensão)
        :return: Caminho para o arquivo temporário
        """
        # Garantir que o diretório existe
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Gerar nome único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_part = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
        filename = f"{prefix}_{timestamp}_{random_part}{suffix}"
        
        # Caminho completo
        filepath = os.path.join(self.temp_dir, filename)
        
        # Criar arquivo vazio
        open(filepath, 'a').close()
        
        return filepath
    
    def create_temp_directory(self, prefix=""):
        """
        Cria um diretório temporário
        :param prefix: Prefixo do nome do diretório
        :return: Caminho para o diretório temporário
        """
        # Garantir que o diretório pai existe
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Gerar nome único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_part = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
        dirname = f"{prefix}_{timestamp}_{random_part}"
        
        # Caminho completo
        dirpath = os.path.join(self.temp_dir, dirname)
        
        # Criar diretório
        os.makedirs(dirpath, exist_ok=True)
        
        return dirpath
    
    def cleanup(self, force=False):
        """
        Limpa arquivos temporários antigos
        :param force: Se True, remove todos os arquivos, independente da idade
        :return: Número de arquivos removidos
        """
        if not os.path.exists(self.temp_dir):
            return 0
            
        removed_count = 0
        current_time = time.time()
        
        for item in os.listdir(self.temp_dir):
            item_path = os.path.join(self.temp_dir, item)
            
            # Verificar idade do arquivo
            try:
                item_age = current_time - os.path.getmtime(item_path)
                
                if force or item_age > self.max_age_seconds:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        removed_count += 1
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                        removed_count += 1
            except Exception as e:
                logger.error(f"Erro ao limpar arquivo temporário {item_path}: {e}")
        
        return removed_count
    
    def schedule_cleanup(self):
        """Agenda a limpeza periódica de arquivos temporários"""
        # Esta função deve ser chamada em um thread separado
        
        while True:
            try:
                # Limpar arquivos
                removed = self.cleanup()
                if removed > 0:
                    logger.info(f"Limpeza automática de arquivos temporários: {removed} itens removidos")
                    
                # Aguardar 24 horas
                time.sleep(24 * 60 * 60)
            except Exception as e:
                logger.error(f"Erro na limpeza automática de arquivos temporários: {e}")
                time.sleep(60 * 60)  # Aguardar 1 hora e tentar novamente
```

### Sistema de Backup Automático:

```python
class DatabaseBackupManager:
    """Gerenciador de backup do banco de dados SQLite"""
    
    def __init__(self, db_path, backup_dir=None, max_backups=10):
        """
        Inicializa o gerenciador de backup
        :param db_path: Caminho para o arquivo do banco de dados
        :param backup_dir: Diretório para backups (None para usar padrão)
        :param max_backups: Número máximo de backups a manter
        """
        self.db_path = db_path
        
        if backup_dir:
            self.backup_dir = backup_dir
        else:
            self.backup_dir = os.path.join(os.path.dirname(db_path), "backups")
        
        self.max_backups = max_backups
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self):
        """
        Cria um backup do banco de dados
        :return: Caminho para o arquivo de backup ou None se falhou
        """
        if not os.path.exists(self.db_path):
            logger.error(f"Banco de dados não encontrado: {self.db_path}")
            return None
            
        try:
            # Gerar nome do arquivo de backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_name = os.path.basename(self.db_path)
            backup_name = f"{os.path.splitext(db_name)[0]}_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Copiar banco de dados
            shutil.copy2(self.db_path, backup_path)
            
            # Registrar backup
            logger.info(f"Backup do banco de dados criado: {backup_path}")
            
            # Limpar backups antigos
            self._cleanup_old_backups()
            
            return backup_path
        except Exception as e:
            logger.error(f"Erro ao criar backup do banco de dados: {e}")
            return None
    
    def restore_backup(self, backup_path=None):
        """
        Restaura um backup do banco de dados
        :param backup_path: Caminho para o arquivo de backup (None para usar o mais recente)
        :return: True se restaurado com sucesso, False caso contrário
        """
        try:
            # Se não especificado, usar o backup mais recente
            if not backup_path:
                backup_files = self.list_backups()
                if not backup_files:
                    logger.error("Nenhum backup encontrado para restauração")
                    return False
                    
                backup_path = backup_files[0][0]
            
            # Verificar se o backup existe
            if not os.path.exists(backup_path):
                logger.error(f"Arquivo de backup não encontrado: {backup_path}")
                return False
                
            # Criar backup do banco atual antes de restaurar
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_name = os.path.basename(self.db_path)
            pre_restore_backup = f"{os.path.splitext(db_name)[0]}_pre_restore_{timestamp}.db"
            pre_restore_path = os.path.join(self.backup_dir, pre_restore_backup)
            
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, pre_restore_path)
                logger.info(f"Backup de segurança criado antes da restauração: {pre_restore_path}")
            
            # Restaurar backup
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"Banco de dados restaurado a partir de: {backup_path}")
            
            return True
        except Exception as e:
            logger.error(f"Erro ao restaurar backup do banco de dados: {e}")
            return False
    
    def list_backups(self):
        """
        Lista backups disponíveis em ordem cronológica inversa (mais recente primeiro)
        :return: Lista de tuplas (caminho, data)
        """
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
            
        # Buscar todos os arquivos .db no diretório de backups
        db_files = [f for f in os.listdir(self.backup_dir) if f.endswith(".db")]
        
        for db_file in db_files:
            file_path = os.path.join(self.backup_dir, db_file)
            file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
            backups.append((file_path, file_date))
        
        # Ordenar por data (mais recente primeiro)
        backups.sort(key=lambda x: x[1], reverse=True)
        
        return backups
    
    def _cleanup_old_backups(self):
        """Remove backups antigos para manter apenas o número máximo configurado"""
        backups = self.list_backups()
        
        # Se há mais backups que o limite, remover os mais antigos
        if len(backups) > self.max_backups:
            for backup_path, _ in backups[self.max_backups:]:
                try:
                    os.remove(backup_path)
                    logger.info(f"Backup antigo removido: {backup_path}")
                except Exception as e:
                    logger.error(f"Erro ao remover backup antigo {backup_path}: {e}")
    
    def schedule_backups(self, interval_hours=24):
        """
        Agenda backups periódicos
        :param interval_hours: Intervalo entre backups em horas
        """
        # Esta função deve ser chamada em um thread separado
        
        while True:
            try:
                # Criar backup
                self.create_backup()
                
                # Aguardar pelo intervalo
                time.sleep(interval_hours * 60 * 60)
            except Exception as e:
                logger.error(f"Erro no backup automático: {e}")
                time.sleep(60 * 60)  # Aguardar 1 hora e tentar novamente
```

### Configuração Avançada de Logging:

```python
def setup_logging(log_dir=None, log_level=logging.INFO):
    """
    Configura o sistema de logs
    :param log_dir: Diretório para arquivos de log (None para usar padrão)
    :param log_level: Nível de log
    """
    if log_dir is None:
        log_dir = os.path.join(os.path.expanduser("~"), ".govideo", "logs")
    
    os.makedirs(log_dir, exist_ok=True)
    
    # Configurar formato básico
    log_format = "%(asctime)s [%(levelname)s] [%(name)s] [%(threadName)s]: %(message)s"
    formatter = logging.Formatter(