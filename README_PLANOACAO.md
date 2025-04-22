# Plano de Ação: Implementação da Arquitetura Unificada de Crew

Este documento detalha o plano de ação para implementar a nova arquitetura unificada de crew, integrando busca semântica via Qdrant com operações executáveis via MCP-Odoo.

## 1. Visão Geral do Problema

Atualmente, o sistema possui múltiplas crews por tenant, o que gera complexidade e potenciais problemas de latência. Além disso, existe uma desconexão entre:

1. **Conhecimento semântico** (armazenado no Qdrant como vetores)
2. **Ações executáveis** (disponíveis via MCP-Odoo)

O desafio central é: **Como fazer a transição fluida entre informação contextual e ação concreta?**

Por exemplo, quando um cliente pergunta sobre uma promoção e depois decide efetuar uma compra, como garantir que:
- A regra de negócio correta seja encontrada (via busca semântica)
- A ação correspondente seja executada corretamente no Odoo (via MCP)
- Tudo isso aconteça de forma eficiente e escalável

## 2. Solução Proposta: Arquitetura Unificada com Bridge Semântico-Operacional

A solução proposta consiste em:

1. **Uma única crew por tenant** (substituindo múltiplas crews)
2. **Configurações via YAML** para informações estáticas (substituindo o company_metadata_agent)
3. **Processamento paralelo** para reduzir latência
4. **Bridge semântico-operacional** usando o campo `rule_data` como ponte entre conhecimento vetorial e automação

### 2.1 O Conceito de Bridge Semântico-Operacional

O elemento central da solução é o uso do campo `rule_data` como uma ponte estruturada entre:
- O conhecimento semântico armazenado em vetores no Qdrant
- As operações executáveis disponíveis via MCP-Odoo

Este campo contém dados estruturados que:
- São gerados durante a vetorização da regra (pré-processamento)
- Incluem templates de payload prontos para execução
- Permitem que o agente MCP execute ações sem precisar interpretar texto novamente

## 3. Fluxo de Dados na Nova Arquitetura

### 3.1 Fluxo de Ingestão de Regras

```
Admin cria/edita regra no Odoo
  ↓
Backend envia para API
  ↓
Agente de embedding processa a regra:
  ↓
  ├── Gera `processed_text` enriquecido para busca semântica
  ↓
  └── Gera `rule_data` estruturado com templates de ação
  ↓
Documento é armazenado no Qdrant (vetorizado + pronto para execução)
```

### 3.2 Fluxo de Atendimento ao Cliente

```
Cliente envia pergunta (via Chatwoot ou App)
  ↓
FastAPI recebe (com account_id)
  ↓
ConfigLoader busca o YAML (Redis ou local)
  ↓
Verifica horário de atendimento e outras informações como: estilo de comunicação, saudação, se usa ou não emojis e etc
  ↓
Inicia a Crew com:
  ↓
  ├── Agente de Intenção → detecta a intenção do cliente
  ↓
  ├── Agente Vetorial → busca regras/documentos relevantes - sendo um agente para cada coleção do Qdrant
  ↓
  ├── Agente MCP → executa ações no Odoo quando necessário
  ↓
  └── Agente de Resposta → formata resposta final
  ↓
Resposta é enviada ao cliente
```

### 3.3 Fluxo de Execução de Ações

```
Agente Vetorial encontra regra relevante com `rule_data`
  ↓
Agente MCP recebe regra com template de ação
  ↓
Agente MCP substitui variáveis no template com dados do contexto
  ↓
Agente MCP executa a ação via MCP-Odoo
  ↓
Resultado da ação é incorporado na resposta final
```

## 4. Componentes a Serem Implementados

### 4.1 Modificação do Agente de Embedding de Regras

O agente de embedding de regras de negócio (`odoo_api/embedding_agents/business_rules/rules_agent.py`) precisa ser modificado para:

1. Gerar `processed_text` enriquecido com palavras-chave para melhorar a busca semântica
2. Gerar `rule_data` estruturado com:
   - Tipo de ação (`action`)
   - Endpoint MCP (`endpoint`)
   - Método HTTP (`method`)
   - Template de payload (`payload_template`)
3. Adicionar campos de status:
   - `is_active` baseado nas datas
   - `status_text` com explicação em linguagem natural

Exemplo de saída do agente modificado:

```json
{
  "account_id": "account_1",
  "rule_id": 12,
  "name": "Frete Grátis",
  "description": "Frete grátis até 01/05",
  "type": "delivery",
  "priority": 1,
  "is_temporary": true,
  "start_date": "2025-04-20",
  "end_date": "2025-05-01",
  "is_active": true,
  "status_text": "Esta regra está ATIVA no momento atual",
  "rule_data": {
    "action": "frete_gratis",
    "endpoint": "/mcp/venda/criar",
    "method": "POST",
    "version": "v1.0",
    "variables": ["cliente_id", "produtos"],
    "payload_template": {
      "cliente_id": "{cliente_id}",
      "produtos": "{produtos}",
      "frete": "gratis"
    }
  },
  "processed_text": "Nome da regra: Frete Grátis. Descrição: Frete grátis válido até 01/05/2025. Tipo: entrega. Regra ativa. Aplica-se a todos os produtos. Palavras-chave: frete grátis, entrega gratuita, delivery free, sem custo de envio, transporte incluído."
}
```

### 4.2 Implementação da Estrutura da Crew Unificada

Seguindo a estrutura proposta no README_CREW.md, implementar:

#### 4.2.1 Estrutura de Diretórios

```
crews/
├── customer_service/
│   ├── __init__.py
│   ├── crew.py                 # Classe principal da crew
│   ├── config_loader.py        # Carregador de configurações
│   ├── memory.py               # Gerenciamento de memória
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── intention_agent.py  # Agente de intenção
│   │   ├── vector_agents.py    # Agentes vetoriais
│   │   ├── mcp_agent.py        # Agente MCP
│   │   └── response_agent.py   # Agente de resposta
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── vector_tools.py     # Ferramentas de busca vetorial
│   │   ├── mcp_tools.py        # Ferramentas MCP
│   │   └── utils_tools.py      # Ferramentas utilitárias
│   └── utils/
│       ├── __init__.py
│       └── horario.py          # Verificação de horário
```

#### 4.2.2 Componentes Principais

1. **ConfigLoader (`config_loader.py`)**
   - Carrega configurações YAML com cache Redis
   - Substitui o company_metadata_agent
   - Implementa TTL para atualizações

2. **Agentes Especializados**
   - **Agente de Intenção**: Detecta a intenção do cliente
   - **Agentes Vetoriais**: Buscam regras e documentos no Qdrant
   - **Agente MCP**: Executa ações no Odoo via MCP
   - **Agente de Resposta**: Formata a resposta final

3. **Ferramentas Especializadas**
   - **VectorSearchTool**: Busca no Qdrant com filtro por account_id
   - **ExecuteMCPActionTool**: Executa ações no MCP com templates

4. **Memória Redis Multi-Tenant**
   - Isolamento por account_id
   - Persistência entre sessões
   - TTL configurável

### 4.3 Ferramenta `ExecuteMCPActionTool` (dinamicamente via rule_data)

Esta ferramenta permite que o agente MCP execute ações dinâmicas no Odoo sem a necessidade de interpretar texto ou lógica adicional em tempo de execução. Ela utiliza o campo `rule_data["payload_template"]` previamente gerado no momento da vetorização, garantindo alta performance e desacoplamento entre interpretação e execução.

#### 💡 Finalidade

- Executar automaticamente ações definidas em regras de negócio
- Substituir variáveis dinâmicas do payload (ex: `{cliente_id}`, `{cep}`)
- Eliminar necessidade de parsing LLM durante o atendimento
- Reduzir latência para < 500ms

