# Recomendações para Correção de Problemas de Vetorização

## Problemas Identificados

1. **Múltiplas Vetorizações**: Quando um documento é carregado, estão sendo criados 4 arquivos no Qdrant para cada documento.
2. **Botão "Carregar documento" vetoriza o documento**: O botão dentro do bloco de upload está vetorizando o documento imediatamente, quando deveria apenas carregar o documento.
3. **Falta de enriquecimento de documentos**: Parece que a vetorização está ocorrendo diretamente sem o enriquecimento do contexto pelo agente responsável.
4. **Formato dos documentos no Qdrant**: O formato atual pode não ser o mais adequado para busca semântica com agentes de IA.

## Correções Recomendadas

### 1. Corrigir o problema de múltiplas vetorizações

No arquivo `odoo_api/modules/business_rules/services.py`, método `sync_support_documents_with_data`, o problema está na geração de UUIDs aleatórios para cada documento:

```python
# Gerar um ID único para o documento usando UUID
import uuid
document_id = str(uuid.uuid4())
```

Isso faz com que cada vez que o documento é sincronizado, um novo vetor seja criado no Qdrant com um ID diferente, em vez de atualizar o vetor existente.

**Solução recomendada**:
Modificar o código para usar um ID determinístico baseado no account_id e no document_id do Odoo:

```python
# Usar um ID determinístico baseado no account_id e document_id
document_id = f"{account_id}_{doc_id}"
```

### 2. Garantir que o agente de enriquecimento seja chamado corretamente

O código atual já está chamando o agente de enriquecimento:

```python
try:
    processed_text = await support_doc_agent.process_data(document_data, business_area)
    logger.info(f"Processed document {doc_id} using support document agent")
except Exception as agent_error:
    logger.error(f"Failed to process document with agent: {agent_error}")
    # Usar o texto original como fallback
    processed_text = original_text
```

Mas é importante verificar se o agente está funcionando corretamente e se os dados estão sendo passados no formato esperado.

### 3. Melhorar o formato dos documentos no Qdrant

O formato atual dos documentos no Qdrant é:

```python
payload={
    "account_id": account_id,
    "business_rule_id": business_rule_id,
    "document_id": doc_id,
    "name": doc_name,
    "document_type": doc_type,
    "content": doc_content,
    "original_text": original_text,
    "processed_text": processed_text,
    "ai_processed": original_text != processed_text,
    "last_updated": datetime.now().isoformat()
}
```

**Recomendação**:
Converter para um formato JSON mais estruturado que facilite a busca semântica:

```python
payload={
    "metadata": {
        "account_id": account_id,
        "business_rule_id": business_rule_id,
        "document_id": doc_id,
        "name": doc_name,
        "document_type": doc_type,
        "last_updated": datetime.now().isoformat(),
        "ai_processed": original_text != processed_text
    },
    "content": {
        "original": original_text,
        "processed": processed_text
    },
    # Adicionar campos estruturados extraídos pelo agente
    "structured_data": {
        # Aqui o agente poderia extrair informações estruturadas do documento
        # Por exemplo: categorias, tópicos, entidades, etc.
    }
}
```

### 4. Implementar verificação de existência antes de inserir

Antes de inserir um novo documento no Qdrant, verificar se já existe um documento com o mesmo ID e, se existir, atualizá-lo em vez de criar um novo:

```python
# Verificar se o documento já existe
existing_points = vector_service.qdrant_client.scroll(
    collection_name=collection_name,
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.account_id",
                match=models.MatchValue(value=account_id)
            ),
            models.FieldCondition(
                key="metadata.document_id",
                match=models.MatchValue(value=doc_id)
            )
        ]
    ),
    limit=1,
    with_payload=False,
    with_vectors=False,
)[0]

# Se o documento já existe, usar o mesmo ID
if existing_points:
    document_id = existing_points[0].id
else:
    # Usar um ID determinístico
    document_id = f"{account_id}_{doc_id}"
```

## Conclusão

Estas recomendações visam resolver os problemas identificados na vetorização de documentos. Ao implementar estas mudanças, o sistema deve:

1. Evitar a criação de múltiplos vetores para o mesmo documento
2. Garantir que o agente de enriquecimento seja chamado corretamente
3. Melhorar o formato dos documentos no Qdrant para facilitar a busca semântica
4. Implementar verificação de existência antes de inserir novos documentos

Estas mudanças devem ser implementadas no sistema de IA, especificamente no módulo `odoo_api/modules/business_rules/services.py`.
