#!/usr/bin/env python3
"""
Script para verificar o esquema do banco de dados PostgreSQL.
Analisa as tabelas existentes e verifica se estão prontas para as funcionalidades do ChatwootAI.
"""

import os
import sys
import json
import logging
from pathlib import Path
from tabulate import tabulate

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
logger = logging.getLogger("DatabaseSchemaChecker")

# Adicionar diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar os serviços
from services.data.data_service_hub import DataServiceHub

class DatabaseSchemaChecker:
    """Classe para verificar o esquema do banco de dados PostgreSQL."""
    
    def __init__(self):
        """Inicializa o verificador de esquema do banco de dados."""
        logger.info("Inicializando verificador de esquema do banco de dados...")
        self.hub = DataServiceHub()
        
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
    
    def list_all_tables(self):
        """Lista todas as tabelas existentes no banco de dados PostgreSQL."""
        if not hasattr(self.hub, 'pg_conn') or not self.hub.pg_conn:
            print("\nNenhuma conexão PostgreSQL disponível para listar tabelas.\n")
            return
            
        try:
            # Consulta para listar todas as tabelas no esquema public (padrão)
            query = """
            SELECT 
                table_name, 
                (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count,
                obj_description(pgc.oid, 'pg_class') as table_comment
            FROM 
                information_schema.tables t
            JOIN 
                pg_class pgc ON pgc.relname = t.table_name
            WHERE 
                table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            ORDER BY 
                table_name;
            """
            
            tables = self.hub.execute_query(query)
            
            if not tables:
                print("\nNenhuma tabela encontrada no banco de dados PostgreSQL.\n")
                return
                
            print("\n" + "=" * 80)
            print("TABELAS EXISTENTES NO BANCO DE DADOS POSTGRESQL")
            print("=" * 80)
            
            # Formatar a saída em formato de tabela
            table_data = []
            for table in tables:
                table_data.append([table['table_name'], table['column_count'], table['table_comment'] or 'Sem descrição'])
                
            print(tabulate(table_data, headers=["Nome da Tabela", "Colunas", "Descrição"], tablefmt="fancy_grid"))
            print("\n")
            
            return tables
                
        except Exception as e:
            print(f"\nErro ao listar tabelas do PostgreSQL: {str(e)}\n")
            return None
    
    def check_required_tables(self, tables=None):
        """Verifica se as tabelas necessárias para as funcionalidades básicas existem."""
        if tables is None:
            tables = self.list_all_tables()
            
        if not tables:
            return
            
        # Verificar tabelas necessárias para a funcionalidade de fragmentos de conversa
        required_tables = [
            'conversations',
            'conversation_messages',
            'conversation_contexts',
            'conversation_snippets',
            'customers',
            'agents',
            'products'
        ]
        
        existing_tables = [t['table_name'] for t in tables]
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print("\nAVISO: As seguintes tabelas necessárias para funcionalidades básicas não foram encontradas:")
            for table in missing_tables:
                print(f"  - {table}")
            print("\n")
            
            print("Você precisará criar estas tabelas para que o sistema funcione corretamente.")
            print("As tabelas podem ser criadas executando o script src/scripts/init_database.py.")
            print("Para mais detalhes, consulte a documentação em docs/DATABASE_SCHEMA.md.")
        else:
            print("\n✅ Todas as tabelas básicas necessárias estão presentes no banco de dados.\n")
        
        return missing_tables
    
    def list_table_columns(self, table_name):
        """Lista as colunas de uma tabela específica."""
        try:
            query = """
            SELECT 
                column_name, 
                data_type, 
                character_maximum_length, 
                column_default,
                is_nullable
            FROM 
                information_schema.columns 
            WHERE 
                table_name = %(table_name)s 
            ORDER BY 
                ordinal_position;
            """
            
            columns = self.hub.execute_query(query, {'table_name': table_name})
            
            if not columns:
                print(f"Nenhuma coluna encontrada para a tabela {table_name}.\n")
                return
                
            print(f"\nColunas da tabela {table_name}:")
            
            # Formatar a saída em formato de tabela
            column_data = []
            for column in columns:
                data_type = column['data_type']
                if column['character_maximum_length']:
                    data_type += f"({column['character_maximum_length']})"
                    
                is_nullable = "Sim" if column['is_nullable'] == "YES" else "Não"
                
                column_data.append([column['column_name'], data_type, column['column_default'] or 'NULL', is_nullable])
                
            print(tabulate(column_data, headers=["Nome da Coluna", "Tipo de Dado", "Valor Padrão", "Null?"], tablefmt="grid"))
            print("\n")
            
            return columns
            
        except Exception as e:
            print(f"Erro ao listar colunas da tabela {table_name}: {str(e)}\n")
            return None
    
    def check_snippet_tables(self):
        """Verifica as tabelas específicas para a funcionalidade de snippets de conversa."""
        print("\n" + "=" * 80)
        print("VERIFICAÇÃO DE TABELAS PARA SNIPPETS DE CONVERSA")
        print("=" * 80)
        
        try:
            # Verificar se a tabela conversation_snippets existe
            if not self.table_exists('conversation_snippets'):
                # Sugerir a criação da tabela
                print("\n❌ A tabela 'conversation_snippets' não existe, mas é necessária para armazenar snippets de conversa.")
                print("Sugestão de criação da tabela:")
                print("""
CREATE TABLE conversation_snippets (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    snippet_text TEXT NOT NULL,
    context_before TEXT,
    context_after TEXT,
    sentiment VARCHAR(20),
    tags JSONB,
    importance_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conv_snippets_conversation_id ON conversation_snippets(conversation_id);
CREATE INDEX idx_conv_snippets_importance ON conversation_snippets(importance_score DESC);
CREATE INDEX idx_conv_snippets_tags ON conversation_snippets USING GIN(tags);
                """)
            else:
                # Verificar se a tabela conversation_snippets tem todos os campos necessários
                snippet_columns = self.list_table_columns('conversation_snippets')
                if snippet_columns:
                    column_names = [c['column_name'] for c in snippet_columns]
                    
                    required_columns = [
                        'id', 'conversation_id', 'snippet_text', 'context_before',
                        'context_after', 'sentiment', 'tags', 'importance_score',
                        'created_at', 'updated_at'
                    ]
                    
                    missing_columns = [c for c in required_columns if c not in column_names]
                    
                    if missing_columns:
                        print(f"\n❌ A tabela 'conversation_snippets' existe, mas faltam as seguintes colunas: {', '.join(missing_columns)}")
                        # Sugerir alterações na tabela
                        alter_statements = []
                        for col in missing_columns:
                            if col == 'tags':
                                alter_statements.append(f"ALTER TABLE conversation_snippets ADD COLUMN {col} JSONB;")
                            elif col == 'importance_score':
                                alter_statements.append(f"ALTER TABLE conversation_snippets ADD COLUMN {col} FLOAT;")
                            elif col in ['created_at', 'updated_at']:
                                alter_statements.append(f"ALTER TABLE conversation_snippets ADD COLUMN {col} TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;")
                            elif col == 'sentiment':
                                alter_statements.append(f"ALTER TABLE conversation_snippets ADD COLUMN {col} VARCHAR(20);")
                            elif col in ['context_before', 'context_after', 'snippet_text']:
                                alter_statements.append(f"ALTER TABLE conversation_snippets ADD COLUMN {col} TEXT;")
                            else:
                                alter_statements.append(f"ALTER TABLE conversation_snippets ADD COLUMN {col} INTEGER;")
                                
                        print("\nSugestão de alterações na tabela:")
                        for stmt in alter_statements:
                            print(stmt)
                    else:
                        print("\n✅ A tabela 'conversation_snippets' existe e tem todas as colunas necessárias.")
            
            # Verificar se a tabela conversations tem os campos necessários
            if self.table_exists('conversations'):
                conversation_columns = self.list_table_columns('conversations')
                if conversation_columns:
                    column_names = [c['column_name'] for c in conversation_columns]
                    
                    # Campos recomendados para a tabela conversations
                    recommended_columns = [
                        'id', 'customer_id', 'agent_id', 'channel', 'status',
                        'started_at', 'ended_at', 'metadata', 'created_at', 'updated_at'
                    ]
                    
                    missing_columns = [c for c in recommended_columns if c not in column_names]
                    
                    if missing_columns:
                        print(f"\n⚠️ A tabela 'conversations' existe, mas seria recomendável ter as seguintes colunas adicionais: {', '.join(missing_columns)}")
                    else:
                        print("\n✅ A tabela 'conversations' tem todas as colunas recomendadas.")
            
            # Verificar se a tabela conversation_messages tem os campos necessários
            if self.table_exists('conversation_messages'):
                message_columns = self.list_table_columns('conversation_messages')
                if message_columns:
                    column_names = [c['column_name'] for c in message_columns]
                    
                    # Campos recomendados para a tabela conversation_messages
                    recommended_columns = [
                        'id', 'conversation_id', 'sender_id', 'sender_type', 'content',
                        'created_at', 'updated_at', 'metadata', 'content_type'
                    ]
                    
                    missing_columns = [c for c in recommended_columns if c not in column_names]
                    
                    if missing_columns:
                        print(f"\n⚠️ A tabela 'conversation_messages' existe, mas seria recomendável ter as seguintes colunas adicionais: {', '.join(missing_columns)}")
                    else:
                        print("\n✅ A tabela 'conversation_messages' tem todas as colunas recomendadas.")
            
        except Exception as e:
            print(f"\nErro ao verificar tabelas para snippets de conversa: {str(e)}\n")
    
    def table_exists(self, table_name):
        """Verifica se uma tabela específica existe."""
        try:
            query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %(table_name)s
            );
            """
            
            result = self.hub.execute_query(query, {'table_name': table_name})
            
            if result and len(result) > 0:
                return result[0]['exists']
            
            return False
        except Exception as e:
            print(f"Erro ao verificar existência da tabela {table_name}: {str(e)}\n")
            return False
    
    def run_all_checks(self):
        """Executa todas as verificações do esquema do banco de dados."""
        print("\n" + "=" * 80)
        print("VERIFICAÇÃO DO ESQUEMA DO BANCO DE DADOS")
        print("=" * 80 + "\n")
        
        # Verificar conexão com o banco de dados
        if not self.check_database_connection():
            print("\nNão foi possível conectar ao banco de dados. Verifique as configurações e tente novamente.\n")
            return
        
        # Listar todas as tabelas
        tables = self.list_all_tables()
        
        # Verificar tabelas necessárias
        missing_tables = self.check_required_tables(tables)
        
        # Verificar tabelas para snippets de conversa
        self.check_snippet_tables()
        
        # Listar tabelas importantes e suas colunas
        important_tables = ['conversation_snippets', 'conversations', 'conversation_messages', 'customers', 'agents']
        for table in important_tables:
            if self.table_exists(table):
                self.list_table_columns(table)
        
        print("\n" + "=" * 80)
        print("CONCLUSÃO DA VERIFICAÇÃO DO BANCO DE DADOS")
        print("=" * 80)
        
        if missing_tables:
            print("\n⚠️ Algumas tabelas necessárias estão faltando no banco de dados.")
            print("Execute o script de inicialização do banco de dados para criar essas tabelas.\n")
        else:
            print("\n✅ O esquema do banco de dados parece estar completo para as funcionalidades básicas.")
            print("O sistema está pronto para armazenar snippets de conversa e outras informações importantes.\n")

def main():
    """Função principal para executar as verificações do esquema do banco de dados."""
    checker = DatabaseSchemaChecker()
    checker.run_all_checks()

if __name__ == "__main__":
    main()
