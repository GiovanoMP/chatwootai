# Correções no Sistema de IA para Vetorização de Documentos

## Problema 1: Múltiplas Vetorizações

### Localização do problema:
No arquivo `odoo_api/modules/business_rules/services.py`, método `sync_support_documents_with_data`, o problema está na geração de UUIDs aleatórios para cada documento:

```python
# Gerar um ID único para o documento usando UUID
import uuid
document_id = str(uuid.uuid4())
```

### Solução:
Modificar o código para usar um ID determinístico baseado no account_id e no document_id do Odoo:

```python
# Usar um ID determinístico baseado no account_id e document_id
document_id = f"{account_id}_{doc_id}"
```

## Problema 2: Verificação de Existência

### Localização do problema:
No mesmo método `sync_support_documents_with_data`, não há verificação se o documento já existe no Qdrant antes de inserir um novo.

### Solução:
Adicionar verificação de existência antes de inserir:

```python
# Verificar se o documento já existe
existing_points = vector_service.qdrant_client.scroll(
    collection_name=collection_name,
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="account_id",
                match=models.MatchValue(value=account_id)
            ),
            models.FieldCondition(
                key="document_id",
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

## Problema 3: Formato dos Documentos no Qdrant

### Localização do problema:
O formato atual dos documentos no Qdrant não é o mais adequado para busca semântica com agentes de IA.

### Solução:
Modificar o formato para usar uma estrutura JSON mais estruturada:

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

## Problema 4: Enriquecimento de Documentos

### Localização do problema:
O agente de enriquecimento está sendo chamado corretamente, mas pode haver um problema na forma como os documentos são processados.

### Solução:
Verificar se o agente de enriquecimento está funcionando corretamente e se os dados estão sendo passados no formato esperado:

```python
# Importar o agente de enriquecimento
from odoo_api.embedding_agents.business_rules.support_docs_agent import get_support_document_agent

# Obter o agente de enriquecimento
support_doc_agent = await get_support_document_agent()

# Preparar os dados do documento
document_data = {
    "name": doc_name,
    "document_type": doc_type,
    "content": doc_content,
    "business_rule_id": business_rule_id
}

# Processar o documento com o agente
try:
    processed_text = await support_doc_agent.process_data(document_data, business_area)
    logger.info(f"Processed document {doc_id} using support document agent")
    
    # Verificar se o processamento foi bem-sucedido
    if not processed_text or processed_text == original_text:
        logger.warning(f"Document {doc_id} was not enriched by the agent")
except Exception as agent_error:
    logger.error(f"Failed to process document with agent: {agent_error}")
    # Usar o texto original como fallback
    processed_text = original_text
