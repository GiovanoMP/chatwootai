#!/usr/bin/env python
"""
Simulador de Agente de Atendimento ao Cliente

Este script simula um agente de atendimento ao cliente que responde a perguntas
com base nas informações armazenadas no Qdrant (regras de negócio, documentos de suporte, etc.)
"""

import asyncio
import argparse
from typing import List, Dict, Any, Optional

from odoo_api.services.vector_service import get_vector_service
from qdrant_client.http import models
from openai import AsyncOpenAI
from odoo_api.config.settings import settings

class CustomerServiceAgent:
    """Agente de atendimento ao cliente que responde a perguntas com base nas informações do Qdrant."""

    def __init__(self, account_id: str):
        """
        Inicializa o agente.

        Args:
            account_id: ID da conta do cliente
        """
        self.account_id = account_id
        self.vector_service = None
        self.openai_client = None

    async def initialize(self):
        """Inicializa os serviços necessários."""
        # Inicializar serviço de vetores
        self.vector_service = await get_vector_service()

        # Inicializar cliente OpenAI
        self.openai_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.TIMEOUT_DEFAULT
        )

        print(f"Agente inicializado para a conta {self.account_id}")

    async def search_business_rules(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca regras de negócio relevantes para a consulta.

        Args:
            query: Consulta do usuário
            limit: Número máximo de resultados

        Returns:
            Lista de regras de negócio relevantes
        """
        # Primeiro, vamos buscar TODAS as regras para garantir que temos acesso a todas elas
        print("Buscando todas as regras de negócio...")
        all_rules = self.vector_service.qdrant_client.scroll(
            collection_name="business_rules",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=self.account_id
                        )
                    )
                ]
            ),
            limit=50  # Buscar até 50 regras
        )

        # Lista para armazenar todas as regras
        all_rules_list = []

        # Processar todas as regras encontradas
        if all_rules and len(all_rules) > 0 and all_rules[0]:
            for point in all_rules[0]:
                all_rules_list.append({
                    "text": point.payload.get("text", ""),
                    "score": 0.5,  # Score base
                    "id": point.id,
                    "is_temporary": point.payload.get("is_temporary", False),
                    "priority": point.payload.get("priority", 3)
                })

        # Se não encontramos nenhuma regra, retornar lista vazia
        if not all_rules_list:
            return []

        # Expandir a consulta para melhorar a busca de promoções
        expanded_query = query

        # Adicionar termos relacionados a promoções se a consulta mencionar produtos ou ofertas
        keywords = {
            'shampoo': ['shampoo', 'cabelo', 'xampu', 'lavar cabelo', 'cuidados com cabelo'],
            'frete': ['frete', 'entrega', 'grátis', 'gratis', 'delivery', 'envio'],
            'presente': ['presente', 'embalagem', 'embrulho', 'gift', 'embalagem para presente'],
            'promoção': ['promo', 'desconto', 'oferta', 'especial', 'cupom', 'preço reduzido'],
            'produto': ['produto', 'item', 'mercadoria', 'cosmético', 'beleza']
        }

        # Verificar quais palavras-chave estão na consulta
        matched_categories = []
        for category, terms in keywords.items():
            if any(term in query.lower() for term in terms):
                matched_categories.append(category)

        # Se encontramos categorias, expandir a consulta
        if matched_categories:
            expanded_terms = []
            for category in matched_categories:
                expanded_terms.extend(keywords[category])
            expanded_query = f"{query} {' '.join(expanded_terms)}"
            print(f"Consulta expandida: {expanded_query}")

        # Gerar embedding para a consulta expandida
        query_embedding = await self.vector_service.generate_embedding(expanded_query)

        # Buscar regras de negócio relevantes usando busca semântica
        search_results = self.vector_service.qdrant_client.search(
            collection_name="business_rules",
            query_vector=query_embedding,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=self.account_id
                        )
                    )
                ]
            ),
            limit=limit
        )

        # Extrair informações relevantes da busca semântica
        semantic_results = []
        for hit in search_results:
            semantic_results.append({
                "text": hit.payload.get("text", ""),
                "score": hit.score,
                "id": hit.id,
                "is_temporary": hit.payload.get("is_temporary", False),
                "priority": hit.payload.get("priority", 3)
            })

        # Aumentar o score das regras que foram encontradas na busca semântica
        semantic_ids = {r['id'] for r in semantic_results}
        for rule in all_rules_list:
            if rule['id'] in semantic_ids:
                # Encontrar o score da busca semântica
                for semantic_rule in semantic_results:
                    if semantic_rule['id'] == rule['id']:
                        rule['score'] = semantic_rule['score']
                        break

        # Aumentar o score das regras temporárias se a consulta mencionar promoções
        if any(term in query.lower() for term in keywords['promoção']):
            print("Aumentando score de regras temporárias para promoções...")
            for rule in all_rules_list:
                if rule['is_temporary']:
                    rule['score'] += 0.3  # Aumentar o score das regras temporárias

        # Aumentar o score das regras que contêm palavras-chave específicas da consulta
        for rule in all_rules_list:
            rule_text = rule['text'].lower()
            for category in matched_categories:
                if any(term in rule_text for term in keywords[category]):
                    rule['score'] += 0.2  # Aumentar o score se a regra contiver palavras-chave da consulta

        # Ordenar por prioridade (menor número = maior prioridade) e depois por score (maior = melhor)
        all_rules_list.sort(key=lambda x: (x.get("priority", 3), -x.get("score", 0)))

        # Limitar o número de resultados
        return all_rules_list[:limit]

    async def search_support_documents(self, query: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        Busca documentos de suporte relevantes para a consulta.

        Args:
            query: Consulta do usuário
            limit: Número máximo de resultados

        Returns:
            Lista de documentos de suporte relevantes
        """
        # Gerar embedding para a consulta
        query_embedding = await self.vector_service.generate_embedding(query)

        # Buscar documentos de suporte relevantes
        search_results = self.vector_service.qdrant_client.search(
            collection_name="support_documents",
            query_vector=query_embedding,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=self.account_id
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
                "title": hit.payload.get("title", "")
            })

        return results

    async def search_company_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Busca metadados da empresa.

        Returns:
            Metadados da empresa
        """
        try:
            # Primeiro, tentar buscar usando scroll para garantir que encontramos os metadados
            scroll_results = self.vector_service.qdrant_client.scroll(
                collection_name="company_metadata",
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="account_id",
                            match=models.MatchValue(
                                value=self.account_id
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

            # Se não encontrar, tentar com search como fallback
            search_results = self.vector_service.qdrant_client.search(
                collection_name="company_metadata",
                query_vector=[0.0] * settings.EMBEDDING_DIMENSION,  # Vetor vazio para buscar todos
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="account_id",
                            match=models.MatchValue(
                                value=self.account_id
                            )
                        )
                    ]
                ),
                limit=1
            )

            if search_results:
                return {
                    "text": search_results[0].payload.get("text", ""),
                    "company_name": search_results[0].payload.get("company_name", "Sandra Cosméticos"),
                    "greeting_message": search_results[0].payload.get("greeting_message", "Olá, obrigada por entrar em contato com a Sandra Cosméticos! Como posso ajudar hoje?")
                }
        except Exception as e:
            print(f"Erro ao buscar metadados da empresa: {e}")

        # Valores padrão se não encontrar nada
        return {
            "text": "Comercializamos cosméticos online e presencialmente, nossos canais de venda são Instagram, Facebook, Mercado Livre e WhatsApp.",
            "company_name": "Sandra Cosméticos",
            "greeting_message": "Olá, obrigada por entrar em contato com a Sandra Cosméticos! Como posso ajudar hoje?"
        }

    async def generate_response(self, query: str) -> str:
        """
        Gera uma resposta para a consulta do usuário.

        Args:
            query: Consulta do usuário

        Returns:
            Resposta gerada
        """
        # Buscar informações relevantes
        business_rules = await self.search_business_rules(query)
        support_documents = await self.search_support_documents(query)
        company_metadata = await self.search_company_metadata()

        # Construir contexto para o modelo
        context = """