#### ⚙️ Estrutura esperada no Qdrant (`rule_data`)

```json
{
  "endpoint": "/mcp/venda/criar",
  "method": "POST",
  "version": "v1.0",
  "variables": ["cliente_id"],
  "payload_template": {
    "cliente_id": "{cliente_id}",
    "produtos": [
      {"id": "shampoo_vanessa", "quantidade": 1},
      {"id": "condicionador_comodoro", "quantidade": 1, "tipo": "bonus"}
    ]
  }
}
```

#### 🛠️ Implementação da Tool

```python
from crewai_tools import BaseTool
import requests
import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class RuleDataModel(BaseModel):
    """Modelo para validação de rule_data."""
    action: str = Field(..., description="Tipo de ação a ser executada")
    endpoint: str = Field(..., description="Endpoint MCP a ser chamado")
    method: str = Field(default="POST", description="Método HTTP")
    version: str = Field(default="v1.0", description="Versão do formato de rule_data")
    variables: List[str] = Field(default_factory=list, description="Variáveis esperadas no template")
    payload_template: Dict[str, Any] = Field(..., description="Template de payload com variáveis")
    condicao: Optional[Dict[str, Any]] = Field(default=None, description="Condições para aplicação da regra")

class ExecuteMCPActionTool(BaseTool):
    name = "Executar Ação com Payload Template"
    description = "Substitui variáveis no template e executa ação no MCP para o tenant especificado"

    def _run(self, rule_data: dict, context: dict, account_id: str):
        """
        Executa uma ação no Odoo usando um template de payload.

        Args:
            rule_data (dict): Dados estruturados da regra, incluindo endpoint, método e payload_template
            context (dict): Dados da sessão (ex: cliente_id, valor_total, cep)
            account_id (str): ID do tenant

        Returns:
            dict ou str: Resposta do MCP ou mensagem de erro
        """
        try:
            # Validar rule_data
            try:
                validated_data = RuleDataModel(**rule_data)
            except Exception as e:
                return f"Erro de validação no rule_data: {str(e)}"

            # Verificar variáveis necessárias
            missing_vars = [var for var in validated_data.variables if var not in context]
            if missing_vars:
                return {
                    "success": False,
                    "error": f"Variáveis ausentes: {missing_vars}",
                    "request_info": missing_vars
                }

            # Prioridade 1: Payload pronto
            if "payload" in rule_data:
                return self._call_mcp(
                    validated_data.endpoint,
                    validated_data.method,
                    rule_data["payload"],
                    account_id
                )

            # Prioridade 2: Template de payload
            payload = self._render_template(validated_data.payload_template, context)
            return self._call_mcp(validated_data.endpoint, validated_data.method, payload, account_id)

        except Exception as e:
            return f"Erro ao executar ação MCP: {str(e)}"

    def _render_template(self, template: dict, context: dict) -> dict:
        """
        Substitui placeholders do payload_template por valores do contexto.
        Suporta apenas substituições diretas. Para lógicas complexas, use Jinja2.

        Exemplo:
        { "cliente_id": "{cliente_id}" } com context["cliente_id"] = 123 → { "cliente_id": 123 }

        Args:
            template (dict): Payload com placeholders
            context (dict): Variáveis disponíveis

        Returns:
            dict: Payload final com variáveis preenchidas
        """
        payload_str = json.dumps(template)
        for key, value in context.items():
            payload_str = payload_str.replace(f"{{{key}}}", str(value))
        return json.loads(payload_str)

    def _call_mcp(self, endpoint: str, method: str, payload: dict, account_id: str):
        """
        Envia a requisição ao servidor MCP.

        Args:
            endpoint (str): Caminho do endpoint
            method (str): GET ou POST
            payload (dict): Dados a serem enviados
            account_id (str): ID do tenant (para autenticação se necessário)

        Returns:
            dict ou str: Resposta
        """
        url = f"http://localhost:9000{endpoint}"
        headers = {
            "X-Account-ID": account_id,
            "Content-Type": "application/json"
        }

        if method == "POST":
            response = requests.post(url, json=payload, headers=headers, timeout=3)
        else:
            response = requests.get(url, params=payload, headers=headers, timeout=3)

        return response.json()
```

