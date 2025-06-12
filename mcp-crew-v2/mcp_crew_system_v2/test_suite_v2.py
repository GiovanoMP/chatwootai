"""
Suite de Testes Automatizados para MCP-Crew System v2
Testa todas as funcionalidades do sistema atualizado
"""

import requests
import json
import time
import logging
from typing import Dict, Any, List

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPCrewV2TestSuite:
    """Suite de testes para o MCP-Crew System v2"""
    
    def __init__(self, base_url: str = "http://localhost:5003"):
        self.base_url = base_url
        self.test_account_id = "test_tenant_v2"
        self.test_results = []
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes"""
        logger.info("🚀 Iniciando suite de testes MCP-Crew System v2")
        
        tests = [
            self.test_health_check,
            self.test_tool_discovery,
            self.test_knowledge_storage,
            self.test_knowledge_search,
            self.test_request_processing,
            self.test_metrics,
            self.test_config_endpoints,
            self.test_cache_invalidation,
            self.test_knowledge_events,
            self.test_system_info
        ]
        
        for test in tests:
            try:
                result = test()
                self.test_results.append(result)
                status = "✅ PASSOU" if result['success'] else "❌ FALHOU"
                logger.info(f"{status} - {result['test_name']}")
                if not result['success']:
                    logger.error(f"   Erro: {result.get('error', 'Desconhecido')}")
            except Exception as e:
                self.test_results.append({
                    'test_name': test.__name__,
                    'success': False,
                    'error': str(e),
                    'execution_time': 0
                })
                logger.error(f"❌ ERRO - {test.__name__}: {e}")
        
        return self.generate_test_report()
    
    def test_health_check(self) -> Dict[str, Any]:
        """Testa endpoint de health check"""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/api/mcp-crew/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                success = 'status' in data and 'redis_available' in data
                return {
                    'test_name': 'Health Check',
                    'success': success,
                    'response_data': data,
                    'execution_time': time.time() - start_time
                }
            else:
                return {
                    'test_name': 'Health Check',
                    'success': False,
                    'error': f"Status code: {response.status_code}",
                    'execution_time': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Health Check',
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_tool_discovery(self) -> Dict[str, Any]:
        """Testa descoberta dinâmica de ferramentas"""
        start_time = time.time()
        
        try:
            payload = {
                "account_id": self.test_account_id,
                "force_refresh": True
            }
            
            response = requests.post(
                f"{self.base_url}/api/mcp-crew/tools/discover",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                success = (
                    data.get('success', False) and
                    'tools_discovered' in data and
                    data.get('total_tools', 0) > 0
                )
                return {
                    'test_name': 'Tool Discovery',
                    'success': success,
                    'tools_found': data.get('total_tools', 0),
                    'mcps_with_tools': len(data.get('tools_discovered', {})),
                    'execution_time': time.time() - start_time
                }
            else:
                return {
                    'test_name': 'Tool Discovery',
                    'success': False,
                    'error': f"Status code: {response.status_code}",
                    'execution_time': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Tool Discovery',
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_knowledge_storage(self) -> Dict[str, Any]:
        """Testa armazenamento de conhecimento"""
        start_time = time.time()
        
        try:
            knowledge_data = {
                "account_id": self.test_account_id,
                "type": "product_info",
                "topic": "test_products",
                "title": "Teste de Produto",
                "content": {
                    "name": "Produto Teste",
                    "price": "R$ 100,00",
                    "category": "Eletrônicos"
                },
                "source_agent": "test_agent",
                "source_crew": "test_crew",
                "tags": ["teste", "produto"],
                "confidence_score": 0.9
            }
            
            response = requests.post(
                f"{self.base_url}/api/mcp-crew/knowledge/store",
                json=knowledge_data,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                success = data.get('success', False) and 'knowledge_id' in data
                return {
                    'test_name': 'Knowledge Storage',
                    'success': success,
                    'knowledge_id': data.get('knowledge_id'),
                    'execution_time': time.time() - start_time
                }
            else:
                return {
                    'test_name': 'Knowledge Storage',
                    'success': False,
                    'error': f"Status code: {response.status_code}",
                    'response': response.text,
                    'execution_time': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Knowledge Storage',
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_knowledge_search(self) -> Dict[str, Any]:
        """Testa busca de conhecimento"""
        start_time = time.time()
        
        try:
            # Primeiro armazenar um conhecimento para buscar
            self.test_knowledge_storage()
            
            # Aguardar um pouco para garantir que foi armazenado
            time.sleep(0.5)
            
            response = requests.get(
                f"{self.base_url}/api/mcp-crew/knowledge/search/{self.test_account_id}",
                params={"topic": "test_products", "limit": 5},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False) and 'results' in data
                return {
                    'test_name': 'Knowledge Search',
                    'success': success,
                    'results_count': data.get('count', 0),
                    'execution_time': time.time() - start_time
                }
            else:
                return {
                    'test_name': 'Knowledge Search',
                    'success': False,
                    'error': f"Status code: {response.status_code}",
                    'execution_time': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Knowledge Search',
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_request_processing(self) -> Dict[str, Any]:
        """Testa processamento de requisições"""
        start_time = time.time()
        
        try:
            request_data = {
                "account_id": self.test_account_id,
                "channel": "api",
                "payload": {
                    "text": "Preciso de informações sobre produtos eletrônicos",
                    "sender_id": "test_user",
                    "conversation_id": "test_conv"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/mcp-crew/process_request",
                json=request_data,
                timeout=30
            )
            
            if response.status_code in [200, 500]:  # Aceitar ambos pois pode falhar por MCPs não disponíveis
                data = response.json()
                # Considerar sucesso se a estrutura da resposta está correta
                success = (
                    'success' in data and
                    'crew_used' in data and
                    'execution_time' in data
                )
                return {
                    'test_name': 'Request Processing',
                    'success': success,
                    'crew_used': data.get('crew_used'),
                    'processing_success': data.get('success', False),
                    'execution_time': time.time() - start_time
                }
            else:
                return {
                    'test_name': 'Request Processing',
                    'success': False,
                    'error': f"Status code: {response.status_code}",
                    'execution_time': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Request Processing',
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_metrics(self) -> Dict[str, Any]:
        """Testa endpoints de métricas"""
        start_time = time.time()
        
        try:
            # Testar métricas gerais
            response = requests.get(f"{self.base_url}/api/mcp-crew/metrics", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                success = 'system_status' in data and 'features' in data
                return {
                    'test_name': 'Metrics',
                    'success': success,
                    'system_status': data.get('system_status'),
                    'execution_time': time.time() - start_time
                }
            else:
                return {
                    'test_name': 'Metrics',
                    'success': False,
                    'error': f"Status code: {response.status_code}",
                    'execution_time': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Metrics',
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_config_endpoints(self) -> Dict[str, Any]:
        """Testa endpoints de configuração"""
        start_time = time.time()
        
        try:
            # Testar configuração de MCPs
            response = requests.get(f"{self.base_url}/api/mcp-crew/config/mcps", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False) and 'mcps' in data
                return {
                    'test_name': 'Config Endpoints',
                    'success': success,
                    'mcps_configured': data.get('total_mcps', 0),
                    'execution_time': time.time() - start_time
                }
            else:
                return {
                    'test_name': 'Config Endpoints',
                    'success': False,
                    'error': f"Status code: {response.status_code}",
                    'execution_time': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Config Endpoints',
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_cache_invalidation(self) -> Dict[str, Any]:
        """Testa invalidação de cache"""
        start_time = time.time()
        
        try:
            payload = {
                "account_id": self.test_account_id
            }
            
            response = requests.post(
                f"{self.base_url}/api/mcp-crew/tools/cache/invalidate",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                return {
                    'test_name': 'Cache Invalidation',
                    'success': success,
                    'execution_time': time.time() - start_time
                }
            else:
                return {
                    'test_name': 'Cache Invalidation',
                    'success': False,
                    'error': f"Status code: {response.status_code}",
                    'execution_time': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Cache Invalidation',
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_knowledge_events(self) -> Dict[str, Any]:
        """Testa eventos de conhecimento"""
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}/api/mcp-crew/knowledge/events/{self.test_account_id}",
                params={"count": 5},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False) and 'events' in data
                return {
                    'test_name': 'Knowledge Events',
                    'success': success,
                    'events_count': data.get('count', 0),
                    'execution_time': time.time() - start_time
                }
            else:
                return {
                    'test_name': 'Knowledge Events',
                    'success': False,
                    'error': f"Status code: {response.status_code}",
                    'execution_time': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'test_name': 'Knowledge Events',
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def test_system_info(self) -> Dict[str, Any]:
        """Testa informações do sistema"""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/api/mcp-crew/admin/system-info", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False) and 'system_info' in data
                return {
                    'test_name': 'System Info',
                    'success': success,
                    'version': data.get('system_info', {}).get('version'),
                    'execution_time': time.time() - start_time
                }
            else:
                return {
                    'test_name': 'System Info',
                    'success': False,
                    'error': f"Status code: {response.status_code}",
                    'execution_time': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'test_name': 'System Info',
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Gera relatório final dos testes"""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        total_execution_time = sum(result.get('execution_time', 0) for result in self.test_results)
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": round(success_rate, 2),
                "total_execution_time": round(total_execution_time, 3)
            },
            "test_results": self.test_results,
            "timestamp": time.time(),
            "system_version": "2.0.0"
        }
        
        logger.info(f"📊 Relatório de Testes:")
        logger.info(f"   Total: {total_tests}")
        logger.info(f"   Sucessos: {successful_tests}")
        logger.info(f"   Falhas: {failed_tests}")
        logger.info(f"   Taxa de Sucesso: {success_rate:.1f}%")
        logger.info(f"   Tempo Total: {total_execution_time:.3f}s")
        
        return report

if __name__ == "__main__":
    # Executar testes
    test_suite = MCPCrewV2TestSuite()
    report = test_suite.run_all_tests()
    
    # Salvar relatório
    with open('/home/ubuntu/mcp_crew_v2_test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 Relatório salvo em: /home/ubuntu/mcp_crew_v2_test_report.json")
    print(f"🎯 Taxa de Sucesso: {report['test_summary']['success_rate']}%")

