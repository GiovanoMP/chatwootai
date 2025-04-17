# Guia para o Próximo Desenvolvedor

Olá, desenvolvedor! Bem-vindo ao projeto de integração Odoo-AI. Este documento fornece um contexto abrangente para você continuar o desenvolvimento do sistema.

## Visão Geral do Projeto

Este projeto é uma plataforma modular de integração entre Odoo e sistemas de IA, com suporte para múltiplos inquilinos (multi-tenant). O sistema utiliza FastAPI para criar uma API REST, implementa uma camada de abstração MCP (Model Context Protocol), usa Redis para cache e Qdrant para busca vetorial.

A arquitetura foi projetada para ser flexível, permitindo a integração não apenas com Odoo, mas potencialmente com outros ERPs no futuro. O sistema também suporta integração com Chatwoot para gerenciamento de conversas.

## Estado Atual do Projeto

### O que está funcionando:

1. **Servidor Unificado**: O servidor que combina a API Odoo e o webhook do Chatwoot está funcionando.
2. **Sistema de Logs**: Implementamos um sistema de logs detalhado que mostra o fluxo completo das mensagens.
3. **Webhook do Chatwoot**: O sistema recebe e processa mensagens do Chatwoot corretamente.
4. **Sincronização de Credenciais**: O módulo `ai_credentials_manager` do Odoo consegue sincronizar credenciais com o sistema de IA.
5. **Estrutura Básica da API**: A API REST para comunicação com o Odoo está estruturada e funcionando.

### Próximos Passos:

1. **Testar a Integração dos Módulos Odoo**: O foco atual é testar a integração dos módulos em `@addons/` com o sistema de IA.
2. **Implementar Crews Funcionais**: Resolver o erro atual na criação de crews para processar mensagens.
3. **Melhorar a Busca Semântica**: Otimizar o sistema de busca semântica (BM42) para regras de negócio e produtos.
4. **Expandir a Documentação**: Continuar a documentação do sistema, especialmente para novos módulos.

## Estrutura do Projeto

```
/
├── @addons/                  # Módulos Odoo personalizados
│   ├── ai_credentials_manager/  # Gerenciamento de credenciais
│   ├── business_rules/          # Regras de negócio
│   └── semantic_product_description/ # Descrições semânticas de produtos
├── @config/                  # Configurações do sistema
│   ├── domains/              # Configurações específicas por domínio
│   │   └── retail/           # Configurações para o domínio de varejo
│   │       └── account_1/    # Configurações para a conta 1
├── @mcp-odoo/                # Camada de abstração para Odoo
├── odoo/                     # Nova estrutura para API Odoo
│   ├── README.md             # Documentação detalhada da API
│   └── docs/                 # Documentação específica da API
│       └── inicializacao_rapida_servidor_unificado.md # Guia de inicialização
├── scripts/                  # Scripts de utilidade
│   ├── monitor_logs.py       # Monitoramento de logs
│   ├── setup_logging.py      # Configuração de logs
│   ├── start_ngrok.sh        # Inicialização do Ngrok
│   └── start_server.sh       # Inicialização do servidor
├── src/                      # Código-fonte principal
│   ├── core/                 # Componentes centrais
│   │   ├── crews/            # Implementação de crews (CrewAI)
│   │   ├── domain/           # Gerenciamento de domínios
│   │   └── hub.py            # Hub central de mensagens
│   └── webhook/              # Manipulação de webhooks
│       ├── routes.py         # Rotas para webhooks
│       └── webhook_handler.py # Manipulador de webhooks
└── main.py                   # Ponto de entrada do servidor unificado
```

## Arquitetura do Sistema

A arquitetura do sistema é baseada em vários componentes que trabalham juntos:

1. **Servidor Unificado**: Um servidor FastAPI que combina a API Odoo e o webhook do Chatwoot.
2. **Camada de Abstração MCP**: Permite a comunicação com diferentes ERPs (atualmente apenas Odoo).
3. **Sistema de Domínios**: Organiza as configurações e regras por domínio de negócio (ex: varejo, saúde).
4. **Sistema de Crews**: Usa CrewAI para criar agentes especializados que processam mensagens.
5. **Sistema de Cache**: Usa Redis para armazenar credenciais, configurações e instâncias de CrewAI.
6. **Sistema de Busca Vetorial**: Usa Qdrant para busca semântica de produtos e regras de negócio.

