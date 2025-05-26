# Módulo de Regras de Negócio

Este módulo permite gerenciar regras de negócio para o sistema de IA, incluindo regras permanentes, temporárias, de agendamento e documentos de suporte.

## Características

- **Regras de Negócio Permanentes**: Crie regras que se aplicam permanentemente ao seu negócio
- **Regras Temporárias**: Configure regras com prazo de validade para situações específicas
- **Regras de Agendamento**: Configure regras para agendamento de serviços, consultas ou reservas
- **Documentos de Suporte**: Adicione documentos de suporte ao cliente, como manuais, FAQs e instruções
- **Sincronização com IA**: Envie todas as regras configuradas para o sistema de IA
- **Visualização de Status**: Acompanhe o status de sincronização com indicadores visuais

## Configuração

### Configurações do Módulo

Acesse **Regras de Negócio > Configurações** para configurar:

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

## Implementação do Botão de Sincronização e Visualizador de Status

### Botão de Sincronização

O botão de sincronização é implementado na view principal do módulo e deve seguir um padrão específico para manter a consistência em todos os módulos. Aqui está o código XML para referência:

```xml
<header>
    <button name="action_sync_with_ai"
            string="Sincronizar com Sistema de IA"
            type="object"
            class="btn btn-success"
            icon="fa-sync"
            style="background-color: #00C853 !important; color: white !important; font-weight: bold !important; padding: 10px 20px !important; border-radius: 4px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;"/>
    <field name="sync_status" widget="statusbar" statusbar_visible="not_synced,syncing,synced,error"/>
</header>
```

#### Posicionamento do Botão
- O botão deve estar sempre no `<header>` do formulário
- Deve ser o primeiro elemento no header, antes do campo de status
- Deve ser visível em todos os estados do formulário (não usar atributos `states` ou `attrs`)

#### Atributos do Botão
- `name="action_sync_with_ai"`: Nome do método Python a ser chamado (deve ser consistente em todos os módulos)
- `string="Sincronizar com Sistema de IA"`: Texto exibido no botão (deve ser idêntico em todos os módulos)
- `type="object"`: Tipo de ação (chama um método Python)
- `class="btn btn-success"`: Classes CSS para estilização
- `icon="fa-sync"`: Ícone FontAwesome (deve ser o mesmo em todos os módulos)
- `style="..."`: Estilos CSS inline para personalização avançada (deve ser idêntico em todos os módulos)

#### Cores e Estilos (Padrão para Todos os Módulos)
- Cor de fundo: `#00C853` (verde)
- Cor do texto: `white`
- Fonte: negrito
- Padding: `10px 20px`
- Border-radius: `4px`
- Box-shadow: `0 2px 4px rgba(0,0,0,0.2)`

#### Comportamento do Botão
- Ao clicar, deve chamar o método `action_sync_with_ai` do modelo
- Deve atualizar o status para "Processando" imediatamente
- Deve exibir uma notificação de sucesso ou erro após a conclusão
- Deve atualizar o campo `last_sync_date` em caso de sucesso

### Visualizador de Status

O visualizador de status é implementado em duas partes e deve seguir um padrão específico para manter a consistência em todos os módulos:

1. Campo de status na barra de status
2. Indicadores visuais no canto superior direito

#### Campo de Status na Barra de Status

```xml
<field name="sync_status" widget="statusbar" statusbar_visible="not_synced,syncing,synced,error"/>
```

Este campo deve:
- Estar posicionado logo após o botão de sincronização no `<header>`
- Usar o widget `statusbar` para exibir o status atual
- Mostrar todos os estados possíveis na ordem correta
- Ter o mesmo nome de campo (`sync_status`) em todos os módulos

#### Indicadores Visuais no Canto Superior Direito

```xml
<div class="oe_title">
    <div class="float-right">
        <div class="d-flex align-items-center mb-2">
            <span class="badge badge-success mr-2" attrs="{'invisible': [('sync_status', '!=', 'synced')]}">
                <i class="fa fa-check mr-1"></i> Sincronizado
            </span>
            <span class="badge badge-warning mr-2" attrs="{'invisible': [('sync_status', '!=', 'syncing')]}">
                <i class="fa fa-refresh fa-spin mr-1"></i> Sincronizando
            </span>
            <span class="badge badge-danger mr-2" attrs="{'invisible': [('sync_status', '!=', 'error')]}">
                <i class="fa fa-exclamation-triangle mr-1"></i> Erro
            </span>
            <span class="badge badge-secondary mr-2" attrs="{'invisible': [('sync_status', '!=', 'not_synced')]}">
                <i class="fa fa-clock-o mr-1"></i> Não Sincronizado
            </span>
        </div>
        <div class="d-flex align-items-center">
            <span class="fa fa-arrow-right text-success mx-1" attrs="{'invisible': [('sync_status', '!=', 'synced')]}"/>
            <span class="fa fa-arrow-left text-success mx-1" attrs="{'invisible': [('sync_status', '!=', 'synced')]}"/>
            <span class="fa fa-arrow-right text-warning mx-1 fa-spin" attrs="{'invisible': [('sync_status', '!=', 'syncing')]}"/>
            <span class="fa fa-arrow-left text-warning mx-1 fa-spin" attrs="{'invisible': [('sync_status', '!=', 'syncing')]}"/>
            <span class="fa fa-times text-danger mx-1" attrs="{'invisible': [('sync_status', '!=', 'error')]}"/>
            <span class="fa fa-minus text-muted mx-1" attrs="{'invisible': [('sync_status', '!=', 'not_synced')]}"/>
        </div>
    </div>
    <field name="name" invisible="1"/>
</div>
```

