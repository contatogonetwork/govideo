#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Widget de visualização de cronograma/timeline
Data: 2025-05-15
"""

import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, 
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QLabel, QPushButton, QComboBox, QDateEdit, QSlider, QMenu, QAction,
    QToolTip, QGraphicsItem
)
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath, 
    QLinearGradient, QIcon
)
from PyQt5.QtCore import Qt, QRectF, QPointF, QDate, pyqtSignal, QEvent

logger = logging.getLogger(__name__)

class ActivityItem(QGraphicsRectItem):
    """Item gráfico para representar uma atividade na timeline"""
    
    def __init__(self, activity, x, y, width, height, parent=None):
        """Inicializar item de atividade
        
        Args:
            activity (dict): Dados da atividade
            x (float): Posição X
            y (float): Posição Y
            width (float): Largura
            height (float): Altura
            parent (QGraphicsItem, opcional): Item pai
        """
        super().__init__(x, y, width, height, parent)
        self.activity = activity
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Definir cores baseadas no tipo e prioridade
        self.setup_colors()
        
        # Adicionar texto
        self.setup_text()
        
    def setup_colors(self):
        """Definir cores do item baseado no tipo e prioridade"""
        # Cores por tipo de atividade
        type_colors = {
            'show': QColor(41, 128, 185),      # Azul
            'activation': QColor(39, 174, 96), # Verde
            'interview': QColor(142, 68, 173), # Roxo
            'photo': QColor(211, 84, 0),       # Laranja
            'setup': QColor(127, 140, 141),    # Cinza
            'other': QColor(44, 62, 80)        # Azul escuro
        }
        
        # Obter tipo ou definir padrão
        activity_type = self.activity.get('type', 'other').lower()
        base_color = type_colors.get(activity_type, type_colors['other'])
        
        # Ajustar cor baseado na prioridade (1=mais alta, 5=mais baixa)
        priority = self.activity.get('priority', 3)
        
        # Alta prioridade = mais saturada, baixa prioridade = menos saturada
        h, s, v, a = base_color.getHsvF()
        s = 0.8 if priority < 3 else (0.6 if priority == 3 else 0.4)
        adjusted_color = QColor.fromHsvF(h, s, v, a)
        
        # Criar gradiente
        gradient = QLinearGradient(0, 0, 0, self.rect().height())
        gradient.setColorAt(0, adjusted_color.lighter(110))
        gradient.setColorAt(1, adjusted_color)
        
        # Aplicar estilo
        self.setBrush(QBrush(gradient))
        
        # Borda mais escura para alta prioridade
        pen_color = adjusted_color.darker(150) if priority <= 2 else adjusted_color.darker(120)
        self.setPen(QPen(pen_color, 1.5 if priority <= 2 else 1))
        
    def setup_text(self):
        """Adicionar texto ao item"""
        # Criar item de texto
        text_item = QGraphicsTextItem(self)
        text_item.setPlainText(self.activity['name'])
        text_item.setDefaultTextColor(Qt.white)
        
        # Definir fonte
        font = QFont("Arial", 8)
        font.setBold(True)
        text_item.setFont(font)
        
        # Centralizar texto
        text_rect = text_item.boundingRect()
        item_rect = self.rect()
        
        text_item.setPos(
            item_rect.left() + 5,
            item_rect.top() + (item_rect.height() - text_rect.height()) / 2
        )
        
        # Verificar se texto cabe na largura disponível
        if text_rect.width() > item_rect.width() - 10:
            # Texto é muito largo, adicionar elipse
            text = self.activity['name']
            max_chars = max(5, int((item_rect.width() - 10) / 8))  # Estimativa
            text = text[:max_chars] + "..."
            text_item.setPlainText(text)
            
    def hoverEnterEvent(self, event):
        """Manipulador para quando o mouse entra no item"""
        # Destacar item
        highlight_brush = self.brush()
        highlight_color = highlight_brush.color().lighter(115)
        self.setBrush(QBrush(highlight_color))
        
        self.setCursor(Qt.PointingHandCursor)
        
        # Mostrar tooltip detalhado
        start_time = self.activity['start_time'].strftime('%H:%M')
        end_time = self.activity['end_time'].strftime('%H:%M')
        
        tooltip = (
            f"<b>{self.activity['name']}</b><br>"
            f"Horário: {start_time} - {end_time}<br>"
            f"Local: {self.activity['stage']}<br>"
        )
        
        if 'type' in self.activity:
            tooltip += f"Tipo: {self.activity['type']}<br>"
            
        if 'priority' in self.activity:
            priority_map = {1: "Alta", 2: "Média-Alta", 3: "Média", 4: "Média-Baixa", 5: "Baixa"}
            priority_text = priority_map.get(self.activity['priority'], "Normal")
            tooltip += f"Prioridade: {priority_text}"
            
        QToolTip.showText(event.screenPos(), tooltip)
        
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Manipulador para quando o mouse sai do item"""
        # Restaurar aparência original
        self.setup_colors()
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)
        
    def mousePressEvent(self, event):
        """Manipulador para clique do mouse"""
        if event.button() == Qt.LeftButton:
            # Emitir sinal via scene
            scene = self.scene()
            if scene and hasattr(scene, 'activity_clicked'):
                scene.activity_clicked.emit(self.activity)
        super().mousePressEvent(event)

