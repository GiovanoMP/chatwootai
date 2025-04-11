"""
Product Description Agent

Este módulo contém um agente especializado em gerar descrições comerciais concisas
para produtos, baseado nos metadados fornecidos.
"""

import openai
from typing import Dict, Any, List
import os
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductDescriptionAgent:
    """
    Agente especializado em gerar descrições comerciais concisas para produtos.
    """
    
    def __init__(self, api_key=None):
        """
        Inicializa o agente de descrição de produtos.
        
        Args:
            api_key: Chave de API do OpenAI (opcional, pode ser definida via variável de ambiente)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not provided. Agent will not function properly.")
        else:
            openai.api_key = self.api_key
    
    def generate_description(self, product_metadata: Dict[str, Any]) -> str:
        """
        Gera uma descrição comercial concisa a partir dos metadados do produto.
        
        Args:
            product_metadata: Dicionário com metadados do produto
            
        Returns:
            str: Descrição gerada
        """
        try:
            # Registrar início da geração
            logger.info(f"Generating description for product: {product_metadata.get('name', 'Unknown')}")
            
            # Construir prompt para o OpenAI
            prompt = self._build_prompt(product_metadata)
            
            # Gerar descrição usando OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um especialista em marketing e vendas, especializado em criar descrições concisas e persuasivas para produtos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            # Extrair e retornar a resposta
            description = response.choices[0].message.content.strip()
            
            # Registrar sucesso
            logger.info(f"Successfully generated description ({len(description.split())} words)")
            
            return description
            
        except Exception as e:
            logger.error(f"Error generating description: {str(e)}")
            raise
    
    def _build_prompt(self, product_metadata: Dict[str, Any]) -> str:
        """
        Constrói o prompt para o LLM com base nos metadados do produto.
        
        Args:
            product_metadata: Dicionário com metadados do produto
            
        Returns:
            str: Prompt formatado
        """
        prompt = f"""
        Crie uma descrição comercial concisa e atraente para o seguinte produto:
        
        Nome do Produto: {product_metadata.get('name', 'N/A')}
        Categoria: {product_metadata.get('category', 'N/A')}
        """
        
        # Adicionar atributos se disponíveis
        if 'attributes' in product_metadata and product_metadata['attributes']:
            prompt += "\nAtributos:\n"
            for attr in product_metadata['attributes']:
                attr_name = attr.get('name', 'N/A')
                attr_values = ", ".join(attr.get('values', []))
                prompt += f"- {attr_name}: {attr_values}\n"
        
        # Adicionar características principais se disponíveis
        if 'key_features' in product_metadata and product_metadata['key_features']:
            prompt += "\nCaracterísticas Principais:\n"
            features = self._ensure_list(product_metadata['key_features'])
            for feature in features:
                prompt += f"- {feature}\n"
        
        # Adicionar casos de uso se disponíveis
        if 'use_cases' in product_metadata and product_metadata['use_cases']:
            prompt += "\nCasos de Uso:\n"
            use_cases = self._ensure_list(product_metadata['use_cases'])
            for use_case in use_cases:
                prompt += f"- {use_case}\n"
        
        # Adicionar tags se disponíveis
        if 'tags' in product_metadata and product_metadata['tags']:
            tags = self._ensure_list(product_metadata['tags'])
            prompt += f"\nTags: {', '.join(tags)}\n"
        
        # Adicionar descrição técnica se disponível
        if 'description' in product_metadata and product_metadata['description']:
            prompt += f"\nDescrição Técnica:\n{product_metadata['description']}\n"
        
        # Adicionar instruções específicas
        prompt += """
        A descrição deve:
        1. Ser atraente e persuasiva
        2. Destacar apenas os principais benefícios e características
        3. Ter entre 50 e 100 palavras (muito importante)
        4. Usar linguagem comercial e direta
        
        Forneça apenas a descrição, sem introduções ou comentários adicionais.
        """
        
        return prompt
    
    def _ensure_list(self, value) -> List[str]:
        """
        Garante que o valor seja uma lista de strings.
        
        Args:
            value: Valor a ser convertido (pode ser string, lista ou None)
            
        Returns:
            List[str]: Lista de strings
        """
        if value is None:
            return []
        elif isinstance(value, str):
            # Se for uma string, dividir por linhas e limpar
            return [line.strip() for line in value.split('\n') if line.strip()]
        elif isinstance(value, list):
            # Se já for uma lista, garantir que todos os itens são strings
            return [str(item) for item in value]
        else:
            # Para outros tipos, converter para string e retornar como lista de um item
            return [str(value)]


# Exemplo de uso
if __name__ == "__main__":
    # Configurar API key
    api_key = os.environ.get("OPENAI_API_KEY")
    
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
        description = agent.generate_description(product_metadata)
        print("\nDescrição Gerada:")
        print("-" * 50)
        print(description)
        print("-" * 50)
        print(f"Número de palavras: {len(description.split())}")
    except Exception as e:
        print(f"Erro ao gerar descrição: {str(e)}")
