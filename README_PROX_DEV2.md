# Documentação para o Próximo Desenvolvedor

## Visão Geral do Projeto

Este projeto consiste em um sistema modular de integração entre Odoo e um sistema de IA, utilizando FastAPI, MCP (Multi-Channel Platform) como camada de abstração, Redis para cache e Qdrant para busca vetorial. O sistema é projetado para ser multi-tenant, priorizando o `account_id` para identificação de banco de dados e usando domínios para organização do código.

## Arquitetura do Sistema

O sistema é composto por:

1. **Módulos Odoo**: Localizados em `/addons/`, incluindo:
   - `business_rules`: Gerenciamento de regras de negócio, configurações de atendimento, regras de agendamento e documentos de suporte
   - `ai_credentials_manager`: Gerenciamento centralizado de credenciais

2. **API Odoo**: Localizada em `@odoo_api/`, contendo:
   - Endpoints para cada módulo Odoo
   - Agentes de embedding para vetorização de dados

3. **Vetorização e Busca Semântica**:
   - Qdrant para armazenamento e busca de vetores
   - Agentes de embedding para processar e vetorizar dados

4. **Integração com IA**:
   - CrewAI para agentes autônomos
   - Configurações em YAML para definição de comportamento

## Reorganização dos Agentes de Embedding

Atualmente, todos os agentes de embedding estão no diretório `@odoo_api/embedding_agents/`. No entanto, como teremos múltiplos endpoints para cada módulo Odoo, precisamos reorganizar a estrutura para melhor manutenção:

```
@odoo_api/
├── embedding_agents/
│   ├── business_rules/
│   │   ├── rules_agent.py
│   │   ├── scheduling_agent.py
│   │   ├── support_docs_agent.py
│   │   └── service_config_agent.py
│   ├── semantic_product/
│   │   ├── product_agent.py
│   │   └── category_agent.py
│   └── other_modules/
│       └── ...
└── modules/
    ├── business_rules/
    │   ├── endpoints.py
    │   └── ...
    └── ...
```

Cada subdiretório dentro de `embedding_agents/` corresponderá a um módulo Odoo específico, contendo os agentes responsáveis pela vetorização dos diferentes tipos de dados desse módulo.

## Implementação de Endpoints para Visualização de Dados Vetorizados

Conforme discutido, precisamos implementar endpoints que permitam aos usuários visualizar os dados que foram vetorizados. Esses endpoints devem seguir a mesma estrutura e nomenclatura das abas no módulo Odoo correspondente:

1. **Para o módulo `business_rules`**:
   - Ver Informações Básicas
   - Ver Configurações de Atendimento
   - Ver Regras de Negócio e Promoções
   - Ver Regras de Agendamento
   - Ver Documentos de Suporte ao Cliente

Esses endpoints devem ser acessíveis através de botões na interface do Odoo, permitindo que o usuário visualize facilmente os dados que foram vetorizados e armazenados no Qdrant.

## Configuração do Qdrant

O Qdrant deve ser configurado para armazenar os vetores gerados pelos agentes de embedding. Cada tipo de dado deve ter sua própria coleção no Qdrant: Por questões arquiteturais, o Qdrant também está previsto para ser multi tenant sendo que cada tenat compartilhará as mesmas coleções mas com dados separados por tenat que correspondem ao account_id

```python
# Exemplo de configuração de coleções no Qdrant
collections = {
    "business_rules": {
        "vectors": {"size": 1536, "distance": "Cosine"},
        "shard_number": 1,
        "replication_factor": 1
    },
    "scheduling_rules": {
        "vectors": {"size": 1536, "distance": "Cosine"},
        "shard_number": 1,
        "replication_factor": 1
    },
    "support_documents": {
        "vectors": {"size": 1536, "distance": "Cosine"},
        "shard_number": 1,
        "replication_factor": 1
    },
    # Outras coleções...
}
```

Cada coleção deve incluir metadados relevantes para facilitar a recuperação e filtragem dos dados:

```python
# Exemplo de metadados para um ponto no Qdrant
point = {
    "id": unique_id,
    "vector": embedding_vector,
    "payload": {
        "account_id": "account_1",
        "domain": "retail",
        "module": "business_rules",
        "type": "rule",
        "content": rule_text,
        "created_at": timestamp,
        "updated_at": timestamp
    }
}
```

## Painel Integrado para Visualização de Vetorizações

Está previsto o desenvolvimento de um painel integrado que oferecerá uma visualização geral de todos os dados vetorizados no sistema. Este painel deve:

1. Mostrar estatísticas sobre as coleções no Qdrant
2. Permitir a visualização dos dados vetorizados por módulo
3. Oferecer funcionalidades de busca e filtragem
4. Exibir métricas de desempenho das buscas vetoriais

## API Bidirecional para Edição de Dados Vetorizados

Também está planejada a implementação de uma API bidirecional que permitirá a edição dos dados vetorizados diretamente da interface do Odoo. Esta API deve:

1. Permitir a atualização de dados no Qdrant quando alterados no Odoo
2. Sincronizar alterações feitas no sistema de IA de volta para o Odoo
3. Manter um histórico de alterações para auditoria
4. Implementar mecanismos de segurança para garantir a integridade dos dados

## Próximos Passos

1. Reorganizar os agentes de embedding conforme a estrutura proposta
2. Implementar os endpoints para visualização de dados vetorizados
3. Configurar o Qdrant com as coleções necessárias
4. Desenvolver o painel integrado para visualização de vetorizações
5. Implementar a API bidirecional para edição de dados vetorizados

## Considerações de Segurança

- Todas as credenciais devem ser armazenadas de forma segura
- A comunicação entre o Odoo e o sistema de IA deve ser autenticada
- O acesso aos dados vetorizados deve ser controlado por permissões
- As operações de edição de dados vetorizados devem ser registradas para auditoria

## Documentação Adicional

Para mais informações sobre os componentes específicos do sistema, consulte:

- `@ARCHITECTURE.md`: Visão geral da arquitetura do sistema
- `@odoo_api/README.md`: Documentação da API Odoo
- `@addons/business_rules/README.md`: Documentação do módulo de regras de negócio
- `@addons/ai_credentials_manager/README.md`: Documentação do módulo de gerenciamento de credenciais
