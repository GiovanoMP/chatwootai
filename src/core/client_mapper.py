#!/usr/bin/env python3
"""
ClientMapper - Módulo para mapeamento de clientes do Chatwoot

Este módulo é responsável por carregar e gerenciar o mapeamento entre
contas do Chatwoot (account_id, inbox_id) e os domínios/clientes
do sistema ChatwootAI.

O mapeamento é carregado a partir do arquivo config/chatwoot_mapping.yaml
e permite identificar qual cliente e domínio devem ser usados para
processar uma mensagem com base no account_id ou inbox_id do Chatwoot.

NOTA: Este arquivo foi criado apenas para fins de teste e monitoramento.
Ele não é utilizado pelo sistema principal e deve ser integrado ao
webhook_handler.py ou excluído no futuro.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class ClientMapper:
    """
    Classe responsável por mapear contas e caixas de entrada do Chatwoot
    para domínios e clientes específicos no sistema.
    """
    
    def __init__(self):
        """
        Inicializa o mapeador de clientes.
        """
        self.accounts_map = {}  # Mapeamento de account_id para domínio/cliente
        self.inboxes_map = {}   # Mapeamento de inbox_id para domínio/cliente (fallback)
        self.clients_info = {}  # Informações detalhadas sobre os clientes
        self.webhook_settings = {}  # Configurações adicionais para o webhook handler
        
        self.mapping_file = None
        self.is_loaded = False
    
    async def load_mappings(self, mapping_file: str = "config/chatwoot_mapping.yaml") -> bool:
        """
        Carrega o mapeamento de clientes a partir do arquivo YAML.
        
        Args:
            mapping_file: Caminho para o arquivo de mapeamento
            
        Returns:
            bool: True se o mapeamento foi carregado com sucesso, False caso contrário
        """
        self.mapping_file = mapping_file
        
        if not os.path.exists(mapping_file):
            logger.error(f"Arquivo de mapeamento não encontrado: {mapping_file}")
            return False
        
        try:
            with open(mapping_file, 'r') as f:
                mapping_data = yaml.safe_load(f)
            
            # Carregar mapeamento de contas
            if 'accounts' in mapping_data:
                self.accounts_map = mapping_data['accounts']
                logger.info(f"Mapeamento de contas carregado: {len(self.accounts_map)} contas")
            
            # Carregar mapeamento de inboxes (fallback)
            if 'inboxes' in mapping_data:
                self.inboxes_map = mapping_data['inboxes']
                logger.info(f"Mapeamento de inboxes carregado: {len(self.inboxes_map)} inboxes")
            
            # Carregar informações de clientes
            if 'clients' in mapping_data:
                self.clients_info = mapping_data['clients']
                logger.info(f"Informações de clientes carregadas: {len(self.clients_info)} clientes")
            
            # Carregar configurações do webhook
            if 'webhook_settings' in mapping_data:
                self.webhook_settings = mapping_data['webhook_settings']
                logger.info("Configurações do webhook carregadas")
            
            self.is_loaded = True
            logger.info(f"Mapeamento de clientes carregado com sucesso de: {mapping_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar mapeamento de clientes: {str(e)}")
            return False
    
    def get_client_by_account_id(self, account_id: str) -> Optional[Dict[str, str]]:
        """
        Obtém as informações de domínio e cliente com base no account_id do Chatwoot.
        
        Args:
            account_id: ID da conta do Chatwoot
            
        Returns:
            Dict[str, str]: Dicionário com 'domain' e 'account_id', ou None se não encontrado
        """
        if not self.is_loaded:
            logger.warning("Mapeamento de clientes não foi carregado")
            return None
        
        # Converter para string para garantir compatibilidade com o mapeamento
        account_id = str(account_id)
        
        if account_id in self.accounts_map:
            logger.info(f"Cliente encontrado para account_id {account_id}: {self.accounts_map[account_id]}")
            return self.accounts_map[account_id]
        else:
            logger.warning(f"Nenhum cliente encontrado para account_id: {account_id}")
            return None
    
    def get_client_by_inbox_id(self, inbox_id: str) -> Optional[Dict[str, str]]:
        """
        Obtém as informações de domínio e cliente com base no inbox_id do Chatwoot.
        Usado como fallback quando o account_id não resolve para um cliente específico.
        
        Args:
            inbox_id: ID da caixa de entrada do Chatwoot
            
        Returns:
            Dict[str, str]: Dicionário com 'domain' e 'account_id', ou None se não encontrado
        """
        if not self.is_loaded:
            logger.warning("Mapeamento de clientes não foi carregado")
            return None
        
        # Converter para string para garantir compatibilidade com o mapeamento
        inbox_id = str(inbox_id)
        
        if inbox_id in self.inboxes_map:
            logger.info(f"Cliente encontrado para inbox_id {inbox_id}: {self.inboxes_map[inbox_id]}")
            return self.inboxes_map[inbox_id]
        else:
            logger.warning(f"Nenhum cliente encontrado para inbox_id: {inbox_id}")
            return None
    
    def get_client_details(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações detalhadas sobre um cliente específico.
        
        Args:
            account_id: ID da conta
            
        Returns:
            Dict[str, Any]: Informações detalhadas do cliente, ou None se não encontrado
        """
        if not self.is_loaded:
            logger.warning("Mapeamento de clientes não foi carregado")
            return None
        
        if account_id in self.clients_info:
            return self.clients_info[account_id]
        else:
            logger.warning(f"Nenhuma informação detalhada encontrada para a conta: {account_id}")
            return None
    
    def get_webhook_settings(self) -> Dict[str, Any]:
        """
        Obtém as configurações do webhook handler.
        
        Returns:
            Dict[str, Any]: Configurações do webhook handler
        """
        return self.webhook_settings if self.is_loaded else {}
    
    def get_client_from_webhook(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Determina o cliente e domínio com base nos dados do webhook.
        Tenta primeiro pelo account_id e, se não encontrar, tenta pelo inbox_id.
        
        Args:
            webhook_data: Dados do webhook do Chatwoot
            
        Returns:
            Dict[str, str]: Dicionário com 'domain' e 'account_id', ou None se não encontrado
        """
        if not self.is_loaded:
            logger.warning("Mapeamento de clientes não foi carregado")
            return None
        
        # Extrair account_id e inbox_id do webhook
        account_id = None
        inbox_id = None
        
        # Verificar se há dados de conta/inbox no webhook
        if 'account' in webhook_data and isinstance(webhook_data['account'], dict):
            account_id = str(webhook_data['account'].get('id'))
        
        if 'inbox' in webhook_data and isinstance(webhook_data['inbox'], dict):
            inbox_id = str(webhook_data['inbox'].get('id'))
        
        # Tentar resolver pelo account_id
        if account_id:
            client_info = self.get_client_by_account_id(account_id)
            if client_info:
                logger.info(f"Cliente identificado pelo account_id {account_id}: {client_info}")
                return client_info
        
        # Fallback: tentar resolver pelo inbox_id
        if inbox_id:
            client_info = self.get_client_by_inbox_id(inbox_id)
            if client_info:
                logger.info(f"Cliente identificado pelo inbox_id {inbox_id}: {client_info}")
                return client_info
        
        logger.warning(f"Não foi possível identificar o cliente para o webhook. Account: {account_id}, Inbox: {inbox_id}")
        return None


# Exemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Criar instância do mapeador
    mapper = ClientMapper()
    
    # Carregar mapeamento
    import asyncio
    asyncio.run(mapper.load_mappings())
    
    # Testar mapeamento
    for account_id in ["1", "2", "3", "4"]:
        client_info = mapper.get_client_by_account_id(account_id)
        if client_info:
            client_details = mapper.get_client_details(client_info.get("account_id"))
            print(f"Account {account_id} -> Domain: {client_info.get('domain')}, Account: {client_info.get('account_id')} ({client_details.get('name')})")
