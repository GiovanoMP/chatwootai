# Proposta de Nova Estrutura do Sistema ChatwootAI

## 1. Visão Geral

Esta proposta detalha uma nova estrutura para o sistema ChatwootAI após o desacoplamento dos componentes odoo-api e mcp-odoo como microsserviços. O objetivo é criar um sistema limpo, modular e fácil de manter, com foco em uma arquitetura que facilite a escalabilidade e a manutenção por um desenvolvedor solo.

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
│   │   └── crew_factory.py      # Fábrica de crews
│   ├── crews/
│   │   ├── base_crew.py         # Classe base para todas as crews
│   │   ├── whatsapp_crew.py     # Implementação da WhatsApp Crew
│   │   ├── instagram_crew.py    # Implementação da Instagram Crew
│   │   └── default_crew.py      # Crew padrão para fallback
│   ├── agents/
│   │   ├── base_agent.py        # Classe base para todos os agentes
│   │   ├── intention_agent.py   # Agente de identificação de intenção
│   │   ├── vector_agent.py      # Classe base para agentes vetoriais
│   │   ├── business_rules_agent.py  # Agente de regras de negócio
│   │   ├── mcp_agent.py         # Agente para comunicação com MCP
│   │   └── response_agent.py    # Agente de resposta
│   ├── tools/
│   │   ├── base_tool.py         # Classe base para ferramentas
│   │   ├── qdrant_tool.py       # Ferramenta para Qdrant
│   │   ├── mcp_tool.py          # Ferramenta para MCP-Odoo
│   │   └── redis_tool.py        # Ferramenta para Redis
│   ├── prompting/               # Gerenciamento de prompts
│   │   ├── prompt_builder.py    # Classe para construção de prompts
│   │   └── templates/           # Templates de prompts
│   │       ├── pt/              # Templates em português
│   │       │   ├── whatsapp_intention.j2
│   │       │   ├── business_rules.j2
│   │       │   └── response.j2
│   │       └── en/              # Templates em inglês
│   │           ├── whatsapp_intention.j2
│   │           └── response.j2
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

### 3.2. Sistema de Gerenciamento de Prompts

O novo diretório `prompting/` contém um sistema completo para gerenciamento de prompts usando Jinja2, permitindo a criação de prompts dinâmicos e multilíngues.

```python
# src/prompting/prompt_builder.py
import jinja2
import os
from typing import Dict, Any, Optional

class PromptBuilder:
    """
    Classe responsável por construir prompts dinâmicos usando templates Jinja2.
    """
    
    def __init__(self, templates_dir: str = None):
        """
        Inicializa o PromptBuilder.
        
        Args:
            templates_dir: Diretório contendo os templates de prompts.
                           Se None, usa o diretório padrão.
        """
        if templates_dir is None:
            # Obter o diretório do módulo atual
            current_dir = os.path.dirname(os.path.abspath(__file__))
            templates_dir = os.path.join(current_dir, "templates")
        
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            autoescape=False,  # Desabilitar escape automático para prompts
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Registrar filtros personalizados
        self._register_custom_filters()
    
    def _register_custom_filters(self):
        """Registra filtros personalizados para uso nos templates."""
        # Exemplo: filtro para formatar listas em texto
        def format_list(items, bullet="•"):
            return "\n".join(f"{bullet} {item}" for item in items)
        
        self.env.filters["format_list"] = format_list
    
    def build_prompt(self, template_name: str, language: str = "pt", **kwargs) -> str:
        """
        Constrói um prompt a partir de um template.
        
        Args:
            template_name: Nome do template (sem extensão)
            language: Código do idioma (pt, en, etc.)
            **kwargs: Variáveis a serem passadas para o template
            
        Returns:
            Prompt renderizado
        """
        template_path = f"{language}/{template_name}.j2"
        try:
            template = self.env.get_template(template_path)
            return template.render(**kwargs)
        except jinja2.exceptions.TemplateNotFound:
            # Fallback para o idioma padrão se o template não existir no idioma solicitado
            if language != "pt":
                return self.build_prompt(template_name, "pt", **kwargs)
            # Se já estamos no idioma padrão, propagar o erro
            raise
```

