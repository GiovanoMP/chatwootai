from odoo_api.services.vector_service import get_vector_service
import asyncio
from qdrant_client.http import models

async def main():
    vs = await get_vector_service()

    # Listar todas as coleções
    collections = vs.qdrant_client.get_collections()
    print(f"Coleções disponíveis: {[c.name for c in collections.collections]}")

    # Listar todos os pontos na coleção business_rules
    scroll_result = vs.qdrant_client.scroll(
        collection_name="business_rules",
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="account_id",
                    match=models.MatchValue(
                        value="account_1"
                    )
                )
            ]
        ),
        limit=10
    )

    if scroll_result and scroll_result.points:
        print(f"Encontrados {len(scroll_result.points)} pontos")
        for point in scroll_result.points:
            print(f"ID: {point.id}")
            print(f"Payload: {point.payload}")
            print("---")
    else:
        print('Nenhum resultado')

if __name__ == "__main__":
    asyncio.run(main())
