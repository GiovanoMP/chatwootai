-- Script para criar tabelas que simulam o módulo CRM do Odoo
-- Este script cria as tabelas necessárias para armazenar o contexto das conversas

-- Tabela de clientes/leads
CREATE TABLE IF NOT EXISTS crm_customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    type VARCHAR(20) NOT NULL DEFAULT 'lead', -- 'lead' ou 'customer'
    status VARCHAR(20) NOT NULL DEFAULT 'new', -- 'new', 'qualified', 'opportunity', 'customer'
    source VARCHAR(50) DEFAULT 'chatwoot',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Índices para busca rápida de clientes
CREATE INDEX IF NOT EXISTS idx_crm_customers_email ON crm_customers(email);
CREATE INDEX IF NOT EXISTS idx_crm_customers_phone ON crm_customers(phone);
CREATE INDEX IF NOT EXISTS idx_crm_customers_status ON crm_customers(status);

-- Tabela de threads de conversas
CREATE TABLE IF NOT EXISTS crm_conversation_threads (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES crm_customers(id) ON DELETE CASCADE,
    conversation_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    domain_id VARCHAR(50),
    metadata JSONB DEFAULT '{}'
);

-- Índices para busca rápida de threads
CREATE INDEX IF NOT EXISTS idx_crm_conversation_threads_customer_id ON crm_conversation_threads(customer_id);
CREATE INDEX IF NOT EXISTS idx_crm_conversation_threads_conversation_id ON crm_conversation_threads(conversation_id);

-- Tabela de mensagens das conversas
CREATE TABLE IF NOT EXISTS crm_conversation_messages (
    id SERIAL PRIMARY KEY,
    thread_id INTEGER NOT NULL REFERENCES crm_conversation_threads(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL, -- 'customer', 'agent', 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Índice para busca rápida de mensagens
CREATE INDEX IF NOT EXISTS idx_crm_conversation_messages_thread_id ON crm_conversation_messages(thread_id);

-- Tabela de contexto das conversas
CREATE TABLE IF NOT EXISTS crm_conversation_contexts (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES crm_customers(id) ON DELETE CASCADE,
    context_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_processed_message_id BIGINT,
    domain_id VARCHAR(50)
);

-- Índices para busca rápida de contextos
CREATE INDEX IF NOT EXISTS idx_crm_conversation_contexts_conversation_id ON crm_conversation_contexts(conversation_id);
CREATE INDEX IF NOT EXISTS idx_crm_conversation_contexts_customer_id ON crm_conversation_contexts(customer_id);

-- Função para atualizar automaticamente o timestamp de atualização
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para atualizar automaticamente os timestamps
CREATE TRIGGER update_crm_customers_updated_at
BEFORE UPDATE ON crm_customers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crm_conversation_threads_updated_at
BEFORE UPDATE ON crm_conversation_threads
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crm_conversation_contexts_updated_at
BEFORE UPDATE ON crm_conversation_contexts
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Inserir alguns dados de exemplo para testes
INSERT INTO crm_customers (name, email, phone, type, status)
VALUES 
    ('João Silva', 'joao.silva@example.com', '11987654321', 'customer', 'customer'),
    ('Maria Oliveira', 'maria.oliveira@example.com', '11912345678', 'lead', 'new'),
    ('Carlos Santos', 'carlos.santos@example.com', '11955556666', 'lead', 'qualified');

-- Comentários explicativos sobre a estrutura
COMMENT ON TABLE crm_customers IS 'Tabela que simula clientes e leads no CRM do Odoo';
COMMENT ON TABLE crm_conversation_threads IS 'Tabela que armazena as threads de conversas vinculadas aos clientes';
COMMENT ON TABLE crm_conversation_messages IS 'Tabela que armazena as mensagens de cada thread de conversa';
COMMENT ON TABLE crm_conversation_contexts IS 'Tabela que armazena o contexto de cada conversa para uso pelos agentes de IA';
