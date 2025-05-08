import requests
import json

# Configuração
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "support_documents"
ACCOUNT_ID = "account_1"
DOCUMENT_ID = 24  # ID do documento problemático

# Método 1: Remover por ID específico
def delete_by_point_id():
    # Primeiro, precisamos obter o ID numérico do ponto no Qdrant
    # Sabemos que é 362084562 pelos logs, mas vamos confirmar
    response = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/scroll",
        json={
            "filter": {
                "must": [
                    {
                        "key": "account_id",
                        "match": {"value": ACCOUNT_ID}
                    },
                    {
                        "key": "document_id",
                        "match": {"value": str(DOCUMENT_ID)}
                    }
                ]
            },
            "limit": 10
        }
    )
    
    result = response.json()
    if 'result' in result and 'points' in result['result'] and len(result['result']['points']) > 0:
        point_id = result['result']['points'][0]['id']
        print(f"Encontrado ponto com ID: {point_id}")
        
        # Agora vamos deletar o ponto
        delete_response = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/delete",
            json={
                "points": [point_id],
                "wait": True
            }
        )
        
        print(f"Resposta da deleção: {delete_response.status_code}")
        print(json.dumps(delete_response.json(), indent=2))
    else:
        print("Ponto não encontrado")
        print(json.dumps(result, indent=2))

# Método 2: Remover todos os documentos para o account_id
def delete_all_for_account():
    response = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/delete",
        json={
            "filter": {
                "must": [
                    {
                        "key": "account_id",
                        "match": {"value": ACCOUNT_ID}
                    }
                ]
            },
            "wait": True
        }
    )
    
    print(f"Resposta da deleção: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    print("=== Método 1: Remover documento específico ===")
    delete_by_point_id()
    
    print("\n=== Método 2: Remover todos os documentos da conta ===")
    delete_all_for_account()
