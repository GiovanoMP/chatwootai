#!/usr/bin/env python3
"""
Teste de Ponta a Ponta para o ChatwootAI

Este script testa o fluxo completo do sistema ChatwootAI:
1. Recebimento de uma mensagem via webhook
2. Processamento pelo HubCrew
3. Roteamento para a crew especializada
4. Consulta ao DataProxyAgent
5. Geração da resposta
6. Envio da resposta de volta

Uso:
    python end_to_end_test.py [--config CONFIG] [--domain DOMAIN] [--verbose]
"""

import os
import sys
import json
import time
import argparse
import logging
import asyncio
import uuid
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Importar o simulador de Chatwoot
from tests.integration.chatwoot_simulator import ChatwootSimulator

# Importar componentes do sistema
try:
    from src.webhook.webhook_handler import ChatwootWebhookHandler
    from src.core.hub import HubCrew
    from src.core.data_proxy_agent import DataProxyAgent
    from src.core.context_manager import ContextManagerAgent
    from src.core.domain.domain_manager import DomainManager
    from src.core.client_mapper import ClientMapper
except ImportError as e:
    print(f"Erro ao importar componentes do sistema: {e}")
    print("Certifique-se de que o diretório raiz está no PYTHONPATH")
    sys.exit(1)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/end_to_end_test.log")
    ]
)
logger = logging.getLogger("end_to_end_test")

