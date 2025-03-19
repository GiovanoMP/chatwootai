"""
Cliente para integração com o Odoo.
"""
from typing import Dict, List, Any, Optional
import logging
import requests
import json



logger = logging.getLogger(__name__)


class OdooClient:
    """
    Cliente para integração com o Odoo.
    
    Implementa a comunicação direta com o sistema ERP Odoo via API,
    utilizando o PostgreSQL em Docker como simulação durante o desenvolvimento.
    """
    
    def initialize(self):
        """
        Inicializa o cliente Odoo.
        """
        super().initialize()
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": self.api_key
        })
    
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Realiza uma requisição para a API do Odoo.
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API
            data: Dados a serem enviados (opcional)
            
        Returns:
            Dict[str, Any]: Resposta da API
        """
        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=data, timeout=self.timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=self.timeout)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, timeout=self.timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, json=data, timeout=self.timeout)
            else:
                logger.error(f"Método HTTP não suportado: {method}")
                return {"error": f"Método HTTP não suportado: {method}"}
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para o Odoo: {str(e)}")
            return {"error": str(e)}
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar resposta JSON: {str(e)}")
            return {"error": f"Erro ao decodificar resposta JSON: {str(e)}"}
    
    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Obtém informações de um cliente pelo ID.
        
        Args:
            customer_id: ID do cliente
            
        Returns:
            Dict[str, Any]: Informações do cliente
        """
        return self._make_request("GET", f"/customers/{customer_id}")
    
    def search_customers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca clientes pelo nome, email ou outros critérios.
        
        Args:
            query: Termo de busca
            limit: Limite de resultados
            
        Returns:
            List[Dict[str, Any]]: Lista de clientes encontrados
        """
        return self._make_request("GET", "/customers", {"query": query, "limit": limit})
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um novo cliente.
        
        Args:
            customer_data: Dados do cliente
            
        Returns:
            Dict[str, Any]: Cliente criado
        """
        return self._make_request("POST", "/customers", customer_data)
    
    def update_customer(self, customer_id: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza os dados de um cliente.
        
        Args:
            customer_id: ID do cliente
            customer_data: Novos dados do cliente
            
        Returns:
            Dict[str, Any]: Cliente atualizado
        """
        return self._make_request("PUT", f"/customers/{customer_id}", customer_data)
    
    def get_product(self, product_id: str) -> Dict[str, Any]:
        """
        Obtém informações de um produto pelo ID.
        
        Args:
            product_id: ID do produto
            
        Returns:
            Dict[str, Any]: Informações do produto
        """
        return self._make_request("GET", f"/products/{product_id}")
    
    def search_products(self, query: str, category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca produtos pelo nome, categoria ou outros critérios.
        
        Args:
            query: Termo de busca
            category: Categoria do produto (opcional)
            limit: Limite de resultados
            
        Returns:
            List[Dict[str, Any]]: Lista de produtos encontrados
        """
        params = {"query": query, "limit": limit}
        if category:
            params["category"] = category
        
        return self._make_request("GET", "/products", params)
    
    def get_product_stock(self, product_id: str, warehouse_id: str = None) -> Dict[str, Any]:
        """
        Obtém informações de estoque de um produto.
        
        Args:
            product_id: ID do produto
            warehouse_id: ID do armazém (opcional)
            
        Returns:
            Dict[str, Any]: Informações de estoque
        """
        params = {}
        if warehouse_id:
            params["warehouse_id"] = warehouse_id
        
        return self._make_request("GET", f"/products/{product_id}/stock", params)
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um novo pedido.
        
        Args:
            order_data: Dados do pedido
            
        Returns:
            Dict[str, Any]: Pedido criado
        """
        return self._make_request("POST", "/orders", order_data)
    
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Obtém informações de um pedido pelo ID.
        
        Args:
            order_id: ID do pedido
            
        Returns:
            Dict[str, Any]: Informações do pedido
        """
        return self._make_request("GET", f"/orders/{order_id}")
    
    def update_order(self, order_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza os dados de um pedido.
        
        Args:
            order_id: ID do pedido
            order_data: Novos dados do pedido
            
        Returns:
            Dict[str, Any]: Pedido atualizado
        """
        return self._make_request("PUT", f"/orders/{order_id}", order_data)
    
    def get_customer_orders(self, customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtém os pedidos de um cliente.
        
        Args:
            customer_id: ID do cliente
            limit: Limite de resultados
            
        Returns:
            List[Dict[str, Any]]: Lista de pedidos do cliente
        """
        return self._make_request("GET", f"/customers/{customer_id}/orders", {"limit": limit})
    
    def get_business_rules(self, category: str = None) -> Dict[str, Any]:
        """
        Obtém as regras de negócio do Odoo.
        
        Args:
            category: Categoria específica de regras (opcional)
            
        Returns:
            Dict[str, Any]: Regras de negócio
        """
        params = {}
        if category:
            params["category"] = category
        
        return self._make_request("GET", "/business-rules", params)
    
    def create_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um novo agendamento.
        
        Args:
            appointment_data: Dados do agendamento
            
        Returns:
            Dict[str, Any]: Agendamento criado
        """
        return self._make_request("POST", "/appointments", appointment_data)
    
    def get_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """
        Obtém informações de um agendamento pelo ID.
        
        Args:
            appointment_id: ID do agendamento
            
        Returns:
            Dict[str, Any]: Informações do agendamento
        """
        return self._make_request("GET", f"/appointments/{appointment_id}")
    
    def update_appointment(self, appointment_id: str, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza os dados de um agendamento.
        
        Args:
            appointment_id: ID do agendamento
            appointment_data: Novos dados do agendamento
            
        Returns:
            Dict[str, Any]: Agendamento atualizado
        """
        return self._make_request("PUT", f"/appointments/{appointment_id}", appointment_data)
    
    def get_available_slots(self, service_id: str, date_from: str, date_to: str) -> List[Dict[str, Any]]:
        """
        Obtém os horários disponíveis para um serviço.
        
        Args:
            service_id: ID do serviço
            date_from: Data inicial
            date_to: Data final
            
        Returns:
            List[Dict[str, Any]]: Lista de horários disponíveis
        """
        params = {
            "service_id": service_id,
            "date_from": date_from,
            "date_to": date_to
        }
        
        return self._make_request("GET", "/appointments/available-slots", params)
    
    def get_customer_appointments(self, customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtém os agendamentos de um cliente.
        
        Args:
            customer_id: ID do cliente
            limit: Limite de resultados
            
        Returns:
            List[Dict[str, Any]]: Lista de agendamentos do cliente
        """
        return self._make_request("GET", f"/customers/{customer_id}/appointments", {"limit": limit})
