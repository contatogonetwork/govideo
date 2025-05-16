#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Utilitários para manipulação de arquivos de mídia
Data: 2025-05-15
Autor: GONETWORK AI
"""

import os
import logging
import cv2
from PyQt5.QtGui import QPixmap, QImage
import numpy as np

logger = logging.getLogger(__name__)

def generate_thumbnail(file_path, size=(120, 90)):
    """
    Gera uma miniatura para um arquivo de mídia
    
    Args:
        file_path (str): Caminho para o arquivo
        size (tuple): Tamanho da miniatura (largura, altura)
        
    Returns:
        QPixmap: Miniatura gerada ou None em caso de erro
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado: {file_path}")
            return None
        
        # Verificar extensão do arquivo
        _, ext = os.path.splitext(file_path.lower())
        
        # Processar imagens estáticas
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            return _generate_image_thumbnail(file_path, size)
        
        # Processar vídeos
        elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
            return _generate_video_thumbnail(file_path, size)
        
        # Tipo não suportado
        else:
            logger.warning(f"Tipo de arquivo não suportado para miniatura: {ext}")
            return None
    
    except Exception as e:
        logger.error(f"Erro ao gerar miniatura: {str(e)}")
        return None
        

def _generate_image_thumbnail(file_path, size):
    """Gera miniatura para imagens estáticas"""
    try:
        # Carregar imagem com OpenCV
        img = cv2.imread(file_path)
        if img is None:
            return None
        
        # Redimensionar mantendo a proporção
        h, w = img.shape[:2]
        target_w, target_h = size
        
        aspect = w / h
        target_aspect = target_w / target_h
        
        if aspect > target_aspect:
            # Imagem mais larga que a proporção alvo
            new_w = target_w
            new_h = int(target_w / aspect)
        else:
            # Imagem mais alta que a proporção alvo
            new_h = target_h
            new_w = int(target_h * aspect)
        
        img_resized = cv2.resize(img, (new_w, new_h))
        
        # Converter de BGR para RGB (OpenCV usa BGR por padrão)
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        
        # Converter para QImage e depois para QPixmap
        qimg = QImage(img_rgb.data, new_w, new_h, img_rgb.strides[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        return pixmap
    
    except Exception as e:
        logger.error(f"Erro ao gerar miniatura para imagem: {str(e)}")
        return None


def _generate_video_thumbnail(file_path, size):
    """Gera miniatura para arquivos de vídeo"""
    try:
        # Abrir o vídeo
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            logger.error(f"Não foi possível abrir o vídeo: {file_path}")
            return None
        
        # Obter o número total de frames
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Se o vídeo tem frames, pegar um frame do meio do vídeo
        if total_frames > 0:
            # Definir a posição para 10% do vídeo
            target_frame = max(1, int(total_frames * 0.1))
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            
            # Ler o frame
            ret, frame = cap.read()
            if not ret:
                # Se falhar, tentar o primeiro frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                
                if not ret:
                    logger.error(f"Não foi possível ler um frame do vídeo: {file_path}")
                    cap.release()
                    return None
        else:
            logger.error(f"Vídeo sem frames: {file_path}")
            cap.release()
            return None
        
        # Liberar o vídeo
        cap.release()
        
        # Adicionar ícone de reprodução sobreposto
        frame = _add_play_icon(frame)
        
        # Redimensionar o frame
        h, w = frame.shape[:2]
        target_w, target_h = size
        
        aspect = w / h
        target_aspect = target_w / target_h
        
        if aspect > target_aspect:
            # Frame mais largo que a proporção alvo
            new_w = target_w
            new_h = int(target_w / aspect)
        else:
            # Frame mais alto que a proporção alvo
            new_h = target_h
            new_w = int(target_h * aspect)
        
        frame_resized = cv2.resize(frame, (new_w, new_h))
        
        # Converter de BGR para RGB (OpenCV usa BGR por padrão)
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        
        # Converter para QImage e depois para QPixmap
        qimg = QImage(frame_rgb.data, new_w, new_h, frame_rgb.strides[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        return pixmap
    
    except Exception as e:
        logger.error(f"Erro ao gerar miniatura para vídeo: {str(e)}")
        return None


def _add_play_icon(frame):
    """Adiciona um ícone de reprodução ao frame do vídeo"""
    try:
        h, w = frame.shape[:2]
        
        # Tamanho do triângulo baseado no tamanho da imagem
        icon_size = min(w, h) // 3
        
        # Criar triângulo para ícone de reprodução
        center_x, center_y = w // 2, h // 2
        
        triangle_pts = np.array([
            [center_x - icon_size // 2, center_y - icon_size // 2],
            [center_x - icon_size // 2, center_y + icon_size // 2],
            [center_x + icon_size // 2, center_y]
        ], np.int32)
        
        # Desenhar círculo semitransparente
        circle_radius = icon_size // 1.5
        overlay = frame.copy()
        cv2.circle(overlay, (center_x, center_y), int(circle_radius), (0, 0, 0), -1)
        
        # Aplicar transparência
        alpha = 0.6
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Desenhar triângulo branco
        cv2.fillPoly(frame, [triangle_pts], (255, 255, 255))
        
        return frame
    
    except Exception as e:
        logger.error(f"Erro ao adicionar ícone de reprodução: {str(e)}")
        return frame
