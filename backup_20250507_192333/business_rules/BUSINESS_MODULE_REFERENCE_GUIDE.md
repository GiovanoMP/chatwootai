# Análise Detalhada do Módulo Business Rules

## 1. Estrutura do Módulo

O módulo `business_rules` é um componente fundamental do sistema, responsável por gerenciar regras de negócio, documentos de suporte e configurações da empresa que são utilizadas pelo sistema de IA. O módulo é composto por duas partes principais:

1. **Módulo Odoo (`addons/business_rules/`)**: Interface de usuário e modelos de dados no Odoo
2. **API FastAPI (`odoo_api/modules/business_rules/`)**: Endpoints e serviços para integração com o sistema de IA

### 1.1. Estrutura de Arquivos do Módulo Odoo

```
addons/business_rules/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── sync_controller.py
├── data/
│   ├── business_template_data.xml
│   └── config_parameter.xml
├── models/
│   ├── __init__.py
│   ├── business_rules.py
│   ├── business_support_document.py
│   ├── business_template.py
│   ├── dashboard.py
│   ├── res_config_settings.py
│   ├── rule_item.py
│   ├── scheduling_rule.py
│   └── temporary_rule.py
├── security/
│   └── ir.model.access.csv
├── static/
│   └── src/
├── views/
│   ├── business_rules_views.xml
│   ├── business_support_document_views.xml
│   ├── dashboard_view.xml
│   ├── menu_views.xml
│   ├── res_config_settings_views.xml
│   ├── rule_item_views.xml
│   ├── scheduling_rule_views.xml
│   └── temporary_rule_views.xml
└── wizards/
    ├── __init__.py
    └── document_upload_wizard.xml
```

### 1.2. Estrutura de Arquivos da API

```
odoo_api/modules/business_rules/
├── __init__.py
├── routes.py
├── schemas.py
├── services.py
├── style_manager.py
└── utils.py
```

## 2. Modelos de Dados

O módulo implementa vários modelos de dados que trabalham juntos para fornecer uma solução completa:

### 2.1. Modelo Principal: `business.rules`

Este é o modelo central que armazena as configurações da empresa e serve como ponto de entrada para as regras de negócio.

**Campos Principais:**
- `name`: Nome da empresa
- `description`: Descrição da empresa
- `business_area`: Área de negócio (varejo, e-commerce, saúde, etc.)
- `visible_in_ai`: Controla se a empresa está disponível no sistema de IA
- `sync_status`: Status de sincronização com o sistema de IA

### 2.2. Modelo de Regras: `business.rule.item`

Armazena regras de negócio permanentes.

**Campos Principais:**
- `name`: Nome da regra
- `description`: Descrição detalhada da regra
- `rule_type`: Tipo de regra (geral, produto, serviço, etc.)
- `active`: Indica se a regra está ativa
- `visible_in_ai`: Controla se a regra está disponível no sistema de IA
- `sync_status`: Status de sincronização com o sistema de IA

### 2.3. Modelo de Regras Temporárias: `business.temporary.rule`

Armazena regras temporárias ou promoções com período de validade.

**Campos Principais:**
- `name`: Nome da regra
- `description`: Descrição detalhada da regra
- `rule_type`: Tipo de regra (geral, produto, serviço, etc.)
- `is_temporary`: Indica se é uma regra temporária
- `date_start`: Data de início da validade
- `date_end`: Data de término da validade
- `state`: Estado da regra (rascunho, ativa, expirada, cancelada)
- `active`: Indica se a regra está ativa
- `visible_in_ai`: Controla se a regra está disponível no sistema de IA
- `sync_status`: Status de sincronização com o sistema de IA

### 2.4. Modelo de Documentos de Suporte: `business.support.document`

Armazena documentos de suporte que são vetorizados e utilizados pelo sistema de IA.

**Campos Principais:**
- `name`: Nome do documento
- `document_type`: Tipo do documento
- `content`: Conteúdo do documento
- `active`: Indica se o documento está ativo
- `visible_in_ai`: Controla se o documento está disponível no sistema de IA
- `sync_status`: Status de sincronização com o sistema de IA

## 3. Interface do Usuário

### 3.1. Layout e Organização

O módulo utiliza um layout bem estruturado com as seguintes características:

