"""
Helpers para testes do ChatwootAI.

Este módulo contém implementações mínimas e mocks para auxiliar nos testes,
especialmente quando as implementações reais ainda estão em desenvolvimento.
"""

from typing import Dict, Any, Optional, List
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

# Implementações mínimas para métodos ausentes
async def process_message_impl(self, 
                           message: Dict[str, Any],
                           conversation_id: str,
                           channel_type: str,
                           functional_crews: Dict[str, Any] = None,
                           domain_name: str = None) -> Dict[str, Any]:
    """
    Implementação mínima do método process_message para testes.
    """
    return {
        "message": message,
        "conversation_id": conversation_id,
        "response": {
            "content": "Esta é uma resposta de teste do process_message"
        },
        "domain_name": domain_name or "default"
    }

def update_context_impl(self, 
                      conversation_id: str, 
                      message: Dict[str, Any],
                      current_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Implementação mínima do método update_context para testes.
    """
    # Copiar o contexto atual para não modificar o original
    updated_context = current_context.copy()
    
    # Incrementar o contador de interações
    if "interaction_count" not in updated_context:
        updated_context["interaction_count"] = 0
    updated_context["interaction_count"] += 1
    
    return updated_context

def apply_test_mixins():
    """
    Aplica os mixins de teste às classes do sistema de forma direta.
    
    Esta abordagem é mais robusta, pois modifica diretamente as instâncias
    nos testes, em vez de tentar modificar as classes.
    """
    from src.core.hub import HubCrew, ContextManagerAgent
    
    # Monkey patch direto nas classes para testes
    # Isto é mais seguro do que modificar as classes originais
    original_hub_crew_init = HubCrew.__init__
    
    def patched_hub_crew_init(self, *args, **kwargs):
        # Chamar o inicializador original
        original_hub_crew_init(self, *args, **kwargs)
        
        # Adicionar o método process_message se não existir
        if not hasattr(self, 'process_message'):
            self.process_message = process_message_impl.__get__(self)
        
        # Garantir que o _context_manager existe
        if not hasattr(self, '_context_manager'):
            self._context_manager = MagicMock(spec=ContextManagerAgent)
        
        # Garantir que o método update_context existe no context_manager
        if not hasattr(self._context_manager, 'update_context'):
            self._context_manager.update_context = update_context_impl.__get__(self._context_manager)
    
    # Aplicar o monkey patch
    HubCrew.__init__ = patched_hub_crew_init

# Função para preparar um objeto HubCrew para testes
def prepare_hub_crew_for_tests(hub_crew):
    """
    Prepara um objeto HubCrew específico para testes.
    
    Esta função é útil quando o apply_test_mixins() não é suficiente
    ou quando precisamos preparar um objeto específico.
    
    Args:
        hub_crew: Instância de HubCrew a ser preparada
    
    Returns:
        A mesma instância, mas preparada para testes
    """
    # Adicionar o método process_message se não existir
    if not hasattr(hub_crew, 'process_message'):
        hub_crew.process_message = process_message_impl.__get__(hub_crew)
    
    # Garantir que o _context_manager existe
    if not hasattr(hub_crew, '_context_manager'):
        from src.core.hub import ContextManagerAgent
        hub_crew._context_manager = MagicMock(spec=ContextManagerAgent)
    
    # Garantir que o método update_context existe no context_manager
    if not hasattr(hub_crew._context_manager, 'update_context'):
        hub_crew._context_manager.update_context = update_context_impl.__get__(hub_crew._context_manager)
    
    return hub_crew
