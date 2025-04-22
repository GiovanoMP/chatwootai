# Guia de Configuração YAML do Sistema Integrado Odoo-AI

Este documento descreve a estrutura, geração e uso dos arquivos YAML de configuração utilizados pelo sistema integrado Odoo-AI.

## Estrutura de Diretórios

```
config/
├── domains/
│   ├── retail/
│   │   ├── account_1/
│   │   │   ├── config.yaml         # Configurações gerais da empresa
│   │   │   ├── credentials.yaml    # Credenciais sensíveis (criptografadas)
│   │   │   └── crews/              # Configurações específicas para crews de IA
│   │   │       └── customer_service/
│   │   │           └── config.yaml # Configurações para o serviço de atendimento
│   │   ├── account_2/
│   │   │   └── ...
│   ├── healthcare/
│   │   └── ...
│   └── education/
│       └── ...
└── chatwoot_mapping.yaml           # Mapeamento de contas do Chatwoot
```

## Arquivos YAML Principais

O sistema utiliza dois arquivos YAML principais para cada conta de cliente:

### 1. `config.yaml`

Este arquivo contém configurações gerais da empresa, incluindo:

- Informações básicas (nome, descrição)
- Metadados da empresa (horários de funcionamento, canais online, estilo de comunicação)
- Referências para credenciais (não as credenciais em si)
- Configurações de integração com sistemas externos

**Exemplo:**

```yaml
account_id: account_1
name: Sandra Cosméticos
description: Comercializamos cosméticos online e presencialmente...
company_metadata:
  business_hours:
    days: [0, 1, 2, 3, 4, 5, 6]
    start_time: 09:00
    end_time: '18:00'
    has_lunch_break: true
  customer_service:
    communication_style: formal
    emoji_usage: none
    greeting_message: Olá! Obrigada por entar em contato...
integrations:
  mcp:
    type: odoo-mcp
    config:
      credential_ref: account_1-00bfe67a  # Referência à credencial
      db: account_1
      url: http://localhost:8069
      username: user@example.com
  facebook:
    app_id: '12345678910'
    app_secret_ref: fb_secret_account_1  # Referência à credencial
    access_token_ref: fb_token_account_1 # Referência à credencial
```

### 2. `credentials.yaml`

Este arquivo contém credenciais sensíveis, todas criptografadas:

- Senhas de acesso ao Odoo
- Tokens de API para redes sociais
- Chaves secretas para integrações externas

**Exemplo:**

```yaml
account_id: account_1
credentials:
  account_1-00bfe67a: ENC:Z0FBQUFBQm9COVloN19tSFJaYS1lRDNUV3I0M19qbUNXN3U1NUJDc2Q4eUlsSHBhTFQ1eW5rbnVpZWhkMlZVUDIxODlxei1IYWZ1amw4VTlBT3lDU2VCZWJ0UFFsdlBzOEE9PQ==
  fb_secret_account_1: ENC:Z0FBQUFBQm9COVloSmRoekJTWEpTd3hCM0lQdko0WEVvSzNoRVdBT1ZKM1FORUstU2MzX0FISjZQcXlYNHYyalp6aVMwamJqRUs5ZklXai0xZ3V1TVpnU194blBvUnJiQ2c9PQ==
  fb_token_account_1: ENC:Z0FBQUFBQm9COVloMHppdmNfcE1lRTB6WVJkMHpaeWlqd0xqUFhzOVk5N2YxT1JJVjAxdXE0UHJYRllOU0FBUDViOGVPaFVYM1dVNFlmQ1VrMEc0cThOSmRiQ1BpdDFPd3c9PQ==
```

## Geração Automática

Ambos os arquivos YAML são gerados e atualizados automaticamente pelo sistema, sem necessidade de intervenção manual:

1. **Módulo Odoo `ai_credentials_manager`**:
   - Envia credenciais para o sistema de IA via webhook
   - As credenciais são verificadas com assinatura HMAC
   - O sistema de IA criptografa as credenciais e as salva em `credentials.yaml`
   - Referências às credenciais são adicionadas ao `config.yaml`

2. **Módulo Odoo `business_rules`**:
   - Envia metadados da empresa para o sistema de IA via webhook
   - Os metadados são processados e salvos em `config.yaml`
   - Regras de negócio são vetorizadas e armazenadas no Qdrant

Este processo automatizado garante que:
- Não é necessário editar manualmente os arquivos YAML
- As configurações são sempre sincronizadas com o Odoo
- As credenciais sensíveis são sempre criptografadas

## Aspectos de Segurança

### Separação de Configurações e Credenciais

A separação em dois arquivos distintos (`config.yaml` e `credentials.yaml`) implementa o princípio de separação de responsabilidades:

- `config.yaml`: Contém apenas configurações não sensíveis e referências a credenciais
- `credentials.yaml`: Contém apenas credenciais sensíveis, todas criptografadas

### Criptografia de Credenciais

Todas as credenciais no arquivo `credentials.yaml` são criptografadas usando:

- Algoritmo AES-256 em modo GCM (Galois/Counter Mode)
- Chave de criptografia armazenada como variável de ambiente (`ENCRYPTION_KEY`)
- Prefixo `ENC:` para identificar valores criptografados

### Autenticação de Webhooks

A comunicação entre o Odoo e o sistema de IA é protegida por:

- Assinatura HMAC-SHA256 para verificar a autenticidade dos payloads
- Chave secreta compartilhada entre o Odoo e o sistema de IA
- Verificação de tokens para garantir que apenas sistemas autorizados possam atualizar as configurações

### Proteção Contra Sobrescrita

O sistema pode ser configurado para impedir a sobrescrita não autorizada de tokens:

- Variável de ambiente `ALLOW_TOKEN_OVERWRITE` controla se tokens existentes podem ser sobrescritos
- Tentativas de sobrescrita são registradas em logs de auditoria
- Proteção adicional contra ataques de substituição de tokens

## Relação Entre os Arquivos

Os arquivos `config.yaml` e `credentials.yaml` se relacionam através de referências:

1. O arquivo `config.yaml` contém referências às credenciais (ex: `credential_ref: account_1-00bfe67a`)
2. Estas referências apontam para chaves no arquivo `credentials.yaml`
3. Quando o sistema precisa usar uma credencial:
   - Lê a referência do `config.yaml`
   - Busca a credencial criptografada no `credentials.yaml`
   - Descriptografa a credencial antes de usá-la

Este mecanismo garante que:
- Credenciais sensíveis nunca são expostas em texto claro
- Configurações e credenciais podem ser atualizadas independentemente
- O sistema pode acessar as credenciais quando necessário, sem comprometer a segurança

## Uso com CrewAI

O arquivo `config.yaml` é especialmente projetado para fornecer contexto aos agentes de IA, incluindo sistemas como o CrewAI:

### 1. Contexto para Agentes Especializados

Diferentes seções do arquivo fornecem contexto para diferentes tipos de agentes:

- `company_metadata.customer_service`: Contexto para agentes de atendimento ao cliente
  - Estilo de comunicação
  - Uso de emojis
  - Mensagem de saudação

- `company_metadata.business_hours`: Contexto para agentes de agendamento
  - Dias e horários de funcionamento
  - Intervalos de almoço
  - Horários especiais para fins de semana

- `integrations`: Contexto para agentes que interagem com sistemas externos
  - Configurações do MCP para interação com Odoo
  - Configurações de redes sociais para marketing

### 2. Implementação com CrewAI

```python
from crewai import Agent, Task, Crew
import yaml

# Carregar contexto da empresa
def load_company_context(account_id):
    config_path = f"config/domains/retail/{account_id}/config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Criar agentes com contexto específico
def create_customer_service_crew(account_id):
    context = load_company_context(account_id)
    
    # Agente de intenção usa o contexto de atendimento
    intention_agent = Agent(
        name="Intention Agent",
        role=f"Customer Service for {context['name']}",
        goal="Identify customer intentions",
        backstory=f"You work for {context['name']} and greet customers with: '{context['company_metadata']['customer_service']['greeting_message']}'",
        verbose=True
    )
    
    # Agente MCP usa o contexto de integração com Odoo
    mcp_agent = Agent(
        name="MCP Agent",
        role="Odoo Specialist",
        goal="Execute operations in Odoo",
        backstory=f"You connect to the Odoo system for {context['name']} using the MCP integration",
        tools=[OdooMCPTool(context['integrations']['mcp'])],
        verbose=True
    )
    
    # Criar a crew com os agentes
    crew = Crew(
        agents=[intention_agent, mcp_agent],
        tasks=[...],  # Tarefas definidas separadamente
        verbose=True
    )
    
    return crew
```

### 3. Benefícios para Agentes de IA

- **Personalização**: Cada cliente tem seu próprio contexto personalizado
- **Consistência**: Os agentes sempre usam as informações mais atualizadas da empresa
- **Segurança**: Os agentes acessam apenas as referências às credenciais, não as credenciais em si
- **Flexibilidade**: Novos tipos de agentes podem ser adicionados sem alterar a estrutura do YAML

## Exemplo de Ferramenta MCP para CrewAI

```python
from crewai.tools import BaseTool
from odoo_api.core.odoo_connector import OdooConnector

class OdooMCPTool(BaseTool):
    name = "Odoo MCP Tool"
    description = "Execute operations in the Odoo ERP system"
    
    def __init__(self, mcp_config):
        super().__init__()
        self.mcp_config = mcp_config
        
    def _run(self, action, model, method, params=None):
        """
        Execute an action in Odoo via MCP.
        
        Args:
            action: Type of action (search, read, create, write, etc.)
            model: Odoo model name (res.partner, product.template, etc.)
            method: Method to call on the model
            params: Parameters for the method
            
        Returns:
            Result from Odoo
        """
        # Criar conector Odoo usando as configurações do YAML
        connector = OdooConnector(
            url=self.mcp_config['config']['url'],
            db=self.mcp_config['config']['db'],
            username=self.mcp_config['config']['username'],
            credential_ref=self.mcp_config['config']['credential_ref']
        )
        
        # Executar a ação solicitada
        if action == "search":
            return connector.search(model, params.get("domain", []))
        elif action == "read":
            return connector.read(model, params.get("ids", []), params.get("fields", []))
        elif action == "create":
            return connector.create(model, params.get("values", {}))
        elif action == "write":
            return connector.write(model, params.get("ids", []), params.get("values", {}))
        else:
            return connector.execute_kw(model, method, params or [])
```

## Melhores Práticas

1. **Nunca edite manualmente** os arquivos YAML - use sempre o Odoo para atualizar as configurações
2. **Não armazene** os arquivos YAML em repositórios públicos
3. **Mantenha a chave de criptografia** em um local seguro e nunca a inclua no código-fonte
4. **Faça backup regular** dos arquivos YAML, especialmente antes de atualizações do sistema
5. **Monitore os logs** para detectar tentativas não autorizadas de modificar as configurações

## Conclusão

Os arquivos YAML de configuração são o coração do sistema integrado Odoo-AI, fornecendo uma ponte segura entre o Odoo e os agentes de IA. A geração automática, a criptografia de credenciais e a separação de responsabilidades garantem que o sistema seja seguro, flexível e fácil de manter.

Para mais informações sobre a implementação de segurança, consulte o arquivo `src/utils/README.md`.