1. **Cabeçalho com Botão de Sincronização**:
   - Botão "Sincronizar com Sistema de IA" (verde fixo)
   - Barra de status mostrando o estado da sincronização

2. **Abas Organizadas por Funcionalidade**:
   - Informações Básicas
   - Configurações de Atendimento
   - Regras de Negócio e Promoções
   - Regras de Agendamento
   - Documentos de Suporte ao Cliente

3. **Seções com Agrupamento Lógico**:
   - Cada aba contém seções agrupadas logicamente
   - Uso de grupos para organizar campos relacionados
   - Alertas informativos no topo de cada aba

### 3.2. Elementos Visuais e Cores

1. **Botões**:
   - Botão de sincronização: Verde fixo (`btn-success` com estilo adicional)
   - Botões de ação: Azul (`btn-primary`)
   - Botões de exclusão: Vermelho com confirmação

2. **Campos Booleanos**:
   - Toggle switches para campos booleanos (`widget="boolean_toggle"`)
   - Botões de status para campos booleanos importantes (`widget="boolean_button"`)

3. **Decorações em Listas**:
   - Verde para status "synced" (`decoration-success`)
   - Vermelho para status "error" (`decoration-danger`)
   - Azul para status "not_synced" (`decoration-info`)

### 3.3. Exemplo de Código XML para Botão de Sincronização

```xml
<button name="action_sync_with_ai"
        string="Sincronizar com Sistema de IA"
        type="object"
        class="btn btn-success"
        style="background-color: #28a745 !important; color: white !important;"/>
```

## 4. Endpoints e Rotas da API

A API implementa vários endpoints para interagir com o módulo:

### 4.1. Endpoints Principais

1. **Sincronização de Regras**:
   - `POST /api/v1/business-rules/sync`
   - Sincroniza todas as regras ativas com o sistema de IA

2. **Sincronização de Metadados da Empresa**:
   - `POST /api/v1/business-rules/sync-company-metadata`
   - Sincroniza metadados gerais da empresa com o sistema de IA

3. **Sincronização de Documentos de Suporte**:
   - `POST /api/v1/business-rules/sync-support-documents`
   - Sincroniza documentos de suporte ao cliente com o sistema de IA

4. **Busca Semântica de Regras**:
   - `GET /api/v1/business-rules/semantic-search`
   - Busca regras de negócio semanticamente similares a uma consulta

5. **Limpeza de Documentos**:
   - `POST /api/v1/business-rules/clear-support-documents`
   - Remove todos os documentos de suporte do Qdrant para um account_id específico

### 4.2. Estrutura de Resposta Padrão

Todas as rotas retornam uma resposta padronizada:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "timestamp": 1619712345.67,
    "request_id": "97346357-b822-4e57-8bcd-8d0ca75b3e38"
  }
}
```

## 5. Processo de Sincronização e Vetorização

O processo de sincronização e vetorização é um dos aspectos mais importantes do módulo. Ele é responsável por transferir as regras e documentos do Odoo para o sistema de IA, vetorizando-os para permitir busca semântica.

### 5.1. Fluxo de Sincronização

1. **Inicialização**:
   - Atualizar status para "syncing"
   - Conectar aos serviços necessários (Odoo, Qdrant, Redis)

2. **Sincronização de Metadados da Empresa**:
   - Obter metadados da empresa do Odoo
   - Processar e enriquecer os metadados
   - Vetorizar e armazenar no Qdrant

3. **Sincronização de Regras de Negócio**:
   - Obter regras ativas e disponíveis no Sistema de IA do Odoo
   - Obter regras existentes no Qdrant
   - Identificar regras obsoletas ou não disponíveis no Sistema de IA
   - Remover regras obsoletas ou não disponíveis do Qdrant
   - Vetorizar e armazenar regras ativas no Qdrant

4. **Sincronização de Documentos de Suporte**:
   - Obter documentos ativos e disponíveis no Sistema de IA do Odoo
   - Obter documentos existentes no Qdrant
   - Identificar documentos obsoletos ou não disponíveis no Sistema de IA
   - Remover documentos obsoletos ou não disponíveis do Qdrant
   - Vetorizar e armazenar documentos ativos no Qdrant

5. **Finalização**:
   - Atualizar status para "synced" ou "error"
   - Retornar resultado da sincronização

### 5.2. Implementação do Campo `visible_in_ai`

O campo `visible_in_ai` é crucial para controlar quais itens são enviados para o sistema de IA. Ele está presente em todos os modelos relevantes:

```python
visible_in_ai = fields.Boolean(default=True, string='Disponível no Sistema de IA',
                              help='Se marcado, esta regra será incluída no sistema de IA')
