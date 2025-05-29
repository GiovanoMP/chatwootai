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
