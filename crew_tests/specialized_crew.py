"""
Implementação de uma crew especializada com agentes para cada coleção do Qdrant.

Esta implementação usa agentes especializados para cada coleção do Qdrant,
processamento paralelo e memória compartilhada para melhorar a precisão
e reduzir a latência das respostas.
"""

import os
import asyncio
import json
from typing import List, Dict, Any, Optional
from crewai import Agent, Task, Crew, Process
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI

# Importar o serviço de vetores existente
from odoo_api.services.vector_service import get_vector_service


class QdrantSearchTool:
    """
    Ferramenta para buscar informações no Qdrant.

    Esta ferramenta permite buscar informações em uma coleção específica do Qdrant
    para uma conta específica.
    """

    def __init__(self, collection_name: str, account_id: str = "account_1"):
        """
        Inicializa a ferramenta de busca no Qdrant.

        Args:
            collection_name: Nome da coleção no Qdrant
            account_id: ID da conta do cliente
        """
        self.collection_name = collection_name
        self.account_id = account_id
        self.vector_service = None

    async def initialize(self):
        """Inicializa o serviço de vetores."""
        if self.vector_service is None:
            self.vector_service = await get_vector_service()

    async def search(self, query: str, limit: int = 10, score_threshold: float = 0.35) -> List[Dict[str, Any]]:
        """
        Busca informações no Qdrant.

        Args:
            query: A consulta do usuário
            limit: Número máximo de resultados
            score_threshold: Limiar mínimo de similaridade

        Returns:
            Lista de resultados
        """
        await self.initialize()

        # Gerar embedding para a consulta
        query_embedding = await self.vector_service.generate_embedding(query)

        # Buscar documentos relevantes
        search_results = self.vector_service.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=self.account_id
                        )
                    )
                ]
            ),
            limit=limit,
            score_threshold=score_threshold
        )

        # Extrair informações relevantes
        results = []
        for hit in search_results:
            # Remover o embedding do payload para economizar espaço
            payload = {k: v for k, v in hit.payload.items() if k != "embedding"}

            results.append({
                "id": hit.id,
                "score": hit.score,
                "payload": payload
            })

        return results

    async def get_all(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recupera todos os documentos de uma coleção para uma conta.

        Args:
            limit: Número máximo de resultados

        Returns:
            Lista de resultados
        """
        await self.initialize()

        # Buscar todos os documentos da coleção para a conta
        scroll_results = self.vector_service.qdrant_client.scroll(
            collection_name=self.collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=self.account_id
                        )
                    )
                ]
            ),
            limit=limit
        )

        results = []
        if scroll_results and len(scroll_results) > 0 and scroll_results[0]:
            for point in scroll_results[0]:
                # Remover o embedding do payload para economizar espaço
                payload = {k: v for k, v in point.payload.items() if k != "embedding"}

                results.append({
                    "id": point.id,
                    "payload": payload
                })

        return results


class SpecializedCrew:
    """
    Crew especializada com agentes para cada coleção do Qdrant.
    """

    def __init__(self, account_id: str = "account_1"):
        """
        Inicializa a crew especializada.

        Args:
            account_id: ID da conta do cliente
        """
        self.account_id = account_id

        # Inicializar ferramentas de busca
        self.business_rules_tool = QdrantSearchTool("business_rules", account_id)
        self.company_metadata_tool = QdrantSearchTool("company_metadata", account_id)
        self.support_documents_tool = QdrantSearchTool("support_documents", account_id)

        # Inicializar agentes
        self.business_rules_agent = self._create_business_rules_agent()
        self.company_info_agent = self._create_company_info_agent()
        self.support_docs_agent = self._create_support_docs_agent()
        self.customer_service_agent = self._create_customer_service_agent()

        # Inicializar crew
        self.crew = None

    def _create_business_rules_agent(self) -> Agent:
        """
        Cria o agente especializado em regras de negócio.

        Returns:
            Agente especializado em regras de negócio
        """
        return Agent(
            role="Especialista em Regras de Negócio",
            goal="Encontrar regras de negócio relevantes para a consulta do cliente",
            backstory="""
            Você é um especialista em regras de negócio da empresa.
            Sua função é encontrar regras relevantes para a consulta do cliente.
            Você NUNCA inventa informações e sempre cita a fonte exata.
            """,
            verbose=True,
            allow_delegation=False,
            temperature=0.1  # Temperatura baixa para reduzir criatividade
        )

    def _create_company_info_agent(self) -> Agent:
        """
        Cria o agente especializado em informações da empresa.

        Returns:
            Agente especializado em informações da empresa
        """
        return Agent(
            role="Especialista em Informações da Empresa",
            goal="Fornecer informações precisas sobre a empresa",
            backstory="""
            Você é um especialista em informações sobre a empresa.
            Sua função é fornecer dados precisos sobre a empresa, como horários de funcionamento,
            políticas, etc. Você NUNCA inventa informações e sempre cita a fonte exata.
            """,
            verbose=True,
            allow_delegation=False,
            temperature=0.1
        )

    def _create_support_docs_agent(self) -> Agent:
        """
        Cria o agente especializado em documentos de suporte.

        Returns:
            Agente especializado em documentos de suporte
        """
        return Agent(
            role="Especialista em Documentos de Suporte",
            goal="Encontrar documentos de suporte relevantes para a consulta do cliente",
            backstory="""
            Você é um especialista em documentos de suporte.
            Sua função é encontrar documentos relevantes para a consulta do cliente.
            Você NUNCA inventa informações e sempre cita a fonte exata.
            """,
            verbose=True,
            allow_delegation=False,
            temperature=0.1
        )

    def _create_customer_service_agent(self) -> Agent:
        """
        Cria o agente de atendimento ao cliente.

        Returns:
            Agente de atendimento ao cliente
        """
        return Agent(
            role="Atendente de Suporte ao Cliente",
            goal="Fornecer respostas precisas e amigáveis aos clientes",
            backstory="""
            Você é um atendente de suporte ao cliente.
            Sua função é fornecer respostas precisas e amigáveis aos clientes,
            com base APENAS nas informações fornecidas pelos outros agentes.
            Você NUNCA inventa informações e sempre cita a fonte exata.
            """,
            verbose=True,
            allow_delegation=False,
            temperature=0.1
        )

    async def _search_business_rules(self, query: str) -> str:
        """
        Busca regras de negócio relevantes para a consulta.

        Args:
            query: A consulta do usuário

        Returns:
            Resultado da busca em formato JSON
        """
        # Buscar regras de negócio relevantes
        results = await self.business_rules_tool.search(query)

        # Formatar resultados
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result["id"],
                "texto": result["payload"].get("text", "Sem texto disponível"),
                "is_temporary": result["payload"].get("is_temporary", False),
                "priority": result["payload"].get("priority", 3),
                "score": result["score"]
            })

        # Ordenar por prioridade (menor número = maior prioridade) e depois por score (maior = melhor)
        formatted_results.sort(key=lambda x: (x.get("priority", 3), -x.get("score", 0)))

        # Converter para JSON
        return json.dumps(formatted_results, ensure_ascii=False)

    async def _search_company_metadata(self) -> str:
        """
        Busca metadados da empresa.

        Returns:
            Resultado da busca em formato JSON
        """
        # Buscar metadados da empresa
        results = await self.company_metadata_tool.get_all(limit=1)

        # Formatar resultados
        if results:
            result = results[0]
            formatted_result = {
                "id": result["id"],
                "company_name": result["payload"].get("company_name", "Sandra Cosméticos"),
                "greeting_message": result["payload"].get("greeting_message", "Olá, obrigada por entrar em contato com a Sandra Cosméticos! Como posso ajudar hoje?"),
                "text": result["payload"].get("text", "Comercializamos cosméticos online e presencialmente, nossos canais de venda são Instagram, Facebook, Mercado Livre e WhatsApp.")
            }
        else:
            # Valores padrão se não encontrar nada
            formatted_result = {
                "id": "default",
                "company_name": "Sandra Cosméticos",
                "greeting_message": "Olá, obrigada por entrar em contato com a Sandra Cosméticos! Como posso ajudar hoje?",
                "text": "Comercializamos cosméticos online e presencialmente, nossos canais de venda são Instagram, Facebook, Mercado Livre e WhatsApp."
            }

        # Converter para JSON
        return json.dumps(formatted_result, ensure_ascii=False)

    async def _search_support_documents(self, query: str) -> str:
        """
        Busca documentos de suporte relevantes para a consulta.

        Args:
            query: A consulta do usuário

        Returns:
            Resultado da busca em formato JSON
        """
        # Buscar documentos de suporte relevantes
        results = await self.support_documents_tool.search(query)

        # Formatar resultados
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result["id"],
                "title": result["payload"].get("title", ""),
                "text": result["payload"].get("text", ""),
                "score": result["score"]
            })

        # Ordenar por score (maior = melhor)
        formatted_results.sort(key=lambda x: -x.get("score", 0))

        # Converter para JSON
        return json.dumps(formatted_results, ensure_ascii=False)

    def _create_business_rules_task(self, query: str, business_rules_json: str) -> Task:
        """
        Cria a tarefa de análise de regras de negócio.

        Args:
            query: A consulta do usuário
            business_rules_json: Regras de negócio em formato JSON

        Returns:
            Tarefa de análise de regras de negócio
        """
        return Task(
            description=f"""
            Analise as seguintes regras de negócio e identifique as mais relevantes para a consulta: "{query}"

            REGRAS DE NEGÓCIO (formato JSON):
            {business_rules_json}

            INSTRUÇÕES IMPORTANTES:
            1. Analise cuidadosamente cada regra de negócio
            2. Priorize regras temporárias (is_temporary=true) quando a consulta for sobre promoções
            3. NÃO INVENTE informações que não estão nas regras
            4. Cite o ID de cada regra encontrada
            5. Indique seu nível de confiança para cada regra (Alta/Média/Baixa)

            Formato da resposta (JSON):
            {{
                "regras_relevantes": [
                    {{
                        "id": "ID da regra",
                        "texto": "Texto completo da regra",
                        "is_temporary": true/false,
                        "relevancia": "Por que esta regra é relevante para a consulta",
                        "confianca": "Alta/Média/Baixa"
                    }}
                ],
                "tem_informacao_suficiente": true/false,
                "explicacao": "Explicação sobre se as regras encontradas são suficientes para responder à consulta"
            }}
            """,
            agent=self.business_rules_agent,
            expected_output="JSON com regras de negócio relevantes"
        )

    def _create_company_info_task(self, query: str, company_metadata_json: str) -> Task:
        """
        Cria a tarefa de análise de informações da empresa.

        Args:
            query: A consulta do usuário
            company_metadata_json: Metadados da empresa em formato JSON

        Returns:
            Tarefa de análise de informações da empresa
        """
        return Task(
            description=f"""
            Analise as seguintes informações da empresa e identifique as mais relevantes para a consulta: "{query}"

            INFORMAÇÕES DA EMPRESA (formato JSON):
            {company_metadata_json}

            INSTRUÇÕES IMPORTANTES:
            1. Analise cuidadosamente as informações da empresa
            2. NÃO INVENTE informações que não estão nos dados
            3. Cite a fonte de cada informação encontrada
            4. Indique seu nível de confiança para cada informação (Alta/Média/Baixa)

            Formato da resposta (JSON):
            {{
                "informacoes_empresa": {{
                    "id": "ID da fonte",
                    "nome": "Nome da empresa",
                    "saudacao": "Saudação oficial",
                    "informacoes_relevantes": [
                        {{
                            "texto": "Informação relevante",
                            "relevancia": "Por que esta informação é relevante para a consulta",
                            "confianca": "Alta/Média/Baixa"
                        }}
                    ]
                }},
                "tem_informacao_suficiente": true/false,
                "explicacao": "Explicação sobre se as informações encontradas são suficientes para responder à consulta"
            }}
            """,
            agent=self.company_info_agent,
            expected_output="JSON com informações da empresa relevantes"
        )

    def _create_support_docs_task(self, query: str, support_documents_json: str) -> Task:
        """
        Cria a tarefa de análise de documentos de suporte.

        Args:
            query: A consulta do usuário
            support_documents_json: Documentos de suporte em formato JSON

        Returns:
            Tarefa de análise de documentos de suporte
        """
        return Task(
            description=f"""
            Analise os seguintes documentos de suporte e identifique os mais relevantes para a consulta: "{query}"

            DOCUMENTOS DE SUPORTE (formato JSON):
            {support_documents_json}

            INSTRUÇÕES IMPORTANTES:
            1. Analise cuidadosamente cada documento de suporte
            2. NÃO INVENTE informações que não estão nos documentos
            3. Cite o ID de cada documento encontrado
            4. Indique seu nível de confiança para cada documento (Alta/Média/Baixa)

            Formato da resposta (JSON):
            {{
                "documentos_relevantes": [
                    {{
                        "id": "ID do documento",
                        "titulo": "Título do documento",
                        "texto": "Texto relevante do documento",
                        "relevancia": "Por que este documento é relevante para a consulta",
                        "confianca": "Alta/Média/Baixa"
                    }}
                ],
                "tem_informacao_suficiente": true/false,
                "explicacao": "Explicação sobre se os documentos encontrados são suficientes para responder à consulta"
            }}
            """,
            agent=self.support_docs_agent,
            expected_output="JSON com documentos de suporte relevantes"
        )

    def _create_customer_service_task(self, query: str) -> Task:
        """
        Cria a tarefa de atendimento ao cliente.

        Args:
            query: A consulta do usuário

        Returns:
            Tarefa de atendimento ao cliente
        """
        return Task(
            description=f"""
            Gere uma resposta amigável e precisa para o cliente com base nas informações fornecidas pelos outros agentes.

            Consulta do cliente: "{query}"

            INSTRUÇÕES IMPORTANTES:
            1. Use APENAS as informações fornecidas pelos outros agentes
            2. NÃO INVENTE informações adicionais
            3. Use a saudação oficial da empresa
            4. Cite as fontes das informações (IDs das regras e documentos)
            5. Se não houver informação suficiente, seja honesto e diga que não tem essa informação
            6. Mantenha um tom amigável e prestativo

            Formato da resposta:

            SAUDAÇÃO: [Saudação oficial da empresa]

            RESPOSTA: [Sua resposta baseada apenas nas informações fornecidas]

            FONTES: [Lista de IDs das regras e documentos utilizados]

            CONFIANÇA: [Alta/Média/Baixa - Indique sua confiança na resposta]
            """,
            agent=self.customer_service_agent,
            expected_output="Resposta formatada para o cliente"
        )

    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Processa uma consulta do usuário.

        Args:
            query: A consulta do usuário

        Returns:
            Resultado do processamento
        """
        print(f"Processando consulta: '{query}'")

        # Buscar informações em paralelo
        business_rules_json, company_metadata_json, support_documents_json = await asyncio.gather(
            self._search_business_rules(query),
            self._search_company_metadata(),
            self._search_support_documents(query)
        )

        print("Informações recuperadas do Qdrant")

        # Criar tarefas
        business_rules_task = self._create_business_rules_task(query, business_rules_json)
        company_info_task = self._create_company_info_task(query, company_metadata_json)
        support_docs_task = self._create_support_docs_task(query, support_documents_json)
        customer_service_task = self._create_customer_service_task(query)

        # Configurar contexto das tarefas
        customer_service_task.context = [
            business_rules_task.output,
            company_info_task.output,
            support_docs_task.output
        ]

        # Criar crew
        self.crew = Crew(
            agents=[
                self.business_rules_agent,
                self.company_info_agent,
                self.support_docs_agent,
                self.customer_service_agent
            ],
            tasks=[
                business_rules_task,
                company_info_task,
                support_docs_task,
                customer_service_task
            ],
            verbose=True,
            memory=True  # Habilitar memória compartilhada
        )

        # Executar crew
        result = self.crew.kickoff()

        # Extrair partes da resposta formatada
        response_parts = {}
        try:
            lines = result.strip().split('\n')
            for line in lines:
                if line.startswith('SAUDAÇÃO:'):
                    response_parts['saudacao'] = line.replace('SAUDAÇÃO:', '').strip()
                elif line.startswith('RESPOSTA:'):
                    response_parts['resposta'] = line.replace('RESPOSTA:', '').strip()
                elif line.startswith('FONTES:'):
                    response_parts['fontes'] = line.replace('FONTES:', '').strip()
                elif line.startswith('CONFIANÇA:'):
                    response_parts['confianca'] = line.replace('CONFIANÇA:', '').strip()
        except Exception:
            # Se não conseguir extrair as partes, use a resposta completa
            response_parts = {'resposta_completa': result}

        return {
            "query": query,
            "response": result,
            "response_parts": response_parts,
            "account_id": self.account_id
        }
