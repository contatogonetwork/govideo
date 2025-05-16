    def show_context_menu(self, point):
        """Exibe menu de contexto no clique direito da tabela"""
        index = self.activations_table.indexAt(point)
        if index.isValid():
            menu = QMenu(self)
            
            # Ações do menu
            edit_action = menu.addAction("Editar")
            edit_action.triggered.connect(self.on_edit_activation)
            
            menu.addSeparator()
            
            status_menu = menu.addMenu("Alterar Status")
            pending_action = status_menu.addAction("⏳ Pendente")
            filmed_action = status_menu.addAction("✅ Filmado")
            failed_action = status_menu.addAction("❌ Falhou")
            
            pending_action.triggered.connect(lambda: self.on_update_status("pending"))
            filmed_action.triggered.connect(lambda: self.on_update_status("filmed"))
            failed_action.triggered.connect(lambda: self.on_update_status("failed"))
            
            menu.addSeparator()
            
            evidence_action = menu.addAction("Adicionar Evidência")
            evidence_action.triggered.connect(self.on_add_evidence)
              
            view_evidence_action = menu.addAction("Ver Evidência")
            activation = self.activation_model.get_activation(index.row())
            # Corrigindo verificação para evitar erro de NoneType
            has_evidence = activation is not None and hasattr(activation, 'location') and activation.location
            view_evidence_action.setEnabled(bool(has_evidence))
            view_evidence_action.triggered.connect(self.on_view_evidence)
            
            menu.addSeparator()
            
            delete_action = menu.addAction("Remover")
            delete_action.triggered.connect(self.on_delete_activation)
            
            # Exibir menu
            menu.exec_(self.activations_table.viewport().mapToGlobal(point))
