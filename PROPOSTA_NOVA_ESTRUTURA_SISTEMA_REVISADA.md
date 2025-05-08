# Proposta de Nova Estrutura do Sistema ChatwootAI (Revisada)

## 1. Visão Geral

Esta proposta revisada detalha uma nova estrutura para o sistema ChatwootAI após o desacoplamento dos componentes odoo-api e mcp-odoo como microsserviços. O objetivo é criar um sistema limpo, modular e fácil de manter, com foco em uma arquitetura que facilite a escalabilidade e a manutenção por um desenvolvedor solo, priorizando a simplicidade e eficiência.

## 2. Estrutura de Diretórios Proposta

```
chatwoot-ai/
├── main.py                      # Ponto de entrada principal
├── config/                      # Configurações locais (fallback)
│   └── templates/               # Templates YAML para configurações
├── src/
│   ├── api/                     # Endpoints da API
│   │   ├── webhook.py           # Handler de webhook do Chatwoot
│   │   ├── internal.py          # Endpoints internos (notificações, etc.)
│   │   └── health.py            # Endpoints de health check
│   ├── core/
│   │   ├── cache/
│   │   │   ├── config_cache.py  # Implementação do cache de configuração
│   │   │   └── redis_cache.py   # Utilitários de cache Redis
│   │   ├── coordinator.py       # Coordenador central (antigo hub.py)
│   │   ├── crew_factory.py      # Fábrica de crews
│   │   └── prompt_builder.py    # Builder de prompts simplificado
│   ├── crews/
│   │   ├── base_crew.py         # Classe base para todas as crews
│   │   ├── whatsapp/            # Crew do WhatsApp
│   │   │   ├── whatsapp_crew.py # Implementação da crew
│   │   │   ├── agents/          # Agentes específicos do WhatsApp
│   │   │   ├── tasks/           # Tasks específicas do WhatsApp
│   │   │   └── tools/           # Tools específicas do WhatsApp
│   │   ├── instagram/           # Crew do Instagram
│   │   │   ├── instagram_crew.py
│   │   │   ├── agents/
│   │   │   ├── tasks/
│   │   │   └── tools/
│   │   └── default/             # Crew padrão para fallback
│   │       ├── default_crew.py
│   │       ├── agents/
│   │       ├── tasks/
│   │       └── tools/
│   ├── prompts/                 # Templates de prompts
│   │   ├── whatsapp/            # Prompts para WhatsApp
│   │   │   ├── intention.txt
│   │   │   ├── business_rules.txt
│   │   │   └── response.txt
│   │   ├── instagram/           # Prompts para Instagram
│   │   └── default/             # Prompts padrão
│   └── utils/
│       ├── logger.py            # Configuração de logging
│       ├── metrics.py           # Métricas e telemetria
│       └── fallback.py          # Mecanismos de fallback
├── tests/                       # Testes automatizados
│   ├── unit/                    # Testes unitários
│   ├── integration/             # Testes de integração
│   └── fixtures/                # Fixtures para testes
└── scripts/                     # Scripts de utilidade
    ├── start.sh                 # Script de inicialização
    └── monitor.sh               # Script de monitoramento
```

## 3. Componentes Principais

### 3.1. Coordinator (antigo Hub)

O `coordinator.py` substitui o antigo `hub.py`, com um nome mais descritivo que reflete sua função de coordenar o fluxo de mensagens entre o webhook handler e as crews especializadas.