#### Posicionamento dos Indicadores Visuais
- Devem estar dentro da `<div class="oe_title">` no canto superior direito do formulário
- Devem usar `float-right` para alinhamento à direita
- Devem estar acima de qualquer outro conteúdo no título

#### Cores e Ícones dos Indicadores
- **Sincronizado**: Verde (`badge-success`) com ícone de check (`fa-check`)
- **Processando**: Amarelo (`badge-warning`) com ícone de refresh girando (`fa-refresh fa-spin`)
- **Erro**: Vermelho (`badge-danger`) com ícone de triângulo de alerta (`fa-exclamation-triangle`)
- **Não Sincronizado**: Cinza (`badge-secondary`) com ícone de relógio (`fa-clock-o`)

#### Setas de Sincronização
- Devem ser exibidas abaixo dos badges
- Devem usar as mesmas cores dos badges correspondentes
- Devem ter animação de rotação para o estado "Processando"
- Devem ser consistentes em todos os módulos

### Implementação do Campo de Status no Modelo

O campo de status é implementado no modelo Python e deve seguir um padrão específico para manter a consistência em todos os módulos:

```python
sync_status = fields.Selection([
    ('not_synced', 'Não Sincronizado'),
    ('syncing', 'Processando'),
    ('synced', 'Sincronizado'),
    ('error', 'Erro')
], string='Status de Sincronização', default='not_synced', readonly=True, tracking=True)

error_message = fields.Text('Mensagem de Erro', readonly=True)
last_sync_date = fields.Datetime(string='Última Sincronização', readonly=True)
```

#### Requisitos para os Campos de Status
- O campo `sync_status` deve ser um campo Selection com exatamente os 4 estados mostrados acima
- A ordem dos estados deve ser mantida para garantir a consistência da interface
- O campo deve ser readonly para evitar edição manual
- O campo deve ter tracking=True para registrar alterações no histórico
- O valor padrão deve ser 'not_synced'

#### Campos Relacionados
- `error_message`: Campo de texto para armazenar mensagens de erro detalhadas
- `last_sync_date`: Campo de data/hora para registrar a última sincronização bem-sucedida
- Ambos os campos devem ser readonly para evitar edição manual

#### Visibilidade dos Campos
- O campo `error_message` deve ser visível apenas quando `sync_status` é 'error'
- O campo `last_sync_date` deve ser sempre visível para referência

### Implementação do Método de Sincronização

O método de sincronização é implementado no modelo Python e deve seguir um padrão específico para manter a consistência em todos os módulos:

```python
def action_sync_with_ai(self):
    """Sincronizar com o sistema de IA"""
    self.ensure_one()

    try:
        # Atualizar status para "Processando"
        self.write({
            'sync_status': 'syncing',
            'error_message': False
        })

        # Lógica de sincronização...

        # Se a sincronização for bem-sucedida
        self.write({
            'last_sync_date': fields.Datetime.now(),
            'sync_status': 'synced'
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sincronização Concluída'),
                'message': _('Regras de negócio sincronizadas com sucesso com o sistema de IA.'),
                'sticky': False,
                'type': 'success',
            }
        }

    except Exception as e:
        self.write({
            'sync_status': 'error',
            'error_message': str(e)
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Erro na Sincronização'),
                'message': str(e),
                'sticky': True,
                'type': 'danger',
            }
        }
```

#### Requisitos para o Método de Sincronização
- O nome do método deve ser `action_sync_with_ai` em todos os módulos
- Deve começar com `self.ensure_one()` para garantir que apenas um registro seja processado
- Deve atualizar o status para 'syncing' no início do método
- Deve limpar qualquer mensagem de erro anterior
- Deve usar um bloco try/except para capturar e tratar erros
- Deve atualizar o status para 'synced' em caso de sucesso
- Deve atualizar o status para 'error' em caso de falha
- Deve armazenar a mensagem de erro completa no campo `error_message`
- Deve retornar uma notificação apropriada para o usuário

#### Notificações para o Usuário
- **Sucesso**: Notificação verde, não persistente (sticky=False)
- **Erro**: Notificação vermelha, persistente (sticky=True) com a mensagem de erro
- As mensagens devem ser traduzíveis usando a função `_()`

#### Estrutura do Método
1. Verificar que apenas um registro está sendo processado
2. Atualizar o status para 'syncing'
3. Executar a lógica de sincronização específica do módulo
4. Atualizar o status para 'synced' ou 'error'
5. Retornar uma notificação apropriada

### Estilização de Regras Ativas

Para estilizar as regras ativas com cor verde, use o atributo `decoration-success` nas visualizações em árvore:

```xml
<tree string="Regras de Negócio" decoration-success="1==1">
    <field name="name"/>
    <field name="rule_type"/>
    <field name="description"/>
</tree>
```

### Implementação do Botão de Exclusão com Ícone de Lixeira

Para implementar um botão de exclusão com ícone de lixeira:

```xml
<button name="unlink" type="object" string="Excluir" icon="fa-trash-o" class="text-danger"/>
```

## Autor

Sprintia - https://www.sprintia.com.br
