"""
Rotas da API do MCP-Crew System v2
Sistema atualizado com provisão dinâmica de ferramentas e compartilhamento de conhecimento
"""

import asyncio
import logging
from flask import Blueprint, request, jsonify
from typing import Dict, Any

from src.core.orchestrator import mcp_crew_orchestrator
from src.core.mcp_tool_discovery import tool_discovery
from src.core.knowledge_manager import knowledge_manager, KnowledgeItem, KnowledgeType
from src.config.config import Config, validate_account_id

logger = logging.getLogger(__name__)

mcp_crew_bp = Blueprint('mcp_crew', __name__, url_prefix='/api/mcp-crew')

@mcp_crew_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificação de saúde"""
    try:
        health_status = mcp_crew_orchestrator.get_health_status()
        return jsonify(health_status), 200
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@mcp_crew_bp.route('/process_request', methods=['POST'])
def process_request():
    """Endpoint principal para processamento de requisições"""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({"error": "Dados da requisição são obrigatórios"}), 400
        
        account_id = request_data.get('account_id')
        if not account_id or not validate_account_id(account_id):
            return jsonify({"error": "account_id válido é obrigatório"}), 400
        
        # Processar requisição de forma assíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                mcp_crew_orchestrator.process_request(request_data)
            )
        finally:
            loop.close()
        
        return jsonify(result), 200 if result.get('success') else 500
        
    except Exception as e:
        logger.error(f"Erro ao processar requisição: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@mcp_crew_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Endpoint para obter métricas gerais"""
    try:
        # Métricas globais (sem account_id específico)
        return jsonify({
            "system_status": "operational",
            "mcps_configured": len(Config.MCP_REGISTRY),
            "features": {
                "dynamic_tool_discovery": True,
                "knowledge_sharing": True,
                "redis_caching": True
            }
        }), 200
    except Exception as e:
        logger.error(f"Erro ao obter métricas: {e}")
        return jsonify({"error": str(e)}), 500

@mcp_crew_bp.route('/tenant/<account_id>/metrics', methods=['GET'])
def get_tenant_metrics(account_id: str):
    """Endpoint para obter métricas específicas de um tenant"""
    try:
        if not validate_account_id(account_id):
            return jsonify({"error": "account_id inválido"}), 400
        
        metrics = mcp_crew_orchestrator.get_metrics(account_id)
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas do tenant: {e}")
        return jsonify({"error": str(e)}), 500

# === Endpoints de Descoberta de Ferramentas ===

