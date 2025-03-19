#!/usr/bin/env python3
"""
Script para inicializar o banco de dados PostgreSQL com as tabelas necessárias para o ChatwootAI.
Este script lê e executa os arquivos SQL na pasta init-scripts.
"""

import os
import sys
import glob
import logging
from pathlib import Path

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    # Carregar variáveis de ambiente do arquivo .env no diretório raiz do projeto
    dotenv_path = Path(__file__).resolve().parents[2] / '.env'
    load_dotenv(dotenv_path)
    print(f"Carregando variáveis de ambiente de: {dotenv_path}")
except ImportError:
    print("Pacote python-dotenv não instalado. Variáveis de ambiente não serão carregadas do arquivo .env")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DatabaseInitializer")

# Adicionar diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar os serviços
from services.data.data_service_hub import DataServiceHub

class DatabaseInitializer:
    """Classe para inicializar o banco de dados PostgreSQL."""
    
    def __init__(self):
        """Inicializa o inicializador de banco de dados."""
        logger.info("Inicializando inicializador de banco de dados...")
        self.hub = DataServiceHub()
        self.project_root = Path(__file__).resolve().parents[2]
        self.script_dir = self.project_root / 'init-scripts'
        
    def check_database_connection(self):
        """Verifica a conexão com o banco de dados."""
        # Exibir informações de diagnóstico
        logger.info(f"Modo de desenvolvimento: {self.hub.dev_mode}")
        logger.info(f"Conexão PostgreSQL: {'Disponível' if hasattr(self.hub, 'pg_conn') and self.hub.pg_conn else 'Não disponível'}")
        
        # Verificar as variáveis de ambiente relacionadas ao banco de dados
        logger.info(f"Variáveis de ambiente para configuração de banco de dados:")
        logger.info(f"  DEV_MODE: {os.environ.get('DEV_MODE', 'Não definido')}")
        logger.info(f"  POSTGRES_HOST: {os.environ.get('POSTGRES_HOST', 'Não definido')}")
        logger.info(f"  POSTGRES_PORT: {os.environ.get('POSTGRES_PORT', 'Não definido')}")
        logger.info(f"  POSTGRES_DB: {os.environ.get('POSTGRES_DB', 'Não definido')}")
        logger.info(f"  DATABASE_URL: {os.environ.get('DATABASE_URL', 'Não definido')}")
        
        # Verificar conexão PostgreSQL
        if not hasattr(self.hub, 'pg_conn') or not self.hub.pg_conn:
            print("Nenhuma conexão PostgreSQL disponível.")
            return False
        
        try:
            # Verificar se podemos executar uma consulta simples
            result = self.hub.execute_query("SELECT 1 as test", {})
            if result and len(result) > 0 and result[0]['test'] == 1:
                print("✅ Conexão com PostgreSQL está funcionando corretamente")
                return True
            else:
                print("❌ Falha ao executar consulta de teste no PostgreSQL")
                return False
        except Exception as e:
            print(f"❌ Erro ao executar consulta no PostgreSQL: {str(e)}")
            return False
    
    def read_sql_files(self):
        """Lê todos os arquivos SQL no diretório init-scripts."""
        sql_files = sorted(glob.glob(str(self.script_dir / '*.sql')))
        
        if not sql_files:
            logger.error(f"Nenhum arquivo SQL encontrado no diretório {self.script_dir}")
            return []
        
        logger.info(f"Encontrados {len(sql_files)} arquivos SQL para executar:")
        for sql_file in sql_files:
            logger.info(f"  - {os.path.basename(sql_file)}")
        
        return sql_files
    
    def execute_sql_file(self, sql_file):
        """Executa o conteúdo de um arquivo SQL."""
        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
                
            # Executar o conteúdo do arquivo SQL
            print(f"\nExecutando arquivo SQL: {os.path.basename(sql_file)}")
            
            # Usar a conexão direta para executar instruções SQL complexas
            # que podem conter múltiplos statements
            with self.hub.pg_conn.cursor() as cursor:
                cursor.execute(sql_content)
                
            self.hub.pg_conn.commit()
            print(f"✅ Arquivo SQL executado com sucesso: {os.path.basename(sql_file)}")
            return True
            
        except Exception as e:
            self.hub.pg_conn.rollback()
            print(f"❌ Erro ao executar arquivo SQL {os.path.basename(sql_file)}: {str(e)}")
            return False
    
    def list_tables(self):
        """Lista as tabelas existentes no banco de dados."""
        try:
            query = """
            SELECT 
                table_name, 
                (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
            FROM 
                information_schema.tables t
            WHERE 
                table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            ORDER BY 
                table_name;
            """
            
            tables = self.hub.execute_query(query)
            
            print("\n=== Tabelas existentes no banco de dados ===")
            if not tables:
                print("Nenhuma tabela encontrada.")
                return []
            
            for table in tables:
                print(f"  - {table['table_name']} ({table['column_count']} colunas)")
                
            return [t['table_name'] for t in tables]
            
        except Exception as e:
            print(f"Erro ao listar tabelas: {str(e)}")
            return []
    
    def initialize_database(self):
        """Inicializa o banco de dados executando todos os scripts SQL."""
        print("\n" + "=" * 80)
        print("INICIALIZAÇÃO DO BANCO DE DADOS POSTGRESQL")
        print("=" * 80 + "\n")
        
        # Verificar conexão com o banco de dados
        if not self.check_database_connection():
            print("\nNão foi possível conectar ao banco de dados. Verifique as configurações e tente novamente.\n")
            return False
        
        # Listar tabelas existentes antes da inicialização
        existing_tables_before = self.list_tables()
        
        # Ler arquivos SQL
        sql_files = self.read_sql_files()
        if not sql_files:
            print("\nNenhum arquivo SQL encontrado para executar.\n")
            return False
        
        # Executar arquivos SQL
        success_count = 0
        failure_count = 0
        
        for sql_file in sql_files:
            if self.execute_sql_file(sql_file):
                success_count += 1
            else:
                failure_count += 1
        
        # Listar tabelas após a inicialização
        print("\n" + "=" * 80)
        print(f"RESULTADO DA INICIALIZAÇÃO: {success_count} sucesso(s), {failure_count} falha(s)")
        print("=" * 80 + "\n")
        
        existing_tables_after = self.list_tables()
        
        # Mostrar novas tabelas criadas
        new_tables = [t for t in existing_tables_after if t not in existing_tables_before]
        if new_tables:
            print("\nNovas tabelas criadas:")
            for table in new_tables:
                print(f"  - {table}")
        
        return failure_count == 0

def main():
    """Função principal para inicializar o banco de dados."""
    initializer = DatabaseInitializer()
    success = initializer.initialize_database()
    
    if success:
        print("\n✅ Banco de dados inicializado com sucesso!")
        sys.exit(0)
    else:
        print("\n⚠️ Inicialização do banco de dados concluída com avisos ou erros.")
        sys.exit(1)

if __name__ == "__main__":
    main()
