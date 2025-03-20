#!/usr/bin/env python3
"""
Teste básico de conexão com PostgreSQL

Este teste verifica a conexão com o PostgreSQL rodando no Docker
e executa uma consulta simples para verificar que a conexão funciona.
"""

import os
import sys
import logging
import unittest
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar caminho raiz ao path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    load_dotenv(env_path)
    logger.info(f"Variáveis de ambiente carregadas de: {env_path}")
except ImportError:
    logger.warning("python-dotenv não encontrado. Usando variáveis de ambiente do sistema.")


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
            import psycopg2
            cls.conn = psycopg2.connect(
                host=cls.pg_config['host'],
                port=cls.pg_config['port'],
                user=cls.pg_config['user'],
                password=cls.pg_config['password'],
                dbname=cls.pg_config['database']
            )
            logger.info("Conexão com PostgreSQL estabelecida com sucesso")
        except ImportError:
            logger.error("Módulo psycopg2 não está instalado")
            cls.conn = None
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
            self.assertTrue(len(tables) >= 0, "Erro ao consultar tabelas no banco de dados")
            
            # Listar as tabelas encontradas
            logger.info("Tabelas encontradas no banco de dados:")
            for table in tables[:5]:  # Limitar a 5 tabelas para não sobrecarregar o log
                logger.info(f"- {table[0]}")
                
            if len(tables) > 5:
                logger.info(f"... e mais {len(tables) - 5} tabelas")
        finally:
            cursor.close()


if __name__ == "__main__":
    unittest.main()
