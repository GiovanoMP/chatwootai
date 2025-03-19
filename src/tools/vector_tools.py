"""
Vector search tools for the hub-and-spoke architecture.

This module implements tools for semantic search using Qdrant vector database.
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from openai import OpenAI
from crewai.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class QdrantVectorSearchTool(BaseTool):
    """Tool for semantic search using Qdrant vector database."""
    
    name: str = "vector_search"
    description: str = "Performs semantic search in a vector database to find relevant information."
    
    # Configuração do modelo para permitir tipos arbitrários
    model_config = {"arbitrary_types_allowed": True}
    
    # Definir campos Pydantic
    qdrant_url: str
    qdrant_api_key: Optional[str] = None
    collection_name: str = "default"
    openai_api_key: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"  # Modelo mais econômico da OpenAI
    top_k: int = 5
    
    # Campos adicionais que serão inicializados no __init__
    qdrant_client: Any = None
    openai_client: Any = None
    embedding_cache: Dict[str, List[float]] = {}
    
    def __init__(self, 
                 qdrant_url: str, 
                 qdrant_api_key: Optional[str] = None,
                 collection_name: str = "default",
                 openai_api_key: Optional[str] = None,
                 embedding_model: str = "text-embedding-3-small",  # Modelo mais econômico da OpenAI
                 top_k: int = 5):
        """
        Initialize the Qdrant vector search tool.
        
        Args:
            qdrant_url: URL of the Qdrant server
            qdrant_api_key: API key for Qdrant (optional)
            collection_name: Name of the collection to search
            openai_api_key: API key for OpenAI (for generating embeddings)
            embedding_model: Name of the embedding model to use
            top_k: Number of results to return
        """
        super().__init__(qdrant_url=qdrant_url,
                         qdrant_api_key=qdrant_api_key,
                         collection_name=collection_name,
                         openai_api_key=openai_api_key,
                         embedding_model=embedding_model,
                         top_k=top_k)
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
        
        # Initialize OpenAI client for embeddings
        self.openai_client = OpenAI(api_key=openai_api_key)
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            The embedding as a list of floats
        """
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return empty embedding in case of error
            return [0.0] * 1536  # text-embedding-3-small também usa 1536 dimensões
    
    def _run(self, query: str, filter_conditions: Optional[Dict[str, Any]] = None, top_k: Optional[int] = None) -> str:
        """
        Execute the tool as required by BaseTool.
        
        Args:
            query: The search query
            filter_conditions: Additional filter conditions (optional)
            top_k: Number of results to return (optional)
            
        Returns:
            String representation of search results
        """
        results = self.search(query, filter_conditions, top_k)
        
        # Format results as a string
        if not results:
            return "No matching documents found."
            
        formatted_results = []
        for i, result in enumerate(results):
            formatted_result = f"Result {i+1} (Score: {result['score']:.4f}):\n"
            
            # Add payload information
            for key, value in result['payload'].items():
                if key == 'text' or key == 'content':
                    # Truncate long text
                    if len(str(value)) > 300:
                        value = str(value)[:300] + "..."
                formatted_result += f"  {key}: {value}\n"
                
            formatted_results.append(formatted_result)
            
        return "\n\n".join(formatted_results)
    
    def search(self, query: str, 
               filter_conditions: Optional[Dict[str, Any]] = None,
               top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query.
        
        Args:
            query: The search query
            filter_conditions: Additional filter conditions
            top_k: Number of results to return (overrides instance default)
            
        Returns:
            List of matching documents with their metadata and similarity scores
        """
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            
            # Build filter if provided
            search_filter = None
            if filter_conditions:
                filter_clauses = []
                for field, value in filter_conditions.items():
                    filter_clauses.append(
                        FieldCondition(
                            key=field,
                            match=MatchValue(value=value)
                        )
                    )
                search_filter = Filter(must=filter_clauses)
            
            # Perform the search
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k or self.top_k,
                filter=search_filter
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "score": result.score,
                    "payload": result.payload,
                    "id": result.id
                })
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []
    
    def add_document(self, text: str, metadata: Dict[str, Any], id: Optional[str] = None) -> bool:
        """
        Add a document to the Qdrant collection.
        
        Args:
            text: The text content of the document
            metadata: Metadata for the document
            id: Optional ID for the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embedding for the document
            embedding = self.generate_embedding(text)
            
            # Add the document to Qdrant
            payload = {**metadata, "text": text}
            
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    {
                        "id": id or metadata.get("id"),
                        "vector": embedding,
                        "payload": payload
                    }
                ]
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error adding document to Qdrant: {e}")
            return False
    
    def delete_document(self, id: str) -> bool:
        """
        Delete a document from the Qdrant collection.
        
        Args:
            id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points=[id]
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting document from Qdrant: {e}")
            return False
    
    def create_collection_if_not_exists(self, vector_size: int = 1536) -> bool:
        """
        Create the collection if it doesn't exist.
        
        Args:
            vector_size: Size of the embedding vectors. O valor padrão 1536 é o tamanho 
                         utilizado pelo modelo text-embedding-3-small da OpenAI.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        "size": vector_size,
                        "distance": "Cosine"
                    }
                )
            
            return True
        
        except Exception as e:
            logger.error(f"Error creating Qdrant collection: {e}")
            return False
