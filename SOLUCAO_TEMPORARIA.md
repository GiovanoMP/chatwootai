# Solução Temporária para o Problema de Múltiplas Vetorizações

## Problema

Quando um único documento de suporte é vetorizado, o sistema está criando 4 vetores diferentes no Qdrant. Isso causa problemas de duplicação e pode afetar a qualidade das respostas do sistema de IA.

## Solução Temporária

### 1. Limpar os vetores existentes

Primeiro, vamos limpar todos os vetores existentes no Qdrant para os documentos de suporte. Isso pode ser feito usando o seguinte script Python:

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Conectar ao Qdrant
client = QdrantClient(host="localhost", port=6333)

# Definir o account_id
account_id = "account_1"  # Substitua pelo seu account_id

# Buscar todos os documentos no Qdrant para este account_id
points = client.scroll(
    collection_name="support_documents",
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="account_id",
                match=models.MatchValue(value=account_id)
            )
        ]
    ),
    limit=100,
    with_payload=True,
    with_vectors=False,
)[0]

# Imprimir os documentos encontrados
print(f"Encontrados {len(points)} documentos para account_id={account_id}")

# Perguntar ao usuário se deseja excluir todos os documentos
resposta = input("Deseja excluir todos os documentos? (s/n): ")

if resposta.lower() == "s":
    # Excluir todos os documentos
    ids_to_delete = [point.id for point in points]
    
    if ids_to_delete:
        client.delete(
            collection_name="support_documents",
            points_selector=models.PointIdsList(
                points=ids_to_delete
            )
        )
        print(f"Excluídos {len(ids_to_delete)} documentos")
    else:
        print("Nenhum documento para excluir")
else:
    print("Operação cancelada")
```

Salve este script como `limpar_vetores.py` e execute-o com Python:

```bash
python limpar_vetores.py
```

### 2. Modificar o fluxo de trabalho

Em vez de usar o botão "Sincronizar com IA" para vetorizar todos os documentos, use o botão "Sincronizar" individual em cada documento. Isso pode ajudar a isolar o problema e identificar quais documentos estão causando a duplicação.

#### Passos:

1. Acesse o Odoo e vá para o módulo `business_rules`
2. Selecione a regra de negócio que contém os documentos
3. Vá para a aba "Documentos de Suporte ao Cliente"
4. Para cada documento:
   - Clique no documento para abri-lo
   - Clique no botão "Sincronizar" individual
   - Verifique no Qdrant se apenas um vetor foi criado

### 3. Verificar no Qdrant

Após cada sincronização, verifique no Qdrant se apenas um vetor foi criado para o documento. Isso pode ser feito usando o seguinte script Python:

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Conectar ao Qdrant
client = QdrantClient(host="localhost", port=6333)

# Definir o account_id e document_id
account_id = "account_1"  # Substitua pelo seu account_id
document_id = "123"  # Substitua pelo ID do documento

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

Salve este script como `verificar_vetores.py` e execute-o com Python:

```bash
python verificar_vetores.py
```

## Próximos passos

1. Implementar as correções no sistema de IA conforme as recomendações no arquivo `CORRECOES_SISTEMA_IA.md`.
2. Testar o fluxo completo de upload e vetorização de documentos para garantir que os problemas foram resolvidos.
3. Considerar a implementação de um formato JSON mais estruturado para os documentos no Qdrant para facilitar a busca semântica.

## Observações

Esta é apenas uma solução temporária até que as correções no sistema de IA possam ser implementadas. O problema raiz está no método `sync_support_documents_with_data` que está gerando múltiplos vetores para o mesmo documento.

As correções necessárias estão detalhadas no arquivo `CORRECOES_SISTEMA_IA.md` e devem ser implementadas o mais rápido possível para resolver o problema de forma permanente.
