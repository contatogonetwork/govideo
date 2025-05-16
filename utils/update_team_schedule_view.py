#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Script para atualizar o arquivo team_schedule_view.py
Data: 2025-05-15
Autor: GONETWORK AI
"""

import os
import sys
import re
from pathlib import Path

def update_file():
    """Atualiza o arquivo team_schedule_view.py para corrigir problemas com filtro de status"""
    # Caminho do arquivo
    base_path = Path(__file__).parent.parent
    file_path = base_path / 'ui' / 'views' / 'team_schedule_view.py'
    
    # Verificar se o arquivo existe
    if not file_path.exists():
        print(f"Erro: O arquivo {file_path} não foi encontrado.")
        return False
    
    # Fazer backup do arquivo
    backup_path = file_path.with_suffix('.py.bak')
    with open(file_path, 'r', encoding='utf-8') as src:
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    
    print(f"Backup salvo em {backup_path}")
    
    try:
        # Ler o conteúdo do arquivo
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Adicionar importação de SQLAlchemyError se ainda não existir
        if 'from sqlalchemy.exc import SQLAlchemyError' not in content:
            modified_content = content.replace(
                'from core.database_upgrade import AssignmentStatus',
                'from core.database_upgrade import AssignmentStatus\nfrom sqlalchemy.exc import SQLAlchemyError'
            )
        else:
            modified_content = content
        
        # Implementação atualizada do método load_assignments
        load_assignments_code = '''    def load_assignments(self):
        """Carrega atribuições de equipe do banco de dados"""
        try:
            if not self.current_event or not self.db:
                self.schedule_model.set_assignments([])
                return
            
            # Data selecionada
            date = self.selected_date.toPyDate()
            
            # Iniciar consulta básica
            query = self.db.query(TeamAssignment)\\
                .join(Activity, TeamAssignment.activity_id == Activity.id)\\
                .filter(Activity.stage.has(Event.id == self.current_event))
            
            # Filtrar por data
            start_date = datetime.combine(date, datetime.min.time())
            end_date = datetime.combine(date, datetime.max.time())
            query = query.filter(Activity.start_time >= start_date, Activity.start_time <= end_date)
            
            # Aplicar filtro de membro da equipe
            if self.filtered_member:
                query = query.filter(TeamAssignment.member_id == self.filtered_member)
            
            # Aplicar filtro de função
            if self.filtered_role:
                query = query.filter(TeamAssignment.role_details.like(f"%{self.filtered_role}%"))
            
            # Aplicar filtro de status - verificar se a coluna existe
            if self.status_filter.currentData():
                try:
                    # Tentativa de filtrar por status
                    query = query.filter(TeamAssignment.status == self.status_filter.currentData())
                except SQLAlchemyError:
                    # Se falhar, ignorar o filtro de status
                    logger.warning("Coluna 'status' não encontrada em TeamAssignment, ignorando filtro")
            
            # Obter resultados
            assignments = query.all()
            
            # Atualizar modelo
            self.schedule_model.set_assignments(assignments)
        except Exception as e:
            logger.error(f"Erro ao carregar atribuições: {e}")
            self.schedule_model.set_assignments([])
'''
        
        # Implementação atualizada do método apply_filters
        apply_filters_code = '''    def apply_filters(self):
        """Aplica os filtros selecionados"""
        # Atualizar os filtros
        if self.member_filter.currentData():
            self.filtered_member = self.member_filter.currentData()
        else:
            self.filtered_member = None
            
        if self.role_filter.currentData():
            self.filtered_role = self.role_filter.currentData()
        else:
            self.filtered_role = None
        
        # Recarregar atribuições
        self.load_assignments()
'''
        
        # Procurar e substituir o método load_assignments
        load_pattern = re.compile(r'(\s+)def load_assignments\(self\):.*?(?=\1def|\Z)', re.DOTALL)
        if re.search(load_pattern, modified_content):
            modified_content = re.sub(load_pattern, load_assignments_code, modified_content)
            print("Método load_assignments substituído")
        else:
            print("AVISO: Método load_assignments não encontrado para substituição")
        
        # Procurar e substituir o método apply_filters
        apply_pattern = re.compile(r'(\s+)def apply_filters\(self\):.*?(?=\1def|\Z)', re.DOTALL)
        if re.search(apply_pattern, modified_content):
            modified_content = re.sub(apply_pattern, apply_filters_code, modified_content)
            print("Método apply_filters substituído")
        else:
            # Se não encontrar, inserir após load_assignments
            if "def load_assignments(self):" in modified_content:
                parts = modified_content.split("def load_assignments(self):")
                if len(parts) >= 2:
                    method_part = parts[1]
                    # Encontrar o final do método load_assignments
                    method_lines = method_part.split("\n")
                    indent_level = None
                    end_line = 0
                    
                    for i, line in enumerate(method_lines):
                        if i == 0 or not line.strip():  # Primeira linha ou linha vazia
                            continue
                        
                        # Determinar nível de indentação do método
                        if indent_level is None:
                            indent_level = len(line) - len(line.lstrip())
                        
                        # Verificar se saímos do método (indentação menor ou igual)
                        current_indent = len(line) - len(line.lstrip())
                        if line.strip() and current_indent <= indent_level:
                            end_line = i
                            break
                    
                    # Se não encontrou o final, usar o final do arquivo
                    if end_line == 0:
                        end_line = len(method_lines)
                    
                    # Adicionar apply_filters após o método
                    new_parts = [parts[0], "def load_assignments(self):", 
                                "\n".join(method_lines[:end_line]), 
                                apply_filters_code,
                                "\n".join(method_lines[end_line:])]
                    modified_content = "".join(new_parts)
                    print("Método apply_filters adicionado após load_assignments")
            else:
                print("AVISO: Não foi possível adicionar apply_filters pois load_assignments não foi encontrado")
        
        # Escrever as alterações no arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"Arquivo {file_path} atualizado com sucesso!")
        return True
    
    except Exception as e:
        print(f"Erro ao atualizar o arquivo: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando atualização do arquivo team_schedule_view.py...")
    success = update_file()
    if success:
        print("Atualização concluída com sucesso!")
    else:
        print("Atualização falhou.")