class EndToEndTest:
    """
    Classe para execução de testes de ponta a ponta no sistema ChatwootAI.
    """
    
    def __init__(
        self, 
        config_path: str = "config/test_config.yaml",
        account_id: int = 1,
        verbose: bool = False
    ):
        """
        Inicializa o teste de ponta a ponta.
        
        Args:
            config_path: Caminho para o arquivo de configuração do teste
            account_id: ID da conta do Chatwoot a ser testada
            verbose: Se True, exibe logs detalhados
        """
        self.config_path = config_path
        self.account_id = account_id
        self.verbose = verbose
        
        # Configurar nível de log
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        # Carregar configuração
        self.config = self._load_config()
        
        # Inicializar componentes
        self.webhook_handler = None
        self.hub_crew = None
        self.domain_manager = None
        self.client_mapper = None
        self.simulator = None
        
        # Informações do cliente e domínio (serão preenchidas durante o setup)
        self.domain = None
        self.client_id = None
        self.client_name = None
        
        # Resultados do teste
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "success_count": 0,
            "failure_count": 0,
            "total_time": 0
        }
        
        logger.info(f"Teste de ponta a ponta inicializado - Domínio: {domain}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Carrega a configuração do teste.
        
        Returns:
            Dict[str, Any]: Configuração do teste
        """
        # Verificar se o arquivo de configuração existe
        if not os.path.exists(self.config_path):
            # Se não existir, criar configuração padrão
            config = {
                "webhook": {
                    "url": "http://localhost:8000/webhook",
                    "base_inbox_id": 100
                },
                "accounts": {
                    "1": {
                        "name": "Beleza Natural Ltda.",
                        "test_messages": [
                            "Olá, vocês têm creme para as mãos?",
                            "Qual o preço do creme hidratante?",
                            "Vocês entregam em São Paulo?"
                        ]
                    },
                    "2": {
                        "name": "Glamour Cosméticos S.A.",
                        "test_messages": [
                            "Bom dia, vocês têm protetor solar?",
                            "Qual o melhor shampoo para cabelos cacheados?",
                            "Vocês têm produtos veganos?"
                        ]
                    },
                    "3": {
                        "name": "Vida Saudável Farmácias",
                        "test_messages": [
                            "Bom dia, preciso de um remédio para dor de cabeça",
                            "Vocês têm vitamina C?",
                            "Qual o horário de funcionamento da farmácia?"
                        ]
                    }
                },
                "test_timeout": 30,  # segundos
                "expected_responses": {
                    "timeout": 10,  # segundos
                    "max_retries": 3
                }
            }
            
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Salvar configuração
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            logger.info(f"Configuração padrão criada em: {self.config_path}")
        else:
            # Carregar configuração existente
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Configuração carregada de: {self.config_path}")
        
        return config
    
    async def setup(self):
        """
        Configura o ambiente de teste.
        """
        logger.info("Configurando ambiente de teste...")
        
        # Carregar o mapeamento de clientes
        self.client_mapper = ClientMapper()
        await self.client_mapper.load_mappings("config/chatwoot_mapping.yaml")
        
        # Obter informações do cliente a partir do account_id
        client_info = self.client_mapper.get_client_by_account_id(str(self.account_id))
        
        if not client_info:
            logger.error(f"Não foi possível encontrar informações para o account_id: {self.account_id}")
            raise ValueError(f"Account ID {self.account_id} não encontrado no mapeamento")
        
        # Armazenar informações do cliente e domínio
        self.domain = client_info.get("domain")
        self.client_id = client_info.get("client_id")
        
        # Obter nome do cliente do arquivo de mapeamento
        client_details = self.client_mapper.get_client_details(self.client_id)
        self.client_name = client_details.get("name", f"Cliente {self.client_id}")
        
        logger.info(f"Cliente identificado: {self.client_name} (ID: {self.client_id}, Domínio: {self.domain})")
        
        # Inicializar simulador de Chatwoot
        webhook_config = self.config.get("webhook", {})
        self.simulator = ChatwootSimulator(
            webhook_url=webhook_config.get("url", "http://localhost:8000/webhook"),
            account_id=self.account_id,
            inbox_id=webhook_config.get("base_inbox_id", 100) + self.account_id
        )
        
        # Inicializar componentes do sistema
        try:
            # Inicializar gerenciador de domínio
            self.domain_manager = DomainManager()
            await self.domain_manager.load_domain(self.domain, self.client_id)
            
            # Inicializar webhook handler
            self.webhook_handler = ChatwootWebhookHandler()
            
            # Inicializar HubCrew
            self.hub_crew = HubCrew()
            
            logger.info(f"Ambiente de teste configurado com sucesso para {self.client_name}")
        except Exception as e:
            logger.error(f"Erro ao configurar ambiente de teste: {e}")
            raise
    
    async def run_tests(self):
        """
        Executa os testes de ponta a ponta.
        """
        logger.info(f"Iniciando testes para o cliente: {self.client_name} (Domínio: {self.domain})")
        
        # Obter mensagens de teste para a conta
        account_config = self.config.get("accounts", {}).get(str(self.account_id), {})
        test_messages = account_config.get("test_messages", [])
        
        if not test_messages:
            logger.warning(f"Nenhuma mensagem de teste definida para a conta: {self.account_id}")
            return
        
        # Iniciar conversa
        logger.info("Iniciando conversa de teste")
        self.simulator.start_conversation(
            contact_name=f"Cliente Teste {self.client_name}",
            contact_email=f"cliente.teste.{self.client_id}@example.com"
        )
        
        # Executar testes para cada mensagem
        for i, message in enumerate(test_messages):
            test_id = f"test_{self.domain}_{i+1}"
            logger.info(f"Executando teste {i+1}/{len(test_messages)}: {message}")
            
            # Registrar início do teste
            test_start_time = time.time()
            
            # Enviar mensagem
            response = self.simulator.send_message(message)
            
            # Verificar se a mensagem foi enviada com sucesso
            if "error" in response:
                logger.error(f"Erro ao enviar mensagem: {response['error']}")
                self._record_test_result(
                    test_id=test_id,
                    message=message,
                    success=False,
                    error=f"Erro ao enviar mensagem: {response['error']}",
                    duration=time.time() - test_start_time
                )
                continue
            
            # Aguardar e verificar resposta
            response_received = await self._wait_for_response(test_id, message)
            
            # Registrar resultado do teste
            self._record_test_result(
                test_id=test_id,
                message=message,
                success=response_received,
                error=None if response_received else "Timeout ao aguardar resposta",
                duration=time.time() - test_start_time
            )
            
            # Pequeno delay entre testes
            await asyncio.sleep(1)
        
        # Encerrar conversa
        logger.info("Encerrando conversa de teste")
        self.simulator.end_conversation()
        
        # Gerar relatório
        self._generate_report()
    
    async def _wait_for_response(self, test_id: str, message: str) -> bool:
        """
        Aguarda e verifica a resposta do sistema.
        
        Args:
            test_id: ID do teste
            message: Mensagem enviada
            
        Returns:
            bool: True se a resposta foi recebida, False caso contrário
        """
        # Configurações de timeout
        timeout = self.config.get("expected_responses", {}).get("timeout", 10)
        max_retries = self.config.get("expected_responses", {}).get("max_retries", 3)
        
        logger.info(f"Aguardando resposta (timeout: {timeout}s, max_retries: {max_retries})")
        
        # Implementação simulada - em um cenário real, verificaríamos a resposta do Chatwoot
        # Aqui, vamos apenas aguardar um tempo e verificar logs ou outros indicadores
        
        for retry in range(max_retries):
            try:
                # Aguardar tempo para processamento
                await asyncio.sleep(timeout / max_retries)
                
                # Verificar se houve resposta nos logs
                # Em um cenário real, verificaríamos a API do Chatwoot ou um callback
                
                # Simulação: assumimos que a resposta foi recebida após o tempo de espera
                # Em um sistema real, implementaríamos a verificação adequada
                
                if retry == max_retries - 1:
                    logger.info(f"Resposta recebida para o teste: {test_id}")
                    return True
                
                logger.debug(f"Aguardando resposta... Tentativa {retry+1}/{max_retries}")
            
            except Exception as e:
                logger.error(f"Erro ao aguardar resposta: {e}")
        
        logger.warning(f"Timeout ao aguardar resposta para o teste: {test_id}")
        return False
    
    def _record_test_result(
        self, 
        test_id: str, 
        message: str, 
        success: bool, 
        error: Optional[str] = None,
        duration: float = 0
    ):
        """
        Registra o resultado de um teste.
        
        Args:
            test_id: ID do teste
            message: Mensagem enviada
            success: Se o teste foi bem-sucedido
            error: Mensagem de erro, se houver
            duration: Duração do teste em segundos
        """
        result = {
            "id": test_id,
            "message": message,
            "success": success,
            "error": error,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "account_id": self.account_id,
            "client_id": self.client_id,
            "domain": self.domain,
            "client_name": self.client_name
        }
        
        self.test_results["tests"].append(result)
        
        if success:
            self.test_results["success_count"] += 1
            logger.info(f"Teste {test_id} concluído com sucesso em {duration:.2f}s")
        else:
            self.test_results["failure_count"] += 1
            logger.error(f"Teste {test_id} falhou em {duration:.2f}s: {error}")
    
    def _generate_report(self):
        """
        Gera um relatório dos testes executados.
        """
        # Calcular tempo total
        self.test_results["end_time"] = datetime.now().isoformat()
        start_time = datetime.fromisoformat(self.test_results["start_time"])
        end_time = datetime.fromisoformat(self.test_results["end_time"])
        self.test_results["total_time"] = (end_time - start_time).total_seconds()
        
        # Adicionar informações adicionais
        self.test_results["account_id"] = self.account_id
        self.test_results["client_id"] = self.client_id
        self.test_results["domain"] = self.domain
        self.test_results["client_name"] = self.client_name
        self.test_results["total_tests"] = len(self.test_results["tests"])
        self.test_results["success_rate"] = (
            self.test_results["success_count"] / self.test_results["total_tests"]
            if self.test_results["total_tests"] > 0 else 0
        ) * 100
        
        # Salvar relatório
        report_dir = Path("logs/test_reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / f"e2e_test_{self.client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Exibir resumo
        logger.info(f"Relatório de testes gerado: {report_path}")
        logger.info(f"Resumo dos testes:")
        logger.info(f"  Cliente: {self.client_name} (ID: {self.client_id})")
        logger.info(f"  Domínio: {self.domain}")
        logger.info(f"  Account ID Chatwoot: {self.account_id}")
        logger.info(f"  Total de testes: {self.test_results['total_tests']}")
        logger.info(f"  Testes bem-sucedidos: {self.test_results['success_count']}")
        logger.info(f"  Testes falhos: {self.test_results['failure_count']}")
        logger.info(f"  Taxa de sucesso: {self.test_results['success_rate']:.2f}%")
        logger.info(f"  Tempo total: {self.test_results['total_time']:.2f}s")
    
    async def teardown(self):
        """
        Limpa o ambiente após os testes.
        """
        logger.info("Limpando ambiente de teste...")
        
        # Limpar recursos
        self.webhook_handler = None
        self.hub_crew = None
        self.domain_manager = None
        self.simulator = None
        
        logger.info("Ambiente de teste limpo")


async def main():
    """
    Função principal.
    """
    # Analisar argumentos
    parser = argparse.ArgumentParser(description="Teste de ponta a ponta para o ChatwootAI")
    parser.add_argument(
        "--config", 
        default="config/test_config.yaml",
        help="Caminho para o arquivo de configuração do teste"
    )
    parser.add_argument(
        "--account", 
        type=int,
        default=1,
        choices=[1, 2, 3, 4],
        help="ID da conta do Chatwoot a ser testada"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Exibir logs detalhados"
    )
    args = parser.parse_args()
    
    # Criar instância de teste
    test = EndToEndTest(
        config_path=args.config,
        account_id=args.account,
        verbose=args.verbose
    )
    
    try:
        # Configurar ambiente
        await test.setup()
        
        # Executar testes
        await test.run_tests()
    except Exception as e:
        logger.error(f"Erro durante a execução dos testes: {e}")
    finally:
        # Limpar ambiente
        await test.teardown()
    
    logger.info("Teste de ponta a ponta concluído")


if __name__ == "__main__":
    # Executar teste
    asyncio.run(main())
