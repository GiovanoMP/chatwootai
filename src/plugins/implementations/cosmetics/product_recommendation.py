"""
Plugin de recomendação de produtos para o domínio de cosméticos.
"""
from typing import Dict, List, Any, Optional
import logging

from src.plugins.base import BasePlugin

logger = logging.getLogger(__name__)


class ProductRecommendationPlugin(BasePlugin):
    """
    Plugin para recomendação de produtos cosméticos baseado no perfil do cliente,
    histórico de compras e preocupações específicas.
    """
    
    def initialize(self):
        """
        Inicializa o plugin carregando dados específicos de produtos cosméticos.
        """
        self.skin_types = ["normal", "seca", "oleosa", "mista", "sensível"]
        self.concerns = ["acne", "rugas", "manchas", "hidratação", "proteção solar"]
        self.product_database = self._load_product_database()
    
    def _load_product_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Carrega o banco de dados de produtos cosméticos.
        Em uma implementação real, isso poderia vir de uma API ou banco de dados.
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Banco de dados de produtos organizados por categoria
        """
        # Simulação de banco de dados de produtos
        return {
            "limpeza": [
                {
                    "id": "cl001",
                    "name": "Gel de Limpeza Facial",
                    "description": "Gel de limpeza suave para todos os tipos de pele",
                    "price": 45.90,
                    "suitable_for": ["normal", "mista", "oleosa"],
                    "addresses_concerns": ["acne", "oleosidade"]
                },
                {
                    "id": "cl002",
                    "name": "Sabonete Facial Hidratante",
                    "description": "Sabonete facial com propriedades hidratantes",
                    "price": 39.90,
                    "suitable_for": ["normal", "seca", "sensível"],
                    "addresses_concerns": ["hidratação", "sensibilidade"]
                }
            ],
            "hidratação": [
                {
                    "id": "hd001",
                    "name": "Creme Hidratante Facial",
                    "description": "Creme hidratante para uso diário",
                    "price": 59.90,
                    "suitable_for": ["normal", "seca", "sensível"],
                    "addresses_concerns": ["hidratação", "ressecamento"]
                },
                {
                    "id": "hd002",
                    "name": "Sérum Hidratante",
                    "description": "Sérum concentrado para hidratação profunda",
                    "price": 89.90,
                    "suitable_for": ["normal", "seca", "mista", "sensível"],
                    "addresses_concerns": ["hidratação", "rugas", "linhas finas"]
                }
            ],
            "tratamento": [
                {
                    "id": "tr001",
                    "name": "Sérum Anti-Acne",
                    "description": "Sérum específico para tratamento de acne",
                    "price": 79.90,
                    "suitable_for": ["oleosa", "mista", "normal"],
                    "addresses_concerns": ["acne", "oleosidade", "poros dilatados"]
                },
                {
                    "id": "tr002",
                    "name": "Creme Anti-Idade",
                    "description": "Creme para combater sinais de envelhecimento",
                    "price": 129.90,
                    "suitable_for": ["normal", "seca", "mista"],
                    "addresses_concerns": ["rugas", "linhas finas", "flacidez"]
                }
            ],
            "proteção": [
                {
                    "id": "pr001",
                    "name": "Protetor Solar FPS 50",
                    "description": "Protetor solar de amplo espectro",
                    "price": 69.90,
                    "suitable_for": ["normal", "seca", "mista", "oleosa", "sensível"],
                    "addresses_concerns": ["proteção solar", "manchas", "envelhecimento precoce"]
                },
                {
                    "id": "pr002",
                    "name": "Protetor Solar com Cor",
                    "description": "Protetor solar com cobertura leve",
                    "price": 79.90,
                    "suitable_for": ["normal", "seca", "mista", "sensível"],
                    "addresses_concerns": ["proteção solar", "uniformização da pele"]
                }
            ]
        }
    
    def execute(self, customer_profile: Dict[str, Any], concerns: List[str], 
                purchase_history: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Recomenda produtos cosméticos com base no perfil do cliente e preocupações.
        
        Args:
            customer_profile: Perfil do cliente (tipo de pele, idade, etc.)
            concerns: Lista de preocupações do cliente (acne, rugas, etc.)
            purchase_history: Histórico de compras do cliente (opcional)
            
        Returns:
            List[Dict[str, Any]]: Lista de produtos recomendados
        """
        skin_type = customer_profile.get("skin_type", "normal")
        age = customer_profile.get("age", 30)
        
        # Validação de dados
        if skin_type not in self.skin_types:
            logger.warning(f"Tipo de pele desconhecido: {skin_type}. Usando 'normal' como padrão.")
            skin_type = "normal"
        
        # Filtra produtos adequados para o tipo de pele
        suitable_products = []
        for category, products in self.product_database.items():
            for product in products:
                if skin_type in product["suitable_for"]:
                    # Verifica se o produto atende às preocupações do cliente
                    if any(concern in product["addresses_concerns"] for concern in concerns):
                        suitable_products.append(product)
        
        # Ordenação por relevância (número de preocupações atendidas)
        suitable_products.sort(key=lambda p: sum(1 for c in concerns if c in p["addresses_concerns"]), reverse=True)
        
        # Considera histórico de compras para evitar recomendar produtos já comprados
        if purchase_history:
            purchased_ids = [item["product_id"] for item in purchase_history]
            suitable_products = [p for p in suitable_products if p["id"] not in purchased_ids]
        
        # Limita a 5 recomendações
        return suitable_products[:5]
    
    def get_routine_recommendation(self, skin_type: str, concerns: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Recomenda uma rotina completa de cuidados com a pele.
        
        Args:
            skin_type: Tipo de pele do cliente
            concerns: Preocupações do cliente
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Rotina recomendada organizada por etapa
        """
        routine = {}
        
        # Para cada etapa da rotina, encontra os produtos mais adequados
        for step, category in [
            ("Limpeza", "limpeza"),
            ("Tratamento", "tratamento"),
            ("Hidratação", "hidratação"),
            ("Proteção", "proteção")
        ]:
            if category in self.product_database:
                # Filtra produtos adequados para o tipo de pele
                suitable_products = [
                    p for p in self.product_database[category]
                    if skin_type in p["suitable_for"] and
                    any(concern in p["addresses_concerns"] for concern in concerns)
                ]
                
                # Ordena por relevância
                suitable_products.sort(
                    key=lambda p: sum(1 for c in concerns if c in p["addresses_concerns"]),
                    reverse=True
                )
                
                # Adiciona à rotina
                routine[step] = suitable_products[:2]  # Até 2 opções por etapa
        
        return routine
