# Módulo Empresa e Serviços

## Visão Geral

O módulo "Empresa e Serviços" é uma solução para gerenciar informações da empresa e serviços oferecidos, permitindo uma integração perfeita com sistemas externos. Este módulo é parte de uma arquitetura maior que visa fornecer uma plataforma de serviços agnóstica em relação ao ERP.

## Funcionalidades Principais

### Informações da Empresa
- Dados básicos da empresa (nome, descrição)
- Endereço completo
- Opção para compartilhar endereço com clientes

### Serviços de IA
- Configuração de serviços de IA disponíveis (nas configurações do desenvolvedor):
  - Vendas
  - Agendamento
  - Entrega
  - Suporte
- Cada serviço pode ser ativado/desativado individualmente
- Interface de usuário mostra serviços contratados e disponíveis
- Seção de marketing para serviços não contratados

### Configurações de Atendimento
- Horários de funcionamento (dias e horários)
- Intervalo de almoço
- Estilo de comunicação do agente de IA
- Uso de emojis
- Mensagem de saudação personalizada
- Mensagem de despedida personalizada
- Opção para permitir ao agente informar o Site/Redes Sociais
- Opção para solicitar ao cliente avaliação sobre o atendimento
- Mensagem personalizada para solicitação de avaliação

### Integração com Sistema de IA
- Sincronização automática de dados (Via botão Sincronizar)
- Token de segurança para autenticação
- Configuração de URL e chave de API para o serviço de configuração

#### Padrão de Interface para Sincronização
O módulo implementa um padrão visual consistente para sincronização que deve ser seguido por outros módulos:

