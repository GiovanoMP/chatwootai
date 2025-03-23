#!/usr/bin/env python3
"""
Script de migração para a nova arquitetura do Chatwoot V4.

Este script facilita a transição dos componentes antigos para os novos,
permitindo uma migração gradual e segura para a nova arquitetura.

Funcionalidades:
1. Migração de configurações de domínio para o novo formato
2. Verificação de compatibilidade de ferramentas
3. Adaptação de agentes existentes para usar o novo DataProxyAgent

Uso:
    python scripts/migrate_to_new_architecture.py --migrate-domain cosmetics
    python scripts/migrate_to_new_architecture.py --check-compatibility
    python scripts/migrate_to_new_architecture.py --adapt-agent sales
"""
import os
import sys
import argparse
import logging
import yaml
import shutil
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

# Adiciona o diretório raiz ao PYTHONPATH para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.domain.domain_loader import DomainLoader as OldDomainLoader
from src.core.domain.domain_loader_new import DomainLoader as NewDomainLoader
from src.core.domain.domain_manager import DomainManager as OldDomainManager
from src.core.domain.domain_manager_new import DomainManager as NewDomainManager
from src.core.tools.tool_registry import ToolRegistry

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("migration")


class MigrationHelper:
    """
    Classe auxiliar para migração da arquitetura antiga para a nova.
    
    Fornece métodos para migrar configurações de domínio, verificar compatibilidade
    e adaptar agentes existentes para a nova arquitetura.
    """
    
    def __init__(self, config_dir: str = None):
        """
        Inicializa o assistente de migração.
        
        Args:
            config_dir: Diretório de configurações. Se não for fornecido,
                        será usado o padrão "config/domains".
        """
        self.config_dir = config_dir or os.path.join("config", "domains")
        self.old_domain_loader = OldDomainLoader(config_dir=self.config_dir)
        self.new_domain_loader = NewDomainLoader(config_dir=self.config_dir)
        self.old_domain_manager = OldDomainManager(config_dir=self.config_dir)
        self.new_domain_manager = NewDomainManager(config_dir=self.config_dir)
        self.tool_registry = ToolRegistry()
        
        # Cria o diretório de backup se não existir
        self.backup_dir = os.path.join("backup", f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        logger.info(f"Assistente de migração inicializado. Diretório de configurações: {self.config_dir}")
        logger.info(f"Diretório de backup: {self.backup_dir}")
    
    def backup_file(self, file_path: str) -> str:
        """
        Faz backup de um arquivo antes de modificá-lo.
        
        Args:
            file_path: Caminho do arquivo a ser copiado
            
        Returns:
            str: Caminho do arquivo de backup
        """
        if not os.path.exists(file_path):
            logger.warning(f"Arquivo não encontrado para backup: {file_path}")
            return None
            
        # Cria o diretório de destino se necessário
        relative_path = os.path.relpath(file_path, os.path.dirname(os.path.dirname(__file__)))
        backup_path = os.path.join(self.backup_dir, relative_path)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Copia o arquivo
        shutil.copy2(file_path, backup_path)
        logger.info(f"Backup criado: {file_path} -> {backup_path}")
        
        return backup_path
    
    def migrate_domain_config(self, domain_name: str) -> bool:
        """
        Migra a configuração de um domínio para o novo formato.
        
        Args:
            domain_name: Nome do domínio a ser migrado
            
        Returns:
            bool: True se a migração foi bem-sucedida, False caso contrário
        """
        try:
            logger.info(f"Iniciando migração do domínio: {domain_name}")
            
            # Carrega a configuração antiga
            old_config = self.old_domain_loader.load_domain(domain_name)
            if not old_config:
                logger.error(f"Domínio não encontrado: {domain_name}")
                return False
                
            # Faz backup da configuração atual
            config_file = os.path.join(self.config_dir, domain_name, "config.yaml")
            self.backup_file(config_file)
            
            # Converte para o novo formato
            new_config = self._convert_domain_config(old_config)
            
            # Valida a nova configuração
            try:
                self.new_domain_loader.validate_configuration(new_config)
            except Exception as e:
                logger.error(f"Configuração inválida após conversão: {str(e)}")
                return False
                
            # Salva a nova configuração
            output_file = os.path.join(self.config_dir, domain_name, "config_new.yaml")
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(new_config, f, sort_keys=False, default_flow_style=False)
                
            logger.info(f"Migração concluída. Nova configuração salva em: {output_file}")
            logger.info(f"Para aplicar a migração, renomeie {output_file} para {config_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao migrar domínio {domain_name}: {str(e)}")
            return False
    
    def _convert_domain_config(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte uma configuração de domínio do formato antigo para o novo.
        
        Args:
            old_config: Configuração no formato antigo
            
        Returns:
            Dict[str, Any]: Configuração no novo formato
        """
        # Cria a estrutura básica da nova configuração
        new_config = {
            "version": "2.1",  # Nova versão do formato
            "name": old_config.get("name", "unknown"),
            "description": old_config.get("description", ""),
        }
        
        # Adiciona herança se presente
        if "inherit" in old_config:
            new_config["inherit"] = old_config["inherit"]
            
        # Converte configurações de ferramentas
        if "tools" in old_config:
            new_config["tools"] = {
                "enabled": old_config["tools"].get("enabled", []),
                "disabled": old_config["tools"].get("disabled", []),
                "configurations": {}
            }
            
            # Migra as configurações específicas de ferramentas
            if "configurations" in old_config["tools"]:
                for tool_id, tool_config in old_config["tools"]["configurations"].items():
                    # Adapta para o novo formato de configuração de ferramentas
                    new_config["tools"]["configurations"][tool_id] = {
                        "type": tool_config.get("type", tool_id),
                        "class": tool_config.get("class", f"src.tools.{tool_id}.{tool_id.capitalize()}Tool"),
                        "config": tool_config.get("parameters", {})
                    }
        
        # Converte configurações de agentes
        if "agents" in old_config:
            new_config["agents"] = {}
            for agent_id, agent_config in old_config["agents"].items():
                new_config["agents"][agent_id] = {
                    "role": agent_config.get("role", f"{agent_id.capitalize()} Agent"),
                    "goal": agent_config.get("goal", ""),
                    "backstory": agent_config.get("backstory", ""),
                    "tools": agent_config.get("tools", []),
                    "memory_settings": agent_config.get("memory_settings", {}),
                }
        
        # Converte configurações de crews
        if "crews" in old_config:
            new_config["crews"] = {}
            for crew_id, crew_config in old_config["crews"].items():
                new_config["crews"][crew_id] = {
                    "description": crew_config.get("description", ""),
                    "agents": [],
                    "tasks": crew_config.get("tasks", []),
                }
                
                # Adiciona agentes à crew
                if "agents" in crew_config:
                    for agent in crew_config["agents"]:
                        if isinstance(agent, str):
                            new_config["crews"][crew_id]["agents"].append({"type": agent})
                        else:
                            new_config["crews"][crew_id]["agents"].append(agent)
        
        # Adiciona outras configurações
        if "settings" in old_config:
            new_config["settings"] = old_config["settings"]
            
        return new_config
    
    def check_tool_compatibility(self) -> Dict[str, Any]:
        """
        Verifica a compatibilidade das ferramentas com o novo ToolRegistry.
        
        Returns:
            Dict[str, Any]: Relatório de compatibilidade
        """
        try:
            logger.info("Verificando compatibilidade de ferramentas...")
            
            # Obtém todos os domínios
            domain_dirs = [d for d in os.listdir(self.config_dir) 
                          if os.path.isdir(os.path.join(self.config_dir, d)) and not d.startswith('.')]
            
            report = {
                "domains_checked": len(domain_dirs),
                "tools_found": 0,
                "compatible_tools": 0,
                "incompatible_tools": 0,
                "issues": []
            }
            
            # Analisa cada domínio
            for domain in domain_dirs:
                logger.info(f"Verificando ferramentas no domínio: {domain}")
                
                # Carrega a configuração do domínio
                config_file = os.path.join(self.config_dir, domain, "config.yaml")
                if not os.path.exists(config_file):
                    continue
                    
                with open(config_file, 'r', encoding='utf-8') as f:
                    try:
                        config = yaml.safe_load(f)
                    except Exception as e:
                        report["issues"].append({
                            "domain": domain,
                            "file": config_file,
                            "error": f"Erro ao carregar YAML: {str(e)}"
                        })
                        continue
                
                # Verifica as ferramentas
                if "tools" in config and "configurations" in config["tools"]:
                    for tool_id, tool_config in config["tools"]["configurations"].items():
                        report["tools_found"] += 1
                        
                        # Verifica se a configuração é compatível com o novo formato
                        issues = []
                        
                        if "type" not in tool_config:
                            issues.append("Falta o campo 'type'")
                        
                        if "class" not in tool_config:
                            issues.append("Falta o campo 'class'")
                        
                        if not issues:
                            # Verifica se a classe pode ser carregada
                            try:
                                # Apenas verifica o formato, não tenta carregar de fato
                                class_path = tool_config["class"]
                                module_parts = class_path.split('.')
                                if len(module_parts) < 2:
                                    issues.append("Formato de classe inválido, deve ser 'module.ClassName'")
                            except Exception as e:
                                issues.append(f"Erro ao analisar classe: {str(e)}")
                        
                        if issues:
                            report["incompatible_tools"] += 1
                            report["issues"].append({
                                "domain": domain,
                                "tool_id": tool_id,
                                "issues": issues
                            })
                        else:
                            report["compatible_tools"] += 1
            
            # Calcula a taxa de compatibilidade
            if report["tools_found"] > 0:
                report["compatibility_rate"] = (report["compatible_tools"] / report["tools_found"]) * 100
            else:
                report["compatibility_rate"] = 100
                
            logger.info(f"Verificação concluída. Taxa de compatibilidade: {report['compatibility_rate']:.2f}%")
            
            # Salva o relatório
            report_file = os.path.join(self.backup_dir, "compatibility_report.json")
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
                
            logger.info(f"Relatório de compatibilidade salvo em: {report_file}")
            
            return report
            
        except Exception as e:
            logger.error(f"Erro ao verificar compatibilidade: {str(e)}")
            return {"error": str(e)}
    
    def adapt_agent_class(self, agent_type: str) -> bool:
        """
        Adapta um agente existente para usar o novo DataProxyAgent.
        
        Cria uma versão adaptada do agente que utiliza o novo DataProxyAgent,
        facilitando a transição entre as arquiteturas.
        
        Args:
            agent_type: Tipo do agente a ser adaptado (e.g., "sales", "support")
            
        Returns:
            bool: True se a adaptação foi bem-sucedida, False caso contrário
        """
        try:
            logger.info(f"Adaptando agente: {agent_type}")
            
            # Mapeia o tipo do agente para o arquivo da classe
            agent_files = {
                "sales": "src/agents/specialized/sales_agent.py",
                "support": "src/agents/specialized/support_agent.py",
                "scheduling": "src/agents/specialized/scheduling_agent.py",
            }
            
            if agent_type not in agent_files:
                logger.error(f"Tipo de agente desconhecido: {agent_type}")
                return False
                
            agent_file = agent_files[agent_type]
            
            # Verifica se o arquivo existe
            if not os.path.exists(agent_file):
                logger.error(f"Arquivo do agente não encontrado: {agent_file}")
                return False
                
            # Faz backup do arquivo original
            self.backup_file(agent_file)
            
            # Lê o conteúdo do arquivo
            with open(agent_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Cria o novo arquivo adaptado
            output_file = agent_file.replace(".py", "_adapted.py")
            
            # Gera o código adaptado
            adapted_content = self._generate_adapted_agent_code(content, agent_type)
            
            # Salva o arquivo adaptado
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(adapted_content)
                
            logger.info(f"Agente adaptado salvo em: {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adaptar agente {agent_type}: {str(e)}")
            return False
    
    def _generate_adapted_agent_code(self, original_code: str, agent_type: str) -> str:
        """
        Gera o código adaptado para um agente.
        
        Args:
            original_code: Código original do agente
            agent_type: Tipo do agente
            
        Returns:
            str: Código adaptado
        """
        # Obtém o nome da classe do agente
        class_name = f"{agent_type.capitalize()}Agent"
        adapted_class_name = f"Adapted{class_name}"
        
        # Adiciona comentários e importações necessárias
        header = f"""\"\"\"
Versão adaptada do {class_name} para usar a nova arquitetura.

Esta classe é um adaptador que permite o uso do {class_name} original
com o novo DataProxyAgent e DomainManager.

GERADO AUTOMATICAMENTE PELO SCRIPT DE MIGRAÇÃO.
\"\"\"
import logging
from typing import Dict, List, Any, Optional

# Importações da arquitetura antiga
{original_code.split('import logging', 1)[1].split('class', 1)[0]}

# Importações da nova arquitetura
from src.core.data_proxy_agent_new import DataProxyAgent as NewDataProxyAgent
from src.core.domain.domain_manager_new import DomainManager as NewDomainManager
from src.core.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

"""

        # Gera a classe adaptadora
        adapter_class = f"""class {adapted_class_name}({class_name}):
    \"\"\"
    Versão adaptada do {class_name} para usar a nova arquitetura.
    
    Esta classe adapta o {class_name} original para trabalhar com o novo
    DataProxyAgent e DomainManager, facilitando a transição entre as arquiteturas.
    \"\"\"
    
    def __init__(self, agent_config: Dict[str, Any], 
                 memory_system=None,
                 data_proxy_agent=None,
                 domain_manager=None,
                 plugin_manager=None,
                 tool_registry=None):
        \"\"\"
        Inicializa o agente adaptado.
        
        Args:
            agent_config: Configuração do agente
            memory_system: Sistema de memória compartilhada
            data_proxy_agent: Novo DataProxyAgent (opcional)
            domain_manager: Novo DomainManager (opcional)
            plugin_manager: Gerenciador de plugins
            tool_registry: Registro de ferramentas (opcional)
        \"\"\"
        # Verifica se estamos usando o novo DataProxyAgent
        self.using_new_architecture = isinstance(data_proxy_agent, NewDataProxyAgent)
        self.tool_registry = tool_registry or ToolRegistry()
        
        if self.using_new_architecture:
            logger.info(f"Inicializando {adapted_class_name} com a nova arquitetura")
            # Armazena referências para componentes da nova arquitetura
            self.new_data_proxy_agent = data_proxy_agent
            self.new_domain_manager = domain_manager if isinstance(domain_manager, NewDomainManager) else None
            
            # Cria uma instância compatível com a arquitetura antiga para o construtor pai
            legacy_data_proxy = self._create_legacy_data_proxy_adapter()
            super().__init__(
                agent_config=agent_config,
                memory_system=memory_system,
                data_proxy_agent=legacy_data_proxy,
                domain_manager=domain_manager,
                plugin_manager=plugin_manager
            )
        else:
            # Usa a inicialização padrão
            logger.info(f"Inicializando {adapted_class_name} com a arquitetura legada")
            super().__init__(
                agent_config=agent_config,
                memory_system=memory_system,
                data_proxy_agent=data_proxy_agent,
                domain_manager=domain_manager,
                plugin_manager=plugin_manager
            )
    
    def _create_legacy_data_proxy_adapter(self):
        \"\"\"
        Cria um adaptador que emula o DataProxyAgent antigo usando o novo.
        
        Returns:
            object: Um objeto que emula a interface do DataProxyAgent antigo
        \"\"\"
        # Cria um objeto que encapsula o novo DataProxyAgent e expõe métodos compatíveis
        class LegacyDataProxyAdapter:
            def __init__(self, new_proxy, tool_registry):
                self.new_proxy = new_proxy
                self.tool_registry = tool_registry
            
            def is_ready(self):
                return self.new_proxy.is_ready()
                
            def query_product_data(self, query_text, filters=None, domain=None):
                return self.new_proxy.query_product_data(query_text, filters, domain)
                
            def query_customer_data(self, query_text, filters=None, domain=None):
                return self.new_proxy.query_customer_data(query_text, filters, domain)
                
            def query_business_rules(self, rule_type, context=None, domain=None):
                return self.new_proxy.query_business_rules(rule_type, context, domain)
                
            def query_vector_search(self, query_text, collection=None, filters=None, domain=None):
                return self.new_proxy.query_vector_search(query_text, collection, filters, domain)
                
            def query_memory(self, query_text, memory_type=None, domain=None):
                return self.new_proxy.query_memory(query_text, memory_type, domain)
                
            def get_tools(self):
                # Obtém todas as ferramentas disponíveis para o domínio ativo
                if hasattr(self.new_proxy, 'get_tools_for_agent'):
                    return self.new_proxy.get_tools_for_agent('{agent_type}')
                return []
                
        return LegacyDataProxyAdapter(self.new_data_proxy_agent, self.tool_registry)
    
    # Override de métodos específicos que precisam se comportar de forma diferente
    # com a nova arquitetura
    
    def get_crew_agent(self):
        \"\"\"
        Cria e retorna um agente CrewAI adaptado.
        
        Returns:
            Agent: Um agente CrewAI configurado
        \"\"\"
        if self.using_new_architecture:
            # Usa a nova abordagem baseada em configuração de domínio
            logger.info(f"Criando CrewAI agent para {self.__class__.__name__} com a nova arquitetura")
            
            # Se já temos um agente criado, retorna-o
            if hasattr(self, 'crew_agent') and self.crew_agent:
                return self.crew_agent
                
            # Obtém ferramentas do novo DataProxyAgent
            tools = self.new_data_proxy_agent.get_tools_for_agent('{agent_type}')
            
            # Obtém configuração do domínio ativo
            domain = self.new_domain_manager.get_active_domain() if self.new_domain_manager else "default"
            domain_config = self.new_domain_manager.get_active_domain_config() if self.new_domain_manager else {{}}
            
            # Extrai configurações do agente no domínio
            agent_config = domain_config.get('agents', {{}}).get('{agent_type}', {{}})
            
            # Usa valores do domínio ou fallback para os padrões
            role = agent_config.get('role', f"Especialista em {agent_type}")
            goal = agent_config.get('goal', f"Auxiliar clientes com consultas de {agent_type}")
            backstory = agent_config.get('backstory', f"Você é um especialista em {agent_type}.")
            
            # Cria o agente com as configurações obtidas
            from crewai import Agent
            crew_agent = Agent(
                role=role,
                goal=goal,
                backstory=backstory,
                tools=tools,
                verbose=True
            )
            
            # Armazena o agente criado
            self.crew_agent = crew_agent
            return crew_agent
        else:
            # Usa a implementação original
            return super().get_crew_agent()
"""

        # Combina tudo
        return header + adapter_class


def main():
    """Ponto de entrada principal do script."""
    parser = argparse.ArgumentParser(description='Ferramenta de migração para a nova arquitetura do Chatwoot V4')
    
    # Adiciona argumentos
    parser.add_argument('--migrate-domain', type=str, help='Migra a configuração de um domínio')
    parser.add_argument('--check-compatibility', action='store_true', help='Verifica a compatibilidade das ferramentas')
    parser.add_argument('--adapt-agent', type=str, help='Adapta um agente para usar a nova arquitetura')
    parser.add_argument('--config-dir', type=str, help='Diretório de configurações')
    
    args = parser.parse_args()
    
    # Cria o assistente de migração
    helper = MigrationHelper(config_dir=args.config_dir)
    
    # Executa a ação solicitada
    if args.migrate_domain:
        success = helper.migrate_domain_config(args.migrate_domain)
        if success:
            logger.info(f"Migração do domínio {args.migrate_domain} concluída com sucesso.")
        else:
            logger.error(f"Falha na migração do domínio {args.migrate_domain}.")
            sys.exit(1)
            
    elif args.check_compatibility:
        report = helper.check_tool_compatibility()
        logger.info(f"Verificação de compatibilidade concluída. Taxa: {report.get('compatibility_rate', 0):.2f}%")
        
    elif args.adapt_agent:
        success = helper.adapt_agent_class(args.adapt_agent)
        if success:
            logger.info(f"Adaptação do agente {args.adapt_agent} concluída com sucesso.")
        else:
            logger.error(f"Falha na adaptação do agente {args.adapt_agent}.")
            sys.exit(1)
            
    else:
        parser.print_help()
        sys.exit(1)
        
    sys.exit(0)


if __name__ == "__main__":
    main()