```python
# src/core/coordinator.py
class MessageCoordinator:
    """
    Coordenador central que direciona mensagens para as crews apropriadas.
    Responsável por:
    1. Determinar qual crew deve processar a mensagem
    2. Obter configurações e credenciais do tenant
    3. Criar a crew apropriada através da fábrica
    4. Coordenar o processamento da mensagem
    """

    def __init__(self, config_cache, crew_factory):
        self.config_cache = config_cache
        self.crew_factory = crew_factory

    async def process_message(self, message, conversation, account_id, inbox_id=None):
        """
        Processa uma mensagem e direciona para a crew apropriada.
        """
        # Identificar o tenant
        tenant_info = await self.config_cache.get_tenant_info(account_id, inbox_id)
        if not tenant_info:
            return {"error": "Tenant not found"}

        # Obter configurações e credenciais
        tenant_id = tenant_info.get("tenant_id")
        domain = tenant_info.get("domain")
        config = await self.config_cache.get_config(tenant_id, domain, "config")
        credentials = await self.config_cache.get_config(tenant_id, domain, "credentials")

        # Determinar o canal
        channel = self._determine_channel(conversation)

        # Criar a crew apropriada
        crew = self.crew_factory.create_crew(
            channel=channel,
            tenant_id=tenant_id,
            domain=domain,
            config=config,
            credentials=credentials
        )

        # Processar a mensagem
        return await crew.process_message(message, conversation)
```

### 3.2. Sistema de Gerenciamento de Prompts Simplificado

O novo sistema de gerenciamento de prompts utiliza `str.format()` para simplicidade e desempenho, sem dependências externas.

```python
# src/core/prompt_builder.py
import os
from typing import Dict, Any

class PromptBuilder:
    """
    Classe responsável por construir prompts usando str.format().
    Simples, eficiente e sem dependências externas.
    """

    def __init__(self, template_path=None, template_content=None):
        """
        Inicializa o PromptBuilder.

        Args:
            template_path: Caminho para o arquivo de template
            template_content: Conteúdo do template (alternativa ao template_path)
        """
        if template_path:
            with open(template_path, 'r', encoding='utf-8') as f:
                self.template = f.read()
        elif template_content:
            self.template = template_content
        else:
            raise ValueError("É necessário fornecer template_path ou template_content")

    def build(self, **kwargs) -> str:
        """
        Constrói um prompt substituindo as variáveis no template.

        Args:
            **kwargs: Variáveis a serem substituídas no template

        Returns:
            Prompt construído
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            # Fornecer uma mensagem de erro mais útil
            missing_key = str(e).strip("'")
            raise KeyError(f"Variável '{missing_key}' não fornecida para o template")
        except Exception as e:
            raise ValueError(f"Erro ao construir prompt: {str(e)}")
```

### 3.3. Exemplo de Template de Prompt

```
# src/prompts/whatsapp/intention.txt
Você é um assistente especializado em identificar a intenção do cliente em mensagens do WhatsApp.

Mensagem do cliente: {mensagem_cliente}

Analise a mensagem e identifique a intenção principal do cliente. Escolha uma das seguintes categorias:
{categorias}

Responda apenas com a categoria, sem explicações adicionais.
```

### 3.4. Estrutura de Crews por Canal

Cada canal tem sua própria crew completa, com agentes, tasks e tools específicos, seguindo o padrão CrewAI:

