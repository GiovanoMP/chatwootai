# Gerenciador de Credenciais para IA

## Visão Geral

O módulo **Gerenciador de Credenciais para IA** fornece uma solução centralizada e segura para gerenciar todas as credenciais de autenticação utilizadas na integração entre o Odoo e sistemas externos, com foco inicial em sistemas de Inteligência Artificial.

Este módulo foi projetado seguindo os mais altos padrões de segurança, com acesso restrito apenas a administradores do sistema, garantindo que informações sensíveis como tokens, chaves de API e senhas sejam armazenadas de forma segura e centralizada.

## Arquitetura de Integração

O sistema utiliza duas abordagens complementares para integração, dependendo do tipo de operação:

### 1. Caminho de API Direta (Módulos Atuais)

Para operações de vetorização e embedding (módulos atuais como business_rules, semantic_product_description):

```
┌─────────────────┐      ┌───────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                   │      │                 │      │                 │
│  Módulos Odoo   │─────►│  API com          │─────►│  Embedding      │─────►│  Armazenamento  │
│  (Vetorização)  │      │  Autenticação     │      │  Agents         │      │  Vetorial       │
│                 │      │                   │      │                 │      │                 │
└─────────────────┘      └───────────────────┘      └─────────────────┘      └─────────────────┘
```

- Utilizado para operações simples, unidirecionais (Odoo → Sistema de IA)
- Ideal para vetorização e geração de embeddings
- Agentes de embedding definidos em `@odoo_api/embedding_agents/`

### 2. Caminho MCP (Módulos Futuros)

Para operações interativas complexas (futuros módulos como análise de dados, chatbots):

```
┌─────────────────┐      ┌───────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                   │      │                 │      │                 │
│  Módulos Odoo   │─────►│  API com          │─────►│  Sistema de IA  │─────►│  Agentes        │
│  (Interativos)  │      │  Autenticação     │      │  (Crews)        │      │  CrewAI         │
│                 │      │                   │      │                 │      │                 │
└─────────────────┘      └───────────────────┘      └─────────────────┘      └─────────────────┘
                                                                                      │
                                                                                      ▼
                                                                            ┌─────────────────┐
                                                                            │                 │
                                                                            │  DataProxyAgent │
                                                                            │                 │
                                                                            └─────────────────┘
                                                                                      │
                                                                                      ▼
                                                                            ┌─────────────────┐
                                                                            │                 │
                                                                            │  MCP-Odoo       │
                                                                            │                 │
                                                                            └─────────────────┘
                                                                                      │
                                                                                      ▼
                                                                            ┌─────────────────┐
                                                                            │                 │
                                                                            │  Banco de Dados │
                                                                            │  Odoo           │
                                                                            │                 │
                                                                            └─────────────────┘
```

- Utilizado para operações complexas e interativas
- Ideal para cenários onde agentes de IA precisam consultar e manipular dados do Odoo
- Agentes utilizam `data_proxy_agent.py` para interagir com o MCP
- MCP fornece acesso padronizado aos dados do Odoo

## Funcionalidades Principais

### 1. Gerenciamento Centralizado de Credenciais

- **Armazenamento Seguro**: Todas as credenciais são armazenadas de forma segura no banco de dados Odoo
- **Acesso Restrito**: Apenas administradores do sistema têm acesso ao módulo
- **Auditoria Completa**: Registro detalhado de todas as operações realizadas com as credenciais
- **Geração Automática de Tokens**: Tokens de autenticação gerados automaticamente com alta entropia

### 2. Integração com Sistemas de IA

- **Identificação de Cliente**: Associação clara entre credenciais e identificadores de cliente (account_id)
- **Compatibilidade com YAML**: Tokens gerados são referenciados em arquivos YAML de configuração
- **Verificação Bidirecional**: Sistema verifica a autenticidade das solicitações em ambas as direções
- **Suporte Multi-tenant**: Configurações específicas para cada cliente/tenant

### 3. API Interna Segura

