"""
Tasks para o Sales Crew.

Este módulo define as tasks específicas para a Sales Crew, que é responsável
por processar mensagens relacionadas a vendas, produtos, preços e promoções.
"""

import logging
from typing import Dict, Any, List, Optional
from crewai import Task
from crewai.agent import Agent

logger = logging.getLogger(__name__)


def create_product_identification_task(agent: Agent) -> Task:
    """
    Cria uma task para identificação de produtos mencionados na mensagem.
    
    Esta task analisa a mensagem para identificar produtos específicos
    mencionados pelo cliente, ou categorias de produtos de interesse.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de identificação de produtos
    """
    return Task(
        description="""
        Analise a mensagem e identifique produtos ou categorias de produtos mencionados.
        
        Considere:
        1. Produtos mencionados explicitamente pelo nome
        2. Categorias de produtos mencionadas
        3. Descrições indiretas de produtos
        4. Produtos relacionados ao contexto da conversa
        
        Utilize o banco de dados de produtos e a busca vetorial para
        identificar produtos relevantes, mesmo quando não mencionados
        explicitamente pelo nome exato.
        """,
        expected_output="""
        {
            "mentioned_products": [
                {
                    "name": "Nome do produto",
                    "id": "ID do produto",
                    "confidence": 0.95,
                    "explicit_mention": true
                }
            ],
            "mentioned_categories": [
                {
                    "name": "Nome da categoria",
                    "id": "ID da categoria",
                    "confidence": 0.85
                }
            ],
            "related_products": [
                {
                    "name": "Nome do produto relacionado",
                    "id": "ID do produto",
                    "relevance_score": 0.75
                }
            ],
            "product_attributes": [
                "Atributo 1",
                "Atributo 2"
            ]
        }
        """,
        agent=agent,
        name="Identificação de Produtos na Mensagem"
    )


def create_price_inquiry_task(agent: Agent) -> Task:
    """
    Cria uma task para processamento de consultas de preço.
    
    Esta task obtém informações de preço para produtos identificados
    e prepara uma resposta adequada para consultas de preço.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de processamento de consultas de preço
    """
    return Task(
        description="""
        Processe consultas de preço para os produtos identificados.
        
        Para cada produto identificado:
        1. Obtenha o preço atual
        2. Verifique descontos e promoções aplicáveis
        3. Verifique preços especiais para o cliente (se aplicável)
        4. Obtenha informações de parcelamento
        5. Verifique disponibilidade de estoque
        
        Prepare uma resposta clara e informativa sobre os preços,
        incluindo todas as informações relevantes para o cliente.
        """,
        expected_output="""
        {
            "price_information": [
                {
                    "product_id": "ID do produto",
                    "product_name": "Nome do produto",
                    "regular_price": 100.00,
                    "discounted_price": 80.00,
                    "discount_percentage": 20,
                    "promotion_name": "Nome da promoção",
                    "installment_options": [
                        {
                            "installments": 3,
                            "value": 26.67,
                            "total": 80.00,
                            "interest": false
                        }
                    ],
                    "stock_status": "Em estoque",
                    "stock_quantity": 10
                }
            ],
            "pricing_notes": [
                "Nota sobre preço 1",
                "Nota sobre preço 2"
            ],
            "price_validity": "Data de validade dos preços",
            "shipping_estimate": {
                "available": true,
                "min_days": 3,
                "max_days": 5,
                "cost": 15.00
            }
        }
        """,
        agent=agent,
        name="Processamento de Consultas de Preço"
    )


def create_promotion_information_task(agent: Agent) -> Task:
    """
    Cria uma task para informações sobre promoções.
    
    Esta task obtém informações sobre promoções ativas e relevantes
    para os produtos identificados ou para o cliente.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de informações sobre promoções
    """
    return Task(
        description="""
        Obtenha informações sobre promoções ativas e relevantes.
        
        Considere:
        1. Promoções específicas para os produtos identificados
        2. Promoções gerais da loja
        3. Promoções sazonais ou de datas comemorativas
        4. Promoções personalizadas para o perfil do cliente
        5. Cupons de desconto disponíveis
        
        Forneça informações detalhadas sobre cada promoção,
        incluindo condições, prazos e benefícios.
        """,
        expected_output="""
        {
            "product_specific_promotions": [
                {
                    "promotion_id": "ID da promoção",
                    "promotion_name": "Nome da promoção",
                    "product_id": "ID do produto",
                    "discount_type": "Tipo de desconto",
                    "discount_value": 20,
                    "start_date": "Data de início",
                    "end_date": "Data de término",
                    "conditions": "Condições da promoção"
                }
            ],
            "general_promotions": [
                {
                    "promotion_id": "ID da promoção",
                    "promotion_name": "Nome da promoção",
                    "discount_type": "Tipo de desconto",
                    "discount_value": 15,
                    "applicable_categories": ["Categoria 1", "Categoria 2"],
                    "start_date": "Data de início",
                    "end_date": "Data de término",
                    "conditions": "Condições da promoção"
                }
            ],
            "available_coupons": [
                {
                    "coupon_code": "Código do cupom",
                    "discount_type": "Tipo de desconto",
                    "discount_value": 10,
                    "minimum_purchase": 100.00,
                    "expiration_date": "Data de expiração",
                    "usage_limit": 1
                }
            ],
            "promotional_bundles": [
                {
                    "bundle_id": "ID do pacote",
                    "bundle_name": "Nome do pacote",
                    "included_products": ["Produto 1", "Produto 2"],
                    "bundle_price": 150.00,
                    "regular_total_price": 200.00,
                    "savings_percentage": 25
                }
            ]
        }
        """,
        agent=agent,
        name="Informações sobre Promoções"
    )


