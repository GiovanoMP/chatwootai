"""
Manipulador de webhooks do Chatwoot.
Recebe e processa eventos enviados pelo Chatwoot.
"""

import hmac
import hashlib
import json
import logging
from flask import Blueprint, request, jsonify, current_app
from app.processor.message_processor import process_message
from app.utils.logger import get_logger

# Configuração do logger
logger = get_logger(__name__)

# Criação do blueprint
webhook_blueprint = Blueprint('webhook', __name__)

def verify_chatwoot_signature(payload, signature, secret):
    """
    Verifica a assinatura HMAC do webhook do Chatwoot.
    
    Args:
        payload: Payload do webhook em bytes
        signature: Assinatura fornecida no header X-Chatwoot-Signature
        secret: Segredo compartilhado para validação
        
    Returns:
        Boolean indicando se a assinatura é válida
    """
    if not signature or not secret:
        return False
    
    computed_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature)

@webhook_blueprint.route('/chatwoot', methods=['POST'])
def chatwoot_webhook():
    """
    Endpoint para receber eventos do Chatwoot.
    Valida a assinatura e processa o evento.
    """
    # Obtém o payload e a assinatura
    payload = request.get_data()
    signature = request.headers.get('X-Chatwoot-Signature')
    
    # Verifica a assinatura se configurada
    webhook_secret = current_app.config.get('CHATWOOT_WEBHOOK_SECRET')
    if webhook_secret and not verify_chatwoot_signature(payload, signature, webhook_secret):
        logger.warning("Assinatura de webhook inválida")
        return jsonify({
            'success': False,
            'message': 'Assinatura inválida'
        }), 401
    
    try:
        # Processa o evento
        event_data = json.loads(payload)
        event_type = event_data.get('event')
        
        logger.info(f"Evento recebido: {event_type}")
        
        # Processa apenas eventos de mensagem
        if event_type == 'message_created':
            # Processa a mensagem de forma assíncrona
            # Em uma implementação real, isso seria feito em uma fila
            process_message(event_data)
        
        return jsonify({
            'success': True,
            'message': 'Evento recebido com sucesso'
        })
    
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao processar evento: {str(e)}'
        }), 500

@webhook_blueprint.route('/status', methods=['GET'])
def webhook_status():
    """
    Endpoint para verificar o status do servidor de webhooks.
    """
    # Em uma implementação real, estas estatísticas seriam armazenadas em um banco de dados
    return jsonify({
        'status': 'online',
        'uptime': 'N/A',  # Seria calculado com base no tempo de inicialização
        'events_processed': 0,
        'last_event': None
    })
