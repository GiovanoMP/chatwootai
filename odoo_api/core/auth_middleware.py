"""
Middleware de autenticação para APIs do sistema Odoo-AI.

Este módulo implementa o middleware de autenticação baseado em token
para proteger as APIs do sistema e garantir a identificação correta
dos clientes em um ambiente multi-tenant.
"""

import logging
import os
import yaml
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from odoo_api.config.settings import settings

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware para autenticação baseada em token.
    
    Valida o token de autorização e extrai o account_id correspondente,
    armazenando-o no estado da requisição para uso pelos endpoints.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Processa a requisição, validando o token de autorização.
        
        Args:
            request: Requisição HTTP
            call_next: Próxima função a ser chamada no pipeline
            
        Returns:
            Resposta HTTP
        """
        # Verificar se é uma rota de API (ignorar rotas de documentação, etc.)
        if request.url.path.startswith("/api/v1/"):
            # Verificar se é uma rota pública (como health check)
            if request.url.path in ["/api/v1/health", "/api/v1/credentials/webhook"]:
                return await call_next(request)
                
            # Obter o token de autorização
            auth_header = request.headers.get("Authorization")
            
            if not auth_header or not auth_header.startswith("Bearer "):
                # Se não tiver token, verificar se é uma requisição de desenvolvimento
                if settings.ENVIRONMENT == "development" and "account_id" in request.query_params:
                    # Em desenvolvimento, permitir o uso do account_id na URL (para compatibilidade)
                    account_id = request.query_params.get("account_id")
                    request.state.account_id = account_id
                    logger.warning(f"Usando account_id da URL em ambiente de desenvolvimento: {account_id}")
                    return await call_next(request)
                
                # Em produção, exigir o token
                logger.warning("Requisição sem token de autorização")
                return HTTPException(
                    status_code=401,
                    detail={
                        "success": False,
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Token de autorização não fornecido",
                        },
                        "meta": {
                            "request_id": getattr(request.state, "request_id", "unknown"),
                        },
                    },
                )
            
            # Extrair o token
            token = auth_header.replace("Bearer ", "")
            
            # Validar o token e obter o account_id
            account_id = await self._validate_token(token)
            
            if not account_id:
                logger.warning(f"Token inválido: {token}")
                return HTTPException(
                    status_code=401,
                    detail={
                        "success": False,
                        "error": {
                            "code": "INVALID_TOKEN",
                            "message": "Token de autorização inválido",
                        },
                        "meta": {
                            "request_id": getattr(request.state, "request_id", "unknown"),
                        },
                    },
                )
            
            # Armazenar o account_id no estado da requisição
            request.state.account_id = account_id
            logger.info(f"Requisição autenticada para account_id: {account_id}")
        
        # Continuar o processamento da requisição
        return await call_next(request)
    
    async def _validate_token(self, token: str) -> Optional[str]:
        """
        Valida o token de autorização e retorna o account_id correspondente.
        
        Args:
            token: Token de autorização
            
        Returns:
            account_id correspondente ao token ou None se o token for inválido
        """
        # Verificar todos os arquivos de configuração em config/domains/*/account_*/config.yaml
        domains_dir = os.path.join(settings.CONFIG_DIR, "domains")
        
        if not os.path.exists(domains_dir):
            logger.error(f"Diretório de domínios não encontrado: {domains_dir}")
            return None
        
        # Percorrer todos os domínios
        for domain in os.listdir(domains_dir):
            domain_dir = os.path.join(domains_dir, domain)
            
            if not os.path.isdir(domain_dir):
                continue
            
            # Percorrer todos os accounts no domínio
            for account in os.listdir(domain_dir):
                account_dir = os.path.join(domain_dir, account)
                
                if not os.path.isdir(account_dir):
                    continue
                
                # Verificar o arquivo de configuração
                config_file = os.path.join(account_dir, "config.yaml")
                
                if not os.path.exists(config_file):
                    continue
                
                try:
                    # Carregar a configuração
                    with open(config_file, "r") as f:
                        config = yaml.safe_load(f)
                    
                    # Verificar se o token existe como chave no arquivo
                    if token in config:
                        logger.info(f"Token válido para account_id: {account}")
                        return account
                except Exception as e:
                    logger.error(f"Erro ao carregar configuração de {config_file}: {e}")
        
        # Se não encontrou o token em nenhum arquivo, verificar o ambiente
        if settings.ENVIRONMENT == "development":
            # Em desenvolvimento, extrair o account_id do token (se o token tiver o formato account_id-*)
            if "-" in token:
                account_id = token.split("-")[0]
                logger.warning(f"Usando account_id extraído do token em ambiente de desenvolvimento: {account_id}")
                return account_id
        
        return None