1. **Botão de Sincronização**:
   - Cor verde (#00C853)
   - Ícone de sincronização (fa-sync)
   - Texto em negrito
   - Sombra suave
   - Exemplo de implementação:
   ```xml
   <button name="action_sync_to_config_service"
           string="Sincronizar com Sistema de IA"
           type="object"
           class="btn btn-success"
           icon="fa-sync"
           style="background-color: #00C853 !important; color: white !important; font-weight: bold !important; padding: 10px 20px !important; border-radius: 4px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;"/>
   ```

2. **Barra de Status**:
   - Estados padrão: "Não Sincronizado", "Processando", "Sincronizado", "Erro"
   - Implementação:
   ```xml
   <field name="sync_status" widget="statusbar" statusbar_visible="not_synced,syncing,synced,error"/>
   ```

## Arquitetura Técnica

### Modelo de Dados
O módulo utiliza os seguintes modelos:
- `company.service`: Armazena informações da empresa e serviços
- `company.sync.service`: Gerencia a sincronização com o serviço de configuração
- `company.init.config`: Inicializa configurações do sistema

### Parâmetros do Sistema
O módulo armazena configurações sensíveis como parâmetros do sistema:
- `company_services.account_id`: ID da conta no sistema de IA
- `company_services.security_token`: Token de segurança para autenticação
- `company_services.config_service_url`: URL do serviço de configuração
- `company_services.config_service_api_key`: Chave de API para o serviço de configuração

### Configurações de MCP (Model Communication Protocol)
O módulo inclui suporte para diferentes tipos de ERP através do MCP:
- `company_services.mcp_type`: Tipo de MCP (odoo, sap, etc.)
- `company_services.mcp_version`: Versão do ERP
- `company_services.db_url`: URL do servidor ERP
- `company_services.db_name`: Nome do banco de dados (agora usa account_id)
- `company_services.db_user`: Usuário para acesso ao banco
- `company_services.db_password`: Senha para acesso ao banco
- `company_services.db_access_level`: Nível de acesso (read, write, admin)

## Estrutura de Dados para Sincronização

O módulo gera uma estrutura de dados modular para sincronização com o sistema de IA:

```json
{
  "account_id": "account_1",
  "security_token": "token-uuid",
  "name": "Nome da Empresa",
  "description": "Descrição da empresa",
  "version": 1,
  "updated_at": "2023-06-15T10:30:00",
  "enabled_modules": ["company_info", "service_settings", "enabled_services", "mcp"],
  "modules": {
    "company_info": {
      "name": "Nome da Empresa",
      "description": "Descrição da empresa",
      "address": {
        "street": "Rua Principal",
        "city": "Cidade",
        "state": "Estado",
        "zip": "12345-678",
        "country": "Brasil",
        "share_with_customers": true
      }
    },
    "service_settings": {
      "business_hours": {
        "days": [0, 1, 2, 3, 4],
        "start_time": "09:00",
        "end_time": "18:00",
        "has_lunch_break": true,
        "lunch_break_start": "12:00",
        "lunch_break_end": "13:00"
      },
      "customer_service": {
        "greeting_message": "Olá, bem-vindo!",
        "communication_style": "friendly",
        "emoji_usage": "moderate",
        "farewell": {
          "message": "Obrigado por entrar em contato!",
          "enabled": true
        },
        "rating_request": {
          "message": "Sua opinião é muito importante para nós. Como você avaliaria este atendimento?",
          "enabled": true
        }
      },
      "online_channels": {
        "website": {
          "url": "www.empresa.com.br",
          "mention_at_end": true
        },
        "facebook": {
          "url": "www.facebook.com/empresa",
          "mention_at_end": true
        },
        "instagram": {
          "url": "www.instagram.com/empresa",
          "mention_at_end": true
        }
      }
    },
    "enabled_services": {
      "collections": ["products_informations", "scheduling_rules", "support_documents"],
      "services": {
        "sales": {
          "enabled": true,
          "promotions": {
            "inform_at_start": true
          }
        },
        "scheduling": {
          "enabled": true
        },
        "delivery": {
          "enabled": false
        },
        "support": {
          "enabled": true
        }
      }
    },
    "mcp": {
      "type": "odoo",
      "version": "14.0",
      "connection": {
        "url": "http://localhost:8069",
        "database": "account_1",
        "username": "admin",
        "password_ref": "account_1_db_pwd",
        "access_level": "read"
      }
    }
  }
}
```

## Plano de Migração para MongoDB

### Motivação
Atualmente, o módulo utiliza arquivos YAML e PostgreSQL para armazenar configurações. No entanto, estamos planejando migrar para MongoDB pelos seguintes motivos:

1. **Melhor suporte para documentos JSON**: MongoDB é otimizado para armazenar e consultar documentos JSON, o que se alinha perfeitamente com nossa estrutura de dados modular.

2. **Escalabilidade**: MongoDB oferece melhor escalabilidade horizontal para lidar com um grande número de tenants.

3. **Flexibilidade de esquema**: Permite adicionar novos campos e módulos sem necessidade de migrações de esquema complexas.

4. **Performance**: Consultas mais rápidas para recuperar configurações específicas de tenant.

5. **Multi-tenancy**: Suporte nativo para isolamento de dados entre diferentes tenants.

### Estrutura Planejada para MongoDB

#### Coleção `tenants`
```json
{
  "_id": "account_1",
  "name": "Nome da Empresa",
  "created_at": ISODate("2023-06-15T10:30:00Z"),
  "updated_at": ISODate("2023-06-15T10:30:00Z"),
  "active": true,
  "security_token": "token-uuid"
}
```

#### Coleção `configurations`
```json
{
  "_id": ObjectId("..."),
  "tenant_id": "account_1",
  "version": 1,
  "created_at": ISODate("2023-06-15T10:30:00Z"),
  "updated_at": ISODate("2023-06-15T10:30:00Z"),
  "config_data": {
    "modules": {
      "company_info": { ... },
      "service_settings": { ... },
      "enabled_services": { ... },
      "mcp": { ... }
    }
  }
}
```

#### Coleção `credentials`
```json
{
  "_id": "account_1_db_pwd",
  "tenant_id": "account_1",
  "type": "database_password",
  "value": "encrypted_password",
  "created_at": ISODate("2023-06-15T10:30:00Z"),
  "updated_at": ISODate("2023-06-15T10:30:00Z")
}
```

### Passos para Migração

1. **Implementar serviço de configuração com MongoDB**: Criar um microserviço dedicado para gerenciar configurações usando MongoDB.

2. **Desenvolver API de compatibilidade**: Garantir que o módulo atual possa se comunicar com o novo serviço de configuração.

3. **Migrar dados existentes**: Transferir configurações do PostgreSQL para MongoDB.

4. **Atualizar o módulo**: Modificar o módulo para usar o novo serviço de configuração.

5. **Testes e validação**: Garantir que todas as funcionalidades continuem funcionando corretamente.

## Instalação e Configuração

### Pré-requisitos
- Odoo 14.0 ou superior
- Acesso ao banco de dados PostgreSQL
- Permissões de administrador no Odoo

### Instalação
1. Copie o diretório `company_services` para a pasta de addons do Odoo
2. Reinicie o servidor Odoo
3. Atualize a lista de aplicativos no Odoo
4. Instale o módulo "Empresa e Serviços"

### Configuração Inicial
1. Acesse o menu "Empresa e Serviços > Configurações"
2. Configure o ID da Conta e gere um Token de Segurança
3. Configure a URL do Serviço de Configuração e a Chave de API
4. Configure os serviços disponíveis nas configurações do desenvolvedor
5. Acesse o menu "Empresa e Serviços > Configurações da Empresa"
6. Preencha as informações da empresa
7. Configure as opções de comunicação, incluindo a nova opção de avaliação
8. Verifique a aba "Serviços de IA" para ver os serviços contratados e disponíveis
9. Clique no botão verde "Sincronizar com Sistema de IA" para enviar os dados

## Suporte e Desenvolvimento

Este módulo é mantido por Sprintia. Para suporte ou desenvolvimento personalizado, entre em contato:

- Website: https://www.sprintia.com.br
- Email: contato@sprintia.com.br

## Licença

Este módulo é distribuído sob a licença LGPL-3.
