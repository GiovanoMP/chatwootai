"""
Database tools for the hub-and-spoke architecture.

This module implements tools for searching and querying PostgreSQL databases.
"""

import logging
from typing import Dict, List, Any, Optional, Union
import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from crewai.tools.base_tool import BaseTool
import json

logger = logging.getLogger(__name__)


class PGSearchTool(BaseTool):
    """Tool for searching PostgreSQL databases."""
    
    name: str = "database_search"
    description: str = "Searches PostgreSQL database tables for specific records."
    
    # Configuração do modelo para permitir tipos arbitrários
    model_config = {"arbitrary_types_allowed": True}
    
    # Definir campos Pydantic
    db_uri: str
    table_name: Union[str, List[str]]
    max_results: int = 50
    
    # Campos não-Pydantic que serão inicializados no __init__
    engine: Any = None
    Session: Any = None
    
    def __init__(self, 
                 db_uri: str,
                 table_name: Union[str, List[str]],
                 max_results: int = 50):
        """
        Initialize the PostgreSQL search tool.
        
        Args:
            db_uri: URI for the PostgreSQL database
            table_name: Name of the table(s) to search
            max_results: Maximum number of results to return
        """
        # Inicializar os campos Pydantic através do construtor da classe pai
        super().__init__(
            db_uri=db_uri,
            table_name=table_name,
            max_results=max_results
        )
        
        # Converter table_name para lista se for string
        if not isinstance(self.table_name, list):
            self.table_name = [self.table_name]
        
        # Initialize SQLAlchemy engine
        self.engine = create_engine(self.db_uri)
        self.Session = sessionmaker(bind=self.engine)
    
    def _run(self, query_str: str, table_name: Optional[str] = None) -> str:
        """
        Execute the tool as required by BaseTool.
        
        Args:
            query_str: JSON string or simple key=value query
            table_name: Optional table name to override the default
            
        Returns:
            String representation of search results
        """
        # Parse the query string
        query = {}
        try:
            # First try to parse as JSON
            query = json.loads(query_str)
        except json.JSONDecodeError:
            # If not JSON, try to parse as key=value pairs
            pairs = query_str.split(',') 
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    query[key.strip()] = value.strip()
        
        # Perform the search
        results = self.search(query, table_name)
        
        # Format results as a string
        if not results:
            return "No matching records found."
            
        formatted_results = []
        for i, result in enumerate(results):
            formatted_result = f"Record {i+1}:\n"
            for key, value in result.items():
                formatted_result += f"  {key}: {value}\n"
            formatted_results.append(formatted_result)
            
        return "\n\n".join(formatted_results)
    
    def search(self, query: Dict[str, Any], table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for records matching the query.
        
        Args:
            query: Dictionary of field-value pairs to match
            table_name: Optional table name to override instance default
            
        Returns:
            List of matching records
        """
        try:
            # Use specified table or default
            tables = [table_name] if table_name else self.table_name
            results = []
            
            with self.Session() as session:
                for table in tables:
                    # Build WHERE clause
                    where_clauses = []
                    params = {}
                    
                    for field, value in query.items():
                        where_clauses.append(f"{field} = :{field}")
                        params[field] = value
                    
                    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                    
                    # Execute query
                    sql = text(f"SELECT * FROM {table} WHERE {where_clause} LIMIT {self.max_results}")
                    result = session.execute(sql, params)
                    
                    # Convert to dictionaries
                    for row in result:
                        results.append(dict(row._mapping))
            
            return results
        
        except Exception as e:
            logger.error(f"Error searching PostgreSQL: {e}")
            return []
    
    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom SQL query.
        
        Args:
            sql: SQL query to execute
            params: Parameters for the query
            
        Returns:
            List of results
        """
        try:
            with self.Session() as session:
                result = session.execute(text(sql), params or {})
                
                # Convert to dictionaries
                results = []
                for row in result:
                    results.append(dict(row._mapping))
                
                return results
        
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return []
    
    def insert(self, table_name: str, data: Dict[str, Any]) -> bool:
        """
        Insert a record into the database.
        
        Args:
            table_name: Name of the table
            data: Data to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build column and value lists
            columns = ", ".join(data.keys())
            placeholders = ", ".join([f":{key}" for key in data.keys()])
            
            with self.Session() as session:
                # Execute insert
                sql = text(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})")
                session.execute(sql, data)
                session.commit()
                
                return True
        
        except Exception as e:
            logger.error(f"Error inserting into PostgreSQL: {e}")
            return False
    
    def update(self, table_name: str, data: Dict[str, Any], 
               condition: Dict[str, Any]) -> bool:
        """
        Update records in the database.
        
        Args:
            table_name: Name of the table
            data: Data to update
            condition: Condition for the update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build SET clause
            set_clauses = []
            params = {}
            
            for field, value in data.items():
                set_clauses.append(f"{field} = :{field}")
                params[field] = value
            
            # Build WHERE clause
            where_clauses = []
            
            for field, value in condition.items():
                where_clauses.append(f"{field} = :where_{field}")
                params[f"where_{field}"] = value
            
            set_clause = ", ".join(set_clauses)
            where_clause = " AND ".join(where_clauses)
            
            with self.Session() as session:
                # Execute update
                sql = text(f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}")
                session.execute(sql, params)
                session.commit()
                
                return True
        
        except Exception as e:
            logger.error(f"Error updating PostgreSQL: {e}")
            return False
    
    def delete(self, table_name: str, condition: Dict[str, Any]) -> bool:
        """
        Delete records from the database.
        
        Args:
            table_name: Name of the table
            condition: Condition for the delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build WHERE clause
            where_clauses = []
            params = {}
            
            for field, value in condition.items():
                where_clauses.append(f"{field} = :{field}")
                params[field] = value
            
            where_clause = " AND ".join(where_clauses)
            
            with self.Session() as session:
                # Execute delete
                sql = text(f"DELETE FROM {table_name} WHERE {where_clause}")
                session.execute(sql, params)
                session.commit()
                
                return True
        
        except Exception as e:
            logger.error(f"Error deleting from PostgreSQL: {e}")
            return False


class OdooSimulationTool:
    """Tool for simulating Odoo API calls using PostgreSQL."""
    
    def __init__(self, db_uri: str):
        """
        Initialize the Odoo simulation tool.
        
        Args:
            db_uri: URI for the PostgreSQL database
        """
        self.db_uri = db_uri
        self.pg_tool = PGSearchTool(db_uri=db_uri, table_name=[])
    
    def get_products(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get products matching the filters.
        
        Args:
            filters: Filters to apply
            
        Returns:
            List of products
        """
        try:
            # Build WHERE clause
            where_clauses = []
            params = {}
            
            if filters:
                for field, value in filters.items():
                    where_clauses.append(f"{field} = :{field}")
                    params[field] = value
            
            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Execute query
            sql = f"""
                SELECT 
                    p.id, p.name, p.description, p.price, p.stock_quantity,
                    c.name as category_name
                FROM 
                    products p
                LEFT JOIN 
                    product_categories c ON p.category_id = c.id
                WHERE 
                    {where_clause}
                ORDER BY 
                    p.name
                LIMIT 50
            """
            
            return self.pg_tool.execute_query(sql, params)
        
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return []
    
    def get_customer(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """
        Get customer by ID.
        
        Args:
            customer_id: ID of the customer
            
        Returns:
            Customer data or None if not found
        """
        try:
            sql = """
                SELECT 
                    c.id, c.name, c.email, c.phone, c.address,
                    c.created_at, c.last_purchase_date,
                    COUNT(o.id) as order_count,
                    SUM(o.total_amount) as total_spent
                FROM 
                    customers c
                LEFT JOIN 
                    orders o ON c.id = o.customer_id
                WHERE 
                    c.id = :customer_id
                GROUP BY 
                    c.id, c.name, c.email, c.phone, c.address, c.created_at, c.last_purchase_date
            """
            
            results = self.pg_tool.execute_query(sql, {"customer_id": customer_id})
            
            return results[0] if results else None
        
        except Exception as e:
            logger.error(f"Error getting customer: {e}")
            return None
    
    def get_business_rules(self, category: str) -> List[Dict[str, Any]]:
        """
        Get business rules by category.
        
        Args:
            category: Category of rules to retrieve
            
        Returns:
            List of business rules
        """
        try:
            sql = """
                SELECT 
                    id, name, description, category, 
                    rule_type, conditions, actions, priority
                FROM 
                    business_rules
                WHERE 
                    category = :category
                ORDER BY 
                    priority DESC
            """
            
            return self.pg_tool.execute_query(sql, {"category": category})
        
        except Exception as e:
            logger.error(f"Error getting business rules: {e}")
            return []
    
    def create_order(self, order_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new order.
        
        Args:
            order_data: Order data
            
        Returns:
            ID of the created order or None if failed
        """
        try:
            # Extract order items
            items = order_data.pop("items", [])
            
            # Insert order
            with self.pg_tool.Session() as session:
                # Insert order
                order_sql = text("""
                    INSERT INTO orders (
                        customer_id, order_date, total_amount, 
                        status, payment_method, shipping_address
                    ) VALUES (
                        :customer_id, NOW(), :total_amount, 
                        :status, :payment_method, :shipping_address
                    ) RETURNING id
                """)
                
                result = session.execute(order_sql, order_data)
                order_id = result.fetchone()[0]
                
                # Insert order items
                for item in items:
                    item["order_id"] = order_id
                    item_sql = text("""
                        INSERT INTO order_items (
                            order_id, product_id, quantity, 
                            unit_price, subtotal
                        ) VALUES (
                            :order_id, :product_id, :quantity, 
                            :unit_price, :subtotal
                        )
                    """)
                    session.execute(item_sql, item)
                
                session.commit()
                
                return order_id
        
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None
