"""
Serviço de Sincronização de Dados entre PostgreSQL e Qdrant.
Este serviço é responsável por manter os dados sincronizados entre o banco de dados
relacional (PostgreSQL) e o banco de dados vetorial (Qdrant).
"""
import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import psycopg2
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

from src.services.embedding_service import EmbeddingService
from src.utils.text_processor import prepare_product_text, prepare_business_rule_text

class DataSyncService:
    """
    Serviço para sincronização de dados entre PostgreSQL e Qdrant.
    
    Este serviço encapsula a lógica de sincronização de dados entre o banco de dados
    relacional (PostgreSQL) e o banco de dados vetorial (Qdrant), garantindo que
    os embeddings estejam sempre atualizados.
    """
    
    def __init__(
        self, 
        db_connection_string: Optional[str] = None,
        qdrant_url: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None,
        redis_client = None
    ):
        """
        Inicializa o serviço de sincronização de dados.
        
        Args:
            db_connection_string: String de conexão com o PostgreSQL. Se não fornecida,
                                 será buscada na variável de ambiente DATABASE_URL.
            qdrant_url: URL do serviço Qdrant. Se não fornecida, será buscada na
                       variável de ambiente QDRANT_URL.
            embedding_service: Instância do EmbeddingService. Se não fornecida, uma nova
                              instância será criada.
            redis_client: Cliente Redis para cache (opcional).
        """
        self.db_connection_string = db_connection_string or os.environ.get("DATABASE_URL")
        if not self.db_connection_string:
            raise ValueError("String de conexão com o PostgreSQL não fornecida e não encontrada nas variáveis de ambiente")
            
        self.qdrant_url = qdrant_url or os.environ.get("QDRANT_URL")
        if not self.qdrant_url:
            raise ValueError("URL do Qdrant não fornecida e não encontrada nas variáveis de ambiente")
            
        self.embedding_service = embedding_service or EmbeddingService()
        self.redis_client = redis_client
        self.qdrant_client = QdrantClient(url=self.qdrant_url)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Serviço de Sincronização de Dados inicializado")
        
    def _get_db_connection(self):
        """
        Obtém uma conexão com o banco de dados PostgreSQL.
        
        Returns:
            Conexão com o PostgreSQL.
        """
        return psycopg2.connect(self.db_connection_string)
        
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém um produto do PostgreSQL pelo ID.
        
        Args:
            product_id: ID do produto a ser obtido.
            
        Returns:
            Dicionário com os dados do produto ou None se não encontrado.
        """
        try:
            with self._get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM products WHERE id = %s
                    """, (product_id,))
                    product = cursor.fetchone()
                    return dict(product) if product else None
        except Exception as e:
            self.logger.error(f"Erro ao obter produto {product_id}: {e}")
            return None
            
    def get_business_rule(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém uma regra de negócio do PostgreSQL pelo ID.
        
        Args:
            rule_id: ID da regra de negócio a ser obtida.
            
        Returns:
            Dicionário com os dados da regra de negócio ou None se não encontrada.
        """
        try:
            with self._get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM business_rules WHERE id = %s
                    """, (rule_id,))
                    rule = cursor.fetchone()
                    return dict(rule) if rule else None
        except Exception as e:
            self.logger.error(f"Erro ao obter regra de negócio {rule_id}: {e}")
            return None
            
    def get_all_product_ids(self) -> List[int]:
        """
        Obtém todos os IDs de produtos do PostgreSQL.
        
        Returns:
            Lista de IDs de produtos.
        """
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM products")
                    return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Erro ao obter IDs de produtos: {e}")
            return []
            
    def get_all_business_rule_ids(self) -> List[int]:
        """
        Obtém todos os IDs de regras de negócio do PostgreSQL.
        
        Returns:
            Lista de IDs de regras de negócio.
        """
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM business_rules")
                    return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Erro ao obter IDs de regras de negócio: {e}")
            return []
            
    def sync_product(self, product_id: int) -> bool:
        """
        Sincroniza um único produto entre PostgreSQL e Qdrant.
        
        Args:
            product_id: ID do produto a ser sincronizado.
            
        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário.
        """
        try:
            # 1. Obter dados do produto do PostgreSQL
            product = self.get_product(product_id)
            
            if not product:
                # Se o produto foi removido, remova-o do Qdrant também
                self.qdrant_client.delete(
                    collection_name="products",
                    points_selector=[product_id]
                )
                self.logger.info(f"Produto {product_id} removido do Qdrant (não encontrado no PostgreSQL)")
                return True
            
            # 2. Preparar o texto para embedding
            product_text = prepare_product_text(product)
            
            # 3. Gerar embedding
            embedding = self.embedding_service.get_embedding(product_text)
            
            # 4. Atualizar ou inserir no Qdrant
            self.qdrant_client.upsert(
                collection_name="products",
                points=[
                    PointStruct(
                        id=product_id,
                        vector=embedding,
                        payload={
                            "name": product["name"],
                            "category_id": product["category_id"],
                            "active": product["active"],
                            "price": float(product["price"]),
                            "last_updated": datetime.now().isoformat()
                        }
                    )
                ]
            )
            
            # 5. Invalidar cache se necessário
            if self.redis_client:
                self.redis_client.delete(f"product:{product_id}")
                self.redis_client.delete("product_search:*")
                
            self.logger.info(f"Produto {product_id} sincronizado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao sincronizar produto {product_id}: {e}")
            return False
            
    def sync_business_rule(self, rule_id: int) -> bool:
        """
        Sincroniza uma única regra de negócio entre PostgreSQL e Qdrant.
        
        Args:
            rule_id: ID da regra de negócio a ser sincronizada.
            
        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário.
        """
        try:
            # 1. Obter dados da regra de negócio do PostgreSQL
            rule = self.get_business_rule(rule_id)
            
            if not rule:
                # Se a regra foi removida, remova-a do Qdrant também
                self.qdrant_client.delete(
                    collection_name="business_rules",
                    points_selector=[rule_id]
                )
                self.logger.info(f"Regra de negócio {rule_id} removida do Qdrant (não encontrada no PostgreSQL)")
                return True
            
            # 2. Preparar o texto para embedding
            rule_text = prepare_business_rule_text(rule)
            
            # 3. Gerar embedding
            embedding = self.embedding_service.get_embedding(rule_text)
            
            # 4. Atualizar ou inserir no Qdrant
            self.qdrant_client.upsert(
                collection_name="business_rules",
                points=[
                    PointStruct(
                        id=rule_id,
                        vector=embedding,
                        payload={
                            "name": rule["name"],
                            "category": rule["category"],
                            "active": rule["active"],
                            "last_updated": datetime.now().isoformat()
                        }
                    )
                ]
            )
            
            # 5. Invalidar cache se necessário
            if self.redis_client:
                self.redis_client.delete(f"business_rule:{rule_id}")
                self.redis_client.delete("business_rule_search:*")
                
            self.logger.info(f"Regra de negócio {rule_id} sincronizada com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao sincronizar regra de negócio {rule_id}: {e}")
            return False
            
    def delete_product(self, product_id: int) -> bool:
        """
        Remove um produto do Qdrant.
        
        Args:
            product_id: ID do produto a ser removido.
            
        Returns:
            True se a remoção foi bem-sucedida, False caso contrário.
        """
        try:
            self.qdrant_client.delete(
                collection_name="products",
                points_selector=[product_id]
            )
            
            # Invalidar cache se necessário
            if self.redis_client:
                self.redis_client.delete(f"product:{product_id}")
                self.redis_client.delete("product_search:*")
                
            self.logger.info(f"Produto {product_id} removido do Qdrant")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao remover produto {product_id} do Qdrant: {e}")
            return False
            
    def delete_business_rule(self, rule_id: int) -> bool:
        """
        Remove uma regra de negócio do Qdrant.
        
        Args:
            rule_id: ID da regra de negócio a ser removida.
            
        Returns:
            True se a remoção foi bem-sucedida, False caso contrário.
        """
        try:
            self.qdrant_client.delete(
                collection_name="business_rules",
                points_selector=[rule_id]
            )
            
            # Invalidar cache se necessário
            if self.redis_client:
                self.redis_client.delete(f"business_rule:{rule_id}")
                self.redis_client.delete("business_rule_search:*")
                
            self.logger.info(f"Regra de negócio {rule_id} removida do Qdrant")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao remover regra de negócio {rule_id} do Qdrant: {e}")
            return False
            
    def full_sync_products(self, batch_size: int = 100) -> bool:
        """
        Sincroniza todos os produtos entre PostgreSQL e Qdrant.
        
        Args:
            batch_size: Tamanho do lote para processamento em batch.
            
        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário.
        """
        try:
            # Obter todos os IDs de produtos
            product_ids = self.get_all_product_ids()
            total_products = len(product_ids)
            
            self.logger.info(f"Iniciando sincronização completa de {total_products} produtos")
            
            # Sincronizar em lotes para evitar sobrecarga de memória
            success_count = 0
            for i in range(0, total_products, batch_size):
                batch = product_ids[i:i+batch_size]
                self.logger.info(f"Processando lote de produtos {i+1} a {min(i+batch_size, total_products)} de {total_products}")
                
                for product_id in batch:
                    if self.sync_product(product_id):
                        success_count += 1
            
            success_rate = (success_count / total_products) * 100 if total_products > 0 else 100
            self.logger.info(f"Sincronização completa de produtos concluída. Taxa de sucesso: {success_rate:.2f}% ({success_count}/{total_products})")
            
            return success_rate > 95  # Consideramos sucesso se mais de 95% dos produtos foram sincronizados
            
        except Exception as e:
            self.logger.error(f"Erro durante sincronização completa de produtos: {e}")
            return False
            
    def full_sync_business_rules(self, batch_size: int = 100) -> bool:
        """
        Sincroniza todas as regras de negócio entre PostgreSQL e Qdrant.
        
        Args:
            batch_size: Tamanho do lote para processamento em batch.
            
        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário.
        """
        try:
            # Obter todos os IDs de regras de negócio
            rule_ids = self.get_all_business_rule_ids()
            total_rules = len(rule_ids)
            
            self.logger.info(f"Iniciando sincronização completa de {total_rules} regras de negócio")
            
            # Sincronizar em lotes para evitar sobrecarga de memória
            success_count = 0
            for i in range(0, total_rules, batch_size):
                batch = rule_ids[i:i+batch_size]
                self.logger.info(f"Processando lote de regras de negócio {i+1} a {min(i+batch_size, total_rules)} de {total_rules}")
                
                for rule_id in batch:
                    if self.sync_business_rule(rule_id):
                        success_count += 1
            
            success_rate = (success_count / total_rules) * 100 if total_rules > 0 else 100
            self.logger.info(f"Sincronização completa de regras de negócio concluída. Taxa de sucesso: {success_rate:.2f}% ({success_count}/{total_rules})")
            
            return success_rate > 95  # Consideramos sucesso se mais de 95% das regras foram sincronizadas
            
        except Exception as e:
            self.logger.error(f"Erro durante sincronização completa de regras de negócio: {e}")
            return False
