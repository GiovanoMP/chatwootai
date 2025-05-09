# Módulo de Regras de Negócio 2.0

Este módulo permite gerenciar regras de negócio para o sistema de IA, incluindo regras permanentes, temporárias, de agendamento e documentos de suporte.

## Características

- **Regras de Negócio Permanentes**: Crie regras que se aplicam permanentemente ao seu negócio
- **Regras Temporárias**: Configure regras com prazo de validade para situações específicas
- **Regras de Agendamento**: Configure regras para agendamento de serviços, consultas ou reservas
- **Documentos de Suporte**: Adicione documentos de suporte ao cliente, como manuais, FAQs e instruções
- **Sincronização com IA**: Envie todas as regras configuradas para o sistema de IA

## Configuração

### Configurações do Módulo

Acesse **Regras de Negócio 2.0 > Configurações** para configurar:

- **URL do Webhook**: URL do webhook para o microsserviço de vetorização
- **Token de API**: Token de autenticação para o microsserviço de vetorização
- **Nome da Empresa**: Nome da empresa para identificação no microsserviço de vetorização
- **ID da Conta**: ID da conta para identificação no sistema de IA (ex: account_1, account_2)

### Regras de Negócio

1. Acesse **Regras de Negócio 2.0 > Regras de Negócio**
2. Crie uma nova regra de negócio
3. Configure as informações básicas da empresa
4. Adicione regras permanentes, temporárias e de agendamento
5. Adicione documentos de suporte
6. Configure os serviços habilitados
7. Clique em **Sincronizar com Sistema de IA** para enviar as regras para o sistema de IA

## Integração com o Microsserviço de Vetorização

O módulo se integra com um microsserviço de vetorização que processa as regras e as armazena no Qdrant para busca semântica. A comunicação é feita via webhook, utilizando o token de API para autenticação.

### Endpoints do Webhook

- **POST /api/v1/business-rules/sync**: Sincroniza regras de negócio permanentes e temporárias
- **POST /api/v1/company-metadata/sync**: Sincroniza metadados da empresa
- **POST /api/v1/scheduling-rules/sync**: Sincroniza regras de agendamento
- **POST /api/v1/support-documents/sync**: Sincroniza documentos de suporte

## Estrutura de Dados

### Regras de Negócio Permanentes

```json
{
  "id": 1,
  "name": "Política de Devolução",
  "description": "Produtos podem ser devolvidos em até 7 dias após a compra",
  "type": "return",
  "last_updated": "2023-01-01 12:00:00"
}
```

### Regras Temporárias

```json
{
  "id": 2,
  "name": "Promoção de Verão",
  "description": "Desconto de 20% em todos os produtos",
  "type": "promotion",
  "start_date": "2023-01-01",
  "end_date": "2023-01-31",
  "last_updated": "2023-01-01 12:00:00"
}
```

### Regras de Agendamento

```json
{
  "id": 3,
  "name": "Consulta Médica",
  "description": "Agendamento de consulta médica",
  "service_type": "consultation",
  "duration": 1.0,
  "min_interval": 0.25,
  "min_advance_time": 24,
  "max_advance_time": 30,
  "days_available": {
    "monday": true,
    "tuesday": true,
    "wednesday": true,
    "thursday": true,
    "friday": true,
    "saturday": false,
    "sunday": false
  },
  "hours": {
    "morning_start": 8.0,
    "morning_end": 12.0,
    "afternoon_start": 13.0,
    "afternoon_end": 18.0,
    "has_lunch_break": true
  },
  "last_updated": "2023-01-01 12:00:00"
}
```

### Documentos de Suporte

```json
{
  "id": 4,
  "name": "Manual do Usuário",
  "document_type": "support",
  "content": "Conteúdo do manual do usuário...",
  "last_updated": "2023-01-01 12:00:00"
}
```

## Requisitos

- Odoo 14.0 ou superior
- Microsserviço de vetorização configurado e acessível
- Qdrant para armazenamento de vetores

## Autor

Sprintia - https://www.sprintia.com.br
