"""
View para o dashboard principal da aplicação.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal


class DashboardView(QWidget):
    """
    Visualização do dashboard principal do aplicativo.
    Exibe os vídeos e opções disponíveis para o usuário.
    """
      # Sinais que podem ser emitidos pela visualização
    video_selected = pyqtSignal(int)  # Emite o ID do vídeo selecionado
    add_video_clicked = pyqtSignal()  # Sinal quando o botão de adicionar vídeo é clicado
    
    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.current_event = None
        self.setup_ui()
    
    def set_current_event(self, event):
        """Define o evento atual e atualiza o dashboard
        
        Args:
            event: Objeto evento selecionado
        """
        self.current_event = event
        self.update_dashboard()
        
    def update_dashboard(self):
        """Atualiza o dashboard com base no evento atual"""
        # Aqui implementaríamos a lógica para atualizar o dashboard com os dados do evento
        pass
        
    def setup_ui(self):
        """Configura a interface do usuário do dashboard"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Cabeçalho
        header = QLabel("Dashboard", self)
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(header)
        
        # Barra de ações
        action_bar = QHBoxLayout()
        add_button = QPushButton("Adicionar Vídeo", self)
        add_button.clicked.connect(self.add_video_clicked.emit)
        action_bar.addWidget(add_button)
        action_bar.addStretch()
        main_layout.addLayout(action_bar)
        
        # Área de conteúdo com scroll
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.content_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Placeholder para lista de vídeos vazia
        self.empty_label = QLabel("Nenhum vídeo encontrado. Clique em 'Adicionar Vídeo'.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.empty_label)
        
        # Definir layout principal
        self.setLayout(main_layout)
    
    def add_video_item(self, video_id, title, thumbnail_path=None):
        """
        Adiciona um item de vídeo ao dashboard
        
        Args:
            video_id: ID único do vídeo
            title: Título do vídeo
            thumbnail_path: Caminho para a miniatura do vídeo (opcional)
        """
        # Se tiver o placeholder de vazio, remova-o
        if self.empty_label.isVisible():
            self.empty_label.setVisible(False)
        
        # Cria um frame para o vídeo
        video_frame = QFrame(self)
        video_frame.setFrameShape(QFrame.StyledPanel)
        video_frame.setLineWidth(1)
        
        # Layout do item de vídeo
        item_layout = QHBoxLayout(video_frame)
        
        # Thumbnail (ou placeholder)
        if thumbnail_path:
            thumbnail = QLabel()
            # Aqui você carregaria a imagem real do thumbnail
            thumbnail.setText("Thumbnail")
            thumbnail.setFixedSize(120, 80)
        else:
            thumbnail = QLabel("Sem\nThumbnail")
            thumbnail.setFixedSize(120, 80)
            thumbnail.setAlignment(Qt.AlignCenter)
        
        item_layout.addWidget(thumbnail)
        
        # Informações do vídeo
        info_layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(title_label)
        
        # Botões de ação
        action_layout = QHBoxLayout()
        view_button = QPushButton("Ver")
        edit_button = QPushButton("Editar")
        delete_button = QPushButton("Excluir")
        
        # Configura os botões para enviarem o ID do vídeo quando clicados
        view_button.clicked.connect(lambda: self.video_selected.emit(video_id))
        
        action_layout.addWidget(view_button)
        action_layout.addWidget(edit_button)
        action_layout.addWidget(delete_button)
        action_layout.addStretch()
        
        info_layout.addLayout(action_layout)
        item_layout.addLayout(info_layout)
        
        # Adiciona o frame do vídeo ao layout de conteúdo
        self.content_layout.addWidget(video_frame)
        
    def clear_videos(self):
        """Remove todos os itens de vídeo do dashboard"""
        # Limpa todos os widgets do layout de conteúdo
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Mostra o placeholder de vazio novamente
        self.empty_label.setVisible(True)
        self.content_layout.addWidget(self.empty_label)
