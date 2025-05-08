# Config Service API

Microserviço para gerenciamento centralizado de configurações do sistema, incluindo mapeamento Chatwoot e configurações YAML para o sistema multi-tenant.

## Status do Projeto

### O que foi realizado até agora:

- ✅ Implementação da estrutura básica do microserviço
- ✅ Armazenamento de mapeamentos Chatwoot no PostgreSQL
- ✅ Armazenamento de configurações YAML no PostgreSQL
- ✅ Versionamento de configurações
- ✅ Integração com o módulo Odoo `ai_credentials_manager`
- ✅ Migração de configurações existentes para o PostgreSQL
- ✅ Implementação de fallback para arquivos locais
- ✅ Correção da migração da seção `enabled_collections` para o PostgreSQL
- ✅ Implementação de interface web para visualizar configurações

### O que ainda falta:

- ⬜ Remover gradualmente o fallback para arquivos locais
- ⬜ Implementar monitoramento e métricas
- ⬜ Melhorar a documentação para desenvolvedores
- ⬜ Implementar testes automatizados mais abrangentes

## Visão Geral

Este microserviço fornece uma API RESTful para gerenciar configurações do sistema, permitindo:

- Armazenar e recuperar mapeamentos Chatwoot
- Mesclar atualizações parciais de mapeamento
- Gerenciar configurações YAML para tenants (config, credentials, crews, etc.)
- Versionamento de configurações
- Exportar configurações em formato YAML
- Autenticação via chave de API

## Requisitos

- Python 3.9+
- PostgreSQL 13+
- Docker e Docker Compose (opcional, para implantação)

## Instalação e Execução

### Ambiente Local

1. Clone o repositório:
   ```bash
   git clone <repository-url>
   cd config-service
   ```

2. Crie um ambiente virtual e instale as dependências:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

4. Inicie o banco de dados PostgreSQL:
   ```bash
   # Usando Docker
   docker run --name config-service-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=config_service -p 5432:5432 -d postgres:13
   ```

5. Execute a aplicação:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Acesse a documentação da API:
   ```
   http://localhost:8000/docs
   ```

### Usando Docker Compose

1. Inicie os serviços:
   ```bash
   docker-compose up -d
   ```

2. Acesse a documentação da API:
   ```
   http://localhost:8000/docs
   ```

## Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| DATABASE_URL | URL de conexão com o banco de dados | postgresql://postgres:postgres@localhost:5432/config_service |
| API_KEY | Chave de API para autenticação | development-api-key |
| DEBUG | Modo de depuração | true |
| ENVIRONMENT | Ambiente de execução | development |
| HOST | Host para o servidor | 0.0.0.0 |
| PORT | Porta para o servidor | 8000 |

### Configurações para Ambiente em Nuvem

Ao implantar em um ambiente de nuvem (produção), é necessário ajustar as seguintes configurações:

1. **Segurança**:
   - Gere uma chave de API forte e única
   - Desative o modo de depuração (`DEBUG=false`)
   - Configure `ENVIRONMENT=production`

2. **Banco de Dados**:
   - Use uma instância gerenciada de PostgreSQL (AWS RDS, Azure Database, GCP Cloud SQL)
   - Configure credenciais seguras
   - Habilite backup automático
   - Configure SSL para conexão com o banco de dados

3. **Rede**:
   - Configure um balanceador de carga
   - Implemente HTTPS com certificado válido
   - Configure regras de firewall para limitar o acesso

4. **Monitoramento**:
   - Configure logs centralizados
   - Implemente métricas e alertas
   - Configure health checks

5. **Escalabilidade**:
   - Configure auto-scaling baseado em carga
   - Use um sistema de orquestração como Kubernetes

Exemplo de configuração para produção:
```bash
DATABASE_URL=postgresql://user:password@production-db.example.com:5432/config_service?sslmode=require
API_KEY=sua-chave-api-segura-e-complexa
DEBUG=false
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
```

## API Endpoints

### Mapeamento Chatwoot

