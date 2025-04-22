# -*- coding: utf-8 -*-

"""
Conector base para Odoo via XML-RPC.
"""

import logging
import xmlrpc.client
from typing import Dict, Any, List, Optional, Tuple, Union
import os
import yaml
import json
import asyncio
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_exponential

from odoo_api.config.settings import settings
from odoo_api.core.exceptions import OdooConnectionError, OdooAuthenticationError, OdooOperationError

# Importar o módulo de criptografia
try:
    from src.utils.encryption import credential_encryption
    ENCRYPTION_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("Encryption module loaded successfully. Credentials will be decrypted.")
except ImportError:
    ENCRYPTION_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Encryption module not available. Credentials will not be decrypted.")

logger = logging.getLogger(__name__)

class OdooConnector:
    """Conector base para Odoo via XML-RPC."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        use_https: bool = True,
    ):
        """
        Inicializa o conector Odoo.

        Args:
            host: Hostname do servidor Odoo
            port: Porta do servidor Odoo
            database: Nome do banco de dados Odoo
            username: Nome de usuário para autenticação
            password: Senha para autenticação
            use_https: Se True, usa HTTPS; caso contrário, usa HTTP
        """
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.use_https = use_https

        # Construir URLs
        protocol = "https" if use_https else "http"
        self.common_url = f"{protocol}://{host}:{port}/xmlrpc/2/common"
        self.object_url = f"{protocol}://{host}:{port}/xmlrpc/2/object"

        # Inicializar conexão
        self.uid = None
        self.common = xmlrpc.client.ServerProxy(self.common_url)
        self.models = xmlrpc.client.ServerProxy(self.object_url)

    async def connect(self) -> int:
        """
        Estabelece conexão com o servidor Odoo.

        Returns:
            ID do usuário autenticado

        Raises:
            OdooConnectionError: Se não for possível conectar ao servidor
            OdooAuthenticationError: Se a autenticação falhar
        """
        try:
            # Executar em thread separada para não bloquear o event loop
            loop = asyncio.get_event_loop()
            uid = await loop.run_in_executor(
                None,
                lambda: self.common.authenticate(
                    self.database, self.username, self.password, {}
                ),
            )

            if not uid:
                raise OdooAuthenticationError(
                    f"Authentication failed for user {self.username} on database {self.database}"
                )

            self.uid = uid
            logger.info(f"Connected to Odoo server {self.host}:{self.port} as {self.username} (uid: {self.uid})")
            return uid

        except xmlrpc.client.Fault as e:
            logger.error(f"Odoo XML-RPC fault: {e}")
            raise OdooConnectionError(f"XML-RPC fault: {e}")

        except Exception as e:
            logger.error(f"Failed to connect to Odoo server: {e}")
            raise OdooConnectionError(f"Failed to connect to Odoo server: {e}")

    @retry(
        stop=stop_after_attempt(settings.RETRY_MAX_ATTEMPTS),
        wait=wait_exponential(
            multiplier=1,
            min=settings.RETRY_MIN_SECONDS,
            max=settings.RETRY_MAX_SECONDS,
        ),
    )
    async def execute_kw(
        self,
        model: str,
        method: str,
        args: List[Any] = None,
        kwargs: Dict[str, Any] = None,
    ) -> Any:
        """
        Executa um método no modelo Odoo.

        Args:
            model: Nome do modelo Odoo
            method: Nome do método a ser executado
            args: Argumentos posicionais para o método
            kwargs: Argumentos nomeados para o método

        Returns:
            Resultado da execução do método

        Raises:
            OdooConnectionError: Se não for possível conectar ao servidor
            OdooOperationError: Se a operação falhar
        """
        if args is None:
            args = []

        if kwargs is None:
            kwargs = {}

        # Garantir que estamos conectados
        if self.uid is None:
            await self.connect()

        try:
            # Executar em thread separada para não bloquear o event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.models.execute_kw(
                    self.database,
                    self.uid,
                    self.password,
                    model,
                    method,
                    args,
                    kwargs,
                ),
            )

            return result

        except xmlrpc.client.Fault as e:
            logger.error(f"Odoo XML-RPC fault: {e}")
            raise OdooOperationError(f"XML-RPC fault: {e}")

        except Exception as e:
            logger.error(f"Failed to execute method {method} on model {model}: {e}")
            raise OdooOperationError(f"Failed to execute method {method} on model {model}: {e}")

    async def search_read(
        self,
        model: str,
        domain: List[Tuple] = None,
        fields: List[str] = None,
        offset: int = 0,
        limit: int = None,
        order: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca e lê registros do modelo Odoo.

        Args:
            model: Nome do modelo Odoo
            domain: Domínio de busca
            fields: Campos a serem retornados
            offset: Offset para paginação
            limit: Limite de registros
            order: Ordenação

        Returns:
            Lista de registros
        """
        if domain is None:
            domain = []

        kwargs = {}

        if fields:
            kwargs["fields"] = fields

        if offset:
            kwargs["offset"] = offset

        if limit:
            kwargs["limit"] = limit

        if order:
            kwargs["order"] = order

        return await self.execute_kw(model, "search_read", [domain], kwargs)

    async def create(self, model: str, values: Dict[str, Any]) -> int:
        """
        Cria um novo registro no modelo Odoo.

        Args:
            model: Nome do modelo Odoo
            values: Valores para o novo registro

        Returns:
            ID do registro criado
        """
        return await self.execute_kw(model, "create", [values])

    async def write(self, model: str, ids: List[int], values: Dict[str, Any]) -> bool:
        """
        Atualiza registros existentes no modelo Odoo.

        Args:
            model: Nome do modelo Odoo
            ids: IDs dos registros a serem atualizados
            values: Valores a serem atualizados

        Returns:
            True se a operação for bem-sucedida
        """
        return await self.execute_kw(model, "write", [ids, values])

    async def unlink(self, model: str, ids: List[int]) -> bool:
        """
        Remove registros do modelo Odoo.

        Args:
            model: Nome do modelo Odoo
            ids: IDs dos registros a serem removidos

        Returns:
            True se a operação for bem-sucedida
        """
        return await self.execute_kw(model, "unlink", [ids])