- **Métodos de Autenticação**: API interna para autenticação sem exposição de credenciais
- **Sincronização Segura**: Processo completo de sincronização gerenciado pelo módulo central
- **Callbacks Configuráveis**: Suporte a callbacks para processamento de respostas
- **Tratamento de Erros**: Gestão robusta de erros e exceções

### 4. Monitoramento e Logs

- **Registro de Acessos**: Logs detalhados de todos os acessos às credenciais
- **Histórico de Sincronização**: Registro completo de todas as tentativas de sincronização
- **Alertas de Segurança**: Notificações para tentativas de acesso não autorizadas
- **Relatórios de Auditoria**: Visualizações para auditoria de segurança

## Especificações Técnicas

### Modelos de Dados

1. **ai.system.credentials**
   - Armazena as credenciais principais para cada cliente
   - Campos para diferentes tipos de tokens e chaves de API
   - Suporte para múltiplos sistemas (Odoo, IA, redes sociais)
   - Campos para tokens definidos manualmente pelo administrador
   - Criptografia para dados sensíveis como senhas e chaves de API


2. **ai.credentials.access.log**
   - Registra todos os acessos às credenciais
   - Armazena informações como usuário, IP, data/hora
   - Registra o tipo de operação realizada
   - Mantém histórico de sucesso/falha

### Segurança

- **Grupo de Segurança Dedicado**: `group_ai_credentials_manager`
- **Herança de Administrador**: Apenas usuários com privilégios de administrador
- **Criptografia de Dados Sensíveis**: Senhas e chaves de API são armazenadas com criptografia
- **Regras de Registro**: Regras de acesso a nível de registro para controle granular
- **Auditoria Completa**: Registro detalhado de todas as operações realizadas

### Interface de Usuário

- **Formulário de Credenciais**: Interface intuitiva para gerenciamento de credenciais
- **Visualização de Logs**: Visualização detalhada de logs de acesso
- **Botão de Teste**: Funcionalidade para testar conexões
- **Notificações**: Sistema de notificações para operações importantes

### Integração com Outros Módulos

- **Dependência Mínima**: Apenas depende dos módulos base e mail
- **API para Módulos de Negócio**: Interface clara para módulos como:
  - business_rules
  - semantic_product
  - product_ai_mass_management
- **Sem Exposição de Tokens**: Módulos de negócio nunca têm acesso direto aos tokens

## Arquitetura de Integração

```
┌─────────────────┐      ┌───────────────────┐      ┌─────────────────┐
│                 │      │                   │      │                 │
│  Módulos Odoo   │◄────►│  ai_credentials   │◄────►│  Sistema de IA  │
│  de Negócio     │      │  _manager         │      │                 │
│                 │      │                   │      │                 │
└─────────────────┘      └───────────────────┘      └─────────────────┘
                                  ▲
                                  │
                                  ▼
                         ┌─────────────────┐
                         │                 │
                         │  Arquivos YAML  │
                         │  de Config      │
                         │                 │
                         └─────────────────┘
```

## Fluxo de Autenticação

1. Módulo de negócio solicita sincronização
2. Módulo de credenciais obtém token para o cliente atual
3. Módulo de credenciais envia dados + token para o sistema de IA
4. Sistema de IA verifica token contra configuração YAML
5. Sistema de IA processa dados e retorna resposta
6. Módulo de credenciais processa resposta e notifica módulo de negócio
7. Todo o processo é registrado para auditoria

## Comunicação entre Odoo e Sistema de IA

O módulo implementa uma estratégia robusta para comunicação entre o Odoo e o sistema de IA, que estará hospedado em uma VPS separada. A implementação segue uma abordagem em fases para facilitar o desenvolvimento e garantir a transição suave para o ambiente de produção.

### Abordagem em Fases

#### Fase 1: Desenvolvimento com Ngrok

Durante o desenvolvimento inicial, utilizamos o Ngrok para expor o sistema de IA local à internet, permitindo testes completos sem necessidade de implantação em produção:

