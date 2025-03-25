"""
Servidor webhook para receber eventos do Chatwoot.

Este servidor recebe notificações do Chatwoot quando eventos ocorrem
(como novas mensagens) e os processa usando a arquitetura hub-and-spoke.
"""

import os
import sys
import logging
import json
import traceback
import yaml
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Dict, Any
from datetime import datetime

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Importa o sistema de debug_logger
from src.utils.debug_logger import get_logger

# Configura o logger
logger = get_logger('webhook_server', level=logging.DEBUG)

# Configurar o logging padrão do Python para gravar no arquivo
file_handler = logging.FileHandler('logs/webhook.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
root_logger = logging.getLogger()
root_logger.addHandler(file_handler)

# Carrega variáveis de ambiente
load_dotenv()

# Importa componentes necessários
from src.webhook.webhook_handler import ChatwootWebhookHandler
from src.core.hub import HubCrew
from src.core.data_service_hub import DataServiceHub
from src.core.memory import MemorySystem
from src.core.domain import DomainManager
from src.plugins.core.plugin_manager import PluginManager
from src.crews.sales_crew import SalesCrew
from src.api.chatwoot.client import ChatwootClient  # Usando a implementação da arquitetura hub-and-spoke

# Cria a aplicação FastAPI
app = FastAPI(title="Chatwoot Webhook Server", description="Servidor para receber webhooks do Chatwoot")

# Adiciona middleware CORS para aceitar requisições do proxy na VPS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variáveis globais
webhook_handler = None

def get_webhook_handler():
    """Obtém ou inicializa o webhook handler"""
    global webhook_handler
    if webhook_handler is None:
        webhook_handler = initialize_system()
    return webhook_handler

def initialize_system():
    """
    Inicializa o sistema completo seguindo a nova arquitetura hub-and-spoke
    com configuração dinâmica de domínios baseada na empresa do Chatwoot.
    
    Na nova arquitetura, o domínio é determinado dinamicamente para cada conversa
    com base nas configurações da empresa no Chatwoot, não mais fixado no código.
    """
    logger.info("🚀 Iniciando servidor webhook...")
    logger.info("🚀 Inicializando sistema para receber webhooks do Chatwoot...")
    
    # Sistema de memória para persistência de contexto
    memory_system = MemorySystem()
    logger.info("✅ Sistema de memória inicializado")
    
    # Gerenciador de domínio - Carrega todos os domínios disponíveis
    # Não define um domínio fixo, pois será determinado dinamicamente por conversa
    domain_manager = DomainManager()
    
    # Carrega todos os domínios disponíveis no sistema
    available_domains = domain_manager.loader.list_available_domains()
    logger.info(f"✅ Domínios disponíveis carregados: {available_domains}")
    
    # Configuração do domínio padrão (fallback) caso não seja possível determinar o domínio
    # Este domínio será usado apenas como fallback, não como padrão para todas as conversas
    default_domain = os.getenv('DEFAULT_DOMAIN', 'cosmetics')
    domain_manager.set_active_domain(default_domain)
    logger.info(f"✅ Domínio padrão (fallback) configurado: {default_domain}")
    
    # Gerenciador de plugins - Carrega plugins base conforme configuração
    # Plugins específicos de domínio serão carregados dinamicamente por conversa
    plugin_config = {
        "enabled_plugins": ["sentiment_analysis_plugin", "faq_knowledge_plugin", "response_enhancer_plugin"],
        "dynamic_loading": True  # Habilita carregamento dinâmico de plugins por domínio
    }
    plugin_manager = PluginManager(config=plugin_config)
    logger.info("✅ Gerenciador de plugins inicializado")
    
    # DataServiceHub - Ponto central de acesso a dados
    # Configurado para suportar múltiplos domínios e empresas
    data_service_hub = DataServiceHub()
    logger.info("✅ DataServiceHub inicializado")
    
    # HubCrew - Centro da arquitetura hub-and-spoke
    # Configurado com todos os componentes necessários para determinar domínios dinamicamente
    hub_crew = HubCrew(
        memory_system=memory_system,
        data_service_hub=data_service_hub,
        domain_manager=domain_manager,
        plugin_manager=plugin_manager
    )
    logger.info("✅ HubCrew inicializado")
    
    # Na nova arquitetura, não inicializamos crews específicas aqui
    # As crews serão instanciadas dinamicamente pelo HubCrew para cada conversa
    # com base no domínio determinado a partir dos dados da empresa no Chatwoot
    
    # Configuração do webhook handler com informações do Chatwoot
    chatwoot_base_url = os.getenv('CHATWOOT_BASE_URL')
    chatwoot_api_key = os.getenv('CHATWOOT_API_KEY')
    
    if not chatwoot_base_url or not chatwoot_api_key:
        logger.warning("⚠️ Variáveis de ambiente CHATWOOT_BASE_URL ou CHATWOOT_API_KEY não definidas!")
    
    # Carrega o arquivo de mapeamento YAML
    mapping_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                    'config', 'chatwoot_mapping.yaml')
    
    # Inicializa as configurações de mapeamento
    account_domain_mapping = {}
    inbox_domain_mapping = {}
    webhook_settings = {}
    
    # Tenta carregar o arquivo de mapeamento
    try:
        if os.path.exists(mapping_file_path):
            with open(mapping_file_path, 'r') as file:
                mapping_config = yaml.safe_load(file)
                
                # Extrai os mapeamentos
                account_domain_mapping = mapping_config.get('account_domain_mapping', {})
                inbox_domain_mapping = mapping_config.get('inbox_domain_mapping', {})
                webhook_settings = mapping_config.get('webhook_settings', {})
                
                logger.info(f"✅ Arquivo de mapeamento carregado: {mapping_file_path}")
                logger.info(f"✅ Accounts mapeados: {len(account_domain_mapping)}")
                logger.info(f"✅ Inboxes mapeados: {len(inbox_domain_mapping)}")
        else:
            logger.warning(f"⚠️ Arquivo de mapeamento não encontrado: {mapping_file_path}")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar arquivo de mapeamento: {str(e)}")
    
    webhook_config = {
        "chatwoot_base_url": chatwoot_base_url,
        "chatwoot_api_key": chatwoot_api_key,
        # Mapeamento dinâmico de canais - será expandido conforme necessário
        "channel_mapping": json.loads(os.getenv('CHANNEL_MAPPING', '{"1": "whatsapp"}')),
        # Adiciona os mapeamentos de domínio carregados do YAML
        "account_domain_mapping": account_domain_mapping,
        "inbox_domain_mapping": inbox_domain_mapping,
        # Adiciona configurações adicionais do webhook
        **webhook_settings
    }
    
    # Inicializa o webhook handler com o HubCrew central
    webhook_handler = ChatwootWebhookHandler(
        hub_crew=hub_crew,
        config=webhook_config
    )
    logger.info("✅ ChatwootWebhookHandler inicializado")
    
    # Inicializa o cliente Chatwoot para comunicação com a API
    chatwoot_client = ChatwootClient(
        base_url=chatwoot_base_url,
        api_token=chatwoot_api_key
    )
    
    # Verifica a conexão com o Chatwoot
    try:
        # Tenta obter informações básicas para verificar a conexão
        chatwoot_client.check_connection()
        logger.info("✅ Conexão com Chatwoot verificada com sucesso")
    except Exception as e:
        logger.warning(f"⚠️ Não foi possível verificar a conexão com o Chatwoot: {str(e)}")
    
    logger.info("🎉 Sistema inicializado com sucesso para receber webhooks!")
    logger.info("🔄 Sistema configurado para determinar domínios dinamicamente por conversa")
    return webhook_handler

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização do servidor."""
    logger.info("🚀 Iniciando servidor webhook...")
    try:
        # Inicializa o handler de webhook
        get_webhook_handler()
        logger.info("✅ Servidor webhook iniciado com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro na inicialização do servidor webhook: {str(e)}")
        logger.error(traceback.format_exc())

@app.get("/")
async def root():
    """Endpoint raiz para verificar se o servidor está funcionando"""
    return {
        "status": "online",
        "message": "Servidor webhook do Chatwoot está funcionando!",
        "timestamp": str(datetime.now())
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde (health check)"""
    return {
        "status": "healthy",
        "timestamp": str(datetime.now())
    }