- `GET /mapping/` - Obtém o mapeamento atual
- `POST /mapping/` - Cria um novo mapeamento (substitui o existente)
- `PATCH /mapping/` - Atualiza parcialmente o mapeamento existente
- `GET /mapping/export` - Exporta o mapeamento como YAML

### Configurações YAML

- `GET /configs/{tenant_id}/{domain}/{config_type}` - Obtém a configuração mais recente
- `POST /configs/{tenant_id}/{domain}/{config_type}` - Cria ou atualiza uma configuração
- `GET /configs/{tenant_id}/{domain}/{config_type}/yaml` - Exporta a configuração como YAML
- `GET /configs/{tenant_id}` - Lista as configurações disponíveis para um tenant
- `GET /configs/{tenant_id}/{domain}/{config_type}/history` - Obtém o histórico de versões
- `GET /configs/{tenant_id}/{domain}/{config_type}/version/{version}` - Obtém uma versão específica

### Saúde do Serviço

- `GET /health` - Verifica a saúde do serviço

## Autenticação

Todas as requisições devem incluir o cabeçalho `X-API-Key` com a chave de API configurada.

Exemplo:
```bash
curl -X GET http://localhost:8000/mapping/ -H "X-API-Key: development-api-key"
```

## Integração com Outros Sistemas

### Módulo Odoo (ai_credentials_manager)

O módulo Odoo `ai_credentials_manager` foi modificado para:
- Enviar atualizações de mapeamento Chatwoot para este microserviço
- Enviar configurações YAML para este microserviço
- Obter configurações do microserviço quando necessário

### Sistema de IA

O sistema de IA foi modificado para:
- Consultar este microserviço para obter o mapeamento Chatwoot
- Carregar configurações YAML do microserviço
- Usar arquivos locais como fallback em caso de falha na comunicação

### Verificação de Configurações

Para facilitar a verificação das configurações armazenadas no PostgreSQL, foi criado um script `check_config.sh` que permite:

- Listar todas as configurações armazenadas
- Verificar uma configuração específica
- Verificar especificamente a seção `enabled_collections`
- Verificar o mapeamento Chatwoot atual

Exemplo de uso:
```bash
./check_config.sh
```

O script apresenta um menu interativo que permite navegar pelas diferentes opções de verificação.

### Acesso às Configurações pelas Crews

As crews podem acessar as configurações de duas maneiras:

1. **Acesso via API REST**:
   ```python
   import requests

   def get_config(tenant_id, domain, config_type, api_key):
       url = f"http://config-service:8000/configs/{tenant_id}/{domain}/{config_type}"
       headers = {"X-API-Key": api_key}
       response = requests.get(url, headers=headers)
       if response.status_code == 200:
           return response.json()
       return None
   ```

2. **Acesso via Serviço Centralizado**:
   Um serviço centralizado pode ser implementado para gerenciar o acesso às configurações, incluindo cache para melhorar o desempenho.

### Script de Migração

O script `migrate_configs.py` permite migrar configurações existentes para o microserviço:

```bash
# Migrar todas as configurações
python migrate_configs.py

# Simular migração sem enviar configurações
python migrate_configs.py --dry-run

# Especificar diretório de configurações
python migrate_configs.py --config-dir /path/to/configs

# Especificar arquivo de mapeamento
python migrate_configs.py --mapping-file /path/to/mapping.yaml
```

## Problemas Conhecidos e Soluções

### Problema com a Seção `enabled_collections` (Resolvido)

**Problema**: A seção `enabled_collections` não estava sendo migrada corretamente para o PostgreSQL.

**Causa Identificada**:
- A seção `enabled_collections` estava sendo gerada corretamente no módulo `business_rules`
- O problema estava na conversão YAML para JSON no microserviço
- Quando o YAML não tinha a estrutura esperada, a seção `enabled_collections` não era processada corretamente

