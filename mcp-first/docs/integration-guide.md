# Guia de Integração MCP First

## Visão Geral

Este guia fornece instruções detalhadas para integrar novos componentes à arquitetura MCP First. A integração é baseada no Model Context Protocol (MCP), que padroniza a comunicação entre todos os componentes do sistema.

## Pré-requisitos

Antes de iniciar a integração, certifique-se de que você tem:

1. Conhecimento básico do componente que deseja integrar
2. Acesso à API ou interface do componente
3. Ambiente de desenvolvimento Python configurado
4. Familiaridade com o protocolo MCP (consulte `mcp-protocol.md`)

## Etapas de Integração

### 1. Definir o Escopo da Integração

Primeiro, defina claramente o que você deseja expor do seu componente através do MCP:

- **Ferramentas (Tools)**: Quais ações os agentes de IA poderão executar no seu componente?
- **Recursos (Resources)**: Quais dados do seu componente serão disponibilizados para consulta?
- **Prompts**: Quais fluxos de trabalho específicos do seu componente serão padronizados?

### 2. Configurar o Ambiente de Desenvolvimento

```bash
# Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install fastmcp pydantic requests
```

### 3. Implementar o Servidor MCP

Crie um novo arquivo Python para o seu servidor MCP:

```python
# mcp_mycomponent.py
from fastmcp import FastMCP, mcp
import json
from typing import List, Dict, Any, Optional

# Inicializar o servidor MCP
app = FastMCP(title="MCP-MyComponent")

# Configurar a conexão com o seu componente
# Exemplo: cliente API, conexão de banco de dados, etc.
component_client = setup_component_client()

# Implementar ferramentas (tools)
@mcp.tool("my_component_action")
def my_component_action(param1: str, param2: int, optional_param: Optional[bool] = False) -> Dict[str, Any]:
    """
    Execute uma ação no seu componente.
    
    Args:
        param1: Primeiro parâmetro da ação
        param2: Segundo parâmetro da ação
        optional_param: Parâmetro opcional (padrão: False)
        
    Returns:
        Resultado da ação
    """
    # Implementar a lógica para executar a ação no seu componente
    result = component_client.execute_action(param1, param2, optional_param)
    return result

# Implementar recursos (resources)
@mcp.resource("mycomponent://items")
def get_items() -> str:
    """
    Obter a lista de itens do seu componente.
    
    Returns:
        Lista de itens em formato JSON
    """
    # Implementar a lógica para obter os itens do seu componente
    items = component_client.get_items()
    return json.dumps(items)

@mcp.resource("mycomponent://item/{item_id}")
def get_item(item_id: str) -> str:
    """
    Obter detalhes de um item específico do seu componente.
    
    Args:
        item_id: ID do item
        
    Returns:
        Detalhes do item em formato JSON
    """
    # Implementar a lógica para obter os detalhes do item
    item = component_client.get_item(item_id)
    return json.dumps(item)

# Iniciar o servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### 4. Testar a Integração

Antes de integrar com o sistema completo, teste seu servidor MCP isoladamente:

```bash
# Iniciar o servidor MCP
python mcp_mycomponent.py
```

Em outro terminal, teste as chamadas usando curl:

```bash
# Listar ferramentas disponíveis
curl -X POST http://localhost:8080/tools/list -H "Content-Type: application/json" -d '{}'

# Chamar uma ferramenta
curl -X POST http://localhost:8080/tools/call -H "Content-Type: application/json" -d '{
  "name": "my_component_action",
  "arguments": {
    "param1": "test",
    "param2": 123
  }
}'

# Acessar um recurso
curl -X POST http://localhost:8080/resources/get -H "Content-Type: application/json" -d '{
  "uri": "mycomponent://items"
}'
```

### 5. Integrar com o MCP-Orchestrator

Após testar sua integração isoladamente, você precisa registrá-la no MCP-Orchestrator:

1. Adicione a configuração do seu servidor MCP ao arquivo de configuração do MCP-Orchestrator:

```yaml
# config.yaml
servers:
  - name: mcp-odoo
    url: http://localhost:8000
  - name: mcp-qdrant
    url: http://localhost:8001
  - name: mcp-chatwoot
    url: http://localhost:8002
  - name: mcp-mycomponent  # Adicione seu servidor aqui
    url: http://localhost:8080
```

2. Reinicie o MCP-Orchestrator para que ele reconheça o novo servidor MCP.

### 6. Criar um Cliente MCP para seu Componente

Para facilitar o uso do seu servidor MCP por outros componentes, crie uma classe cliente:

```python
# mcp_mycomponent_client.py
from mcp_client import MCPClient
from typing import List, Dict, Any, Optional

class MyComponentClient:
    def __init__(self, mcp_url: str = "http://localhost:8080"):
        self.client = MCPClient(mcp_url)
    
    def execute_action(self, param1: str, param2: int, optional_param: bool = False) -> Dict[str, Any]:
        """
        Execute uma ação no componente.
        """
        result = self.client.call_tool("my_component_action", {
            "param1": param1,
            "param2": param2,
            "optional_param": optional_param
        })
        return result
    
    def get_items(self) -> List[Dict[str, Any]]:
        """
        Obtenha a lista de itens do componente.
        """
        resource = self.client.get_resource("mycomponent://items")
        return resource
    
    def get_item(self, item_id: str) -> Dict[str, Any]:
        """
        Obtenha detalhes de um item específico.
        """
        resource = self.client.get_resource(f"mycomponent://item/{item_id}")
        return resource
