# Implementações de Segurança no Sistema Integrado Odoo-AI

Este documento descreve as implementações de segurança adicionadas ao sistema integrado Odoo-AI, focando na proteção de dados sensíveis e na autenticação de comunicações entre sistemas.


Conclusão sobre o estado atual

O sistema Odoo-AI não pode ser considerado completamente seguro no estado atual. Embora tenha implementado medidas fundamentais de segurança (criptografia de credenciais e assinatura HMAC), várias vulnerabilidades críticas ainda estão presentes:

A ausência de HTTPS expõe todas as comunicações a interceptações
A falta de autenticação robusta para todas as APIs
A integração insegura com o Chatwoot
A ausência de mecanismos de defesa contra ataques comuns (rate limiting)

Recomendações prioritárias:

Implementar HTTPS imediatamente antes de qualquer implantação em produção
Estender as medidas de segurança para o webhook do Chatwoot
Implementar rate limiting para prevenir ataques de força bruta
Adicionar autenticação JWT para APIs que não usam webhooks
Estabelecer um sistema de logs de auditoria para todas as operações sensíveis


## Índice

1. [Visão Geral](#visão-geral)
2. [Implementações de Segurança](#implementações-de-segurança)
   - [Criptografia de Credenciais](#criptografia-de-credenciais)
   - [Assinatura HMAC para Webhooks](#assinatura-hmac-para-webhooks)
3. [Casos de Uso](#casos-de-uso)
4. [Como Estender para Outros Módulos](#como-estender-para-outros-módulos)
5. [Futuras Melhorias de Segurança](#futuras-melhorias-de-segurança)
6. [Limitações Atuais](#limitações-atuais)

## Visão Geral

O sistema integrado Odoo-AI é uma plataforma que conecta o ERP Odoo com um sistema de IA, permitindo a sincronização de dados e a automação de processos usando inteligência artificial. A segurança é um aspecto crítico deste sistema, especialmente porque ele lida com dados sensíveis de empresas e credenciais de acesso a sistemas externos.

As implementações de segurança descritas neste documento foram projetadas para:

1. Proteger credenciais sensíveis armazenadas no sistema
2. Garantir a autenticidade das comunicações entre o Odoo e o sistema de IA
3. Prevenir acesso não autorizado a dados e funcionalidades

## Implementações de Segurança

### Criptografia de Credenciais

#### Descrição

O módulo `credential_encryption` implementa criptografia simétrica (AES-256) para proteger credenciais sensíveis armazenadas nos arquivos YAML de configuração. As credenciais são criptografadas antes de serem armazenadas e descriptografadas apenas quando necessário para uso.

#### Arquivos Relevantes

- `src/utils/encryption.py`: Implementação da criptografia/descriptografia
- `src/webhook/webhook_handler.py`: Uso da criptografia ao receber credenciais via webhook
- `odoo_api/core/odoo_connector.py`: Descriptografia das credenciais antes do uso

#### Funcionamento

1. **Criptografia**: Quando credenciais são recebidas via webhook do Odoo, elas são criptografadas antes de serem armazenadas nos arquivos YAML.
   ```python
   encrypted_password = credential_encryption.encrypt(credentials.get("odoo_password"))
   creds_config["credentials"][token] = encrypted_password
   ```

2. **Descriptografia**: Quando as credenciais são necessárias para conectar ao Odoo, elas são descriptografadas.
   ```python
   if ENCRYPTION_AVAILABLE and isinstance(credential_value, str) and credential_value.startswith("ENC:"):
       decrypted_value = credential_encryption.decrypt(credential_value)
       return decrypted_value
   ```

3. **Chave de Criptografia**: A chave é armazenada como variável de ambiente `ENCRYPTION_KEY`, não no código-fonte.

### Assinatura HMAC para Webhooks

#### Descrição

O módulo `webhook_security` implementa assinatura HMAC-SHA256 para verificar a autenticidade dos payloads recebidos via webhook. Isso garante que apenas sistemas autorizados (como o Odoo) possam enviar dados para o sistema de IA.

#### Arquivos Relevantes

- `src/utils/webhook_security.py`: Implementação da geração e verificação de assinaturas
- `src/webhook/routes.py`: Verificação da assinatura nos webhooks recebidos
- `addons/ai_credentials_manager/models/ai_credentials.py`: Geração da assinatura no lado do Odoo
- `addons/business_rules/controllers/sync_controller.py`: Geração da assinatura para sincronização de regras de negócio

#### Funcionamento

1. **Geração da Assinatura (Odoo)**:
   ```python
   payload_str = json.dumps(payload, sort_keys=True)
   signature = hmac.new(
       webhook_secret.encode(),
       payload_str.encode(),
       hashlib.sha256
   ).hexdigest()
   headers = {
       'Content-Type': 'application/json',
       'X-Webhook-Signature': signature
   }
   ```

2. **Verificação da Assinatura (Sistema de IA)**:
   ```python
   if signature:
       if not webhook_security.verify_signature(sorted_body_str, signature):
           raise HTTPException(status_code=401, detail="Assinatura inválida")
   ```

3. **Chave Secreta**: A chave secreta é armazenada como parâmetro de sistema no Odoo e como variável de ambiente `WEBHOOK_SECRET_KEY` no sistema de IA.

## Casos de Uso

### Criptografia de Credenciais

- **Armazenamento Seguro de Senhas**: Protege senhas de acesso ao Odoo e outros sistemas.
- **Proteção de Tokens de API**: Criptografa tokens de acesso para Facebook, Instagram, Mercado Livre, etc.
- **Auditoria de Segurança**: Facilita a conformidade com regulamentações de segurança de dados.

### Assinatura HMAC para Webhooks

- **Prevenção de Ataques de Falsificação**: Impede que atacantes enviem dados falsos para o sistema.
- **Verificação de Integridade**: Garante que os dados não foram alterados durante a transmissão.
- **Autenticação de Origem**: Confirma que os dados vieram realmente do Odoo.

## Como Estender para Outros Módulos

Para estender estas implementações de segurança para novos módulos Odoo que se comunicam com o sistema de IA, siga estas diretrizes:

### Para Criptografia de Credenciais

1. **No Módulo Odoo**:
   - Envie as credenciais sensíveis via webhook para o sistema de IA.
   - Não armazene credenciais em texto claro no banco de dados do Odoo.

   ```python
   def sync_credentials(self):
       credentials = {
           "module_password": self.password,
           "module_api_key": self.api_key,
           # Outras credenciais sensíveis
       }
       
       payload = {
           "event": "credentials_sync",
           "account_id": self.account_id,
           "credentials": credentials,
           # Outros dados não sensíveis
       }
       
       # Gerar assinatura HMAC
       webhook_secret = self.env['ir.config_parameter'].sudo().get_param('webhook_secret_key', '')
       if webhook_secret:
           import hmac, hashlib, json
           payload_str = json.dumps(payload, sort_keys=True)
           signature = hmac.new(
               webhook_secret.encode(),
               payload_str.encode(),
               hashlib.sha256
           ).hexdigest()
           headers = {
               'Content-Type': 'application/json',
               'X-Webhook-Signature': signature
           }
       else:
           headers = {'Content-Type': 'application/json'}
       
       # Enviar para o sistema de IA
       response = requests.post(
           webhook_url,
           headers=headers,
           json=payload,
           timeout=30
       )
   ```

2. **No Sistema de IA**:
   - Adicione o processamento das novas credenciais no `webhook_handler.py`.
   - Use o módulo `credential_encryption` para criptografar as credenciais.

   ```python
   # No webhook_handler.py
   if credentials.get("module_password"):
       encrypted_password = credential_encryption.encrypt(credentials.get("module_password"))
       creds_config["credentials"][f"module_pwd_{account_id}"] = encrypted_password
       logger.info(f"Senha do módulo criptografada salva para {account_id}")
   
   if credentials.get("module_api_key"):
       encrypted_key = credential_encryption.encrypt(credentials.get("module_api_key"))
       creds_config["credentials"][f"module_key_{account_id}"] = encrypted_key
       logger.info(f"API key do módulo criptografada salva para {account_id}")
   ```

3. **Para Usar as Credenciais**:
   - Implemente a descriptografia no código que precisa usar as credenciais.

   ```python
   def get_module_credentials(self, account_id):
       password_ref = f"module_pwd_{account_id}"
       api_key_ref = f"module_key_{account_id}"
       
       password = self._get_credential_by_ref(password_ref, account_id)
       api_key = self._get_credential_by_ref(api_key_ref, account_id)
       
       return {
           "password": password,
           "api_key": api_key
       }
   ```

### Para Assinatura HMAC de Webhooks

1. **No Módulo Odoo**:
   - Adicione a geração de assinatura HMAC para todos os endpoints que enviam dados para o sistema de IA.

   ```python
   def send_data_to_ai_system(self, data, endpoint):
       # Preparar payload
       payload = {
           "account_id": self.account_id,
           "data": data
       }
       
       # Gerar assinatura HMAC
       webhook_secret = self.env['ir.config_parameter'].sudo().get_param('webhook_secret_key', '')
       if webhook_secret:
           import hmac, hashlib, json
           payload_str = json.dumps(payload, sort_keys=True)
           signature = hmac.new(
               webhook_secret.encode(),
               payload_str.encode(),
               hashlib.sha256
           ).hexdigest()
           headers = {
               'Content-Type': 'application/json',
               'X-Webhook-Signature': signature
           }
       else:
           headers = {'Content-Type': 'application/json'}
       
       # Enviar para o sistema de IA
       response = requests.post(
           f"{ai_system_url}/{endpoint}",
           headers=headers,
           json=payload,
           timeout=30
       )
   ```

2. **No Sistema de IA**:
   - Adicione a verificação de assinatura HMAC para todos os novos endpoints.

   ```python
   @router.post("/api/v1/new-module/data")
   async def receive_module_data(request: Request):
       # Verificar assinatura
       signature = request.headers.get('x-webhook-signature')
       body_bytes = await request.body()
       body_str = body_bytes.decode()
       
       if signature:
           logger.info(f"Verificando assinatura do webhook: {signature[:10]}...")
           data_json = json.loads(body_str)
           sorted_body_str = json.dumps(data_json, sort_keys=True)
           
           if not webhook_security.verify_signature(sorted_body_str, signature):
               logger.warning("Assinatura de webhook inválida")
               raise HTTPException(status_code=401, detail="Assinatura inválida")
           logger.info("Assinatura de webhook válida")
       else:
           logger.warning("Webhook recebido sem assinatura")
       
       # Processar os dados
       data = json.loads(body_str)
       # ...
   ```

## Futuras Melhorias de Segurança

### 1. Implementação de HTTPS

Atualmente, o sistema está rodando localmente sem HTTPS. Para ambientes de produção, é essencial implementar HTTPS para criptografar todas as comunicações entre o Odoo e o sistema de IA.

```bash
# Exemplo de configuração com Nginx como proxy reverso com SSL
server {
    listen 443 ssl;
    server_name ai-system.example.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Rotação Automática de Chaves

Implementar rotação automática de chaves de criptografia e segredos de webhook para aumentar a segurança.

```python
def rotate_encryption_key():
    """
    Gera uma nova chave de criptografia e re-criptografa todas as credenciais.
    """
    # Gerar nova chave
    new_key = os.urandom(32).hex()
    
    # Obter todas as credenciais atuais
    all_credentials = {}
    for domain_dir in os.listdir("config/domains"):
        # Percorrer todos os arquivos de credenciais e descriptografar com a chave antiga
        # Re-criptografar com a nova chave
        # Salvar os arquivos atualizados
    
    # Atualizar a variável de ambiente
    os.environ["ENCRYPTION_KEY"] = new_key
    
    # Salvar a nova chave em um local seguro
```

### 3. Implementação de Rate Limiting

Adicionar rate limiting para prevenir ataques de força bruta e DoS.

```python
# Usando o middleware do FastAPI
from fastapi import FastAPI, Request
import time
from fastapi.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Limpar entradas antigas
        self.requests = {ip: times for ip, times in self.requests.items() 
                         if any(t > current_time - self.window_seconds for t in times)}
        
        # Verificar limite de requisições
        if client_ip in self.requests:
            self.requests[client_ip] = [t for t in self.requests[client_ip] 
                                       if t > current_time - self.window_seconds]
            if len(self.requests[client_ip]) >= self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"}
                )
            self.requests[client_ip].append(current_time)
        else:
            self.requests[client_ip] = [current_time]
        
        return await call_next(request)

app = FastAPI()
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
```

### 4. Implementação de Autenticação JWT

Adicionar autenticação JWT para APIs que não usam webhooks.

```python
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Configuração
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        account_id: str = payload.get("sub")
        if account_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return account_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@app.post("/api/v1/protected-endpoint")
async def protected_endpoint(account_id: str = Depends(verify_token)):
    # Lógica do endpoint
    return {"account_id": account_id}
```

### 5. Auditoria de Segurança

Implementar logs de auditoria para todas as operações sensíveis.

```python
def audit_log(user_id, action, resource, success, details=None):
    """
    Registra uma ação de auditoria.
    
    Args:
        user_id: ID do usuário ou sistema que realizou a ação
        action: Ação realizada (ex: "login", "access", "modify")
        resource: Recurso afetado (ex: "credentials", "business_rules")
        success: Se a ação foi bem-sucedida
        details: Detalhes adicionais sobre a ação
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "success": success,
        "details": details or {},
        "ip_address": request.client.host if 'request' in locals() else None,
        "user_agent": request.headers.get("user-agent") if 'request' in locals() else None
    }
    
    # Salvar em um arquivo de log seguro ou banco de dados
    with open("logs/audit.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

## Limitações Atuais

### Webhook do Chatwoot

Atualmente, as implementações de segurança (assinatura HMAC e criptografia de credenciais) estão funcionais apenas para a integração com o Odoo. O webhook do Chatwoot ainda não implementa estas medidas de segurança.

Para estender a segurança para o webhook do Chatwoot, seria necessário:

1. Implementar a verificação de assinatura HMAC para mensagens recebidas do Chatwoot
2. Configurar o Chatwoot para enviar assinaturas HMAC com suas requisições
3. Criptografar quaisquer credenciais sensíveis relacionadas ao Chatwoot

```python
# Exemplo de como poderia ser implementado no futuro
@router.post("/webhook/chatwoot")
async def chatwoot_webhook(request: Request):
    # Verificar assinatura
    signature = request.headers.get('x-chatwoot-signature')
    body_bytes = await request.body()
    body_str = body_bytes.decode()
    
    if signature:
        if not webhook_security.verify_signature(body_str, signature):
            raise HTTPException(status_code=401, detail="Assinatura inválida")
    
    # Processar a mensagem do Chatwoot
    data = json.loads(body_str)
    # ...
```

---

## Conclusão

As implementações de segurança descritas neste documento fornecem uma base sólida para proteger dados sensíveis e garantir a autenticidade das comunicações no sistema integrado Odoo-AI. Ao seguir as diretrizes para estender estas implementações para novos módulos e implementar as melhorias futuras sugeridas, o sistema pode atingir um alto nível de segurança adequado para ambientes de produção.

Para quaisquer dúvidas ou sugestões relacionadas à segurança do sistema, entre em contato com a equipe de desenvolvimento.
