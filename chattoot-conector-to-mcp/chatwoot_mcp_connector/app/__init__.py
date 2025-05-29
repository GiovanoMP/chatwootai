"""
Arquivo de inicialização do pacote app.
"""

from app.webhook.handler import webhook_blueprint
from app.client.chatwoot_client import ChatwootClient
from app.client.mcp_crew_client import MCPCrewClient
from app.context.context_manager import ContextManager
from app.config.manager import ConfigManager
from app.processor.message_processor import process_message
from app.utils.logger import setup_logger, get_logger
