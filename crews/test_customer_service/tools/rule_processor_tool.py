"""
Ferramenta de processamento de regras para o CrewAI.

Esta ferramenta permite que os agentes processem e priorizem regras de negócio
com base na consulta do usuário.
"""

from typing import Dict, List, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class RuleProcessorInput(BaseModel):
    """Modelo de entrada para a ferramenta de processamento de regras."""

    rules: List[Dict[str, Any]] = Field(description="Lista de regras de negócio")
    query: str = Field(description="A consulta do usuário")
    max_rules: int = Field(default=5, description="Número máximo de regras a retornar")


class RuleProcessorTool(BaseTool):
    """Ferramenta para processar e priorizar regras de negócio."""

    name: str = "rule_processor"
    description: str = """
    Processa e prioriza regras de negócio com base na consulta do usuário.
    Use esta ferramenta para filtrar e ordenar regras de negócio por relevância.

    Parâmetros:
    - rules: Lista de regras de negócio
    - query: A consulta do usuário
    - max_rules: Número máximo de regras a retornar (padrão: 5)
    """

    def _run(self, rules: List[Dict[str, Any]], query: str, max_rules: int = 5) -> List[Dict[str, Any]]:
        """
        Processa e prioriza regras de negócio.

        Args:
            rules: Lista de regras de negócio
            query: A consulta do usuário
            max_rules: Número máximo de regras a retornar

        Returns:
            Lista de regras priorizadas
        """
        if not rules:
            return []

        # Palavras-chave para categorização
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

        # Aumentar o score das regras que contêm palavras-chave da consulta
        for rule in rules:
            rule_text = rule.get('text', '').lower()

            # Inicializar o score de relevância
            relevance_score = rule.get('score', 0.5)

            # Aumentar o score para regras temporárias se a consulta mencionar promoções
            if any(term in query.lower() for term in keywords['promoção']) and rule.get('is_temporary', False):
                relevance_score += 0.3

            # Aumentar o score para regras que contêm palavras-chave da consulta
            for category in matched_categories:
                if any(term in rule_text for term in keywords[category]):
                    relevance_score += 0.2

            # Atualizar o score
            rule['relevance_score'] = relevance_score

        # Ordenar por prioridade (menor número = maior prioridade) e depois por score de relevância (maior = melhor)
        sorted_rules = sorted(rules, key=lambda x: (x.get('priority', 3), -x.get('relevance_score', 0)))

        # Limitar o número de regras
        return sorted_rules[:max_rules]
