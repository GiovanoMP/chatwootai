# CrewAI Multi-Tenant - Plano de Implementação

Este documento descreve o plano de implementação para a nova arquitetura da CrewAI Multi-Tenant, otimizada para baixa latência, isolamento entre tenants e escalabilidade.

## 1. Visão Geral da Nova Arquitetura

### 1.1 Princípios Fundamentais

- **Uma única crew para todos os tenants** (substituindo múltiplas crews por tenant)
- **Account_ID como chave central** para isolamento de dados e configurações
- **Configurações via YAML** para informações estáticas (substituindo o company_metadata_agent)
- **Acesso direto a dados nas crews** (substituindo o data_proxy_agent centralizado)
- **Processamento paralelo** para reduzir latência
- **Cache em múltiplas camadas** para otimizar desempenho

### 1.2 Fluxo de Processamento

```
Cliente envia pergunta (via Chatwoot ou App)
  |
FastAPI recebe (com account_id)
  |
ConfigLoader busca o YAML (Redis ou local)
  |
Verifica horário de atendimento
  |
Inicia a Crew com:
  🔹 Agente de Intenção → detecta a intenção do cliente
     ├─ Regras? → agente vetorial (rules)
     ├─ Suporte? → agente vetorial (support_documents)
     ├─ Institucional? → informações do YAML
     ├─ Ação no Odoo? → MCP Agent com tools REST
     ├─ Falar com humano? → sinaliza handoff
  |
Finalizador junta tudo, formata com saudação e assina
```

## 2. Estrutura do Projeto

### 2.1 Organização de Diretórios

```
crewai-multi-tenant/
├── app/
│   ├── api/
│   │   └── main.py                 # Entrada FastAPI
│   ├── agents/
│   │   ├── intention_agent.py      # Classificação
│   │   ├── vector_agents.py        # Agentes de busca vetorial
│   │   ├── mcp_agent.py            # Integração com Odoo
│   │   └── response_agent.py       # Finalizador
│   ├── crew/
│   │   ├── crew_factory.py         # Montagem completa
│   │   ├── config_loader.py        # Redis + YAML + Odoo
│   │   ├── memory.py               # Memória por tenant
│   │   └── handoff_detector.py     # Detecta se deve redirecionar para humano
│   ├── tools/
│   │   ├── vector_tools.py         # Conexões Qdrant
│   │   └── mcp_tools.py            # Tools REST Odoo
│   └── utils/
│       └── horario.py              # Verifica horários de atendimento
├── config/
│   └── domains/
│       └── retail/
│           └── account_1/
│               └── config.yaml     # Configuração específica do tenant
├── requirements.txt                # Dependências
├── .env.example                    # OpenAI Key, Redis, etc.
└── README.md                       # Instruções de uso
```

### 2.2 Dependências

```
crewai[tools]
langchain
langchain-openai
langchain-community
fastapi
uvicorn
qdrant-client
redis
python-dotenv
requests
PyYAML
```

## 3. Componentes Principais

### 3.1 Configuração YAML

O arquivo de configuração YAML substituirá o company_metadata_agent, contendo informações estáticas como:

```yaml
# config/domains/retail/account_1/config.yaml
account_id: "account_1"
name: "Loja Exemplo"
domain: "retail"

# Configurações de atendimento
atendimento:
  horarios:
    dias: ["segunda", "terça", "quarta", "quinta", "sexta"]
    horario: "09:00 - 18:00"
    fuso: "America/Sao_Paulo"
  regras:
    atender_fora_do_horario: false

# Configurações de estilo
estilo:
  tone: "formal"  # formal ou informal
  use_emoji: false
  saudacao: "Olá! Bem-vindo à Loja Exemplo."
  assinatura: "Atenciosamente, Equipe de Atendimento"

# Informações institucionais
institucional:
  endereco: "Rua Exemplo, 123 - Centro"
  telefone: "(11) 1234-5678"
  email: "contato@exemplo.com"
  sobre: "A Loja Exemplo é especializada em produtos de alta qualidade desde 2010."

# Integrações
integracoes:
  mcp:
    url: "http://localhost:9000"
    timeout: 3
  qdrant:
    collections:
      - "business_rules"
      - "support_documents"
```

### 3.2 Agentes Especializados

#### 3.2.1 Agente de Intenção

```python
from crewai import Agent

def build_intention_agent(config):
    return Agent(
        role="Classificador de Intenção",
        goal="Detectar a intenção do cliente e direcionar para o agente apropriado",
        backstory="Você analisa mensagens e identifica precisamente o que o cliente deseja.",
        verbose=True
    )
```

