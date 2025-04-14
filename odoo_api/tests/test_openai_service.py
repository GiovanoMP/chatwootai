"""
Testes para o serviço OpenAI.

Este módulo contém testes para verificar o funcionamento do serviço OpenAI,
incluindo geração de texto e embeddings.
"""

import asyncio
import os
import sys
import unittest
from typing import List

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odoo_api.services.openai_service import get_openai_service

class TestOpenAIService(unittest.TestCase):
    """Testes para o serviço OpenAI."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.loop = asyncio.get_event_loop()
    
    def test_generate_text(self):
        """Testar geração de texto."""
        async def _test():
            # Obter serviço OpenAI
            openai_service = await get_openai_service()
            
            # Testar geração de texto
            system_prompt = "Você é um assistente útil."
            user_prompt = "Qual é a capital do Brasil?"
            
            response = await openai_service.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=100,
                temperature=0.7
            )
            
            # Verificar se a resposta contém a palavra "Brasília"
            self.assertIn("Brasília", response)
        
        self.loop.run_until_complete(_test())
    
    def test_generate_embedding(self):
        """Testar geração de embedding."""
        async def _test():
            # Obter serviço OpenAI
            openai_service = await get_openai_service()
            
            # Testar geração de embedding
            text = "Este é um texto de teste para geração de embedding."
            
            embedding = await openai_service.generate_embedding(text)
            
            # Verificar se o embedding foi gerado corretamente
            self.assertIsInstance(embedding, list)
            self.assertTrue(len(embedding) > 0)
            self.assertIsInstance(embedding[0], float)
        
        self.loop.run_until_complete(_test())
    
    def test_embedding_similarity(self):
        """Testar similaridade entre embeddings."""
        async def _test():
            # Obter serviço OpenAI
            openai_service = await get_openai_service()
            
            # Gerar embeddings para textos similares
            text1 = "Qual é o horário de funcionamento da loja?"
            text2 = "A loja está aberta agora?"
            text3 = "Qual é a política de devolução?"
            
            embedding1 = await openai_service.generate_embedding(text1)
            embedding2 = await openai_service.generate_embedding(text2)
            embedding3 = await openai_service.generate_embedding(text3)
            
            # Calcular similaridade (produto escalar normalizado)
            def cosine_similarity(a: List[float], b: List[float]) -> float:
                dot_product = sum(x * y for x, y in zip(a, b))
                magnitude_a = sum(x * x for x in a) ** 0.5
                magnitude_b = sum(x * x for x in b) ** 0.5
                return dot_product / (magnitude_a * magnitude_b)
            
            sim_1_2 = cosine_similarity(embedding1, embedding2)
            sim_1_3 = cosine_similarity(embedding1, embedding3)
            
            # A similaridade entre text1 e text2 deve ser maior que entre text1 e text3
            self.assertGreater(sim_1_2, sim_1_3)
        
        self.loop.run_until_complete(_test())

if __name__ == "__main__":
    unittest.main()
