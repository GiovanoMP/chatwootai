-- Criação da tabela conversation_snippets para armazenar trechos importantes de conversas
-- Esta tabela é essencial para implementar a funcionalidade de análise de conversas

-- Verificar se a tabela conversation_snippets já existe
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'conversation_snippets') THEN
        CREATE TABLE conversation_snippets (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER NOT NULL,
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

        -- Comentário da tabela
        COMMENT ON TABLE conversation_snippets IS 'Armazena trechos importantes de conversas para análise posterior';
        
        -- Comentários das colunas
        COMMENT ON COLUMN conversation_snippets.snippet_text IS 'Texto do trecho importante da conversa';
        COMMENT ON COLUMN conversation_snippets.context_before IS 'Contexto anterior ao trecho (opcional)';
        COMMENT ON COLUMN conversation_snippets.context_after IS 'Contexto posterior ao trecho (opcional)';
        COMMENT ON COLUMN conversation_snippets.sentiment IS 'Análise de sentimento do trecho (positivo, negativo, neutro)';
        COMMENT ON COLUMN conversation_snippets.tags IS 'Tags ou categorias associadas ao trecho em formato JSON';
        COMMENT ON COLUMN conversation_snippets.importance_score IS 'Pontuação de importância do trecho (0.0 a 1.0)';
        
        RAISE NOTICE 'Tabela conversation_snippets criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela conversation_snippets já existe';
    END IF;
END $$;

-- Verificar se a tabela conversations existe, caso contrário, criá-la
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'conversations') THEN
        CREATE TABLE conversations (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
            agent_id INTEGER,
            channel VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'open',
            started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP WITH TIME ZONE,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX idx_conversations_customer_id ON conversations(customer_id);
        CREATE INDEX idx_conversations_agent_id ON conversations(agent_id);
        CREATE INDEX idx_conversations_status ON conversations(status);
        CREATE INDEX idx_conversations_metadata ON conversations USING GIN(metadata);
        
        -- Comentário da tabela
        COMMENT ON TABLE conversations IS 'Armazena informações sobre conversas entre clientes e agentes';
        
        -- Função para atualizar o timestamp de updated_at automaticamente
        CREATE OR REPLACE FUNCTION update_conversation_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        -- Trigger para atualizar o timestamp quando uma conversa for modificada
        CREATE TRIGGER update_conversation_timestamp
        BEFORE UPDATE ON conversations
        FOR EACH ROW
        EXECUTE FUNCTION update_conversation_timestamp();
        
        RAISE NOTICE 'Tabela conversations criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela conversations já existe';
    END IF;
END $$;

-- Verificar se a tabela conversation_messages existe, caso contrário, criá-la
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'conversation_messages') THEN
        CREATE TABLE conversation_messages (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            sender_id INTEGER,
            sender_type VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            content_type VARCHAR(50) DEFAULT 'text',
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX idx_conv_messages_conversation_id ON conversation_messages(conversation_id);
        CREATE INDEX idx_conv_messages_created_at ON conversation_messages(created_at);
        CREATE INDEX idx_conv_messages_sender ON conversation_messages(sender_id, sender_type);
        CREATE INDEX idx_conv_messages_metadata ON conversation_messages USING GIN(metadata);
        
        -- Comentário da tabela
        COMMENT ON TABLE conversation_messages IS 'Armazena mensagens individuais dentro de uma conversa';
        
        -- Função para atualizar o timestamp de updated_at automaticamente
        CREATE OR REPLACE FUNCTION update_conversation_message_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        -- Trigger para atualizar o timestamp quando uma mensagem for modificada
        CREATE TRIGGER update_conversation_message_timestamp
        BEFORE UPDATE ON conversation_messages
        FOR EACH ROW
        EXECUTE FUNCTION update_conversation_message_timestamp();
        
        RAISE NOTICE 'Tabela conversation_messages criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela conversation_messages já existe';
    END IF;
END $$;

-- Verificar se a tabela conversation_contexts existe, caso contrário, criá-la
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'conversation_contexts') THEN
        CREATE TABLE conversation_contexts (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
            context_type VARCHAR(50) NOT NULL,
            metadata JSONB,
            vector_data BYTEA,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX idx_conv_contexts_conversation_id ON conversation_contexts(conversation_id);
        CREATE INDEX idx_conv_contexts_customer_id ON conversation_contexts(customer_id);
        CREATE INDEX idx_conv_contexts_context_type ON conversation_contexts(context_type);
        CREATE INDEX idx_conv_contexts_metadata ON conversation_contexts USING GIN(metadata);
        
        -- Comentário da tabela
        COMMENT ON TABLE conversation_contexts IS 'Armazena contexto de conversas para continuidade e análise';
        
        -- Função para atualizar o timestamp de updated_at automaticamente
        CREATE OR REPLACE FUNCTION update_conversation_context_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        -- Trigger para atualizar o timestamp quando um contexto for modificado
        CREATE TRIGGER update_conversation_context_timestamp
        BEFORE UPDATE ON conversation_contexts
        FOR EACH ROW
        EXECUTE FUNCTION update_conversation_context_timestamp();
        
        RAISE NOTICE 'Tabela conversation_contexts criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela conversation_contexts já existe';
    END IF;
END $$;

-- Verificar se a tabela agents existe, caso contrário, criá-la
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'agents') THEN
        CREATE TABLE agents (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            role VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            avatar_url TEXT,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX idx_agents_email ON agents(email);
        CREATE INDEX idx_agents_role ON agents(role);
        CREATE INDEX idx_agents_status ON agents(status);
        
        -- Comentário da tabela
        COMMENT ON TABLE agents IS 'Armazena informações sobre agentes do sistema';
        
        -- Função para atualizar o timestamp de updated_at automaticamente
        CREATE OR REPLACE FUNCTION update_agent_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        -- Trigger para atualizar o timestamp quando um agente for modificado
        CREATE TRIGGER update_agent_timestamp
        BEFORE UPDATE ON agents
        FOR EACH ROW
        EXECUTE FUNCTION update_agent_timestamp();
        
        RAISE NOTICE 'Tabela agents criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela agents já existe';
    END IF;
END $$;
