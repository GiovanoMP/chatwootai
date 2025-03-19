"""
Teste básico de conexão com PostgreSQL

Este teste verifica a conexão com o PostgreSQL rodando no Docker
e executa uma consulta simples para verificar que a conexão funciona.
"""

import os
import sys
import logging
import psycopg2
import unittest

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar caminho raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestPostgresConnection(unittest.TestCase):
    """Testes básicos de conexão com PostgreSQL"""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para os testes"""
        # Configurações do PostgreSQL
        cls.pg_config = {
            'host': os.environ.get('POSTGRES_HOST', 'localhost'),
            'port': os.environ.get('POSTGRES_PORT', '5433'),
            'user': os.environ.get('POSTGRES_USER', 'postgres'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
            'database': os.environ.get('POSTGRES_DB', 'chatwootai')
        }
        
        logger.info(f"Configuração PostgreSQL: {cls.pg_config}")
        
        # Testar conexão
        try:
            cls.conn = psycopg2.connect(
                host=cls.pg_config['host'],
                port=cls.pg_config['port'],
                user=cls.pg_config['user'],
                password=cls.pg_config['password'],
                database=cls.pg_config['database']
            )
            logger.info("Conexão com PostgreSQL estabelecida com sucesso")
        except Exception as e:
            logger.error(f"Erro ao conectar ao PostgreSQL: {str(e)}")
            cls.conn = None
            raise
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes"""
        if cls.conn:
            cls.conn.close()
            logger.info("Conexão com PostgreSQL encerrada")
    
    def test_simple_query(self):
        """Teste de consulta simples no PostgreSQL"""
        if not self.conn:
            self.skipTest("Conexão com PostgreSQL não disponível")
        
        # Criar um cursor
        cursor = self.conn.cursor()
        
        try:
            # Executar uma consulta simples
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            
            # Verificar o resultado
            self.assertIsNotNone(result, "A consulta não retornou resultados")
            self.assertEqual(result[0], 1, "O resultado da consulta não é o esperado")
            
            logger.info("Consulta simples executada com sucesso")
        finally:
            cursor.close()
    
    def test_list_tables(self):
        """Teste para listar tabelas no banco de dados"""
        if not self.conn:
            self.skipTest("Conexão com PostgreSQL não disponível")
        
        # Criar um cursor
        cursor = self.conn.cursor()
        
        try:
            # Consulta para listar todas as tabelas do schema public
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            
            # Verificar se existem tabelas
            self.assertTrue(len(tables) > 0, "Nenhuma tabela encontrada no banco de dados")
            
            # Listar as tabelas encontradas
            logger.info("Tabelas encontradas no banco de dados:")
            for table in tables:
                logger.info(f"- {table[0]}")
        finally:
            cursor.close()


if __name__ == "__main__":
    unittest.main()