```

### 7. Documentar a Integração

Documente sua integração para que outros desenvolvedores possam utilizá-la:

```markdown
# MCP-MyComponent

## Visão Geral

MCP-MyComponent é uma implementação do Model Context Protocol (MCP) para [seu componente]. Ele permite que agentes de IA interajam com [seu componente] de forma padronizada.

## Ferramentas (Tools)

- **my_component_action**: Execute uma ação no componente
  - Parâmetros:
    - `param1` (string): Primeiro parâmetro da ação
    - `param2` (integer): Segundo parâmetro da ação
    - `optional_param` (boolean, opcional): Parâmetro opcional (padrão: false)
  - Retorno: Resultado da ação

## Recursos (Resources)

- **mycomponent://items**: Lista de itens do componente
- **mycomponent://item/{item_id}**: Detalhes de um item específico

## Exemplo de Uso

```python
from mcp_mycomponent_client import MyComponentClient

# Inicializar o cliente
client = MyComponentClient("http://localhost:8080")

# Executar uma ação
result = client.execute_action("test", 123)
print(result)

# Obter a lista de itens
items = client.get_items()
print(items)

# Obter detalhes de um item específico
item = client.get_item("item123")
print(item)
```
```

## Exemplos de Integração

### Exemplo 1: Integração com Sistema de Pagamento

```python
# mcp_payment.py
from fastmcp import FastMCP, mcp
import json
from payment_gateway import PaymentGateway

app = FastMCP(title="MCP-Payment")

# Configurar o gateway de pagamento
payment_gateway = PaymentGateway(
    api_key="your_api_key",
    secret="your_secret"
)

@mcp.tool("process_payment")
def process_payment(amount: float, currency: str, customer_id: str, description: str = None):
    """
    Processa um pagamento através do gateway.
    """
    try:
        result = payment_gateway.charge(
            amount=amount,
            currency=currency,
            customer_id=customer_id,
            description=description
        )
        return {
            "success": True,
            "transaction_id": result.transaction_id,
            "status": result.status
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.resource("payment://transactions")
def get_transactions():
    """
    Obtém a lista de transações recentes.
    """
    transactions = payment_gateway.list_transactions(limit=50)
    return json.dumps(transactions)

@mcp.resource("payment://transaction/{transaction_id}")
def get_transaction(transaction_id: str):
    """
    Obtém detalhes de uma transação específica.
    """
    transaction = payment_gateway.get_transaction(transaction_id)
    return json.dumps(transaction)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
```

### Exemplo 2: Integração com Serviço de Email

```python
# mcp_email.py
from fastmcp import FastMCP, mcp
import json
from email_service import EmailClient
from typing import List, Optional

app = FastMCP(title="MCP-Email")

# Configurar o cliente de email
email_client = EmailClient(
    smtp_server="smtp.example.com",
    smtp_port=587,
    username="your_username",
    password="your_password"
)

@mcp.tool("send_email")
def send_email(to: List[str], subject: str, body: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None, attachments: Optional[List[str]] = None):
    """
    Envia um email.
    """
    try:
        result = email_client.send(
            to=to,
            subject=subject,
            body=body,
            cc=cc or [],
            bcc=bcc or [],
            attachments=attachments or []
        )
        return {
            "success": True,
            "message_id": result.message_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.resource("email://templates")
def get_templates():
    """
    Obtém a lista de templates de email disponíveis.
    """
    templates = email_client.list_templates()
    return json.dumps(templates)

@mcp.resource("email://template/{template_id}")
def get_template(template_id: str):
    """
    Obtém um template de email específico.
    """
    template = email_client.get_template(template_id)
    return json.dumps(template)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)
```

## Melhores Práticas

### Segurança

1. **Autenticação**: Sempre implemente autenticação no seu servidor MCP.
2. **Autorização**: Defina claramente quais ferramentas e recursos cada cliente pode acessar.
3. **Validação de Entrada**: Valide todos os parâmetros de entrada para evitar injeção de código.
4. **Tratamento de Erros**: Implemente tratamento de erros adequado para evitar vazamento de informações sensíveis.

### Desempenho

1. **Cache**: Implemente cache para recursos frequentemente acessados.
2. **Paginação**: Para recursos que retornam grandes conjuntos de dados, implemente paginação.
3. **Timeout**: Configure timeouts adequados para evitar que chamadas lentas bloqueiem o sistema.
4. **Monitoramento**: Implemente métricas para monitorar o desempenho do seu servidor MCP.

### Manutenibilidade

1. **Documentação**: Documente todas as ferramentas e recursos do seu servidor MCP.
2. **Versionamento**: Implemente versionamento para garantir compatibilidade retroativa.
3. **Testes**: Escreva testes automatizados para garantir que sua integração funcione corretamente.
4. **Logging**: Implemente logging adequado para facilitar a depuração.

## Conclusão

Seguindo este guia, você pode integrar qualquer componente à arquitetura MCP First, permitindo que agentes de IA interajam com ele de forma padronizada. A abordagem MCP First garante que o sistema seja modular, flexível e escalável, facilitando a adição de novos componentes e a expansão para outros contextos.
