"""
Serviço para geração de embeddings.
"""

import logging
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Serviço para geração de embeddings."""
    
    def __init__(self):
        """Inicializa o serviço de embeddings."""
        self.openai_client = None
    
    async def connect(self):
        """Conecta ao serviço OpenAI."""
        if self.openai_client is not None:
            return
        
        try:
            self.openai_client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.TIMEOUT_DEFAULT
            )
            logger.info("Conectado ao serviço OpenAI")
            
        except Exception as e:
            logger.error(f"Falha ao conectar ao serviço OpenAI: {e}")
            raise EmbeddingError(f"Falha ao conectar ao serviço OpenAI: {e}")
    
    @retry(
        stop=stop_after_attempt(settings.RETRY_MAX_ATTEMPTS),
        wait=wait_exponential(
            multiplier=1,
            min=settings.RETRY_MIN_SECONDS,
            max=settings.RETRY_MAX_SECONDS,
        ),
    )
    async def generate_embedding(self, text: str, max_tokens: Optional[int] = None) -> List[float]:
        """
        Gera um embedding para um texto.
        
        Args:
            text: Texto para gerar o embedding
            max_tokens: Limite máximo de tokens (opcional)
            
        Returns:
            Embedding do texto
        """
        if not text:
            # Retornar um vetor de zeros se o texto estiver vazio
            return [0.0] * settings.EMBEDDING_DIMENSION
        
        await self.connect()
        
        # Limitar o tamanho do texto se necessário
        if max_tokens and len(text.split()) > max_tokens:
            # Truncar o texto para o número máximo de tokens
            # Esta é uma aproximação simples, em produção seria melhor usar um tokenizador real
            text = " ".join(text.split()[:max_tokens])
            logger.warning(f"Texto truncado para {max_tokens} tokens")
        
        try:
            # Gerar embedding usando o OpenAI
            response = await self.openai_client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text
            )
            
            # Extrair o embedding
            embedding = response.data[0].embedding
            
            return embedding
            
        except Exception as e:
            if hasattr(e, "status_code") and e.status_code:
                logger.error(f"Erro HTTP ao gerar embedding: {e}")
                raise EmbeddingError(f"Erro HTTP ao gerar embedding: {e}")
            else:
                logger.error(f"Falha ao gerar embedding: {e}")
                raise EmbeddingError(f"Falha ao gerar embedding: {e}")
    
    async def batch_generate_embeddings(self, texts: List[str], max_tokens: Optional[int] = None) -> List[List[float]]:
        """
        Gera embeddings para múltiplos textos.
        
        Args:
            texts: Lista de textos para gerar embeddings
            max_tokens: Limite máximo de tokens por texto (opcional)
            
        Returns:
            Lista de embeddings
        """
        if not texts:
            return []
        
        await self.connect()
        
        # Limitar o tamanho dos textos se necessário
        if max_tokens:
            limited_texts = []
            for text in texts:
                if len(text.split()) > max_tokens:
                    # Truncar o texto para o número máximo de tokens
                    limited_text = " ".join(text.split()[:max_tokens])
                    limited_texts.append(limited_text)
                    logger.warning(f"Texto truncado para {max_tokens} tokens")
                else:
                    limited_texts.append(text)
            texts = limited_texts
        
        try:
            # Gerar embeddings usando o OpenAI
            response = await self.openai_client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=texts
            )
            
            # Extrair os embeddings
            embeddings = [item.embedding for item in response.data]
            
            return embeddings
            
        except Exception as e:
            if hasattr(e, "status_code") and e.status_code:
                logger.error(f"Erro HTTP ao gerar embeddings em lote: {e}")
                raise EmbeddingError(f"Erro HTTP ao gerar embeddings em lote: {e}")
            else:
                logger.error(f"Falha ao gerar embeddings em lote: {e}")
                raise EmbeddingError(f"Falha ao gerar embeddings em lote: {e}")
