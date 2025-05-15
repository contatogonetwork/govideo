#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Análise de Vídeo com IA
Implementação para detecção de momentos-chave, faces e análise de áudio
Data: 2025-05-15
"""

import os
import logging
import numpy as np
import cv2
import tempfile
import json
from datetime import timedelta, datetime
import subprocess
import shutil

logger = logging.getLogger(__name__)

class VideoAnalyzer:
    """Classe para análise de vídeo usando técnicas de IA"""
    
    def __init__(self, models_path="resources/models"):
        """Inicializa o analisador de vídeo
        
        Args:
            models_path: Caminho para modelos pré-treinados
        """
        self.models_path = models_path
        self.face_cascade = None
        self.initialize_models()
        
    def initialize_models(self):
        """Inicializa modelos de detecção"""
        try:
            # Criar diretório de modelos se não existir
            os.makedirs(self.models_path, exist_ok=True)
            
            # Carregar Haar Cascade para detecção de faces
            face_cascade_path = os.path.join(self.models_path, 'haarcascade_frontalface_default.xml')
            
            # Se o arquivo não existir, usar o do OpenCV diretamente
            if not os.path.exists(face_cascade_path):
                face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                
            if os.path.exists(face_cascade_path):
                self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
                logger.info("Modelo de detecção facial carregado com sucesso")
            else:
                logger.error("Modelo de detecção facial não encontrado")
                
        except Exception as e:
            logger.error(f"Erro ao inicializar modelos: {str(e)}")
            
    def extract_key_frames(self, video_path, sensitivity=0.5, max_frames=20):
        """Extrair frames-chave de um vídeo baseado em mudanças de cena
        
        Args:
            video_path (str): Caminho do vídeo
            sensitivity (float): Sensibilidade para detecção de mudança (0.0-1.0)
            max_frames (int): Número máximo de frames a retornar
            
        Returns:
            list: Lista de dicionários com frames-chave (timestamp e caminho da imagem)
        """
        if not os.path.exists(video_path):
            logger.error(f"Arquivo não encontrado: {video_path}")
            return []
            
        try:
            # Criar diretório temporário para os frames
            temp_dir = tempfile.mkdtemp()
            
            # Abrir vídeo com OpenCV
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Não foi possível abrir o vídeo: {video_path}")
                return []
                
            # Obter FPS e duração
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if fps <= 0 or total_frames <= 0:
                logger.error("Não foi possível determinar FPS ou total de frames")
                cap.release()
                return []
                
            # Ajustar limiar baseado na sensibilidade
            threshold = 35.0 * (1.0 - sensitivity)
            
            # Ler primeiro frame
            ret, prev_frame = cap.read()
            if not ret:
                logger.error("Não foi possível ler o primeiro frame")
                cap.release()
                return []
                
            prev_frame_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            
            key_frames = []
            frame_number = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame_number += 1
                
                # Processar apenas 1 a cada 15 frames para eficiência
                if frame_number % 15 != 0:
                    continue
                    
                # Converter para escala de cinza
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Calcular diferença absoluta entre frames
                diff = cv2.absdiff(prev_frame_gray, gray)
                non_zero = np.count_nonzero(diff > 25)
                score = non_zero / diff.size
                
                # Se a mudança for significativa, salvar frame-chave
                if score * 100 > threshold:
                    timestamp = frame_number / fps
                    timestamp_str = str(timedelta(seconds=int(timestamp)))
                    frame_path = os.path.join(temp_dir, f"frame_{frame_number:06d}.jpg")
                    
                    cv2.imwrite(frame_path, frame)
                    
                    key_frames.append({
                        'frame_number': frame_number,
                        'timestamp': timestamp,
                        'timestamp_str': timestamp_str,
                        'path': frame_path,
                        'score': score
                    })
                    
                    # Atualizar frame anterior
                    prev_frame_gray = gray.copy()
                    
            cap.release()
            
            # Limitar número de frames se necessário
            key_frames.sort(key=lambda x: x['score'], reverse=True)
            return key_frames[:max_frames]
            
        except Exception as e:
            logger.error(f"Erro ao extrair frames-chave: {str(e)}")
            return []
            
    def detect_faces(self, video_path, sample_rate=30):
        """Detectar rostos no vídeo e momentos em que aparecem
        
        Args:
            video_path (str): Caminho do vídeo
            sample_rate (int): Taxa de amostragem (analisar 1 a cada N frames)
            
        Returns:
            list: Lista com detecções de rostos com timestamp
        """
        if not self.face_cascade:
            logger.error("Detector facial não inicializado")
            return []
            
        if not os.path.exists(video_path):
            logger.error(f"Arquivo não encontrado: {video_path}")
            return []
            
        try:
            # Abrir vídeo com OpenCV
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Não foi possível abrir o vídeo: {video_path}")
                return []
                
            # Obter FPS
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                logger.error("Não foi possível determinar FPS")
                cap.release()
                return []
                
            detections = []
            frame_number = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame_number += 1
                
                # Processar apenas 1 a cada N frames
                if frame_number % sample_rate != 0:
                    continue
                    
                # Converter para escala de cinza
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detectar faces
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                if len(faces) > 0:
                    timestamp = frame_number / fps
                    timestamp_str = str(timedelta(seconds=int(timestamp)))
                    
                    detections.append({
                        'frame_number': frame_number,
                        'timestamp': timestamp,
                        'timestamp_str': timestamp_str,
                        'num_faces': len(faces),
                        'faces': faces.tolist()  # Converter para lista para serialização
                    })
                    
            cap.release()
            return detections
            
        except Exception as e:
            logger.error(f"Erro na detecção de faces: {str(e)}")
            return []
            
    def analyze_audio_energy(self, video_path, window_size=1.0):
        """Analisar picos de energia no áudio para sincronização
        
        Args:
            video_path (str): Caminho do vídeo
            window_size (float): Tamanho da janela em segundos para análise
            
        Returns:
            list: Lista com momentos de picos de energia
        """
        if not os.path.exists(video_path):
            logger.error(f"Arquivo não encontrado: {video_path}")
            return []
            
        try:
            # Diretório temporário para extração de áudio
            temp_dir = tempfile.mkdtemp()
            audio_path = os.path.join(temp_dir, "audio.wav")
            
            # Extrair áudio com FFmpeg
            ffmpeg_cmd = [
                "ffmpeg", "-i", video_path, 
                "-vn", "-acodec", "pcm_s16le", 
                "-ar", "44100", "-ac", "1", 
                audio_path, "-y"
            ]
            
            try:
                subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                logger.error(f"Erro ao extrair áudio com FFmpeg: {str(e)}")
                return []
                
            if not os.path.exists(audio_path):
                logger.error("Extração de áudio falhou")
                return []
                
            # Usar OpenCV para análise (simplificada)
            # Em uma implementação completa, usaria librosa ou biblioteca similar
            cap = cv2.VideoCapture(audio_path)
            if not cap.isOpened():
                logger.error("Não foi possível abrir o áudio extraído")
                return []
                
            # Ler áudio como se fosse vídeo (para simplicidade)
            audio_samples = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                audio_samples.append(np.mean(np.abs(frame)))
                
            cap.release()
            
            if len(audio_samples) == 0:
                logger.error("Não foi possível extrair amostras de áudio")
                return []
                
            # Normalizar amostras
            audio_samples = np.array(audio_samples)
            audio_samples = (audio_samples - np.min(audio_samples)) / (np.max(audio_samples) - np.min(audio_samples))
            
            # Calcular média móvel para suavização
            window = int(window_size * 10)  # Assumindo 10 amostras por segundo
            window = max(1, window)
            smoothed = np.convolve(audio_samples, np.ones(window)/window, mode='same')
            
            # Detectar picos (aproximação simplificada)
            mean_energy = np.mean(smoothed)
            std_energy = np.std(smoothed)
            threshold = mean_energy + 1.5 * std_energy
            
            # Encontrar picos
            peaks = []
            for i in range(1, len(smoothed)-1):
                if smoothed[i] > threshold and smoothed[i] > smoothed[i-1] and smoothed[i] > smoothed[i+1]:
                    timestamp = i / 10.0  # Assumindo 10 amostras por segundo
                    peaks.append({
                        'timestamp': timestamp,
                        'timestamp_str': str(timedelta(seconds=int(timestamp))),
                        'energy': float(smoothed[i])
                    })
                    
            # Limpar arquivos temporários
            if os.path.exists(audio_path):
                os.remove(audio_path)
            os.rmdir(temp_dir)
                
            return peaks
            
        except Exception as e:
            logger.error(f"Erro na análise de áudio: {str(e)}")
            return []
            
    def summarize_video(self, video_path):
        """Gerar resumo do vídeo com momentos-chave, faces e pontos de energia
        
        Args:
            video_path (str): Caminho do vídeo
            
        Returns:
            dict: Dicionário com resumo do vídeo
        """
        if not os.path.exists(video_path):
            logger.error(f"Arquivo não encontrado: {video_path}")
            return {}
            
        try:
            # Obter metadados básicos do vídeo
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Não foi possível abrir o vídeo: {video_path}")
                return {}
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            duration = total_frames / fps if fps > 0 else 0
            cap.release()
            
            # Estrutura para o resumo
            summary = {
                'metadata': {
                    'path': video_path,
                    'filename': os.path.basename(video_path),
                    'fps': fps,
                    'total_frames': total_frames,
                    'width': width,
                    'height': height,
                    'duration': duration,
                    'duration_str': str(timedelta(seconds=int(duration)))
                },
                'analysis': {}
            }
            
            # Extrair frames-chave
            logger.info(f"Extraindo frames-chave de {video_path}")
            summary['analysis']['key_frames'] = self.extract_key_frames(
                video_path, 
                sensitivity=0.7, 
                max_frames=10
            )
            
            # Detectar faces
            logger.info(f"Detectando faces em {video_path}")
            face_detections = self.detect_faces(video_path, sample_rate=24)
            
            # Agrupar detecções de faces para evitar duplicações muito próximas
            grouped_faces = []
            last_timestamp = -5.0  # Iniciar com valor que garante que o primeiro será incluído
            
            for detection in face_detections:
                # Se for pelo menos 3 segundos depois da última detecção
                if detection['timestamp'] - last_timestamp > 3.0:
                    grouped_faces.append(detection)
                    last_timestamp = detection['timestamp']
                    
            summary['analysis']['faces'] = grouped_faces
            
            # Analisar energia de áudio
            logger.info(f"Analisando áudio de {video_path}")
            energy_peaks = self.analyze_audio_energy(video_path)
            
            # Filtrar picos muito próximos (manter intervalo de pelo menos 2 segundos)
            filtered_peaks = []
            last_peak = -5.0
            
            for peak in energy_peaks:
                if peak['timestamp'] - last_peak > 2.0:
                    filtered_peaks.append(peak)
                    last_peak = peak['timestamp']
                    
            summary['analysis']['audio_peaks'] = filtered_peaks
            
            # Adicionar timestamp de geração
            summary['generated'] = datetime.now().isoformat()
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo do vídeo: {str(e)}")
            return {}
            
    def generate_thumbnails(self, video_path, output_folder=None, num_thumbnails=5, 
                          thumbnail_size=(320, 180)):
        """Gerar miniaturas para o vídeo
        
        Args:
            video_path (str): Caminho do vídeo
            output_folder (str, opcional): Pasta para salvar miniaturas (None = usar temp)
            num_thumbnails (int): Número de miniaturas a gerar
            thumbnail_size (tuple): Tamanho das miniaturas em pixels (largura, altura)
            
        Returns:
            list: Lista de caminhos para as miniaturas geradas
        """
        if not os.path.exists(video_path):
            logger.error(f"Arquivo não encontrado: {video_path}")
            return []
            
        try:
            # Criar diretório de saída se não especificado
            if output_folder is None:
                output_folder = tempfile.mkdtemp()
            else:
                os.makedirs(output_folder, exist_ok=True)
                
            # Abrir vídeo
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Não foi possível abrir o vídeo: {video_path}")
                return []
                
            # Obter duração total
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if fps <= 0 or total_frames <= 0:
                logger.error("Não foi possível determinar FPS ou total de frames")
                cap.release()
                return []
                
            duration = total_frames / fps
            
            # Calcular posições para as miniaturas (distribuídas ao longo do vídeo)
            thumbnail_positions = []
            if num_thumbnails == 1:
                thumbnail_positions = [duration / 2]  # Metade do vídeo
            else:
                # Evitar os primeiros e últimos 5% do vídeo (geralmente créditos ou telas pretas)
                usable_duration = duration * 0.9
                start_time = duration * 0.05
                
                for i in range(num_thumbnails):
                    pos = start_time + (i * usable_duration / (num_thumbnails - 1))
                    thumbnail_positions.append(pos)
                    
            # Gerar miniaturas
            thumbnail_paths = []
            
            for i, pos in enumerate(thumbnail_positions):
                # Definir posição no vídeo
                frame_pos = int(pos * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                
                # Ler frame
                ret, frame = cap.read()
                if not ret:
                    continue
                    
                # Redimensionar
                thumbnail = cv2.resize(frame, thumbnail_size)
                
                # Salvar miniatura
                thumbnail_path = os.path.join(output_folder, f"thumbnail_{i+1}.jpg")
                cv2.imwrite(thumbnail_path, thumbnail)
                thumbnail_paths.append(thumbnail_path)
                
            cap.release()
            return thumbnail_paths
            
        except Exception as e:
            logger.error(f"Erro ao gerar miniaturas: {str(e)}")
            return []
            
    def extract_metadata_from_video(self, video_path):
        """Extrair metadados técnicos do vídeo
        
        Args:
            video_path (str): Caminho do vídeo
            
        Returns:
            dict: Dicionário com metadados técnicos
        """
        if not os.path.exists(video_path):
            logger.error(f"Arquivo não encontrado: {video_path}")
            return {}
            
        metadata = {}
        
        try:
            # Tentar usar pymediainfo se disponível
            try:
                import pymediainfo
                media_info = pymediainfo.MediaInfo.parse(video_path)
                
                for track in media_info.tracks:
                    if track.track_type == 'General':
                        metadata['format'] = track.format
                        metadata['format_profile'] = track.format_profile
                        metadata['codec_id'] = track.codec_id
                        metadata['file_size'] = track.file_size
                        metadata['duration'] = track.duration / 1000.0 if track.duration else None
                        metadata['overall_bit_rate'] = track.overall_bit_rate
                        
                    elif track.track_type == 'Video':
                        metadata['video_format'] = track.format
                        metadata['video_format_profile'] = track.format_profile
                        metadata['video_codec'] = track.codec_id
                        metadata['width'] = track.width
                        metadata['height'] = track.height
                        metadata['aspect_ratio'] = track.display_aspect_ratio
                        metadata['frame_rate'] = track.frame_rate
                        metadata['bit_depth'] = track.bit_depth
                        metadata['color_space'] = track.color_space
                        
                    elif track.track_type == 'Audio':
                        metadata['audio_format'] = track.format
                        metadata['audio_codec'] = track.codec_id
                        metadata['audio_channels'] = track.channel_s
                        metadata['audio_sampling_rate'] = track.sampling_rate
                        metadata['audio_bit_rate'] = track.bit_rate
                        
                return metadata
                
            except ImportError:
                logger.warning("pymediainfo não disponível, usando OpenCV para metadados limitados")
        
            # Usar OpenCV como fallback para metadados básicos
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Não foi possível abrir o vídeo: {video_path}")
                return {}
                
            # Obter metadados básicos
            metadata['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            metadata['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            metadata['fps'] = cap.get(cv2.CAP_PROP_FPS)
            metadata['frame_count'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            metadata['duration'] = metadata['frame_count'] / metadata['fps'] if metadata['fps'] > 0 else None
            
            cap.release()
            
            return metadata
            
        except Exception as e:
            logger.error(f"Erro ao extrair metadados do vídeo: {str(e)}")
            return {}