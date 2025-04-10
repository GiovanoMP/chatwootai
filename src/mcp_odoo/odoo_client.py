"""
Odoo XML-RPC client for MCP server integration
"""

import os
import re
import socket
import urllib.parse

import http.client
import xmlrpc.client


class OdooClient:
    """Client for interacting with Odoo via XML-RPC"""

    def __init__(
        self,
        url,
        db,
        username,
        password,
        timeout=10,
        verify_ssl=True,
    ):
        """
        Initialize the Odoo client with connection parameters

        Args:
            url: Odoo server URL (with or without protocol)
            db: Database name
            username: Login username
            password: Login password
            timeout: Connection timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        # Ensure URL has a protocol
        if not re.match(r"^https?://", url):
            url = f"http://{url}"

        # Remove trailing slash from URL if present
        url = url.rstrip("/")

        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Parse URL to get hostname and port
        parsed_url = urllib.parse.urlparse(url)
        self.hostname = parsed_url.netloc
        self.use_https = parsed_url.scheme == "https"

        # Print configuration for debugging
        print("Odoo client configuration:")
        print(f"  URL: {self.url}")
        print(f"  Database: {self.db}")
        print(f"  Username: {self.username}")
        print(f"  Timeout: {self.timeout}s")
        print(f"  Verify SSL: {self.verify_ssl}")

        # Connect to Odoo
        self._connect()

    def _connect(self):
        """
        Connect to Odoo server and authenticate
        """
        print(f"Connecting to Odoo at: {self.url}")
        print(f"  Hostname: {self.hostname}")
        print(f"  Timeout: {self.timeout}s, Verify SSL: {self.verify_ssl}")

        # Create XML-RPC transports with proper timeout and SSL settings
        transport = RedirectTransport(
            timeout=self.timeout,
            use_https=self.use_https,
            verify_ssl=self.verify_ssl,
        )

        # Create XML-RPC proxies
        self._common = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/common", transport=transport
        )
        self._models = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", transport=transport
        )

        # Authenticate
        print(f"Authenticating with database: {self.db}, username: {self.username}")
        try:
            print(f"Making request to {self.hostname}/xmlrpc/2/common (attempt 1)")
            self.uid = self._common.authenticate(
                self.db, self.username, self.password, {}
            )
            if not self.uid:
                raise Exception("Authentication failed: Invalid credentials")
        except (socket.error, xmlrpc.client.ProtocolError) as e:
            print(f"Connection error: {str(e)}")
            # Try one more time
            print(f"Making request to {self.hostname}/xmlrpc/2/common (attempt 2)")
            self.uid = self._common.authenticate(
                self.db, self.username, self.password, {}
            )
            if not self.uid:
                raise Exception("Authentication failed: Invalid credentials")

    def _execute(self, model_name, method, *args, **kwargs):
        """
        Execute a method on a model

        Args:
            model_name: Name of the model (e.g., 'res.partner')
            method: Method name to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of the method execution
        """
        # Ensure we're connected
        if not self.uid:
            self._connect()

        try:
            print(f"Making request to {self.hostname}/xmlrpc/2/object")
            result = self._models.execute_kw(
                self.db, self.uid, self.password, model_name, method, args, kwargs
            )
            return result
        except (socket.error, xmlrpc.client.ProtocolError) as e:
            print(f"Connection error: {str(e)}")
            # Try one more time
            print(f"Making request to {self.hostname}/xmlrpc/2/object (retry)")
            result = self._models.execute_kw(
                self.db, self.uid, self.password, model_name, method, args, kwargs
            )
            return result
        except xmlrpc.client.Fault as e:
            print(f"Error during request: {e}")
            raise

    def get_models(self):
        """
        Get list of available models

        Returns:
            Dictionary containing:
            - model_names: List of model names
            - models_details: Dictionary mapping model names to details
            - error: Error message (if any)

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> models = client.get_models()
            >>> print(len(models['model_names']))
            100
            >>> print(models['model_names'][0])
            'res.partner'
        """
        try:
            # Primeiro, buscar os IDs dos modelos
            model_ids = self._models.execute_kw(
                self.db,
                self.uid,
                self.password,
                "ir.model",
                'search',
                [[]],
                {}
            )

            if not model_ids:
                return {"model_names": [], "models_details": {}}

            # Depois, ler os dados desses modelos
            models = self._models.execute_kw(
                self.db,
                self.uid,
                self.password,
                "ir.model",
                'read',
                [model_ids, ["model", "name"]],
                {}
            )

            # Extract model names and create details dictionary
            model_names = [m["model"] for m in models]
            models_details = {m["model"]: m for m in models}

            return {"model_names": model_names, "models_details": models_details}
        except Exception as e:
            print(f"Error retrieving models: {str(e)}", file=os.sys.stderr)
            return {"model_names": [], "models_details": {}, "error": str(e)}

    def get_model_info(self, model_name):
        """
        Get information about a specific model

        Args:
            model_name: Name of the model (e.g., 'res.partner')

        Returns:
            Dictionary with model information

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> info = client.get_model_info('res.partner')
            >>> print(info['name'])
            'Contact'
        """
        try:
            # Primeiro, buscar os IDs dos modelos que correspondem ao nome
            model_ids = self._execute(
                "ir.model",
                "search",
                [("model", "=", model_name)]
            )

            if not model_ids:
                return {"error": f"Model {model_name} not found"}

            # Depois, ler os dados desses modelos
            result = self._execute(
                "ir.model",
                "read",
                model_ids,
                ["name", "model"]
            )

            if not result:
                return {"error": f"Model {model_name} not found"}

            return result[0]
        except Exception as e:
            print(f"Error retrieving model info: {str(e)}", file=os.sys.stderr)
            return {"error": str(e)}

    def get_model_fields(self, model_name):
        """
        Get field definitions for a specific model

        Args:
            model_name: Name of the model (e.g., 'res.partner')

        Returns:
            Dictionary mapping field names to field definitions

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> fields = client.get_model_fields('res.partner')
            >>> print(fields['name']['type'])
            'char'
        """
        try:
            fields_data = self._execute(model_name, "fields_get", [], {})
            return fields_data
        except Exception as e:
            print(f"Error retrieving model fields: {str(e)}", file=os.sys.stderr)
            return {"error": str(e)}

    def search(self, model_name, domain=None, limit=None, offset=None, order=None):
        """
        Search for records

        Args:
            model_name: Name of the model (e.g., 'res.partner')
            domain: Search domain (e.g., [('is_company', '=', True)])
            limit: Maximum number of records to return
            offset: Number of records to skip
            order: Sorting order (e.g., 'name ASC, id DESC')

        Returns:
            List of record IDs

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> ids = client.search('res.partner', [('is_company', '=', True)], limit=5)
            >>> print(ids)
            [1, 3, 4, 5, 7]
        """
        try:
            if domain is None:
                domain = []

            # Preparar os argumentos para a chamada
            args = [domain]

            # Preparar os argumentos nomeados
            kwargs = {}
            if limit is not None:
                kwargs['limit'] = limit
            if offset is not None:
                kwargs['offset'] = offset
            if order is not None:
                kwargs['order'] = order

            # Chamar o método search diretamente via execute_kw
            result = self._models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model_name,
                'search',
                args,
                kwargs
            )
            return result
        except Exception as e:
            print(f"Error searching records: {str(e)}", file=os.sys.stderr)
            return []

    def read_records(self, model_name, ids, fields=None):
        """
        Read data of records by IDs

        Args:
            model_name: Name of the model (e.g., 'res.partner')
            ids: List of record IDs to read
            fields: List of field names to return (None for all)

        Returns:
            List of dictionaries with the requested records

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> records = client.read_records('res.partner', [1])
            >>> print(records[0]['name'])
            'YourCompany'
        """
        try:
            # Preparar os argumentos para a chamada
            args = [ids]

            # Preparar os argumentos nomeados
            kwargs = {}
            if fields is not None:
                # No Odoo 14, o parâmetro 'fields' é passado como segundo argumento posicional
                args.append(fields)

            # Chamar o método read diretamente via execute_kw
            result = self._models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model_name,
                'read',
                args,
                kwargs
            )
            return result
        except Exception as e:
            print(f"Error reading records: {str(e)}", file=os.sys.stderr)
            return []

    def create(self, model_name, values):
        """
        Create a new record

        Args:
            model_name: Name of the model (e.g., 'res.partner')
            values: Dictionary of field values for the new record

        Returns:
            ID of the created record

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> new_id = client.create('res.partner', {'name': 'New Partner'})
            >>> print(new_id)
            42
        """
        try:
            result = self._execute(model_name, "create", values)
            return result
        except Exception as e:
            print(f"Error creating record: {str(e)}", file=os.sys.stderr)
            raise

    def write(self, model_name, record_id, values):
        """
        Update an existing record

        Args:
            model_name: Name of the model (e.g., 'res.partner')
            record_id: ID of the record to update
            values: Dictionary of field values to update

        Returns:
            Boolean indicating success

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> success = client.write('res.partner', 42, {'name': 'Updated Name'})
            >>> print(success)
            True
        """
        try:
            result = self._execute(model_name, "write", [record_id], values)
            return result
        except Exception as e:
            print(f"Error updating record: {str(e)}", file=os.sys.stderr)
            raise

    def unlink(self, model_name, record_id):
        """
        Delete a record

        Args:
            model_name: Name of the model (e.g., 'res.partner')
            record_id: ID of the record to delete

        Returns:
            Boolean indicating success

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> success = client.unlink('res.partner', 42)
            >>> print(success)
            True
        """
        try:
            result = self._execute(model_name, "unlink", [record_id])
            return result
        except Exception as e:
            print(f"Error deleting record: {str(e)}", file=os.sys.stderr)
            raise

    def execute_kw(self, model_name, method, args=None, kwargs=None):
        """
        Execute a method with keyword arguments

        Args:
            model_name: Name of the model (e.g., 'res.partner')
            method: Method name to execute
            args: Positional arguments (optional)
            kwargs: Keyword arguments (optional)

        Returns:
            Result of the method execution

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> result = client.execute_kw('res.partner', 'check_access_rights', ['read'], {'raise_exception': False})
            >>> print(result)
            True
        """
        try:
            args = args or []
            kwargs = kwargs or {}
            result = self._models.execute_kw(self.db, self.uid, self.password, model_name, method, args, kwargs)
            return result
        except Exception as e:
            print(f"Error executing method: {str(e)}", file=os.sys.stderr)
            raise

    def search_read(self, model_name, domain=None, fields=None, limit=None, offset=None, order=None):
        """
        Search and read records in one operation

        Args:
            model_name: Name of the model (e.g., 'res.partner')
            domain: Search domain (e.g., [('is_company', '=', True)])
            fields: List of field names to return (None for all)
            limit: Maximum number of records to return
            offset: Number of records to skip
            order: Sorting order (e.g., 'name ASC, id DESC')

        Returns:
            List of dictionaries with the requested records

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> records = client.search_read('res.partner', [('is_company', '=', True)], ['name', 'email'], limit=5)
            >>> for record in records:
            ...     print(f"{record['id']}: {record['name']}")
            1: YourCompany
        """
        try:
            if domain is None:
                domain = []

            # Primeiro, buscar os IDs dos registros
            search_kwargs = {}
            if limit is not None:
                search_kwargs['limit'] = limit
            if offset is not None:
                search_kwargs['offset'] = offset
            if order is not None:
                search_kwargs['order'] = order

            record_ids = self._execute(model_name, "search", domain, search_kwargs)

            if not record_ids:
                return []

            # Depois, ler os dados desses registros
            read_kwargs = {}
            if fields is not None:
                read_kwargs['fields'] = fields

            result = self._execute(model_name, "read", record_ids, read_kwargs)
            return result
        except Exception as e:
            print(f"Error in search_read: {str(e)}", file=os.sys.stderr)
            return []


class RedirectTransport(xmlrpc.client.Transport):
    """Transport that adds timeout, SSL verification, and redirect handling"""

    def __init__(
        self, timeout=10, use_https=True, verify_ssl=True, max_redirects=5, proxy=None
    ):
        super().__init__()
        self.timeout = timeout
        self.use_https = use_https
        self.verify_ssl = verify_ssl
        self.max_redirects = max_redirects
        self.proxy = proxy or os.environ.get("HTTP_PROXY")

        if use_https and not verify_ssl:
            import ssl

            self.context = ssl._create_unverified_context()

    def make_connection(self, host):
        if self.proxy:
            proxy_url = urllib.parse.urlparse(self.proxy)
            connection = http.client.HTTPConnection(
                proxy_url.hostname, proxy_url.port, timeout=self.timeout
            )
            connection.set_tunnel(host)
        else:
            if self.use_https and not self.verify_ssl:
                connection = http.client.HTTPSConnection(
                    host, timeout=self.timeout, context=self.context
                )
            else:
                if self.use_https:
                    connection = http.client.HTTPSConnection(
                        host, timeout=self.timeout
                    )
                else:
                    connection = http.client.HTTPConnection(
                        host, timeout=self.timeout
                    )
        return connection

    def request(self, host, handler, request_body, verbose=0):
        """Send request, handle redirects"""
        redirects = 0
        while redirects < self.max_redirects:
            try:
                return super().request(host, handler, request_body, verbose)
            except http.client.HTTPException as e:
                if hasattr(e, "status") and e.status in (301, 302, 303, 307, 308):
                    redirects += 1
                    location = e.headers.get("Location")
                    if location:
                        parsed = urllib.parse.urlparse(location)
                        if parsed.netloc:
                            host = parsed.netloc
                        handler = parsed.path
                        if parsed.query:
                            handler += "?" + parsed.query
                    else:
                        raise
                else:
                    raise
            except Exception:
                raise
        raise xmlrpc.client.ProtocolError(
            host + handler, 500, "Too many redirects", {}
        )


def get_odoo_client(config=None):
    """
    Create an Odoo client from configuration or environment variables

    ATENÇÃO: Esta função é destinada apenas para desenvolvimento e testes.
    Em produção, sempre use get_odoo_client_for_account() com o DomainManager.

    Args:
        config: Dictionary with Odoo configuration (optional)
            Expected keys: url, db, username, password, timeout, verify_ssl

    Returns:
        OdooClient instance or None if required configuration is missing
    """
    if config is None:
        config = {}

    # Get configuration from environment variables if not provided in config
    url = config.get("url", os.environ.get("ODOO_URL"))
    db = config.get("db", os.environ.get("ODOO_DB"))
    username = config.get("username", os.environ.get("ODOO_USERNAME"))
    password = config.get("password", os.environ.get("ODOO_PASSWORD"))

    # Verificar se as configurações obrigatórias estão presentes
    if not all([url, db, username, password]):
        print("AVISO: Configurações de Odoo incompletas. Verifique as variáveis de ambiente ou forneça um dicionário de configuração completo.", file=os.sys.stderr)
        return None

    # Converter timeout para inteiro
    timeout_str = config.get("timeout", os.environ.get("ODOO_TIMEOUT", "30"))
    timeout = int(timeout_str) if isinstance(timeout_str, str) else timeout_str

    # Converter verify_ssl para booleano
    verify_ssl_value = config.get("verify_ssl", os.environ.get("ODOO_VERIFY_SSL", "False"))
    if isinstance(verify_ssl_value, str):
        verify_ssl = verify_ssl_value.lower() in ("true", "1", "yes")
    else:
        verify_ssl = bool(verify_ssl_value)

    # Create client
    client = OdooClient(
        url=url,
        db=db,
        username=username,
        password=password,
        timeout=timeout,
        verify_ssl=verify_ssl,
    )

    return client


def get_odoo_client_for_account(domain_name=None, account_id=None, domain_manager=None):
    """
    Create an Odoo client for a specific account

    Args:
        domain_name: Domain name to get credentials for
        account_id: Account ID to get credentials for
        domain_manager: Domain manager instance to load configurations

    Returns:
        OdooClient instance or None if credentials not found
    """
    # Se não temos um domain_manager, não podemos carregar configurações específicas
    if not domain_manager:
        return get_odoo_client()

    try:
        # Tentar carregar a configuração da conta
        if domain_name and account_id:
            account_config = domain_manager.domain_loader.load_client_config(domain_name, account_id)
            if account_config:
                # Extrair a configuração do Odoo da conta
                odoo_config = account_config.get("integrations", {}).get("odoo", {})
                if odoo_config and all(k in odoo_config for k in ["url", "db", "username", "password"]):
                    # Criar cliente com as credenciais da conta
                    return OdooClient(
                        url=odoo_config["url"],
                        db=odoo_config["db"],
                        username=odoo_config["username"],
                        password=odoo_config["password"],
                        timeout=int(odoo_config.get("timeout", 30)),
                        verify_ssl=odoo_config.get("verify_ssl", False)
                    )

        # Se não encontrou configuração específica da conta ou não foi fornecido domain_name/account_id,
        # tentar usar a configuração do domínio
        if domain_name:
            domain_config = domain_manager.get_domain_config(domain_name)
            if domain_config:
                odoo_config = domain_config.get("integrations", {}).get("odoo", {})
                if odoo_config and all(k in odoo_config for k in ["url", "db", "username", "password"]):
                    # Criar cliente com as credenciais do domínio
                    return OdooClient(
                        url=odoo_config["url"],
                        db=odoo_config["db"],
                        username=odoo_config["username"],
                        password=odoo_config["password"],
                        timeout=int(odoo_config.get("timeout", 30)),
                        verify_ssl=odoo_config.get("verify_ssl", False)
                    )
    except Exception as e:
        print(f"Error creating Odoo client for account {account_id}: {str(e)}", file=os.sys.stderr)

    # Se não conseguiu criar o cliente com configurações específicas, usar o cliente padrão
    return get_odoo_client()