#### ✅ Vantagens

| Recurso | Benefício |
|---------|----------|
| payload_template | Permite automação segura, clara e rápida |
| context dinâmico | Flexível para adaptar a qualquer cliente |
| Sem LLM em tempo de execução | Latência mínima (< 500ms por chamada) |
| Totalmente desacoplado do agente | O mesmo agente pode executar diversas regras diferentes |
| Suporte Multi-Tenant | MCP executado com account_id isolado |

### 4.4 Implementação da Fábrica de Crew

A fábrica de crew (`crew_factory.py`) será responsável por:

1. Criar todos os agentes necessários
2. Configurar as tarefas com dependências corretas
3. Montar a crew com processamento paralelo
4. Gerenciar o cache Redis para crews

```python
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

## 5. Configuração YAML Aprimorada

A configuração YAML será expandida para incluir:

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

## 6. Exemplos de Casos de Uso

### 6.1 Caso de Uso: Promoção com Brinde

**Regra no Qdrant:**
```json
{
  "name": "Promoção Shampoo Vanessa",
  "description": "Compre um Shampoo Vanessa e ganhe um Condicionador Comodoro",
  "is_temporary": true,
  "start_date": "2025-04-20",
  "end_date": "2025-05-01",
  "is_active": true,
  "rule_data": {
    "action": "adicionar_bonus",
    "endpoint": "/mcp/venda/criar",
    "method": "POST",
    "version": "v1.0",
    "variables": ["cliente_id"],
    "payload_template": {
      "cliente_id": "{cliente_id}",
      "produtos": [
        {"id": "shampoo_vanessa", "quantidade": 1},
        {"id": "condicionador_comodoro", "quantidade": 1, "tipo": "bonus"}
      ]
    }
  },
  "processed_text": "Promoção: Compre um Shampoo Vanessa e ganhe um Condicionador Comodoro grátis. Válido de 20/04/2025 até 01/05/2025. Palavras-chave: shampoo, condicionador, brinde, promoção, compre e ganhe, produto grátis."
}
```

**Fluxo de Conversa:**
1. Cliente: "Vocês têm alguma promoção de shampoo?"
2. Agente de Intenção: Identifica como "consulta_promocao" + "produto_especifico"
3. Agente Vetorial: Encontra a regra acima no Qdrant
4. Agente de Resposta: "Sim! Temos uma promoção especial: na compra de um Shampoo Vanessa, você ganha um Condicionador Comodoro grátis! Esta promoção é válida até 01/05/2025."
5. Cliente: "Ótimo! Quero comprar."
6. Agente de Intenção: Identifica como "intencao_compra"
7. Agente MCP: Usa o `rule_data` para executar a ação no Odoo via MCP
8. Agente de Resposta: "Perfeito! Acabei de registrar seu pedido com o Shampoo Vanessa e adicionei o Condicionador Comodoro como brinde. Seu pedido #12345 foi criado com sucesso!"

### 6.2 Caso de Uso: Frete Grátis

**Regra no Qdrant:**
```json
{
  "name": "Frete Grátis",
  "description": "Frete grátis para compras acima de R$ 100",
  "is_temporary": false,
  "is_active": true,
  "rule_data": {
    "action": "frete_gratis",
    "endpoint": "/mcp/venda/calcular_frete",
    "method": "POST",
    "version": "v1.0",
    "variables": ["cliente_id", "valor_total", "cep"],
    "payload_template": {
      "cliente_id": "{cliente_id}",
      "valor_total": "{valor_total}",
      "cep": "{cep}",
      "aplicar_frete_gratis": true
    },
    "condicao": {
      "campo": "valor_total",
      "operador": ">=",
      "valor": 100
    }
  },
  "processed_text": "Regra: Frete grátis para compras acima de R$ 100. Esta regra é permanente. Palavras-chave: frete grátis, entrega gratuita, delivery free, sem custo de envio, transporte incluído, compras acima de 100 reais."
}
```

**Fluxo de Conversa:**
1. Cliente: "Vocês cobram frete?"
2. Agente de Intenção: Identifica como "consulta_frete"
3. Agente Vetorial: Encontra a regra acima no Qdrant
4. Agente de Resposta: "Sim, cobramos frete, mas temos frete grátis para compras acima de R$ 100!"
5. Cliente: "Quero comprar produtos no valor de R$ 150, qual meu CEP é 12345-678"
6. Agente de Intenção: Identifica como "intencao_compra" + "informacao_entrega"
7. Agente MCP: Usa o `rule_data` para calcular o frete (que será grátis) via MCP
8. Agente de Resposta: "Ótimo! Para sua compra de R$ 150, o frete será grátis para o CEP 12345-678. Deseja prosseguir com a compra?"

## 7. Plano de Implementação

### 7.1 Fase 1: Preparação (Semana 1)

1. **Modificar o Agente de Embedding de Regras**
   - Implementar geração de `rule_data` estruturado
   - Adicionar campos de status e metadados
   - Adicionar campos `version` e `variables` ao schema
   - Implementar validação com Pydantic para `rule_data`
   - Testar com diferentes tipos de regras

2. **Criar Estrutura de Diretórios**
   - Implementar a estrutura proposta
   - Criar arquivos iniciais

3. **Implementar ConfigLoader**
   - Implementar carregamento de YAML com cache Redis
   - Criar arquivos YAML de exemplo

### 7.2 Fase 2: Componentes Básicos (Semana 2)

1. **Implementar Ferramentas Vetoriais**
   - Adaptar `VectorSearchTool` para a nova estrutura
   - Implementar filtragem por account_id
   - Testar conexão com Qdrant

2. **Implementar Ferramentas MCP**
   - Criar `ExecuteMCPActionTool`
   - Implementar processamento de templates
   - Implementar hierarquia clara de prioridades (payload > template > fallback)
   - Implementar validação prévia de variáveis necessárias
   - Testar conexão com MCP-Odoo

3. **Implementar Memória Redis**
   - Implementar `memory.py`
   - Testar isolamento entre tenants

4. **Implementar Verificador de Horário**
   - Implementar `horario.py`
   - Testar com diferentes configurações

### 7.3 Fase 3: Agentes (Semana 3)

1. **Implementar Agente de Intenção**
   - Implementar `intention_agent.py`
   - Testar classificação de intenções

2. **Implementar Agentes Vetoriais**
   - Implementar `vector_agents.py`
   - Testar busca em coleções do Qdrant

3. **Implementar Agente MCP**
   - Implementar `mcp_agent.py`
   - Testar integração com Odoo

4. **Implementar Agente de Resposta**
   - Implementar `response_agent.py`
   - Testar formatação de respostas

### 7.4 Fase 4: Integração (Semana 4)

1. **Implementar Fábrica de Crew**
   - Implementar `crew_factory.py`
   - Testar criação de crew completa

2. **Implementar API FastAPI**
   - Atualizar `main.py`
   - Testar endpoint de atendimento

3. **Implementar Detector de Handoff**
   - Implementar `handoff_detector.py`
   - Implementar detecção explícita de intenção de handoff
   - Otimizar fluxo de tarefas com base na intenção
   - Testar redirecionamento para humano

### 7.5 Fase 5: Testes e Otimização (Semana 5)

1. **Testes de Performance**
   - Medir tempo de resposta
   - Identificar gargalos

2. **Testes de Isolamento**
   - Verificar isolamento entre tenants
   - Testar concorrência

3. **Otimizações Finais**
   - Ajustar parâmetros
   - Implementar sistema de analytics por tenant
   - Implementar testes unitários automatizados
   - Implementar melhorias identificadas

## 8. Métricas de Sucesso

1. **Tempo de Resposta**
   - Meta: < 3 segundos para 95% das requisições
   - Monitorar latência de cada componente

2. **Isolamento entre Tenants**
   - Zero vazamento de dados entre tenants
   - Configurações isoladas por account_id

3. **Qualidade das Respostas**
   - Respostas precisas e relevantes
   - Personalização conforme configuração do tenant

4. **Execução de Ações**
   - Taxa de sucesso > 98% para ações no Odoo
   - Tempo médio de execução < 1 segundo

5. **Escalabilidade**
   - Suporte a múltiplos tenants simultâneos
   - Degradação graceful sob carga

## 9. Considerações Futuras

1. **Expansão para Outros ERPs**
   - Adaptar para outros ERPs além do Odoo
   - Implementar adaptadores MCP específicos

2. **Aprendizado Contínuo**
   - Implementar feedback loop para melhorar embeddings
   - Ajustar templates de ação com base em resultados
   - Implementar versionamento progressivo de rule_data

3. **Personalização Avançada**
   - Permitir que tenants definam seus próprios templates
   - Suporte a lógica condicional complexa
   - Implementar validação de schema para templates personalizados

4. **Integração com Marketplaces**
   - Expandir para Mercado Livre, Facebook, Instagram
   - Implementar ações específicas para cada plataforma

5. **Analytics e Dashboards**
   - Monitorar uso de regras e ações
   - Gerar insights para melhorias
   - Implementar dashboards por tenant sem dependência de desenvolvimento adicional

6. **Testes Automatizados Avançados**
   - Implementar testes com dados reais do Qdrant
   - Automatizar testes de renderização de templates
   - Implementar testes de integração end-to-end

## 10. Conclusão

Esta arquitetura unificada resolve o problema central de conectar conhecimento semântico com ações executáveis, através de:

1. **Pré-processamento Inteligente**: Enriquecendo regras no momento da ingestão
2. **Bridge Estruturado**: Usando `rule_data` como ponte entre semântica e operação
3. **Execução Eficiente**: Permitindo ações diretas sem reinterpretação
4. **Escalabilidade**: Suportando múltiplos tenants e regras sem reprogramação

A implementação seguirá o plano detalhado acima, com foco em performance, isolamento e qualidade de resposta.


NOTA : Como a crew.yaml acessa dados de config.yaml e credentials.yaml?
Resposta curta: Não acessa diretamente — você carrega tudo no Python e funde os dados no runtime.

✅ Exemplo realista:


def build_atendimento_crew(account_id):
    config = load_yaml(f"config/domains/retail/{account_id}/config.yaml")
    credentials = load_yaml(f"config/credentials/{account_id}.yaml")
    crew_config = load_yaml("config/crew/atendimento.yaml")

    # Mescla tudo num contexto único
    context = {
        "account_id": account_id,
        "config": config,
        "credentials": credentials,
        "crew": crew_config
    }

    return CrewFactory(context).build()

    DICA> 🛠️ DICA: Deixe os agentes mais "magros"
O próprio Agent pode receber dados de contexto via backstory ou ferramentas injetadas:

Agent(
    role="Finalizador de Atendimento",
    goal="Responder ao cliente com base nos dados institucionais",
    backstory=f"""
Você atende pelo nome de {config["name"]}. Utilize o tom {config["customer_service"]["communication_style"]}.
Respeite os horários de atendimento definidos em {config["business_hours"]["start_time"]} às {config["business_hours"]["end_time"]}.
""",
    tools=[...],
    ...
)