**Solução Implementada**:
1. Foi criado o script `fix_enabled_collections.py` para diagnosticar e corrigir o problema
2. O script verifica se a seção `enabled_collections` está presente nas configurações
3. Se não estiver presente, o script adiciona a seção com os valores corretos
4. O script pode ser executado periodicamente para garantir que todas as configurações tenham a seção `enabled_collections`

**Código Corrigido**:
- O script `fix_enabled_collections.py` foi modificado para lidar com diferentes estruturas de YAML
- Não é mais necessário que exista a seção `company_metadata` para adicionar a seção `enabled_collections`
- O script obtém os valores corretos do arquivo local ou usa valores padrão se necessário

### Fallback para Arquivos Locais

**Problema**: O sistema ainda está criando arquivos locais como fallback, mesmo quando o microserviço está funcionando corretamente.

**Solução Proposta**:
1. Implementar um mecanismo de verificação de saúde do microserviço
2. Criar arquivos locais apenas quando o microserviço não estiver disponível
3. Adicionar uma opção de configuração para desativar completamente o fallback

## Desenvolvimento

### Estrutura do Projeto

```
config-service/
├── app/
│   ├── api/            # Endpoints da API
│   │   ├── mapping.py  # Endpoints para mapeamento Chatwoot
│   │   └── config.py   # Endpoints para configurações YAML
│   ├── core/           # Configurações centrais
│   │   ├── config.py   # Configurações da aplicação
│   │   ├── database.py # Conexão com o banco de dados
│   │   └── security.py # Autenticação e autorização
│   ├── models/         # Modelos de dados
│   │   ├── mapping.py  # Modelo para mapeamento Chatwoot
│   │   └── config.py   # Modelo para configurações YAML
│   ├── schemas/        # Esquemas de validação
│   │   ├── mapping.py  # Esquemas para mapeamento Chatwoot
│   │   └── config.py   # Esquemas para configurações YAML
│   └── services/       # Lógica de negócio
│       ├── mapping_service.py  # Serviço para mapeamento Chatwoot
│       └── config_service.py   # Serviço para configurações YAML
├── migrations/         # Migrações de banco de dados
├── tests/              # Testes automatizados
├── .env                # Variáveis de ambiente
├── .env.example        # Exemplo de variáveis de ambiente
├── docker-compose.yml  # Configuração Docker Compose
├── Dockerfile          # Configuração Docker
├── migrate_configs.py  # Script para migrar configurações
├── start.sh            # Script para iniciar o serviço
└── requirements.txt    # Dependências
```

### Executando Testes

```bash
pytest
```

## Próximos Passos

### Curto Prazo

1. **Melhorar a Interface Web de Configurações**:
   - Adicionar autenticação para proteger o acesso às configurações
   - Adicionar funcionalidades para editar as configurações
   - Melhorar a visualização das configurações com formatação de código e destaque de sintaxe

2. **Integrar a Interface Web com o Módulo Odoo**:
   - Adicionar um botão no módulo Odoo que redireciona para a aplicação web
   - Ou usar a API REST da aplicação para obter os dados e exibi-los no módulo Odoo

3. **Otimizar o Acesso às Configurações**:
   - Implementar um serviço centralizado para acesso às configurações
   - Adicionar suporte para cache para melhorar o desempenho

### Médio Prazo

1. **Remover Gradualmente o Fallback**:
   - Implementar um mecanismo de verificação de saúde do microserviço
   - Criar arquivos locais apenas quando o microserviço não estiver disponível
   - Adicionar uma opção de configuração para desativar completamente o fallback

2. **Melhorar a Segurança**:
   - Implementar autenticação mais robusta
   - Adicionar suporte para HTTPS
   - Implementar controle de acesso baseado em funções

3. **Implementar Monitoramento**:
   - Adicionar métricas para rastrear o uso do microserviço
   - Implementar alertas para problemas de desempenho ou disponibilidade
   - Configurar logs centralizados

### Longo Prazo

1. **Migrar para Kubernetes**:
   - Preparar o microserviço para execução em Kubernetes
   - Implementar auto-scaling baseado em carga
   - Configurar health checks e readiness probes