def create_sales_response_task(agent: Agent) -> Task:
    """
    Cria uma task para geração de resposta de vendas.
    
    Esta task combina as informações obtidas nas tasks anteriores
    para gerar uma resposta completa e persuasiva para o cliente.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de geração de resposta de vendas
    """
    return Task(
        description="""
        Gere uma resposta de vendas persuasiva e informativa para o cliente.
        
        Combine as informações de produtos, preços e promoções para criar
        uma resposta que:
        1. Responda diretamente à consulta do cliente
        2. Destaque os benefícios dos produtos
        3. Comunique claramente preços e condições
        4. Mencione promoções relevantes
        5. Inclua um call-to-action apropriado
        
        A resposta deve ser persuasiva, mas honesta e transparente,
        focando nas necessidades específicas do cliente.
        """,
        expected_output="""
        {
            "response_content": "Conteúdo completo da resposta",
            "highlighted_products": [
                {
                    "product_id": "ID do produto",
                    "product_name": "Nome do produto",
                    "key_benefits": ["Benefício 1", "Benefício 2"]
                }
            ],
            "highlighted_promotions": [
                {
                    "promotion_id": "ID da promoção",
                    "promotion_name": "Nome da promoção"
                }
            ],
            "call_to_action": {
                "type": "Tipo de call-to-action",
                "content": "Conteúdo do call-to-action"
            },
            "suggested_next_steps": [
                "Próximo passo sugerido 1",
                "Próximo passo sugerido 2"
            ],
            "additional_resources": [
                {
                    "type": "Tipo de recurso",
                    "title": "Título do recurso",
                    "url": "URL do recurso"
                }
            ]
        }
        """,
        agent=agent,
        name="Geração de Resposta de Vendas"
    )


def create_purchase_intent_task(agent: Agent) -> Task:
    """
    Cria uma task para identificação de intenção de compra.
    
    Esta task analisa a mensagem para determinar o nível de intenção
    de compra do cliente e sugerir os próximos passos apropriados.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de identificação de intenção de compra
    """
    return Task(
        description="""
        Analise a mensagem e determine o nível de intenção de compra do cliente.
        
        Identifique:
        1. Estágio do funil de vendas (conscientização, consideração, decisão)
        2. Nível de interesse nos produtos mencionados
        3. Urgência da compra
        4. Objeções ou preocupações expressas
        5. Fatores decisivos para a compra
        
        Com base nessa análise, sugira os próximos passos apropriados
        para avançar no processo de vendas.
        """,
        expected_output="""
        {
            "purchase_intent": {
                "stage": "Estágio do funil de vendas",
                "intent_level": "Alto/Médio/Baixo",
                "urgency": "Alta/Média/Baixa",
                "estimated_timeframe": "Estimativa de tempo para decisão"
            },
            "expressed_objections": [
                {
                    "objection": "Objeção expressa",
                    "severity": "Alta/Média/Baixa"
                }
            ],
            "decision_factors": [
                {
                    "factor": "Fator decisivo",
                    "importance": "Alta/Média/Baixa"
                }
            ],
            "suggested_next_steps": [
                {
                    "step": "Próximo passo sugerido",
                    "rationale": "Justificativa para o próximo passo"
                }
            ],
            "recommended_approach": "Abordagem recomendada para avançar na venda"
        }
        """,
        agent=agent,
        name="Identificação de Intenção de Compra"
    )


def create_sales_tasks(sales_agent: Agent, product_specialist_agent: Agent) -> List[Task]:
    """
    Cria todas as tasks necessárias para a Sales Crew.
    
    Args:
        sales_agent: Agente de vendas
        product_specialist_agent: Agente especialista em produtos
        
    Returns:
        List[Task]: Lista de todas as tasks para a Sales Crew
    """
    tasks = [
        create_product_identification_task(product_specialist_agent),
        create_price_inquiry_task(product_specialist_agent),
        create_promotion_information_task(sales_agent),
        create_purchase_intent_task(sales_agent),
        create_sales_response_task(sales_agent)
    ]
    
    return tasks
