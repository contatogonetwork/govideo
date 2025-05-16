#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Gerador de relatórios em PDF
Data: 2025-05-15
Autor: GONETWORK AI
"""

import os
import logging
import tempfile
from io import BytesIO
from datetime import datetime

# Importações do ReportLab
from reportlab.lib.pagesizes import A4, letter, A3, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, ListFlowable, ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie

# Importações dos modelos necessários para EventReportGenerator
from core.database import Event, Activity, TeamAssignment, Delivery, Activation

logger = logging.getLogger(__name__)

class PDFReport:
    """Classe para geração de relatórios PDF profissionais"""
    
    def __init__(self, db_session=None):
        """
        Inicializa o gerador de relatórios
        
        Args:
            db_session: Sessão SQLAlchemy (opcional)
        """
        self.db = db_session
        self.styles = getSampleStyleSheet()
        self.current_event = None
        
        # Criar estilos personalizados
        self._create_custom_styles()
        
        # Configurações visuais
        self.company_logo = None
        self.event_logo = None
        self.color_primary = colors.HexColor('#1976D2')  # Azul
        self.color_secondary = colors.HexColor('#388E3C')  # Verde
        self.color_accent = colors.HexColor('#FFC107')  # Amarelo
        
        # Diretório temporário para arquivos
        self.temp_dir = tempfile.mkdtemp(prefix="govideo_reports_")
    
    def _create_custom_styles(self):
        """Cria estilos personalizados para os relatórios"""
        self.styles.add(
            ParagraphStyle(
                name='Title',
                parent=self.styles['Title'],
                fontSize=24,
                leading=30,
                textColor=colors.HexColor('#0D47A1'),
                alignment=TA_CENTER,
                spaceAfter=20
            )
        )
        
        self.styles.add(
            ParagraphStyle(
                name='Subtitle',
                parent=self.styles['Heading2'],
                fontSize=18,
                leading=22,
                textColor=colors.HexColor('#1976D2'),
                alignment=TA_LEFT,
                spaceAfter=12
            )
        )
        
        self.styles.add(
            ParagraphStyle(
                name='NormalCentered',
                parent=self.styles['Normal'],
                alignment=TA_CENTER
            )
        )
        
        self.styles.add(
            ParagraphStyle(
                name='Caption',
                parent=self.styles['Normal'],
                fontSize=8,
                leading=10,
                textColor=colors.darkgray
            )
        )
        
    def set_current_event(self, event):
        """Define o evento atual para os relatórios"""
        self.current_event = event
        
    def set_company_logo(self, logo_path):
        """Define o logo da empresa para os relatórios"""
        self.company_logo = logo_path
        
    def set_event_logo(self, logo_path):
        """Define o logo do evento para os relatórios"""
        self.event_logo = logo_path
        
    def generate_sponsor_activation_report(self, activation, output_path=None):
        """
        Gera um relatório detalhado de uma ativação patrocinada
        
        Args:
            activation: Objeto SponsorActivation
            output_path: Caminho onde salvar o arquivo (opcional)
            
        Returns:
            str: Caminho do arquivo gerado
        """
        from models.activation_evidence import ActivationEvidence
        from PyQt5.QtWidgets import QFileDialog
        
        # Determinar caminho de saída
        if not output_path:
            # Gerar nome de arquivo padrão
            safe_name = "".join(c for c in activation.name if c.isalnum() or c in " _-").strip()
            safe_name = safe_name.replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"activation_{safe_name}_{timestamp}.pdf"
            
            output_path, _ = QFileDialog.getSaveFileName(
                None,
                "Salvar Relatório de Ativação",
                default_name,
                "Arquivos PDF (*.pdf)"
            )
            
            if not output_path:
                logger.info("Geração de relatório cancelada pelo usuário")
                return None
        
        # Criar documento
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            title=f"Relatório de Ativação: {activation.name}",
            author="GONETWORK AI"
        )
        
        # Elementos do documento
        elements = []
        
        # Adicionar cabeçalho do relatório
        elements.append(Paragraph("Relatório de Ativação Patrocinada", self.styles['Title']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Logo do patrocinador (se existir)
        if activation.sponsor and hasattr(activation.sponsor, 'logo_path') and activation.sponsor.logo_path:
            try:
                logo = Image(activation.sponsor.logo_path)
                logo.drawHeight = 1.2*inch
                logo.drawWidth = 2*inch
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 0.2*inch))
            except Exception as e:
                logger.warning(f"Não foi possível carregar o logo: {str(e)}")
        
        # Nome da ativação
        elements.append(Paragraph(activation.name, self.styles['Subtitle']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Informações básicas
        data = [
            ["Patrocinador", activation.sponsor.name if activation.sponsor else "N/A"],
            ["Data", activation.scheduled_date.strftime("%d/%m/%Y") if activation.scheduled_date else "N/A"],
            ["Local", activation.location or "N/A"],
            ["Status", activation.status.capitalize() if activation.status else "N/A"],
            ["Responsável", activation.responsible.name if hasattr(activation, 'responsible') and activation.responsible else "N/A"],
            ["Público Alvo", activation.target_audience or "N/A"]
        ]
        
        info_table = Table(data, colWidths=[120, 350])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (1, 0), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Descrição
        if activation.description:
            elements.append(Paragraph("Descrição", self.styles['Subtitle']))
            elements.append(Paragraph(activation.description, self.styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Evidências
        elements.append(Paragraph("Evidências Registradas", self.styles['Subtitle']))
        
        if self.db:
            # Buscar evidências do banco de dados
            evidences = self.db.query(ActivationEvidence).filter(
                ActivationEvidence.activation_id == activation.id
            ).all()
            
            if evidences:
                # Tabela com informações das evidências
                evidence_data = [["Tipo", "Descrição", "Adicionada em", "Usuário"]]
                
                for evidence in evidences:
                    evidence_data.append([
                        evidence.type_name,
                        evidence.description or "N/A",
                        evidence.created_at.strftime("%d/%m/%Y %H:%M") if evidence.created_at else "N/A",
                        evidence.user.name if hasattr(evidence, 'user') and evidence.user else "N/A"
                    ])
                
                evidence_table = Table(evidence_data, repeatRows=1)
                evidence_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(evidence_table)
                elements.append(Spacer(1, 0.2*inch))
                
                # Adicionar imagens de evidências
                images_added = 0
                for evidence in evidences:
                    if evidence.file_type == "image" and os.path.exists(evidence.file_path):
                        # Limitar a 4 imagens por página
                        if images_added % 4 == 0 and images_added > 0:
                            elements.append(PageBreak())
                            elements.append(Paragraph("Continuação - Imagens de Evidências", self.styles['Subtitle']))
                        
                        try:
                            img = Image(evidence.file_path)
                            img.drawHeight = 2.5*inch
                            img.drawWidth = 3.5*inch
                            
                            # Adicionar legenda
                            caption = evidence.description or f"Evidência #{evidence.id}"
                            
                            elements.append(img)
                            elements.append(Paragraph(caption, self.styles['Caption']))
                            elements.append(Spacer(1, 0.1*inch))
                            
                            images_added += 1
                        except Exception as e:
                            logger.warning(f"Não foi possível carregar a imagem {evidence.file_path}: {str(e)}")
            else:
                elements.append(Paragraph("Nenhuma evidência registrada para esta ativação.", self.styles['Normal']))
        else:
            elements.append(Paragraph("Não há conexão com o banco de dados para buscar evidências.", self.styles['Normal']))
        
        # Adicionar rodapé com data de geração
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles['Caption']
        ))
        
        # Construir documento
        doc.build(elements)
        
        logger.info(f"Relatório de ativação gerado com sucesso: {output_path}")
        return output_path
    
    def generate_team_schedule_report(self, event, output_path=None):
        """
        Gera um relatório de agenda da equipe
        
        Args:
            event: Objeto Event
            output_path: Caminho onde salvar o arquivo (opcional)
            
        Returns:
            str: Caminho do arquivo gerado
        """
        from models.team import Team, TeamMember
        from models.event import Activity
        from PyQt5.QtWidgets import QFileDialog
        
        # Determinar caminho de saída
        if not output_path:
            # Gerar nome de arquivo padrão
            safe_name = "".join(c for c in event.name if c.isalnum() or c in " _-").strip()
            safe_name = safe_name.replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"team_schedule_{safe_name}_{timestamp}.pdf"
            
            output_path, _ = QFileDialog.getSaveFileName(
                None,
                "Salvar Agenda da Equipe",
                default_name,
                "Arquivos PDF (*.pdf)"
            )
            
            if not output_path:
                logger.info("Geração de relatório cancelada pelo usuário")
                return None
        
        # Criar documento
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            title=f"Agenda da Equipe: {event.name}",
            author="GONETWORK AI"
        )
        
        # Elementos do documento
        elements = []
        
        # Adicionar cabeçalho do relatório
        elements.append(Paragraph("Agenda da Equipe", self.styles['Title']))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(event.name, self.styles['Subtitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        if self.db:
            # Buscar equipes e atividades
            teams = self.db.query(Team).filter(Team.event_id == event.id).all()
            
            if not teams:
                elements.append(Paragraph("Nenhuma equipe registrada para este evento.", self.styles['Normal']))
            else:
                # Para cada equipe, mostrar suas atividades
                for team in teams:
                    elements.append(Paragraph(f"Equipe: {team.name}", self.styles['Subtitle']))
                    
                    # Membros da equipe
                    elements.append(Paragraph("Membros da Equipe:", self.styles['Normal']))
                    
                    team_members = self.db.query(TeamMember).filter(TeamMember.team_id == team.id).all()
                    
                    if team_members:
                        member_data = [["Nome", "Função", "Email", "Telefone"]]
                        
                        for member in team_members:
                            member_data.append([
                                member.name,
                                member.role or "N/A",
                                member.email or "N/A",
                                member.phone or "N/A"
                            ])
                        
                        member_table = Table(member_data, repeatRows=1)
                        member_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        
                        elements.append(member_table)
                    else:
                        elements.append(Paragraph("Nenhum membro registrado nesta equipe.", self.styles['Normal']))
                    
                    elements.append(Spacer(1, 0.2*inch))
                    
                    # Atividades desta equipe
                    elements.append(Paragraph("Agenda de Atividades:", self.styles['Normal']))
                    
                    # Buscar atividades associadas a esta equipe
                    activities = self.db.query(Activity).filter(
                        Activity.event_id == event.id,
                        Activity.team_id == team.id
                    ).order_by(
                        Activity.start_time
                    ).all()
                    
                    if activities:
                        activity_data = [["Data", "Hora", "Atividade", "Local", "Responsável", "Status"]]
                        
                        for activity in activities:
                            date_str = activity.start_time.strftime("%d/%m/%Y") if activity.start_time else "N/A"
                            time_str = activity.start_time.strftime("%H:%M") if activity.start_time else "N/A"
                            
                            activity_data.append([
                                date_str,
                                time_str,
                                activity.name,
                                activity.location or "N/A",
                                activity.responsible.name if hasattr(activity, 'responsible') and activity.responsible else "N/A",
                                activity.status.capitalize() if activity.status else "N/A"
                            ])
                        
                        activity_table = Table(activity_data, repeatRows=1)
                        activity_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        
                        elements.append(activity_table)
                    else:
                        elements.append(Paragraph("Nenhuma atividade registrada para esta equipe.", self.styles['Normal']))
                    
                    # Adicionar quebra de página entre equipes
                    elements.append(PageBreak())
        else:
            elements.append(Paragraph("Não há conexão com o banco de dados para buscar equipes.", self.styles['Normal']))
        
        # Adicionar rodapé com data de geração
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            self.styles['Caption']
        ))
        
        # Construir documento
        doc.build(elements)
        
        logger.info(f"Relatório de agenda da equipe gerado com sucesso: {output_path}")
        return output_path


class EventReportGenerator:
    """Gerador de relatórios de eventos completos"""
    
    def __init__(self, session, event_id):
        """
        Inicializa o gerador de relatórios de eventos
        
        Args:
            session: Sessão SQLAlchemy
            event_id: ID do evento para o qual gerar o relatório
        """
        self.session = session
        self.event_id = event_id
        self.event = self.session.query(Event).get(event_id)
        if not self.event:
            raise ValueError(f"Evento com ID {event_id} não encontrado")
    
    def generate_complete_report(self, output_path, logo_path=None, include_charts=True):
        """
        Gera um relatório completo do evento em PDF
        
        Args:
            output_path: Caminho para salvar o arquivo PDF
            logo_path: Caminho opcional para o logo a ser incluído na capa
            include_charts: Se deve incluir gráficos no relatório
            
        Returns:
            bool: True se o relatório foi gerado com sucesso, False caso contrário
        """
        if not self.event:
            return False
            
        # Criar relatório
        report = PDFReport(self.session)
        
        # Configurar documento
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Lista de elementos a serem adicionados ao PDF
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading1_style = styles['Heading1']
        heading2_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Título do relatório
        report_title = f"Relatório de Evento: {self.event.name}"
        elements.append(Paragraph(report_title, title_style))
        elements.append(Spacer(1, 12))
        
        # Subtítulo com local e data
        subtitle = f"{self.event.location} • {self.event.start_date.strftime('%d/%m/%Y')} a {self.event.end_date.strftime('%d/%m/%Y')}"
        elements.append(Paragraph(subtitle, heading2_style))
        elements.append(Spacer(1, 12))
        
        # Descrição do evento
        if self.event.description:
            elements.append(Paragraph(self.event.description, normal_style))
            elements.append(Spacer(1, 12))
        
        # Logo
        if logo_path and os.path.exists(logo_path):
            img = Image(logo_path, width=200, height=100)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 24))
        
        # Sumário Executivo
        elements.append(Paragraph("Sumário Executivo", heading1_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            f"Este relatório apresenta um resumo completo do evento {self.event.name}, realizado em {self.event.location} entre "
            f"{self.event.start_date.strftime('%d/%m/%Y')} e {self.event.end_date.strftime('%d/%m/%Y')}.",
            normal_style
        ))
        elements.append(Spacer(1, 12))
        
        # Dados gerais em formato de tabela
        event_info = [
            ["Cliente:", self.event.client if hasattr(self.event, 'client') and self.event.client else "N/A"],
            ["Local:", self.event.location],
            ["Data de início:", self.event.start_date.strftime("%d/%m/%Y")],
            ["Data de término:", self.event.end_date.strftime("%d/%m/%Y")],
            ["Status:", self.event.status],
            ["Responsável:", self.event.created_by if hasattr(self.event, 'created_by') and self.event.created_by else "N/A"]
        ]
        
        event_table = Table(
            event_info, 
            colWidths=[100, 400]
        )
        event_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0, colors.white),  # Sem bordas
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),  # Alinhar à direita primeira coluna
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),   # Alinhar à esquerda segunda coluna
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Negrito na primeira coluna
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(event_table)
        
        elements.append(Spacer(1, 20))
        
        # Estatísticas do evento
        if include_charts:
            elements.append(Paragraph("Estatísticas do Evento", heading2_style))
            elements.append(Spacer(1, 12))
            
            # Status das atividades
            activity_stats = self._get_activity_stats()
            if activity_stats and activity_stats["labels"] and activity_stats["values"]:
                self._add_pie_chart(elements, activity_stats["labels"], activity_stats["values"], "Status das Atividades")
                
            # Status das entregas
            delivery_stats = self._get_delivery_stats()
            if delivery_stats and delivery_stats["labels"] and delivery_stats["values"]:
                self._add_pie_chart(elements, delivery_stats["labels"], delivery_stats["values"], "Status das Entregas")
                
            elements.append(PageBreak())
        
        # Seção de Atividades
        elements.append(Paragraph("Programação e Cronograma", heading1_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            "Abaixo estão listadas todas as atividades programadas para o evento, com seus respectivos status, responsáveis e localizações.",
            normal_style
        ))
        elements.append(Spacer(1, 12))
        
        activities = self._get_activities()
        if activities:
            activity_data = [["Horário", "Atividade", "Local", "Responsável", "Status"]]
            for activity in activities:
                stage_name = "N/A"
                if hasattr(activity, 'stage') and activity.stage:
                    stage_name = activity.stage.name
                
                responsible_name = "N/A"
                # Tentamos encontrar o responsável nas atribuições de equipe
                if activity.team_assignments:
                    for assignment in activity.team_assignments:
                        if assignment.member:
                            responsible_name = assignment.member.name
                            break
                
                activity_data.append([
                    activity.start_time.strftime("%d/%m %H:%M"),
                    activity.name,
                    stage_name,
                    responsible_name,
                    activity.type if hasattr(activity, 'type') else "N/A"
                ])
            
            activity_table = Table(activity_data, repeatRows=1)
            activity_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(activity_table)
        else:
            elements.append(Paragraph("Nenhuma atividade registrada para este evento.", normal_style))
            
        elements.append(PageBreak())
        
        # Seção de Entregas
        elements.append(Paragraph("Entregas e Produtos Finais", heading1_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            "Esta seção apresenta as entregas associadas ao evento, incluindo status de produção e prazos.",
            normal_style
        ))
        elements.append(Spacer(1, 12))
        
        deliveries = self._get_deliveries()
        if deliveries:
            delivery_data = [["Título", "Tipo", "Editor", "Prazo", "Status", "Progresso"]]
            for delivery in deliveries:
                deadline = "Sem prazo"
                if delivery.deadline:
                    deadline = delivery.deadline.strftime("%d/%m/%Y")
                
                editor_name = "N/A"
                if hasattr(delivery, 'responsible') and delivery.responsible:
                    editor_name = delivery.responsible.name
                
                progress = "N/A"
                if hasattr(delivery, 'status'):
                    # Aqui podemos mapear o status para um valor de progresso aproximado
                    progress_map = {
                        'pending': '0%',
                        'in_progress': '50%',
                        'review': '80%',
                        'completed': '100%',
                        'delivered': '100%'
                    }
                    progress = progress_map.get(delivery.status, "N/A")
                
                delivery_data.append([
                    delivery.title,
                    delivery.format_specs if hasattr(delivery, 'format_specs') else "N/A",
                    editor_name,
                    deadline,
                    delivery.status if hasattr(delivery, 'status') else "N/A",
                    progress
                ])
            
            delivery_table = Table(delivery_data, repeatRows=1)
            delivery_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(delivery_table)
        else:
            elements.append(Paragraph("Nenhuma entrega registrada para este evento.", normal_style))
            
        elements.append(PageBreak())
        
        # Seção de Equipe
        elements.append(Paragraph("Equipe e Atuação", heading1_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            "Detalhes sobre a equipe designada para o evento e suas atribuições.",
            normal_style
        ))
        elements.append(Spacer(1, 12))
        
        team_assignments = self._get_team_assignments()
        if team_assignments:
            team_data = [["Membro", "Função", "Início", "Término", "Localização"]]
            for assignment in team_assignments:
                member_name = "N/A"
                if hasattr(assignment, 'member') and assignment.member:
                    member_name = assignment.member.name
                
                role = "N/A"
                if hasattr(assignment, 'member') and assignment.member:
                    role = assignment.member.role
                
                activity_name = "N/A"
                if hasattr(assignment, 'activity') and assignment.activity:
                    activity_name = assignment.activity.name
                
                team_data.append([
                    member_name,
                    role,
                    assignment.start_time.strftime("%d/%m %H:%M") if assignment.start_time else "N/A",
                    assignment.end_time.strftime("%d/%m %H:%M") if assignment.end_time else "N/A",
                    activity_name
                ])
            
            team_table = Table(team_data, repeatRows=1)
            team_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(team_table)
        else:
            elements.append(Paragraph("Nenhuma atribuição de equipe registrada para este evento.", normal_style))
            
        # Notas e observações finais
        elements.append(PageBreak())
        elements.append(Paragraph("Observações Finais", heading1_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            "Observações gerais sobre o evento, lições aprendidas e recomendações para futuros eventos similares.",
            normal_style
        ))
        elements.append(Spacer(1, 12))
        
        if hasattr(self.event, 'description') and self.event.description:
            elements.append(Paragraph(self.event.description, normal_style))
        else:
            elements.append(Paragraph("Nenhuma observação registrada para este evento.", normal_style))
        
        # Rodapé
        elements.append(Spacer(1, inch))
        elements.append(Paragraph(
            f"Relatório gerado por GoNetwork AI em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            styles['Caption']
        ))
        
        # Construir o documento
        doc.build(elements)
        logger.info(f"Relatório completo do evento gerado com sucesso: {output_path}")
        return True
    
    def _add_pie_chart(self, elements, labels, values, title):
        """
        Adiciona um gráfico de pizza ao relatório
        
        Args:
            elements: Lista de elementos do ReportLab
            labels: Lista de rótulos
            values: Lista de valores
            title: Título do gráfico
        """
        drawing = Drawing(400, 300)
        
        pie = Pie()
        pie.x = 150
        pie.y = 150
        pie.width = 120
        pie.height = 120
        pie.data = values
        pie.labels = labels
        pie.slices.strokeWidth = 0.5
        
        drawing.add(pie)
        
        elements.append(Paragraph(title, getSampleStyleSheet()['Heading3']))
        elements.append(drawing)
        elements.append(Spacer(1, 12))
    
    def _get_activities(self):
        """
        Recupera atividades do evento
        
        Returns:
            list: Lista de objetos Activity
        """
        # Recuperar todas as atividades relacionadas ao evento através dos estágios
        activities = []
        
        stages = self.session.query(Event).get(self.event_id).stages
        for stage in stages:
            activities.extend(stage.activities)
        
        # Ordenar por data/hora de início
        activities.sort(key=lambda a: a.start_time)
        return activities
    
    def _get_deliveries(self):
        """
        Recupera entregas do evento
        
        Returns:
            list: Lista de objetos Delivery
        """
        return self.session.query(Delivery).filter(
            Delivery.event_id == self.event_id
        ).all()
    
    def _get_team_assignments(self):
        """
        Recupera atribuições de equipe do evento
        
        Returns:
            list: Lista de objetos TeamAssignment
        """
        assignments = []
        activities = self._get_activities()
        
        # Coletar IDs de atividades
        activity_ids = [activity.id for activity in activities]
        
        # Buscar atribuições de equipe para essas atividades
        if activity_ids:
            assignments = self.session.query(TeamAssignment).filter(
                TeamAssignment.activity_id.in_(activity_ids)
            ).all()
        
        return assignments
    
    def _get_sponsor_activations(self):
        """
        Recupera ativações de patrocinadores do evento
        
        Returns:
            list: Lista de objetos Activation
        """
        # Verificar se há ativações diretamente relacionadas ao evento
        return self.session.query(Activation).filter(
            Activation.event_id == self.event_id
        ).all()
    
    def _get_activity_stats(self):
        """
        Calcula estatísticas de atividades
        
        Returns:
            dict: Dicionário com labels e valores para gráficos
        """
        activities = self._get_activities()
        if not activities:
            return None
            
        status_count = {}
        for activity in activities:
            if hasattr(activity, 'type'):
                status = activity.type or "unknown"
                if status not in status_count:
                    status_count[status] = 0
                status_count[status] += 1
        
        labels = list(status_count.keys())
        values = list(status_count.values())
        
        return {"labels": labels, "values": values}
    
    def _get_delivery_stats(self):
        """
        Calcula estatísticas de entregas
        
        Returns:
            dict: Dicionário com labels e valores para gráficos
        """
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