#### 3.2.2 Agentes Vetoriais

```python
from crewai import Agent
from app.tools.vector_tools import get_vector_tool

def build_rules_agent(account_id):
    return Agent(
        role="Especialista em Regras de Negócio",
        goal="Encontrar regras de negócio relevantes para a consulta do cliente",
        backstory="Você conhece todas as políticas, promoções e regras da empresa.",
        tools=[get_vector_tool("business_rules", account_id)],
        verbose=True
    )

def build_support_agent(account_id):
    return Agent(
        role="Especialista em Suporte",
        goal="Encontrar informações de suporte relevantes para a consulta do cliente",
        backstory="Você é especializado em resolver problemas técnicos e dúvidas sobre produtos.",
        tools=[get_vector_tool("support_documents", account_id)],
        verbose=True
    )
```

#### 3.2.3 Agente MCP

```python
from crewai import Agent
from app.tools.mcp_tools import get_mcp_tools

def build_mcp_agent(account_id, config):
    mcp_url = config["integracoes"]["mcp"]["url"]
    return Agent(
        role="Agente de Integração com Odoo",
        goal="Executar ações no sistema Odoo conforme solicitado pelo cliente",
        backstory="Você tem acesso ao sistema Odoo e pode realizar consultas e operações.",
        tools=get_mcp_tools(account_id, mcp_url),
        verbose=True
    )
```

#### 3.2.4 Agente de Resposta

```python
from crewai import Agent

def build_response_agent(config):
    estilo = config["estilo"]
    tone = "informal" if estilo.get("tone") == "informal" else "formal"
    emojis = "Use emojis ocasionalmente. 😊" if estilo.get("use_emoji") else "Não use emojis."

    return Agent(
        role="Finalizador de Atendimento",
        goal="Formular uma resposta final clara, cordial e personalizada para o cliente",
        backstory=f"Você é um especialista em atendimento ao cliente com tom {tone}. "
                 f"Você sempre inicia com '{estilo['saudacao']}' e finaliza com '{estilo['assinatura']}'. {emojis}",
        verbose=True
    )
```

### 3.3 Ferramentas Especializadas

#### 3.3.1 Ferramentas Vetoriais

```python
from langchain.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from crewai_tools import VectorStoreTool

embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
qdrant_client = QdrantClient(host="localhost", port=6333)

def get_vector_tool(collection_name, account_id):
    descriptions = {
        "business_rules": "Busca regras de negócio, políticas e promoções da empresa",
        "support_documents": "Busca documentos de suporte, manuais e FAQs"
    }

    return VectorStoreTool(
        name=f"{collection_name.capitalize()} Tool",
        description=descriptions.get(collection_name, f"Busca em {collection_name}"),
        vectorstore=Qdrant(
            client=qdrant_client,
            collection_name=collection_name,
            embeddings=embedding_model,
            metadata_filter={"account_id": account_id}
        ),
        top_k=3
    )
```

#### 3.3.2 Ferramentas MCP

```python
from crewai_tools import BaseTool
import requests

class MCPTool(BaseTool):
    def __init__(self, name, description, endpoint, mcp_url, account_id, method="GET"):
        self.endpoint = endpoint
        self.mcp_url = mcp_url
        self.account_id = account_id
        self.method = method
        super().__init__(name=name, description=description)

    def _run(self, **kwargs):
        url = f"{self.mcp_url}/{self.endpoint}"
        headers = {"X-Account-ID": self.account_id}

        try:
            if self.method == "GET":
                response = requests.get(url, params=kwargs, headers=headers, timeout=3)
            else:
                response = requests.post(url, json=kwargs, headers=headers, timeout=3)

            return response.json()
        except Exception as e:
            return f"Erro ao acessar o MCP: {str(e)}"

def get_mcp_tools(account_id, mcp_url):
    return [
        MCPTool(
            name="ConsultaProduto",
            description="Consulta informações sobre um produto no Odoo",
            endpoint="produto/info",
            mcp_url=mcp_url,
            account_id=account_id
        ),
        MCPTool(
            name="ConsultaEstoque",
            description="Verifica a disponibilidade de um produto em estoque",
            endpoint="produto/estoque",
            mcp_url=mcp_url,
            account_id=account_id
        ),
        MCPTool(
            name="CriarPedido",
            description="Cria um novo pedido de venda no Odoo",
            endpoint="venda/criar",
            mcp_url=mcp_url,
            account_id=account_id,
            method="POST"
        )
    ]
```

### 3.4 Memória Redis Multi-Tenant