### 3.3. Exemplo de Template de Prompt

```jinja
{# templates/pt/whatsapp_intention.j2 #}
Você é um assistente especializado em identificar a intenção do cliente em mensagens do WhatsApp.

Mensagem do cliente: {{ message }}

{% if context and context.history %}
Histórico da conversa:
{% for msg in context.history %}
{{ msg.role }}: {{ msg.content }}
{% endfor %}
{% endif %}

Analise a mensagem e identifique a intenção principal do cliente. Escolha uma das seguintes categorias:
- informacao_produto
- suporte_tecnico
- reclamacao
- agendamento
- consulta_pedido
- duvida_geral

Responda apenas com a categoria, sem explicações adicionais.
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
    
    async def get_tenant_info(self, account_id, inbox_id=None) -> Optional[Dict[str, Any]]:
        """
        Obtém informações do tenant com base no account_id e inbox_id.
        
        Args:
            account_id: ID da conta no Chatwoot
            inbox_id: ID da caixa de entrada no Chatwoot (opcional)
            
        Returns:
            Informações do tenant ou None se não encontrado
        """
        self._refresh_if_needed()
        
        # Tentar obter pelo inbox_id primeiro
        if inbox_id:
            tenant_info = self.inbox_mapping_cache.get(str(inbox_id))
            if tenant_info:
                return tenant_info
        
        # Se não encontrou pelo inbox_id, tentar pelo account_id
        tenant_info = self.account_mapping_cache.get(str(account_id))
        if tenant_info:
            return tenant_info
        
        # Se não encontrou no cache, tentar fallback local
        return self._get_local_mapping(account_id, inbox_id)
    
    async def get_config(self, tenant_id, domain, config_type) -> Optional[Dict[str, Any]]:
        """
        Obtém configuração para um tenant.
        
        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            config_type: Tipo de configuração
            
        Returns:
            Configuração ou None se não encontrada
        """
        self._refresh_if_needed()
        cache_key = f"{tenant_id}:{domain}:{config_type}"
        config = self.config_cache.get(cache_key)
        
        if config:
            return config
        
        # Se não encontrou no cache, tentar obter do serviço
        try:
            response = requests.get(
                f"{self.config_service_url}/configs/{tenant_id}/{domain}/{config_type}"
            )
            if response.status_code == 200:
                config = response.json()
                self.config_cache[cache_key] = config
                return config
        except Exception as e:
            logger.error(f"Erro ao obter configuração do serviço: {str(e)}")
        
        # Se não conseguiu obter do serviço, tentar fallback local
        return self._get_local_config(tenant_id, domain, config_type)
```

## 5. Vantagens da Nova Estrutura

1. **Modularidade**: Cada componente tem uma responsabilidade clara e bem definida.

2. **Gerenciamento de Prompts**: Sistema dedicado para criação e manutenção de prompts.

3. **Multilinguismo**: Suporte nativo para múltiplos idiomas nos prompts.

4. **Testabilidade**: Estrutura que facilita a criação de testes unitários e de integração.

5. **Manutenibilidade**: Código limpo e bem organizado, facilitando a manutenção.

6. **Desempenho**: Cache eficiente com invalidação por evento para configurações.

7. **Resiliência**: Mecanismos de fallback para garantir funcionamento mesmo em caso de falhas.

## 6. Próximos Passos

1. Implementar a estrutura básica do sistema
2. Migrar a lógica do webhook handler para o novo formato
3. Implementar o sistema de gerenciamento de prompts
4. Criar as crews especializadas
5. Implementar o cache de configurações
6. Desenvolver testes unitários e de integração
7. Criar scripts de automação para desenvolvimento e implantação
