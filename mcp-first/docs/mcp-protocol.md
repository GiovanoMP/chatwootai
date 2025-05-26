# Protocolo MCP (Model Context Protocol)

## Visão Geral

O Model Context Protocol (MCP) é um protocolo padronizado que permite que modelos de IA descubram e interajam com ferramentas e recursos externos. Na arquitetura ChatwootAI, o MCP serve como a camada universal de integração entre todos os componentes, padronizando a comunicação e permitindo uma arquitetura verdadeiramente modular e extensível.

## Princípios Fundamentais do MCP

### 1. Primitivas Padronizadas

O MCP organiza as interações em três primitivas padronizadas:

- **Ferramentas (Tools)**: Funções executáveis que permitem ao modelo de IA realizar ações em sistemas externos. Representam as "mãos" do agente de IA.
- **Recursos (Resources)**: Fluxos de dados estruturados que fornecem contexto vital ao LLM. Representam o "conhecimento" que a IA precisa para entender seu ambiente.
- **Prompts**: Modelos de instrução reutilizáveis para fluxos de trabalho comuns. Fornecem a "orientação" para as ações da IA.

### 2. Arquitetura Cliente-Servidor

O MCP opera em uma arquitetura cliente-servidor:

- **Host**: A aplicação central alimentada por IA com a qual os usuários interagem diretamente.
- **Clientes**: Intermediários que mantêm conexões individuais entre a aplicação host e os servidores MCP.
- **Servidores MCP**: Programas leves que expõem capacidades específicas, dados ou modelos de prompt de sistemas externos.

### 3. Comunicação JSON-RPC

O MCP utiliza JSON-RPC 2.0 como protocolo de comunicação, garantindo interoperabilidade e simplicidade:

- Mensagens são codificadas em JSON
- Cada requisição inclui um ID, método e parâmetros
- Cada resposta inclui o mesmo ID e o resultado ou erro
- Suporte para notificações (mensagens sem resposta esperada)

## Implementação do MCP na Arquitetura ChatwootAI

### MCP-Odoo

O MCP-Odoo implementa o protocolo MCP para o Odoo ERP, expondo as seguintes capacidades:

#### Ferramentas (Tools)

- **search_records**: Busca registros em qualquer modelo Odoo
- **read_record**: Lê detalhes de um registro específico
- **create_record**: Cria um novo registro no Odoo
- **update_record**: Atualiza um registro existente
- **delete_record**: Remove um registro do Odoo
- **execute_method**: Executa um método personalizado em um modelo Odoo
- **get_model_fields**: Obtém definições de campos para um modelo
- **search_employee**: Busca funcionários por nome
- **search_holidays**: Busca férias dentro de um intervalo de datas

#### Recursos (Resources)

- **odoo://models**: Lista todos os modelos disponíveis no sistema Odoo
- **odoo://model/{model_name}**: Obtém informações sobre um modelo específico
- **odoo://record/{model_name}/{record_id}**: Obtém um registro específico por ID
- **odoo://search/{model_name}/{domain}**: Busca registros que correspondem a um domínio

### MCP-Qdrant

O MCP-Qdrant implementa o protocolo MCP para o banco de dados vetorial Qdrant:

#### Ferramentas (Tools)

- **search_vectors**: Busca vetores similares em uma coleção
- **store_vector**: Armazena um vetor com metadados
- **delete_vector**: Remove um vetor da coleção
- **create_collection**: Cria uma nova coleção vetorial
- **list_collections**: Lista todas as coleções disponíveis
- **get_collection_info**: Obtém informações sobre uma coleção específica

#### Recursos (Resources)

- **qdrant://collections**: Lista todas as coleções disponíveis
- **qdrant://collection/{collection_name}**: Informações sobre uma coleção específica
- **qdrant://collection/{collection_name}/stats**: Estatísticas sobre uma coleção

### MCP-Chatwoot

O MCP-Chatwoot implementa o protocolo MCP para o Chatwoot:

#### Ferramentas (Tools)

- **send_message**: Envia uma mensagem para um contato
- **get_conversation**: Obtém o histórico de uma conversa
- **create_contact**: Cria um novo contato
- **update_contact**: Atualiza informações de um contato
- **assign_conversation**: Atribui uma conversa a um agente
- **add_label**: Adiciona uma etiqueta a uma conversa
- **resolve_conversation**: Marca uma conversa como resolvida

#### Recursos (Resources)

