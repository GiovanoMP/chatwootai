# MCP-Crew: Cérebro Central para Integração de Agentes de IA

## Visão Geral

MCP-Crew é um protocolo central de contexto para modelos (Model Context Protocol) projetado para gerenciar múltiplas crews de agentes de IA de forma eficiente, escalável e segura. Este sistema atua como um "cérebro central" que coordena a comunicação entre diferentes crews especializadas (Mercado Livre, Instagram, Facebook, etc.) e facilita a integração com diversos serviços externos.

## Características Principais

- **Sistema de Gerenciamento de Agentes**: Coordenação centralizada de múltiplos agentes com papéis especializados
- **Protocolos de Comunicação Padronizados**: Interface unificada para todas as crews
- **Mecanismos de Autorização Configuráveis**: Controle granular sobre permissões e ações autônomas
- **Arquitetura Modular e Escalável**: Facilidade para adicionar novas crews e integrações
- **Otimização com Redis**: Suporte para cache de alta performance e gerenciamento de contexto
- **Processamento Paralelo**: Capacidade de executar múltiplas tarefas simultaneamente
- **Documentação Abrangente**: Guias detalhados para desenvolvimento e integração

## Arquitetura

O MCP-Crew segue uma arquitetura modular com os seguintes componentes principais:

```
mcp_crew/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent_manager.py      # Gerenciamento de agentes
│   │   ├── auth_manager.py       # Controle de autorizações
│   │   ├── communication.py      # Protocolos de comunicação
│   │   ├── context_manager.py    # Gerenciamento de contexto
│   │   └── redis_integration.py  # Integração com Redis
│   ├── crews/
│   │   ├── __init__.py
│   │   ├── base_crew.py          # Classe base para todas as crews
│   │   └── mercadolivre_crew.py  # Implementação específica para Mercado Livre
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── mcp_connector.py      # Conector para outros MCPs
│   │   └── odoo_connector.py     # Conector para Odoo
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py            # Utilitários de logging
│   │   └── serialization.py      # Serialização de dados
│   ├── __init__.py
│   └── main.py                   # Ponto de entrada principal
├── config/
│   ├── default_config.yaml       # Configurações padrão
│   └── crews/                    # Configurações específicas para cada crew
│       └── mercadolivre.yaml
├── tests/                        # Testes unitários e de integração
├── docs/                         # Documentação detalhada
├── examples/                     # Exemplos de uso
├── requirements.txt              # Dependências
├── setup.py                      # Script de instalação
└── README.md                     # Este arquivo
```

## Fluxo de Dados

1. **Recebimento de Solicitações**: O MCP-Crew recebe solicitações de agentes, sistemas externos ou usuários
2. **Autorização**: Verifica permissões e níveis de acesso
3. **Roteamento**: Direciona a solicitação para a crew especializada apropriada
4. **Processamento**: A crew processa a solicitação, possivelmente interagindo com MCPs específicos
5. **Resposta**: Os resultados são retornados ao solicitante original
6. **Persistência**: Informações relevantes são armazenadas para uso futuro

## Integração com Redis

O MCP-Crew utiliza Redis para otimizar o desempenho e gerenciar o contexto dos agentes:

- **Cache de Alta Velocidade**: Armazenamento em memória para acesso rápido a dados frequentes
- **Gerenciamento de Estado**: Manutenção do estado dos agentes entre interações
- **Filas de Mensagens**: Comunicação assíncrona entre componentes
- **Armazenamento de Contexto**: Preservação de contexto conversacional e histórico de interações
- **Expiração Automática**: Limpeza de dados temporários após um período definido

## Mecanismos de Autorização

O MCP-Crew implementa um sistema sofisticado de controle de autorização:

- **Níveis de Permissão**: Controle granular sobre o que cada agente pode fazer
- **Aprovação Manual**: Configuração para exigir aprovação humana para ações específicas
- **Auditoria**: Registro detalhado de todas as ações e decisões
- **Políticas Personalizáveis**: Definição de regras específicas para diferentes contextos

## Processamento Paralelo

Para garantir alta performance, o MCP-Crew suporta processamento paralelo:

- **Multithreading**: Execução simultânea de múltiplas tarefas
- **Processamento Assíncrono**: Operações não-bloqueantes para maior eficiência
- **Balanceamento de Carga**: Distribuição inteligente de tarefas entre recursos disponíveis
- **Escalabilidade Horizontal**: Capacidade de adicionar mais recursos conforme necessário

## Requisitos

- Python 3.8+
- Redis 6.0+ (opcional, mas recomendado para produção)
- Dependências listadas em requirements.txt

## Instalação

```bash
# Clone o repositório
git clone https://github.com/sprintia/mcp-crew.git
cd mcp-crew

# Instale as dependências
pip install -r requirements.txt

# Configure o ambiente
cp config/default_config.yaml config/config.yaml
# Edite config/config.yaml conforme necessário

# Execute o servidor
python -m src.main
```

## Uso Básico

