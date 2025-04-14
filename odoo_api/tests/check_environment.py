#!/usr/bin/env python3
"""
Script para verificar o ambiente de testes.

Este script verifica se todas as dependências necessárias estão instaladas
e se o ambiente está configurado corretamente para executar os testes.
"""

import os
import sys
import logging
import importlib
import subprocess
from typing import List, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lista de dependências necessárias
REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "httpx",
    "pydantic",
    "redis",
    "qdrant-client",
    "openai",
    "python-dotenv",
    "tenacity",
    "PyYAML"
]

# Lista de serviços necessários
REQUIRED_SERVICES = [
    ("Redis", "redis-cli ping", "PONG"),
    ("Qdrant", "curl -s http://localhost:6333/collections", "collections")
]

def check_packages() -> List[str]:
    """
    Verificar se todas as dependências necessárias estão instaladas.

    Returns:
        Lista de pacotes faltantes
    """
    missing_packages = []

    # Mapeamento de nomes de pacotes para nomes de módulos
    package_to_module = {
        "python-dotenv": "dotenv",
        "PyYAML": "yaml"
    }

    for package in REQUIRED_PACKAGES:
        try:
            # Usar o mapeamento se disponível, caso contrário usar a regra padrão
            module_name = package_to_module.get(package, package.replace("-", "_"))
            importlib.import_module(module_name)
            logger.info(f"✅ Pacote {package} está instalado")
        except ImportError:
            logger.warning(f"❌ Pacote {package} não está instalado")
            missing_packages.append(package)

    return missing_packages

def check_services() -> List[str]:
    """
    Verificar se todos os serviços necessários estão rodando.

    Returns:
        Lista de serviços não disponíveis
    """
    unavailable_services = []

    for service_name, check_command, expected_output in REQUIRED_SERVICES:
        try:
            result = subprocess.run(
                check_command.split(),
                capture_output=True,
                text=True,
                timeout=5
            )

            if expected_output in result.stdout:
                logger.info(f"✅ Serviço {service_name} está rodando")
            else:
                logger.warning(f"❌ Serviço {service_name} não está respondendo corretamente")
                unavailable_services.append(service_name)
        except subprocess.TimeoutExpired:
            logger.warning(f"❌ Serviço {service_name} não respondeu dentro do tempo limite")
            unavailable_services.append(service_name)
        except Exception as e:
            logger.warning(f"❌ Erro ao verificar serviço {service_name}: {e}")
            unavailable_services.append(service_name)

    return unavailable_services

def check_environment_variables() -> List[str]:
    """
    Verificar se todas as variáveis de ambiente necessárias estão definidas.

    Returns:
        Lista de variáveis de ambiente faltantes
    """
    required_env_vars = [
        "OPENAI_API_KEY",
        "REDIS_HOST",
        "REDIS_PORT",
        "QDRANT_HOST",
        "QDRANT_PORT"
    ]

    missing_env_vars = []

    for env_var in required_env_vars:
        if not os.environ.get(env_var):
            logger.warning(f"❌ Variável de ambiente {env_var} não está definida")
            missing_env_vars.append(env_var)
        else:
            logger.info(f"✅ Variável de ambiente {env_var} está definida")

    return missing_env_vars

def main():
    """Verificar o ambiente de testes."""
    logger.info("Verificando o ambiente de testes...")

    # Verificar pacotes
    missing_packages = check_packages()

    # Verificar serviços
    unavailable_services = check_services()

    # Verificar variáveis de ambiente
    missing_env_vars = check_environment_variables()

    # Verificar resultado
    if not missing_packages and not unavailable_services and not missing_env_vars:
        logger.info("✅ Ambiente de testes está configurado corretamente!")
        return 0
    else:
        logger.error("❌ Ambiente de testes não está configurado corretamente!")

        if missing_packages:
            logger.error(f"Pacotes faltantes: {', '.join(missing_packages)}")
            logger.info(f"Instale-os com: pip install {' '.join(missing_packages)}")

        if unavailable_services:
            logger.error(f"Serviços não disponíveis: {', '.join(unavailable_services)}")

        if missing_env_vars:
            logger.error(f"Variáveis de ambiente faltantes: {', '.join(missing_env_vars)}")
            logger.info("Defina-as no arquivo .env ou no ambiente")

        return 1

if __name__ == "__main__":
    sys.exit(main())
