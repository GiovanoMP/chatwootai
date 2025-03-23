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
    Inicializa o sistema completo usando a mesma abordagem 
    que funcionou nos testes manuais
    """
    logger.info("🚀 Inicializando sistema para receber webhooks do Chatwoot...")
    
    # Sistema de memória
    memory_system = MemorySystem()
    logger.info("✅ Sistema de memória inicializado")
    
    # Gerenciador de domínio
    domain_manager = DomainManager()
    domain_manager.switch_domain("cosmetics")
    logger.info(f"✅ Domínio 'cosmetics' carregado com sucesso")
    
    # Gerenciador de plugins
    plugin_config = {
        "enabled_plugins": ["sentiment_analysis_plugin", "faq_knowledge_plugin", "response_enhancer_plugin"]
    }
    plugin_manager = PluginManager(config=plugin_config)
    logger.info("✅ Gerenciador de plugins inicializado")
    
    # DataServiceHub
    data_service_hub = DataServiceHub()
    logger.info("✅ DataServiceHub inicializado")
    
    # HubCrew (centro da arquitetura hub-and-spoke)
    hub_crew = HubCrew(
        memory_system=memory_system,
        data_service_hub=data_service_hub
    )
    logger.info("✅ HubCrew inicializado")
    
    # SalesCrew
    sales_crew = SalesCrew(
        memory_system=memory_system,
        domain_manager=domain_manager,
        data_service_hub=data_service_hub,
        plugin_manager=plugin_manager
    )
    logger.info("✅ SalesCrew inicializada")
    
    # Registra a SalesCrew no HubCrew (como no test_message_manually.py)
    functional_crews = {
        "sales": sales_crew
    }
    
    # Adiciona as crews funcionais ao HubCrew
    setattr(hub_crew, "_functional_crews", functional_crews)
    logger.info("✅ Crews funcionais registradas no HubCrew")
    
    # Configuração do webhook handler
    webhook_config = {
        "chatwoot_base_url": os.getenv('CHATWOOT_BASE_URL'),
        "chatwoot_api_key": os.getenv('CHATWOOT_API_KEY'),
        "channel_mapping": {"1": "whatsapp"}
    }
    
    # Inicializa o webhook handler
    webhook_handler = ChatwootWebhookHandler(
        hub_crew=hub_crew,
        config=webhook_config
    )
    logger.info("✅ ChatwootWebhookHandler inicializado")
    
    logger.info("🎉 Sistema inicializado com sucesso para receber webhooks!")
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