### Fluxo de Dados

O fluxo de dados no sistema segue este padrão:

1. **Entrada de Mensagens**:
   - Mensagens do Chatwoot chegam via webhook
   - Requisições do Odoo chegam via API REST

2. **Processamento de Mensagens**:
   - As mensagens são roteadas para o domínio correto conforme o account_id
   - O sistema identifica o account_id correspondente
   - A mensagem é processada pelo crew apropriado

3. **Resposta**:
   - O sistema gera uma resposta usando a crew correta (após o mapeamento do account_id/domínio)
   - A resposta é enviada de volta para o canal de origem

## Módulos Odoo (@addons/)

### ai_credentials_manager

Este módulo gerencia as credenciais para acesso ao sistema de IA. Ele é responsável por:

- Armazenar tokens de autenticação
- Configurar domínios de negócio
- Sincronizar credenciais com o sistema de IA

Exemplo de uso:

```python
# No módulo Odoo
def sync_credentials(self):
    """
    Sincroniza credenciais com o sistema de IA.
    """
    # Preparar dados
    data = {
        'token': self.token,
        'domain': self.domain,
        'business_area': self.business_area,
        'account_id': self.account_id,
    }
    
    # Enviar para o sistema de IA
    url = f"{self.api_url}/webhook"
    headers = {'Content-Type': 'application/json'}
    payload = {
        'event': 'credentials_sync',
        'data': data
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    # Verificar resposta
    if response.status_code == 200:
        self.last_sync = fields.Datetime.now()
        return True
    else:
        raise UserError(f"Erro ao sincronizar credenciais: {response.text}")
```

### business_rules

Este módulo gerencia regras de negócio que são usadas pelo sistema de IA para tomar decisões. Ele permite:

- Criar e gerenciar regras de negócio
- Categorizar regras por área de negócio
- Sincronizar regras com o sistema de IA para busca semântica

Exemplo de uso:

```python
# No módulo Odoo
def sync_rules(self):
    """
    Sincroniza regras de negócio com o sistema de IA.
    """
    # Obter todas as regras ativas
    rules = self.search([('active', '=', True)])
    
    # Preparar dados
    rules_data = []
    for rule in rules:
        rules_data.append({
            'id': rule.id,
            'name': rule.name,
            'description': rule.description,
            'category': rule.category_id.name,
            'content': rule.content,
        })
    
    # Enviar para o sistema de IA
    credentials = self.env['ai.credentials'].search([], limit=1)
    url = f"{credentials.api_url}/webhook"
    headers = {'Content-Type': 'application/json'}
    payload = {
        'event': 'business_rules_sync',
        'account_id': credentials.account_id,
        'data': {
            'rules': rules_data
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    # Verificar resposta
    if response.status_code == 200:
        return True
    else:
        raise UserError(f"Erro ao sincronizar regras: {response.text}")
```

### semantic_product_description

Este módulo gerencia descrições semânticas de produtos. Ele permite:

- Gerar descrições semânticas para produtos
- Sincronizar produtos com o sistema de IA para busca semântica
- Realizar busca semântica de produtos

Exemplo de uso:

```python
# No módulo Odoo
def generate_description(self):
    """
    Gera uma descrição semântica para o produto.
    """
    # Preparar dados do produto
    product_data = {
        'id': self.id,
        'name': self.name,
        'description': self.description or '',
        'attributes': self._get_product_attributes(),
    }
    
    # Enviar para o sistema de IA
    credentials = self.env['ai.credentials'].search([], limit=1)
    url = f"{credentials.api_url}/api/v1/products/{self.id}/description"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {credentials.token}"
    }
    params = {'account_id': credentials.account_id}
    
    response = requests.post(url, json=product_data, headers=headers, params=params)
    
    # Verificar resposta
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            self.semantic_description = result.get('data', {}).get('description', '')
            return True
    
    raise UserError(f"Erro ao gerar descrição: {response.text}")
```

## Sistema de Crews (CrewAI)

O sistema usa CrewAI para criar agentes especializados que processam mensagens. Cada crew é configurado em um arquivo YAML no diretório `@config/domains/{domain}/{account_id}/`.

Exemplo de configuração de crew:

