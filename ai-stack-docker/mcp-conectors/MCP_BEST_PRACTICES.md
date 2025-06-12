# Boas Práticas para Servidores MCP e Adaptadores CrewAI

Este documento apresenta diretrizes e boas práticas para o desenvolvimento de servidores MCP (Model Context Protocol) e adaptadores para integração com o framework CrewAI, com foco especial na descoberta dinâmica de ferramentas.

## Índice

1. [Princípios Fundamentais](#princípios-fundamentais)
2. [Servidores MCP](#servidores-mcp)
   - [Exposição de Ferramentas](#exposição-de-ferramentas)
   - [Implementação de Endpoints](#implementação-de-endpoints)
   - [Documentação de Ferramentas](#documentação-de-ferramentas)
3. [Adaptadores CrewAI](#adaptadores-crewai)
   - [Descoberta Dinâmica](#descoberta-dinâmica)
   - [Conversão de Ferramentas](#conversão-de-ferramentas)
   - [Tratamento de Erros](#tratamento-de-erros)
4. [Testes e Validação](#testes-e-validação)
5. [Exemplos de Implementação](#exemplos-de-implementação)

## Princípios Fundamentais

1. **Descoberta Dinâmica**: Servidores MCP devem permitir a descoberta dinâmica de ferramentas sem hardcoding.
2. **Interoperabilidade**: Adaptadores devem funcionar com qualquer servidor MCP que siga o protocolo.
3. **Documentação Clara**: Ferramentas devem ter descrições claras e parâmetros bem documentados.
4. **Robustez**: Implementações devem tratar erros graciosamente e fornecer feedback útil.
5. **Flexibilidade**: Suportar diferentes transportes (SSE, REST, etc.) quando possível.

## Servidores MCP

### Exposição de Ferramentas

Para garantir a descoberta dinâmica de ferramentas, servidores MCP devem implementar pelo menos um dos seguintes mecanismos:

1. **Endpoint REST `/tools`**:
   - Deve retornar um JSON com a lista completa de ferramentas disponíveis
   - Formato recomendado:
   ```json
   {
     "tools": [
       {
         "name": "ferramenta-exemplo",
         "description": "Descrição detalhada da ferramenta",
         "parameters": {
           "param1": {
             "type": "string",
             "description": "Descrição do parâmetro"
           },
           "param2": {
             "type": "integer",
             "description": "Descrição do parâmetro"
           }
         }
       }
     ]
   }
   ```

2. **Método JSON-RPC `getTools`**:
   - Deve ser implementado para compatibilidade com clientes JSON-RPC
   - Deve retornar o mesmo formato do endpoint REST `/tools`
   - Exemplo de chamada:
   ```json
   {
     "jsonrpc": "2.0",
     "method": "getTools",
     "id": 1
   }
   ```

### Implementação de Endpoints

1. **Endpoint de Saúde**:
   - Implementar um endpoint `/health` que retorne o status do servidor
   - Incluir status de dependências (banco de dados, serviços externos, etc.)
   - Exemplo:
   ```json
   {
     "status": "healthy",
     "details": {
       "database": "ok",
       "external_service": "ok"
     }
   }
   ```

2. **Transporte SSE**:
   - Para servidores que usam SSE, implementar um endpoint `/sse` ou similar
   - Garantir que o endpoint suporte conexões de longa duração
   - Implementar reconexão automática em caso de falha

3. **Transporte REST**:
   - Para servidores que usam REST, implementar endpoints RESTful para cada ferramenta
   - Usar métodos HTTP apropriados (GET, POST, PUT, DELETE)
   - Retornar códigos de status HTTP adequados

### Documentação de Ferramentas

1. **Descrições Claras**:
   - Cada ferramenta deve ter uma descrição clara e concisa
   - Explicar o propósito, comportamento esperado e possíveis efeitos colaterais

2. **Parâmetros Bem Definidos**:
   - Documentar todos os parâmetros com tipos e descrições
   - Indicar quais parâmetros são obrigatórios e quais são opcionais
   - Fornecer valores padrão quando aplicável

3. **Exemplos de Uso**:
   - Incluir exemplos de uso para cada ferramenta
   - Mostrar entradas e saídas esperadas

## Adaptadores CrewAI

### Descoberta Dinâmica

Implementar um processo de descoberta dinâmica de ferramentas em três etapas:

1. **Verificação de Saúde**:
   - Verificar se o servidor MCP está acessível e saudável
   - Usar o endpoint `/health` se disponível

2. **Descoberta de Ferramentas**:
   - Tentar primeiro o endpoint REST `/tools`
   - Se não disponível, tentar o método JSON-RPC `getTools`
   - Se ambos falharem, usar uma lista padrão de ferramentas (apenas como último recurso)

3. **Validação de Ferramentas**:
   - Verificar se as ferramentas descobertas têm todos os campos necessários
   - Preencher campos ausentes com valores padrão quando possível

### Conversão de Ferramentas

Para converter ferramentas MCP em objetos Tool do CrewAI:

1. **Mapeamento de Campos**:
   - Nome da ferramenta MCP → Nome da ferramenta CrewAI
   - Descrição da ferramenta MCP → Descrição da ferramenta CrewAI
   - Parâmetros da ferramenta MCP → Parâmetros da função CrewAI

2. **Criação de Funções de Wrapper**:
   - Criar uma função Python para cada ferramenta MCP
   - Implementar chamadas JSON-RPC ou REST para o servidor MCP
   - Tratar erros e retornar resultados formatados

3. **Criação de Objetos Tool**:
   - Usar a classe `Tool` do CrewAI para criar objetos de ferramenta
   - Associar a função wrapper à ferramenta
   - Definir nome, descrição e outros metadados

### Tratamento de Erros

1. **Erros de Conexão**:
   - Implementar tentativas de reconexão com backoff exponencial
   - Fornecer mensagens de erro claras sobre problemas de conexão

2. **Erros de Ferramenta**:
   - Capturar e tratar erros específicos de cada ferramenta
   - Retornar mensagens de erro informativas para o agente

3. **Fallbacks**:
   - Implementar mecanismos de fallback para quando ferramentas não estão disponíveis
   - Considerar caching de resultados para operações frequentes

## Testes e Validação

1. **Testes de Conectividade**:
   - Verificar se o adaptador consegue se conectar ao servidor MCP
   - Testar diferentes cenários de rede (latência, desconexões, etc.)

2. **Testes de Descoberta**:
   - Verificar se todas as ferramentas são descobertas corretamente
   - Testar com diferentes versões do servidor MCP

3. **Testes de Execução**:
   - Verificar se cada ferramenta pode ser executada corretamente
   - Testar com diferentes parâmetros e condições de borda

4. **Testes de Integração**:
   - Verificar se o adaptador funciona corretamente com o CrewAI
   - Testar cenários completos de uso com agentes reais

## Exemplos de Implementação

### Servidor MCP com FastAPI

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Any

app = FastAPI()

# Lista de ferramentas disponíveis
tools = [
    {
        "name": "exemplo-ferramenta",
        "description": "Uma ferramenta de exemplo",
        "parameters": {
            "param1": {"type": "string", "description": "Primeiro parâmetro"},
            "param2": {"type": "integer", "description": "Segundo parâmetro"}
        }
    }
]

@app.get("/tools")
async def get_tools():
    """Endpoint para listar todas as ferramentas disponíveis."""
    return {"tools": tools}

@app.get("/health")
async def health_check():
    """Endpoint para verificar a saúde do servidor."""
    return {
        "status": "healthy",
        "details": {
            "database": "ok",
            "external_service": "ok"
        }
    }
```

### Adaptador CrewAI Dinâmico

```python
import requests
from typing import List, Dict, Any
from crewai.tools.base_tool import Tool

class DynamicMCPAdapter:
    """Adaptador dinâmico para servidores MCP."""
    
    def __init__(self, base_url: str):
        """
        Inicializa o adaptador com a URL base do servidor MCP.
        
        Args:
            base_url: URL base do servidor MCP
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self._tools = None
        self._verify_server_health()
        
    def _verify_server_health(self) -> None:
        """Verifica se o servidor MCP está acessível e saudável."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            health_data = response.json()
            print(f"Status do servidor MCP: {health_data}")
        except Exception as e:
            print(f"Aviso: Não foi possível verificar a saúde do servidor: {e}")
    
    def _discover_tools(self) -> List[Dict[str, Any]]:
        """Descobre ferramentas disponíveis no servidor MCP."""
        # Tentar endpoint REST /tools
        try:
            response = self.session.get(f"{self.base_url}/tools")
            if response.status_code == 200:
                data = response.json()
                if "tools" in data and isinstance(data["tools"], list):
                    print(f"Ferramentas descobertas via endpoint /tools: {len(data['tools'])}")
                    return data["tools"]
        except Exception as e:
            print(f"Erro ao descobrir ferramentas via REST: {e}")
        
        # Tentar método JSON-RPC getTools
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "getTools",
                "id": 1
            }
            response = self.session.post(f"{self.base_url}/jsonrpc", json=payload)
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "tools" in data["result"]:
                    print(f"Ferramentas descobertas via JSON-RPC: {len(data['result']['tools'])}")
                    return data["result"]["tools"]
        except Exception as e:
            print(f"Erro ao descobrir ferramentas via JSON-RPC: {e}")
        
        # Fallback para lista padrão
        print("Aviso: Usando lista padrão de ferramentas")
        return self._get_default_tools()
    
    def _get_default_tools(self) -> List[Dict[str, Any]]:
        """Retorna uma lista padrão de ferramentas como fallback."""
        # Implementar conforme necessário
        return []
    
    def _create_tool_function(self, tool_data: Dict[str, Any]):
        """Cria uma função wrapper para uma ferramenta MCP."""
        tool_name = tool_data["name"]
        
        def tool_function(**kwargs):
            """Função wrapper que chama a ferramenta no servidor MCP."""
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "method": tool_name,
                    "params": kwargs,
                    "id": 1
                }
                response = self.session.post(f"{self.base_url}/jsonrpc", json=payload)
                response.raise_for_status()
                result = response.json()
                if "error" in result:
                    return f"Erro: {result['error']['message']}"
                return result.get("result", {})
            except Exception as e:
                return f"Erro ao executar {tool_name}: {str(e)}"
        
        return tool_function
    
    def _build_tool(self, tool_data: Dict[str, Any]) -> Tool:
        """Constrói um objeto Tool do CrewAI a partir dos dados da ferramenta MCP."""
        tool_name = tool_data["name"]
        tool_description = tool_data.get("description", f"Tool Name: {tool_name}")
        tool_function = self._create_tool_function(tool_data)
        
        return Tool(
            name=tool_name,
            description=tool_description,
            func=tool_function
        )
    
    @property
    def tools(self) -> List[Tool]:
        """Retorna a lista de ferramentas como objetos Tool do CrewAI."""
        if self._tools is None:
            raw_tools = self._discover_tools()
            self._tools = [self._build_tool(tool) for tool in raw_tools]
        return self._tools
```

## Conclusão

Seguir estas boas práticas garantirá que seus servidores MCP e adaptadores CrewAI sejam robustos, interoperáveis e fáceis de manter. A descoberta dinâmica de ferramentas é essencial para criar agentes de IA verdadeiramente adaptáveis que possam aproveitar todas as capacidades disponíveis sem configuração manual excessiva.

Para mais informações sobre o protocolo MCP e o framework CrewAI, consulte a documentação oficial:
- [Documentação do MCP](https://github.com/microsoft/mcp)
- [Documentação do CrewAI](https://github.com/crewai/crewai)
