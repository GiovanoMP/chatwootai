"""
Serviço de Monitoramento de Alterações no Banco de Dados.
Este serviço monitora alterações no PostgreSQL e notifica o DataSyncService
para manter o Qdrant atualizado.
"""
import os
import json
import logging
import asyncio
import asyncpg
from typing import Optional, Callable, Dict, Any

from src.services.data_sync_service import DataSyncService

class DatabaseChangeListener:
    """
    Serviço para monitoramento de alterações no banco de dados PostgreSQL.
    
    Este serviço utiliza o sistema de notificações do PostgreSQL para detectar
    alterações em tempo real e notificar o DataSyncService para manter o Qdrant
    atualizado.
    """
    
    def __init__(
        self, 
        data_sync_service: DataSyncService,
        db_connection_string: Optional[str] = None
    ):
        """
        Inicializa o serviço de monitoramento de alterações no banco de dados.
        
        Args:
            data_sync_service: Instância do DataSyncService para sincronização.
            db_connection_string: String de conexão com o PostgreSQL. Se não fornecida,
                                 será buscada na variável de ambiente DATABASE_URL.
        """
        self.data_sync_service = data_sync_service
        self.db_connection_string = db_connection_string or os.environ.get("DATABASE_URL")
        if not self.db_connection_string:
            raise ValueError("String de conexão com o PostgreSQL não fornecida e não encontrada nas variáveis de ambiente")
            
        self.running = False
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Serviço de Monitoramento de Alterações no Banco de Dados inicializado")
        
    async def start(self):
        """
        Inicia o listener para mudanças no banco de dados.
        
        Este método configura os triggers necessários no PostgreSQL e inicia
        o monitoramento de notificações.
        """
        self.running = True
        
        try:
            # Estabelecer conexão com o PostgreSQL
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Configurar triggers no PostgreSQL (se ainda não existirem)
            await self._setup_triggers(conn)
            
            # Inscrever-se para receber notificações
            await conn.add_listener('product_changes', self._on_product_change)
            await conn.add_listener('business_rule_changes', self._on_business_rule_change)
            
            self.logger.info("Listener de alterações no banco de dados iniciado com sucesso")
            
            # Manter a conexão aberta enquanto o serviço estiver rodando
            while self.running:
                await asyncio.sleep(1)
                
            # Limpar ao parar
            await conn.remove_listener('product_changes', self._on_product_change)
            await conn.remove_listener('business_rule_changes', self._on_business_rule_change)
            await conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar listener de alterações no banco de dados: {e}")
            self.running = False
            
    def stop(self):
        """
        Para o listener de alterações no banco de dados.
        """
        self.running = False
        self.logger.info("Listener de alterações no banco de dados parado")
    
    async def _on_product_change(self, connection, pid, channel, payload):
        """
        Callback para mudanças em produtos.
        
        Este método é chamado automaticamente quando uma notificação de alteração
        em produto é recebida do PostgreSQL.
        
        Args:
            connection: Conexão com o PostgreSQL.
            pid: ID do processo que gerou a notificação.
            channel: Canal de notificação.
            payload: Dados da notificação em formato JSON.
        """
        try:
            # Converter o payload para um dicionário
            data = json.loads(payload)
            product_id = data['id']
            operation = data['operation']  # INSERT, UPDATE, DELETE
            
            self.logger.info(f"Notificação recebida: {operation} em produto {product_id}")
            
            # Processar a alteração de acordo com a operação
            if operation == 'DELETE':
                # Remover do Qdrant
                await asyncio.to_thread(self.data_sync_service.delete_product, product_id)
            else:
                # Sincronizar com Qdrant (INSERT ou UPDATE)
                await asyncio.to_thread(self.data_sync_service.sync_product, product_id)
                
        except Exception as e:
            self.logger.error(f"Erro ao processar mudança de produto: {e}")
    
    async def _on_business_rule_change(self, connection, pid, channel, payload):
        """
        Callback para mudanças em regras de negócio.
        
        Este método é chamado automaticamente quando uma notificação de alteração
        em regra de negócio é recebida do PostgreSQL.
        
        Args:
            connection: Conexão com o PostgreSQL.
            pid: ID do processo que gerou a notificação.
            channel: Canal de notificação.
            payload: Dados da notificação em formato JSON.
        """
        try:
            # Converter o payload para um dicionário
            data = json.loads(payload)
            rule_id = data['id']
            operation = data['operation']  # INSERT, UPDATE, DELETE
            
            self.logger.info(f"Notificação recebida: {operation} em regra de negócio {rule_id}")
            
            # Processar a alteração de acordo com a operação
            if operation == 'DELETE':
                # Remover do Qdrant
                await asyncio.to_thread(self.data_sync_service.delete_business_rule, rule_id)
            else:
                # Sincronizar com Qdrant (INSERT ou UPDATE)
                await asyncio.to_thread(self.data_sync_service.sync_business_rule, rule_id)
                
        except Exception as e:
            self.logger.error(f"Erro ao processar mudança de regra de negócio: {e}")
        
    async def _setup_triggers(self, conn):
        """
        Configura triggers no PostgreSQL para notificar sobre mudanças.
        
        Este método cria as funções e triggers necessários no PostgreSQL para
        que o sistema de notificações funcione corretamente.
        
        Args:
            conn: Conexão com o PostgreSQL.
        """
        try:
            # Criar função para notificação de produtos
            await conn.execute("""
                CREATE OR REPLACE FUNCTION notify_product_changes()
                RETURNS trigger AS $$
                BEGIN
                    PERFORM pg_notify(
                        'product_changes',
                        json_build_object(
                            'operation', TG_OP,
                            'id', CASE TG_OP WHEN 'DELETE' THEN OLD.id ELSE NEW.id END
                        )::text
                    );
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # Verificar se o trigger de produtos já existe
            trigger_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_trigger 
                    WHERE tgname = 'products_change_trigger'
                );
            """)
            
            if not trigger_exists:
                # Criar trigger para produtos
                await conn.execute("""
                    CREATE TRIGGER products_change_trigger
                    AFTER INSERT OR UPDATE OR DELETE ON products
                    FOR EACH ROW EXECUTE FUNCTION notify_product_changes();
                """)
                self.logger.info("Trigger para produtos criado com sucesso")
            else:
                self.logger.info("Trigger para produtos já existe")
                
            # Criar função para notificação de regras de negócio
            await conn.execute("""
                CREATE OR REPLACE FUNCTION notify_business_rule_changes()
                RETURNS trigger AS $$
                BEGIN
                    PERFORM pg_notify(
                        'business_rule_changes',
                        json_build_object(
                            'operation', TG_OP,
                            'id', CASE TG_OP WHEN 'DELETE' THEN OLD.id ELSE NEW.id END
                        )::text
                    );
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # Verificar se o trigger de regras de negócio já existe
            trigger_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_trigger 
                    WHERE tgname = 'business_rules_change_trigger'
                );
            """)
            
            if not trigger_exists:
                # Criar trigger para regras de negócio
                await conn.execute("""
                    CREATE TRIGGER business_rules_change_trigger
                    AFTER INSERT OR UPDATE OR DELETE ON business_rules
                    FOR EACH ROW EXECUTE FUNCTION notify_business_rule_changes();
                """)
                self.logger.info("Trigger para regras de negócio criado com sucesso")
            else:
                self.logger.info("Trigger para regras de negócio já existe")
                
        except Exception as e:
            self.logger.error(f"Erro ao configurar triggers no PostgreSQL: {e}")
            raise