Você é um assistente virtual de atendimento ao cliente da Sandra Cosméticos, altamente eficiente e amigável.

INSTRUÇÕES IMPORTANTES:
1. SEMPRE CONSULTE AS REGRAS DE NEGÓCIO FORNECIDAS ABAIXO ANTES DE RESPONDER. Estas regras são a fonte de verdade.
2. Quando o cliente perguntar sobre promoções, descontos, frete grátis ou ofertas especiais, SEMPRE consulte as regras de negócio fornecidas e cite-as diretamente.
3. Priorize as regras marcadas como [PROMOÇÃO TEMPORÁRIA] - estas são as mais importantes e atuais.
4. Seja preciso e direto nas suas respostas, mas mantenha um tom amigável e prestativo.
5. Se não encontrar informações específicas nas regras fornecidas, seja honesto e diga que não tem essa informação no momento.
6. SEMPRE mencione as datas de validade das promoções temporárias quando disponíveis.
7. NÃO INVENTE informações que não estão nas regras fornecidas.
"""

        if company_metadata:
            company_info = f"""
INFORMAÇÕES DA EMPRESA:
Nome: {company_metadata.get('company_name', 'Sandra Cosméticos')}
{company_metadata.get('text', 'Comercializamos cosméticos online e presencialmente, nossos canais de venda são Instagram, Facebook, Mercado Livre e WhatsApp.')}