@mcp_crew_bp.route('/tools/discover', methods=['POST'])
def discover_tools():
    """Força descoberta de ferramentas para um tenant"""
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        force_refresh = data.get('force_refresh', False)
        
        if not account_id or not validate_account_id(account_id):
            return jsonify({"error": "account_id válido é obrigatório"}), 400
        
        # Executar descoberta
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tools = loop.run_until_complete(
                tool_discovery.discover_all_tools(account_id, force_refresh)
            )
        finally:
            loop.close()
        
        # Converter para formato serializável
        tools_summary = {}
        for mcp_name, tool_list in tools.items():
            tools_summary[mcp_name] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "mcp_source": tool.mcp_source,
                    "last_updated": tool.last_updated
                }
                for tool in tool_list
            ]
        
        return jsonify({
            "success": True,
            "tools_discovered": tools_summary,
            "total_tools": sum(len(tool_list) for tool_list in tools.values())
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na descoberta de ferramentas: {e}")
        return jsonify({"error": str(e)}), 500

@mcp_crew_bp.route('/tools/summary/<account_id>', methods=['GET'])
def get_tools_summary(account_id: str):
    """Obtém resumo das ferramentas disponíveis"""
    try:
        if not validate_account_id(account_id):
            return jsonify({"error": "account_id inválido"}), 400
        
        summary = tool_discovery.get_available_tools_summary(account_id)
        return jsonify({
            "account_id": account_id,
            "tools_by_mcp": summary,
            "total_tools": sum(summary.values())
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter resumo de ferramentas: {e}")
        return jsonify({"error": str(e)}), 500

@mcp_crew_bp.route('/tools/cache/invalidate', methods=['POST'])
def invalidate_tools_cache():
    """Invalida cache de ferramentas"""
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        mcp_name = data.get('mcp_name')  # Opcional
        
        if not account_id or not validate_account_id(account_id):
            return jsonify({"error": "account_id válido é obrigatório"}), 400
        
        # Invalidar cache
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                tool_discovery.invalidate_tools_cache(account_id, mcp_name)
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "message": f"Cache invalidado para {mcp_name or 'todos os MCPs'}"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao invalidar cache: {e}")
        return jsonify({"error": str(e)}), 500

# === Endpoints de Compartilhamento de Conhecimento ===

@mcp_crew_bp.route('/knowledge/store', methods=['POST'])
def store_knowledge():
    """Armazena item de conhecimento"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['account_id', 'type', 'topic', 'title', 'content', 'source_agent']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Campo obrigatório: {field}"}), 400
        
        account_id = data['account_id']
        if not validate_account_id(account_id):
            return jsonify({"error": "account_id inválido"}), 400
        
        # Criar item de conhecimento
        knowledge_item = KnowledgeItem(
            id="",  # Será gerado automaticamente
            type=KnowledgeType(data['type']),
            topic=data['topic'],
            title=data['title'],
            content=data['content'],
            metadata=data.get('metadata', {}),
            source_agent=data['source_agent'],
            source_crew=data.get('source_crew', 'unknown'),
            account_id=account_id,
            created_at=data.get('created_at', None),  # None = usar timestamp atual
            expires_at=data.get('expires_at'),
            tags=data.get('tags', []),
            confidence_score=data.get('confidence_score', 1.0)
        )
        
        # Armazenar conhecimento
        success = knowledge_manager.store_knowledge(knowledge_item)
        
        if success:
            return jsonify({
                "success": True,
                "knowledge_id": knowledge_item.id,
                "message": "Conhecimento armazenado com sucesso"
            }), 201
        else:
            return jsonify({"error": "Falha ao armazenar conhecimento"}), 500
        
    except ValueError as e:
        return jsonify({"error": f"Tipo de conhecimento inválido: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Erro ao armazenar conhecimento: {e}")
        return jsonify({"error": str(e)}), 500

@mcp_crew_bp.route('/knowledge/retrieve/<account_id>/<knowledge_id>', methods=['GET'])
def retrieve_knowledge(account_id: str, knowledge_id: str):
    """Recupera item de conhecimento específico"""
    try:
        if not validate_account_id(account_id):
            return jsonify({"error": "account_id inválido"}), 400
        
        topic = request.args.get('topic')  # Opcional
        
        knowledge_item = knowledge_manager.retrieve_knowledge(account_id, knowledge_id, topic)
        
        if knowledge_item:
            return jsonify({
                "success": True,
                "knowledge": knowledge_item.to_dict()
            }), 200
        else:
            return jsonify({"error": "Conhecimento não encontrado"}), 404
        
    except Exception as e:
        logger.error(f"Erro ao recuperar conhecimento: {e}")
        return jsonify({"error": str(e)}), 500

@mcp_crew_bp.route('/knowledge/search/<account_id>', methods=['GET'])
def search_knowledge(account_id: str):
    """Busca conhecimento por tópico ou conteúdo"""
    try:
        if not validate_account_id(account_id):
            return jsonify({"error": "account_id inválido"}), 400
        
        topic = request.args.get('topic')
        query = request.args.get('query')
        limit = int(request.args.get('limit', 10))
        tags = request.args.getlist('tags')
        
        if not topic and not query:
            return jsonify({"error": "Parâmetro 'topic' ou 'query' é obrigatório"}), 400
        
        if topic:
            # Busca por tópico
            results = knowledge_manager.search_knowledge_by_topic(
                account_id, topic, limit, tags if tags else None
            )
        else:
            # Busca por conteúdo
            results = knowledge_manager.search_knowledge_by_content(
                account_id, query, limit
            )
        
        return jsonify({
            "success": True,
            "results": [item.to_dict() for item in results],
            "count": len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na busca de conhecimento: {e}")
        return jsonify({"error": str(e)}), 500

@mcp_crew_bp.route('/knowledge/events/<account_id>', methods=['GET'])
def get_knowledge_events(account_id: str):
    """Obtém eventos de conhecimento"""
    try:
        if not validate_account_id(account_id):
            return jsonify({"error": "account_id inválido"}), 400
        
        last_id = request.args.get('last_id', '0')
        count = int(request.args.get('count', 10))
        
        events = knowledge_manager.get_knowledge_events(account_id, last_id, count)
        
        return jsonify({
            "success": True,
            "events": [event.to_dict() for event in events],
            "count": len(events)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter eventos de conhecimento: {e}")
        return jsonify({"error": str(e)}), 500

@mcp_crew_bp.route('/knowledge/stats/<account_id>', methods=['GET'])
def get_knowledge_stats(account_id: str):
    """Obtém estatísticas de conhecimento"""
    try:
        if not validate_account_id(account_id):
            return jsonify({"error": "account_id inválido"}), 400
        
        stats = knowledge_manager.get_knowledge_stats(account_id)
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({"error": str(e)}), 500

@mcp_crew_bp.route('/knowledge/cleanup/<account_id>', methods=['POST'])
def cleanup_expired_knowledge(account_id: str):
    """Remove conhecimento expirado"""
    try:
        if not validate_account_id(account_id):
            return jsonify({"error": "account_id inválido"}), 400
        
        removed_count = knowledge_manager.cleanup_expired_knowledge(account_id)
        
        return jsonify({
            "success": True,
            "removed_count": removed_count,
            "message": f"Removidos {removed_count} itens expirados"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na limpeza de conhecimento: {e}")
        return jsonify({"error": str(e)}), 500

# === Endpoints de Configuração ===

@mcp_crew_bp.route('/config/mcps', methods=['GET'])
def get_mcp_config():
    """Obtém configuração dos MCPs"""
    try:
        mcps_config = {}
        for mcp_name, mcp_config in Config.MCP_REGISTRY.items():
            mcps_config[mcp_name] = {
                "name": mcp_config.name,
                "url": mcp_config.url,
                "enabled": mcp_config.enabled,
                "cache_ttl": mcp_config.cache_ttl,
                "timeout": mcp_config.timeout
            }
        
        return jsonify({
            "success": True,
            "mcps": mcps_config,
            "total_mcps": len(mcps_config)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter configuração de MCPs: {e}")
        return jsonify({"error": str(e)}), 500

@mcp_crew_bp.route('/config/knowledge-types', methods=['GET'])
def get_knowledge_types():
    """Obtém tipos de conhecimento disponíveis"""
    try:
        knowledge_types = [
            {
                "value": kt.value,
                "name": kt.name,
                "description": f"Tipo de conhecimento: {kt.value}"
            }
            for kt in KnowledgeType
        ]
        
        return jsonify({
            "success": True,
            "knowledge_types": knowledge_types
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter tipos de conhecimento: {e}")
        return jsonify({"error": str(e)}), 500

# === Endpoints de Administração ===

@mcp_crew_bp.route('/admin/system-info', methods=['GET'])
def get_system_info():
    """Obtém informações do sistema (apenas para administração)"""
    try:
        return jsonify({
            "success": True,
            "system_info": {
                "version": "2.0.0",
                "features": {
                    "dynamic_tool_discovery": True,
                    "knowledge_sharing": True,
                    "redis_caching": True,
                    "multi_tenant": True
                },
                "mcps_configured": len(Config.MCP_REGISTRY),
                "redis_available": True,  # Simplificado
                "cache_ttl_default": Config.DEFAULT_CACHE_TTL,
                "tools_cache_ttl": Config.TOOLS_CACHE_TTL,
                "knowledge_cache_ttl": Config.KNOWLEDGE_CACHE_TTL
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter informações do sistema: {e}")
        return jsonify({"error": str(e)}), 500

# Tratamento de erros
@mcp_crew_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint não encontrado"}), 404

@mcp_crew_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Método não permitido"}), 405

@mcp_crew_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Erro interno: {error}")
    return jsonify({"error": "Erro interno do servidor"}), 500

