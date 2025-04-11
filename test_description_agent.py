#!/usr/bin/env python
"""
Script para testar o agente de descrição de produtos.
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar o agente
from src.agents.product_description_agent import ProductDescriptionAgent

def main():
    """
    Função principal para testar o agente de descrição.
    """
    # Verificar API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return 1
    
    # Criar agente
    agent = ProductDescriptionAgent(api_key)
    
    # Exemplo de metadados de produto
    product_metadata = {
        "name": "Cadeira Ergonômica Deluxe",
        "category": "Móveis de Escritório",
        "attributes": [
            {"name": "Cor", "values": ["Preto", "Azul", "Cinza"]},
            {"name": "Material", "values": ["Couro Sintético", "Malha"]}
        ],
        "key_features": [
            "Suporte lombar ajustável",
            "Apoio de braço 3D",
            "Altura regulável",
            "Rodízios silenciosos"
        ],
        "use_cases": [
            "Escritórios corporativos",
            "Home office",
            "Estações de trabalho de longa duração"
        ],
        "tags": ["ergonômico", "conforto", "premium", "escritório"],
        "description": "Cadeira projetada para proporcionar máximo conforto durante longas horas de trabalho, com múltiplos ajustes e materiais de alta qualidade."
    }
    
    # Gerar descrição
    try:
        logger.info("Generating description...")
        description = agent.generate_description(product_metadata)
        
        print("\nDescrição Gerada:")
        print("-" * 50)
        print(description)
        print("-" * 50)
        print(f"Número de palavras: {len(description.split())}")
        
        # Salvar resultado em um arquivo
        with open("description_result.json", "w") as f:
            json.dump({
                "product_metadata": product_metadata,
                "generated_description": description,
                "word_count": len(description.split())
            }, f, indent=2)
        
        logger.info("Result saved to description_result.json")
        
        return 0
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
