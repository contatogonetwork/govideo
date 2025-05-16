#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GONETWORK AI - Modificador para corrigir a indentação do método on_change_status
Data: 2025-05-15
Autor: GONETWORK AI
"""

import os
import sys
import re

def fix_indentation():
    """Corrige problemas de indentação no arquivo team_schedule_view.py"""
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ui', 'views', 'team_schedule_view.py')
    
    if not os.path.exists(file_path):
        print(f"Erro: O arquivo {file_path} não foi encontrado.")
        return False
    
    try:
        # Ler o conteúdo do arquivo
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Corrigir indentação do método on_change_status
        fixed_content = re.sub(
            r'(\s+)def on_delete_assignment\(.*?\)\:.*?QMessageBox\.critical.*?\n(\s+)def on_change_status',
            r'\1def on_delete_assignment\1\n\1def on_change_status',
            content, 
            flags=re.DOTALL
        )
        
        # Corrigir duplicata de except
        fixed_content = re.sub(
            r'(\s+)except Exception as e:(\s+)logger\.error.*?QMessageBox\.critical.*?\n(\s+)except Exception as e:',
            r'\1except Exception as e:\2logger.error(f"Erro ao alterar status: {e}")\n\2QMessageBox.critical(self, "Erro", f"Não foi possível atualizar o status: {e}")',
            fixed_content, 
            flags=re.DOTALL
        )
        
        # Adicionar a importação de SQLAlchemyError se não existir
        if 'from sqlalchemy.exc import SQLAlchemyError' not in fixed_content:
            fixed_content = fixed_content.replace(
                'from core.database_upgrade import AssignmentStatus',
                'from core.database_upgrade import AssignmentStatus\nfrom sqlalchemy.exc import SQLAlchemyError'
            )
        
        # Encontrar e substituir o método load_assignments
        load_assignments_pattern = re.compile(r'(\s+)def load_assignments\(self\):.*?(?=\1def|\Z)', re.DOTALL)
        load_assignments_method = '''    def load_assignments(self):
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
          if re.search(load_assignments_pattern, fixed_content):
            fixed_content = re.sub(load_assignments_pattern, load_assignments_method, fixed_content)
        
        # Encontrar e substituir o método apply_filters se existir
        apply_filters_pattern = re.compile(r'(\s+)def apply_filters\(self\):.*?(?=\1def|\Z)', re.DOTALL)
        apply_filters_method = '''    def apply_filters(self):
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
        
        if re.search(apply_filters_pattern, fixed_content):
            fixed_content = re.sub(apply_filters_pattern, apply_filters_method, fixed_content)
        else:
            # Se não encontrar, adicionar após o método load_assignments
            fixed_content = fixed_content.replace(load_assignments_method, load_assignments_method + "\n" + apply_filters_method)
        
        # Escrever conteúdo corrigido
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(fixed_content)
        
        print(f"Arquivo {file_path} corrigido com sucesso!")
        return True
        
    except Exception as e:
        print(f"Erro ao corrigir o arquivo: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando correção de indentação...")
    result = fix_indentation()
    
    if result:
        print("Correção concluída com sucesso!")
        sys.exit(0)
    else:
        print("Falha na correção do arquivo.")
        sys.exit(1)
