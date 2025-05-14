"""
Serviço para enriquecimento de informações usando IA.
"""

from typing import Dict, Any, List
import logging
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.exceptions import EmbeddingError
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)

class EnrichmentService:
    """Serviço para enriquecimento de informações usando IA."""

    def __init__(self, redis_service: RedisService):
        """
        Inicializa o serviço de enriquecimento.

        Args:
            redis_service: Serviço Redis para controle de rate limiting
        """
        self.openai_client = None
        self.redis = redis_service

    async def connect(self):
        """Conecta ao serviço OpenAI."""
        if self.openai_client is not None:
            return

        try:
            self.openai_client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.TIMEOUT_DEFAULT
            )
            logger.info("Conectado ao serviço OpenAI para enriquecimento")

        except Exception as e:
            logger.error(f"Falha ao conectar ao serviço OpenAI para enriquecimento: {e}")
            raise EmbeddingError(f"Falha ao conectar ao serviço OpenAI para enriquecimento: {e}")

    async def enrich_business_rule(self, rule_data: Dict[str, Any], account_id: str) -> Dict[str, Any]:
        """
        Enriquece uma regra de negócio com informações adicionais.
        Limita o uso de tokens para evitar consumo excessivo.

        Args:
            rule_data: Dados da regra
            account_id: ID da conta

        Returns:
            Dados da regra enriquecidos
        """
        # Extrair dados da regra
        name = rule_data.get("name", "")
        description = rule_data.get("description", "")
        rule_type = rule_data.get("type", "")
        rule_id = rule_data.get("id", 0)

        # Verificar se o enriquecimento é necessário
        if len(description) > settings.MIN_DESCRIPTION_LENGTH:
            # Descrição já é suficientemente detalhada
            return rule_data

        # Verificar limite de taxa para enriquecimento
        rate_key = f"rate:enrichment:{account_id}"
        if not await self.redis.rate_limit_check(rate_key, 10, 3600):  # 10 enriquecimentos por hora
            logger.warning(f"Limite de taxa excedido para enriquecimento da conta {account_id}")
            return rule_data

        # Verificar cache
        cache_key = f"enrichment:rule:{account_id}:{rule_id}"
        cached_data = await self.redis.get_json(cache_key)
        if cached_data:
            logger.info(f"Usando dados enriquecidos em cache para regra {rule_id}")
            return cached_data

        try:
            await self.connect()

            # Preparar prompt para o modelo
            prompt = f"""
            Enriqueça a seguinte regra de negócio com detalhes adicionais:

            Nome: {name}
            Tipo: {rule_type}
            Descrição atual: {description}

            Forneça uma descrição mais detalhada em até 3 frases, mantendo o contexto original.
            """

            # Limitar tokens na chamada
            response = await self.openai_client.chat.completions.create(
                model=settings.ENRICHMENT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.MAX_ENRICHMENT_TOKENS,
                temperature=0.7
            )

            # Extrair resposta
            enriched_description = response.choices[0].message.content.strip()

            # Atualizar dados da regra
            rule_data["description"] = enriched_description
            rule_data["enriched"] = True

            # Armazenar em cache
            await self.redis.set_json(
                key=cache_key,
                value=rule_data,
                expiry=86400  # 24 horas
            )

            return rule_data

        except Exception as e:
            logger.error(f"Erro ao enriquecer regra: {str(e)}")
            # Em caso de erro, retornar dados originais
            return rule_data

    async def enrich_document(self, document_data: Dict[str, Any], account_id: str) -> Dict[str, Any]:
        """
        Enriquece um documento com informações adicionais.
        Limita o uso de tokens para evitar consumo excessivo.

        Args:
            document_data: Dados do documento
            account_id: ID da conta

        Returns:
            Dados do documento enriquecidos
        """
        # Extrair dados do documento
        name = document_data.get("name", "")
        content = document_data.get("content", "")
        document_type = document_data.get("document_type", "")

        # Verificar se o enriquecimento é necessário
        if len(content) > 1000:
            # Conteúdo já é suficientemente detalhado
            return document_data

        # Verificar limite de taxa para enriquecimento
        rate_key = f"rate:enrichment_doc:{account_id}"
        if not await self.redis.rate_limit_check(rate_key, 20, 3600):  # 20 enriquecimentos por hora
            logger.warning(f"Limite de taxa excedido para enriquecimento de documentos da conta {account_id}")
            return document_data

        # Verificar cache
        cache_key = f"enrichment:doc:{account_id}:{hash(content)}"
        cached_data = await self.redis.get_json(cache_key)
        if cached_data:
            logger.info(f"Usando dados enriquecidos em cache para documento {name}")
            return cached_data

        try:
            await self.connect()

            # Preparar prompt para o modelo
            prompt = f"""
            Enriqueça o seguinte documento com detalhes adicionais:

            Nome: {name}
            Tipo: {document_type}
            Conteúdo original: {content}

            Forneça uma versão enriquecida do conteúdo, mantendo o contexto original mas adicionando:
            1. Termos relacionados que possam ajudar na recuperação
            2. Explicações adicionais para conceitos importantes
            3. Exemplos relevantes (se aplicável)

            Mantenha o texto conciso e focado no assunto principal.
            """

            # Limitar tokens na chamada
            response = await self.openai_client.chat.completions.create(
                model=settings.ENRICHMENT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.MAX_ENRICHMENT_TOKENS * 2,  # Dobro para documentos
                temperature=0.7
            )

            # Extrair resposta
            enriched_content = response.choices[0].message.content.strip()

            # Atualizar dados do documento
            result = document_data.copy()
            result["enriched_content"] = enriched_content
            result["enriched"] = True

            # Armazenar em cache
            await self.redis.set_json(
                key=cache_key,
                value=result,
                expiry=86400  # 24 horas
            )

            return result

        except Exception as e:
            logger.error(f"Erro ao enriquecer documento: {str(e)}")
            # Em caso de erro, retornar dados originais
            return document_data

    async def batch_enrich_rules(self, rules: List[Dict[str, Any]], account_id: str, max_batch: int = 5) -> List[Dict[str, Any]]:
        """
        Enriquece um lote de regras, limitando o número máximo de enriquecimentos
        para controlar o consumo de tokens.

        Args:
            rules: Lista de regras
            account_id: ID da conta
            max_batch: Número máximo de regras a enriquecer

        Returns:
            Lista de regras enriquecidas
        """
        # Verificar limite de taxa para enriquecimento em lote
        rate_key = f"rate:enrichment_batch:{account_id}"
        if not await self.redis.rate_limit_check(rate_key, 2, 3600):  # 2 lotes por hora
            logger.warning(f"Limite de taxa excedido para enriquecimento em lote da conta {account_id}")
            return rules

        # Filtrar regras que precisam de enriquecimento
        candidates = [
            rule for rule in rules
            if len(rule.get("description", "")) <= settings.MIN_DESCRIPTION_LENGTH
        ]

        # Limitar o número de enriquecimentos
        to_enrich = candidates[:min(len(candidates), max_batch)]

        # Enriquecer regras selecionadas
        enriched_rules = []
        for rule in rules:
            if rule in to_enrich:
                enriched_rule = await self.enrich_business_rule(rule, account_id)
                enriched_rules.append(enriched_rule)
            else:
                enriched_rules.append(rule)

        return enriched_rules