```yaml
# @config/domains/retail/account_1/config.yaml
domain: retail
account_id: account_1
crews:
  customer_support:
    name: Customer Support Crew
    description: Crew for handling customer support inquiries
    agents:
      - name: Customer Service Agent
        role: customer_service
        goal: Provide excellent customer service
        backstory: You are a helpful customer service agent
        tools:
          - name: product_search
            description: Search for products
          - name: order_status
            description: Check order status
      - name: Technical Support Agent
        role: technical_support
        goal: Solve technical issues
        backstory: You are a knowledgeable technical support agent
        tools:
          - name: troubleshoot
            description: Troubleshoot technical issues
    tasks:
      - name: Identify customer intent
        description: Identify what the customer needs
      - name: Provide appropriate response
        description: Respond to the customer's inquiry
```

## Problema Atual com Crews

Atualmente, há um erro ao criar crews para processar mensagens:

```
Erro ao criar crew domain_crew para domínio retail: expected str, bytes or os.PathLike object, not NoneType
```

Este erro ocorre quando o sistema tenta criar uma crew para processar mensagens. O problema parece estar relacionado a um caminho de arquivo que está sendo passado como `None` quando deveria ser uma string.

## Inicialização do Sistema

Para iniciar o sistema, siga as instruções no arquivo `odoo/docs/inicializacao_rapida_servidor_unificado.md`. Em resumo:

1. **Configurar o sistema de logs**:
   ```bash
   cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/setup_logging.py
   ```

2. **Iniciar o servidor unificado**:
   ```bash
   cd /home/giovano/Projetos/Chatwoot\ V4 && ./scripts/start_server.sh
   ```

3. **Iniciar o Ngrok**:
   ```bash
   cd /home/giovano/Projetos/Chatwoot\ V4 && ./scripts/start_ngrok.sh
   ```

4. **Monitorar os logs**:
   ```bash
   cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --all
   ```

5. **Atualizar a URL do Ngrok na VPS**:
   ```bash
   ssh root@srv692745.hstgr.cloud
   docker exec webhook-proxy sed -i "s|FORWARD_URL *= *[\"'][^\"']*[\"']|FORWARD_URL = 'https://sua-url-do-ngrok.ngrok-free.app/webhook'|g" /app/simple_webhook.py && docker exec webhook-proxy grep FORWARD_URL /app/simple_webhook.py && docker restart webhook-proxy
   ```

## Configuração de Portas

O sistema usa as seguintes portas:

- **8001**: Servidor unificado (FastAPI)
- **8802**: Porta na VPS para o webhook (mapeada para a porta 8002 do container `webhook-proxy`)

## Próximos Passos Recomendados

1. **Resolver o Erro de Criação de Crews**:
   - Investigar o código em `src/core/crews/crew_factory.py`
   - Verificar se os arquivos de configuração existem em `@config/domains/retail/account_1/`
   - Implementar uma solução para lidar com caminhos nulos

2. **Testar a Integração dos Módulos Odoo**:
   - Verificar se o módulo `ai_credentials_manager` sincroniza corretamente as credenciais
   - Testar a sincronização de regras de negócio do módulo `business_rules`
   - Testar a geração de descrições semânticas do módulo `semantic_product_description`

3. **Melhorar a Busca Semântica**:
   - Otimizar o sistema de busca semântica (BM42) para regras de negócio e produtos
   - Implementar cache para melhorar o desempenho

4. **Expandir a Documentação**:
   - Documentar novos módulos e funcionalidades
   - Atualizar a documentação existente conforme necessário

## Recursos Adicionais

- **Documentação da API Odoo**: Consulte `odoo/README.md` para detalhes sobre a API REST
- **Guia de Inicialização Rápida**: Consulte `odoo/docs/inicializacao_rapida_servidor_unificado.md`
- **Documentação do CrewAI**: [CrewAI Documentation](https://docs.crewai.com/)
- **Documentação do FastAPI**: [FastAPI Documentation](https://fastapi.tiangolo.com/)
- **Documentação do Qdrant**: [Qdrant Documentation](https://qdrant.tech/documentation/)

## Contato

Se tiver dúvidas ou precisar de ajuda, entre em contato com o desenvolvedor anterior ou com o gerente do projeto.

Boa sorte com o desenvolvimento! 🚀
