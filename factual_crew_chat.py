#!/usr/bin/env python
"""
Chat factual com agentes do CrewAI que acessam o Qdrant.

Este script implementa técnicas para evitar alucinações nos agentes do CrewAI,
garantindo que as respostas sejam baseadas apenas nos dados do Qdrant.
"""

import os
import asyncio
import argparse
import json
from typing import List, Dict, Any
from crewai import Agent, Task, Crew
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI

# Importar o serviço de vetores existente
from odoo_api.services.vector_service import get_vector_service


async def search_business_rules(query: str, account_id: str = "account_1", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Busca regras de negócio no Qdrant.
    
    Args:
        query: A consulta do usuário
        account_id: ID da conta do cliente
        limit: Número máximo de resultados
        
    Returns:
        Lista de regras de negócio
    """
    print(f"Buscando regras de negócio para a consulta: '{query}'")
    
    # Inicializar o serviço de vetores
    vector_service = await get_vector_service()
    
    # Gerar embedding para a consulta
    query_embedding = await vector_service.generate_embedding(query)
    
    # Buscar regras de negócio relevantes
    search_results = vector_service.qdrant_client.search(
        collection_name="business_rules",
        query_vector=query_embedding,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="account_id",
                    match=models.MatchValue(
                        value=account_id
                    )
                )
            ]
        ),
        limit=limit
    )
    
    # Extrair informações relevantes
    results = []
    for hit in search_results:
        results.append({
            "text": hit.payload.get("text", ""),
            "score": hit.score,
            "id": hit.id,
            "is_temporary": hit.payload.get("is_temporary", False),
            "priority": hit.payload.get("priority", 3)
        })
    
    # Ordenar por prioridade (menor número = maior prioridade) e depois por score (maior = melhor)
    results.sort(key=lambda x: (x.get("priority", 3), -x.get("score", 0)))
    
    return results


async def get_company_metadata(account_id: str = "account_1") -> Dict[str, Any]:
    """
    Recupera os metadados da empresa.
    
    Args:
        account_id: ID da conta do cliente
        
    Returns:
        Metadados da empresa
    """
    print(f"Recuperando metadados da empresa para a conta: '{account_id}'")
    
    # Inicializar o serviço de vetores
    vector_service = await get_vector_service()
    
    try:
        # Buscar metadados da empresa usando scroll
        scroll_results = vector_service.qdrant_client.scroll(
            collection_name="company_metadata",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=account_id
                        )
                    )
                ]
            ),
            limit=1
        )
        
        if scroll_results and len(scroll_results) > 0 and scroll_results[0]:
            point = scroll_results[0][0]  # Primeiro ponto do primeiro batch
            return {
                "text": point.payload.get("text", ""),
                "company_name": point.payload.get("company_name", "Sandra Cosméticos"),
                "greeting_message": point.payload.get("greeting_message", "Olá, obrigada por entrar em contato com a Sandra Cosméticos! Como posso ajudar hoje?")
            }
    except Exception as e:
        print(f"Erro ao buscar metadados da empresa: {e}")
    
    # Valores padrão se não encontrar nada
    return {
        "text": "Comercializamos cosméticos online e presencialmente, nossos canais de venda são Instagram, Facebook, Mercado Livre e WhatsApp.",
        "company_name": "Sandra Cosméticos",
        "greeting_message": "Olá, obrigada por entrar em contato com a Sandra Cosméticos! Como posso ajudar hoje?"
    }


def create_crew_with_qdrant_data(query: str, business_rules: List[Dict[str, Any]], company_metadata: Dict[str, Any]) -> Crew:
    """
    Cria uma crew com dados do Qdrant.
    
    Args:
        query: A consulta do usuário
        business_rules: Lista de regras de negócio
        company_metadata: Metadados da empresa
        
    Returns:
        Crew criada
    """
    # Formatar regras de negócio para o prompt
    rules_text = ""
    for i, rule in enumerate(business_rules, 1):
        rule_type = "[PROMOÇÃO TEMPORÁRIA]" if rule.get("is_temporary", False) else "[REGRA PERMANENTE]"
        rule_id = rule.get("id", f"rule_{i}")
        rules_text += f"REGRA #{rule_id}: {rule_type} {rule.get('text', '')}\n\n"
    
    # Formatar metadados da empresa para o prompt
    company_text = f"""
    Nome da empresa: {company_metadata.get('company_name', 'Sandra Cosméticos')}
    Saudação oficial: {company_metadata.get('greeting_message', 'Olá, como posso ajudar?')}
    Descrição: {company_metadata.get('text', '')}
    """
    
    # Criar agente de análise
    analysis_agent = Agent(
        role="Analista de Regras de Negócio",
        goal="Analisar regras de negócio para fornecer informações precisas e factuais",
        backstory="""
        Você é um analista especializado em interpretar regras de negócio e políticas da empresa.
        Sua habilidade está em entender as nuances das regras e extrair as informações mais 
        relevantes para o contexto atual. Você NUNCA inventa informações e sempre se baseia
        apenas nos dados fornecidos.
        """,
        verbose=True,
        temperature=0.1  # Temperatura baixa para reduzir criatividade
    )
    
    # Criar agente de atendimento ao cliente
    customer_service_agent = Agent(
        role="Atendente de Suporte ao Cliente",
        goal="Fornecer respostas precisas, amigáveis e ESTRITAMENTE baseadas nas regras de negócio",
        backstory="""
        Você é um atendente de suporte ao cliente da Sandra Cosméticos.
        Sua missão é fornecer respostas precisas, amigáveis e úteis aos clientes,
        com base APENAS nas regras de negócio e informações da empresa fornecidas.
        Você NUNCA inventa informações e sempre cita a fonte exata das informações.
        Se não tiver informações suficientes, você admite que não sabe a resposta.
        """,
        verbose=True,
        temperature=0.1  # Temperatura baixa para reduzir criatividade
    )
    
    # Criar tarefa de análise
    analysis_task = Task(
        description=f"""
        Analise as seguintes regras de negócio e identifique as mais relevantes para a consulta: "{query}"
        
        REGRAS DE NEGÓCIO:
        {rules_text}
        
        INFORMAÇÕES DA EMPRESA:
        {company_text}
        
        INSTRUÇÕES IMPORTANTES:
        1. Priorize regras temporárias (promoções) quando a consulta for sobre promoções.
        2. Cite APENAS informações que estão explicitamente nas regras fornecidas.
        3. NÃO INVENTE informações que não estão nas regras.
        4. Se não houver informações suficientes, indique claramente que não há dados disponíveis.
        5. Para cada informação relevante, cite o ID da regra (ex: REGRA #123).
        
        Seu resultado deve seguir este formato JSON:
        {{
            "regras_relevantes": [
                {{
                    "id": "ID da regra",
                    "texto": "Texto da regra",
                    "relevancia": "Explicação da relevância para a consulta",
                    "confianca": 0.95  // Valor entre 0 e 1 indicando sua confiança na relevância
                }}
            ],
            "tem_informacao_suficiente": true/false,  // Indica se há informação suficiente para responder
            "recomendacao": "Sua recomendação sobre como responder à consulta"
        }}
        """,
        agent=analysis_agent,
        expected_output="Uma análise detalhada das regras de negócio mais relevantes para a consulta em formato JSON."
    )
    
    # Criar tarefa de atendimento ao cliente
    customer_service_task = Task(
        description=f"""
        Gere uma resposta amigável e precisa para o cliente com base na análise das regras de negócio.
        
        CONSULTA DO CLIENTE: "{query}"
        
        INFORMAÇÕES DA EMPRESA:
        {company_text}
        
        INSTRUÇÕES IMPORTANTES:
        1. Use a saudação oficial da empresa.
        2. Responda à consulta do cliente com base APENAS nas regras de negócio analisadas.
        3. Mencione datas de validade de promoções quando disponíveis.
        4. NÃO INVENTE informações que não estão na análise.
        5. Se a análise indicar que não há informação suficiente, seja honesto e diga que não tem essa informação.
        6. Cite as regras específicas que você está usando (ex: "De acordo com nossa regra #123...").
        7. Mantenha um tom amigável e prestativo, mas NUNCA sacrifique a precisão pela amabilidade.
        
        Sua resposta deve seguir este formato:
        
        SAUDAÇÃO: [Saudação oficial da empresa]
        
        RESPOSTA: [Sua resposta baseada apenas nas regras analisadas]
        
        FONTES: [Lista de IDs das regras utilizadas]
        
        CONFIANÇA: [Alta/Média/Baixa - Indique sua confiança na resposta]
        """,
        agent=customer_service_agent,
        expected_output="Uma resposta completa e bem formatada para o cliente, citando apenas informações das regras."
    )
    
    # Criar crew
    crew = Crew(
        agents=[analysis_agent, customer_service_agent],
        tasks=[analysis_task, customer_service_task],
        verbose=True
    )
    
    return crew


async def process_query(query: str, account_id: str = "account_1") -> Dict[str, Any]:
    """
    Processa uma consulta do usuário.
    
    Args:
        query: A consulta do usuário
        account_id: ID da conta do cliente
        
    Returns:
        Resultado do processamento
    """
    # Buscar informações relevantes
    business_rules = await search_business_rules(query, account_id)
    company_metadata = await get_company_metadata(account_id)
    
    print(f"Encontradas {len(business_rules)} regras de negócio relevantes")
    
    # Criar crew
    crew = create_crew_with_qdrant_data(query, business_rules, company_metadata)
    
    # Executar crew
    result = crew.kickoff()
    
    # Extrair partes da resposta formatada
    response_parts = {}
    try:
        lines = result.strip().split('\n')
        for line in lines:
            if line.startswith('SAUDAÇÃO:'):
                response_parts['saudacao'] = line.replace('SAUDAÇÃO:', '').strip()
            elif line.startswith('RESPOSTA:'):
                response_parts['resposta'] = line.replace('RESPOSTA:', '').strip()
            elif line.startswith('FONTES:'):
                response_parts['fontes'] = line.replace('FONTES:', '').strip()
            elif line.startswith('CONFIANÇA:'):
                response_parts['confianca'] = line.replace('CONFIANÇA:', '').strip()
    except Exception:
        # Se não conseguir extrair as partes, use a resposta completa
        response_parts = {'resposta_completa': result}
    
    return {
        "query": query,
        "response": result,
        "response_parts": response_parts,
        "account_id": account_id,
        "num_rules_found": len(business_rules)
    }


def parse_args():
    """
    Analisa os argumentos da linha de comando.
    
    Returns:
        Argumentos analisados
    """
    parser = argparse.ArgumentParser(description="Chat factual com agentes do CrewAI")
    parser.add_argument("--account_id", type=str, default="account_1", help="ID da conta do cliente")
    return parser.parse_args()


def main():
    """Função principal."""
    # Analisar argumentos
    args = parse_args()
    
    # Exibir mensagem de boas-vindas
    print(f"Bem-vindo ao chat factual com agentes do CrewAI para a conta {args.account_id}")
    print("Este chat foi projetado para fornecer APENAS informações factuais baseadas nos dados do Qdrant.")
    print("Digite 'sair' para encerrar o chat")
    print()
    
    # Exibir saudação inicial
    company_metadata = asyncio.run(get_company_metadata(args.account_id))
    print(f"\033[1;36m{company_metadata.get('greeting_message')}\033[0m")
    
    # Loop de chat
    while True:
        # Obter consulta do usuário
        query = input("\n\033[1;32mVocê:\033[0m ")
        
        if query.lower() in ["sair", "exit", "quit"]:
            break
        
        # Processar consulta
        print("\n\033[1;33mProcessando...\033[0m")
        result = asyncio.run(process_query(query, args.account_id))
        
        # Exibir resposta
        if 'response_parts' in result and 'resposta' in result['response_parts']:
            # Exibir resposta formatada
            parts = result['response_parts']
            print(f"\n\033[1;36mAtendente:\033[0m {parts.get('resposta', '')}")
            
            # Exibir fontes se disponíveis
            if 'fontes' in parts:
                print(f"\n\033[0;90mFontes: {parts.get('fontes', '')}\033[0m")
            
            # Exibir confiança se disponível
            if 'confianca' in parts:
                confianca = parts.get('confianca', '').lower()
                if 'alta' in confianca:
                    print(f"\n\033[0;32mConfiança: {confianca}\033[0m")
                elif 'média' in confianca:
                    print(f"\n\033[0;33mConfiança: {confianca}\033[0m")
                else:
                    print(f"\n\033[0;31mConfiança: {confianca}\033[0m")
        else:
            # Exibir resposta completa
            print(f"\n\033[1;36mAtendente:\033[0m {result['response']}")
    
    print("\nObrigado por usar o chat factual com agentes do CrewAI!")


if __name__ == "__main__":
    main()