@app.post("/webhook")
async def webhook(request: Request, handler: ChatwootWebhookHandler = Depends(get_webhook_handler)):
    """Endpoint para receber webhooks do Chatwoot"""
    try:
        # Registra chegada do webhook com timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        logger.info(f"📩 [{timestamp}] Webhook recebido do Chatwoot")
        
        # Registra headers da requisição para debug
        headers = dict(request.headers)
        logger.debug(f"Headers da requisição: {json.dumps(headers, indent=2)}")
        
        # Obtém dados do webhook
        data = await request.json()
        
        # Log completo dos dados para arquivo
        with open('logs/last_webhook_payload.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        # Log resumido para console
        logger.debug(f"Dados do webhook: {json.dumps(data, indent=2)[:1000]}...")
        
        # Verifica o tipo de evento
        event_type = data.get("event")
        if not event_type:
            logger.warning("⚠️ Webhook sem tipo de evento")
            raise HTTPException(status_code=400, detail="Tipo de evento não especificado")
        
        # Extrai informações importantes para log
        message_info = ""
        if event_type == "message_created":
            message = data.get("message", {})
            conversation = data.get("conversation", {})
            contact = data.get("contact", {})
            message_info = f"ID: {message.get('id')}, Conversa: {conversation.get('id')}, Contato: {contact.get('name')}"
            logger.info(f"📨 Mensagem: '{message.get('content', '')[:100]}...'")
        
        # Processa o webhook
        logger.info(f"⚙️ Processando evento: {event_type} | {message_info}")
        response = await handler.process_webhook(data)
        
        # Retorna a resposta do processamento com detalhes
        logger.info(f"✅ Webhook processado com sucesso: {json.dumps(response)}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar webhook: {str(e)}")

def main():
    """Função principal para iniciar o servidor"""
    # Usa valores de .env ou padrões
    port = int(os.getenv("WEBHOOK_PORT", "8000"))
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")  # Importante usar 0.0.0.0 para funcionar com ngrok
    
    print("\n" + "="*70)
    print("🚀 INICIANDO SERVIDOR WEBHOOK PARA CHATWOOT")
    print("="*70)
    print(f"📡 Servidor rodando em: http://{host}:{port}")
    print(f"🔗 Use ngrok para expor este servidor para a internet:")
    print(f"   ngrok http {port}")
    print("="*70 + "\n")
    
    # Inicia o servidor
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()