2. **Expandir Funcionalidades**:
   - Adicionar suporte para mais tipos de configuração
   - Implementar validação de esquema para configurações
   - Adicionar suporte para rollback de configurações

3. **Integrar com Outros Sistemas**:
   - Implementar webhooks para notificar outros sistemas sobre mudanças de configuração
   - Adicionar suporte para importação/exportação de configurações em massa
   - Implementar integração com sistemas de CI/CD

## Atualizações Recentes

### Correção da Seção `enabled_collections`

Foi identificado e corrigido um problema com a migração da seção `enabled_collections` para o PostgreSQL:

- Criado script `fix_enabled_collections.py` para diagnosticar e corrigir o problema
- O script verifica se a seção `enabled_collections` está presente nas configurações
- Se não estiver presente, o script adiciona a seção com os valores corretos
- O script pode ser executado periodicamente para garantir que todas as configurações tenham a seção `enabled_collections`

Para executar o script de correção:
```bash
python fix_enabled_collections.py
```

Opções disponíveis:
```bash
python fix_enabled_collections.py --tenant-id=account_1 --domain=retail  # Corrigir apenas um tenant específico
python fix_enabled_collections.py --dry-run  # Simular a correção sem aplicá-la
```

### Interface Web para Visualização de Configurações

Foi desenvolvida uma interface web para visualizar as configurações armazenadas no PostgreSQL, com foco especial na seção `enabled_collections` que é crítica para o funcionamento correto do sistema de IA:

#### Credenciais de Acesso

A interface web é protegida por autenticação para garantir a segurança das configurações:

- **Usuário:** admin
- **Senha padrão:** Config@Viewer2025!

**IMPORTANTE**: Esta senha deve ser alterada em ambiente de produção!

- Aplicação web moderna usando Flask e Bootstrap
- Interface intuitiva para visualizar todas as configurações, incluindo YAML e JSON
- Visualização específica da seção `enabled_collections` para fácil monitoramento
- Visualização do mapeamento Chatwoot para verificar o roteamento de mensagens
- API REST completa para acesso programático às configurações
- Dockerfile e docker-compose.yml para facilitar a implantação em qualquer ambiente

A aplicação está disponível no diretório `config-viewer` e pode ser executada de duas formas:

1. Usando o script de execução (recomendado para desenvolvimento):
   ```bash
   cd config-viewer
   ./run.sh
   ```

2. Usando Docker (recomendado para produção):
   ```bash
   cd config-viewer
   docker-compose up -d
   ```

Acesse a aplicação web em: http://localhost:8080

#### Funcionalidades da Interface Web

- **Dashboard Inicial**: Visão geral de todas as configurações armazenadas no PostgreSQL
- **Visualização Detalhada**: Veja os detalhes de uma configuração específica, incluindo:
  - Conteúdo YAML formatado
  - Dados JSON estruturados
  - Metadados como versão, data de criação e atualização
- **Coleções Habilitadas**: Visualização dedicada da seção `enabled_collections` de todas as configurações
- **Mapeamento Chatwoot**: Visualização do mapeamento atual para roteamento de mensagens
- **Histórico de Versões**: Acesso a versões anteriores das configurações
- **API REST**: Endpoints para acesso programático a todas as funcionalidades

#### Script de Consulta com Fallback

Além da interface web, o sistema inclui um script de linha de comando `check_config.sh` que serve como fallback para consultar as configurações diretamente no PostgreSQL:

```bash
# Dar permissão de execução ao script
chmod +x check_config.sh

# Executar o script
./check_config.sh
```

O script apresenta um menu interativo com opções para:
1. Listar todas as configurações
2. Verificar uma configuração específica
3. Verificar especificamente a seção `enabled_collections`
4. Verificar o mapeamento Chatwoot

#### Integração com o Módulo Odoo

A interface web foi integrada ao módulo Odoo `@addons/ai_credentials_manager/` com as seguintes funcionalidades:

