#!/usr/bin/env python3
"""
Script para criar um novo domínio de negócio no ChatwootAI.

Este script automatiza a criação de um novo domínio de negócio, incluindo:
- Arquivo de configuração YAML
- Estrutura básica de plugins
- Documentação do domínio

Uso:
    python create_new_domain.py --name "nome_do_setor" [--description "descrição"] [--template "template"]
"""
import os
import sys
import argparse
import shutil
import yaml
from datetime import datetime


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Criar um novo domínio de negócio para o ChatwootAI")
    parser.add_argument("--name", required=True, help="Nome do domínio de negócio (ex: healthcare)")
    parser.add_argument("--description", help="Descrição do domínio de negócio")
    parser.add_argument("--template", default="retail", 
                        help="Template a ser usado como base (ex: cosmetics, healthcare, retail)")
    return parser.parse_args()


def create_yaml_config(domain_name, description, template):
    """
    Cria o arquivo de configuração YAML para o novo domínio.
    
    Args:
        domain_name: Nome do domínio
        description: Descrição do domínio
        template: Nome do template a ser usado como base
    
    Returns:
        bool: True se a criação foi bem-sucedida, False caso contrário
    """
    # Caminhos dos arquivos
    config_dir = os.path.join("src", "config", "business_domains")
    template_file = os.path.join(config_dir, f"{template}.yaml")
    target_file = os.path.join(config_dir, f"{domain_name}.yaml")
    
    # Verifica se o diretório existe
    if not os.path.exists(config_dir):
        print(f"Criando diretório: {config_dir}")
        os.makedirs(config_dir, exist_ok=True)
    
    # Verifica se o arquivo de template existe
    if not os.path.exists(template_file):
        print(f"Erro: Template não encontrado: {template_file}")
        return False
    
    # Verifica se o arquivo de destino já existe
    if os.path.exists(target_file):
        print(f"Aviso: Arquivo de configuração já existe: {target_file}")
        overwrite = input("Deseja sobrescrever? (s/N): ").lower() == "s"
        if not overwrite:
            return False
    
    try:
        # Carrega o template
        with open(template_file, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        
        # Modifica as informações básicas
        config["name"] = domain_name.capitalize()
        if description:
            config["description"] = description
        
        # Adiciona metadados
        config["metadata"] = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "created_by": os.environ.get("USER", "unknown"),
            "template": template
        }
        
        # Salva o novo arquivo de configuração
        with open(target_file, "w", encoding="utf-8") as file:
            yaml.dump(config, file, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        print(f"Arquivo de configuração criado: {target_file}")
        return True
        
    except Exception as e:
        print(f"Erro ao criar arquivo de configuração: {str(e)}")
        return False


def create_plugin_structure(domain_name):
    """
    Cria a estrutura básica de plugins para o novo domínio.
    
    Args:
        domain_name: Nome do domínio
    
    Returns:
        bool: True se a criação foi bem-sucedida, False caso contrário
    """
    # Caminhos dos diretórios
    plugins_dir = os.path.join("src", "plugins")
    domain_plugins_dir = os.path.join(plugins_dir, domain_name)
    
    # Verifica se o diretório existe
    if not os.path.exists(plugins_dir):
        print(f"Criando diretório: {plugins_dir}")
        os.makedirs(plugins_dir, exist_ok=True)
    
    # Verifica se o diretório de plugins do domínio já existe
    if os.path.exists(domain_plugins_dir):
        print(f"Aviso: Diretório de plugins já existe: {domain_plugins_dir}")
    else:
        # Cria o diretório de plugins do domínio
        os.makedirs(domain_plugins_dir, exist_ok=True)
        print(f"Diretório de plugins criado: {domain_plugins_dir}")
    
    # Cria o arquivo __init__.py
    init_file = os.path.join(domain_plugins_dir, "__init__.py")
    with open(init_file, "w", encoding="utf-8") as file:
        file.write(f'"""\nPlugins específicos para o domínio de {domain_name}.\n"""\n\n')
    
    # Cria um plugin de exemplo
    example_plugin_file = os.path.join(domain_plugins_dir, "example_plugin.py")
    with open(example_plugin_file, "w", encoding="utf-8") as file:
        file.write(f'''"""
Plugin de exemplo para o domínio de {domain_name}.
"""
from typing import Dict, List, Any, Optional
import logging

from src.plugins.base import BasePlugin

logger = logging.getLogger(__name__)


class ExamplePlugin(BasePlugin):
    """
    Plugin de exemplo para o domínio de {domain_name}.
    
    Este é um plugin de exemplo que pode ser usado como base para
    implementar funcionalidades específicas do domínio de {domain_name}.
    """
    
    def initialize(self):
        """
        Inicializa o plugin carregando dados específicos.
        """
        self.example_data = self._load_example_data()
    
    def _load_example_data(self) -> Dict[str, Any]:
        """
        Carrega dados de exemplo para o plugin.
        Em uma implementação real, isso poderia vir de uma API ou banco de dados.
        
        Returns:
            Dict[str, Any]: Dados de exemplo
        """
        return {
            "example_key": "example_value",
            "items": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"},
                {"id": 3, "name": "Item 3"}
            ]
        }
    
    def execute(self, action: str, **kwargs) -> Any:
        """
        Executa uma ação do plugin.
        
        Args:
            action: Ação a ser executada
            **kwargs: Parâmetros específicos da ação
            
        Returns:
            Any: Resultado da ação
        """
        if action == "get_items":
            return self.example_data.get("items", [])
        
        elif action == "get_item":
            item_id = kwargs.get("item_id")
            if item_id is None:
                logger.error("ID do item não fornecido")
                return None
            
            items = self.example_data.get("items", [])
            for item in items:
                if item["id"] == item_id:
                    return item
            
            logger.warning(f"Item não encontrado: {item_id}")
            return None
        
        else:
            logger.error(f"Ação desconhecida: {action}")
            return {{"success": False, "error": f"Ação desconhecida: {{action}}"}}
''')
    
    print(f"Plugin de exemplo criado: {example_plugin_file}")
    return True


def create_documentation(domain_name, description):
    """
    Cria a documentação para o novo domínio.
    
    Args:
        domain_name: Nome do domínio
        description: Descrição do domínio
    
    Returns:
        bool: True se a criação foi bem-sucedida, False caso contrário
    """
    # Caminhos dos diretórios
    docs_dir = os.path.join("docs", "domains")
    
    # Verifica se o diretório existe
    if not os.path.exists(docs_dir):
        print(f"Criando diretório: {docs_dir}")
        os.makedirs(docs_dir, exist_ok=True)
    
    # Cria o arquivo de documentação
    doc_file = os.path.join(docs_dir, f"{domain_name}.md")
    
    # Verifica se o arquivo já existe
    if os.path.exists(doc_file):
        print(f"Aviso: Arquivo de documentação já existe: {doc_file}")
        overwrite = input("Deseja sobrescrever? (s/N): ").lower() == "s"
        if not overwrite:
            return False
    
    with open(doc_file, "w", encoding="utf-8") as file:
        file.write(f'''# Domínio de Negócio: {domain_name.capitalize()}

{description or f"Configuração para o domínio de {domain_name}."}

## Visão Geral

Este documento descreve a configuração e implementação do domínio de negócio {domain_name.capitalize()} no ChatwootAI.

## Configuração

A configuração do domínio está definida no arquivo `src/config/business_domains/{domain_name}.yaml`.

### Regras de Negócio

As regras de negócio específicas deste domínio incluem:

- Regra 1
- Regra 2
- Regra 3

### Agentes Especializados

Os agentes especializados para este domínio incluem:

- Agente 1: Responsável por...
- Agente 2: Responsável por...
- Agente 3: Responsável por...

### Plugins

Os plugins específicos para este domínio incluem:

- Plugin 1: Funcionalidade...
- Plugin 2: Funcionalidade...

## Implementação

### Fluxos de Trabalho

Os principais fluxos de trabalho deste domínio são:

1. Fluxo 1
   - Passo 1
   - Passo 2
   - Passo 3

2. Fluxo 2
   - Passo 1
   - Passo 2
   - Passo 3

### Integrações

Este domínio requer as seguintes integrações:

- Integração 1
- Integração 2
- Integração 3

## Personalização

Para personalizar este domínio para necessidades específicas, você pode:

1. Editar o arquivo de configuração YAML
2. Implementar plugins personalizados
3. Ajustar os prompts dos agentes

## Exemplos

### Exemplo 1

```python
# Código de exemplo
```

### Exemplo 2

```python
# Código de exemplo
```

## Referências

- [Link 1](https://example.com)
- [Link 2](https://example.com)
''')
    
    print(f"Documentação criada: {doc_file}")
    return True


def main():
    """Main function."""
    args = parse_args()
    
    domain_name = args.name.lower()
    description = args.description or f"Configuração para o domínio de {domain_name}"
    template = args.template.lower()
    
    print(f"Criando novo domínio de negócio: {domain_name}")
    print(f"Descrição: {description}")
    print(f"Template: {template}")
    print()
    
    # Cria o arquivo de configuração YAML
    if not create_yaml_config(domain_name, description, template):
        print("Erro ao criar arquivo de configuração YAML")
        return 1
    
    # Cria a estrutura de plugins
    if not create_plugin_structure(domain_name):
        print("Erro ao criar estrutura de plugins")
        return 1
    
    # Cria a documentação
    if not create_documentation(domain_name, description):
        print("Erro ao criar documentação")
        return 1
    
    print()
    print(f"Domínio de negócio '{domain_name}' criado com sucesso!")
    print()
    print("Próximos passos:")
    print(f"1. Edite o arquivo de configuração: src/config/business_domains/{domain_name}.yaml")
    print(f"2. Implemente plugins específicos em: src/plugins/{domain_name}/")
    print(f"3. Complete a documentação em: docs/domains/{domain_name}.md")
    print()
    print("Para ativar o novo domínio, use o DomainManager:")
    print("```python")
    print("from src.core.domain import DomainManager")
    print()
    print("domain_manager = DomainManager()")
    print(f"domain_manager.switch_domain('{domain_name}')")
    print("```")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