```python
class AISystemCredentials(models.Model):
    # Campos existentes...

    # Configuração de conexão
    ai_system_url = fields.Char('URL do Sistema de IA')
    ai_system_api_key = fields.Char('Chave de API do Sistema de IA')

    # Configuração de desenvolvimento
    use_ngrok = fields.Boolean('Usar Ngrok', default=False)
    ngrok_url = fields.Char('URL Ngrok')

    def get_ai_system_url(self):
        """Retorna a URL correta do sistema de IA."""
        self.ensure_one()
        if self.use_ngrok and self.ngrok_url:
            return self.ngrok_url
        return self.ai_system_url
```

#### Fase 2: Sistema de Fila de Mensagens

Para garantir a confiabilidade da comunicação, implementamos um sistema de fila que armazena todas as operações pendentes e gerencia retentativas em caso de falhas:

```python
class AISyncQueue(models.Model):
    _name = 'ai.sync.queue'
    _description = 'Fila de Sincronização com IA'

    credential_id = fields.Many2one('ai.system.credentials', 'Credencial')
    module = fields.Char('Módulo de Origem')
    operation = fields.Char('Operação')
    data = fields.Text('Dados', help="Dados em formato JSON")
    state = fields.Selection([
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('done', 'Concluído'),
        ('failed', 'Falha')
    ], string='Estado', default='pending')
    retry_count = fields.Integer('Tentativas', default=0)
```

#### Fase 3: Implementação em Produção

Em produção, o sistema utiliza uma API REST completa com autenticação segura, monitoramento e alta disponibilidade:

- **Endpoints REST**: API completa no sistema de IA para receber dados do Odoo
- **Autenticação JWT**: Tokens JWT para autenticação segura entre sistemas
- **Monitoramento**: Registro detalhado de todas as comunicações para auditoria
- **Alta Disponibilidade**: Mecanismos de retry e fallback para garantir a entrega

### Diagrama de Comunicação em Produção

```
┬───────────────┬                      ┬───────────────┬
│                 │                      │                 │
│  Servidor Odoo  │                      │  VPS do Sistema  │
│                 │                      │  de IA           │
│  ┬────────────┬  │  API REST Segura     │  ┬────────────┬  │
│  │ Credenciais  │  │ ────────────────────────► │ API Endpoints │  │
│  └────────────┘  │                      │  └────────────┘  │
│                 │                      │                 │
│  ┬────────────┬  │                      │  ┬────────────┬  │
│  │ Fila de     │  │                      │  │ Processamento │  │
│  │ Mensagens   │  │                      │  │ de Mensagens │  │
│  └────────────┘  │                      │  └────────────┘  │
└───────────────┘                      └───────────────┘
```

### Fluxo de Comunicação

1. **Solicitação de Sincronização**: Módulo de negócio solicita sincronização com o sistema de IA
2. **Obtenção de Credenciais**: Módulo de credenciais recupera as credenciais apropriadas
3. **Enfileiramento**: Operação é registrada na fila de mensagens
4. **Processamento Assíncrono**: Agendador processa a fila periodicamente
5. **Comunicação Segura**: Dados são enviados para o sistema de IA via API REST segura
6. **Tratamento de Respostas**: Respostas são processadas e registradas
7. **Retentativas Automáticas**: Em caso de falha, o sistema tenta novamente com backoff exponencial

### Vantagens desta Abordagem

- **Confiabilidade**: Nenhuma operação é perdida, mesmo em caso de falhas de conexão
- **Segurança**: Comunicação segura com autenticação robusta
- **Flexibilidade**: Funciona tanto em desenvolvimento quanto em produção
- **Escalabilidade**: Suporta aumento de carga com processamento assíncrono
- **Auditoria**: Registro completo de todas as operações para rastreabilidade

## Expansão para Plataformas Sociais e Marketplaces

O módulo foi projetado para expandir além da integração com sistemas de IA, servindo como repositório centralizado para todas as credenciais de autenticação, incluindo redes sociais e marketplaces.

### Suporte a Múltiplas Plataformas

- **Redes Sociais**: Facebook, Instagram, Twitter, LinkedIn
- **Marketplaces**: Mercado Livre, Amazon, Shopee
- **Plataformas de Mensagens**: WhatsApp Business, Telegram
- **Serviços de Anúncios**: Google Ads, Facebook Ads

### Armazenamento Expandido de Credenciais

