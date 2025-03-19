-- Script para atualizar produtos com informações detalhadas
-- Este script atualiza os produtos existentes com informações detalhadas em linguagem natural
-- As informações detalhadas serão usadas para gerar embeddings no Qdrant

-- Primeiro, vamos verificar se a tabela de produtos existe
-- Se não existir, o script 01_create_tables.sql deve ser executado primeiro

-- Usar PL/pgSQL para processar os dados JSON
DO $$
DECLARE
    product_data json;
    product_record record;
BEGIN
    -- Ler o arquivo JSON
    product_data := (SELECT content::json FROM (SELECT pg_read_file('/docker-entrypoint-initdb.d/data/product_descriptions.json') as content) as json_content);
    
    -- Processar cada produto no arquivo JSON
    FOR product_record IN
        SELECT * FROM json_to_recordset(product_data) AS x(id INTEGER, name TEXT, description TEXT, detailed_information TEXT)
    LOOP
        -- Atualizar o produto se existir pelo ID
        UPDATE products 
        SET detailed_information = product_record.detailed_information
        WHERE id = product_record.id;
        
        -- Se não encontrar pelo ID, tentar encontrar pelo nome
        IF NOT FOUND THEN
            UPDATE products
            SET detailed_information = product_record.detailed_information
            WHERE name LIKE '%' || product_record.name || '%';
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Atualização de informações detalhadas de produtos concluída';
END;
$$;