```

Na sincronização, apenas itens com `visible_in_ai = True` são considerados:

```python
# Buscar regras permanentes ativas e disponíveis no Sistema de IA
permanent_rule_ids = await odoo_permanent.execute_kw(
    'business.rule.item',
    'search',
    [[('active', '=', True), ('visible_in_ai', '=', True)]]
)
```

### 5.3. Vetorização Eficiente

O sistema implementa várias otimizações para tornar a vetorização eficiente:

1. **Vetorização Seletiva**:
   - Apenas itens modificados são revetorizados
   - Comparação de campos relevantes para determinar se houve alteração

2. **Remoção de Itens Obsoletos**:
   - Itens não mais disponíveis no Sistema de IA são removidos do Qdrant
   - Isso mantém o banco de dados vetorial limpo e eficiente

3. **Processamento de Texto**:
   - Texto é preparado especificamente para vetorização
   - Campos relevantes são combinados em um formato otimizado

4. **Armazenamento de Metadados**:
   - Metadados relevantes são armazenados junto com os vetores
   - Isso permite filtragem e recuperação eficientes

### 5.4. Exemplo de Código para Vetorização

```python
# Preparar texto para vetorização
rule_text = self._prepare_rule_text_for_vectorization(rule)

# Gerar embedding
embedding = await vector_service.generate_embedding(rule_text)