```python
# src/crews/whatsapp/whatsapp_crew.py
from crewai import Crew, Agent, Task, Process
from src.crews.base_crew import BaseCrew

class WhatsAppCrew(BaseCrew):
    """
    Crew especializada para processamento de mensagens do WhatsApp.
    """

    def __init__(self, tenant_id, domain, config, credentials):
        super().__init__(tenant_id, domain, config, credentials)
        self.channel = "whatsapp"

        # Inicializar componentes
        self.tools = self._initialize_tools()
        self.agents = self._initialize_agents()
        self.tasks = self._initialize_tasks()
        self.crew = self._initialize_crew()

    def _initialize_tools(self):
        """Inicializa as ferramentas específicas para WhatsApp."""
        tools = {}

        # Ferramentas básicas
        tools["redis_cache"] = self._create_redis_tool()

        # Ferramentas específicas para coleções habilitadas
        if "business_rules" in self.enabled_collections:
            tools["business_rules"] = self._create_business_rules_tool()

        # ... outras ferramentas

        return tools

    def _initialize_agents(self):
        """Inicializa os agentes específicos para WhatsApp."""
        agents = {}

        # Agente de intenção (sempre presente)
        intention_prompt = self.prompt_builder.build(
            template_path="src/prompts/whatsapp/intention.txt",
            mensagem_cliente="{message}",
            categorias="informacao_produto, suporte_tecnico, reclamacao, agendamento, consulta_pedido, duvida_geral"
        )

        agents["intention"] = Agent(
            name="intention_agent",
            description="Identifica a intenção do cliente",
            llm=self.llm,
            prompt_template=intention_prompt
        )

        # Agentes específicos para coleções habilitadas
        if "business_rules" in self.enabled_collections:
            business_rules_prompt = self.prompt_builder.build(
                template_path="src/prompts/whatsapp/business_rules.txt",
                # ... variáveis
            )

            agents["business_rules"] = Agent(
                name="business_rules_agent",
                description="Consulta regras de negócio",
                llm=self.llm,
                prompt_template=business_rules_prompt,
                tools=[self.tools["business_rules"]]
            )

        # ... outros agentes

        return agents

    def _initialize_tasks(self):
        """Inicializa as tarefas específicas para WhatsApp."""
        tasks = {}

        # Tarefa de intenção (sempre executada primeiro)
        tasks["intention"] = Task(
            description="Identifique a intenção do cliente na mensagem",
            expected_output="Classificação da intenção do cliente",
            agent=self.agents["intention"],
            async_execution=False  # Esta tarefa deve ser executada primeiro
        )

        # Tarefas específicas para coleções habilitadas
        if "business_rules" in self.enabled_collections:
            tasks["business_rules"] = Task(
                description="Consulte regras de negócio relevantes",
                expected_output="Regras de negócio aplicáveis",
                agent=self.agents["business_rules"],
                async_execution=True,  # Execução paralela
                depends_on=[tasks["intention"]]  # Usa depends_on em vez de context
            )

        # ... outras tarefas

        return tasks

    def _initialize_crew(self):
        """Inicializa a crew com os agentes e tarefas configurados."""
        return Crew(
            agents=list(self.agents.values()),
            tasks=list(self.tasks.values()),
            process=Process.parallel,  # Processamento paralelo
            verbose=True
        )

    async def process_message(self, message, conversation):
        """Processa uma mensagem do WhatsApp."""
        # Pré-processar mensagem
        processed_message = await self._preprocess_message(message, conversation)

        # Executar a crew
        result = await self.crew.kickoff(inputs=processed_message)

        # Pós-processar resultado
        return self._postprocess_result(result)
```

## 4. Implementação do Config Cache

```python
# src/core/cache/config_cache.py
import threading
import time
import json
import requests
import logging
import os
import yaml
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigCache:
    """
    Cache para configurações e mapeamentos com suporte a invalidação.
    """

    def __init__(self, config_service_url, refresh_interval=300):
        """
        Inicializa o cache.

        Args:
            config_service_url: URL do serviço de configuração
            refresh_interval: Intervalo de atualização periódica em segundos
        """
        self.config_service_url = config_service_url
        self.refresh_interval = refresh_interval
        self.mapping_cache = {}
        self.account_mapping_cache = {}
        self.inbox_mapping_cache = {}
        self.config_cache = {}
        self.last_refresh = 0
        self.lock = threading.RLock()

        # Iniciar job de atualização periódica
        self._start_refresh_job()

    # ... métodos do cache (como no documento original)
```

## 5. Vantagens da Nova Estrutura

1. **Modularidade**: Cada componente tem uma responsabilidade clara e bem definida.

2. **Simplicidade**: Uso de `str.format()` para prompts, sem dependências externas.

3. **Desempenho**: Cache eficiente e prompts simples para melhor performance.

4. **Organização por Canal**: Estrutura que segue o padrão CrewAI com crews separadas por canal.

5. **Testabilidade**: Estrutura que facilita a criação de testes unitários e de integração.

6. **Manutenibilidade**: Código limpo e bem organizado, facilitando a manutenção.

7. **Resiliência**: Mecanismos de fallback para garantir funcionamento mesmo em caso de falhas.

8. **Caminho de Evolução Claro**: Possibilidade de migrar para Jinja2 no futuro quando necessário.

## 6. Arquitetura de Comunicação entre Serviços

### 6.1. Fluxo de Recuperação de Configurações

A arquitetura do sistema foi projetada para ser modular, segura e eficiente na recuperação de configurações específicas para cada tenant. O fluxo de comunicação entre os componentes segue o seguinte padrão:

```
Chatwoot → Webhook → Coordinator → Config-Service API → PostgreSQL
                                  ↓
                                Redis Cache
```

#### 6.1.1. Processo Detalhado

1. **Recebimento da Mensagem**:
   - O Chatwoot envia uma mensagem para o webhook com o `account_id` do tenant
   - O webhook extrai o `account_id` e passa para o coordinator

2. **Recuperação de Configurações**:
   - O coordinator verifica se a configuração está no cache Redis
   - Se não estiver, faz uma requisição HTTP para o config-service: `GET /configs/{account_id}/config`
   - O config-service consulta o PostgreSQL e retorna a configuração em JSON
   - O coordinator armazena a configuração no cache Redis para uso futuro

3. **Criação da Crew**:
   - Com a configuração obtida, o coordinator cria a crew específica para o tenant
   - A crew é inicializada com os agentes, ferramentas e tarefas definidos na configuração

4. **Processamento da Mensagem**:
   - A crew processa a mensagem usando a configuração específica do tenant
   - A resposta é enviada de volta para o Chatwoot

#### 6.1.2. Vantagens desta Abordagem

- **Separação de Responsabilidades**: Cada componente tem uma função clara e bem definida
- **Segurança**: As credenciais do banco de dados ficam isoladas no config-service
- **Performance**: O cache Redis reduz a necessidade de consultas frequentes ao banco de dados
- **Manutenção**: Cada serviço pode ser atualizado independentemente
- **Escalabilidade**: A arquitetura suporta o crescimento do número de tenants sem alterações significativas

### 6.2. Implementação do Config-Service Client

O coordinator se comunica com o config-service através de um cliente HTTP dedicado:

```python
# src/core/clients/config_service_client.py
class ConfigServiceClient:
    """
    Cliente para o serviço de configuração.
    """

    def __init__(self, base_url, api_key):
        """
        Inicializa o cliente.

        Args:
            base_url: URL base do serviço de configuração
            api_key: Chave de API para autenticação
        """
        self.base_url = base_url
        self.api_key = api_key
        self.http_client = httpx.AsyncClient(
            headers={"X-API-Key": api_key},
            timeout=10.0
        )

    async def get_config(self, tenant_id, config_type):
        """
        Obtém uma configuração do serviço.

        Args:
            tenant_id: ID do tenant
            config_type: Tipo de configuração

        Returns:
            Configuração ou None se não encontrada
        """
        url = f"{self.base_url}/configs/{tenant_id}/{config_type}"

        try:
            response = await self.http_client.get(url)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.error(f"Erro ao obter configuração: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Erro na comunicação com o serviço de configuração: {str(e)}")
            return None
```

### 6.3. Modelo de Dados Multi-Tenant

O config-service utiliza um modelo de dados multi-tenant eficiente:

```sql
CREATE TABLE configurations (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    config_type VARCHAR(50) NOT NULL,
    config_data JSONB NOT NULL,
    version INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, config_type, version)
);

CREATE INDEX idx_configurations_tenant ON configurations(tenant_id);
```

Esta estrutura permite:
- Armazenar configurações para múltiplos tenants em uma única tabela
- Manter versões históricas das configurações
- Consultas eficientes por tenant_id
- Armazenamento flexível de dados em formato JSON

### 6.4. Configuração via Environment Variables

As credenciais e URLs são configuradas via variáveis de ambiente:

```python
# src/config.py
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do serviço de configuração
CONFIG_SERVICE_URL = os.getenv("CONFIG_SERVICE_URL", "http://config-service:8002")
CONFIG_SERVICE_API_KEY = os.getenv("CONFIG_SERVICE_API_KEY", "development-api-key")

# Configurações do Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_TTL = int(os.getenv("REDIS_TTL", "300"))  # 5 minutos
```

Esta abordagem permite configurar o sistema para diferentes ambientes (desenvolvimento, teste, produção) sem alterar o código.

## 7. Oportunidades de Melhoria

### 7.1. Monitoramento e Observabilidade

- Adicionar instrumentação mais robusta para telemetria
- Implementar tracing distribuído para rastrear fluxos entre microsserviços

