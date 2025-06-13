#!/usr/bin/env python3
"""
Script para testar o gerenciador de sessões.
"""

import logging
import time
from typing import Dict

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SessionManagerTest")

# Importar o gerenciador de sessões e o redis_manager
from src.redis_manager.session_manager import SessionManager
from src.redis_manager.redis_manager import redis_manager, DataType

def test_session_crud():
    """Testa operações CRUD de sessão."""
    logger.info("=== Teste de Operações CRUD de Sessão ===")
    
    # Criar gerenciador de sessões
    session_mgr = SessionManager(tenant_id="test_account")
    
    # Criar sessão
    user_id = "user123"
    initial_data = {"preferences": {"theme": "dark"}, "last_page": "/dashboard"}
    
    session_id = session_mgr.create_session(user_id, initial_data, ttl=60)
    logger.info(f"Sessão criada: {session_id}")
    
    if not session_id:
        logger.error("Falha ao criar sessão")
        return False
    
    # Recuperar sessão
    session = session_mgr.get_session(session_id)
    logger.info(f"Sessão recuperada: {session}")
    
    if not session or session.get("user_id") != user_id:
        logger.error("Falha ao recuperar sessão")
        return False
    
    # Atualizar sessão
    update_data = {"current_action": "testing", "timestamp": time.time()}
    updated = session_mgr.update_session(session_id, update_data)
    logger.info(f"Sessão atualizada: {updated}")
    
    # Verificar atualização
    updated_session = session_mgr.get_session(session_id)
    has_new_data = (
        updated_session and 
        "current_action" in updated_session.get("data", {}) and
        updated_session["data"]["current_action"] == "testing"
    )
    logger.info(f"Dados atualizados presentes: {has_new_data}")
    
    # Excluir sessão
    deleted = session_mgr.delete_session(session_id)
    logger.info(f"Sessão excluída: {deleted}")
    
    # Verificar exclusão
    deleted_session = session_mgr.get_session(session_id)
    is_deleted = deleted_session is None
    logger.info(f"Sessão realmente excluída: {is_deleted}")
    
    return session_id and updated and has_new_data and deleted and is_deleted

def test_user_sessions():
    """Testa gerenciamento de múltiplas sessões de usuário."""
    logger.info("\n=== Teste de Múltiplas Sessões de Usuário ===")
    
    # Criar gerenciador de sessões
    session_mgr = SessionManager(tenant_id="test_account")
    
    # Criar múltiplas sessões para o mesmo usuário
    user_id = "multi_session_user"
    session_ids = []
    
    for i in range(3):
        data = {"device": f"device_{i}", "login_time": time.time()}
        session_id = session_mgr.create_session(user_id, data, ttl=60)
        if session_id:
            session_ids.append(session_id)
    
    logger.info(f"Sessões criadas: {len(session_ids)}")
    
    # Recuperar todas as sessões do usuário
    user_sessions = session_mgr.get_user_sessions(user_id)
    logger.info(f"Sessões do usuário recuperadas: {len(user_sessions)}")
    
    # Limpar sessões
    for session_id in session_ids:
        session_mgr.delete_session(session_id)
    
    return len(session_ids) == 3 and len(user_sessions) >= len(session_ids)

def test_session_expiry():
    """Testa expiração e limpeza de sessões."""
    logger.info("\n=== Teste de Expiração de Sessões ===")
    
    # Criar gerenciador de sessões
    session_mgr = SessionManager(tenant_id="test_account")
    
    # Criar sessões com TTL curto
    user_id = "expiry_test_user"
    short_ttl = 2  # 2 segundos
    
    session_id = session_mgr.create_session(user_id, {"test": "expiry"}, ttl=short_ttl)
    logger.info(f"Sessão com TTL curto criada: {session_id}")
    
    # Verificar se a sessão existe
    session = session_mgr.get_session(session_id)
    exists_before = session is not None
    logger.info(f"Sessão existe antes da expiração: {exists_before}")
    
    # Aguardar expiração
    logger.info("Aguardando expiração (3 segundos)...")
    time.sleep(3)
    
    # Verificar se a sessão ainda existe
    expired_session = session_mgr.get_session(session_id)
    expired = expired_session is None
    logger.info(f"Sessão expirou corretamente: {expired}")
    
    # Testar limpeza manual
    # Criar algumas sessões "antigas"
    old_sessions = []
    for i in range(3):
        old_id = session_mgr.create_session(f"cleanup_user_{i}", {"old": True})
        if old_id:
            old_sessions.append(old_id)
            
            # Forçar last_accessed para um tempo antigo
            session_data = session_mgr.get_session(old_id, update_access=False)
            if session_data:
                session_data["last_accessed"] = time.time() - 3600  # 1 hora atrás
                redis_manager.set(
                    tenant_id="test_account",
                    data_type=DataType.CONVERSATION_CONTEXT,
                    identifier=f"session:{old_id}",
                    value=session_data
                )
    
    # Executar limpeza
    cleaned = session_mgr.cleanup_expired_sessions(max_idle_time=1800)  # 30 minutos
    logger.info(f"Sessões limpas: {cleaned}")
    
    # Limpar sessões restantes
    for session_id in old_sessions:
        session_mgr.delete_session(session_id)
    
    return exists_before and expired and cleaned >= len(old_sessions)

def run_all_tests():
    """Executa todos os testes e retorna o resultado"""
    results = {}
    
    # Teste CRUD
    results["session_crud"] = test_session_crud()
    
    # Teste de múltiplas sessões
    results["user_sessions"] = test_user_sessions()
    
    # Teste de expiração
    results["session_expiry"] = test_session_expiry()
    
    # Resumo
    logger.info("\n=== Resumo dos Testes ===")
    for test, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"{test}: {status}")
    
    return all(results.values())

if __name__ == "__main__":
    success = run_all_tests()
    exit_code = 0 if success else 1
    logger.info(f"\nTestes {'concluídos com sucesso' if success else 'falharam'}")
    exit(exit_code)