```python
from langchain.memory.chat_message_histories import RedisChatMessageHistory
from langchain.memory import ConversationBufferMemory

def get_memory(account_id):
    history = RedisChatMessageHistory(
        session_id=f"chat:{account_id}",
        url="redis://localhost:6379"
    )
    return ConversationBufferMemory(
        chat_memory=history,
        return_messages=True,
        memory_key="chat_history"
    )
```

### 3.5 Carregador de Configuração

```python
import os
import yaml
import json
import redis
import requests
from typing import Dict, Any

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_tenant_config(account_id: str) -> Dict[str, Any]:
    """
    Carrega a configuração do tenant com cache Redis.

    Args:
        account_id: ID da conta do tenant

    Returns:
        Configuração do tenant
    """
    # Verificar cache Redis
    cache_key = f"config:{account_id}"
    cached_config = redis_client.get(cache_key)

    if cached_config:
        return json.loads(cached_config)

    # Tentar carregar do arquivo YAML
    yaml_path = f"config/domains/retail/{account_id}/config.yaml"

    if os.path.exists(yaml_path):
        with open(yaml_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)

            # Armazenar em cache
            redis_client.set(cache_key, json.dumps(config), ex=600)  # TTL: 10 minutos

            return config

    # Tentar obter do Odoo via API
    try:
        response = requests.get(
            f"http://localhost:8001/api/v1/config/{account_id}",
            timeout=3
        )

        if response.ok:
            config = response.json()

            # Armazenar em cache
            redis_client.set(cache_key, json.dumps(config), ex=600)

            # Salvar localmente para fallback
            os.makedirs(os.path.dirname(yaml_path), exist_ok=True)
            with open(yaml_path, 'w', encoding='utf-8') as file:
                yaml.dump(config, file)

            return config
    except Exception as e:
        print(f"Erro ao obter configuração do Odoo: {e}")

    # Configuração padrão como fallback
    return {
        "account_id": account_id,
        "name": "Loja Padrão",
        "domain": "retail",
        "atendimento": {
            "horarios": {
                "dias": ["segunda", "terça", "quarta", "quinta", "sexta"],
                "horario": "09:00 - 18:00",
                "fuso": "America/Sao_Paulo"
            },
            "regras": {
                "atender_fora_do_horario": False
            }
        },
        "estilo": {
            "tone": "formal",
            "use_emoji": False,
            "saudacao": "Olá!",
            "assinatura": "Atenciosamente, Equipe de Atendimento"
        }
    }
```

### 3.6 Verificador de Horário

```python
from datetime import datetime
import pytz

def esta_dentro_do_horario(config):
    """
    Verifica se o momento atual está dentro do horário de atendimento.

    Args:
        config: Configuração do tenant

    Returns:
        True se estiver dentro do horário, False caso contrário
    """
    horarios = config["atendimento"]["horarios"]

    # Obter fuso horário
    tz_name = horarios.get("fuso", "America/Sao_Paulo")
    tz = pytz.timezone(tz_name)

    # Obter data e hora atual
    agora = datetime.now(tz)
    dia_semana = agora.strftime("%A").lower()
    hora_atual = agora.strftime("%H:%M")

    # Mapear dias da semana em português
    mapeamento_dias = {
        "monday": "segunda",
        "tuesday": "terça",
        "wednesday": "quarta",
        "thursday": "quinta",
        "friday": "sexta",
        "saturday": "sábado",
        "sunday": "domingo"
    }

    dia_pt = mapeamento_dias.get(dia_semana, dia_semana)

    # Verificar se o dia atual está na lista de dias de atendimento
    if dia_pt not in horarios["dias"]:
        return False

    # Verificar se a hora atual está dentro do horário de atendimento
    inicio, fim = horarios["horario"].split(" - ")

    return inicio <= hora_atual <= fim
```

### 3.7 Fábrica de Crew