### 7.2. Gerenciamento de Configuração

- Considerar usar ferramentas como etcd ou Consul para configuração distribuída
- Implementar validação de schema para configurações

### 7.3. Segurança

- Expandir detalhes sobre autenticação entre serviços
- Adicionar rate limiting e proteção contra ataques

### 7.4. Escalabilidade Avançada

- Considerar implementação de filas de mensagens (RabbitMQ/Kafka) para comunicação assíncrona
- Estratégias de particionamento para tenants muito grandes

### 7.5. Containerização e CI/CD

- Adicionar Dockerfiles e docker-compose
- Implementar pipeline de CI/CD para automação de implantação

## 8. Recomendações para Evoluir a Arquitetura

### 8.1. Autenticação e Autorização

- Implementar OAuth2 ou JWT para autenticação entre serviços
- Adicionar RBAC para controle de acesso granular

### 8.2. Gerenciamento de Filas

- Implementar um sistema de filas como RabbitMQ ou Kafka para comunicação assíncrona
- Adicionar "retry policies" para operações que podem falhar

### 8.3. Observabilidade

- Integrar com ferramentas como Prometheus para métricas
- Implementar rastreamento distribuído com OpenTelemetry

### 8.4. Deployment e Infraestrutura

- Adicionar Dockerfiles e Kubernetes manifests
- Implementar infraestrutura como código (Terraform/Pulumi)

### 8.5. Testes Automatizados

- Expandir testes unitários, integração e e2e
- Implementar testes de carga para verificar escalabilidade

### 8.6. Versioning de API

- Adicionar versionamento explícito de APIs
- Implementar estratégia de migração para atualizações

## 9. Plano de Módulos Odoo

### 9.1. Divisão de Responsabilidades

Para garantir uma separação clara de responsabilidades e facilitar a manutenção, os módulos Odoo serão divididos da seguinte forma:

#### 9.1.1. Módulo de Dados da Empresa e Atendimento

```
@addons/company_config/
├── models/
│   ├── company_config.py    # Modelo principal para dados da empresa
│   ├── config_service.py    # Cliente para config-service
│   └── sync_service.py      # Serviço de sincronização
├── controllers/
│   └── sync_controller.py   # Controlador para sincronização
├── security/
│   ├── ir.model.access.csv
│   └── security.xml
├── views/
│   ├── company_config_views.xml
│   ├── res_config_settings_views.xml  # Configurações do módulo
│   └── menu_views.xml
└── __manifest__.py
```

Este módulo será responsável por:
- Gerenciar dados da empresa e configurações de atendimento
- Sincronizar esses dados com o config-service
- Armazenar os dados no PostgreSQL via config-service

#### 9.1.2. Módulo de Regras de Negócio

```
@addons/business_rules_ai/
├── models/
│   ├── business_rule.py     # Modelo principal para regras de negócio
│   ├── vectorization_service.py  # Cliente para serviço de vetorização
│   └── sync_service.py      # Serviço de sincronização
├── controllers/
│   └── sync_controller.py   # Controlador para sincronização
├── security/
│   ├── ir.model.access.csv
│   └── security.xml
├── views/
│   ├── business_rule_views.xml
│   ├── res_config_settings_views.xml  # Configurações do módulo
│   └── menu_views.xml
└── __manifest__.py
```

Este módulo será responsável por:
- Gerenciar regras de negócio
- Sincronizar essas regras com o serviço de vetorização
- Permitir a criação e edição de regras de negócio

### 9.2. Configuração de Credenciais em Settings

Cada módulo terá suas próprias configurações independentes usando o modelo `res.config.settings` do Odoo, que é a forma padrão de adicionar configurações a módulos Odoo.

#### 9.2.1. Exemplo de Implementação para o Módulo de Dados da Empresa

```python
# Em company_config/models/res_config_settings.py
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Campos de configuração para o serviço
    company_config_service_url = fields.Char(
        string='URL do Serviço de Configuração',
        help="URL do serviço de configuração (ex: http://localhost:8002)",
        config_parameter='company_config.service_url'
    )

    company_config_service_api_key = fields.Char(
        string='Chave de API do Serviço de Configuração',
        help="Chave de API para autenticação no serviço de configuração",
        config_parameter='company_config.service_api_key'
    )
```

