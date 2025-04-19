# Arquitetura Multi-Tenant para Vetorização

Este documento descreve a arquitetura multi-tenant implementada para o sistema de vetorização usando Qdrant.

## Visão Geral

O sistema utiliza uma abordagem de **multi-tenancy em nível de coleção** com **particionamento lógico por account_id**. Isso significa que:

1. Todas as empresas (tenants) compartilham as mesmas coleções no Qdrant
2. Os dados são separados logicamente usando o campo `account_id` em cada documento
3. Todas as consultas são filtradas por `account_id` para garantir o isolamento dos dados

## Coleções Compartilhadas

O sistema utiliza três coleções principais:

1. **company_metadata**: Armazena metadados gerais da empresa
2. **business_rules**: Armazena regras de negócio (permanentes e temporárias)
3. **support_documents**: Armazena documentos de suporte ao cliente

## Estrutura dos Documentos

Cada documento armazenado no Qdrant inclui um campo `account_id` que identifica o tenant ao qual o documento pertence. Exemplo:

```json
{
  "id": "account_1_metadata",
  "vector": [...],
  "payload": {
    "account_id": "account_1",
    "metadata": {
      "company_info": {
        "company_name": "Empresa Exemplo",
        ...
      },
      ...
    },
    "processed_text": "...",
    "last_updated": "2023-06-15T14:30:00.000Z"
  }
}
```

## Índices

Para otimizar as consultas filtradas por `account_id`, cada coleção possui um índice específico:

```python
client.create_payload_index(
    collection_name=collection_name,
    field_name="account_id",
    field_schema=models.PayloadSchemaType.KEYWORD,
)
```

## Consultas

Todas as consultas ao Qdrant incluem um filtro por `account_id` para garantir que apenas os dados do tenant correto sejam retornados:

```python
account_filter = models.Filter(
    must=[
        models.FieldCondition(
            key="account_id",
            match=models.MatchValue(
                value=account_id
            )
        )
    ]
)

results = client.search(
    collection_name="business_rules",
    query_vector=query_embedding,
    filter=account_filter,
    limit=limit,
    score_threshold=score_threshold
)
```

## Vantagens desta Abordagem

1. **Eficiência de recursos**: Compartilhar coleções reduz a sobrecarga de gerenciamento de muitas coleções separadas
2. **Escalabilidade**: Suporta um número muito maior de tenants sem criar milhares de coleções
3. **Simplicidade operacional**: Facilita backups, monitoramento e manutenção
4. **Flexibilidade**: Permite consultas que abrangem múltiplos tenants (se necessário)
5. **Isolamento de dados**: Garante que cada tenant acesse apenas seus próprios dados

## Scripts de Migração

Para facilitar a transição da arquitetura anterior (uma coleção por tenant) para a nova arquitetura compartilhada, foram criados dois scripts:

1. `scripts/initialize_shared_collections.py`: Cria as novas coleções compartilhadas com os índices necessários
2. `scripts/migrate_qdrant_collections.py`: Migra os dados das coleções específicas por tenant para as coleções compartilhadas

## Considerações de Segurança

- O isolamento dos dados depende da correta aplicação dos filtros por `account_id` em todas as consultas
- É essencial validar o `account_id` em todas as requisições para evitar acesso não autorizado
- Recomenda-se implementar auditoria de acesso para monitorar consultas ao Qdrant

## Limitações

- Consultas sem filtro por `account_id` podem expor dados de outros tenants
- O desempenho pode ser afetado se o número total de documentos for muito grande (milhões)
- A exclusão completa de um tenant requer a remoção seletiva de seus documentos em todas as coleções
