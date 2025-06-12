# Resumo de Desenvolvimento: Integração MCP-Chatwoot com MCPAdapt

## Contexto e Objetivo

Estamos desenvolvendo uma integração entre o servidor MCP-Chatwoot (baseado em FastAPI) e o framework MCPAdapt para permitir que agentes do CrewAI possam interagir com o Chatwoot através do protocolo MCP (Machine Communication Protocol). O objetivo principal é expor as funcionalidades do Chatwoot como ferramentas que podem ser descobertas e utilizadas dinamicamente por agentes de IA.

## Arquitetura Atual

```
CrewAI → MCPAdapt → MCP-Chatwoot (FastAPI) → Chatwoot API
```

- **MCP-Chatwoot**: Servidor FastAPI que implementa o protocolo MCP e se comunica com a API do Chatwoot
- **MCPAdapt**: Framework que permite a descoberta dinâmica de ferramentas via protocolo MCP
- **CrewAI**: Framework para criar agentes de IA que podem utilizar ferramentas externas

## Desafios Enfrentados

### 1. Conformidade com o Protocolo MCP

O principal desafio tem sido garantir que o servidor MCP-Chatwoot implemente corretamente o protocolo MCP, especificamente:

- **Mensagem `initialize`**: O MCPAdapt envia uma mensagem `initialize` para o servidor MCP-Chatwoot, que deve responder com um objeto JSON-RPC contendo informações sobre as capacidades do servidor.
- **Eventos SSE**: O servidor MCP-Chatwoot deve enviar eventos SSE (Server-Sent Events) no formato JSON-RPC esperado pelo MCPAdapt.

### 2. Problemas de Compatibilidade

Identificamos vários problemas de compatibilidade:

1. **Resposta à mensagem `initialize`**: Inicialmente, o servidor MCP-Chatwoot não respondia à mensagem `initialize` no formato JSON-RPC correto, causando falhas na descoberta de ferramentas.

2. **Formato dos eventos SSE**: Os eventos SSE enviados pelo MCP-Chatwoot não estavam no formato JSON-RPC esperado pelo MCPAdapt, causando erros de parsing JSON.

3. **Interpretação da URL do endpoint**: O MCPAdapt estava interpretando incorretamente a URL do endpoint enviada pelo MCP-Chatwoot, tentando fazer requisições para URLs inválidas.

## Modificações Realizadas

### 1. Endpoint `/messages/` (JSON-RPC)

Modificamos o endpoint `/messages/` para tratar especificamente a mensagem `initialize`:

```python
@app.post("/messages/")
async def handle_messages(request: Request):
    # ...
    if body.get("method") == "initialize":
        initialize_response = {
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "result": {
                "serverInfo": {
                    "name": "MCP-Chatwoot",
                    "version": "1.0.0",
                    "protocolVersion": "2025-03-26"
                },
                "capabilities": {
                    "tools": True,
                    "resources": False,
                    "prompts": False
                }
            }
        }
        return initialize_response
    # ...
```

### 2. Endpoint `/sse` (SSE)

Modificamos o endpoint `/sse` para enviar eventos no formato esperado pelo MCPAdapt:

```python
async def sse_endpoint(request: Request):
    # ...
    async def event_stream():
        # O MCPAdapt espera apenas a URL como valor do evento endpoint
        # A URL deve ser absoluta, incluindo o host
        full_url = f"http://{request.headers.get('host')}{message_url}"
        yield f"event: endpoint\ndata: {full_url}\n\n"
        # ...
```

## Abordagem Alternativa: Adaptador Direto

Devido aos desafios persistentes com o protocolo MCP e o MCPAdapt, começamos a desenvolver uma abordagem alternativa: um adaptador direto que se conecta ao servidor MCP-Chatwoot sem depender do MCPAdapt.

```
CrewAI → ChatwootDirectAdapter → MCP-Chatwoot (FastAPI) → Chatwoot API
```

Este adaptador:
1. Se conecta diretamente ao servidor MCP-Chatwoot via HTTP
2. Expõe as ferramentas do MCP-Chatwoot como funções Python compatíveis com o CrewAI
3. Elimina a complexidade do protocolo MCP e do MCPAdapt

O código do adaptador direto está em `/home/giovano/Projetos/ai_stack/ai-stack-docker/mcp-conectors/chatwoot_direct_adapter.py`.

## Próximos Passos

1. **Finalizar o adaptador direto**: Corrigir os problemas restantes no adaptador direto e garantir que ele funcione corretamente com o CrewAI.

2. **Testar com casos de uso reais**: Verificar se o adaptador direto permite que agentes do CrewAI interajam efetivamente com o Chatwoot.

3. **Documentar a solução**: Criar documentação detalhada sobre como usar o adaptador direto com o CrewAI.

4. **Decidir sobre o futuro do MCPAdapt**: Avaliar se vale a pena continuar tentando fazer o MCPAdapt funcionar com o MCP-Chatwoot ou se é melhor focar no adaptador direto.

## Arquivos Importantes

- `/home/giovano/Projetos/ai_stack/mcp-chatwoot/main.py`: Implementação do servidor MCP-Chatwoot
- `/home/giovano/Projetos/ai_stack/ai-stack-docker/mcp-conectors/test_mcpadapt_chatwoot.py`: Script de teste para a integração MCPAdapt com MCP-Chatwoot
- `/home/giovano/Projetos/ai_stack/ai-stack-docker/mcp-conectors/chatwoot_direct_adapter.py`: Implementação do adaptador direto
- `/home/giovano/Projetos/ai_stack/mcp-chatwoot/mcp_server.sh`: Script para gerenciar o servidor MCP-Chatwoot

## Lições Aprendidas

1. **Protocolo MCP é complexo**: O protocolo MCP tem requisitos específicos para o formato das mensagens JSON-RPC e eventos SSE que podem ser difíceis de implementar corretamente.

2. **Testes manuais são essenciais**: Testar manualmente os endpoints SSE e JSON-RPC foi crucial para identificar problemas de compatibilidade.

3. **Logging detalhado ajuda**: Adicionar logging detalhado no servidor MCP-Chatwoot e nos scripts de teste foi fundamental para diagnosticar problemas.

4. **Abordagens alternativas são importantes**: Quando uma abordagem (MCPAdapt) apresenta desafios persistentes, é importante considerar alternativas (adaptador direto).

5. **Formato dos eventos SSE é crítico**: O MCPAdapt espera que os eventos SSE estejam em um formato específico, e qualquer desvio causa falhas na comunicação.

## Recomendações para o Próximo Desenvolvedor

1. **Foque no adaptador direto**: O adaptador direto parece ser a abordagem mais promissora para integrar o MCP-Chatwoot com o CrewAI.

2. **Teste com casos de uso reais**: Verifique se o adaptador direto permite que agentes do CrewAI interajam efetivamente com o Chatwoot em cenários reais.

3. **Considere simplificar a arquitetura**: Se o adaptador direto funcionar bem, considere simplificar a arquitetura removendo a dependência do protocolo MCP e do MCPAdapt.

4. **Documente a solução**: Crie documentação detalhada sobre como usar o adaptador direto com o CrewAI para facilitar a adoção por outros desenvolvedores.

5. **Resolva problemas de conexão com Redis**: O servidor MCP-Chatwoot está reportando erros de conexão com o Redis, o que pode afetar algumas funcionalidades.
