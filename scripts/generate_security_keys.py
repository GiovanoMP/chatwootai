#!/usr/bin/env python3
from cryptography.fernet import Fernet
import secrets
import base64

def generate_security_keys():
    # Gerar chave de criptografia para credenciais
    encryption_key = Fernet.generate_key().decode()
    
    # Gerar segredo para assinatura de webhook
    webhook_secret = secrets.token_hex(32)
    
    print("\n=== CHAVES DE SEGURANÇA GERADAS ===")
    print(f"CREDENTIAL_ENCRYPTION_KEY={encryption_key}")
    print(f"WEBHOOK_SECRET_KEY={webhook_secret}")
    print("\nAdicione estas variáveis ao seu arquivo .env")
    print("IMPORTANTE: Mantenha estas chaves seguras e não as comite no repositório!")

if __name__ == "__main__":
    generate_security_keys()