```python
from crewai import Crew, Task, Process
from langchain_openai import ChatOpenAI
from app.crew.config_loader import get_tenant_config
from app.crew.memory import get_memory
from app.utils.horario import esta_dentro_do_horario
from app.agents.intention_agent import build_intention_agent
from app.agents.vector_agents import build_rules_agent, build_support_agent
from app.agents.mcp_agent import build_mcp_agent
from app.agents.response_agent import build_response_agent

def build_crew(account_id, pergunta):
    """
    Cria uma crew completa para processar a pergunta do cliente.

    Args:
        account_id: ID da conta do tenant
        pergunta: Pergunta do cliente

    Returns:
        Crew configurada
    """
    # Carregar configuração do tenant
    config = get_tenant_config(account_id)

    # Obter memória do tenant
    memory = get_memory(account_id)

    # Configurar LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    # Criar agentes
    intention_agent = build_intention_agent(config)
    rules_agent = build_rules_agent(account_id)
    support_agent = build_support_agent(account_id)
    mcp_agent = build_mcp_agent(account_id, config)
    response_agent = build_response_agent(config)

    # Criar tarefas
    intention_task = Task(
        description=f"Analise a seguinte pergunta do cliente e identifique a intenção principal: '{pergunta}'",
        agent=intention_agent
    )

    rules_task = Task(
        description=f"Busque regras de negócio relevantes para a pergunta: '{pergunta}'",
        agent=rules_agent,
        async_execution=True
    )

    support_task = Task(
        description=f"Busque documentos de suporte relevantes para a pergunta: '{pergunta}'",
        agent=support_agent,
        async_execution=True
    )

    mcp_task = Task(
        description=f"Execute ações no sistema Odoo se necessário para responder: '{pergunta}'",
        agent=mcp_agent,
        async_execution=True
    )

    response_task = Task(
        description="Formule uma resposta final clara, cordial e personalizada para o cliente",
        agent=response_agent,
        context=[
            {"role": "system", "content": f"Informações institucionais: {config.get('institucional', {})}"}
        ],
        depends_on=[intention_task, rules_task, support_task, mcp_task]
    )

    # Criar crew
    return Crew(
        agents=[intention_agent, rules_agent, support_agent, mcp_agent, response_agent],
        tasks=[intention_task, rules_task, support_task, mcp_task, response_task],
        process=Process.parallel,
        memory=memory,
        verbose=True,
        cache=True
    )
```

### 3.8 API FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.crew.crew_factory import build_crew
from app.crew.config_loader import get_tenant_config
from app.utils.horario import esta_dentro_do_horario

app = FastAPI()

class AtendimentoRequest(BaseModel):
    account_id: str
    pergunta: str

