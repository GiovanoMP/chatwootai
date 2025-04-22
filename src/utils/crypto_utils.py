"""
Utilitários de criptografia para o sistema.
Fornece funções para criptografar e descriptografar senhas e verificar assinaturas.
"""

import os
import base64
import hmac
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

# Chave mestra para criptografia - em produção, deve vir de variável de ambiente
# Usando um valor fixo para desenvolvimento, mas em produção deve ser substituído
# por uma chave segura armazenada em variável de ambiente
MASTER_KEY = os.environ.get('ENCRYPTION_MASTER_KEY', 'YmFzZTY0X2VuY29kZWRfMzJfYnl0ZXNfa2V5X2Zvcl9mZXJuZXQ=')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'webhook_secret_for_hmac_signature')

# Prefixo para identificar senhas criptografadas
ENCRYPTED_PREFIX = "encrypted:"

def get_encryption_key():
    """
    Obtém a chave de criptografia Fernet.
    Em produção, esta chave deve vir de uma variável de ambiente ou serviço de gestão de segredos.
    """
    try:
        # Verificar se a chave é válida para Fernet (32 bytes base64-encoded)
        key = MASTER_KEY
        # Tentar criar um objeto Fernet com a chave para validar
        Fernet(key)
        return key
    except Exception as e:
        logger.warning(f"Chave de criptografia inválida ou não encontrada: {e}")
        logger.warning("Gerando nova chave de criptografia. Em produção, use uma chave fixa!")
        # Gerar uma nova chave apenas para desenvolvimento
        return Fernet.generate_key().decode()

def encrypt_password(password):
    """
    Criptografa uma senha usando Fernet (criptografia simétrica).
    
    Args:
        password: Senha em texto plano
        
    Returns:
        Senha criptografada com prefixo para identificação
    """
    if not password:
        return password
        
    # Se a senha já estiver criptografada, retornar como está
    if password.startswith(ENCRYPTED_PREFIX):
        return password
        
    try:
        key = get_encryption_key()
        cipher_suite = Fernet(key)
        encrypted_password = cipher_suite.encrypt(password.encode())
        # Adicionar prefixo para identificar que está criptografada
        return f"{ENCRYPTED_PREFIX}{encrypted_password.decode()}"
    except Exception as e:
        logger.error(f"Erro ao criptografar senha: {e}")
        # Em caso de erro, retornar a senha original
        # Em produção, considere lançar uma exceção em vez de retornar a senha
        return password

def decrypt_password(encrypted_password):
    """
    Descriptografa uma senha criptografada com Fernet.
    
    Args:
        encrypted_password: Senha criptografada com prefixo
        
    Returns:
        Senha em texto plano
    """
    if not encrypted_password:
        return encrypted_password
        
    # Se não tiver o prefixo, pode não estar criptografada
    if not encrypted_password.startswith(ENCRYPTED_PREFIX):
        return encrypted_password
        
    try:
        # Remover o prefixo
        encrypted_data = encrypted_password[len(ENCRYPTED_PREFIX):]
        key = get_encryption_key()
        cipher_suite = Fernet(key)
        decrypted_password = cipher_suite.decrypt(encrypted_data.encode())
        return decrypted_password.decode()
    except Exception as e:
        logger.error(f"Erro ao descriptografar senha: {e}")
        # Em caso de erro, retornar a senha criptografada
        # Em produção, considere lançar uma exceção
        return encrypted_password

def generate_hmac_signature(payload):
    """
    Gera uma assinatura HMAC para um payload.
    
    Args:
        payload: Payload em formato string (geralmente JSON serializado)
        
    Returns:
        Assinatura HMAC em formato hexadecimal
    """
    try:
        signature = hmac.new(
            WEBHOOK_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    except Exception as e:
        logger.error(f"Erro ao gerar assinatura HMAC: {e}")
        return ""

def verify_hmac_signature(payload, signature):
    """
    Verifica se uma assinatura HMAC é válida para um payload.
    
    Args:
        payload: Payload em formato string (geralmente JSON serializado)
        signature: Assinatura HMAC em formato hexadecimal
        
    Returns:
        True se a assinatura for válida, False caso contrário
    """
    try:
        expected_signature = generate_hmac_signature(payload)
        # Usar comparação de tempo constante para evitar timing attacks
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Erro ao verificar assinatura HMAC: {e}")
        return False
