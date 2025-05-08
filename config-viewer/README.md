# Config Viewer

Aplicação web para visualizar as configurações armazenadas no PostgreSQL do config-service. Esta ferramenta foi desenvolvida para facilitar a verificação e o monitoramento das configurações do sistema, especialmente a seção `enabled_collections` que é crítica para o funcionamento correto do sistema de IA.

## Funcionalidades

- **Autenticação de Usuários**: Sistema de login para proteger o acesso às configurações
- **Busca Avançada**: Busca de configurações por tenant ID, domínio e tipo
- **Visualização Detalhada**: Visualização de configurações com formatação de código e destaque de sintaxe
- **Coleções Habilitadas**: Visualização específica da seção `enabled_collections`
- **Mapeamento Chatwoot**: Visualização do mapeamento para roteamento de mensagens
- **Documentação Integrada**: Página de documentação explicando o sistema
- **API REST**: Acesso programático às configurações

## Requisitos

- Python 3.9+
- PostgreSQL 13+
- Docker e Docker Compose (opcional, para implantação)

## Instalação e Execução

### Ambiente Local

1. Clone o repositório:
   ```bash
   git clone <repository-url>
   cd config-viewer
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

   **Importante**: Defina uma senha forte para o administrador:
   ```
   ADMIN_PASSWORD=sua_senha_forte_aqui
   ```

4. Execute a aplicação usando o script:
   ```bash
   ./run.sh
   ```

   Ou manualmente:
   ```bash
   python app.py
   ```

5. Acesse a aplicação:
   ```
   http://localhost:8080
   ```

6. Faça login com as credenciais:
   - Usuário: `admin`
   - Senha: A senha definida na variável `ADMIN_PASSWORD` (padrão: `Config@Viewer2025!`)

### Usando Docker Compose

1. Inicie os serviços:
   ```bash
   docker-compose up -d
   ```

2. Acesse a aplicação:
   ```
   http://localhost:8080
   ```

## Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| DB_HOST | Host do banco de dados | localhost |
| DB_PORT | Porta do banco de dados | 5433 |
| DB_NAME | Nome do banco de dados | config_service |
| DB_USER | Usuário do banco de dados | postgres |
| DB_PASSWORD | Senha do banco de dados | postgres |

## Script de Consulta com Fallback

O sistema inclui um script de linha de comando `check_config.sh` para consultar as configurações diretamente no PostgreSQL. Este script oferece uma interface interativa para verificar as configurações e serve como fallback caso a interface web não esteja disponível.

### Funcionalidades do Script

- Listar todas as configurações armazenadas no PostgreSQL
- Verificar uma configuração específica por tenant_id, domain e config_type
- Verificar especificamente a seção `enabled_collections`
- Verificar o mapeamento Chatwoot

### Como Usar o Script

```bash
# Dar permissão de execução ao script
chmod +x check_config.sh

# Executar o script
./check_config.sh
```

O script apresentará um menu interativo com as seguintes opções:
1. Listar todas as configurações
2. Verificar configuração específica
3. Verificar enabled_collections
4. Verificar mapeamento Chatwoot
0. Sair

## Integração com o Módulo Odoo

Esta aplicação está integrada ao módulo Odoo `@addons/ai_credentials_manager/` com as seguintes funcionalidades:

1. **Botão de Acesso Rápido**:
   - Um botão "Visualizar Configurações" foi adicionado ao formulário de credenciais do sistema de IA
   - O botão redireciona para esta aplicação com o tenant_id pré-preenchido
   - Facilita a busca de configurações específicas para cada cliente

2. **Configuração da URL**:
   - A URL desta aplicação pode ser configurada nas Configurações do Sistema do Odoo
   - Permite adaptar a integração para diferentes ambientes (desenvolvimento, homologação, produção)

### Integração via API REST

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

### Configuração da URL no Odoo

A URL desta aplicação pode ser configurada no Odoo através do menu:

```
Configurações > Técnico > Microserviço de Configuração
```

Defina o campo "URL do Visualizador de Configurações" com o endereço apropriado:
- Desenvolvimento: `http://localhost:8080`
- Produção: `https://config.seudominio.com`

## Próximos Passos

- Implementar funcionalidades para editar as configurações diretamente na interface web
- Adicionar suporte para múltiplos usuários com diferentes níveis de acesso
- Implementar monitoramento e alertas para configurações problemáticas
- Adicionar dashboard com métricas e estatísticas sobre as configurações

## Licença

Proprietária - Todos os direitos reservados