# Armazenar no Qdrant
vector_service.qdrant_client.upsert(
    collection_name=collection_name,
    points=[
        models.PointStruct(
            id=rule.id,
            vector=embedding,
            payload={
                "account_id": account_id,  # Campo crucial para filtragem por tenant
                "rule_id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "type": rule.type,
                "priority": rule.priority,
                "is_temporary": rule.is_temporary,
                "rule_data": rule.rule_data,
                "processed_text": rule_text,
                "last_updated": datetime.now().isoformat()
            }
        )
    ],
)
```

## 6. Boas Práticas Implementadas

O módulo implementa várias boas práticas que devem ser seguidas em outros módulos:

### 6.1. Separação de Responsabilidades

- **Modelos**: Definem a estrutura de dados e a lógica de negócio
- **Visualizações**: Definem a interface do usuário
- **Controladores**: Gerenciam a comunicação entre o Odoo e a API
- **Serviços**: Implementam a lógica de negócio da API
- **Rotas**: Definem os endpoints da API

### 6.2. Tratamento de Erros

- Uso de blocos try/except para capturar e registrar erros
- Registro detalhado de erros com traceback
- Retorno de mensagens de erro claras e informativas

### 6.3. Logging Detalhado

- Uso de diferentes níveis de log (info, warning, error)
- Inclusão de informações contextuais nos logs
- Registro de início e fim de operações importantes

### 6.4. Validação de Dados

- Validação de dados de entrada
- Verificação de existência de registros antes de operações
- Tratamento de casos especiais (listas vazias, valores nulos)

### 6.5. Otimização de Desempenho

- Uso de Redis para cache
- Vetorização seletiva
- Remoção de itens obsoletos
- Processamento em lote quando possível

## 7. Recomendações para Futuros Módulos

Com base na análise do módulo `business_rules`, aqui estão as recomendações para o desenvolvimento de futuros módulos:

### 7.1. Estrutura e Organização

1. **Seguir a Mesma Estrutura de Arquivos**:
   - Manter a separação entre modelos, visualizações, controladores, etc.
   - Usar nomes de arquivo descritivos e consistentes

2. **Organizar Visualizações por Funcionalidade**:
   - Agrupar campos relacionados em seções lógicas
   - Usar abas para separar diferentes aspectos do módulo

### 7.2. Implementação do Campo `visible_in_ai`

1. **Adicionar o Campo em Todos os Modelos Relevantes**:
   ```python
   visible_in_ai = fields.Boolean(default=True, string='Disponível no Sistema de IA',
                                 help='Se marcado, este item será incluído no sistema de IA')
   ```

2. **Atualizar o Status de Sincronização Quando o Campo Mudar**:
   ```python
   def write(self, vals):
       # Se o item está sendo marcado como não disponível no IA, marcar para sincronização
       if 'visible_in_ai' in vals and vals['visible_in_ai'] is False:
           vals['sync_status'] = 'not_synced'
       return super(ModelName, self).write(vals)
   ```

3. **Filtrar por `visible_in_ai` na Sincronização**:
   ```python
   items = await odoo.execute_kw(
       'model.name',
       'search',
       [[('active', '=', True), ('visible_in_ai', '=', True)]]
   )
   ```

### 7.3. Processo de Vetorização

1. **Implementar Vetorização Seletiva**:
   - Comparar campos relevantes para determinar se um item foi modificado
   - Revetorizar apenas itens modificados

2. **Remover Itens Obsoletos ou Não Disponíveis no Sistema de IA**:
   - Identificar itens que não estão mais ativos ou disponíveis no Sistema de IA
   - Remover esses itens do Qdrant

3. **Armazenar Metadados Relevantes**:
   - Incluir `account_id` para filtragem por tenant
   - Incluir campos relevantes para busca e filtragem
   - Incluir timestamp de última atualização

### 7.4. Interface do Usuário

1. **Botão de Sincronização**:
   ```xml
   <button name="action_sync_with_ai"
           string="Sincronizar com Sistema de IA"
           type="object"
           class="btn btn-success"
           style="background-color: #28a745 !important; color: white !important;"/>
   ```

2. **Campo `visible_in_ai` na Visualização de Árvore**:
   ```xml
   <field name="visible_in_ai" widget="boolean_toggle" string="Disponível no Sistema de IA"/>
   ```

3. **Campo `visible_in_ai` na Visualização de Formulário**:
   ```xml
   <field name="visible_in_ai" string="Disponível no Sistema de IA"/>
   ```

4. **Decorações para Status de Sincronização**:
   ```xml
   <field name="sync_status" decoration-success="sync_status == 'synced'" decoration-danger="sync_status == 'error'" decoration-info="sync_status == 'not_synced'"/>
   ```

### 7.5. Endpoints da API

1. **Seguir o Mesmo Padrão de Resposta**:
   ```python
   return build_response(
       success=True,
       data=result,
       meta={"request_id": getattr(request.state, "request_id", "unknown")},
   )
   ```

2. **Implementar Endpoints Similares**:
   - Endpoint de sincronização
   - Endpoint de busca semântica
   - Endpoint de limpeza

3. **Tratar Erros de Forma Consistente**:
   ```python
   except ValidationError as e:
       logger.warning(f"Validation error: {e}")
       raise HTTPException(
           status_code=422,
           detail={"code": "VALIDATION_ERROR", "message": str(e)},
       )
   ```

## 8. Implementação da Aba de Agendamento

A aba de Regras de Agendamento é uma funcionalidade importante do módulo `business_rules` que permite configurar regras para agendamento de serviços. Esta seção descreve a implementação desta funcionalidade.

### 8.1. Modelo de Dados: `business.scheduling.rule`

O modelo `business.scheduling.rule` armazena as regras de agendamento.

**Campos Principais:**
- `name`: Nome da regra
- `description`: Descrição da regra
- `service_type`: Tipo de serviço (consulta, atendimento, etc.)
- `duration`: Duração do serviço em minutos
- `min_interval`: Intervalo mínimo entre agendamentos
- `min_advance_time`: Tempo mínimo de antecedência para agendamento
- `max_advance_time`: Tempo máximo de antecedência para agendamento
- `days_available`: Dias da semana disponíveis (campos booleanos)
- `active`: Indica se a regra está ativa
- `visible_in_ai`: Controla se a regra está disponível no sistema de IA
- `sync_status`: Status de sincronização com o sistema de IA

### 8.2. Coleção Específica no Qdrant

As regras de agendamento são armazenadas em uma coleção específica no Qdrant chamada `scheduling_rules`. Isso proporciona:

1. **Melhor organização dos dados**: Cada tipo de dado tem sua própria coleção
2. **Consultas mais eficientes**: Não é necessário filtrar por tipo de regra
3. **Isolamento de dados**: Problemas em uma coleção não afetam as outras

### 8.3. Agente de Vetorização Específico

Foi implementado um agente específico para processar e vetorizar regras de agendamento:

```python
class SchedulingRulesEmbeddingAgent:
    """Agente para processar e vetorizar regras de agendamento."""

    def process_scheduling_rule(self, rule_data: Dict[str, Any]) -> str:
        """
        Processa uma regra de agendamento para vetorização.

        Args:
            rule_data: Dados da regra de agendamento

        Returns:
            Texto processado para vetorização
        """
        # Implementação do processamento