class TimelineScene(QGraphicsScene):
    """Cena para o cronograma com eventos personalizados"""
    
    activity_clicked = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Inicializar cena da timeline"""
        super().__init__(parent)
        self.setBackgroundBrush(QColor(33, 33, 33))

class TimelineView(QWidget):
    """Widget para visualização de cronograma de evento"""
    
    activity_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Inicializar widget de cronograma"""
        super().__init__(parent)
        
        self.activities = []
        self.start_date = None
        self.end_date = None
        self.current_date = None
        self.current_view = "day"
        self.zoom_factor = 1.0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface do usuário"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de controles superiores
        control_layout = QHBoxLayout()
        
        # Navegação de data
        self.prev_btn = QPushButton(QIcon("resources/icons/prev.png"), "")
        self.prev_btn.setToolTip("Dia anterior")
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        
        self.next_btn = QPushButton(QIcon("resources/icons/next.png"), "")
        self.next_btn.setToolTip("Próximo dia")
        
        # Visualização
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Dia", "3 Dias", "Semana", "Evento"])
        self.view_combo.setToolTip("Escolher visualização")
        
        # Zoom
        zoom_label = QLabel("Zoom:")
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(1, 5)
        self.zoom_slider.setValue(3)
        self.zoom_slider.setFixedWidth(100)
        self.zoom_slider.setToolTip("Ajustar zoom")
        
        # Adicionar widgets ao layout
        control_layout.addWidget(self.prev_btn)
        control_layout.addWidget(self.date_edit)
        control_layout.addWidget(self.next_btn)
        control_layout.addStretch(1)
        control_layout.addWidget(QLabel("Visualização:"))
        control_layout.addWidget(self.view_combo)
        control_layout.addSpacing(10)
        control_layout.addWidget(zoom_label)
        control_layout.addWidget(self.zoom_slider)
        
        # Área de visualização do cronograma
        self.scene = TimelineScene()
        self.scene.activity_clicked.connect(self.on_activity_clicked)
        
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.TextAntialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        
        # Adicionar layouts ao layout principal
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.view)
        
        # Conectar sinais
        self.prev_btn.clicked.connect(self.prev_day)
        self.next_btn.clicked.connect(self.next_day)
        self.date_edit.dateChanged.connect(self.on_date_changed)
        self.view_combo.currentTextChanged.connect(self.on_view_changed)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        
    def set_activities(self, activities):
        """Definir atividades para exibição
        
        Args:
            activities (list): Lista de dicionários com dados das atividades
        """
        self.activities = activities
        self.update_view()
        
    def set_date_range(self, start_date, end_date):
        """Definir intervalo de datas do evento
        
        Args:
            start_date (datetime): Data de início
            end_date (datetime): Data de término
        """
        self.start_date = start_date
        self.end_date = end_date
        
        if not self.current_date:
            self.current_date = start_date
            self.date_edit.setDate(QDate(start_date.year, start_date.month, start_date.day))
            
        # Atualizar limites do DateEdit
        self.date_edit.setMinimumDate(QDate(start_date.year, start_date.month, start_date.day))
        self.date_edit.setMaximumDate(QDate(end_date.year, end_date.month, end_date.day))
        
        self.update_view()
        
    def go_to_date(self, date):
        """Ir para data específica
        
        Args:
            date (datetime.date): Data para visualizar
        """
        if isinstance(date, QDate):
            date = date.toPyDate()
            
        self.current_date = datetime.combine(date, datetime.min.time())
        self.date_edit.setDate(QDate(date.year, date.month, date.day))
        self.update_view()
        
    def prev_day(self):
        """Ir para o dia anterior"""
        if not self.current_date:
            return
            
        new_date = self.current_date - timedelta(days=1)
        
        # Verificar se está dentro do intervalo do evento
        if self.start_date and new_date < self.start_date:
            return
            
        self.go_to_date(new_date.date())
        
    def next_day(self):
        """Ir para o próximo dia"""
        if not self.current_date:
            return
            
        new_date = self.current_date + timedelta(days=1)
        
        # Verificar se está dentro do intervalo do evento
        if self.end_date and new_date > self.end_date:
            return
            
        self.go_to_date(new_date.date())
        
    def on_date_changed(self, qdate):
        """Manipulador para mudança de data no DateEdit
        
        Args:
            qdate (QDate): Nova data
        """
        self.go_to_date(qdate.toPyDate())
        
    def on_view_changed(self, text):
        """Manipulador para mudança de tipo de visualização
        
        Args:
            text (str): Texto da opção selecionada
        """
        text = text.lower()
        
        if "dia" in text and "3" not in text:
            self.current_view = "day"
        elif "3 dias" in text:
            self.current_view = "3days"
        elif "semana" in text:
            self.current_view = "week"
        elif "evento" in text:
            self.current_view = "event"
            
        self.update_view()
        
    def on_zoom_changed(self, value):
        """Manipulador para mudança de zoom
        
        Args:
            value (int): Novo valor de zoom (1-5)
        """
        # Calcular novo fator de zoom
        self.zoom_factor = 0.6 + (value * 0.2)  # 0.8 a 1.6
        self.update_view()
        
    def on_activity_clicked(self, activity):
        """Manipulador para clique em atividade
        
        Args:
            activity (dict): Dados da atividade clicada
        """
        self.activity_selected.emit(activity)
        
    def update_view(self):
        """Atualizar visualização conforme configurações atuais"""
        if not self.current_date:
            return
            
        # Limpar cena
        self.scene.clear()
        
        # Definir período a visualizar
        if self.current_view == "day":
            start_view = self.current_date
            end_view = self.current_date + timedelta(days=1)
        elif self.current_view == "3days":
            start_view = self.current_date
            end_view = self.current_date + timedelta(days=3)
        elif self.current_view == "week":
            # Começar no domingo da semana atual
            weekday = self.current_date.weekday()
            start_view = self.current_date - timedelta(days=weekday)
            end_view = start_view + timedelta(days=7)
        elif self.current_view == "event":
            if self.start_date and self.end_date:
                start_view = self.start_date
                end_view = self.end_date + timedelta(days=1)
            else:
                start_view = self.current_date
                end_view = self.current_date + timedelta(days=1)
        else:
            start_view = self.current_date
            end_view = self.current_date + timedelta(days=1)
        
        # Aplicar margens de tempo (1 hora antes e depois para visualização)
        start_view = start_view - timedelta(hours=1)
        end_view = end_view + timedelta(hours=1)
        
        # Configurar tamanhos
        hours_total = (end_view - start_view).total_seconds() / 3600
        width_per_hour = 100 * self.zoom_factor
        height_per_stage = 60
        
        total_width = width_per_hour * hours_total
        
        # Criar lista de palcos únicos
        stages = set()
        for activity in self.activities:
            # Verificar se a atividade está no período visualizado
            if 'start_time' not in activity or 'end_time' not in activity:
                continue
                
            if (activity['end_time'] < start_view or 
                activity['start_time'] > end_view):
                continue
                
            stages.add(activity['stage'])
            
        stages = sorted(list(stages))
        total_height = height_per_stage * (len(stages) + 1)  # +1 para cabeçalho
        
        # Definir tamanho da cena
        self.scene.setSceneRect(0, 0, total_width, total_height)
        
        # Desenhar linhas de grade de tempo (verticais)
        hours_range = int(hours_total) + 1
        start_hour = start_view.hour
        
        for i in range(hours_range):
            hour = (start_hour + i) % 24
            x = i * width_per_hour
            
            # Linha vertical
            self.scene.addLine(
                x, 0, x, total_height,
                QPen(QColor(60, 60, 60), 1, Qt.DashLine)
            )
            
            # Texto da hora
            time_text = f"{hour:02d}:00"
            text_item = self.scene.addText(time_text)
            text_item.setDefaultTextColor(QColor(200, 200, 200))
            text_item.setPos(x + 5, 5)
        
        # Desenhar linhas horizontais e nomes dos palcos
        for i, stage in enumerate(stages):
            y = (i + 1) * height_per_stage
            
            # Linha horizontal
            self.scene.addLine(
                0, y, total_width, y,
                QPen(QColor(60, 60, 60), 1)
            )
            
            # Nome do palco
            stage_item = self.scene.addText(stage)
            stage_item.setDefaultTextColor(QColor(200, 200, 200))
            font = QFont("Arial", 9)
            font.setBold(True)
            stage_item.setFont(font)
            stage_item.setPos(5, y - height_per_stage + 10)
        
        # Adicionar atividades
        for activity in self.activities:
            # Verificar se a atividade está no período visualizado
            if 'start_time' not in activity or 'end_time' not in activity:
                continue
                
            if (activity['end_time'] < start_view or 
                activity['start_time'] > end_view):
                continue
                
            # Calcular posição e tamanho
            try:
                stage_index = stages.index(activity['stage'])
            except ValueError:
                # Se o palco não está na lista, pular atividade
                continue
                
            x_start = (activity['start_time'] - start_view).total_seconds() / 3600 * width_per_hour
            x_end = (activity['end_time'] - start_view).total_seconds() / 3600 * width_per_hour
            width = x_end - x_start
            
            y = (stage_index + 1) * height_per_stage + 5
            height = height_per_stage - 10
            
            # Criar item de atividade
            activity_item = ActivityItem(activity, x_start, y, width, height)
            self.scene.addItem(activity_item)
        
        # Linha vertical para hora atual (se estiver visualizando o dia atual)
        now = datetime.now()
        if (now.date() >= start_view.date() and now.date() <= end_view.date()):
            # Calcular posição
            x_now = (now - start_view).total_seconds() / 3600 * width_per_hour
            
            # Adicionar linha
            if 0 <= x_now <= total_width:
                self.scene.addLine(
                    x_now, 0, x_now, total_height,
                    QPen(QColor(255, 50, 50), 2)
                )
                
                # Adicionar indicador na parte superior
                now_path = QPainterPath()
                now_path.moveTo(QPointF(x_now, 0))
                now_path.lineTo(QPointF(x_now - 5, 10))
                now_path.lineTo(QPointF(x_now + 5, 10))
                now_path.closeSubpath()
                
                now_indicator = self.scene.addPath(
                    now_path,
                    QPen(Qt.NoPen),
                    QBrush(QColor(255, 50, 50))
                )
                
                # Texto de "Agora"
                now_text = self.scene.addText("AGORA")
                now_text.setDefaultTextColor(QColor(255, 50, 50))
                font = QFont("Arial", 7)
                font.setBold(True)
                now_text.setFont(font)
                now_text.setPos(x_now - 15, 12)
        
        # Ajustar visualização para mostrar tudo
        self.view.resetTransform()
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
    def clear(self):
        """Limpar visualização"""
        self.activities = []
        self.scene.clear()
        
    def resizeEvent(self, event):
        """Manipulador para redimensionamento do widget"""
        super().resizeEvent(event)
        if not self.scene.items():
            return
            
        # Reajustar visualização
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)