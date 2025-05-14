"""
API para sincronização de documentos de suporte.
"""

import logging
import time
import traceback
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, status

from app.models.support_document import SupportDocumentSync, SupportDocumentResponse
from app.services.vector_service import VectorService
from app.services.embedding_service import EmbeddingService
from app.services.cache_service import CacheService
from app.services.enrichment_service import EnrichmentService
from app.core.auth import verify_api_key
from app.core.config import settings
from app.core.exceptions import VectorDBError, EmbeddingError
from app.core.dependencies import get_vector_service, get_embedding_service, get_cache_service, get_enrichment_service
from app.services.document_processor import DocumentProcessor

router = APIRouter(prefix="/api/v1/support-documents", tags=["support-documents"])

# Loggers específicos
logger = logging.getLogger(__name__)
sync_logger = logging.getLogger("vectorization.sync")
embedding_logger = logging.getLogger("vectorization.embedding")
critical_logger = logging.getLogger("vectorization.critical")

@router.post("/sync", response_model=SupportDocumentResponse)
async def sync_support_documents(
    data: SupportDocumentSync,
    vector_service: VectorService = Depends(get_vector_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    cache_service: CacheService = Depends(get_cache_service),
    enrichment_service: EnrichmentService = Depends(get_enrichment_service),
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Sincroniza documentos de suporte com o sistema de IA.
    """
    start_time = time.time()
    operation_id = f"sync_docs_{datetime.now().strftime('%Y%m%d%H%M%S')}_{data.account_id}"

    sync_logger.info(f"[{operation_id}] Iniciando sincronização de documentos de suporte para account_id={data.account_id}, business_rule_id={data.business_rule_id}")

    # Verificar API key
    verify_api_key(api_key)

    account_id = data.account_id
    business_rule_id = data.business_rule_id

    # Coleção global para documentos de suporte
    collection_name = "support_documents"

    # Contadores
    vectorized_documents = 0
    removed_documents = 0

    sync_logger.info(f"[{operation_id}] Documentos de suporte: {len(data.documents)}")

    try:
        # 1. Obter IDs de todos os documentos existentes no Qdrant para esta conta
        existing_doc_ids = await vector_service.get_all_rule_ids(
            collection_name=collection_name,
            account_id=account_id
        )

        # 2. Coletar IDs de todos os documentos recebidos na sincronização
        current_doc_ids = {f"document_{doc.id}" for doc in data.documents}

        # 3. Identificar documentos a serem removidos (existem no Qdrant mas não na sincronização atual)
        docs_to_remove = existing_doc_ids - current_doc_ids

        # 4. Remover documentos que não existem mais
        if docs_to_remove:
            await vector_service.delete_vectors(
                collection_name=collection_name,
                vector_ids=list(docs_to_remove)
            )
            removed_documents = len(docs_to_remove)
            logger.info(f"Removidos {removed_documents} documentos de suporte obsoletos da coleção {collection_name}")

        # 5. Processar documentos de suporte com chunking e enriquecimento
        for doc in data.documents:
            # Converter para dicionário para processamento
            doc_dict = {
                "id": doc.id,
                "name": doc.name,
                "document_type": doc.document_type,
                "content": doc.content,
                "last_updated": doc.last_updated
            }

            # Processar documento (chunking se necessário)
            if settings.ENABLE_DOCUMENT_CHUNKING:
                processed_chunks = DocumentProcessor.process_document(
                    document=doc_dict,
                    account_id=account_id,
                    business_rule_id=business_rule_id
                )

                sync_logger.info(f"[{operation_id}] Documento '{doc.name}' dividido em {len(processed_chunks)} chunks")
            else:
                # Modo legado sem chunking
                metadata = {
                    "id": doc.id,
                    "name": doc.name,
                    "document_type": doc.document_type,
                    "account_id": account_id,
                    "business_rule_id": business_rule_id,
                    "last_updated": doc.last_updated
                }

                doc_text = f"""
                Nome: {doc.name}
                Tipo: {doc.document_type}
                Conteúdo: {doc.content}
                """

                processed_chunks = [{
                    "metadata": metadata,
                    "content": doc.content,
                    "formatted_text": doc_text
                }]

            # Processar cada chunk
            for chunk in processed_chunks:
                # Enriquecer o texto se necessário (documentos pequenos ou importantes)
                if doc.document_type in ["faq", "policy", "terms"] and len(chunk["content"]) < 1000:
                    try:
                        # Enriquecer o conteúdo para melhorar a recuperação
                        enriched_data = await enrichment_service.enrich_document(
                            {
                                "content": chunk["content"],
                                "name": chunk["metadata"]["name"],
                                "document_type": chunk["metadata"]["document_type"]
                            },
                            account_id
                        )

                        if enriched_data.get("enriched_content"):
                            chunk["content"] = enriched_data["enriched_content"]
                            chunk["metadata"]["enriched"] = True

                            # Atualizar o texto formatado
                            chunk["formatted_text"] = DocumentProcessor.format_chunk_for_embedding(
                                chunk["content"],
                                chunk["metadata"]
                            )
                    except Exception as e:
                        # Falha no enriquecimento não deve interromper o processo
                        logger.warning(f"Falha ao enriquecer documento: {str(e)}")

                # Gerar embedding
                embedding = await embedding_service.generate_embedding(
                    text=chunk["formatted_text"],
                    max_tokens=settings.MAX_EMBEDDING_TOKENS
                )

                # Criar ID único para o chunk
                if chunk["metadata"].get("is_chunk"):
                    vector_id = f"document_{doc.id}_chunk_{chunk['metadata']['chunk_index']}"
                else:
                    vector_id = f"document_{doc.id}"

                # Armazenar no Qdrant
                await vector_service.store_vector(
                    collection_name=collection_name,
                    vector_id=vector_id,
                    vector=embedding,
                    payload=chunk["metadata"]
                )

                vectorized_documents += 1

        # 6. Invalidar cache no Redis
        await cache_service.invalidate_collection_cache(
            account_id=account_id,
            collection_type="support_documents"
        )

        # 7. Atualizar metadados de sincronização no Redis
        sync_metadata = {
            "last_sync": datetime.now().isoformat(),
            "document_count": vectorized_documents,
            "removed_count": removed_documents,
            "business_rule_id": business_rule_id
        }

        await vector_service.redis_service.set_json(
            key=f"sync:support_documents:{account_id}",
            value=sync_metadata,
            expiry=settings.REDIS_SYNC_METADATA_TTL
        )

        # Calcular tempo de execução
        execution_time = time.time() - start_time

        # Registrar conclusão da sincronização
        sync_logger.info(f"[{operation_id}] Sincronização concluída em {execution_time:.2f}s. Documentos vetorizados: {vectorized_documents}, Documentos removidos: {removed_documents}")

        return {
            "success": True,
            "data": {
                "vectorized_documents": vectorized_documents,
                "removed_documents": removed_documents,
                "collection": collection_name,
                "execution_time": f"{execution_time:.2f}s"
            },
            "message": f"Sincronizados {vectorized_documents} documentos de suporte, removidos {removed_documents} documentos obsoletos"
        }

    except (VectorDBError, EmbeddingError) as e:
        execution_time = time.time() - start_time
        error_message = f"Erro ao sincronizar documentos de suporte: {str(e)}"
        critical_logger.error(f"[{operation_id}] {error_message} (após {execution_time:.2f}s)")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        execution_time = time.time() - start_time
        error_message = f"Erro inesperado ao sincronizar documentos de suporte: {str(e)}"
        critical_logger.error(f"[{operation_id}] {error_message} (após {execution_time:.2f}s)")
        # Registrar traceback completo para depuração
        critical_logger.error(f"[{operation_id}] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Nota: O endpoint de metadados da empresa foi removido
# Os dados da empresa agora são enviados pelo MongoDB via outro módulo
