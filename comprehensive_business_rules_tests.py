#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testes abrangentes do módulo business_rules e sua integração com o sistema de IA.
Este script testa todas as funcionalidades principais do módulo.
"""

import asyncio
import logging
import sys
import json
import base64
import os
from datetime import datetime, timedelta
from pprint import pprint
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('business_rules_tests.log')
    ]
)
logger = logging.getLogger(__name__)

# Configurações
ACCOUNT_ID = "account_1"  # ID da conta Odoo
TEST_RESULTS = {}  # Armazenar resultados dos testes

# Constantes para formatação
HEADER = "\n" + "="*80 + "\n{}\n" + "="*80
SUBHEADER = "\n" + "-"*80 + "\n{}\n" + "-"*80
SEPARATOR = "\n" + "-"*80 + "\n"

class BusinessRulesTestSuite:
    """Suite de testes para o módulo business_rules."""

    def __init__(self, account_id: str):
        """Inicializa a suite de testes."""
        self.account_id = account_id
        self.service = None
        self.test_rule_id = None
        self.test_results = {}

    async def setup(self):
        """Configuração inicial para os testes."""
        try:
            # Configurar variáveis de ambiente necessárias
            os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "sk-your-api-key")

            # Importar módulos necessários
            import sys
            sys.path.append(os.path.abspath("."))

            from modules.business_rules.services import get_business_rules_service
            from modules.business_rules.schemas import (
                BusinessRuleRequest, RuleType, RulePriority
            )

            self.service = get_business_rules_service()
            self.BusinessRuleRequest = BusinessRuleRequest
            self.RuleType = RuleType
            self.RulePriority = RulePriority

            logger.info("Setup concluído com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro no setup: {e}")
            return False

    async def run_all_tests(self):
        """Executa todos os testes."""
        if not await self.setup():
            logger.error("Falha no setup. Abortando testes.")
            return False

        # Testes CRUD
        await self.test_crud_operations()

        # Testes de sincronização
        await self.test_sync_operations()

        # Testes de busca
        await self.test_search_operations()

        # Testes de suporte ao cliente
        await self.test_customer_support()

        # Exibir resumo
        self.print_summary()

        return True

    async def test_crud_operations(self):
        """Testa operações CRUD (Create, Read, Update, Delete)."""
        logger.info(HEADER.format("TESTES DE OPERAÇÕES CRUD"))

        # Teste: Criar regra
        logger.info(SUBHEADER.format("Teste: Criar Regra de Negócio"))
        create_result = await self.test_create_rule()
        self.test_results["create_rule"] = create_result

        if not create_result.get("success"):
            logger.error("Falha ao criar regra. Pulando testes dependentes.")
            return

        # Teste: Obter regra
        logger.info(SUBHEADER.format("Teste: Obter Regra de Negócio"))
        get_result = await self.test_get_rule()
        self.test_results["get_rule"] = get_result

        # Teste: Atualizar regra
        logger.info(SUBHEADER.format("Teste: Atualizar Regra de Negócio"))
        update_result = await self.test_update_rule()
        self.test_results["update_rule"] = update_result

        # Teste: Listar regras
        logger.info(SUBHEADER.format("Teste: Listar Regras de Negócio"))
        list_result = await self.test_list_rules()
        self.test_results["list_rules"] = list_result

        # Teste: Listar regras ativas
        logger.info(SUBHEADER.format("Teste: Listar Regras Ativas"))
        active_result = await self.test_list_active_rules()
        self.test_results["list_active_rules"] = active_result

        # Teste: Excluir regra
        logger.info(SUBHEADER.format("Teste: Excluir Regra de Negócio"))
        delete_result = await self.test_delete_rule()
        self.test_results["delete_rule"] = delete_result

    async def test_sync_operations(self):
        """Testa operações de sincronização."""
        logger.info(HEADER.format("TESTES DE SINCRONIZAÇÃO"))

        # Teste: Sincronizar regras
        logger.info(SUBHEADER.format("Teste: Sincronizar Regras de Negócio"))
        sync_result = await self.test_sync_rules()
        self.test_results["sync_rules"] = sync_result

    async def test_search_operations(self):
        """Testa operações de busca."""
        logger.info(HEADER.format("TESTES DE BUSCA SEMÂNTICA"))

        # Teste: Buscar regras
        logger.info(SUBHEADER.format("Teste: Buscar Regras de Negócio"))
        search_result = await self.test_search_rules()
        self.test_results["search_rules"] = search_result

    async def test_customer_support(self):
        """Testa funcionalidades de suporte ao cliente."""
        logger.info(HEADER.format("TESTES DE SUPORTE AO CLIENTE"))

        # Teste: Enviar mensagem de suporte
        logger.info(SUBHEADER.format("Teste: Enviar Mensagem de Suporte"))
        support_result = await self.test_send_support_message()
        self.test_results["send_support_message"] = support_result

        # Teste: Enviar arquivo de suporte
        logger.info(SUBHEADER.format("Teste: Enviar Arquivo de Suporte"))
        file_result = await self.test_send_support_file()
        self.test_results["send_support_file"] = file_result

    async def test_create_rule(self) -> Dict[str, Any]:
        """Testa a criação de uma regra de negócio."""
        try:
            # Criar regra de teste
            rule_data = self.BusinessRuleRequest(
                name="Regra de Teste - Horário de Funcionamento",
                description="Esta é uma regra de teste criada automaticamente para fins de teste.",
                type=self.RuleType.BUSINESS_HOURS,
                priority=self.RulePriority.MEDIUM,
                is_temporary=False,
                rule_data={
                    "days": [0, 1, 2, 3, 4],  # Segunda a sexta
                    "start_time": "09:00",
                    "end_time": "18:00"
                }
            )

            logger.info("Criando regra de negócio...")
            result = await self.service.create_business_rule(
                account_id=self.account_id,
                rule_data=rule_data
            )

            # Armazenar ID para testes subsequentes
            self.test_rule_id = result.id

            logger.info(f"Regra criada com sucesso. ID: {result.id}")
            return {
                "success": True,
                "rule_id": result.id,
                "details": f"Regra '{result.name}' criada com sucesso."
            }

        except Exception as e:
            logger.error(f"Erro ao criar regra: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_get_rule(self) -> Dict[str, Any]:
        """Testa a obtenção de uma regra de negócio."""
        if not self.test_rule_id:
            return {
                "success": False,
                "error": "Nenhuma regra de teste disponível."
            }

        try:
            logger.info(f"Obtendo regra de negócio (ID: {self.test_rule_id})...")
            result = await self.service.get_business_rule(
                account_id=self.account_id,
                rule_id=self.test_rule_id
            )

            logger.info(f"Regra obtida com sucesso: {result.name}")
            return {
                "success": True,
                "rule": {
                    "id": result.id,
                    "name": result.name,
                    "type": result.type
                },
                "details": f"Regra '{result.name}' obtida com sucesso."
            }

        except Exception as e:
            logger.error(f"Erro ao obter regra: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_update_rule(self) -> Dict[str, Any]:
        """Testa a atualização de uma regra de negócio."""
        if not self.test_rule_id:
            return {
                "success": False,
                "error": "Nenhuma regra de teste disponível."
            }

        try:
            # Obter regra atual
            current_rule = await self.service.get_business_rule(
                account_id=self.account_id,
                rule_id=self.test_rule_id
            )

            # Criar dados atualizados
            rule_data = self.BusinessRuleRequest(
                name=f"{current_rule.name} (Atualizada)",
                description=f"{current_rule.description} Esta regra foi atualizada em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.",
                type=current_rule.type,
                priority=current_rule.priority,
                is_temporary=current_rule.is_temporary,
                rule_data=current_rule.rule_data
            )

            logger.info(f"Atualizando regra de negócio (ID: {self.test_rule_id})...")
            result = await self.service.update_business_rule(
                account_id=self.account_id,
                rule_id=self.test_rule_id,
                rule_data=rule_data
            )

            logger.info(f"Regra atualizada com sucesso: {result.name}")
            return {
                "success": True,
                "rule": {
                    "id": result.id,
                    "name": result.name,
                    "type": result.type
                },
                "details": f"Regra '{result.name}' atualizada com sucesso."
            }

        except Exception as e:
            logger.error(f"Erro ao atualizar regra: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_list_rules(self) -> Dict[str, Any]:
        """Testa a listagem de regras de negócio."""
        try:
            logger.info("Listando regras de negócio...")
            result = await self.service.list_business_rules(
                account_id=self.account_id,
                limit=10,
                offset=0,
                include_temporary=True
            )

            logger.info(f"Regras listadas com sucesso. Total: {result.total}")

            # Exibir algumas regras
            for i, rule in enumerate(result.rules[:3]):
                logger.info(f"Regra {i+1}: {rule.name} (ID: {rule.id}, Tipo: {rule.type})")

            if len(result.rules) > 3:
                logger.info(f"... e mais {len(result.rules) - 3} regras.")

            return {
                "success": True,
                "total": result.total,
                "rules_count": len(result.rules),
                "details": f"Listadas {len(result.rules)} de {result.total} regras."
            }

        except Exception as e:
            logger.error(f"Erro ao listar regras: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_list_active_rules(self) -> Dict[str, Any]:
        """Testa a listagem de regras ativas."""
        try:
            logger.info("Listando regras ativas...")
            result = await self.service.list_active_rules(
                account_id=self.account_id
            )

            logger.info(f"Regras ativas listadas com sucesso. Total: {len(result)}")

            # Exibir algumas regras
            for i, rule in enumerate(result[:3]):
                logger.info(f"Regra {i+1}: {rule.name} (ID: {rule.id}, Tipo: {rule.type})")

            if len(result) > 3:
                logger.info(f"... e mais {len(result) - 3} regras.")

            return {
                "success": True,
                "total": len(result),
                "details": f"Listadas {len(result)} regras ativas."
            }

        except Exception as e:
            logger.error(f"Erro ao listar regras ativas: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_delete_rule(self) -> Dict[str, Any]:
        """Testa a exclusão de uma regra de negócio."""
        if not self.test_rule_id:
            return {
                "success": False,
                "error": "Nenhuma regra de teste disponível."
            }

        try:
            logger.info(f"Excluindo regra de negócio (ID: {self.test_rule_id})...")
            result = await self.service.delete_business_rule(
                account_id=self.account_id,
                rule_id=self.test_rule_id
            )

            logger.info(f"Regra excluída com sucesso.")
            return {
                "success": True,
                "details": f"Regra (ID: {self.test_rule_id}) excluída com sucesso."
            }

        except Exception as e:
            logger.error(f"Erro ao excluir regra: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_sync_rules(self) -> Dict[str, Any]:
        """Testa a sincronização de regras de negócio."""
        try:
            logger.info("Sincronizando regras de negócio...")
            result = await self.service.sync_business_rules(
                account_id=self.account_id
            )

            logger.info(f"Sincronização concluída. Status: {result.sync_status}")
            logger.info(f"Regras permanentes: {result.permanent_rules}")
            logger.info(f"Regras temporárias: {result.temporary_rules}")
            logger.info(f"Regras vetorizadas: {result.vectorized_rules}")

            return {
                "success": result.sync_status == "completed",
                "permanent_rules": result.permanent_rules,
                "temporary_rules": result.temporary_rules,
                "vectorized_rules": result.vectorized_rules,
                "details": f"Sincronização {result.sync_status}. {result.vectorized_rules} regras vetorizadas."
            }

        except Exception as e:
            logger.error(f"Erro ao sincronizar regras: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_search_rules(self) -> Dict[str, Any]:
        """Testa a busca semântica de regras de negócio."""
        try:
            # Consultas de teste
            queries = [
                "Qual é o horário de funcionamento?",
                "Como faço para devolver um produto?",
                "Quais são as políticas de entrega?",
                "Vocês oferecem garantia?"
            ]

            search_results = {}

            for query in queries:
                logger.info(f"Buscando regras para: '{query}'...")
                results = await self.service.search_business_rules(
                    account_id=self.account_id,
                    query=query,
                    limit=3,
                    score_threshold=0.6
                )

                logger.info(f"Resultados para '{query}': {len(results)} regras encontradas.")

                # Exibir resultados
                for i, result in enumerate(results[:2]):
                    logger.info(f"Resultado {i+1}:")
                    logger.info(f"  Nome: {result.get('payload', {}).get('name', 'N/A')}")
                    logger.info(f"  Score: {result.get('score', 'N/A')}")

                search_results[query] = {
                    "count": len(results),
                    "results": results[:2] if results else []
                }

            return {
                "success": True,
                "queries": len(queries),
                "results": search_results,
                "details": f"Busca realizada para {len(queries)} consultas."
            }

        except Exception as e:
            logger.error(f"Erro ao buscar regras: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_send_support_message(self) -> Dict[str, Any]:
        """Testa o envio de uma mensagem de suporte."""
        try:
            logger.info("Enviando mensagem de suporte...")
            result = await self.service.customer_support(
                account_id=self.account_id,
                message="Esta é uma mensagem de teste para o suporte ao cliente. Por favor, ignore.",
                file_content=None,
                file_name=None,
                file_type=None
            )

            logger.info(f"Mensagem enviada com sucesso. ID: {result.get('id')}")
            return {
                "success": True,
                "ticket_id": result.get('id'),
                "details": f"Mensagem enviada com sucesso. ID: {result.get('id')}"
            }

        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de suporte: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_send_support_file(self) -> Dict[str, Any]:
        """Testa o envio de um arquivo de suporte."""
        try:
            # Criar arquivo de teste
            test_file_content = """
            # Perguntas Frequentes

            ## Horário de Funcionamento

            **P1: Qual é o horário de funcionamento da loja?**
            R: Nossa loja está aberta de segunda a sexta, das 9h às 18h, e aos sábados das 9h às 13h.

            **P2: Vocês atendem aos domingos?**
            R: Não, nossa loja não funciona aos domingos e feriados.

            ## Entregas

            **P3: Qual o prazo de entrega?**
            R: O prazo de entrega varia de 3 a 5 dias úteis, dependendo da região.

            **P4: Vocês entregam em todo o Brasil?**
            R: Sim, realizamos entregas para todo o território nacional.
            """

            # Codificar em base64
            file_content_b64 = base64.b64encode(test_file_content.encode('utf-8')).decode('utf-8')

            logger.info("Enviando arquivo de suporte...")
            result = await self.service.customer_support(
                account_id=self.account_id,
                message="Segue arquivo com perguntas frequentes para processamento.",
                file_content=file_content_b64,
                file_name="faq_teste.txt",
                file_type="text/plain"
            )

            logger.info(f"Arquivo enviado com sucesso. ID: {result.get('id')}")
            return {
                "success": True,
                "ticket_id": result.get('id'),
                "details": f"Arquivo enviado com sucesso. ID: {result.get('id')}"
            }

        except Exception as e:
            logger.error(f"Erro ao enviar arquivo de suporte: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def print_summary(self):
        """Imprime um resumo dos resultados dos testes."""
        logger.info(HEADER.format("RESUMO DOS TESTES"))

        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result.get("success"))
        failed_tests = total_tests - successful_tests

        logger.info(f"Total de testes: {total_tests}")
        logger.info(f"Testes bem-sucedidos: {successful_tests}")
        logger.info(f"Testes com falha: {failed_tests}")
        logger.info(SEPARATOR)

        # Exibir resultados detalhados
        for test_name, result in self.test_results.items():
            status = "SUCESSO" if result.get("success") else "FALHA"
            details = result.get("details", "")
            error = result.get("error", "")

            logger.info(f"{test_name}: {status}")
            if details:
                logger.info(f"  Detalhes: {details}")
            if error:
                logger.info(f"  Erro: {error}")

        # Salvar resultados em arquivo JSON
        with open('business_rules_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)

        logger.info(SEPARATOR)
        logger.info(f"Resultados detalhados salvos em 'business_rules_test_results.json'")

async def main():
    """Função principal."""
    logger.info("Iniciando testes abrangentes do módulo business_rules...")

    # Criar e executar suite de testes
    test_suite = BusinessRulesTestSuite(ACCOUNT_ID)
    await test_suite.run_all_tests()

    logger.info("Testes concluídos.")

if __name__ == "__main__":
    asyncio.run(main())
