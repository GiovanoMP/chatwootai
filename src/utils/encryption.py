from cryptography.fernet import Fernet
import os
import base64
import logging

logger = logging.getLogger(__name__)

class CredentialEncryption:
    def __init__(self):
        # Obter chave de criptografia da variável de ambiente
        env_key = os.environ.get('CREDENTIAL_ENCRYPTION_KEY')
        
        if env_key:
            try:
                # Garantir que a chave esteja no formato correto
                padded_key = env_key + '=' * (-len(env_key) % 4)
                # Verificar se a chave decodificada tem o tamanho correto
                decoded_key = base64.urlsafe_b64decode(padded_key)
                if len(decoded_key) != 32:
                    raise ValueError("Chave de criptografia inválida: tamanho incorreto")
                
                self.key = env_key
                logger.info("Usando chave de criptografia da variável de ambiente")
            except Exception as e:
                logger.error(f"Erro com a chave de criptografia: {e}")
                self.key = Fernet.generate_key().decode()
                logger.warning(f"Gerada nova chave de criptografia: {self.key}")
                logger.warning("Adicione esta chave ao seu arquivo .env como CREDENTIAL_ENCRYPTION_KEY")
        else:
            # Se não houver chave no ambiente, gerar uma nova
            self.key = Fernet.generate_key().decode()
            logger.warning(f"Nenhuma chave de criptografia encontrada no ambiente. Gerada nova chave: {self.key}")
            logger.warning("Adicione esta chave ao seu arquivo .env como CREDENTIAL_ENCRYPTION_KEY")
        
        # Garantir que a chave esteja no formato correto para o Fernet
        padded_key = self.key + '=' * (-len(self.key) % 4)
        self.cipher_suite = Fernet(padded_key.encode())
    
    def encrypt(self, text):
        """Criptografa um texto"""
        if not text:
            return text
        
        try:
            # Prefixar valores criptografados para identificação
            encrypted = self.cipher_suite.encrypt(text.encode())
            return f"ENC:{base64.urlsafe_b64encode(encrypted).decode()}"
        except Exception as e:
            logger.error(f"Erro ao criptografar: {e}")
            return text
    
    def decrypt(self, text):
        """Descriptografa um texto"""
        if not text or not isinstance(text, str):
            return text
        
        # Verificar se o texto está criptografado
        if text.startswith("ENC:"):
            try:
                # Remover prefixo e descriptografar
                encrypted = base64.urlsafe_b64decode(text[4:])
                return self.cipher_suite.decrypt(encrypted).decode()
            except Exception as e:
                logger.error(f"Erro ao descriptografar: {e}")
                return text
        
        # Se não estiver criptografado, retornar como está
        return text

# Instância global para uso em todo o sistema
credential_encryption = CredentialEncryption()