O modelo `ai.system.credentials` inclui campos específicos para cada plataforma:

```python
# Redes Sociais
facebook_app_id = fields.Char('Facebook App ID')
facebook_app_secret = fields.Char('Facebook App Secret', invisible=True)
facebook_access_token = fields.Char('Facebook Access Token', invisible=True)

instagram_client_id = fields.Char('Instagram Client ID')
instagram_access_token = fields.Char('Instagram Access Token', invisible=True)

# Marketplaces
mercadolivre_app_id = fields.Char('Mercado Livre App ID')
mercadolivre_client_secret = fields.Char('Mercado Livre Client Secret', invisible=True)
mercadolivre_access_token = fields.Char('Mercado Livre Access Token', invisible=True)
```

### Integração com Agentes Definidos no YAML

Para permitir que agentes de IA definidos em arquivos YAML interajam com estas plataformas, implementamos uma arquitetura segura de integração:

#### Abordagem de Webhook para Operações

1. **Agentes Solicitam Operações, Não Credenciais**:
   - Em vez de obter credenciais diretamente, os agentes solicitam que operações específicas sejam realizadas
   - Exemplo: "Postar no Facebook" em vez de "Me dê o token do Facebook"

2. **Endpoints Seguros no Odoo**:
   - Implementamos endpoints REST para cada operação nas plataformas sociais
   - Exemplo: `/api/v1/social/post_to_facebook`
   - O Odoo usa as credenciais armazenadas para executar a operação de forma segura

3. **Configuração no YAML**:
```yaml
agents:
  marketing_agent:
    actions:
      post_to_facebook:
        endpoint: "https://odoo.example.com/api/v1/social/post_to_facebook"
        method: "POST"
        auth_type: "api_key"
      get_instagram_insights:
        endpoint: "https://odoo.example.com/api/v1/social/instagram_insights"
        method: "GET"
        auth_type: "api_key"
```

#### Vantagens desta Abordagem

- **Segurança Máxima**: As credenciais nunca saem do ambiente Odoo
- **Auditoria Completa**: Todas as operações são registradas e auditáveis
- **Flexibilidade**: Permite implementar lógica de negócio adicional no Odoo
- **Manutenção Simplificada**: Renovação de tokens e tratamento de erros centralizados

### Fluxo de Integração

1. Agente de IA identifica necessidade de ação em plataforma social
2. Agente chama endpoint específico no Odoo via API
3. Módulo de credenciais autentica a solicitação
4. Módulo recupera credenciais apropriadas para a plataforma
5. Módulo executa a operação na plataforma usando as credenciais
6. Resultado é retornado ao agente
7. Todo o processo é registrado para auditoria

## Implementação de Criptografia

Para garantir a segurança das informações sensíveis, o módulo implementa criptografia para campos como senhas e chaves de API:

```python
from cryptography.fernet import Fernet
import base64

class AISystemCredentials(models.Model):
    _name = 'ai.system.credentials'
    # ...

    # Campos criptografados
    odoo_password_encrypted = fields.Binary('Senha (Criptografada)', attachment=False)
    odoo_api_key_encrypted = fields.Binary('Chave de API (Criptografada)', attachment=False)

    # Campos para interface
    odoo_password = fields.Char('Senha', compute='_compute_password', inverse='_inverse_password', store=False)
    odoo_api_key = fields.Char('Chave de API', compute='_compute_api_key', inverse='_inverse_api_key', store=False)

    def _get_encryption_key(self):
        """Obtém a chave de criptografia do parâmetro do sistema."""
        param = self.env['ir.config_parameter'].sudo().get_param('ai_credentials.encryption_key')
        if not param:
            # Gerar nova chave se não existir
            key = Fernet.generate_key()
            self.env['ir.config_parameter'].sudo().set_param('ai_credentials.encryption_key', key.decode())
            return key
        return param.encode()

    def _encrypt_value(self, value):
        """Criptografa um valor."""
        if not value:
            return False
        key = self._get_encryption_key()
        cipher = Fernet(key)
        return base64.b64encode(cipher.encrypt(value.encode()))

    def _decrypt_value(self, encrypted_value):
        """Descriptografa um valor."""
        if not encrypted_value:
            return ''
        key = self._get_encryption_key()
        cipher = Fernet(key)
        try:
            decrypted = cipher.decrypt(base64.b64decode(encrypted_value))
            return decrypted.decode()
        except Exception:
            return ''
```

