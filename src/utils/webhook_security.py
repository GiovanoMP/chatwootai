import hmac
import hashlib
import os
import logging
import json

logger = logging.getLogger(__name__)

class WebhookSecurity:
    """
    Classe para lidar com a segurança dos webhooks.
    Implementa assinatura HMAC para verificar a autenticidade dos payloads.
    """

    def __init__(self):
        """
        Inicializa a classe de segurança do webhook.
        Obtém a chave secreta da variável de ambiente WEBHOOK_SECRET_KEY.
        """
        self.secret_key = os.environ.get('WEBHOOK_SECRET_KEY')

        if not self.secret_key:
            logger.warning("WEBHOOK_SECRET_KEY não configurada. Autenticação de webhook desativada.")
        else:
            logger.info("Segurança de webhook inicializada com sucesso.")

    def generate_signature(self, payload):
        """
        Gera uma assinatura HMAC para o payload.

        Args:
            payload: O payload a ser assinado (dict ou string)

        Returns:
            str: A assinatura HMAC em formato hexadecimal
        """
        if not self.secret_key:
            logger.warning("Tentativa de gerar assinatura sem chave secreta configurada.")
            return None

        # Converter o payload para string se for um dicionário
        if isinstance(payload, dict):
            payload_str = json.dumps(payload, sort_keys=True)
        else:
            payload_str = payload

        # Gerar a assinatura HMAC
        signature = hmac.new(
            self.secret_key.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    def verify_signature(self, payload_str, signature):
        """
        Verifica a assinatura HMAC do payload.

        Args:
            payload_str: O payload como string
            signature: A assinatura HMAC a ser verificada

        Returns:
            bool: True se a assinatura for válida, False caso contrário
        """
        if not self.secret_key:
            logger.warning("Tentativa de verificar assinatura sem chave secreta configurada.")
            return True  # Permitir sem verificação se a chave não estiver configurada

        if not signature:
            logger.warning("Tentativa de verificar assinatura sem assinatura fornecida.")
            return False

        # Gerar a assinatura esperada
        expected = hmac.new(
            self.secret_key.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        # Comparação segura contra timing attacks
        is_valid = hmac.compare_digest(expected, signature)

        if not is_valid:
            logger.warning(f"Assinatura de webhook inválida. Esperada: {expected[:10]}..., Recebida: {signature[:10]}...")

        return is_valid

# Instância global para uso em todo o sistema
webhook_security = WebhookSecurity()