```xml
<!-- Em company_config/views/res_config_settings_views.xml -->
<odoo>
    <record id="res_config_settings_view_form" model="ir.ui.view">
        <field name="name">res.config.settings.view.form.inherit.company.config</field>
        <field name="model">res.config.settings</field>
        <field name="priority" eval="70"/>
        <field name="inherit_id" ref="base.res_config_settings_view_form"/>
        <field name="arch" type="xml">
            <xpath expr="//div[hasclass('settings')]" position="inside">
                <div class="app_settings_block" data-string="Configuração da Empresa" string="Configuração da Empresa" data-key="company_config">
                    <h2>Serviço de Configuração</h2>
                    <div class="row mt16 o_settings_container">
                        <div class="col-12 col-lg-6 o_setting_box">
                            <div class="o_setting_left_pane"/>
                            <div class="o_setting_right_pane">
                                <span class="o_form_label">URL do Serviço</span>
                                <div class="text-muted">
                                    URL do serviço de configuração
                                </div>
                                <div class="content-group">
                                    <div class="mt16">
                                        <field name="company_config_service_url" class="o_light_label" placeholder="http://localhost:8002"/>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-12 col-lg-6 o_setting_box">
                            <div class="o_setting_left_pane"/>
                            <div class="o_setting_right_pane">
                                <span class="o_form_label">Chave de API</span>
                                <div class="text-muted">
                                    Chave de API para autenticação
                                </div>
                                <div class="content-group">
                                    <div class="mt16">
                                        <field name="company_config_service_api_key" class="o_light_label" password="True" placeholder="development-api-key"/>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </xpath>
        </field>
    </record>
</odoo>
```

#### 9.2.2. Uso das Configurações no Código

```python
# Em company_config/models/sync_service.py
from odoo import models, fields, api, _
import requests
import logging

_logger = logging.getLogger(__name__)

class CompanyConfigSyncService(models.AbstractModel):
    _name = 'company.config.sync.service'
    _description = 'Serviço de Sincronização de Configurações da Empresa'

    def _get_config_service_url_and_key(self):
        """Obtém a URL e a chave API do serviço de configuração."""
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        url = IrConfigParam.get_param('company_config.service_url', '')
        api_key = IrConfigParam.get_param('company_config.service_api_key', 'development-api-key')

        return url, api_key

    def sync_company_data(self, company_data, account_id):
        """Sincroniza dados da empresa com o serviço de configuração."""
        url, api_key = self._get_config_service_url_and_key()
        if not url:
            return {'success': False, 'error': 'URL do serviço de configuração não configurada'}

        # Construir o endpoint
        endpoint = f"{url}/configs/{account_id}/metadata"

        # Preparar headers
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }

        # Fazer a requisição
        try:
            response = requests.post(
                endpoint,
                json={'yaml_content': company_data},
                headers=headers,
                timeout=30
            )

            if response.status_code in (200, 201):
                return {'success': True, 'message': 'Dados sincronizados com sucesso'}
            else:
                return {'success': False, 'error': f"Erro na API: {response.status_code} - {response.text}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}
```

### 9.3. Vantagens desta Abordagem

1. **Independência**: Cada módulo gerencia suas próprias configurações
2. **Flexibilidade**: Novos módulos podem ser adicionados sem modificar os existentes
3. **Manutenção**: Mais fácil de manter, pois as mudanças são isoladas por módulo
4. **Interface Padrão do Odoo**: Usa a interface de configurações padrão do Odoo
5. **Segurança**: Cada módulo pode ter suas próprias permissões de acesso

## 10. Próximos Passos

1. Implementar a estrutura básica do sistema
2. Migrar a lógica do webhook handler para o novo formato
3. Implementar o sistema de gerenciamento de prompts simplificado
4. Criar as crews especializadas por canal
5. Implementar o cache de configurações
6. Desenvolver testes unitários e de integração
7. Criar scripts de automação para desenvolvimento e implantação
