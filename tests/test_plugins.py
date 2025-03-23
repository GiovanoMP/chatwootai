"""
Script para testar os plugins do ChatwootAI.

Este script carrega e testa os plugins implementados, verificando
se eles estão funcionando corretamente.
"""
import logging
import sys
import os
from typing import Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("test_plugins")

# Adicionar diretório raiz ao path para importações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar classes necessárias
from src.plugins.core.plugin_manager import PluginManager
from src.plugins.base.base_plugin import BasePlugin

def create_test_config() -> Dict[str, Any]:
    """
    Cria uma configuração de teste para o PluginManager.
    
    Returns:
        Configuração de teste
    """
    return {
        "plugin_paths": [
            "src.plugins.core",
            "src.plugins.implementations"
        ],
        "enabled_plugins": [
            "sentiment_analysis_plugin",
            "response_enhancer_plugin",
            "faq_knowledge_plugin"
        ],
        "plugins": {
            "sentiment_analysis_plugin": {
                "threshold": 0.3,
                "positive_words": ["ótimo", "excelente", "adoro", "perfeito"],
                "negative_words": ["péssimo", "horrível", "detesto", "ruim"]
            },
            "response_enhancer_plugin": {
                "enhancement_probability": 1.0,  # Sempre aplicar para testes
                "max_enhancements": 2
            },
            "faq_knowledge_plugin": {
                "min_similarity_score": 0.5,  # Limiar mais baixo para testes
                "max_results": 2
            }
        }
    }

def test_sentiment_analysis_plugin(plugin_manager: PluginManager):
    """
    Testa o plugin de análise de sentimento.
    
    Args:
        plugin_manager: Gerenciador de plugins
    """
    logger.info("\n=== Testando SentimentAnalysisPlugin ===")
    
    # Verificar se o plugin está disponível
    if not plugin_manager.has_plugin("sentiment_analysis_plugin"):
        logger.error("Plugin de análise de sentimento não encontrado!")
        return
    
    # Obter o plugin
    plugin = plugin_manager.get_plugin("sentiment_analysis_plugin")
    
    # Testar análise de sentimento com diferentes mensagens
    test_messages = [
        "Estou muito feliz com o produto, é excelente!",
        "Esse produto é horrível, não funciona como deveria.",
        "Gostaria de informações sobre entrega do pedido."
    ]
    
    for message in test_messages:
        logger.info(f"\nMensagem: '{message}'")
        
        # Analisar sentimento
        context = {}
        result = plugin.process_message(message, context)
        
        # Exibir resultado
        sentiment = result.get("sentiment", {})
        logger.info(f"Sentimento: {sentiment.get('sentiment')}")
        logger.info(f"Pontuação: {sentiment.get('score', 0):.2f}")
        logger.info(f"Confiança: {sentiment.get('confidence', 0):.2f}")
        
        # Testar adaptação de resposta
        original_response = "Obrigado por entrar em contato conosco."
        adapted_response = plugin.process_response(original_response, result)
        logger.info(f"Resposta original: '{original_response}'")
        logger.info(f"Resposta adaptada: '{adapted_response}'")

def test_response_enhancer_plugin(plugin_manager: PluginManager):
    """
    Testa o plugin de enriquecimento de respostas.
    
    Args:
        plugin_manager: Gerenciador de plugins
    """
    logger.info("\n=== Testando ResponseEnhancerPlugin ===")
    
    # Verificar se o plugin está disponível
    if not plugin_manager.has_plugin("response_enhancer_plugin"):
        logger.error("Plugin de enriquecimento de respostas não encontrado!")
        return
    
    # Obter o plugin
    plugin = plugin_manager.get_plugin("response_enhancer_plugin")
    
    # Testar enriquecimento com diferentes contextos
    test_cases = [
        {
            "response": "Temos vários tipos de creme para as mãos disponíveis.",
            "context": {
                "domain": {"name": "cosmetics"},
                "last_message": "Vocês têm creme para as mãos?"
            }
        },
        {
            "response": "Nossos protetores solares oferecem alta proteção contra raios UVA e UVB.",
            "context": {
                "domain": {"name": "health"},
                "last_message": "Preciso de um protetor solar bom."
            }
        }
    ]
    
    for case in test_cases:
        logger.info(f"\nResposta original: '{case['response']}'")
        logger.info(f"Contexto: {case['context']}")
        
        # Enriquecer resposta
        enhanced_response = plugin.process_response(case["response"], case["context"])
        
        # Exibir resultado
        logger.info(f"Resposta enriquecida:\n{enhanced_response}")

def test_faq_knowledge_plugin(plugin_manager: PluginManager):
    """
    Testa o plugin de base de conhecimento e FAQs.
    
    Args:
        plugin_manager: Gerenciador de plugins
    """
    logger.info("\n=== Testando FAQKnowledgePlugin ===")
    
    # Verificar se o plugin está disponível
    if not plugin_manager.has_plugin("faq_knowledge_plugin"):
        logger.error("Plugin de FAQs não encontrado!")
        return
    
    # Obter o plugin
    plugin = plugin_manager.get_plugin("faq_knowledge_plugin")
    
    # Testar consultas à base de conhecimento
    test_queries = [
        "Como faço para devolver um produto?",
        "Qual o prazo de entrega dos pedidos?",
        "Vocês têm alguma loja física?",
        "Como devo aplicar o protetor solar?",
        "Quais produtos são bons para pele oleosa?"
    ]
    
    for query in test_queries:
        logger.info(f"\nConsulta: '{query}'")
        
        # Processar mensagem
        context = {}
        result = plugin.process_message(query, context)
        
        # Verificar se houve match
        faq_match = result.get("faq_match", {})
        found = faq_match.get("found", False)
        similarity = faq_match.get("similarity", 0)
        
        logger.info(f"Match encontrado: {found}")
        logger.info(f"Similaridade: {similarity:.2f}")
        
        if found:
            response = faq_match.get("response", "")
            logger.info(f"Resposta: '{response}'")

def main():
    """
    Função principal para testar os plugins.
    """
    logger.info("Iniciando testes de plugins do ChatwootAI")
    
    # Criar configuração de teste
    config = create_test_config()
    
    # Criar gerenciador de plugins
    plugin_manager = PluginManager(config)
    
    # Carregar plugins
    logger.info("Carregando plugins...")
    plugins = plugin_manager.load_plugins()
    logger.info(f"Plugins carregados: {len(plugins)}")
    
    # Listar plugins carregados
    for name, plugin in plugins.items():
        logger.info(f"- {name}: {plugin.__class__.__name__}")
    
    # Testar cada plugin
    test_sentiment_analysis_plugin(plugin_manager)
    test_response_enhancer_plugin(plugin_manager)
    test_faq_knowledge_plugin(plugin_manager)
    
    logger.info("\nTestes de plugins concluídos com sucesso!")

if __name__ == "__main__":
    main()
