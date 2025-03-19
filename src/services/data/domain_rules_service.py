"""
DomainRulesService - Serviço para gerenciamento de regras de domínio de negócio.

Este serviço gerencia regras de negócio para diferentes domínios, como:
- Regras de produtos
- FAQs e documentação de suporte
- Regras de vendas e promoções
- Regras de agendamento
- Políticas de entrega

O serviço suporta carregamento de regras a partir de arquivos YAML
e também permite integração futura com um módulo Odoo para gerenciamento
das regras via interface administrativa.
"""

import logging
import json
import os
import yaml
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

from .base_data_service import BaseDataService

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomainRulesService(BaseDataService):
    """
    Serviço de dados especializado em gerenciamento de regras de domínio de negócio.
    
    Responsabilidades:
    - Carregar configurações YAML de domínios
    - Integrar com módulos Odoo para diferentes domínios (futuro)
    - Indexar regras de negócio no Qdrant para busca semântica
    - Fornecer API unificada para consulta de regras
    - Suportar plugins para operações específicas
    """
    
    def __init__(self, data_service_hub, config=None):
        """
        Inicializa o serviço de regras de domínio.
        
        Args:
            data_service_hub: Instância do DataServiceHub.
            config: Configuração opcional.
        """
        super().__init__(data_service_hub)
        self.config = config or {}
        self.domain_config = {}
        self.active_domain = None
        self.rule_cache = {}
        
        # Diretório de domínios (padrão: src/config/domains)
        self.domains_dir = self.config.get("domains_dir", os.path.join("src", "config", "domains"))
        
        # Inicializar sistema de plugins
        self.plugin_manager = self._initialize_plugin_manager()
        
        # Carregar domínios
        self._initialize_domains()
        
        logger.info("DomainRulesService inicializado")

    def get_entity_type(self) -> str:
        """
        Retorna o tipo de entidade gerenciada por este serviço.
        
        Returns:
            String representando o tipo de entidade.
        """
        return "business_rules"
    
    def _initialize_plugin_manager(self):
        """
        Inicializa o gerenciador de plugins se necessário.
        
        Returns:
            Instância do gerenciador de plugins.
        """
        # Verificar se já existe um plugin manager no hub
        if hasattr(self.hub, 'plugin_manager'):
            return self.hub.plugin_manager
        
        # Se não existir, importar e criar uma nova instância
        try:
            from ...plugins.plugin_manager import PluginManager
            config = self.config.get("plugin_config", {})
            return PluginManager(config)
        except ImportError:
            logger.warning("PluginManager não encontrado. O suporte a plugins está desativado.")
            return None
    
    def _initialize_domains(self):
        """
        Inicializa todos os domínios de negócio configurados.
        """
        # Verificar se o diretório de domínios existe
        if not os.path.exists(self.domains_dir):
            logger.warning(f"Diretório de domínios não encontrado: {self.domains_dir}")
            return
        
        # Carregar domínios a partir de arquivos YAML
        domain_files = [f for f in os.listdir(self.domains_dir) if f.endswith('.yaml') or f.endswith('.yml')]
        
        for domain_file in domain_files:
            domain_id = os.path.splitext(domain_file)[0]
            file_path = os.path.join(self.domains_dir, domain_file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    domain_config = yaml.safe_load(f)
                    
                if domain_config and isinstance(domain_config, dict):
                    self.domain_config[domain_id] = domain_config
                    logger.info(f"Domínio carregado: {domain_id}")
                else:
                    logger.warning(f"Arquivo de domínio inválido: {domain_file}")
            except Exception as e:
                logger.error(f"Erro ao carregar domínio {domain_id}: {str(e)}")
        
        # Definir domínio ativo (padrão: primeiro domínio encontrado)
        default_domain = self.config.get('default_domain')
        if default_domain and default_domain in self.domain_config:
            self.set_active_domain(default_domain)
        elif self.domain_config:
            self.set_active_domain(next(iter(self.domain_config)))
        
        logger.info(f"Domínios carregados: {list(self.domain_config.keys())}")
    
    def set_active_domain(self, domain_id: str) -> bool:
        """
        Define o domínio ativo para o sistema.
        
        Args:
            domain_id: ID do domínio a ser ativado.
            
        Returns:
            True se o domínio foi ativado, False caso contrário.
        """
        if domain_id not in self.domain_config:
            logger.error(f"Domínio não encontrado: {domain_id}")
            return False
        
        self.active_domain = domain_id
        
        # Atualizar cache
        self.rule_cache = {}
        
        # Ativar plugins específicos do domínio
        if self.plugin_manager:
            domain_plugins = self.domain_config[domain_id].get('plugins', [])
            for plugin_name in domain_plugins:
                self.plugin_manager.load_plugin(plugin_name)
        
        logger.info(f"Domínio ativo definido: {domain_id}")
        return True
    
    def get_active_domain(self) -> Optional[str]:
        """
        Retorna o ID do domínio ativo.
        
        Returns:
            ID do domínio ativo ou None se nenhum domínio estiver ativo.
        """
        return self.active_domain
    
    def get_domain_config(self, domain_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retorna a configuração completa de um domínio.
        
        Args:
            domain_id: ID do domínio ou None para o domínio ativo.
            
        Returns:
            Configuração do domínio ou dicionário vazio se não encontrado.
        """
        domain = domain_id or self.active_domain
        if not domain or domain not in self.domain_config:
            return {}
        
        return self.domain_config[domain]
    
    def get_business_rules(self, rule_type: Optional[str] = None, domain_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna regras de negócio para um tipo específico ou todos os tipos.
        
        Args:
            rule_type: Tipo de regra (ex: "product", "sales", "support") ou None para todos.
            domain_id: ID do domínio ou None para o domínio ativo.
            
        Returns:
            Lista de regras de negócio.
        """
        domain = domain_id or self.active_domain
        if not domain or domain not in self.domain_config:
            logger.error(f"Domínio não encontrado: {domain}")
            return []
        
        # Obter regras do YAML
        domain_data = self.domain_config[domain]
        all_rules = domain_data.get('business_rules', [])
        
        # Filtrar por tipo se necessário
        if rule_type:
            filtered_rules = [rule for rule in all_rules if rule.get('type') == rule_type]
            return filtered_rules
        
        return all_rules
    
    def query_rules(self, query: str, rule_type: Optional[str] = None, 
                    domain_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Consulta regras de negócio usando busca semântica.
        Atualmente implementa uma busca simplificada baseada em keywords.
        Após a integração com Qdrant, será implementada a busca vetorial.
        
        Args:
            query: Texto da consulta
            rule_type: Tipo de regra ou None para todos
            domain_id: ID do domínio ou None para o domínio ativo
            limit: Número máximo de resultados
            
        Returns:
            Lista de regras relevantes
        """
        # Obter todas as regras do tipo especificado
        rules = self.get_business_rules(rule_type, domain_id)
        
        if not rules:
            return []
        
        # Busca simples baseada em palavras-chave
        # Será substituída por busca vetorial quando Qdrant estiver integrado
        query_terms = query.lower().split()
        scored_rules = []
        
        for rule in rules:
            # Calcular score baseado na frequência dos termos da consulta
            score = 0
            rule_text = f"{rule.get('title', '')} {rule.get('content', '')}".lower()
            
            for term in query_terms:
                if term in rule_text:
                    # Termo encontrado no título tem peso maior
                    if term in rule.get('title', '').lower():
                        score += 2
                    else:
                        score += 1
            
            if score > 0:
                scored_rules.append((rule, score))
        
        # Ordenar por score (decrescente) e limitar resultados
        scored_rules.sort(key=lambda x: x[1], reverse=True)
        return [rule for rule, _ in scored_rules[:limit]]
    
    def get_support_faqs(self, domain_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna FAQs de suporte para o domínio específico.
        
        Args:
            domain_id: ID do domínio ou None para o domínio ativo.
            
        Returns:
            Lista de FAQs.
        """
        return self.get_business_rules("support", domain_id)
    
    def get_product_rules(self, domain_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna regras relacionadas a produtos para o domínio específico.
        
        Args:
            domain_id: ID do domínio ou None para o domínio ativo.
            
        Returns:
            Lista de regras de produtos.
        """
        return self.get_business_rules("product", domain_id)
    
    def get_sales_rules(self, domain_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna regras de vendas para o domínio específico.
        
        Args:
            domain_id: ID do domínio ou None para o domínio ativo.
            
        Returns:
            Lista de regras de vendas.
        """
        return self.get_business_rules("sales", domain_id)
    
    def execute_plugin(self, plugin_id: str, method: str, *args, **kwargs) -> Any:
        """
        Executa um método específico de um plugin.
        
        Args:
            plugin_id: ID do plugin
            method: Nome do método a ser executado
            args/kwargs: Argumentos para o método
            
        Returns:
            Resultado da execução do plugin ou None se não for possível executar
        """
        if not self.plugin_manager:
            logger.error("PluginManager não está disponível")
            return None
        
        # Definir domínio para o plugin
        domain = kwargs.pop('domain_id', self.active_domain)
        
        try:
            # Carregar o plugin se ainda não estiver carregado
            plugin = self.plugin_manager.get_plugin(plugin_id)
            if not plugin:
                plugin = self.plugin_manager.load_plugin(plugin_id)
                
            if not plugin:
                logger.error(f"Plugin não encontrado: {plugin_id}")
                return None
            
            # Verificar se o método existe
            if not hasattr(plugin, method):
                logger.error(f"Método não encontrado no plugin {plugin_id}: {method}")
                return None
            
            # Executar o método
            plugin_method = getattr(plugin, method)
            return plugin_method(*args, **kwargs)
        except Exception as e:
            logger.error(f"Erro ao executar plugin {plugin_id}.{method}: {str(e)}")
            return None
    
    def _prepare_for_qdrant_integration(self):
        """
        Prepara o serviço para futura integração com Qdrant.
        Esta é uma função de placeholder que será expandida quando
        a integração com Qdrant for implementada.
        """
        logger.info("Preparando serviço para integração com Qdrant (placeholder)")
        # TODO: Implementar esta função quando Qdrant estiver disponível

    def _prepare_for_odoo_integration(self):
        """
        Prepara o serviço para futura integração com módulo Odoo.
        Esta é uma função de placeholder que será expandida quando
        o módulo Odoo for desenvolvido.
        """
        logger.info("Preparando serviço para integração com Odoo (placeholder)")
        # TODO: Implementar esta função quando o módulo Odoo estiver disponível
