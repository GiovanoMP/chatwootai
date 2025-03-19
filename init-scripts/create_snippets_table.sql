-- Script simplificado para criar a tabela conversation_snippets

-- Criar a tabela conversation_snippets se não existir
CREATE TABLE IF NOT EXISTS conversation_snippets (
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

-- Criar índices
CREATE INDEX IF NOT EXISTS idx_conv_snippets_conversation_id ON conversation_snippets(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conv_snippets_importance ON conversation_snippets(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_conv_snippets_tags ON conversation_snippets USING GIN(tags);

-- Comentários das tabelas e colunas
COMMENT ON TABLE conversation_snippets IS 'Armazena trechos importantes de conversas para análise posterior';
COMMENT ON COLUMN conversation_snippets.snippet_text IS 'Texto do trecho importante da conversa';
COMMENT ON COLUMN conversation_snippets.context_before IS 'Contexto anterior ao trecho (opcional)';
COMMENT ON COLUMN conversation_snippets.context_after IS 'Contexto posterior ao trecho (opcional)';
COMMENT ON COLUMN conversation_snippets.sentiment IS 'Análise de sentimento do trecho (positivo, negativo, neutro)';
COMMENT ON COLUMN conversation_snippets.tags IS 'Tags ou categorias associadas ao trecho em formato JSON';
COMMENT ON COLUMN conversation_snippets.importance_score IS 'Pontuação de importância do trecho (0.0 a 1.0)';
