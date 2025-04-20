#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de teste para verificar a integração com o Qdrant usando dados reais do Odoo.

Este script permite:
1. Listar as coleções disponíveis no Qdrant
2. Consultar dados de uma coleção específica
3. Testar a atualização de dados vetorizados
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
ACCOUNT_ID = "account_1"  # ID da conta para teste

class QdrantTester:
    """Classe para testar a integração com o Qdrant."""

    def __init__(self, host: str = QDRANT_HOST, port: int = QDRANT_PORT):
        """Inicializa o testador com as configurações do Qdrant."""
        self.client = QdrantClient(host=host, port=port)
        logger.info(f"Conectado ao Qdrant em {host}:{port}")

    async def list_collections(self) -> List[str]:
        """Lista todas as coleções disponíveis no Qdrant."""
        collections = self.client.get_collections()
        collection_names = [c.name for c in collections.collections]
        logger.info(f"Coleções disponíveis: {collection_names}")
        return collection_names

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Obtém informações sobre uma coleção específica."""
        try:
            collection_info = self.client.get_collection(collection_name=collection_name)
            logger.info(f"Informações da coleção {collection_name}: {collection_info}")
            return collection_info.dict()
        except Exception as e:
            logger.error(f"Erro ao obter informações da coleção {collection_name}: {e}")
            return {"error": str(e)}

    async def query_points(
        self,
        collection_name: str,
        account_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Consulta pontos de uma coleção filtrados por account_id."""
        try:
            # Filtrar por account_id
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=account_id
                        )
                    )
                ]
            )

            # Buscar pontos no Qdrant
            points = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_condition,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )[0]

            if not points:
                logger.warning(f"Nenhum ponto encontrado na coleção {collection_name} para account_id {account_id}")
                return []

            # Extrair dados dos pontos
            result = []
            for point in points:
                result.append({
                    "id": point.id,
                    "payload": point.payload
                })

            logger.info(f"Encontrados {len(result)} pontos na coleção {collection_name} para account_id {account_id}")
            return result

        except Exception as e:
            logger.error(f"Erro ao consultar pontos da coleção {collection_name}: {e}")
            return []

    async def update_point(
        self,
        collection_name: str,
        point_id: str,
        new_payload: Dict[str, Any],
        account_id: str
    ) -> bool:
        """Atualiza um ponto específico na coleção."""
        try:
            # Verificar se o ponto existe e pertence ao account_id correto
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=account_id
                        )
                    )
                ]
            )

            # Buscar o ponto específico pelo ID
            try:
                point = self.client.retrieve(
                    collection_name=collection_name,
                    ids=[point_id],
                    with_payload=True,
                    with_vectors=True
                )[0]
                points = [point]
            except Exception as e:
                logger.error(f"Erro ao recuperar ponto {point_id}: {e}")
                return False

            if not points:
                logger.warning(f"Ponto {point_id} não encontrado ou não pertence ao account_id {account_id}")
                return False

            # Obter o vetor original
            original_vector = points[0].vector

            # Adicionar metadados de edição
            if "edit_history" not in new_payload:
                new_payload["edit_history"] = []

            new_payload["edit_history"].append({
                "editor": "test_script",
                "timestamp": datetime.now().isoformat(),
                "change_summary": "Teste de edição"
            })

            new_payload["last_updated"] = datetime.now().isoformat()
            new_payload["version"] = len(new_payload["edit_history"])

            # Atualizar o ponto mantendo o mesmo vetor
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=original_vector,
                        payload=new_payload
                    )
                ]
            )

            logger.info(f"Ponto {point_id} atualizado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao atualizar ponto {point_id}: {e}")
            return False

    async def simulate_edit_workflow(
        self,
        collection_name: str,
        account_id: str,
        edit_mode: str = "exact"
    ) -> Dict[str, Any]:
        """Simula o fluxo completo de edição de um ponto."""
        try:
            # 1. Buscar um ponto para editar
            points = await self.query_points(collection_name, account_id, limit=1)
            if not points:
                return {"success": False, "message": "Nenhum ponto encontrado para editar"}

            point = points[0]
            point_id = point["id"]
            payload = point["payload"]

            # 2. Simular edição do texto
            original_text = payload.get("processed_text", "")
            if not original_text:
                original_text = payload.get("original_text", "")

            edited_text = original_text + "\n\n[Este texto foi editado pelo script de teste]"

            # 3. Processar a edição conforme o modo
            if edit_mode == "exact":
                # Modo exato: usar o texto exatamente como editado
                processed_text = edited_text
            elif edit_mode == "assisted":
                # Modo assistido: simular sugestões
                processed_text = edited_text + "\n\n[Sugestões aplicadas pelo sistema]"
            elif edit_mode == "ai":
                # Modo IA: simular processamento completo
                processed_text = edited_text + "\n\n[Texto otimizado pelo sistema de IA]"
            else:
                processed_text = edited_text

            # 4. Atualizar o payload
            new_payload = payload.copy()
            new_payload["processed_text"] = processed_text
            new_payload["ai_processed"] = edit_mode != "exact"

            # 5. Atualizar o ponto
            success = await self.update_point(
                collection_name=collection_name,
                point_id=point_id,
                new_payload=new_payload,
                account_id=account_id
            )

            if success:
                return {
                    "success": True,
                    "message": "Edição simulada com sucesso",
                    "point_id": point_id,
                    "edit_mode": edit_mode,
                    "original_text": original_text,
                    "edited_text": processed_text
                }
            else:
                return {"success": False, "message": "Falha ao atualizar o ponto"}

        except Exception as e:
            logger.error(f"Erro ao simular fluxo de edição: {e}")
            return {"success": False, "error": str(e)}

async def main():
    """Função principal para executar os testes."""
    tester = QdrantTester()

    # Listar coleções
    collections = await tester.list_collections()

    if not collections:
        logger.error("Nenhuma coleção encontrada no Qdrant")
        return

    # Selecionar coleções relevantes para teste
    test_collections = [c for c in collections if c in [
        "company_metadata",
        "support_documents",
        "business_rules"
    ]]

    if not test_collections:
        logger.warning("Nenhuma coleção relevante encontrada para teste")
        logger.info("Coleções disponíveis: " + ", ".join(collections))
        return

    # Testar cada coleção
    for collection in test_collections:
        logger.info(f"\n{'='*50}\nTestando coleção: {collection}\n{'='*50}")

        # Obter informações da coleção
        collection_info = await tester.get_collection_info(collection)

        # Consultar pontos
        points = await tester.query_points(collection, ACCOUNT_ID)

        if points:
            # Mostrar detalhes do primeiro ponto
            logger.info(f"Detalhes do primeiro ponto:")
            logger.info(json.dumps(points[0], indent=2, ensure_ascii=False))

            # Simular edição
            logger.info(f"\nSimulando edição no modo 'exact':")
            edit_result = await tester.simulate_edit_workflow(collection, ACCOUNT_ID, "exact")
            logger.info(json.dumps(edit_result, indent=2, ensure_ascii=False))

    logger.info("\nTestes concluídos!")

if __name__ == "__main__":
    asyncio.run(main())
