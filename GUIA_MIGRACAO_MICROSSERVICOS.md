# Guia de Migração para a Nova Arquitetura de Microsserviços

Este documento descreve o processo de migração do sistema atual para a nova arquitetura baseada em microsserviços.

## Visão Geral da Nova Arquitetura

A nova arquitetura separa o sistema em microsserviços independentes:

1. **Stack de IA** - O sistema principal que processa mensagens e utiliza os modelos de IA
2. **Config Service** - Microsserviço para armazenamento e gerenciamento de configurações
3. **Config Viewer** - Interface web para visualização de configurações
4. **Odoo API** (futuro) - Microsserviço para vetorização de dados do Odoo

Esta separação permite:
- Melhor escalabilidade
- Manutenção independente
- Maior resiliência
- Separação clara de responsabilidades

## Componentes Migrados

### 1. Config Service

O `config-service` é um microsserviço que:
- Recebe dados de configuração via webhook
- Armazena configurações no PostgreSQL
- Fornece endpoints para consulta de configurações

### 2. Config Viewer

O `config-viewer` é uma interface web que:
- Exibe configurações armazenadas no PostgreSQL
- Permite busca por tenant_id
- Mostra histórico de versões

### 3. Módulos Odoo

Os módulos Odoo foram atualizados para:
- Enviar dados diretamente para o `config-service`
- Não depender mais do webhook da stack de IA
- Configurar parâmetros para os novos microsserviços

## Processo de Migração

### Fase 1: Preparação (Concluída)

1. ✅ Desenvolvimento do `config-service`
2. ✅ Desenvolvimento do `config-viewer`
3. ✅ Atualização dos módulos Odoo

### Fase 2: Implantação Local (Atual)

1. ✅ Testes locais do `config-service`
2. ✅ Testes locais do `config-viewer`
3. ✅ Testes locais dos módulos Odoo
4. ✅ Documentação do processo

### Fase 3: Implantação em Produção

1. Configuração do PostgreSQL em produção
2. Implantação do `config-service` em produção
3. Implantação do `config-viewer` em produção
4. Atualização dos módulos Odoo em produção
5. Migração dos dados existentes

## Instruções de Implantação

### 1. Configuração do PostgreSQL

```bash
# Criar banco de dados
createdb -U postgres config_service

# Aplicar migrações
cd config-service
python -m alembic upgrade head
```

### 2. Implantação do Config Service

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/config-service.git
cd config-service

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/config_service
export API_KEY=sua-chave-api-secreta

# Iniciar serviço
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

### 3. Implantação do Config Viewer

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/config-viewer.git
cd config-viewer

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/config_service

# Iniciar serviço
python app.py
```

### 4. Configuração dos Módulos Odoo

No Odoo, configure os seguintes parâmetros do sistema:

1. Para o módulo `ai_credentials_manager`:
   - `config_service.url`: URL do config-service (ex: http://localhost:8002)
   - `config_service.api_key`: Chave de API para autenticação
   - `config_viewer.url`: URL do config-viewer (ex: http://localhost:8080)

2. Para o módulo `business_rules`:
   - `config_service.url`: URL do config-service (ex: http://localhost:8002)
   - `config_service.api_key`: Chave de API para autenticação
   - `business_rules.account_id`: ID da conta para sincronização de regras de negócio
   - `config_viewer.url`: URL do config-viewer (ex: http://localhost:8080)

## Migração de Dados

Para migrar dados existentes:

1. Exporte as configurações atuais:
   ```bash
   cd scripts
   python export_configs.py --output configs.json
   ```

2. Importe as configurações no novo sistema:
   ```bash
   cd scripts
   python import_configs.py --input configs.json
   ```

## Considerações de Segurança

### 1. Comunicação entre Serviços

- Use HTTPS para todas as comunicações entre serviços
- Configure o Traefik como reverse proxy
- Implemente autenticação via API Key

### 2. Acesso ao PostgreSQL

- Restrinja o acesso ao banco de dados apenas aos microsserviços
- Use usuários com privilégios mínimos
- Ative logs de auditoria

### 3. Proteção do Config Viewer

- Implemente autenticação para o Config Viewer
- Restrinja o acesso apenas a IPs autorizados
- Considere usar um VPN para acesso administrativo

## Monitoramento e Logs

- Configure logs centralizados para todos os microsserviços
- Implemente métricas para monitorar a saúde dos serviços
- Configure alertas para falhas e comportamentos anômalos

## Próximos Passos

1. Desenvolvimento do microsserviço `odoo_api` para vetorização de dados
2. Integração do `odoo_api` com o Qdrant
3. Atualização da stack de IA para consultar o `config-service`
4. Implementação de testes automatizados para todos os microsserviços

## Contato e Suporte

Para dúvidas ou suporte durante a migração, entre em contato:
- Email: suporte@sprintia.com.br
- Documentação: https://docs.sprintia.com.br
