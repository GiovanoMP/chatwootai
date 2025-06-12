# README - Sistema MCP-Crew v2

## 🚀 Visão Geral

O **Sistema MCP-Crew v2** é uma plataforma revolucionária de automação empresarial baseada em arquitetura MCP-First (Model Context Protocol). Esta versão introduz capacidades avançadas de **provisão dinâmica de ferramentas** e **compartilhamento de conhecimento** entre agentes e crews, estabelecendo um novo paradigma para sistemas multi-agentes em ambientes corporativos.

### ✨ Principais Inovações

- **🔧 Provisão Dinâmica de Ferramentas**: Agentes descobrem e utilizam ferramentas automaticamente sem configuração prévia
- **🧠 Compartilhamento de Conhecimento**: Sistema de memória organizacional que permite aprendizado coletivo
- **⚡ Performance Otimizada**: Arquitetura Redis-first com cache multi-nível e latência sub-200ms
- **🏢 Multi-Tenancy Robusta**: Isolamento completo entre organizações com escalabilidade horizontal
- **🔗 Integração Odoo**: Preparado para agente universal no Odoo 16 via linguagem natural

## 📋 Índice

- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso Básico](#uso-básico)
- [API Reference](#api-reference)
- [Arquitetura](#arquitetura)
- [Desenvolvimento](#desenvolvimento)
- [Deployment](#deployment)
- [Monitoramento](#monitoramento)
- [Troubleshooting](#troubleshooting)
- [Contribuição](#contribuição)

## 🛠️ Instalação

### Pré-requisitos

- Python 3.11+
- Redis 6.0+
- Docker (opcional, recomendado)
- 4GB RAM mínimo (8GB recomendado)

### Instalação Local

```bash
# Clone o repositório
git clone https://github.com/sua-org/mcp-crew-system-v2.git
cd mcp-crew-system-v2

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# Inicie Redis (se não estiver rodando)
redis-server

# Execute o sistema
python src/main.py
```

### Instalação com Docker

```bash
# Clone o repositório
git clone https://github.com/sua-org/mcp-crew-system-v2.git
cd mcp-crew-system-v2

# Execute com Docker Compose
docker-compose up -d

# Verifique status
docker-compose ps
```

### Instalação em Kubernetes

```bash
# Aplique manifests
kubectl apply -f k8s/

# Verifique deployment
kubectl get pods -n mcp-crew

# Acesse via port-forward
kubectl port-forward svc/mcp-crew-api 5003:80 -n mcp-crew
```

## ⚙️ Configuração

### Configuração Básica

O sistema utiliza variáveis de ambiente para configuração. Principais variáveis:

```bash
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Cache TTL (segundos)
DEFAULT_CACHE_TTL=3600
TOOLS_CACHE_TTL=7200
KNOWLEDGE_CACHE_TTL=1800

# Performance
MAX_WORKERS=4
REQUEST_TIMEOUT=30
MAX_CONCURRENT_REQUESTS=100

# Segurança
JWT_SECRET_KEY=sua-chave-secreta
ENCRYPTION_KEY=sua-chave-criptografia

# Observabilidade
ENABLE_TRACING=true
ENABLE_METRICS=true
LOG_LEVEL=INFO
```

### Configuração de MCPs

MCPs são configurados no arquivo `src/config.py`:

```python
MCP_REGISTRY = {
    'mcp-mongodb': MCPConfig(
        name='mcp-mongodb',
        url='http://localhost:8001',
        cache_ttl=3600
    ),
    'mcp-redis': MCPConfig(
        name='mcp-redis', 
        url='http://localhost:8002',
        cache_ttl=1800
    ),
    'mcp-chatwoot': MCPConfig(
        name='mcp-chatwoot',
        url='http://localhost:8004',
        cache_ttl=900
    ),
    'mcp-qdrant': MCPConfig(
        name='mcp-qdrant',
        url='http://localhost:8003',
        cache_ttl=7200
    )
}
```

### Configuração de Crews

Crews são configuradas via YAML em `config/agents.yaml` e `config/tasks.yaml`:

```yaml
# config/agents.yaml
agents:
  product_researcher:
    role: "Pesquisador de Produtos"
    goal: "Encontrar produtos relevantes usando ferramentas disponíveis"
    backstory: "Especialista em pesquisa de produtos com acesso a sistemas avançados"
    
  customer_support:
    role: "Agente de Suporte"
    goal: "Resolver problemas de clientes eficientemente"
    backstory: "Especialista em atendimento ao cliente com conhecimento técnico"
```

## 🚀 Uso Básico

### Iniciando o Sistema

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Inicie o servidor
python src/main.py

# O sistema estará disponível em http://localhost:5003
```

### Primeira Requisição

```bash
# Teste de saúde
curl http://localhost:5003/api/mcp-crew/health

# Descoberta de ferramentas
curl -X POST http://localhost:5003/api/mcp-crew/tools/discover \
  -H "Content-Type: application/json" \
  -d '{"account_id": "sua_empresa", "force_refresh": true}'

# Processamento de requisição
curl -X POST http://localhost:5003/api/mcp-crew/process_request \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "sua_empresa",
    "channel": "api",
    "payload": {
      "text": "Preciso de informações sobre produtos eletrônicos",
      "sender_id": "user_001"
    }
  }'
```

### Armazenamento de Conhecimento

```bash
curl -X POST http://localhost:5003/api/mcp-crew/knowledge/store \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "sua_empresa",
    "type": "product_info",
    "topic": "produtos",
    "title": "Smartphone Samsung Galaxy S24",
    "content": {
      "name": "Samsung Galaxy S24",
      "price": "R$ 2.999,00",
      "specs": {
        "display": "6.2 polegadas",
        "camera": "50MP tripla"
      }
    },
    "source_agent": "product_researcher",
    "tags": ["samsung", "smartphone"]
  }'
```

### Busca de Conhecimento

```bash
# Busca por tópico
curl "http://localhost:5003/api/mcp-crew/knowledge/search/sua_empresa?topic=produtos&limit=10"

# Busca por conteúdo
curl "http://localhost:5003/api/mcp-crew/knowledge/search/sua_empresa?query=samsung&limit=5"
```

## 📚 API Reference

### Endpoints Principais

#### Health Check
```
GET /api/mcp-crew/health
```
Verifica status do sistema e MCPs conectados.

#### Processamento de Requisições
```
POST /api/mcp-crew/process_request
```
Processa requisição utilizando crews apropriadas.

**Body:**
```json
{
  "account_id": "string",
  "channel": "string",
  "payload": {
    "text": "string",
    "sender_id": "string",
    "conversation_id": "string"
  }
}
```

#### Descoberta de Ferramentas
```
POST /api/mcp-crew/tools/discover
```
Força descoberta de ferramentas de MCPs.

**Body:**
```json
{
  "account_id": "string",
  "force_refresh": boolean
}
```

#### Gestão de Conhecimento

**Armazenar Conhecimento:**
```
POST /api/mcp-crew/knowledge/store
```

**Buscar Conhecimento:**
```
GET /api/mcp-crew/knowledge/search/{account_id}
```

**Recuperar Conhecimento:**
```
GET /api/mcp-crew/knowledge/retrieve/{account_id}/{knowledge_id}
```

#### Métricas e Monitoramento

**Métricas Gerais:**
```
GET /api/mcp-crew/metrics
```

**Métricas por Tenant:**
```
GET /api/mcp-crew/tenant/{account_id}/metrics
```

**Configuração de MCPs:**
```
GET /api/mcp-crew/config/mcps
```

### Códigos de Resposta

- `200` - Sucesso
- `201` - Criado com sucesso
- `400` - Erro de validação
- `401` - Não autorizado
- `404` - Não encontrado
- `500` - Erro interno

## 🏗️ Arquitetura

### Componentes Principais

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │  Orquestrador   │    │ Tool Discovery  │
│                 │────│    Principal    │────│                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Knowledge     │    │     Redis       │    │      MCPs       │
│   Manager       │────│    Cache        │────│   Externos     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Fluxo de Dados

1. **Requisição** → API Gateway valida e autentica
2. **Descoberta** → Tool Discovery identifica ferramentas disponíveis
3. **Análise** → Orquestrador seleciona crew apropriada
4. **Execução** → Crew executa com ferramentas dinâmicas
5. **Conhecimento** → Resultados são catalogados automaticamente
6. **Resposta** → Resultado é retornado ao cliente

### Tecnologias Utilizadas

- **Backend**: Python 3.11, Flask, CrewAI
- **Cache**: Redis 6.0+ com Streams
- **Observabilidade**: OpenTelemetry, Prometheus
- **Containerização**: Docker, Kubernetes
- **Segurança**: JWT, AES-256, TLS

## 💻 Desenvolvimento

### Estrutura do Projeto

```
mcp_crew_system_v2/
├── src/
│   ├── main.py                 # Ponto de entrada
│   ├── config.py              # Configurações
│   ├── mcp_crew_core.py       # Orquestrador principal
│   ├── mcp_tool_discovery.py  # Descoberta de ferramentas
│   ├── knowledge_sharing.py   # Compartilhamento de conhecimento
│   └── routes/
│       └── mcp_crew.py        # Rotas da API
├── config/
│   ├── agents.yaml            # Configuração de agentes
│   └── tasks.yaml             # Configuração de tarefas
├── tests/
│   └── test_suite_v2.py       # Suite de testes
├── requirements.txt           # Dependências Python
├── docker-compose.yml        # Configuração Docker
└── README.md                  # Este arquivo
```

### Executando Testes

```bash
# Testes unitários
python -m pytest tests/

# Suite de testes completa
python test_suite_v2.py

# Testes de carga
python tests/load_test.py
```

### Contribuindo

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Padrões de Código

- Use type hints em todas as funções
- Docstrings no formato Google
- Máximo 88 caracteres por linha
- Testes para todas as funcionalidades públicas

## 🚢 Deployment

### Ambiente de Produção

```bash
# Configuração de produção
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
export REDIS_HOST=redis-cluster.internal
export ENABLE_METRICS=true

# Deploy com Docker
docker-compose -f docker-compose.prod.yml up -d

# Verificação
curl http://localhost:5003/api/mcp-crew/health
```

### Kubernetes

```bash
# Namespace
kubectl create namespace mcp-crew

# Secrets
kubectl create secret generic mcp-crew-secrets \
  --from-literal=jwt-secret=sua-chave \
  --from-literal=redis-password=sua-senha \
  -n mcp-crew

# Deploy
kubectl apply -f k8s/ -n mcp-crew

# Verificação
kubectl get pods -n mcp-crew
kubectl logs -f deployment/mcp-crew-api -n mcp-crew
```

### Scaling

```bash
# Horizontal Pod Autoscaler
kubectl autoscale deployment mcp-crew-api \
  --cpu-percent=70 \
  --min=3 \
  --max=20 \
  -n mcp-crew

# Verificar scaling
kubectl get hpa -n mcp-crew
```

## 📊 Monitoramento

### Métricas Principais

- **Latência**: P50, P95, P99 de requisições
- **Throughput**: Requisições por segundo
- **Taxa de Erro**: Percentual de requisições falhadas
- **Utilização**: CPU, memória, Redis

### Dashboards

Dashboards Grafana pré-configurados disponíveis em `/monitoring/dashboards/`:

- **Executive Dashboard**: Métricas de negócio
- **Technical Dashboard**: Métricas de sistema
- **Redis Dashboard**: Performance do cache
- **MCPs Dashboard**: Status dos MCPs

### Alertas

Alertas configurados para:

- Latência > 500ms
- Taxa de erro > 5%
- Utilização CPU > 80%
- Redis indisponível
- MCPs offline

## 🔧 Troubleshooting

### Problemas Comuns

#### Sistema não inicia
```bash
# Verificar Redis
redis-cli ping

# Verificar logs
tail -f logs/mcp-crew.log

# Verificar configuração
python -c "from src.config import Config; print(Config.REDIS_HOST)"
```

#### Performance degradada
```bash
# Verificar métricas Redis
redis-cli info stats

# Verificar cache hit ratio
curl http://localhost:5003/api/mcp-crew/metrics

# Verificar MCPs
curl http://localhost:5003/api/mcp-crew/health
```

#### MCPs não descobertos
```bash
# Forçar redescoberta
curl -X POST http://localhost:5003/api/mcp-crew/tools/discover \
  -H "Content-Type: application/json" \
  -d '{"account_id": "test", "force_refresh": true}'

# Verificar conectividade
curl http://localhost:8001/health  # MCP MongoDB
curl http://localhost:8002/health  # MCP Redis
```

### Logs Importantes

```bash
# Logs de aplicação
tail -f logs/application.log

# Logs de descoberta de ferramentas
grep "Tool Discovery" logs/application.log

# Logs de conhecimento
grep "Knowledge" logs/application.log

# Logs de erro
grep "ERROR" logs/application.log
```

## 📞 Suporte

### Documentação

- [Documentação Técnica Completa](./documentacao_tecnica_mcp_crew_v2.md)
- [Guia de Conexão MCPs](./GUIA_CONEXAO_MCP_CREW.md)
- [API Documentation](./api-docs.md)

### Comunidade

- **Issues**: [GitHub Issues](https://github.com/sua-org/mcp-crew-system-v2/issues)
- **Discussões**: [GitHub Discussions](https://github.com/sua-org/mcp-crew-system-v2/discussions)
- **Discord**: [Servidor da Comunidade](https://discord.gg/mcp-crew)

### Suporte Comercial

Para suporte comercial e implementações empresariais:
- Email: suporte@mcp-crew.com
- Website: https://mcp-crew.com
- Telefone: +55 11 9999-9999

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- Equipe CrewAI pelo framework base
- Comunidade MCP pelo protocolo
- Contribuidores do projeto
- Beta testers e early adopters

---

**Sistema MCP-Crew v2** - Transformando automação empresarial através de inteligência artificial colaborativa.

*Desenvolvido com ❤️ pela equipe Manus AI*