### Vantagens da Abordagem de Criptografia

- **Segurança Aprimorada**: Dados sensíveis nunca são armazenados em texto simples no banco de dados
- **Transparência para o Usuário**: A criptografia é transparente na interface do usuário
- **Chave Centralizada**: A chave de criptografia é armazenada como parâmetro do sistema
- **Proteção contra Vazamentos**: Mesmo com acesso ao banco de dados, os dados sensíveis permanecem protegidos

### Considerações de Segurança

- A chave de criptografia é armazenada no banco de dados do Odoo como parâmetro do sistema
- Para segurança adicional em ambientes de produção, considere armazenar a chave em variáveis de ambiente ou em um serviço externo de gerenciamento de segredos
- Backups do banco de dados devem ser protegidos, pois contêm tanto os dados criptografados quanto a chave

## Expansão Futura

O módulo foi projetado para fácil expansão, permitindo:

- Adição de novos tipos de credenciais
- Suporte a novas plataformas e APIs
- Implementação de mecanismos adicionais de segurança
- Integração com sistemas de monitoramento externos
- Suporte a fluxos OAuth completos para plataformas que o exigem

## Instalação e Configuração

1. Instale o módulo através do menu Aplicativos do Odoo
2. Configure as credenciais iniciais através do menu dedicado
3. Adicione os tokens gerados aos arquivos YAML de configuração
4. Verifique a conexão usando o botão de teste

## Notas de Segurança

- Mantenha o acesso ao módulo restrito apenas a administradores confiáveis
- Implemente rotação regular de tokens e senhas
- Monitore regularmente os logs de acesso
- Mantenha o Odoo atualizado com as últimas correções de segurança

## Mecanismo de Recuperação de Credenciais

O sistema implementa dois mecanismos complementares para recuperação segura de credenciais:

### 1. Para o Caminho de API Direta

Os módulos Odoo que utilizam a API direta recuperam credenciais da seguinte forma:

1. **Módulo Odoo Inicia Requisição**:
   - O módulo (ex: business_rules) chama o endpoint da API com seu account_id
   - Exemplo: `POST /api/v1/business-rules/sync` com account_id no corpo da requisição

2. **API Autentica Requisição**:
   - O endpoint da API verifica se a requisição vem de uma instância Odoo válida
   - Utiliza o account_id para identificar quais credenciais usar

3. **API Recupera Credenciais**:
   - A API chama o módulo `ai_credentials_manager` via XML-RPC
   - Recupera as credenciais específicas para o account_id

4. **API Utiliza Credenciais**:
   - A API usa as credenciais recuperadas para autenticar com serviços externos
   - Passa os dados necessários para os agentes de embedding

### 2. Para o Caminho MCP

Para módulos futuros que utilizam o MCP através de agentes:

1. **Sistema de Referência Segura**:
   - Em vez de armazenar credenciais reais nos arquivos YAML, armazenamos referências
   - Exemplo YAML:
     ```yaml
     integrations:
       mcp:
         type: "odoo-mcp"
         config:
           url: "http://localhost:8069"
           db: "account_1"
           credential_ref: "account_1_mcp_credentials"  # Referência, não credenciais reais
     ```

2. **DataProxyAgent Recupera Credenciais**:
   - O `data_proxy_agent.py` obtém a referência do arquivo YAML
   - Usa a referência para recuperar as credenciais reais do sistema seguro

3. **MCP Utiliza Credenciais**:
   - O MCP usa essas credenciais para conectar ao banco de dados Odoo
   - Realiza as operações solicitadas e retorna os resultados aos agentes

Esta abordagem garante que credenciais sensíveis nunca sejam armazenadas em texto claro nos arquivos de configuração, mantendo a segurança mesmo quando os arquivos YAML são compartilhados ou versionados.