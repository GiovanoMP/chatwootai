    def sync_categories(self):
        """Sincroniza as categorias do marketplace."""
        self.ensure_one()
        
        if not self.api_base_url or not self.access_token:
            raise ValidationError(_('Configurações de API incompletas ou token de acesso inválido'))
        
        try:
            # Verificar se o token está válido
            if not self.access_token or (self.token_expiry and self.token_expiry < fields.Datetime.now()):
                self.refresh_token()
            
            # Esta é uma implementação genérica. Cada marketplace terá sua própria lógica.
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(
                f"{self.api_base_url}/categories",
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                categories = response.json()
                # Aqui seria implementada a lógica para processar as categorias recebidas
                # e atualizar os mapeamentos de categoria
                
                self.write({'last_sync': fields.Datetime.now()})
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sucesso'),
                        'message': _('Categorias de %s sincronizadas com sucesso') % self.name,
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Erro'),
                        'message': _('Falha na sincronização: %s - %s') % (response.status_code, response.text),
                        'sticky': True,
                        'type': 'danger',
                    }
                }
                
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro'),
                    'message': _('Exceção: %s') % str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }
