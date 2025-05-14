-- Script para forçar a desinstalação do módulo business_rules
-- Este script deve ser executado no banco de dados PostgreSQL do Odoo
-- ATENÇÃO: Faça backup do banco de dados antes de executar este script

-- 1. Atualizar o estado do módulo business_rules para 'uninstalled' na tabela ir_module_module
UPDATE ir_module_module SET state = 'uninstalled' WHERE name = 'business_rules';

-- 2. Remover dependências do módulo business_rules
DELETE FROM ir_module_module_dependency WHERE module_id IN (SELECT id FROM ir_module_module WHERE name = 'business_rules');

-- 3. Remover registros da tabela ir_model_data relacionados ao módulo
DELETE FROM ir_model_data WHERE module = 'business_rules';