1. **Botão de Acesso Rápido**:

   Um botão "Visualizar Configurações" foi adicionado ao formulário de credenciais do sistema de IA, permitindo acesso direto ao visualizador de configurações com o tenant_id pré-preenchido.

   ![Botão Visualizar Configurações](https://via.placeholder.com/400x100?text=Bot%C3%A3o+Visualizar+Configura%C3%A7%C3%B5es)

2. **Configuração da URL**:

   A URL do visualizador de configurações pode ser configurada nas Configurações do Sistema, na seção "Microserviço de Configuração":

   ![Configuração da URL](https://via.placeholder.com/400x200?text=Configura%C3%A7%C3%A3o+da+URL)

3. **Uso em Produção**:

   Para ambientes de produção, configure a URL para apontar para o servidor de produção:

   ```
   https://config.seudominio.com
   ```

#### Deploy em Produção

Para deploy em produção, siga estas etapas:

1. **Configurar Variáveis de Ambiente**:

   Crie um arquivo `.env.production` com configurações seguras:

   ```
   # Configurações do banco de dados
   DB_HOST=config-service-db
   DB_PORT=5432
   DB_NAME=config_service
   DB_USER=postgres
   DB_PASSWORD=senha_segura_do_postgres

   # Configurações da aplicação
   FLASK_APP=app.py
   FLASK_ENV=production
   FLASK_DEBUG=0
   SECRET_KEY=chave_secreta_longa_e_aleatoria
   ADMIN_PASSWORD=senha_admin_forte_e_segura
   ```

2. **Deploy com Docker Swarm**:

   Crie um arquivo `docker-compose.prod.yml`:

   ```yaml
   version: '3.8'

   services:
     config-viewer:
       image: ${REGISTRY}/config-viewer:${TAG}
       deploy:
         replicas: 2
         update_config:
           parallelism: 1
           delay: 10s
         restart_policy:
           condition: on-failure
       environment:
         - DB_HOST=config-service-db
         - DB_PORT=5432
         - DB_NAME=config_service
         - DB_USER=postgres
         - DB_PASSWORD=${DB_PASSWORD}
         - SECRET_KEY=${SECRET_KEY}
         - ADMIN_PASSWORD=${ADMIN_PASSWORD}
       networks:
         - traefik-public
         - backend
       labels:
         - "traefik.enable=true"
         - "traefik.http.routers.config-viewer.rule=Host(`config.${DOMAIN}`)"
         - "traefik.http.routers.config-viewer.entrypoints=websecure"
         - "traefik.http.routers.config-viewer.tls.certresolver=letsencrypt"
         - "traefik.http.services.config-viewer.loadbalancer.server.port=8080"

   networks:
     traefik-public:
       external: true
     backend:
       external: true
   ```

3. **Atualizar URL no Odoo**:

   Após o deploy, atualize o parâmetro do sistema no Odoo:

   ```
   config_viewer.url = https://config.seudominio.com
   ```

4. **Segurança em Produção**:

   - Use HTTPS com certificados válidos
   - Configure firewall para limitar o acesso
   - Altere a senha padrão para uma senha forte e única
   - Considere implementar autenticação baseada em banco de dados
   - Configure backups regulares do banco de dados

#### API REST para Integração

Além do botão de redirecionamento, você pode usar a API REST para integração programática:

```python
import requests
from requests.auth import HTTPBasicAuth

def get_enabled_collections(tenant_id=None):
    """Obtém as coleções habilitadas de todas as configurações."""
    base_url = self.env['ir.config_parameter'].sudo().get_param('config_viewer.url', 'http://localhost:8080')
    auth = HTTPBasicAuth('admin', self.env['ir.config_parameter'].sudo().get_param('config_viewer.password', 'Config@Viewer2025!'))

    url = f"{base_url}/api/enabled_collections"
    if tenant_id:
        url += f"?tenant_id={tenant_id}"

    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        return response.json()
    return None
```

## Licença

Proprietária - Todos os direitos reservados
