"""
Serviço de Sincronização entre PostgreSQL e Qdrant.
Este serviço é responsável por manter os dados sincronizados entre o banco relacional
e o banco vetorial, garantindo consistência nas buscas híbridas.
"""
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http import models

from .embedding_service import EmbeddingService

class PostgreSQLClient:
    """
    Cliente para interação com o PostgreSQL.
    
    Esta é uma implementação simplificada que deve ser adaptada para usar
    a conexão real com o PostgreSQL do seu projeto.
    """
    def __init__(self, connection_string: Optional[str] = None):
        """
        Inicializa o cliente PostgreSQL.
        
        Args:
            connection_string: String de conexão com o PostgreSQL.
                Se não fornecida, será buscada na variável de ambiente DATABASE_URL.
        """
        import psycopg2
        import psycopg2.extras
        
        self.connection_string = connection_string or os.environ.get("DATABASE_URL")
        if not self.connection_string:
            raise ValueError("String de conexão com o PostgreSQL não fornecida e não encontrada nas variáveis de ambiente")
            
        self.logger = logging.getLogger(__name__)
    
    def get_connection(self):
        """Obtém uma conexão com o PostgreSQL."""
        import psycopg2
        import psycopg2.extras
        return psycopg2.connect(self.connection_string)
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Executa uma consulta SQL e retorna os resultados.
        
        Args:
            query: Consulta SQL a ser executada.
            params: Parâmetros para a consulta.
            
        Returns:
            Lista de dicionários com os resultados da consulta.
        """
        import psycopg2.extras
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"Erro ao executar consulta: {str(e)}")
            raise
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém um produto pelo ID.
        
        Args:
            product_id: ID do produto.
            
        Returns:
            Dicionário com os dados do produto ou None se não encontrado.
        """
        results = self.execute_query("""
            SELECT p.id, p.name, p.description, p.price, p.detailed_information,
                   pc.name as category_name, COALESCE(i.quantity, 0) as stock,
                   p.active
            FROM products p
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.id = %s
        """, (product_id,))
        
        return results[0] if results else None
    
    def get_products_by_ids(self, product_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Obtém múltiplos produtos pelos IDs.
        
        Args:
            product_ids: Lista de IDs de produtos.
            
        Returns:
            Lista de dicionários com os dados dos produtos.
        """
        if not product_ids:
            return []
            
        results = self.execute_query("""
            SELECT p.id, p.name, p.description, p.price, p.detailed_information,
                   pc.name as category_name, COALESCE(i.quantity, 0) as stock,
                   p.active
            FROM products p
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.id IN %s
        """, (tuple(product_ids),))
        
        return results


class DataSyncService:
    """
    Serviço para sincronização de dados entre PostgreSQL e Qdrant.
    
    Este serviço é responsável por manter os dados consistentes entre o banco
    relacional (PostgreSQL) e o banco vetorial (Qdrant), garantindo que as
    buscas híbridas retornem resultados precisos e atualizados.
    """
    
    def __init__(self, 
                 postgres_client: Optional[PostgreSQLClient] = None,
                 qdrant_client: Optional[QdrantClient] = None,
                 embedding_service: Optional[EmbeddingService] = None):
        """
        Inicializa o serviço de sincronização.
        
        Args:
            postgres_client: Cliente PostgreSQL. Se não fornecido, será criado um novo.
            qdrant_client: Cliente Qdrant. Se não fornecido, será criado um novo.
            embedding_service: Serviço de embeddings. Se não fornecido, será criado um novo.
        """
        self.postgres = postgres_client or PostgreSQLClient()
        
        qdrant_url = os.environ.get("QDRANT_URL", "http://qdrant:6333")
        self.qdrant = qdrant_client or QdrantClient(url=qdrant_url)
        
        self.embedding_service = embedding_service or EmbeddingService()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Serviço de Sincronização inicializado")
        
    def sync_new_product(self, product_id: int) -> None:
        """
        Sincroniza um novo produto do PostgreSQL para o Qdrant.
        
        Este método:
        1. Busca os dados do produto no PostgreSQL
        2. Gera um embedding para o texto do produto
        3. Insere o produto com seu embedding no Qdrant
        
        Args:
            product_id: ID do produto a ser sincronizado.
        """
        # Buscar dados do produto
        product = self.postgres.get_product_by_id(product_id)
        if not product:
            self.logger.warning(f"Produto {product_id} não encontrado no PostgreSQL")
            return
            
        # Preparar texto para embedding
        text = self._prepare_product_text(product)
        
        # Gerar embedding usando a API externa
        embedding = self.embedding_service.get_embedding(text)
        
        # Inserir no Qdrant
        self.qdrant.upsert(
            collection_name="products",
            points=[models.PointStruct(
                id=product_id,
                vector=embedding,
                payload=self._prepare_product_payload(product)
            )]
        )
        self.logger.info(f"Produto {product_id} sincronizado com sucesso")
        
    def sync_batch_products(self, product_ids: List[int]) -> None:
        """
        Sincroniza múltiplos produtos em lote para economizar chamadas de API.
        
        Este método é mais eficiente para sincronizar muitos produtos de uma vez,
        pois faz apenas uma chamada à API de embeddings.
        
        Args:
            product_ids: Lista de IDs de produtos a serem sincronizados.
        """
        # Buscar dados dos produtos
        products = self.postgres.get_products_by_ids(product_ids)
        if not products:
            self.logger.warning(f"Nenhum produto encontrado para os IDs: {product_ids}")
            return
            
        # Preparar textos para embeddings
        texts = [self._prepare_product_text(product) for product in products]
        
        # Gerar embeddings em lote (mais econômico)
        embeddings = self.embedding_service.get_batch_embeddings(texts)
        
        # Preparar pontos para o Qdrant
        points = []
        for i, product in enumerate(products):
            points.append(models.PointStruct(
                id=product['id'],
                vector=embeddings[i],
                payload=self._prepare_product_payload(product)
            ))
        
        # Inserir no Qdrant em lote
        self.qdrant.upsert(
            collection_name="products",
            points=points
        )
        self.logger.info(f"{len(points)} produtos sincronizados com sucesso")
        
    def update_product_metadata(self, product_id: int) -> None:
        """
        Atualiza apenas os metadados de um produto sem gerar novo embedding.
        
        Este método é útil quando apenas informações como preço, estoque ou status
        mudam, mas a descrição do produto permanece a mesma.
        
        Args:
            product_id: ID do produto a ter os metadados atualizados.
        """
        product = self.postgres.get_product_by_id(product_id)
        if not product:
            self.logger.warning(f"Produto {product_id} não encontrado no PostgreSQL")
            return
            
        # Atualizar apenas payload no Qdrant
        self.qdrant.update_payload(
            collection_name="products",
            points=[product_id],
            payload=self._prepare_product_payload(product)
        )
        self.logger.info(f"Metadados do produto {product_id} atualizados com sucesso")
        
    def deactivate_product(self, product_id: int) -> None:
        """
        Marca um produto como inativo no Qdrant.
        
        Este método é preferível à exclusão completa, pois permite reativar
        o produto no futuro sem precisar gerar um novo embedding.
        
        Args:
            product_id: ID do produto a ser desativado.
        """
        self.qdrant.update_payload(
            collection_name="products",
            points=[product_id],
            payload={"active": False}
        )
        self.logger.info(f"Produto {product_id} desativado com sucesso")
        
    def delete_product(self, product_id: int) -> None:
        """
        Remove completamente um produto do Qdrant.
        
        Use este método com cautela, pois a exclusão é permanente e exigirá
        gerar um novo embedding se o produto for reintroduzido.
        
        Args:
            product_id: ID do produto a ser removido.
        """
        self.qdrant.delete(
            collection_name="products",
            points_selector=models.PointIdsList(
                points=[product_id]
            )
        )
        self.logger.info(f"Produto {product_id} removido com sucesso")
        
    def _prepare_product_text(self, product: Dict[str, Any]) -> str:
        """
        Prepara o texto de um produto para geração de embedding.
        
        Este método combina diferentes campos do produto para criar um texto
        rico que capture bem as características do produto para busca semântica.
        
        Args:
            product: Dicionário com os dados do produto.
            
        Returns:
            Texto preparado para geração de embedding.
        """
        text_parts = []
        
        # Adicionar nome e categoria
        text_parts.append(product['name'])
        if product.get('category_name'):
            text_parts.append(f"Categoria: {product['category_name']}")
        
        # Adicionar descrição
        if product.get('description'):
            text_parts.append(product['description'])
            
        # Adicionar informações detalhadas
        if product.get('detailed_information'):
            text_parts.append(product['detailed_information'])
            
        return ". ".join(text_parts)
        
    def _prepare_product_payload(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara o payload de um produto para armazenamento no Qdrant.
        
        O payload contém metadados que serão usados para filtragem e
        exibição dos resultados da busca.
        
        Args:
            product: Dicionário com os dados do produto.
            
        Returns:
            Dicionário com o payload para o Qdrant.
        """
        return {
            "id": product['id'],
            "name": product['name'],
            "description": product.get('description', ''),
            "category": product.get('category_name', ''),
            "price": float(product['price']) if product.get('price') else None,
            "stock": product.get('stock', 0),
            "active": product.get('active', True)
        }