Saudação oficial: {company_metadata.get('greeting_message', 'Olá, obrigada por entrar em contato com a Sandra Cosméticos! Como posso ajudar hoje?')}
"""
            context += company_info

        context += "\n=== REGRAS DE NEGÓCIO E PROMOÇÕES ATUAIS ===\n"
        if business_rules:
            for i, rule in enumerate(business_rules, 1):
                # Destacar se é uma regra temporária (promoção)
                rule_type = "[PROMOÇÃO TEMPORÁRIA]" if rule.get('is_temporary', False) else "[REGRA PERMANENTE]"
                context += f"REGRA {i}: {rule_type}\n{rule.get('text', '')}\n\n"
        else:
            context += "ATENÇÃO: Não foram encontradas regras de negócio ou promoções específicas para esta consulta.\n"

        context += "\n=== DOCUMENTOS DE SUPORTE RELEVANTES ===\n"
        if support_documents:
            for i, doc in enumerate(support_documents, 1):
                context += f"DOCUMENTO {i}: {doc.get('title', 'Documento')}\n{doc.get('text', '')}\n\n"
        else:
            context += "Nenhum documento de suporte específico encontrado para esta consulta.\n"

        context += "\nLEMBRE-SE: Responda com base APENAS nas informações fornecidas acima. Se a informação não estiver nas regras, informe que não tem essa informação no momento."

        # Gerar resposta
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo padrão
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content

async def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Simulador de Agente de Atendimento ao Cliente")
    parser.add_argument("--account_id", type=str, default="account_1", help="ID da conta do cliente")
    args = parser.parse_args()

    # Inicializar agente
    agent = CustomerServiceAgent(args.account_id)
    await agent.initialize()

    print(f"Bem-vindo ao simulador de agente de atendimento ao cliente para {args.account_id}")
    print("Digite 'sair' para encerrar")

    while True:
        # Obter consulta do usuário
        query = input("\nPergunta do cliente: ")

        if query.lower() in ["sair", "exit", "quit"]:
            break

        # Gerar resposta
        print("\nProcessando...")
        response = await agent.generate_response(query)

        # Exibir resposta
        print(f"\nResposta do agente:\n{response}")

    print("Obrigado por usar o simulador de agente de atendimento ao cliente!")

if __name__ == "__main__":
    asyncio.run(main())
