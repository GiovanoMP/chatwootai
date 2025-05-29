"""
Processador de mensagens do Chatwoot.
Normaliza e enriquece os dados das mensagens recebidas.
"""

import json
import logging
from app.client.mcp_crew_client import MCPCrewClient
from app.client.chatwoot_client import ChatwootClient
from app.context.context_manager import ContextManager
from app.utils.logger import get_logger

# Configuração do logger
logger = get_logger(__name__)

def process_message(event_data):
    """
    Processa uma mensagem recebida do Chatwoot.
    
    Args:
        event_data: Dados do evento recebido do webhook
        
    Returns:
        Boolean indicando sucesso ou falha
    """
    try:
        # Extrai informações relevantes da mensagem
        message_data = extract_message_data(event_data)
        
        # Obtém o contexto da conversa
        context = get_conversation_context(message_data)
        
        # Envia a mensagem para o MCP-Crew
        response = send_to_mcp_crew(message_data, context)
        
        # Se houver resposta automática, envia de volta ao Chatwoot
        if response and response.get('auto_reply'):
            send_reply_to_chatwoot(message_data, response.get('reply_content'))
        
        logger.info(f"Mensagem processada com sucesso: {message_data.get('message_id')}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        return False

def extract_message_data(event_data):
    """
    Extrai e normaliza os dados da mensagem.
    
    Args:
        event_data: Dados do evento recebido do webhook
        
    Returns:
        Dicionário com dados normalizados da mensagem
    """
    # Extrai informações básicas
    message_id = event_data.get('id')
    content = event_data.get('content')
    created_at = event_data.get('created_at')
    message_type = event_data.get('message_type')
    
    # Extrai informações do remetente
    sender = event_data.get('sender', {})
    sender_id = sender.get('id')
    sender_name = sender.get('name')
    sender_type = sender.get('type', 'contact')  # 'contact' ou 'agent'
    
    # Extrai informações da conversa
    conversation = event_data.get('conversation', {})
    conversation_id = conversation.get('display_id')
    additional_attributes = conversation.get('additional_attributes', {})
    
    # Extrai informações da conta e inbox
    account = event_data.get('account', {})
    account_id = account.get('id')
    account_name = account.get('name')
    
    inbox = event_data.get('inbox', {})
    inbox_id = inbox.get('id')
    inbox_name = inbox.get('name')
    
    # Determina o canal com base no inbox ou atributos adicionais
    channel = determine_channel(inbox, additional_attributes)
    
    # Constrói o objeto normalizado
    message_data = {
        'message_id': message_id,
        'content': content,
        'created_at': created_at,
        'message_type': message_type,
        'sender': {
            'id': sender_id,
            'name': sender_name,
            'type': sender_type
        },
        'conversation': {
            'id': conversation_id,
            'attributes': additional_attributes
        },
        'account': {
            'id': account_id,
            'name': account_name
        },
        'inbox': {
            'id': inbox_id,
            'name': inbox_name
        },
        'channel': channel
    }
    
    return message_data

def determine_channel(inbox, additional_attributes):
    """
    Determina o canal da mensagem com base no inbox e atributos adicionais.
    
    Args:
        inbox: Informações do inbox
        additional_attributes: Atributos adicionais da conversa
        
    Returns:
        String representando o canal (whatsapp, facebook, instagram, api, etc.)
    """
    # Tenta determinar o canal pelo tipo de inbox
    if inbox and 'channel_type' in inbox:
        channel_type = inbox.get('channel_type', '').lower()
        
        if 'whatsapp' in channel_type:
            return 'whatsapp'
        elif 'facebook' in channel_type:
            return 'facebook'
        elif 'instagram' in channel_type:
            return 'instagram'
        elif 'twitter' in channel_type:
            return 'twitter'
        elif 'api' in channel_type:
            return 'api'
    
    # Tenta determinar o canal pelos atributos adicionais
    if additional_attributes:
        if 'source' in additional_attributes:
            source = additional_attributes.get('source', '').lower()
            if source in ['whatsapp', 'facebook', 'instagram', 'twitter']:
                return source
    
    # Canal padrão se não for possível determinar
    return 'unknown'

def get_conversation_context(message_data):
    """
    Obtém o contexto da conversa.
    
    Args:
        message_data: Dados normalizados da mensagem
        
    Returns:
        Dicionário com o contexto da conversa
    """
    # Em uma implementação real, isso buscaria o contexto de um banco de dados
    # Para este exemplo, criamos um contexto básico
    conversation_id = message_data.get('conversation', {}).get('id')
    
    # Instancia o gerenciador de contexto
    context_manager = ContextManager()
    
    # Obtém o contexto existente ou cria um novo
    context = context_manager.get_context(conversation_id)
    
    # Atualiza o contexto com informações da mensagem atual
    context_manager.update_context(conversation_id, {
        'last_message': message_data.get('content'),
        'last_message_time': message_data.get('created_at'),
        'channel': message_data.get('channel'),
        'sender': message_data.get('sender')
    })
    
    return context

def send_to_mcp_crew(message_data, context):
    """
    Envia a mensagem para o MCP-Crew para análise e roteamento.
    
    Args:
        message_data: Dados normalizados da mensagem
        context: Contexto da conversa
        
    Returns:
        Resposta do MCP-Crew
    """
    # Instancia o cliente MCP-Crew
    mcp_crew_client = MCPCrewClient()
    
    # Prepara os dados para envio
    payload = {
        'message': message_data.get('content'),
        'message_id': message_data.get('message_id'),
        'conversation_id': message_data.get('conversation', {}).get('id'),
        'sender': message_data.get('sender'),
        'channel': message_data.get('channel'),
        'context': context
    }
    
    # Envia para o MCP-Crew
    response = mcp_crew_client.send_message(payload)
    
    return response

def send_reply_to_chatwoot(message_data, reply_content):
    """
    Envia uma resposta de volta ao Chatwoot.
    
    Args:
        message_data: Dados normalizados da mensagem original
        reply_content: Conteúdo da resposta
        
    Returns:
        Boolean indicando sucesso ou falha
    """
    # Instancia o cliente Chatwoot
    chatwoot_client = ChatwootClient()
    
    # Prepara os dados da resposta
    conversation_id = message_data.get('conversation', {}).get('id')
    
    # Envia a resposta
    result = chatwoot_client.send_message(
        conversation_id=conversation_id,
        content=reply_content,
        message_type='outgoing'
    )
    
    return result