class OdooConnectorFactory:
    """Fábrica para criar conectores Odoo."""

    @staticmethod
    async def create_connector(account_id: str) -> OdooConnector:
        """
        Cria um conector Odoo para o account_id especificado.

        Args:
            account_id: ID da conta

        Returns:
            Instância de OdooConnector

        Raises:
            ValueError: Se a configuração para o account_id não for encontrada
        """
        # Obter configuração do Redis (se disponível)
        # TODO: Implementar cache Redis

        # Se não estiver no cache, carregar do arquivo YAML
        config = await OdooConnectorFactory._load_config_from_yaml(account_id)

        if not config:
            raise ValueError(f"Configuration for account_id {account_id} not found")

        # Criar conector
        connector = OdooConnector(
            host=config.get("host"),
            port=config.get("port", 8069),
            database=config.get("database"),
            username=config.get("username"),
            password=config.get("password"),
            use_https=config.get("use_https", True),
        )

        # Conectar
        await connector.connect()

        return connector

    @staticmethod
    async def _load_config_from_yaml(account_id: str) -> Dict[str, Any]:
        """
        Carrega a configuração do arquivo YAML.

        Args:
            account_id: ID da conta

        Returns:
            Configuração do Odoo
        """
        # Determinar o domínio com base no account_id
        domain = await OdooConnectorFactory._determine_domain(account_id)
        if not domain:
            logger.error(f"Could not determine domain for account_id {account_id}")
            return None

        # Construir caminho para o arquivo de configuração
        config_file = os.path.join(settings.CONFIG_DIR, "domains", domain, account_id, "config.yaml")

        if not os.path.exists(config_file):
            logger.error(f"Configuration file {config_file} not found")
            return None

        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)

            # Extrair configuração do MCP (Odoo)
            if "integrations" in config and "mcp" in config["integrations"]:
                mcp_config = config["integrations"]["mcp"]

                if "config" in mcp_config:
                    db_config = {
                        "host": mcp_config["config"].get("url", "").replace("http://", "").replace("https://", "").split(":")[0],
                        "port": int(mcp_config["config"].get("url", "").split(":")[-1]) if ":" in mcp_config["config"].get("url", "") else 8069,
                        "database": mcp_config["config"].get("db", ""),
                        "username": mcp_config["config"].get("username", ""),
                        "credential_ref": mcp_config["config"].get("credential_ref", ""),
                        "use_https": mcp_config["config"].get("url", "").startswith("https")
                    }

                    # Obter a senha real usando a referência
                    password = await OdooConnectorFactory._get_credential_by_ref(
                        db_config["credential_ref"],
                        account_id,
                        domain
                    )

                    if password:
                        db_config["password"] = password
                    else:
                        logger.error(f"Could not retrieve password for credential_ref {db_config['credential_ref']}")
                        return None

                    return db_config

            logger.error(f"MCP configuration not found in {config_file}")
            return None

        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")
            return None

    @staticmethod
    async def _determine_domain(account_id: str) -> str:
        """
        Determina o domínio com base no account_id.

        Args:
            account_id: ID da conta

        Returns:
            Nome do domínio
        """
        # Verificar se existe um mapeamento de account_id para domínio
        mapping_file = os.path.join(settings.CONFIG_DIR, "account_mapping.yaml")

        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, "r") as f:
                    mapping = yaml.safe_load(f)

                if mapping and "accounts" in mapping:
                    for domain, accounts in mapping["accounts"].items():
                        if account_id in accounts:
                            return domain
            except Exception as e:
                logger.error(f"Failed to load account mapping: {e}")

        # Se não encontrar no mapeamento, verificar no chatwoot_mapping.yaml
        chatwoot_mapping_file = os.path.join(settings.CONFIG_DIR, "chatwoot_mapping.yaml")

        if os.path.exists(chatwoot_mapping_file):
            try:
                with open(chatwoot_mapping_file, "r") as f:
                    mapping = yaml.safe_load(f)

                if mapping and "clients" in mapping and account_id in mapping["clients"]:
                    return mapping["clients"][account_id]["domain"]
            except Exception as e:
                logger.error(f"Failed to load chatwoot mapping: {e}")

        # Se não encontrar em nenhum lugar, usar o domínio padrão
        return "retail"  # Domínio padrão

    @staticmethod
    async def _get_credential_by_ref(credential_ref: str, account_id: str, domain: str = None) -> str:
        """
        Recupera a credencial real usando a referência.

        Args:
            credential_ref: Referência da credencial
            account_id: ID da conta
            domain: Domínio da conta (opcional, será determinado se não fornecido)

        Returns:
            Credencial real
        """
        if not domain:
            domain = await OdooConnectorFactory._determine_domain(account_id)
            if not domain:
                logger.error(f"Could not determine domain for account_id {account_id}")
                return None

        # Construir caminho para o arquivo de credenciais
        credentials_file = os.path.join(settings.CONFIG_DIR, "domains", domain, account_id, "credentials.yaml")
        config_file = os.path.join(settings.CONFIG_DIR, "domains", domain, account_id, "config.yaml")

        # Primeiro, tentar carregar do arquivo de credenciais
        if os.path.exists(credentials_file):
            try:
                with open(credentials_file, "r") as f:
                    creds_config = yaml.safe_load(f)

                # Verificar se a credencial existe na seção de credenciais
                if creds_config and "credentials" in creds_config and credential_ref in creds_config["credentials"]:
                    logger.info(f"Credential found in credentials.yaml: {credential_ref}")
                    credential_value = creds_config["credentials"][credential_ref]

                    # Descriptografar a senha se estiver criptografada e o módulo de criptografia estiver disponível
                    if ENCRYPTION_AVAILABLE and isinstance(credential_value, str) and credential_value.startswith("ENC:"):
                        try:
                            decrypted_value = credential_encryption.decrypt(credential_value)
                            logger.info(f"Credential decrypted successfully for {credential_ref}")
                            return decrypted_value
                        except Exception as e:
                            logger.error(f"Failed to decrypt credential {credential_ref}: {e}")
                            # Retornar o valor criptografado como fallback
                            return credential_value

                    return credential_value

            except Exception as e:
                logger.error(f"Failed to load credentials from {credentials_file}: {e}")
                # Continuar para tentar o arquivo de configuração

        # Se não encontrou no arquivo de credenciais, tentar no arquivo de configuração (para compatibilidade)
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)

                # Verificar se a credencial existe na seção de credenciais
                if "credentials" in config and credential_ref in config["credentials"]:
                    logger.warning(f"Credential found in config.yaml (deprecated): {credential_ref}")
                    credential_value = config["credentials"][credential_ref]

                    # Descriptografar a senha se estiver criptografada e o módulo de criptografia estiver disponível
                    if ENCRYPTION_AVAILABLE and isinstance(credential_value, str) and credential_value.startswith("ENC:"):
                        try:
                            decrypted_value = credential_encryption.decrypt(credential_value)
                            logger.info(f"Credential decrypted successfully for {credential_ref} (from config.yaml)")
                            return decrypted_value
                        except Exception as e:
                            logger.error(f"Failed to decrypt credential {credential_ref} (from config.yaml): {e}")
                            # Retornar o valor criptografado como fallback
                            return credential_value

                    return credential_value

                # Verificar se a credencial existe no nível raiz do arquivo
                if credential_ref in config:
                    logger.warning(f"Credential found at root level in config.yaml (deprecated): {credential_ref}")
                    credential_value = config[credential_ref]

                    # Descriptografar a senha se estiver criptografada e o módulo de criptografia estiver disponível
                    if ENCRYPTION_AVAILABLE and isinstance(credential_value, str) and credential_value.startswith("ENC:"):
                        try:
                            decrypted_value = credential_encryption.decrypt(credential_value)
                            logger.info(f"Credential decrypted successfully for {credential_ref} (from config.yaml root)")
                            return decrypted_value
                        except Exception as e:
                            logger.error(f"Failed to decrypt credential {credential_ref} (from config.yaml root): {e}")
                            # Retornar o valor criptografado como fallback
                            return credential_value

                    return credential_value

                logger.error(f"Credential reference {credential_ref} not found in {config_file} or {credentials_file}")
                return None

            except Exception as e:
                logger.error(f"Failed to load credentials from {config_file}: {e}")
                return None

        # Se não encontrar o arquivo, usar a própria referência como senha (para desenvolvimento)
        logger.warning(f"Using credential_ref as password for development: {credential_ref}")
        return credential_ref
