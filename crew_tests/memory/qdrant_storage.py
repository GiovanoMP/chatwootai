"""
Implementação de armazenamento de memória usando Qdrant.
"""

from typing import Any, Dict, List, Optional
import os
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models

from ..config import QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIMENSION


class QdrantMultiTenantStorage:
    """
    Armazenamento de memória multi-tenant usando Qdrant.
    
    Esta classe implementa a interface de armazenamento para memória de curto prazo
    e memória de entidade do CrewAI, usando Qdrant como backend.
    """
    
    def __init__(
        self,
        type: str,
        account_id: str,
        allow_reset: bool = True,
        embedder_config: Optional[Dict[str, Any]] = None,
        crew: Optional[Any] = None
    ):
        """
        Inicializa o armazenamento de memória.
        
        Args:
            type: Tipo de memória (short-term ou entity)
            account_id: ID da conta do cliente
            allow_reset: Se permite resetar a memória
            embedder_config: Configuração do embedder
            crew: Instância da crew
        """
        self.type = type
        self.account_id = account_id
        self.allow_reset = allow_reset
        self.embedder_config = embedder_config
        self.crew = crew
        
        # Inicializar cliente OpenAI para embeddings
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Inicializar
        self._initialize_app()
    
    def _initialize_app(self):
        """Inicializa o cliente Qdrant e cria a coleção se necessário."""
        # Inicializar cliente Qdrant
        self.qdrant_client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY
        )
        
        # Nome da coleção com prefixo do account_id
        self.collection_name = f"{self.account_id}_{self.type}_memory"
        
        # Criar coleção se não existir
        if not self.qdrant_client.collection_exists(self.collection_name):
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=models.Distance.COSINE
                )
            )
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Gera embedding para o texto usando OpenAI.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Lista de floats representando o embedding
        """
        response = self.openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    
    def save(self, value: Any, metadata: Dict[str, Any]) -> None:
        """
        Salva um valor na memória.
        
        Args:
            value: Valor a ser salvo
            metadata: Metadados associados ao valor
        """
        # Adicionar account_id aos metadados
        metadata["account_id"] = self.account_id
        
        # Gerar embedding para o valor
        embedding = self._generate_embedding(value)
        
        # Salvar no Qdrant
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=metadata.get("id", str(hash(value))),
                    vector=embedding,
                    payload={
                        "text": value,
                        **metadata
                    }
                )
            ]
        )
    
    def search(
        self,
        query: str,
        limit: int = 3,
        filter: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Busca valores na memória.
        
        Args:
            query: Consulta para busca
            limit: Número máximo de resultados
            filter: Filtro adicional
            score_threshold: Limiar mínimo de similaridade
            
        Returns:
            Lista de resultados
        """
        # Gerar embedding para a consulta
        query_embedding = self._generate_embedding(query)
        
        # Construir filtro
        search_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="account_id",
                    match=models.MatchValue(
                        value=self.account_id
                    )
                )
            ]
        )
        
        # Adicionar filtros adicionais se fornecidos
        if filter:
            for key, value in filter.items():
                search_filter.must.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(
                            value=value
                        )
                    )
                )
        
        # Buscar no Qdrant
        search_results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=limit,
            score_threshold=score_threshold
        )
        
        # Formatar resultados
        results = []
        for hit in search_results:
            # Remover campos internos
            metadata = {k: v for k, v in hit.payload.items() if k not in ["text", "embedding"]}
            
            results.append({
                "id": hit.id,
                "metadata": metadata,
                "context": hit.payload.get("text", ""),
                "score": hit.score
            })
        
        return results
    
    def reset(self) -> None:
        """Reseta a memória, deletando a coleção."""
        if self.allow_reset and self.qdrant_client.collection_exists(self.collection_name):
            self.qdrant_client.delete_collection(self.collection_name)
            self._initialize_app()
