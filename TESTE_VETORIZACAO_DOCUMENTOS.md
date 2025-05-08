# Teste de Vetorização de Documentos

Este documento descreve os passos para testar o fluxo de upload e vetorização de documentos no módulo `business_rules`.

## Pré-requisitos

1. Acesso ao Odoo com o módulo `business_rules` instalado
2. Acesso ao sistema de IA
3. Acesso ao Qdrant para verificar os vetores

## Passos para Teste

### 1. Teste do botão "Carregar documento"

1. Acesse o Odoo e vá para o módulo `business_rules`
2. Selecione uma regra de negócio existente ou crie uma nova
3. Vá para a aba "Documentos de Suporte ao Cliente"
4. Clique no botão "Adicionar Documento"
5. Preencha os campos obrigatórios:
   - Nome do Documento
   - Tipo de Documento
   - Selecione um arquivo para upload
6. Clique no botão "Extrair Conteúdo" para extrair o texto do documento
7. Clique no botão "Criar Documento"
8. Verifique se o documento foi criado com sucesso
9. **Verificação**: Acesse o Qdrant e verifique se o documento **NÃO** foi vetorizado

### 2. Teste do botão "Sincronizar com IA"

1. Após criar o documento, vá para a tela principal da regra de negócio
2. Clique no botão "Sincronizar com IA" no topo da página
3. Aguarde a sincronização ser concluída
4. **Verificação**: Acesse o Qdrant e verifique se o documento foi vetorizado corretamente

### 3. Teste de múltiplas sincronizações

1. Faça alguma alteração no documento (por exemplo, altere o nome ou o conteúdo)
2. Clique novamente no botão "Sincronizar com IA"
3. Aguarde a sincronização ser concluída
4. **Verificação**: Acesse o Qdrant e verifique se o documento foi atualizado corretamente e se **NÃO** foram criados múltiplos vetores para o mesmo documento

## Verificação no Qdrant

Para verificar os vetores no Qdrant, você pode usar o seguinte script Python:

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Conectar ao Qdrant
client = QdrantClient(host="localhost", port=6333)

# Definir o account_id e document_id para verificação
account_id = "seu_account_id"
document_id = "seu_document_id"

# Buscar documentos no Qdrant
points = client.scroll(
    collection_name="support_documents",
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="account_id",
                match=models.MatchValue(value=account_id)
            ),
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(value=str(document_id))
            )
        ]
    ),
    limit=10,
    with_payload=True,
    with_vectors=False,
)[0]

# Verificar quantos documentos foram encontrados
print(f"Encontrados {len(points)} documentos para account_id={account_id} e document_id={document_id}")

# Imprimir detalhes dos documentos encontrados
for i, point in enumerate(points):
    print(f"\nDocumento {i+1}:")
    print(f"ID: {point.id}")
    print(f"Nome: {point.payload.get('name')}")
    print(f"Tipo: {point.payload.get('document_type')}")
    print(f"Última atualização: {point.payload.get('last_updated')}")
```

## Resultados Esperados

1. **Teste do botão "Carregar documento"**: Nenhum vetor deve ser criado no Qdrant após clicar no botão "Criar Documento".

2. **Teste do botão "Sincronizar com IA"**: Um único vetor deve ser criado no Qdrant para o documento após clicar no botão "Sincronizar com IA".

3. **Teste de múltiplas sincronizações**: O vetor existente deve ser atualizado, e nenhum novo vetor deve ser criado para o mesmo documento.

## Resolução de Problemas

Se os testes não produzirem os resultados esperados, verifique:

1. Se as correções no sistema de IA foram implementadas corretamente
2. Se o botão "Carregar documento" não está chamando a sincronização automaticamente
3. Se o botão "Sincronizar com IA" está chamando a API corretamente
4. Se o agente de enriquecimento está processando os documentos corretamente

## Conclusão

Estes testes ajudarão a verificar se os problemas de vetorização foram resolvidos. Se todos os testes passarem, o sistema deve estar funcionando corretamente.