```

### 8.4. Endpoint de Sincronização Específico

Foi implementado um endpoint específico para sincronizar regras de agendamento:

```python
@router.post(
    "/sync-scheduling-rules",
    response_model=APIResponse,
    summary="Sincroniza regras de agendamento com o sistema de IA",
    description="Sincroniza regras de agendamento com o sistema de IA.",
)
async def sync_scheduling_rules(
    request: Request,
    account_id: str = Query(None, description="ID da conta (opcional, para compatibilidade)"),
):
    """
    Sincroniza regras de agendamento com o sistema de IA.
    """
    # Implementação da sincronização
```

### 8.5. Tratamento do Campo `visible_in_ai`

O campo `visible_in_ai` é crucial para controlar quais regras de agendamento são enviadas para o sistema de IA. Quando este campo é alterado, o sistema:

1. **Desativação**: Remove a regra do Qdrant quando `visible_in_ai` é alterado para `False`
2. **Ativação**: Adiciona a regra ao Qdrant quando `visible_in_ai` é alterado para `True`

```python
def write(self, vals):
    """Sobrescrever método write para atualizar status de sincronização"""
    # Se a regra está sendo marcada como não visível no IA, marcar para sincronização
    if 'visible_in_ai' in vals:
        vals['sync_status'] = 'not_synced'

        # Se a regra está sendo ativada novamente no IA, sincronizar imediatamente
        if vals['visible_in_ai'] is True and hasattr(self, 'business_rule_id') and self.business_rule_id:
            # Executar sincronização
```

### 8.6. Remoção de Regras Obsoletas

Durante a sincronização, o sistema identifica e remove regras obsoletas do Qdrant:

1. Obter todas as regras de agendamento do Odoo
2. Filtrar as regras ativas e visíveis no sistema de IA
3. Obter todas as regras de agendamento do Qdrant
4. Identificar quais regras estão no Qdrant mas não estão ativas ou visíveis no Odoo
5. Remover essas regras do Qdrant

```python
# Identificar regras obsoletas (no Qdrant mas não ativas/visíveis no Odoo)
qdrant_rule_ids = [point.payload.get('rule_id') for point in existing_points]
obsolete_rule_ids = [rule_id for rule_id in qdrant_rule_ids if rule_id not in active_visible_rule_ids]

# Remover regras obsoletas do Qdrant
for rule_id in obsolete_rule_ids:
    # Calcular o ID numérico usado no Qdrant
    qdrant_id = int(hashlib.md5(f"{account_id}_{rule_id}".encode()).hexdigest(), 16) % (2**63)

    # Remover do Qdrant
    vector_service.qdrant_client.delete(
        collection_name=collection_name,
        points_selector=models.PointIdsList(
            points=[qdrant_id]
        ),
        wait=True
    )
```

## 9. Conclusão

O módulo `business_rules` implementa uma solução completa para gerenciar regras de negócio, documentos de suporte, regras de agendamento e configurações da empresa que são utilizadas pelo sistema de IA. Ele segue boas práticas de desenvolvimento e implementa um processo eficiente de sincronização e vetorização.

As principais características que devem ser replicadas em outros módulos são:

1. **Campo `visible_in_ai`** para controlar quais itens são enviados para o sistema de IA
2. **Processo de vetorização seletiva** para otimizar o desempenho
3. **Remoção de itens obsoletos ou não disponíveis no Sistema de IA** para manter o banco de dados vetorial limpo
4. **Coleções específicas no Qdrant** para diferentes tipos de dados
5. **Agentes de vetorização específicos** para diferentes tipos de dados
6. **Interface do usuário consistente** com botões e campos padronizados
7. **Tratamento de erros e logging detalhado** para facilitar a depuração

Seguindo essas recomendações, futuros módulos serão mais fáceis de desenvolver, manter e integrar com o sistema de IA.
