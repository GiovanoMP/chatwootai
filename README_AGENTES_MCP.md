Agente MCP Dinâmico — Integrações Inteligentes com Odoo via CrewAI + YAML
Este documento descreve a implementação e uso do Agente de Integração com o Odoo, capaz de gerar e executar instruções dinâmicas via MCP, com base em intenção do usuário e descrições estruturadas dos métodos Odoo em YAML.

Essa abordagem elimina a necessidade de hardcode, permite automação escalável e oferece suporte a múltiplos tenants (clientes) com estruturas diferentes de negócio.

📌 Visão Geral
Objetivo
Transformar linguagem natural em ações executáveis no Odoo, via um servidor MCP (Model Context Protocol), sem que o desenvolvedor precise codar cada regra ou integração manualmente.

Como Funciona
O cliente envia uma solicitação (ex: “Quero agendar horário para o cliente João”)

A CrewAI aciona um agente com conhecimento do schema de métodos Odoo, fornecido via YAML

O agente entende os parâmetros e gera um payload dinâmico (rule_data)

Esse payload é enviado ao servidor MCP para ser executado

A resposta da operação é retornada ao cliente

🧩 Componentes Envolvidos

Componente	Descrição
schema.yaml	Arquivo que descreve os métodos disponíveis do Odoo (endpoints, parâmetros, tipos, etc.)
FileReadTool	Ferramenta usada pelo agente para ler o schema
Agente MCP	Agente da CrewAI treinado para ler o YAML e gerar um payload pronto
ExecuteMCPActionTool	Tool que realmente executa o rule_data gerado
Crew	Estrutura que conecta o agente com a task e executa a operação
MCP Server	Servidor backend responsável por transformar os payloads em chamadas reais ao Odoo
📁 Estrutura de Diretórios
graphql
Copiar
Editar
mcp_crew/
├── agents/
│   └── odoo_mcp_agent.py          # Agente principal de geração de métodos
├── crew/
│   └── mcp_query_crew.py          # Classe que monta a Crew para MCP
├── schemas/
│   └── agendamento.yaml           # Schema YAML com definição de métodos
├── tools/
│   └── execute_mcp_tool.py        # Tool que executa chamadas ao MCP
└── examples/
    └── main.py                    # Exemplo de execução
📘 Exemplo de Schema YAML (schemas/agendamento.yaml)
yaml
Copiar
Editar
module: agendamento
methods:
  - name: criar
    endpoint: /mcp/agendamento/criar
    method: POST
    parameters:
      - nome: cliente_id
        tipo: integer
        obrigatório: true
      - nome: data
        tipo: date
      - nome: hora
        tipo: time
      - nome: motivo
        tipo: string
🔧 Agente: Especialista em Métodos Odoo
python
Copiar
Editar
from crewai import Agent
from crewai_tools import FileReadTool

schema_tool = FileReadTool()

odoo_agent = Agent(
    role="Especialista em Integrações Odoo",
    goal="Gerar instruções MCP completas para interagir com o Odoo",
    backstory=(
        "Você é um especialista em automações e integrações com o Odoo ERP. "
        "Dado um schema YAML descrevendo métodos disponíveis, você gera um JSON estruturado "
        "com endpoint, método HTTP e um payload com variáveis que serão preenchidas em tempo de execução."
    ),
    tools=[schema_tool],
    verbose=True,
    memory=True,
    llm="gpt-4o-mini"
)
🧠 Task: Geração de Payload
python
Copiar
Editar
from crewai import Task

odoo_task = Task(
    description=(
        r"""Com base na estrutura descrita no YAML {yaml_path},
gere uma instrução MCP no seguinte formato:

```json
{
  "endpoint": "...",
  "method": "POST",
  "payload_template": {
    ...
  }
}
Requisição do usuário: {user_request}

Regras:

O endpoint deve existir no YAML

Os parâmetros devem estar corretos com base no schema

Variáveis devem ser envolvidas por chaves (ex: "{cliente_id}")

Use o método HTTP correto (POST, GET)

Exemplo de resultado válido:

json
Copiar
Editar
{
  "endpoint": "/mcp/agendamento/criar",
  "method": "POST",
  "payload_template": {
    "cliente_id": "{cliente_id}",
    "data": "{data}",
    "hora": "{hora}",
    "motivo": "{motivo}"
  }
}
""" ), expected_output="Uma estrutura JSON com endpoint, método e payload_template" )

yaml
Copiar
Editar

---

## 🧪 Exemplo de Execução (`examples/main.py`)

```python
from crew.mcp_query_crew import MCPQueryCrew

crew = MCPQueryCrew()
inputs = {
    "yaml_path": "schemas/agendamento.yaml",
    "user_request": "Quero agendar um horário para o cliente João na próxima segunda às 14h"
}

result = crew.kickoff(inputs)
print(result)
🔄 Resultado Esperado
json
Copiar
Editar
{
  "endpoint": "/mcp/agendamento/criar",
  "method": "POST",
  "payload_template": {
    "cliente_id": "{cliente_id}",
    "data": "{data}",
    "hora": "{hora}",
    "motivo": "{motivo}"
  }
}
Este payload pode ser repassado para a ExecuteMCPActionTool para execução imediata no backend.

🧰 Tool: ExecuteMCPActionTool (opcional)
Esta ferramenta é usada para consumir diretamente o rule_data gerado:

python
Copiar
Editar
tool = ExecuteMCPActionTool()
response = tool._run(rule_data=generated_data, context=contexto, account_id="account_1")
Ela cuida de:

Substituir variáveis no payload_template

Chamar o servidor MCP via HTTP

Retornar a resposta ao agente finalizador da Crew

✅ Benefícios da Abordagem

Benefício	Descrição
🔌 Plugável	Pode ser usada para qualquer módulo do Odoo com schema definido
🔁 Reutilizável	O mesmo agente atende diferentes tenants, produtos e domínios
🧠 Sem necessidade de programar regras	O YAML define tudo, e o agente infere automaticamente
🚀 Alta performance	Nenhum uso de LLM na execução final, apenas na geração
🧩 Integração com RAG	Pode ser combinada com vetorização de regras
📤 Pode ser usada em tempo real ou offline	Útil para automações pré-processadas ou assistentes conversacionais
📦 Extensões Futuras
✅ Suporte a múltiplos YAMLs simultâneos (módulos compostos)

✅ Templates com lógica condicional via Jinja2

✅ Validação com pydantic antes de executar

✅ Integração com Agente de Intenção para escolher o YAML certo