```

## Implementação Completa

Aqui está a implementação completa do método `sync_support_documents_with_data` com todas as correções:

```python
async def sync_support_documents_with_data(
    self,
    account_id: str,
    business_rule_id: int,
    documents: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Sincroniza documentos de suporte específicos com o sistema de IA.

    Args:
        account_id: ID da conta
        business_rule_id: ID da regra de negócio
        documents: Lista de documentos de suporte

    Returns:
        Resultado da sincronização
    """
    try:
        # Obter serviço de vetorização
        vector_service = await get_vector_service()
        collection_name = "support_documents"  # Coleção compartilhada para todos os tenants

        # Garantir que a coleção existe
        try:
            await vector_service.ensure_collection_exists(collection_name)
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            # Tentar criar a coleção diretamente
            try:
                vector_service.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
                )
                # Criar índice para account_id
                vector_service.qdrant_client.create_payload_index(
                    collection_name=collection_name,
                    field_name="account_id",
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
            except Exception as create_error:
                logger.error(f"Failed to create collection: {create_error}")
                raise

        # Obter o agente de enriquecimento
        from odoo_api.embedding_agents.business_rules.support_docs_agent import get_support_document_agent
        support_doc_agent = await get_support_document_agent()

        # Obter informações da área de negócio
        business_area = None
        try:
            # Obter conector Odoo
            odoo = await OdooConnectorFactory.create_connector(account_id)
            
            # Obter dados da regra de negócio
            business_rule_data = await odoo.execute_kw(
                'business.rules',
                'read',
                [business_rule_id],
                {'fields': ['business_area', 'business_area_other']}
            )
            
            if business_rule_data:
                business_area = business_rule_data[0].get('business_area')
                if business_area == 'other':
                    business_area = business_rule_data[0].get('business_area_other')
        except Exception as e:
            logger.error(f"Failed to get business area: {e}")
            # Continuar sem a área de negócio

        # Processar cada documento
        synced_docs = []
        for doc in documents:
            try:
                doc_id = doc.get('id')
                doc_name = doc.get('name')
                doc_type = doc.get('document_type', '')
                doc_content = doc.get('content', '')

                if not doc_id or not doc_name:
                    logger.warning(f"Skipping document with missing ID or name: {doc}")
                    continue

                # Preparar texto original
                original_text = f"""
Nome: {doc_name}
Tipo: {doc_type}
Conteúdo:
{doc_content}
"""

                # Preparar os dados do documento para o agente
                document_data = {
                    "name": doc_name,
                    "document_type": doc_type,
                    "content": doc_content,
                    "business_rule_id": business_rule_id
                }

                # Processar texto do documento usando o agente
                try:
                    processed_text = await support_doc_agent.process_data(document_data, business_area)
                    logger.info(f"Processed document {doc_id} using support document agent")
                    
                    # Verificar se o processamento foi bem-sucedido
                    if not processed_text or processed_text == original_text:
                        logger.warning(f"Document {doc_id} was not enriched by the agent")
                except Exception as agent_error:
                    logger.error(f"Failed to process document with agent: {agent_error}")
                    # Usar o texto original como fallback
                    processed_text = original_text

                # Verificar se o documento já existe
                existing_points = vector_service.qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="account_id",
                                match=models.MatchValue(value=account_id)
                            ),
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=str(doc_id))
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
                    logger.info(f"Document {doc_id} already exists in Qdrant with ID {document_id}")
                else:
                    # Usar um ID determinístico
                    document_id = f"{account_id}_{doc_id}"
                    logger.info(f"Creating new document in Qdrant with ID {document_id}")

                # Gerar embedding do texto processado
                try:
                    embedding = await vector_service.generate_embedding(processed_text)

                    # Armazenar no Qdrant
                    vector_service.qdrant_client.upsert(
                        collection_name=collection_name,
                        points=[
                            models.PointStruct(
                                id=document_id,
                                vector=embedding,
                                payload={
                                    "metadata": {
                                        "account_id": account_id,
                                        "business_rule_id": business_rule_id,
                                        "document_id": str(doc_id),
                                        "name": doc_name,
                                        "document_type": doc_type,
                                        "last_updated": datetime.now().isoformat(),
                                        "ai_processed": original_text != processed_text
                                    },
                                    "content": {
                                        "original": original_text,
                                        "processed": processed_text
                                    },
                                    # Compatibilidade com código existente
                                    "account_id": account_id,
                                    "business_rule_id": business_rule_id,
                                    "document_id": str(doc_id),
                                    "name": doc_name,
                                    "document_type": doc_type,
                                    "content": doc_content,
                                    "original_text": original_text,
                                    "processed_text": processed_text,
                                    "ai_processed": original_text != processed_text,
                                    "last_updated": datetime.now().isoformat()
                                }
                            )
                        ],
                    )
                    logger.info(f"Stored support document in Qdrant: {doc_name} (ID: {doc_id})")
                    synced_docs.append(str(doc_id))
                except Exception as e:
                    logger.error(f"Failed to generate embedding or store document in Qdrant: {e}")
                    # Continuar com o próximo documento

            except Exception as doc_error:
                logger.error(f"Error processing document: {doc_error}")
                # Continuar com o próximo documento

        logger.info(f"Synchronized {len(synced_docs)} support documents for account {account_id}")
        return {
            "success": True,
            "synced_docs": synced_docs,
            "total": len(synced_docs)
        }

    except Exception as e:
        logger.error(f"Failed to sync support documents: {e}")
        logger.exception("Detailed traceback:")
        return {
            "success": False,
            "error": str(e)
        }
```

## Notas Adicionais

1. A implementação mantém campos de compatibilidade com o código existente para evitar quebrar outras partes do sistema que possam depender desses campos.

2. Foram adicionados logs detalhados para facilitar a depuração.

3. O código agora verifica se o documento já existe no Qdrant antes de inserir um novo, e usa o mesmo ID se o documento já existir.

4. O formato dos documentos no Qdrant foi melhorado para facilitar a busca semântica.

5. O código agora verifica se o processamento pelo agente foi bem-sucedido e usa o texto original como fallback se necessário.

Estas correções devem resolver os problemas identificados na vetorização de documentos.