```python
from mcp_crew.core import MCPCrew
from mcp_crew.crews import MercadoLivreCrew

# Inicialize o MCP-Crew
mcp = MCPCrew(config_path="config/config.yaml")

# Registre uma crew
ml_crew = MercadoLivreCrew(
    client_id="seu_client_id",
    client_secret="seu_client_secret"
)
mcp.register_crew("mercado_livre", ml_crew)

# Inicie o servidor
mcp.start()
```

## Integração com Outros MCPs

O MCP-Crew foi projetado para se integrar facilmente com MCPs específicos, como o MCP do Mercado Livre:

```python
from mcp_crew.integrations import MCPConnector

# Conecte-se ao MCP do Mercado Livre
ml_mcp = MCPConnector(
    mcp_type="mercado_livre",
    endpoint="https://api.mercadolivre.mcp.com",
    credentials={
        "client_id": "seu_client_id",
        "client_secret": "seu_client_secret"
    }
)

# Registre o MCP no MCP-Crew
mcp.register_mcp("mercado_livre", ml_mcp)
```

## Arquitetura Docker

O MCP-Crew foi projetado para ser executado em ambiente Docker, facilitando a implantação e a integração com outros serviços. A arquitetura Docker do MCP-Crew consiste em:

### Componentes Docker

- **Contêiner MCP-Crew**: Executa o servidor principal que gerencia as crews e os conectores MCP
- **Contêiner MCP-MongoDB**: Fornece acesso a dados armazenados no MongoDB com suporte a multi-tenancy
- **Rede AI_Network**: Conecta todos os MCPs em uma única rede Docker para comunicação eficiente

### Estrutura do Docker Compose

O arquivo `docker-compose.ai-stack.yml` na raiz do projeto orquestra todos os componentes da stack de IA:

```yaml
version: '3.8'

services:
  # MCP-Crew - Gerenciador de Crews e Conectores MCP
  mcp-crew:
    build:
      context: ./mcp-crew
      dockerfile: Dockerfile
    container_name: mcp-crew
    environment:
      - MONGODB_URI=mongodb://config_user:config_password@chatwoot-mongodb:27017/config_service
      - REDIS_URI=redis://redis:6379/0
      - MCP_MONGODB_URL=http://mcp-mongodb:8000
      - DEFAULT_TENANT=account_1
      - MULTI_TENANT=true
    ports:
      - "5000:5000"
    networks:
      - ai_network

  # MCP-MongoDB - Conector para MongoDB
  mcp-mongodb:
    build:
      context: ./mcp-mongodb
      dockerfile: Dockerfile
    container_name: mcp-mongodb
    environment:
      - MONGODB_URI=mongodb://config_user:config_password@chatwoot-mongodb:27017/config_service
      - MULTI_TENANT=true
      - DEFAULT_TENANT=account_1
      - ALLOWED_COLLECTIONS=company_services,tenants,configurations
    ports:
      - "8001:8000"
    networks:
      - ai_network
      - chatwoot-mongo-network

networks:
  ai_network:
    name: ai_network
    driver: bridge
  chatwoot-mongo-network:
    external: true
```

### Como Funciona

1. **Inicialização**: Ao iniciar o stack com `./start-ai-stack.sh`, todos os contêineres são construídos e iniciados
2. **Registro de MCPs**: O MCP-Crew automaticamente registra os MCPs disponíveis na rede
3. **Comunicação**: Os serviços se comunicam através da rede `ai_network` usando os nomes dos contêineres
4. **Multi-tenancy**: Todos os serviços suportam multi-tenancy via `account_id`

### Adicionando Novos MCPs

Para adicionar um novo MCP à stack:

1. **Criar o Diretório do MCP**: Crie um diretório para o novo MCP (ex: `mcp-odoo`)
2. **Implementar o Conector**: Crie um conector que implemente a interface `MCPConnector`
3. **Criar o Dockerfile**: Defina como o MCP será construído em Docker
4. **Adicionar ao Docker Compose**: Adicione uma nova seção de serviço ao `docker-compose.ai-stack.yml`
5. **Registrar no MCP-Crew**: Atualize o `start.py` para registrar o novo MCP

Exemplo de adição do MCP-Odoo:

```yaml
# Adicionar ao docker-compose.ai-stack.yml
services:
  # ... serviços existentes ...

  # MCP-Odoo - Conector para Odoo
  mcp-odoo:
    build:
      context: ./mcp-odoo
      dockerfile: Dockerfile
    container_name: mcp-odoo
    environment:
      - ODOO_URL=http://odoo-server:8069
      - ODOO_DB=odoo_db
      - MULTI_TENANT=true
      - DEFAULT_TENANT=account_1
    ports:
      - "8002:8002"
    networks:
      - ai_network
```

## Próximos Passos

- Implementação de crews adicionais (Instagram, Facebook, etc.)
- Integração com mais serviços externos
- Aprimoramento da interface de usuário
- Otimizações de performance
- Expansão da documentação e exemplos

## Contribuição

Contribuições são bem-vindas! Por favor, siga as diretrizes de contribuição no arquivo CONTRIBUTING.md.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.
