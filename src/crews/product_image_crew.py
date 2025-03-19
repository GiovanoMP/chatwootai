"""
Crew especializada em recuperação e geração de imagens de produtos.

Esta crew é responsável por automatizar a recuperação de imagens de produtos
para o Odoo, utilizando tanto o Google Custom Search API para imagens reais
quanto APIs de geração de imagens com IA como fallback.
"""

import logging
import os
import base64
import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

from crewai import Agent, Task
from dotenv import load_dotenv

from src.crews.functional_crew import FunctionalCrew
from src.core.domain import DomainManager
from src.plugins.plugin_manager import PluginManager
from src.api.erp.odoo.client import OdooClient

# Carregar variáveis de ambiente
load_dotenv()

logger = logging.getLogger(__name__)


class ProductImageCrew(FunctionalCrew):
    """
    Crew especializada em recuperação e geração de imagens de produtos.
    
    Esta crew é responsável por automatizar a recuperação de imagens de produtos
    para o Odoo, utilizando tanto o Google Custom Search API para imagens reais
    quanto APIs de geração de imagens com IA como fallback.
    """
    
    def __init__(self, **kwargs):
        """
        Inicializa a crew de imagens de produtos.
        
        Args:
            **kwargs: Argumentos adicionais para a classe base
        """
        # Inicializa os gerenciadores de domínio e plugins
        self.domain_manager = kwargs.pop('domain_manager', DomainManager())
        self.plugin_manager = kwargs.pop('plugin_manager', PluginManager(config={}))
        
        # Inicializa o cliente Odoo
        self.odoo_client = kwargs.pop('odoo_client', OdooClient())
        
        # Configurações para Google Custom Search API
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
        
        # Configurações para OpenAI API (fallback para geração de imagens)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Diretório para armazenar imagens temporárias
        self.temp_image_dir = Path(os.getenv("TEMP_IMAGE_DIR", "/tmp/product_images"))
        self.temp_image_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializa a classe base
        super().__init__(crew_type="product_image", **kwargs)
    
    def _create_agents(self) -> List[Agent]:
        """
        Cria os agentes necessários para a crew de imagens de produtos.
        
        Returns:
            List[Agent]: Lista de agentes
        """
        # Agente de busca de imagens
        image_search_agent = Agent(
            role="Especialista em Busca de Imagens",
            goal="Encontrar imagens de alta qualidade para produtos usando APIs de busca",
            backstory="""Você é um especialista em busca de imagens de produtos.
            Seu objetivo é encontrar imagens de alta qualidade e relevantes para produtos
            usando o Google Custom Search API e outras fontes de imagens.""",
            tools=[self.vector_tool, self.db_tool, self.cache_tool] + self.additional_tools,
            verbose=True
        )
        
        # Agente de geração de imagens (fallback)
        image_generation_agent = Agent(
            role="Especialista em Geração de Imagens",
            goal="Gerar imagens de produtos de alta qualidade usando IA quando imagens reais não estão disponíveis",
            backstory="""Você é especializado em gerar imagens de produtos usando
            tecnologias de IA como DALL-E. Seu objetivo é criar imagens realistas e
            atraentes quando imagens reais não estão disponíveis.""",
            tools=[self.vector_tool, self.cache_tool],
            verbose=True
        )
        
        # Agente de processamento de imagens
        image_processing_agent = Agent(
            role="Especialista em Processamento de Imagens",
            goal="Processar, otimizar e preparar imagens para uso no Odoo",
            backstory="""Você é especializado em processar e otimizar imagens para
            uso em sistemas de e-commerce. Seu objetivo é garantir que as imagens
            estejam no formato correto, com tamanho otimizado e qualidade adequada.""",
            tools=[self.vector_tool, self.db_tool, self.cache_tool],
            verbose=True
        )
        
        return [image_search_agent, image_generation_agent, image_processing_agent]
    
    def _create_tasks(self) -> List[Task]:
        """
        Cria as tarefas necessárias para a crew de imagens de produtos.
        
        Returns:
            List[Task]: Lista de tarefas
        """
        # Tarefa para buscar informações do produto
        get_product_info_task = Task(
            description="""
            Busque informações detalhadas sobre o produto no Odoo.
            
            Você precisa obter:
            - Nome completo do produto
            - Descrição
            - Categoria
            - Código de barras (se disponível)
            - Características específicas
            
            Estas informações serão usadas para criar consultas de busca precisas.
            """,
            expected_output="""
            {
                "product_id": "id_do_produto",
                "name": "Nome completo do produto",
                "description": "Descrição detalhada",
                "category": "Categoria do produto",
                "barcode": "Código de barras (se disponível)",
                "attributes": [
                    {"name": "Atributo1", "value": "Valor1"},
                    {"name": "Atributo2", "value": "Valor2"}
                ]
            }
            """,
            agent=self.agents[0]  # Image Search Agent
        )
        
        # Tarefa para buscar imagens usando Google Custom Search API
        search_images_task = Task(
            description="""
            Busque imagens do produto usando o Google Custom Search API.
            
            Use as informações do produto para criar consultas de busca eficazes.
            Priorize imagens de alta qualidade, relevantes e que mostrem claramente o produto.
            
            Retorne os URLs das melhores imagens encontradas.
            """,
            expected_output="""
            {
                "search_query": "Consulta usada para busca",
                "images": [
                    {
                        "url": "URL da imagem",
                        "title": "Título da imagem",
                        "source": "Fonte da imagem",
                        "relevance_score": 0.95
                    }
                ]
            }
            """,
            agent=self.agents[0]  # Image Search Agent
        )
        
        # Tarefa para gerar imagens com IA (fallback)
        generate_images_task = Task(
            description="""
            Gere imagens do produto usando IA quando imagens reais não estão disponíveis ou são insuficientes.
            
            Use as informações do produto para criar prompts detalhados para a API de geração de imagens.
            Priorize a criação de imagens realistas e profissionais.
            
            Retorne os dados das imagens geradas.
            """,
            expected_output="""
            {
                "prompt": "Prompt usado para geração",
                "images": [
                    {
                        "data": "Dados da imagem (base64)",
                        "format": "png"
                    }
                ]
            }
            """,
            agent=self.agents[1]  # Image Generation Agent
        )
        
        # Tarefa para processar e otimizar imagens
        process_images_task = Task(
            description="""
            Processe e otimize as imagens obtidas para uso no Odoo.
            
            Tarefas de processamento:
            - Redimensionar para tamanhos padrão
            - Otimizar qualidade e tamanho do arquivo
            - Converter para formatos adequados
            - Adicionar marca d'água se necessário
            
            Retorne os dados das imagens processadas.
            """,
            expected_output="""
            {
                "processed_images": [
                    {
                        "data": "Dados da imagem processada (base64)",
                        "format": "jpg",
                        "size": "800x800",
                        "file_size": "150KB"
                    }
                ]
            }
            """,
            agent=self.agents[2]  # Image Processing Agent
        )
        
        # Tarefa para atualizar o produto no Odoo
        update_product_task = Task(
            description="""
            Atualize o produto no Odoo com as imagens processadas.
            
            Tarefas:
            - Fazer upload das imagens para o Odoo
            - Associar as imagens ao produto correto
            - Definir a imagem principal e imagens secundárias
            - Verificar se a atualização foi bem-sucedida
            
            Retorne o status da atualização.
            """,
            expected_output="""
            {
                "product_id": "id_do_produto",
                "update_status": "success",
                "images_added": 3,
                "main_image_url": "URL da imagem principal no Odoo"
            }
            """,
            agent=self.agents[0]  # Image Search Agent
        )
        
        return [get_product_info_task, search_images_task, generate_images_task, 
                process_images_task, update_product_task]
    
    def _get_process_type(self) -> str:
        """
        Obtém o tipo de processamento da crew.
        
        Returns:
            str: Tipo de processamento
        """
        # Usa processamento sequencial para garantir que as tarefas sejam executadas na ordem correta
        return "sequential"
    
    def search_images_with_google(self, query: str, num_images: int = 5) -> List[Dict[str, Any]]:
        """
        Busca imagens usando a API Google Custom Search.
        
        Esta função implementa a mesma lógica usada pelo Odoo em sua funcionalidade nativa
        "Get Pictures from Google Images", que permite buscar imagens de produtos tanto pelo
        nome quanto pelo código de barras.
        
        Args:
            query: Consulta de busca (pode ser código de barras ou nome do produto)
            num_images: Número de imagens para retornar
            
        Returns:
            List[Dict[str, Any]]: Lista de informações de imagens
        """
        if not self.google_api_key or not self.google_search_engine_id:
            logger.error("Google API Key ou Search Engine ID não configurados")
            return []
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.google_api_key,
            "cx": self.google_search_engine_id,
            "q": query,
            "searchType": "image",
            "num": min(num_images, 10),  # API limita a 10 resultados por página
            "imgSize": "large",
            "safe": "active",
            "rights": "cc_publicdomain cc_attribute cc_sharealike cc_noncommercial cc_nonderived"  # Filtrar por licenças adequadas
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            results = response.json()
            
            images = []
            if "items" in results:
                for item in results["items"]:
                    images.append({
                        "url": item.get("link"),
                        "title": item.get("title"),
                        "source": item.get("displayLink"),
                        "thumbnail": item.get("image", {}).get("thumbnailLink")
                    })
            
            return images
        except Exception as e:
            logger.error(f"Erro ao buscar imagens com Google API: {e}")
            return []
    
    def generate_image_with_openai(self, prompt: str, size: str = "1024x1024") -> Optional[str]:
        """
        Gera uma imagem usando a API DALL-E da OpenAI.
        
        Args:
            prompt: Descrição textual para geração da imagem
            size: Tamanho da imagem (1024x1024, 512x512, ou 256x256)
            
        Returns:
            Optional[str]: URL da imagem gerada ou None em caso de falha
        """
        if not self.openai_api_key:
            logger.error("OpenAI API Key não configurada")
            return None
        
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if "data" in result and len(result["data"]) > 0:
                return result["data"][0].get("url")
            return None
        except Exception as e:
            logger.error(f"Erro ao gerar imagem com OpenAI: {e}")
            return None
    
    def download_image(self, url: str) -> Optional[bytes]:
        """
        Faz o download de uma imagem a partir de uma URL.
        
        Args:
            url: URL da imagem
            
        Returns:
            Optional[bytes]: Dados binários da imagem ou None em caso de falha
        """
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Erro ao fazer download da imagem: {e}")
            return None
    
    def update_product_image_in_odoo(self, product_id: str, image_data: bytes) -> bool:
        """
        Atualiza a imagem de um produto no Odoo.
        
        Args:
            product_id: ID do produto no Odoo
            image_data: Dados binários da imagem
            
        Returns:
            bool: True se a atualização foi bem-sucedida, False caso contrário
        """
        try:
            # Codifica a imagem em base64 para envio ao Odoo
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Atualiza o produto no Odoo
            result = self.odoo_client.update_product(
                product_id=product_id,
                data={"image_1920": image_base64}
            )
            
            return bool(result)
        except Exception as e:
            logger.error(f"Erro ao atualizar imagem no Odoo: {e}")
            return False
    
    def process_product(self, product_id: str, product_name: str, barcode: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa um produto para buscar e atualizar suas imagens.
        
        Este método orquestra todo o processo de busca, geração, processamento
        e atualização de imagens para um produto específico.
        
        Args:
            product_id: ID do produto no Odoo
            product_name: Nome do produto para busca
            barcode: Código de barras do produto (opcional, mas recomendado para resultados mais precisos)
            
        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        logger.info(f"Iniciando processamento de imagens para produto: {product_name}")
        
        # Se não temos o código de barras, tentamos obtê-lo do Odoo
        if not barcode:
            try:
                product_info = self.odoo_client.get_product(product_id)
                barcode = product_info.get("barcode")
                logger.info(f"Código de barras obtido do Odoo: {barcode}")
            except Exception as e:
                logger.warning(f"Não foi possível obter o código de barras do produto: {e}")
        
        # Etapa 1: Buscar imagens com Google Custom Search
        images = []
        
        # Primeiro tentamos buscar pelo código de barras (mais preciso)
        if barcode:
            logger.info(f"Buscando imagens pelo código de barras: {barcode}")
            images = self.search_images_with_google(barcode, num_images=5)
        
        # Se não encontrou imagens pelo código de barras, tenta pelo nome do produto
        if not images:
            logger.info(f"Buscando imagens pelo nome do produto: {product_name}")
            images = self.search_images_with_google(f"{product_name} produto real", num_images=5)
        
        # Se não encontrou imagens, tenta gerar com IA
        if not images:
            logger.info(f"Nenhuma imagem encontrada para {product_name}, tentando geração com IA")
            prompt = f"Fotografia profissional de produto real: {product_name}, fundo branco, iluminação de estúdio, alta resolução, fotografia comercial"
            image_url = self.generate_image_with_openai(prompt)
            
            if image_url:
                images = [{"url": image_url, "source": "OpenAI DALL-E", "is_ai_generated": True}]
        
        # Se ainda não temos imagens, retorna erro
        if not images:
            logger.error(f"Não foi possível obter imagens para o produto: {product_name}")
            return {
                "product_id": product_id,
                "product_name": product_name,
                "barcode": barcode,
                "status": "error",
                "message": "Não foi possível obter imagens para o produto"
            }
        
        # Etapa 2: Fazer download da primeira imagem encontrada
        image_data = self.download_image(images[0]["url"])
        if not image_data:
            return {
                "product_id": product_id,
                "product_name": product_name,
                "barcode": barcode,
                "status": "error",
                "message": "Falha ao fazer download da imagem"
            }
        
        # Etapa 3: Atualizar o produto no Odoo
        success = self.update_product_image_in_odoo(product_id, image_data)
        
        if success:
            return {
                "product_id": product_id,
                "product_name": product_name,
                "barcode": barcode,
                "status": "success",
                "image_source": images[0].get("source", "Unknown"),
                "is_ai_generated": images[0].get("is_ai_generated", False),
                "search_method": "barcode" if barcode and images else "product_name"
            }
        else:
            return {
                "product_id": product_id,
                "product_name": product_name,
                "barcode": barcode,
                "status": "error",
                "message": "Falha ao atualizar imagem no Odoo"
            }
    
    def process_products_batch(self, products: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Processa um lote de produtos para buscar e atualizar suas imagens.
        
        Args:
            products: Lista de dicionários com product_id, product_name e opcionalmente barcode
                Exemplo: [
                    {"product_id": "123", "product_name": "Creme Nívea", "barcode": "4005900107398"},
                    {"product_id": "456", "product_name": "Shampoo Pantene"}
                ]
            
        Returns:
            List[Dict[str, Any]]: Resultados do processamento para cada produto
        """
        results = []
        
        for product in products:
            product_id = product.get("product_id")
            product_name = product.get("product_name")
            barcode = product.get("barcode")
            
            if not product_id or not product_name:
                logger.warning("Produto sem ID ou nome, ignorando")
                continue
            
            result = self.process_product(product_id, product_name, barcode)
            results.append(result)
        
        return results
