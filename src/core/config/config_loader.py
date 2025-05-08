#!/usr/bin/env python3
"""
ConfigLoader para o ChatwootAI

Este módulo implementa o ConfigLoader, responsável por carregar e mesclar
configurações YAML dos clientes, com suporte a carregamento de configurações
do serviço de configuração.
"""

import logging
import os
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path

# Importar cliente do serviço de configuração
try:
    from src.utils.config_service_client import config_service
    HAS_CONFIG_SERVICE = True
except ImportError:
    HAS_CONFIG_SERVICE = False

# Configurar logging
logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Carregador de configurações YAML.

    Esta classe é responsável por carregar configurações YAML dos clientes,
    com suporte a mesclagem de configurações base e específicas.
    """

    def __init__(self, config_dir: str = None):
        """
        Inicializa o carregador de configurações.

        Args:
            config_dir: Diretório base de configurações
        """
        self.config_dir = config_dir or os.path.join("config", "domains")
        logger.info(f"ConfigLoader inicializado com diretório: {self.config_dir}")

    async def load_config(self, domain_name: str, account_id: str) -> Dict[str, Any]:
        """
        Carrega a configuração para um domínio e account_id específicos.

        Processo de carregamento:
        1. Tentar carregar do serviço de configuração (se disponível)
        2. Se não for possível, carregar dos arquivos locais:
           a. Carregar configuração base do domínio (se existir)
           b. Carregar configuração específica do account_id
           c. Mesclar as configurações

        Args:
            domain_name: Nome do domínio
            account_id: ID da conta

        Returns:
            Configuração mesclada

        Raises:
            FileNotFoundError: Se o arquivo de configuração não for encontrado
        """
        # Tentar carregar do serviço de configuração
        if HAS_CONFIG_SERVICE and config_service.health_check():
            logger.info(f"Tentando carregar configuração do serviço de configuração: {domain_name}/{account_id}")
            config_data = config_service.get_config(account_id, domain_name, "config")
            if config_data:
                logger.info(f"Configuração carregada do serviço de configuração: {domain_name}/{account_id}")
                # Extrair os dados JSON da resposta
                config = config_data.get("json_data", {})
                # Garantir que account_id e domain_name estejam na configuração
                config["account_id"] = account_id
                config["domain_name"] = domain_name
                return config
            else:
                logger.warning(f"Configuração não encontrada no serviço de configuração: {domain_name}/{account_id}")

        # Fallback para carregamento de arquivos locais
        logger.info(f"Carregando configuração de arquivos locais: {domain_name}/{account_id}")

        # Verificar se o domínio existe
        domain_dir = os.path.join(self.config_dir, domain_name)
        if not os.path.exists(domain_dir):
            logger.warning(f"Diretório de domínio não encontrado: {domain_dir}")
            # Tentar usar o domínio padrão
            domain_dir = os.path.join(self.config_dir, "default")
            if not os.path.exists(domain_dir):
                raise FileNotFoundError(f"Nem o domínio {domain_name} nem o domínio padrão foram encontrados")
            domain_name = "default"
            logger.info(f"Usando domínio padrão: {domain_name}")

        # Verificar se o account_id existe
        account_dir = os.path.join(domain_dir, account_id)
        if not os.path.exists(account_dir):
            logger.warning(f"Diretório de account_id não encontrado: {account_dir}")
            raise FileNotFoundError(f"Account_id {account_id} não encontrado no domínio {domain_name}")

        # Caminho para o arquivo de configuração
        config_file = os.path.join(account_dir, "config.yaml")
        if not os.path.exists(config_file):
            logger.warning(f"Arquivo de configuração não encontrado: {config_file}")
            raise FileNotFoundError(f"Arquivo de configuração não encontrado para {domain_name}/{account_id}")

        # Carregar configuração base do domínio (se existir)
        base_config = {}
        base_config_file = os.path.join(domain_dir, "config.yaml")
        if os.path.exists(base_config_file):
            try:
                with open(base_config_file, 'r') as f:
                    base_config = yaml.safe_load(f) or {}
                logger.debug(f"Configuração base carregada: {domain_name}")
            except Exception as e:
                logger.warning(f"Erro ao carregar configuração base: {e}")

        # Carregar configuração específica do account_id
        specific_config = {}
        try:
            with open(config_file, 'r') as f:
                specific_config = yaml.safe_load(f) or {}
            logger.debug(f"Configuração específica carregada: {domain_name}/{account_id}")
        except Exception as e:
            logger.error(f"Erro ao carregar configuração específica: {e}")
            raise

        # Mesclar configurações
        merged_config = self._merge_configs(base_config, specific_config)

        # Garantir que account_id e domain_name estejam na configuração
        merged_config["account_id"] = account_id
        merged_config["domain_name"] = domain_name

        return merged_config

    def _merge_configs(self, base_config: Dict[str, Any], specific_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mescla configurações base e específicas.

        Args:
            base_config: Configuração base
            specific_config: Configuração específica

        Returns:
            Configuração mesclada
        """
        # Cópia profunda da configuração base
        merged = base_config.copy()

        # Mesclar configurações específicas
        for key, value in specific_config.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # Mesclar dicionários recursivamente
                merged[key] = self._merge_configs(merged[key], value)
            else:
                # Substituir ou adicionar valor
                merged[key] = value

        return merged

    async def list_available_configs(self) -> Dict[str, List[str]]:
        """
        Lista todas as configurações disponíveis.

        Returns:
            Dicionário com domínios como chaves e listas de account_ids como valores
        """
        result = {}

        # Verificar se o diretório de configurações existe
        if not os.path.exists(self.config_dir):
            logger.warning(f"Diretório de configurações não encontrado: {self.config_dir}")
            return result

        # Listar domínios
        for domain_name in os.listdir(self.config_dir):
            domain_dir = os.path.join(self.config_dir, domain_name)
            if not os.path.isdir(domain_dir):
                continue

            # Listar account_ids
            account_ids = []
            for item in os.listdir(domain_dir):
                account_dir = os.path.join(domain_dir, item)
                if os.path.isdir(account_dir):
                    config_file = os.path.join(account_dir, "config.yaml")
                    if os.path.exists(config_file):
                        account_ids.append(item)

            if account_ids:
                result[domain_name] = account_ids

        return result

    async def get_credentials(self, domain_name: str, account_id: str) -> Dict[str, Any]:
        """
        Carrega as credenciais para um domínio e account_id específicos.

        Processo de carregamento:
        1. Tentar carregar do serviço de configuração (se disponível)
        2. Se não for possível, carregar dos arquivos locais

        Args:
            domain_name: Nome do domínio
            account_id: ID da conta

        Returns:
            Credenciais carregadas

        Raises:
            FileNotFoundError: Se o arquivo de credenciais não for encontrado
        """
        # Tentar carregar do serviço de configuração
        if HAS_CONFIG_SERVICE and config_service.health_check():
            logger.info(f"Tentando carregar credenciais do serviço de configuração: {domain_name}/{account_id}")
            config_data = config_service.get_config(account_id, domain_name, "credentials")
            if config_data:
                logger.info(f"Credenciais carregadas do serviço de configuração: {domain_name}/{account_id}")
                # Extrair os dados JSON da resposta
                credentials = config_data.get("json_data", {})
                return credentials
            else:
                logger.warning(f"Credenciais não encontradas no serviço de configuração: {domain_name}/{account_id}")

        # Fallback para carregamento de arquivos locais
        logger.info(f"Carregando credenciais de arquivos locais: {domain_name}/{account_id}")

        # Caminho para o arquivo de credenciais
        credentials_file = os.path.join(self.config_dir, domain_name, account_id, "credentials.yaml")

        # Verificar se o arquivo existe
        if not os.path.exists(credentials_file):
            logger.warning(f"Arquivo de credenciais não encontrado: {credentials_file}")
            # Tentar arquivo de credenciais global
            credentials_file = os.path.join("config", "credentials", f"{account_id}.yaml")
            if not os.path.exists(credentials_file):
                logger.warning(f"Arquivo de credenciais global não encontrado: {credentials_file}")
                return {}

        # Carregar credenciais
        try:
            with open(credentials_file, 'r') as f:
                credentials = yaml.safe_load(f) or {}
            logger.debug(f"Credenciais carregadas: {domain_name}/{account_id}")
            return credentials
        except Exception as e:
            logger.error(f"Erro ao carregar credenciais: {e}")
            return {}