- **chatwoot://accounts**: Lista todas as contas disponíveis
- **chatwoot://account/{account_id}/inboxes**: Lista as caixas de entrada de uma conta
- **chatwoot://account/{account_id}/agents**: Lista os agentes de uma conta
- **chatwoot://account/{account_id}/labels**: Lista as etiquetas disponíveis

## Fluxo de Comunicação MCP

### Inicialização

1. O cliente MCP envia uma solicitação de inicialização ao servidor
2. O servidor responde com informações sobre suas capacidades

### Descoberta de Ferramentas

1. O cliente solicita a lista de ferramentas disponíveis
2. O servidor responde com a descrição detalhada de cada ferramenta

### Execução de Ferramentas

1. O cliente seleciona uma ferramenta e envia uma solicitação de execução
2. O servidor executa a ferramenta e responde com o resultado

### Acesso a Recursos

1. O cliente solicita um recurso específico
2. O servidor responde com o conteúdo do recurso

## Exemplos de Payloads JSON

### Exemplo de Solicitação de Ferramenta

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_records",
    "arguments": {
      "model": "res.partner",
      "domain": [["is_company", "=", true]],
      "fields": ["name", "email", "phone"],
      "limit": 10
    }
  }
}
```

### Exemplo de Resposta de Ferramenta

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "isError": false,
    "content": [
      {
        "type": "json",
        "json": [
          {
            "id": 1,
            "name": "YourCompany",
            "email": "info@yourcompany.example.com",
            "phone": "+1 (650) 555-0111"
          },
          {
            "id": 2,
            "name": "Deco Addict",
            "email": "info@deco-addict.example.com",
            "phone": "+1 (650) 555-0112"
          }
        ]
      }
    ]
  }
}
```

### Exemplo de Solicitação de Recurso

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/get",
  "params": {
    "uri": "odoo://model/res.partner"
  }
}
```

### Exemplo de Resposta de Recurso

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "json",
        "json": {
          "name": "Contact",
          "model": "res.partner",
          "fields": {
            "name": {"type": "char", "string": "Name", "required": true},
            "email": {"type": "char", "string": "Email"},
            "phone": {"type": "char", "string": "Phone"}
          }
        }
      }
    ]
  }
}
```

## Implementação Técnica

### Servidor MCP

Um servidor MCP é implementado usando a biblioteca FastMCP, que fornece uma API simples para definir ferramentas e recursos:

```python
from fastmcp import FastMCP, mcp

app = FastMCP()

@mcp.tool("search_records")
def search_records(model: str, domain: list, fields: list = None, limit: int = None):
    # Implementação da ferramenta
    return results

@mcp.resource("odoo://models")
def get_models():
    # Implementação do recurso
    return models

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Cliente MCP

Um cliente MCP é implementado usando a biblioteca MCPClient, que fornece uma API simples para descobrir e chamar ferramentas e recursos:

```python
from mcp_client import MCPClient

client = MCPClient("http://localhost:8000")

# Descoberta de ferramentas
tools = client.list_tools()

# Chamada de ferramenta
result = client.call_tool("search_records", {
    "model": "res.partner",
    "domain": [["is_company", "=", true]],
    "fields": ["name", "email", "phone"],
    "limit": 10
})

# Acesso a recurso
resource = client.get_resource("odoo://models")
```

## Considerações de Segurança

### Autenticação

O MCP suporta vários métodos de autenticação:

- Autenticação básica (usuário/senha)
- Autenticação por token (JWT)
- Autenticação por certificado (mTLS)

### Autorização

O MCP implementa um sistema de autorização baseado em papéis:

- Cada cliente MCP tem um conjunto de papéis
- Cada ferramenta e recurso tem um conjunto de papéis permitidos
- O servidor MCP verifica se o cliente tem os papéis necessários antes de permitir o acesso

### Auditoria

O MCP registra todas as solicitações e respostas para fins de auditoria:

- Quem fez a solicitação
- Qual ferramenta ou recurso foi acessado
- Quais parâmetros foram fornecidos
- Qual foi o resultado

## Conclusão

O Model Context Protocol (MCP) é a espinha dorsal da arquitetura ChatwootAI, permitindo uma comunicação padronizada entre todos os componentes do sistema. Ao adotar o MCP como camada universal de integração, o sistema se torna mais modular, flexível e escalável, facilitando a adição de novos componentes e a expansão para outros contextos.

A implementação do MCP para Odoo, Qdrant e Chatwoot permite que os agentes de IA interajam com esses sistemas de forma padronizada, sem conhecer os detalhes de implementação de cada um. Isso resulta em um sistema mais coeso e fácil de manter, onde os componentes podem ser substituídos ou atualizados individualmente sem impactar o sistema como um todo.
