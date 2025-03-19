-- Script para atualizar serviços com informações detalhadas
-- Este script atualiza os serviços existentes com informações detalhadas em linguagem natural
-- As informações detalhadas serão usadas para gerar embeddings no Qdrant

-- Primeiro, vamos verificar se a tabela de serviços existe
-- Se não existir, o script 01_create_tables.sql deve ser executado primeiro

-- Atualizar a Limpeza de Pele Profunda (ID 1)
WITH json_data AS (
    SELECT * FROM json_to_recordset(
        (SELECT content::json FROM (
            SELECT pg_read_file('/docker-entrypoint-initdb.d/data/service_descriptions.json') as content
        ) as json_content)
    ) AS x(id INTEGER, name TEXT, description TEXT, detailed_information TEXT)
)
UPDATE services 
SET detailed_information = json_data.detailed_information
FROM json_data
WHERE services.id = 1 AND json_data.id = 1;

-- Inserir o serviço se não existir
INSERT INTO services (id, name, description, duration, price, detailed_information)
SELECT 1, 'Limpeza de Pele Profunda', 'Tratamento para remover impurezas e células mortas', 60, 120.00, detailed_information
FROM json_data
WHERE id = 1
AND NOT EXISTS (SELECT 1 FROM services WHERE id = 1);

-- Atualizar o Microagulhamento Facial (ID 2)
WITH json_data AS (
    SELECT * FROM json_to_recordset(
        (SELECT content::json FROM (
            SELECT pg_read_file('/docker-entrypoint-initdb.d/data/service_descriptions.json') as content
        ) as json_content)
    ) AS x(id INTEGER, name TEXT, description TEXT, detailed_information TEXT)
)
UPDATE services 
SET detailed_information = json_data.detailed_information
FROM json_data
WHERE services.id = 2 AND json_data.id = 2;

-- Inserir o serviço se não existir
INSERT INTO services (id, name, description, duration, price, detailed_information)
SELECT 2, 'Microagulhamento Facial', 'Estimulação de colágeno com micro agulhas', 45, 250.00, detailed_information
FROM json_data
WHERE id = 2
AND NOT EXISTS (SELECT 1 FROM services WHERE id = 2);

-- Atualizar o Peeling de Diamante (ID 3)
WITH json_data AS (
    SELECT * FROM json_to_recordset(
        (SELECT content::json FROM (
            SELECT pg_read_file('/docker-entrypoint-initdb.d/data/service_descriptions.json') as content
        ) as json_content)
    ) AS x(id INTEGER, name TEXT, description TEXT, detailed_information TEXT)
)
UPDATE services 
SET detailed_information = json_data.detailed_information
FROM json_data
WHERE services.id = 3 AND json_data.id = 3;

-- Inserir o serviço se não existir
INSERT INTO services (id, name, description, duration, price, detailed_information)
SELECT 3, 'Peeling de Diamante', 'Esfoliação profunda para renovação celular', 30, 180.00, detailed_information
FROM json_data
WHERE id = 3
AND NOT EXISTS (SELECT 1 FROM services WHERE id = 3);

-- Atualizar a Drenagem Linfática Facial (ID 4)
WITH json_data AS (
    SELECT * FROM json_to_recordset(
        (SELECT content::json FROM (
            SELECT pg_read_file('/docker-entrypoint-initdb.d/data/service_descriptions.json') as content
        ) as json_content)
    ) AS x(id INTEGER, name TEXT, description TEXT, detailed_information TEXT)
)
UPDATE services 
SET detailed_information = json_data.detailed_information
FROM json_data
WHERE services.id = 4 AND json_data.id = 4;

-- Inserir o serviço se não existir
INSERT INTO services (id, name, description, duration, price, detailed_information)
SELECT 4, 'Drenagem Linfática Facial', 'Massagem para reduzir inchaço e toxinas', 40, 150.00, detailed_information
FROM json_data
WHERE id = 4
AND NOT EXISTS (SELECT 1 FROM services WHERE id = 4);

-- Atualizar a Radiofrequência Facial (ID 5)
WITH json_data AS (
    SELECT * FROM json_to_recordset(
        (SELECT content::json FROM (
            SELECT pg_read_file('/docker-entrypoint-initdb.d/data/service_descriptions.json') as content
        ) as json_content)
    ) AS x(id INTEGER, name TEXT, description TEXT, detailed_information TEXT)
)
UPDATE services 
SET detailed_information = json_data.detailed_information
FROM json_data
WHERE services.id = 5 AND json_data.id = 5;

-- Inserir o serviço se não existir
INSERT INTO services (id, name, description, duration, price, detailed_information)
SELECT 5, 'Radiofrequência Facial', 'Tratamento para firmeza e elasticidade da pele', 50, 220.00, detailed_information
FROM json_data
WHERE id = 5
AND NOT EXISTS (SELECT 1 FROM services WHERE id = 5);

-- Inserir preços de serviços
INSERT INTO service_prices (service_id, price_type, price, special_condition)
SELECT id, 'regular', price, NULL
FROM services
LIMIT 5;

-- Inserir preços promocionais para alguns serviços
INSERT INTO service_prices (service_id, price_type, price, special_condition)
VALUES
(1, 'promotional', 129.90, 'Promoção válida por 30 dias'),
(3, 'promotional', 149.90, 'Promoção válida por 15 dias');
