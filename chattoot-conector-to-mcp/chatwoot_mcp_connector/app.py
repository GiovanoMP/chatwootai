"""
Arquivo principal do conector Chatwoot-MCP-Crew.
Inicializa o servidor Flask e configura os endpoints.
"""

import os
import logging
from flask import Flask, request, jsonify
from app.webhook.handler import webhook_blueprint
from app.config.manager import ConfigManager
from app.utils.logger import setup_logger

# Configuração de logging
logger = setup_logger()

def create_app(config_path=None):
    """
    Cria e configura a aplicação Flask.
    
    Args:
        config_path: Caminho para o arquivo de configuração
        
    Returns:
        Aplicação Flask configurada
    """
    app = Flask(__name__)
    
    # Carrega configurações
    if config_path is None:
        config_path = os.environ.get('CONFIG_PATH', 'config/config.json')
    
    try:
        config_manager = ConfigManager(config_path)
        app.config.update(config_manager.get_config())
    except Exception as e:
        logger.error(f"Erro ao carregar configurações: {str(e)}")
        # Usa configurações padrão em caso de erro
        app.config.update({
            'DEBUG': True,
            'CHATWOOT_API_URL': os.environ.get('CHATWOOT_API_URL', ''),
            'CHATWOOT_API_ACCESS_TOKEN': os.environ.get('CHATWOOT_API_ACCESS_TOKEN', ''),
            'MCP_CREW_API_URL': os.environ.get('MCP_CREW_API_URL', ''),
            'MCP_CREW_API_KEY': os.environ.get('MCP_CREW_API_KEY', ''),
        })
    
    # Registra blueprints
    app.register_blueprint(webhook_blueprint, url_prefix='/webhook')
    
    # Rota de saúde
    @app.route('/health', methods=['GET'])
    def health_check():
        """Endpoint para verificar a saúde do serviço."""
        return jsonify({
            'status': 'healthy',
            'components': {
                'webhook_server': 'online',
                'chatwoot_client': 'online' if app.config.get('CHATWOOT_API_URL') else 'not_configured',
                'mcp_crew_client': 'online' if app.config.get('MCP_CREW_API_URL') else 'not_configured',
            },
            'version': '1.0.0'
        })
    
    # Rota de configuração
    @app.route('/config', methods=['GET'])
    def get_config():
        """Endpoint para obter a configuração atual."""
        # Oculta informações sensíveis
        config = {
            'chatwoot': {
                'api_url': app.config.get('CHATWOOT_API_URL', ''),
                'webhook_url': request.host_url + 'webhook/chatwoot',
                'api_access_token': '***********' if app.config.get('CHATWOOT_API_ACCESS_TOKEN') else '',
            },
            'mcp_crew': {
                'api_url': app.config.get('MCP_CREW_API_URL', ''),
                'decision_engine_url': app.config.get('MCP_CREW_DECISION_ENGINE_URL', ''),
                'api_key': '***********' if app.config.get('MCP_CREW_API_KEY') else '',
            },
            'routing': app.config.get('ROUTING_RULES', {
                'default_crew': 'suporte',
                'rules': []
            })
        }
        return jsonify(config)
    
    # Rota de métricas
    @app.route('/metrics', methods=['GET'])
    def get_metrics():
        """Endpoint para obter métricas do serviço."""
        # Em uma implementação real, estas métricas seriam coletadas de um sistema de monitoramento
        return jsonify({
            'messages_received': 0,
            'messages_sent': 0,
            'errors': 0,
            'average_response_time': 0,
            'crews': {}
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