@app.post("/atendimento")
async def atendimento(request: AtendimentoRequest):
    """
    Endpoint para processar perguntas de clientes.

    Args:
        request: Requisição contendo account_id e pergunta

    Returns:
        Resposta da crew
    """
    # Carregar configuração do tenant
    config = get_tenant_config(request.account_id)

    # Verificar horário de atendimento
    if not esta_dentro_do_horario(config):
        atender_fora = config["atendimento"]["regras"].get("atender_fora_do_horario", False)

        if not atender_fora:
            return {
                "resposta": f"{config['estilo']['saudacao']} Estamos fora do horário de atendimento. "
                           f"Nosso horário é {config['atendimento']['horarios']['horario']}. "
                           f"{config['estilo']['assinatura']}"
            }

    # Criar e executar crew
    try:
        crew = build_crew(request.account_id, request.pergunta)
        result = crew.kickoff()

        return {"resposta": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar pergunta: {str(e)}")
```

## 4. Plano de Implementação

### 4.1 Fase 1: Preparação

1. **Configurar ambiente de desenvolvimento**
   - Instalar dependências
   - Configurar variáveis de ambiente
   - Configurar Redis e Qdrant

2. **Criar estrutura de diretórios**
   - Seguir a estrutura proposta
   - Criar arquivos iniciais

3. **Implementar carregador de configuração**
   - Implementar `config_loader.py`
   - Criar arquivos YAML de exemplo

### 4.2 Fase 2: Componentes Básicos

1. **Implementar ferramentas vetoriais**
   - Implementar `vector_tools.py`
   - Testar conexão com Qdrant

2. **Implementar ferramentas MCP**
   - Implementar `mcp_tools.py`
   - Testar conexão com Odoo

3. **Implementar memória Redis**
   - Implementar `memory.py`
   - Testar isolamento entre tenants

4. **Implementar verificador de horário**
   - Implementar `horario.py`
   - Testar com diferentes configurações

### 4.3 Fase 3: Agentes

1. **Implementar agente de intenção**
   - Implementar `intention_agent.py`
   - Testar classificação de intenções

2. **Implementar agentes vetoriais**
   - Implementar `vector_agents.py`
   - Testar busca em coleções do Qdrant

3. **Implementar agente MCP**
   - Implementar `mcp_agent.py`
   - Testar integração com Odoo

4. **Implementar agente de resposta**
   - Implementar `response_agent.py`
   - Testar formatação de respostas

### 4.4 Fase 4: Integração

1. **Implementar fábrica de crew**
   - Implementar `crew_factory.py`
   - Testar criação de crew completa

2. **Implementar API FastAPI**
   - Implementar `main.py`
   - Testar endpoint de atendimento

3. **Implementar detector de handoff**
   - Implementar `handoff_detector.py`
   - Testar redirecionamento para humano

### 4.5 Fase 5: Testes e Otimização

1. **Testes de performance**
   - Medir tempo de resposta
   - Identificar gargalos

2. **Testes de isolamento**
   - Verificar isolamento entre tenants
   - Testar concorrência

3. **Otimizações finais**
   - Ajustar parâmetros
   - Implementar melhorias identificadas

## 5. Métricas de Sucesso

1. **Tempo de resposta**
   - Meta: < 3 segundos para 95% das requisições
   - Monitorar latência de cada componente

2. **Isolamento entre tenants**
   - Zero vazamento de dados entre tenants
   - Configurações isoladas por account_id

3. **Qualidade das respostas**
   - Respostas precisas e relevantes
   - Personalização conforme configuração do tenant

4. **Escalabilidade**
   - Suporte a múltiplos tenants simultâneos
   - Degradação graceful sob carga

## 6. Estratégias para Otimização de Agentes

### 6.1 Gerenciamento de Agentes em Conversas Fluidas

Um desafio importante em conversas fluidas é que os clientes podem alternar entre diferentes tópicos que exigem diferentes agentes. Existem várias estratégias para lidar com isso:

#### 6.1.1 Pré-carregamento Inteligente

- **Pré-carregamento Baseado em Histórico**: Analisar o histórico de conversas do cliente para pré-carregar os agentes mais prováveis de serem necessários
- **Pré-carregamento por Domínio**: Certos domínios de negócio têm padrões previsíveis de consulta que podem informar quais agentes pré-carregar

#### 6.1.2 Carregamento Adaptativo

- **Carregamento em Segundo Plano**: Enquanto o agente de intenção processa a consulta, iniciar o carregamento de outros agentes em segundo plano
- **Cache de Agentes**: Manter um cache LRU (Least Recently Used) de agentes carregados, removendo apenas os menos usados quando necessário

#### 6.1.3 Estratégias de Fallback

- **Agente Universal**: Manter um agente de fallback que pode lidar com consultas gerais enquanto agentes especializados são carregados
- **Resposta em Duas Fases**: Fornecer uma resposta rápida inicial seguida de uma resposta mais detalhada quando todos os agentes estiverem disponíveis

#### 6.1.4 Implementação Recomendada

Para nossa implementação inicial, recomendamos:

1. **Abordagem Híbrida**: Carregar o agente de intenção e o agente de resposta sempre, e carregar os demais agentes conforme necessário
2. **Cache de Sessão**: Manter agentes carregados durante toda a sessão de conversa
3. **Pré-carregamento Baseado em Intenção**: Usar a primeira detecção de intenção para carregar agentes relacionados
4. **Monitoramento de Performance**: Registrar métricas de tempo de carregamento e uso de agentes para otimização contínua

```python
# Exemplo de implementação de cache de agentes
class AgentCache:
    def __init__(self, max_size=10):
        self.cache = {}
        self.max_size = max_size
        self.usage_count = {}

    def get(self, agent_type, account_id):
        key = f"{agent_type}:{account_id}"
        if key in self.cache:
            self.usage_count[key] += 1
            return self.cache[key]
        return None

    def put(self, agent_type, account_id, agent):
        key = f"{agent_type}:{account_id}"
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Remover o agente menos usado
            least_used = min(self.usage_count.items(), key=lambda x: x[1])[0]
            del self.cache[least_used]
            del self.usage_count[least_used]

        self.cache[key] = agent
        self.usage_count[key] = 1
```

## 7. Próximos Passos

1. **Implementação de dashboard de monitoramento**
   - Visualização de métricas em tempo real
   - Alertas para problemas de performance

2. **Expansão de ferramentas MCP**
   - Adicionar mais integrações com Odoo
   - Implementar operações mais complexas

3. **Melhorias na detecção de intenção**
   - Treinamento específico por domínio
   - Suporte a múltiplos idiomas

4. **Integração com sistemas de feedback**
   - Coleta de feedback do cliente
   - Melhoria contínua baseada em feedback

5. **Otimização do gerenciamento de agentes**
   - Implementar cache de agentes
   - Desenvolver estratégias de pré-carregamento
   - Testar diferentes configurações para conversas fluidas

---

Este plano de implementação fornece um roteiro detalhado para a criação da nova arquitetura da CrewAI Multi-Tenant, otimizada para baixa latência, isolamento entre tenants e escalabilidade.
