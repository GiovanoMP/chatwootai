#!/usr/bin/env python3
# MCP-Crew - Script de inicialização para ambiente Docker
import os
import asyncio
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

# Importar componentes do MCP-Crew
from context_manager import ContextManager
from mcp_connector_manager import MCPConnectorManager
from crew_manager import CrewManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp-crew")

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
DEFAULT_TENANT = os.getenv('DEFAULT_TENANT', 'account_1')
MULTI_TENANT = os.getenv('MULTI_TENANT', 'true').lower() == 'true'
REDIS_URI = os.getenv('REDIS_URI', 'redis://localhost:6379/0')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
MCP_MONGODB_URL = os.getenv('MCP_MONGODB_URL', 'http://mcp-mongodb:8000')
MCP_QDRANT_URL = os.getenv('MCP_QDRANT_URL', 'http://mcp-qdrant:8000')
PORT = int(os.getenv('PORT', '5000'))

# Ajustar URI do Redis se houver senha
if REDIS_PASSWORD:
    REDIS_URI = REDIS_URI.replace('redis://', f'redis://:{REDIS_PASSWORD}@')

# Inicializar componentes
context_manager = ContextManager(redis_uri=REDIS_URI)
mcp_connector_manager = MCPConnectorManager(context_manager=context_manager)
crew_manager = CrewManager(context_manager=context_manager, mcp_connector_manager=mcp_connector_manager)

# Inicializar Flask
app = Flask(__name__)
CORS(app)

# Registrar conectores MCP disponíveis
async def register_mcps():
    # Registrar MCP-MongoDB
    await mcp_connector_manager.register_connector(
        "mongodb",
        {
            "base_url": MCP_MONGODB_URL,
            "multi_tenant": MULTI_TENANT,
            "default_tenant": DEFAULT_TENANT
        }
    )
    logger.info(f"MCP-MongoDB registrado com sucesso: {MCP_MONGODB_URL}")
    
    # Registrar MCP-Qdrant
    await mcp_connector_manager.register_connector(
        "qdrant",
        {
            "base_url": MCP_QDRANT_URL,
            "multi_tenant": MULTI_TENANT,
            "default_tenant": DEFAULT_TENANT
        }
    )
    logger.info(f"MCP-Qdrant registrado com sucesso: {MCP_QDRANT_URL}")

# Rotas da API
@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificação de saúde"""
    return jsonify({
        "status": "healthy",
        "service": "mcp-crew",
        "version": "0.1.0"
    })

@app.route('/mcps', methods=['GET'])
def list_mcps():
    """Lista todos os MCPs registrados"""
    mcps = mcp_connector_manager.list_connectors()
    return jsonify({
        "mcps": mcps
    })

@app.route('/crews', methods=['GET'])
async def list_crews():
    """Lista todas as crews disponíveis"""
    account_id = request.args.get('account_id', DEFAULT_TENANT)
    crews = await crew_manager.list_crews(account_id)
    return jsonify({
        "account_id": account_id,
        "crews": crews
    })

@app.route('/crews', methods=['POST'])
async def create_crew():
    """Cria uma nova crew"""
    data = request.json
    account_id = data.get('account_id', DEFAULT_TENANT)
    crew_name = data.get('name')
    crew_config = data.get('config', {})
    
    if not crew_name:
        return jsonify({"error": "Nome da crew é obrigatório"}), 400
    
    crew_id = await crew_manager.create_crew(account_id, crew_name, crew_config)
    return jsonify({
        "account_id": account_id,
        "crew_id": crew_id,
        "message": f"Crew '{crew_name}' criada com sucesso"
    })

@app.route('/crews/<crew_id>/run', methods=['POST'])
async def run_crew(crew_id):
    """Executa uma crew específica"""
    data = request.json
    account_id = data.get('account_id', DEFAULT_TENANT)
    task_input = data.get('input', {})
    
    result = await crew_manager.run_crew(account_id, crew_id, task_input)
    return jsonify({
        "account_id": account_id,
        "crew_id": crew_id,
        "result": result
    })

@app.route('/mcp/<mcp_name>/execute', methods=['POST'])
async def execute_mcp_operation(mcp_name):
    """Executa uma operação em um MCP específico"""
    data = request.json
    account_id = data.get('account_id', DEFAULT_TENANT)
    operation = data.get('operation')
    method = data.get('method', 'GET')
    endpoint = data.get('endpoint')
    params = data.get('params', {})
    payload = data.get('payload', {})
    headers = data.get('headers', {})
    
    if not operation or not endpoint:
        return jsonify({"error": "Operação e endpoint são obrigatórios"}), 400
    
    try:
        result = await mcp_connector_manager.execute_operation(
            mcp_name, account_id, operation, method, endpoint, params, payload, headers
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Função para inicializar os componentes de forma assíncrona
async def init_components():
    """Inicializa todos os componentes necessários"""
    logger.info("Inicializando componentes do MCP-Crew...")
    await context_manager.initialize()
    await register_mcps()
    logger.info("Componentes inicializados com sucesso!")

# Função principal para iniciar o servidor
def start_server():
    """Inicia o servidor Flask"""
    # Executar inicialização assíncrona
    asyncio.run(init_components())
    
    # Iniciar servidor Flask
    logger.info(f"Iniciando servidor MCP-Crew na porta {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    start_server()
