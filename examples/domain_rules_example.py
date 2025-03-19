"""
Exemplo de uso do DomainRulesService para consultar regras de domínio.

Este script demonstra como:
- Inicializar o sistema de serviços de dados
- Acessar o DomainRulesService
- Carregar diferentes domínios
- Consultar regras de negócio por tipo
- Realizar buscas semânticas por regras relevantes
"""

import os
import sys
import logging

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.data.data_service_hub import DataServiceHub
from src.services.data.domain_rules_service import DomainRulesService

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_divider():
    """Imprime uma linha divisória para melhorar a legibilidade"""
    print("\n" + "=" * 80 + "\n")

def main():
    """
    Função principal que demonstra o uso do DomainRulesService
    """
    logger.info("Inicializando exemplo de DomainRulesService")
    
    # Inicializar o DataServiceHub
    data_hub = DataServiceHub()
    
    # Inicializar diretamente o DomainRulesService
    domain_rules_service = DomainRulesService(data_hub)
    
    if not domain_rules_service:
        logger.error("Não foi possível inicializar o serviço de regras de domínio")
        return
    
    # Listar domínios disponíveis
    print_divider()
    print("DOMÍNIOS DISPONÍVEIS:")
    domains = domain_rules_service.domain_config.keys()
    for domain in domains:
        print(f"- {domain} ({'ATIVO' if domain == domain_rules_service.active_domain else 'Inativo'})")
    
    # Verificar domínio ativo e alterá-lo se necessário
    active_domain = domain_rules_service.get_active_domain()
    print(f"\nDomínio ativo: {active_domain}")
    
    # Ativar domínio de cosméticos se não for o ativo
    if active_domain != "cosmeticos":
        print("\nAlterando para o domínio de cosméticos...")
        domain_rules_service.set_active_domain("cosmeticos")
        print(f"Novo domínio ativo: {domain_rules_service.get_active_domain()}")
    
    # Obter todas as regras de negócio do domínio ativo
    print_divider()
    print("TODAS AS REGRAS DE NEGÓCIO:")
    rules = domain_rules_service.get_business_rules()
    print(f"Total de regras: {len(rules)}")
    for rule in rules:
        print(f"- {rule['type'].upper()}: {rule['title']}")
    
    # Obter apenas regras de tipo específico
    print_divider()
    print("REGRAS DE SUPORTE (FAQs):")
    support_rules = domain_rules_service.get_support_faqs()
    for rule in support_rules:
        print(f"- {rule['title']}")
        print(f"  Keywords: {', '.join(rule.get('keywords', []))}")
    
    # Realizar consulta semântica para encontrar regras relevantes
    print_divider()
    print("BUSCA SEMÂNTICA POR REGRAS:")
    
    queries = [
        "Como escolher produtos para pele sensível?",
        "Qual a política de devolução?",
        "Desconto para primeira compra"
    ]
    
    for query in queries:
        print(f"\nConsulta: '{query}'")
        results = domain_rules_service.query_rules(query, limit=2)
        
        if results:
            print(f"  Resultados encontrados: {len(results)}")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['title']}")
                print(f"     Tipo: {result['type']}")
                print(f"     Primeiras palavras: {result['content'][:60]}...")
        else:
            print("  Nenhum resultado encontrado")
    
    # Testar com outro domínio
    print_divider()
    print("ALTERANDO PARA DOMÍNIO DE SAÚDE:")
    if domain_rules_service.set_active_domain("saude"):
        print(f"Domínio ativo alterado para: {domain_rules_service.get_active_domain()}")
        
        # Listar regras do novo domínio
        rules = domain_rules_service.get_business_rules()
        print(f"\nTotal de regras no domínio de saúde: {len(rules)}")
        for rule in rules:
            print(f"- {rule['type'].upper()}: {rule['title']}")
        
        # Busca semântica no domínio de saúde
        print_divider()
        print("BUSCA SEMÂNTICA NO DOMÍNIO DE SAÚDE:")
        health_queries = [
            "Quais documentos preciso levar para consulta?",
            "Como funciona o reembolso?",
            "Preparação para exame de sangue"
        ]
        
        for query in health_queries:
            print(f"\nConsulta: '{query}'")
            results = domain_rules_service.query_rules(query, limit=1)
            
            if results:
                print(f"  Resultado encontrado: {results[0]['title']}")
                content_preview = results[0]['content'].replace('\n', ' ')[:100]
                print(f"  {content_preview}...")
            else:
                print("  Nenhum resultado encontrado")
    else:
        print("Falha ao alternar para o domínio de saúde")
    
    print_divider()
    print("Exemplo concluído!")

if __name__ == "__main__":
    main()
