"""
Serviço de Embeddings usando a API da OpenAI.
Este serviço é responsável por gerar embeddings para textos usando a API da OpenAI.
Inclui estratégias de otimização de custos como cache Redis e processamento em lote.
"""
from openai import OpenAI
import os
import hashlib
import json
from typing import List, Dict, Any, Optional, Union
import logging
import redis

class EmbeddingService:
    """
    Serviço para geração de embeddings usando a API da OpenAI.
    
    Este serviço encapsula a lógica de geração de embeddings para textos,
    permitindo que outros componentes do sistema possam facilmente obter
    representações vetoriais de textos para busca semântica.
    
    Inclui estratégias de otimização de custos:
    1. Cache de embeddings no Redis para evitar chamadas repetidas à API
    2. Processamento em lote para reduzir o número de chamadas à API
    3. Compressão de texto para reduzir o número de tokens
    4. Monitoramento de uso e custos
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, use_cache: bool = True):
        """
        Inicializa o serviço de embeddings.
        
        Args:
            api_key: Chave de API da OpenAI. Se não fornecida, será buscada na variável de ambiente OPENAI_API_KEY.
            model: Modelo de embeddings a ser usado. Se não fornecido, será usado o padrão definido na variável de ambiente.
            use_cache: Se True, utiliza cache Redis para armazenar embeddings e economizar chamadas à API.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key da OpenAI não fornecida e não encontrada nas variáveis de ambiente")
            
        self.model = model or os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
        self.client = OpenAI(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)
        
        # Configurar cache Redis se disponível
        self.use_cache = use_cache
        self.redis_client = None
        self.cache_ttl = 60 * 60 * 24 * 7  # 7 dias em segundos
        
        if self.use_cache:
            redis_url = os.environ.get("REDIS_URL")
            if redis_url:
                try:
                    self.redis_client = redis.from_url(redis_url)
                    self.logger.info("Cache Redis configurado para o serviço de embeddings")
                except Exception as e:
                    self.logger.warning(f"Não foi possível conectar ao Redis: {e}")
                    self.use_cache = False
            else:
                self.logger.warning("REDIS_URL não encontrada. Cache de embeddings desativado.")
                self.use_cache = False
        
        # Contadores para monitoramento de uso e custos
        self.token_usage = 0
        self.api_calls = 0
        
        self.logger.info(f"Serviço de Embeddings inicializado com o modelo: {self.model}")
        
    def _get_cache_key(self, text: str) -> str:
        """
        Gera uma chave de cache para o texto e modelo fornecidos.
        
        Args:
            text: Texto para o qual gerar a chave de cache
            
        Returns:
            Chave de cache como string
        """
        # Criar um hash do texto para usar como chave de cache
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"embedding:{self.model}:{text_hash}"
    
    def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """
        Tenta obter um embedding do cache.
        
        Args:
            text: Texto para o qual buscar o embedding no cache
            
        Returns:
            Embedding como lista de floats, ou None se não estiver no cache
        """
        if not self.use_cache or not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(text)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                self.logger.debug(f"Embedding encontrado no cache para: {text[:30]}...")
                return json.loads(cached_data)
        except Exception as e:
            self.logger.warning(f"Erro ao acessar cache: {e}")
        
        return None
    
    def _save_to_cache(self, text: str, embedding: List[float]) -> bool:
        """
        Salva um embedding no cache.
        
        Args:
            text: Texto original
            embedding: Embedding a ser salvo
            
        Returns:
            True se o embedding foi salvo com sucesso, False caso contrário
        """
        if not self.use_cache or not self.redis_client:
            return False
        
        try:
            cache_key = self._get_cache_key(text)
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(embedding)
            )
            return True
        except Exception as e:
            self.logger.warning(f"Erro ao salvar no cache: {e}")
            return False
    
    def _preprocess_text(self, text: str) -> str:
        """
        Pré-processa o texto para reduzir o número de tokens.
        
        Args:
            text: Texto a ser pré-processado
            
        Returns:
            Texto pré-processado
        """
        if not text or not text.strip():
            return ""
        
        # Remover espaços extras
        text = " ".join(text.strip().split())
        
        # Limitar o tamanho do texto (8000 caracteres é um bom limite para a maioria dos casos)
        if len(text) > 8000:
            text = text[:8000]
        
        return text
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Gera embedding para um único texto usando a API da OpenAI.
        
        Esta implementação inclui otimizações de custo:
        1. Verifica se o embedding já está no cache
        2. Pré-processa o texto para reduzir tokens
        3. Monitora o uso e custos
        
        Args:
            text: Texto para o qual gerar o embedding.
            
        Returns:
            Lista de floats representando o embedding do texto.
            
        Raises:
            Exception: Se ocorrer um erro ao gerar o embedding.
        """
        # Pré-processar o texto
        processed_text = self._preprocess_text(text)
        
        if not processed_text:
            self.logger.warning("Tentativa de gerar embedding para texto vazio")
            return []
        
        # Verificar se o embedding está no cache
        cached_embedding = self._get_from_cache(processed_text)
        if cached_embedding is not None:
            return cached_embedding
        
        # Se não estiver no cache, gerar o embedding
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=processed_text
            )
            
            embedding = response.data[0].embedding
            
            # Atualizar contadores de uso
            self.token_usage += response.usage.total_tokens
            self.api_calls += 1
            
            # Salvar no cache
            self._save_to_cache(processed_text, embedding)
            
            return embedding
        except Exception as e:
            self.logger.error(f"Erro ao gerar embedding: {str(e)}")
            raise
    
    def get_batch_embeddings(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """
        Gera embeddings para múltiplos textos em uma única chamada de API.
        
        Esta função é mais eficiente e econômica para processar múltiplos textos,
        pois faz apenas uma chamada à API. Inclui otimizações:
        1. Verifica quais textos já têm embeddings no cache
        2. Processa apenas os textos não encontrados no cache
        3. Divide em lotes menores para evitar limites da API
        
        Args:
            texts: Lista de textos para os quais gerar embeddings.
            batch_size: Tamanho máximo de cada lote para enviar à API
            
        Returns:
            Lista de embeddings, onde cada embedding é uma lista de floats.
            
        Raises:
            Exception: Se ocorrer um erro ao gerar os embeddings.
        """
        if not texts:
            self.logger.warning("Tentativa de gerar embeddings para lista vazia de textos")
            return []
        
        # Pré-processar todos os textos
        processed_texts = [self._preprocess_text(text) for text in texts]
        
        # Filtrar textos vazios
        valid_indices = [i for i, text in enumerate(processed_texts) if text]
        if not valid_indices:
            self.logger.warning("Todos os textos na lista estão vazios após pré-processamento")
            return [[] for _ in texts]  # Retornar lista vazia para cada texto
        
        # Inicializar lista de resultados com o mesmo tamanho da entrada
        results = [[] for _ in texts]
        
        # Verificar quais textos já estão no cache
        texts_to_embed = []
        indices_to_embed = []
        
        for i in valid_indices:
            text = processed_texts[i]
            cached_embedding = self._get_from_cache(text)
            if cached_embedding is not None:
                results[i] = cached_embedding
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(i)
        
        # Se todos os embeddings foram encontrados no cache, retornar os resultados
        if not texts_to_embed:
            return results
        
        # Processar em lotes para os textos não encontrados no cache
        for i in range(0, len(texts_to_embed), batch_size):
            batch_texts = texts_to_embed[i:i+batch_size]
            batch_indices = indices_to_embed[i:i+batch_size]
            
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch_texts
                )
                
                # Atualizar contadores de uso
                self.token_usage += response.usage.total_tokens
                self.api_calls += 1
                
                # Extrair os embeddings da resposta e salvá-los no cache
                for j, data in enumerate(response.data):
                    embedding = data.embedding
                    original_index = batch_indices[j]
                    original_text = batch_texts[j]
                    
                    # Salvar no cache
                    self._save_to_cache(original_text, embedding)
                    
                    # Atualizar resultados
                    results[original_index] = embedding
                    
            except Exception as e:
                self.logger.error(f"Erro ao gerar embeddings em lote: {e}")
                # Preencher os resultados faltantes com listas vazias
                for idx in batch_indices:
                    if not results[idx]:
                        results[idx] = []
        
        return results
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de uso do serviço de embeddings.
        
        Returns:
            Dicionário com estatísticas de uso e estimativa de custos
        """
        # Calcular custo estimado com base no uso de tokens
        # Para text-embedding-3-small: $0.02 por milhão de tokens
        cost_per_million = 0.02
        estimated_cost = (self.token_usage / 1_000_000) * cost_per_million
        
        return {
            "model": self.model,
            "api_calls": self.api_calls,
            "tokens_used": self.token_usage,
            "estimated_cost_usd": estimated_cost,
            "cache_enabled": self.use_cache,
            "cache_status": "connected" if (self.use_cache and self.redis_client) else "disabled"
        }
    
    def reset_usage_stats(self) -> None:
        """
        Reinicia os contadores de uso.
        """
        self.token_usage = 0
        self.api_calls = 0
        self.logger.info("Contadores de uso reiniciados")
