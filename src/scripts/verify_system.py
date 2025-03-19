#!/usr/bin/env python3
"""
Script para verificar o sistema e seus componentes.
Executa uma série de testes para garantir que todos os serviços estão funcionando corretamente.
"""

import os
import sys
import logging
import json
import time
from datetime import datetime
from tabulate import tabulate
from pathlib import Path

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    # Carregar variáveis de ambiente do arquivo .env no diretório raiz do projeto
    dotenv_path = Path(__file__).resolve().parents[2] / '.env'
    load_dotenv(dotenv_path)
    print(f"Carregando variáveis de ambiente de: {dotenv_path}")
    print(f"DEV_MODE = {os.environ.get('DEV_MODE', 'Não definido')}")
except ImportError:
    print("Pacote python-dotenv não instalado. Variáveis de ambiente não serão carregadas do arquivo .env")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SystemVerifier")

# Adicionar diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar os serviços
from services.data.data_service_hub import DataServiceHub

class SystemVerifier:
    """Classe para verificar o sistema e seus componentes."""
    
    def __init__(self):
        """Inicializa o verificador do sistema."""
        logger.info("Inicializando verificador do sistema...")
        
        # Forçar o recarregamento das variáveis de ambiente para garantir valores corretos
        try:
            dotenv_path = Path(__file__).resolve().parents[2] / '.env'
            load_dotenv(dotenv_path, override=True)
            logger.info(f"Recarregando variáveis de ambiente de: {dotenv_path}")
            logger.info(f"REDIS_URL: {os.environ.get('REDIS_URL')}")
            logger.info(f"REDIS_HOST: {os.environ.get('REDIS_HOST')}")
        except Exception as e:
            logger.error(f"Erro ao recarregar variáveis de ambiente: {str(e)}")
        
        # Inicializar o hub após recarregar as variáveis de ambiente
        self.hub = DataServiceHub()
        self.success_count = 0
        self.failure_count = 0
    
    def run_all_checks(self):
        """Executa todas as verificações disponíveis."""
        logger.info("Iniciando verificação completa do sistema...")
        
        # Verificar tabelas do banco de dados
        logger.info("Verificando as tabelas existentes no banco de dados...")
        tables = self.list_all_tables()
        
        # Lista de verificações a serem executadas
        checks = [
            self.check_database_connection,
            self.check_cache_connection,
            self.check_product_service,
            self.check_customer_service,
            self.check_conversation_context_service,
            self.check_conversation_analytics_service,
        ]
        
        # Executar cada verificação
        results = []
        start_time = time.time()
        
        for check in checks:
            check_name = check.__name__.replace('check_', '').replace('_', ' ').title()
            try:
                success, message = check()
                status = "✅ PASSOU" if success else "❌ FALHOU"
                if success:
                    self.success_count += 1
                else:
                    self.failure_count += 1
            except Exception as e:
                success = False
                message = f"Erro: {str(e)}"
                status = "❌ FALHOU"
                self.failure_count += 1
            
            results.append([check_name, status, message])
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Exibir resultados
        print("\n" + "=" * 80)
        print(f"RESULTADOS DA VERIFICAÇÃO DO SISTEMA ({duration:.2f}s)")
        print("=" * 80)
        
        print(tabulate(results, headers=["Verificação", "Status", "Mensagem"], tablefmt="fancy_grid"))
        
        print("\n" + "=" * 80)
        print(f"RESUMO: {self.success_count} verificações passaram, {self.failure_count} falharam")
        print("=" * 80 + "\n")
        
        return self.failure_count == 0
    
    def check_database_connection(self):
        """Verifica a conexão com o banco de dados."""
        # Exibir informações de diagnóstico
        logger.info(f"Modo de desenvolvimento: {self.hub.dev_mode}")
        logger.info(f"Conexão SQLite: {'Disponível' if self.hub.sqlite_conn else 'Não disponível'}")
        logger.info(f"Conexão PostgreSQL: {'Disponível' if self.hub.pg_conn else 'Não disponível'}")
        
        # Verificar as variáveis de ambiente relacionadas ao banco de dados
        logger.info(f"Variáveis de ambiente para configuração de banco de dados:")
        logger.info(f"  DEV_MODE: {os.environ.get('DEV_MODE', 'Não definido')}")
        logger.info(f"  POSTGRES_HOST: {os.environ.get('POSTGRES_HOST', 'Não definido')}")
        logger.info(f"  POSTGRES_PORT: {os.environ.get('POSTGRES_PORT', 'Não definido')}")
        logger.info(f"  POSTGRES_DB: {os.environ.get('POSTGRES_DB', 'Não definido')}")
        logger.info(f"  DATABASE_URL: {os.environ.get('DATABASE_URL', 'Não definido')}")
        logger.info(f"  SQLITE_DB_PATH: {os.environ.get('SQLITE_DB_PATH', 'Não definido')}")
        
        # Verificar se estamos em modo de desenvolvimento com SQLite
        if self.hub.dev_mode and self.hub.sqlite_conn:
            try:
                # Verificar se podemos executar uma consulta simples no SQLite
                result = self.hub.execute_query("SELECT 1 as test", {})
                if result and len(result) > 0 and result[0]['test'] == 1:
                    return True, "Conexão com SQLite está funcionando corretamente (modo de desenvolvimento)"
                else:
                    return False, "Falha ao executar consulta de teste no SQLite"
            except Exception as e:
                return False, f"Erro ao executar consulta no SQLite: {str(e)}"
        # Verificar conexão PostgreSQL (modo produção)
        elif self.hub.pg_conn:
            try:
                # Verificar se podemos executar uma consulta simples
                result = self.hub.execute_query("SELECT 1 as test", {})
                if result and len(result) > 0 and result[0]['test'] == 1:
                    return True, "Conexão com PostgreSQL está funcionando corretamente"
                else:
                    return False, "Falha ao executar consulta de teste no PostgreSQL"
            except Exception as e:
                return False, f"Erro ao executar consulta no PostgreSQL: {str(e)}"
        else:
            return False, "Nenhuma conexão com banco de dados disponível (nem SQLite nem PostgreSQL)"
    
    def check_cache_connection(self):
        """Verifica a conexão com o cache Redis."""
        # Exibir informações de diagnóstico
        logger.info(f"Conexão Redis: {'Disponível' if hasattr(self.hub, 'redis_client') and self.hub.redis_client else 'Não disponível'}")
        
        # Verificar as variáveis de ambiente relacionadas ao Redis
        logger.info(f"Variáveis de ambiente para configuração de Redis:")
        logger.info(f"  REDIS_URL: {os.environ.get('REDIS_URL', 'Não definido')}")
        logger.info(f"  REDIS_HOST: {os.environ.get('REDIS_HOST', 'Não definido')}")
        logger.info(f"  REDIS_PORT: {os.environ.get('REDIS_PORT', 'Não definido')}")
        logger.info(f"  REDIS_DB: {os.environ.get('REDIS_DB', 'Não definido')}")
        
        # Em modo de desenvolvimento, não requeremos Redis
        if self.hub.dev_mode:
            return True, "Cache em memória local sendo usado no modo de desenvolvimento"
            
        # Em modo de produção, verificamos o Redis
        if not hasattr(self.hub, 'redis_client') or not self.hub.redis_client:  # Verificar se o atributo existe
            return False, "Conexão com Redis não está disponível"
        
        try:
            # Verificar se podemos realizar operações de cache
            test_key = "test_connection_" + datetime.now().strftime("%Y%m%d%H%M%S")
            test_value = "connection_test_value"
            
            # Definir valor
            self.hub.redis_client.set(test_key, test_value, ex=60)  # Expira em 60 segundos
            
            # Recuperar valor - verifica se já vem como string (devido a decode_responses=True)
            retrieved_value = self.hub.redis_client.get(test_key)
            
            if isinstance(retrieved_value, bytes):
                retrieved_value = retrieved_value.decode('utf-8')
                
            if retrieved_value == test_value:
                return True, "Conexão com Redis está funcionando corretamente"
            else:
                return False, f"Falha ao recuperar valor de teste do Redis: esperado '{test_value}', obtido '{retrieved_value}'"
        except Exception as e:
            return False, f"Erro ao testar operações no Redis: {str(e)}"
    
    def check_product_service(self):
        """Verifica o serviço de produtos."""
        if "ProductDataService" not in self.hub.services:
            return False, "Serviço de produtos não está registrado no hub"
        
        try:
            # Verificar se há produtos no banco
            product_count_query = "SELECT COUNT(*) as count FROM products"
            result = self.hub.execute_query(product_count_query, {})
            
            if not result or len(result) == 0:
                return False, "Não foi possível contar produtos no banco de dados"
            
            product_count = result[0]['count']
            
            if product_count == 0:
                return False, "Nenhum produto encontrado no banco de dados"
            
            # Buscar um produto para testar o serviço
            random_product_query = "SELECT id FROM products ORDER BY RANDOM() LIMIT 1"
            product_result = self.hub.execute_query(random_product_query, {})
            
            if not product_result or len(product_result) == 0:
                return False, "Não foi possível obter um produto aleatório para testes"
            
            product_id = product_result[0]['id']
            
            # Testar obtenção de produto pelo serviço
            product = self.hub.services["ProductDataService"].get_by_id(product_id)
            
            if not product:
                return False, f"Não foi possível obter o produto com ID {product_id}"
            
            # Testar busca de produtos
            search_results = self.hub.services["ProductDataService"].search_by_text(
                query_text="produto",  # Texto de busca genérico
                limit=5,
                offset=0
            )
            
            if not search_results or len(search_results) == 0:
                return False, "A busca de produtos não retornou resultados"
            
            return True, f"Serviço de produtos está funcionando corretamente. {product_count} produtos no banco."
        except Exception as e:
            return False, f"Erro ao testar o serviço de produtos: {str(e)}"
    
    def check_customer_service(self):
        """Verifica o serviço de clientes."""
        if "CustomerDataService" not in self.hub.services:
            return False, "Serviço de clientes não está registrado no hub"
        
        try:
            # Verificar se há clientes no banco
            customer_count_query = "SELECT COUNT(*) as count FROM customers"
            result = self.hub.execute_query(customer_count_query, {})
            
            if not result or len(result) == 0:
                return False, "Não foi possível contar clientes no banco de dados"
            
            customer_count = result[0]['count']
            
            if customer_count == 0:
                return False, "Nenhum cliente encontrado no banco de dados"
            
            # Buscar um cliente para testar o serviço
            random_customer_query = "SELECT id FROM customers ORDER BY RANDOM() LIMIT 1"
            customer_result = self.hub.execute_query(random_customer_query, {})
            
            if not customer_result or len(customer_result) == 0:
                return False, "Não foi possível obter um cliente aleatório para testes"
            
            customer_id = customer_result[0]['id']
            
            # Testar obtenção de cliente pelo serviço
            customer = self.hub.services["CustomerDataService"].get_by_id(customer_id)
            
            if not customer:
                return False, f"Não foi possível obter o cliente com ID {customer_id}"
            
            # Testar obtenção de preferências
            preferences = self.hub.services["CustomerDataService"].get_preferences(customer_id)
            
            # Testar obtenção de endereços
            addresses = self.hub.services["CustomerDataService"].get_addresses(customer_id)
            
            return True, f"Serviço de clientes está funcionando corretamente. {customer_count} clientes no banco."
        except Exception as e:
            return False, f"Erro ao testar o serviço de clientes: {str(e)}"
    
    def check_conversation_context_service(self):
        """Verifica o serviço de contexto de conversas."""
        if "ConversationContextService" not in self.hub.services:
            return False, "Serviço de contexto de conversas não está registrado no hub"
        
        try:
            # Verificar se há conversas no banco
            context_count_query = "SELECT COUNT(*) as count FROM conversation_contexts"
            result = self.hub.execute_query(context_count_query, {})
            
            if not result or len(result) == 0:
                return False, "Não foi possível contar contextos de conversa no banco de dados"
            
            context_count = result[0]['count']
            
            if context_count == 0:
                return False, "Nenhum contexto de conversa encontrado no banco de dados"
            
            # Buscar uma conversa para testar o serviço
            random_context_query = "SELECT conversation_id FROM conversation_contexts ORDER BY RANDOM() LIMIT 1"
            context_result = self.hub.execute_query(random_context_query, {})
            
            if not context_result or len(context_result) == 0:
                return False, "Não foi possível obter uma conversa aleatória para testes"
            
            conversation_id = context_result[0]['conversation_id']
            
            # Testar obtenção de contexto pelo serviço
            context = self.hub.services["ConversationContextService"].get_context(conversation_id)
            
            if not context:
                return False, f"Não foi possível obter o contexto da conversa {conversation_id}"
            
            # Testar obtenção de mensagens
            messages = self.hub.services["ConversationContextService"].get_messages(conversation_id)
            
            # Garantir que messages é uma lista e não uma string JSON
            if isinstance(messages, str):
                try:
                    messages = json.loads(messages)
                except json.JSONDecodeError:
                    return False, f"Erro ao decodificar mensagens da conversa {conversation_id}"
            
            # Testar obtenção de variáveis
            variables = self.hub.services["ConversationContextService"].get_variables(conversation_id)
            
            # Garantir que variables é um dicionário e não uma string JSON
            if isinstance(variables, str):
                try:
                    variables = json.loads(variables)
                except json.JSONDecodeError:
                    return False, f"Erro ao decodificar variáveis da conversa {conversation_id}"
            
            return True, f"Serviço de contexto de conversas está funcionando corretamente. {context_count} conversas no banco."
        except Exception as e:
            return False, f"Erro ao testar o serviço de contexto de conversas: {str(e)}"
    
    def list_all_tables(self):
        """Lista todas as tabelas existentes no banco de dados PostgreSQL."""
        if not hasattr(self.hub, 'pg_conn') or not self.hub.pg_conn:
            logger.warning("Nenhuma conexão PostgreSQL disponível para listar tabelas.")
            return None
            
        try:
            # Consulta para listar todas as tabelas no esquema public (padrão)
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
            
            tables = self.hub.execute_query(query, {})
            
            if not tables:
                logger.warning("Nenhuma tabela encontrada no banco de dados PostgreSQL.")
                return None
                
            # Verificar especificamente a tabela conversation_snippets
            snippet_table_exists = any(table['table_name'] == 'conversation_snippets' for table in tables)
            if snippet_table_exists:
                logger.info("✅ Tabela 'conversation_snippets' encontrada no banco de dados.")
            else:
                logger.warning("⚠️ Tabela 'conversation_snippets' NÃO encontrada no banco de dados.")
            
            # Formatar e exibir informações sobre as tabelas
            logger.info(f"Total de tabelas encontradas: {len(tables)}")
            return tables
                
        except Exception as e:
            logger.error(f"Erro ao listar tabelas do PostgreSQL: {str(e)}")
            return None
    
    def check_conversation_analytics_service(self):
        """Verifica o serviço de análise de conversas."""
        if "ConversationAnalyticsService" not in self.hub.services:
            return False, "Serviço de análise de conversas não está registrado no hub"
        
        try:
            # Buscar uma conversa para testar o serviço
            random_context_query = """
            SELECT cc.conversation_id, cc.customer_id, cc.metadata
            FROM conversation_contexts cc
            JOIN conversation_messages cm ON cc.conversation_id = cm.conversation_id
            GROUP BY cc.conversation_id, cc.customer_id, cc.metadata
            HAVING COUNT(cm.conversation_id) >= 3
            ORDER BY RANDOM() LIMIT 1
            """
            context_result = self.hub.execute_query(random_context_query, {})
            
            if not context_result or len(context_result) == 0:
                return False, "Não foi possível obter uma conversa adequada para testes de análise"
            
            conversation_id = context_result[0]['conversation_id']
            customer_id = context_result[0]['customer_id']
            metadata = json.loads(context_result[0]['metadata']) if context_result[0]['metadata'] else {}
            channel = metadata.get('channel', 'unknown')
            
            # Obter mensagens da conversa
            message_query = """
            SELECT sender_id, sender_type, content, created_at 
            FROM conversation_messages 
            WHERE conversation_id = %(conversation_id)s
            ORDER BY created_at
            """
            message_result = self.hub.execute_query(message_query, {"conversation_id": conversation_id})
            
            if not message_result or len(message_result) < 3:
                return False, "Não há mensagens suficientes para análise na conversa selecionada"
            
            # Formatar mensagens para análise
            messages = []
            for msg in message_result:
                messages.append({
                    "sender_id": msg['sender_id'],
                    "sender_type": msg['sender_type'],
                    "content": msg['content'],
                    "timestamp": msg['created_at'].isoformat() if hasattr(msg['created_at'], 'isoformat') else str(msg['created_at'])
                })
            
            # Testar análise de conversa
            summary = self.hub.services["ConversationAnalyticsService"].store_conversation_summary(
                conversation_id, customer_id, channel, messages
            )
            
            if not summary:
                return False, "Falha ao gerar e armazenar análise da conversa"
            
            # Verificar insights armazenados
            insights = self.hub.services["ConversationAnalyticsService"].get_conversation_insights(conversation_id)
            
            # Garantir que insights é um dicionário e não uma string JSON
            if isinstance(insights, str):
                try:
                    insights = json.loads(insights)
                except json.JSONDecodeError:
                    return False, f"Erro ao decodificar insights da conversa {conversation_id}"
            
            if not insights:
                return False, "Não foi possível recuperar insights da conversa após análise"
            
            return True, "Serviço de análise de conversas está funcionando corretamente"
        except Exception as e:
            return False, f"Erro ao testar o serviço de análise de conversas: {str(e)}"

def main():
    """Função principal."""
    verifier = SystemVerifier()
    success = verifier.run_all_checks()
    
    if success:
        logger.info("Todas as verificações foram concluídas com sucesso!")
        sys.exit(0)
    else:
        logger.error("Algumas verificações falharam. Verifique os detalhes acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()
