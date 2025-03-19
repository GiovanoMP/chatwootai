# Documentação: Simulação de Fluxo Completo do ChatwootAI

Este documento descreve o fluxo completo de processamento de mensagens no ChatwootAI, desde a recepção de uma mensagem via Chatwoot até o processamento pelos agentes de IA e o envio da resposta de volta ao usuário. A documentação também inclui instruções passo a passo para configurar e testar o sistema.

## Visão Geral da Arquitetura

O sistema ChatwootAI utiliza uma arquitetura de três camadas:

1. **Camada de Canais (Channel Crews)**: Recebe mensagens de diferentes canais (WhatsApp, Instagram, etc.)
2. **Camada de Orquestração (Hub Crew)**: Processa e encaminha mensagens para crews funcionais
3. **Camada Funcional (Functional Crews)**: Crews especializadas que realizam tarefas específicas

Todo o acesso a dados é centralizado através do **DataServiceHub** e do **DataProxyAgent**.

## Fluxo de Processamento de Mensagens

### 1. Recepção da Mensagem (Webhook do Chatwoot)

O fluxo começa quando o Chatwoot recebe uma mensagem de um usuário e envia um webhook para o `webhook_server.py` do ChatwootAI.

```
Usuário (WhatsApp) → Chatwoot → Webhook → ChatwootAI
```

#### Detalhes Técnicos:
- O servidor webhook é implementado usando FastAPI
- O endpoint principal é `/webhook`
- A autenticação é feita via token no cabeçalho

### 2. Roteamento e Normalização

A mensagem recebida é processada pelo `ChatwootWebhookHandler` que:

1. Identifica o tipo de evento (nova mensagem, nova conversa, etc.)
2. Extrai informações relevantes da mensagem
3. Identifica o canal de origem (WhatsApp, Instagram, etc.)
4. Encaminha a mensagem para a crew do canal apropriada

A crew do canal (por exemplo, `WhatsAppChannelCrew`) normaliza a mensagem e a prepara para processamento.

### 3. Processamento pelo Hub

A mensagem normalizada é encaminhada para o `HubCrew`, que contém três agentes principais:

- **OrchestratorAgent**: Analisa a intenção da mensagem e decide para qual crew funcional encaminhá-la
- **ContextManagerAgent**: Gerencia o contexto da conversa, mantendo histórico e informações relevantes
- **IntegrationAgent**: Lida com a integração com sistemas externos como o Odoo

### 4. Acesso a Dados pelo DataProxyAgent

Durante o processamento, os agentes acessam dados através do `DataProxyAgent`, que:

1. Recebe solicitações de dados em linguagem natural dos agentes
2. Traduz essas solicitações em consultas estruturadas
3. Utiliza o `DataServiceHub` para acessar diferentes fontes de dados
4. Aplica estratégias de cache para otimizar o desempenho
5. Retorna os dados em um formato consistente

### 5. Processamento pela Crew Funcional

Com base na análise do `OrchestratorAgent`, a mensagem é encaminhada para uma crew funcional específica:

- **SalesCrew**: Processa consultas relacionadas a vendas, produtos e pedidos
- **SupportCrew**: Lida com problemas, dúvidas e reclamações dos clientes
- **InfoCrew**: Fornece informações gerais sobre a empresa, produtos, etc.
- **SchedulingCrew**: Gerencia agendamentos e compromissos

A crew funcional utiliza seus agentes especializados para gerar uma resposta apropriada.

### 6. Envio da Resposta

A resposta gerada pela crew funcional é enviada de volta para o Chatwoot usando o `ChatwootClient`, que faz uma chamada para a API do Chatwoot.

```
ChatwootAI → API Chatwoot → Chatwoot → Usuário (WhatsApp)
```

## Configuração e Testes

### Pré-requisitos

- Instância do Chatwoot configurada e acessível
- WhatsApp conectado ao Chatwoot via Evolution API
- Variáveis de ambiente configuradas
- Docker e Docker Compose instalados

### Configuração do Ambiente

1. **Configurar Variáveis de Ambiente**

   ```bash
   cp .env.example .env
   ```

   Editar o arquivo `.env` com as seguintes configurações:

   ```
   # Configurações do Chatwoot
   CHATWOOT_API_KEY=sua_api_key
   CHATWOOT_BASE_URL=https://seu-chatwoot.com/api/v1
   CHATWOOT_ACCOUNT_ID=1

   # Configurações do Webhook
   WEBHOOK_PORT=8001
   WEBHOOK_DOMAIN=seu-dominio-ou-ip
   WEBHOOK_USE_HTTPS=false
   ```

2. **Iniciar os Serviços**

   ```bash
   docker-compose up -d
   ```

3. **Configurar o Webhook no Chatwoot**

   No painel de administração do Chatwoot, vá para:
   - Configurações > Desenvolvedor > Webhooks
   - Adicione um novo webhook com a URL: `http://seu-dominio-ou-ip:8001/webhook`
   - Marque os eventos: `message_created`, `conversation_created`, `conversation_status_changed`

### Simulação do Fluxo Completo

#### Método 1: Usando o WhatsApp Real

1. Envie uma mensagem do WhatsApp para o número conectado ao Chatwoot
2. Observe os logs do servidor webhook:
   ```bash
   docker-compose logs -f webhook_server
   ```
3. Verifique se a mensagem foi recebida, processada e respondida

#### Método 2: Simulação com Curl

É possível simular um webhook do Chatwoot usando curl:

```bash
curl -X POST http://localhost:8001/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": "message_created", "message": {"content": "Olá, gostaria de saber mais sobre os produtos", "message_type": 1, "conversation": {"id": 1, "inbox_id": 1}}, "account": {"id": 1}}'
```

#### Método 3: Usando o Script de Demonstração

O script `demo/run_agents_demo.py` simula o fluxo completo sem depender do Chatwoot:

```bash
python -m demo.run_agents_demo
```

Este script:
1. Inicializa todos os componentes necessários (Hub Crew, Crews Funcionais, etc.)
2. Processa um conjunto de mensagens pré-definidas
3. Exibe as respostas geradas

## Validação e Depuração

### Verificações de Validação

- **Recepção do Webhook**: O webhook está sendo recebido pelo servidor?
- **Processamento da Mensagem**: A mensagem está sendo processada corretamente?
- **Acesso a Dados**: Os agentes estão conseguindo acessar os dados necessários?
- **Geração de Resposta**: A resposta está sendo gerada corretamente?
- **Envio da Resposta**: A resposta está sendo enviada de volta para o Chatwoot?

### Registros (Logs)

Os logs do sistema são cruciais para depuração. Verifique os logs usando:

```bash
docker-compose logs -f webhook_server
```

Principais eventos a serem observados nos logs:
1. Recebimento de webhooks
2. Processamento de mensagens
3. Comunicação entre crews
4. Geração e envio de respostas

### Resolução de Problemas Comuns

- **Webhook não recebido**: Verifique configurações de rede, firewall e URL do webhook
- **Erro no processamento da mensagem**: Verifique o formato da mensagem e os logs do servidor
- **Falha no acesso a dados**: Verifique a conexão com os bancos de dados e serviços externos
- **Resposta não enviada**: Verifique a conexão com a API do Chatwoot e as permissões

## Próximos Passos

### Melhorias Futuras

1. **Implementação de Testes Automatizados**:
   - Testes unitários para cada componente
   - Testes de integração para fluxos completos
   - Testes de carga para verificar escalabilidade

2. **Monitoramento e Métricas**:
   - Implementar métricas para tempos de resposta
   - Monitorar taxa de sucesso e falha nas interações
   - Criar dashboards para visualização de desempenho

3. **Experiências Controladas (A/B Testing)**:
   - Comparar diferentes estratégias de respostas
   - Testar diferentes configurações de agentes
   - Avaliar impacto no engajamento dos usuários

## Conclusão

O fluxo completo do ChatwootAI demonstra como uma arquitetura bem estruturada e modular pode gerenciar eficientemente o processamento de mensagens em um cenário de atendimento multicanal. A centralização do acesso a dados através do DataServiceHub e do DataProxyAgent melhora a manutenibilidade e a escalabilidade do sistema.

Para garantir o funcionamento correto, é fundamental testar cada etapa do fluxo e monitorar o sistema em produção.
O plugin especializado formata as recomendações com explicações específicas para cosméticos
O SalesAgent estrutura a resposta em linguagem natural
A mensagem é enviada de volta para o cliente
Resposta: "Olá Maria! Para pele oleosa, temos estas ótimas opções: 1) Hidratante Facial Oil-Free XYZ, que controla a oleosidade e não obstrui os poros; 2) Gel Hidratante ABC, com textura leve e acabamento matte; 3) Hidratante Facial DEF, com proteção solar e controle de brilho. Algum desses lhe interessa em particular?"

Mensagem 2: Consulta de disponibilidade de produto específico
Cliente: "O Hidratante Facial XYZ parece bom. Vocês têm em estoque? Quanto custa?"

Fluxo de Processamento:
Recepção e análise da mensagem
Fluxo similar ao anterior, mas agora com foco em verificação de estoque
Consulta ao estoque (via DataProxyAgent)
CopyInsert
SalesAgent → DataProxyAgent → InventoryDataService
Código:
python
CopyInsert
# Em DataProxyAgent
def _check_inventory(self, product_id):
    # Consulta ao serviço de inventário
    return self.data_service_hub.inventory_service.get_stock(
        {"product_id": product_id}
    )
Consulta de preço (via DataProxyAgent)
CopyInsert
SalesAgent → DataProxyAgent → PricingDataService
O DataProxyAgent combina as duas consultas (estoque e preço) para otimizar o acesso
Resposta ao cliente
Formata informações de disponibilidade, preço e promoções
Resposta: "Ótima escolha, Maria! Sim, temos o Hidratante Facial Oil-Free XYZ em estoque (12 unidades). O preço é R$ 89,90, mas hoje está com 15% de desconto, saindo por R$ 76,41. Posso separar um para você?"

Mensagem 3: Consulta de horários para tratamento
Cliente: "Perfeito! Vou querer um. Aproveitando, vocês têm horários disponíveis para uma limpeza de pele na próxima semana?"

Fluxo de Processamento:
Análise da mensagem com múltiplas intenções
CopyInsert
Mensagem → OrchestratorAgent → Detecção de intenções múltiplas
O OrchestratorAgent identifica duas intenções distintas: a) Confirmação de compra b) Consulta de agendamento
Processamento da compra (via SalesCrew)
CopyInsert
SalesAgent → DataProxyAgent → CartDataService
Adiciona o produto ao carrinho da cliente
Encaminhamento para SchedulingCrew
CopyInsert
OrchestratorAgent → SchedulingCrew
A segunda parte da mensagem é encaminhada para a crew especializada em agendamentos
Consulta de disponibilidade (via DataProxyAgent)
CopyInsert
SchedulingAgent → DataProxyAgent → SchedulingDataService
Código:
python
CopyInsert
# Em DataProxyAgent
def _check_availability(self, service_type, date_range):
    # Adaptação para o domínio atual
    domain_params = self.domain_adapter.adapt_scheduling_query({
        "service": service_type,
        "start_date": date_range[0],
        "end_date": date_range[1]
    })
    # Consulta ao serviço de agendamento
    return self.data_service_hub.scheduling_service.get_available_slots(domain_params)
Resposta coordenada
CopyInsert
HubCrew → Combinação de respostas → Resposta unificada
O Hub combina as respostas das duas crews (Sales e Scheduling) em uma única resposta coerente
Resposta: "Adicionei o Hidratante Facial Oil-Free XYZ ao seu carrinho! Quanto à limpeza de pele, temos os seguintes horários disponíveis na próxima semana: Segunda (15:00 ou 17:30), Quarta (10:00 ou 14:00) ou Sexta (09:00). Gostaria de agendar em algum desses horários?"

Mensagem 4: Agendamento e finalização
Cliente: "Vou querer na quarta às 14h. Posso pagar o hidratante quando for à loja ou preciso pagar online?"

Fluxo de Processamento:
Processamento do agendamento
CopyInsert
SchedulingAgent → DataProxyAgent → SchedulingDataService
Código:
python
CopyInsert
# Em DataProxyAgent
def _create_appointment(self, customer_id, service, datetime):
    # Adaptação para o domínio atual
    domain_params = self.domain_adapter.adapt_appointment_creation({
        "customer_id": customer_id,
        "service_type": service,
        "datetime": datetime
    })
    # Criação do agendamento
    return self.data_service_hub.scheduling_service.create_appointment(domain_params)
Consulta sobre políticas de pagamento
CopyInsert
SalesAgent → DataProxyAgent → PaymentPolicyDataService
Busca informações sobre opções de pagamento para o domínio atual
Resposta integrada
CopyInsert
HubCrew → Resposta final coordenada
Combina confirmação do agendamento com informações sobre pagamento
Resposta: "Perfeito, Maria! Seu agendamento para limpeza de pele foi confirmado para quarta-feira, 14h, com a especialista Ana. Quanto ao hidratante, você tem a opção de pagar online agora (com 5% de desconto adicional) ou na loja no dia do seu tratamento. Como prefere proceder?"

Análise da Arquitetura
Componentes-chave Demonstrados
DataProxyAgent
Papel central como intermediário entre agentes e serviços de dados
Otimização de consultas e combinar solicitações relacionadas
Adaptação automática para o domínio específico
Adaptadores de Domínio
Transformação de consultas genéricas em consultas específicas para o domínio
Isolamento das especificidades do domínio de cosméticos
Plugins Especializados
Lógica de negócio específica para o domínio (ex: recomendação de produtos para pele)
Formatação e enriquecimento de dados específicos do domínio
Arquitetura Hub-and-Spoke
Orquestração central pelo HubCrew
Crews especializadas para diferentes funções
Comunicação coordenada entre crews
Sistema de Contexto
Manutenção do contexto da conversa entre mensagens
Enriquecimento de consultas com dados de contexto
Validação da Arquitetura
A simulação demonstra que a arquitetura cumpre os requisitos de:

Adaptabilidade - O mesmo sistema pode funcionar para diferentes domínios mudando apenas adaptadores e plugins
Modularidade - Crews especializadas com responsabilidades bem definidas
Desacoplamento - Agentes funcionais não precisam conhecer detalhes de acesso a dados
Extensibilidade - Novos serviços e funcionalidades podem ser adicionados sem alterar o núcleo
Exemplos de Implementação
1. Exemplo de Plugin Específico de Domínio
python
CopyInsert
# src/plugins/cosmetics/product_recommendation.py
from src.plugins.base.base_plugin import BasePlugin

class CosmeticsProductRecommendationPlugin(BasePlugin):
    """Plugin especializado em recomendação de produtos cosméticos."""
    
    def __init__(self, data_proxy=None):
        super().__init__(name="cosmetics_product_recommendation")
        self.data_proxy = data_proxy
    
    def recommend_for_skin_type(self, skin_type, product_category=None, concerns=None):
        """Recomenda produtos com base no tipo de pele e preocupações."""
        query_params = {
            "skin_type": skin_type,
            "category": product_category,
            "concerns": concerns or []
        }
        
        # Usando o DataProxyAgent para buscar dados
        product_data = self.data_proxy.execute_task(
            description=f"Buscar produtos para pele {skin_type}",
            input_data=query_params
        )
        
        # Lógica específica para domínio de cosméticos
        ranked_products = self._rank_by_skin_compatibility(product_data, skin_type)
        
        return {
            "products": ranked_products,
            "explanation": self._generate_skin_explanation(skin_type),
            "recommendations": self._generate_usage_tips(ranked_products, skin_type)
        }
    
    def _rank_by_skin_compatibility(self, products, skin_type):
        """Classifica produtos por compatibilidade com tipo de pele (lógica específica)."""
        compatibility_scores = {
            "oleosa": {
                "oil-free": 5,
                "matte": 4,
                "gel": 4,
                "salicylic-acid": 3,
                "cream": 1
            },
            "seca": {
                "cream": 5,
                "hyaluronic-acid": 4,
                "oil": 3,
                "matte": 1
            }
            # Outros tipos de pele...
        }
        
        scores = compatibility_scores.get(skin_type, {})
        
        # Lógica de classificação específica para cosméticos
        for product in products:
            product["compatibility_score"] = 0
            for feature in product.get("features", []):
                product["compatibility_score"] += scores.get(feature, 0)
        
        return sorted(products, key=lambda p: p.get("compatibility_score", 0), reverse=True)
    
    def _generate_skin_explanation(self, skin_type):
        """Gera explicação sobre o tipo de pele (conhecimento específico do domínio)."""
        explanations = {
            "oleosa": "Peles oleosas se beneficiam de produtos oil-free, com textura leve, que controlam a produção de sebo sem ressecar.",
            "seca": "Peles secas necessitam de produtos ricos em hidratantes e emolientes para restaurar a barreira cutânea.",
            # Outros tipos...
        }
        return explanations.get(skin_type, "")
    
    def _generate_usage_tips(self, products, skin_type):
        """Gera dicas de uso específicas para os produtos e tipo de pele."""
        # Lógica específica de domínio
        tips = []
        for product in products[:3]:  # Apenas top 3
            if skin_type == "oleosa" and "gel" in product.get("features", []):
                tips.append(f"Aplique o {product['name']} em uma pele limpa, pela manhã e noite para controlar o brilho.")
            # Outras regras específicas...
            
        return tips
2. Exemplo de Adaptador de Domínio
python
CopyInsert
# src/domain/adapters/cosmetics_adapter.py
from src.domain.adapters.base_adapter import BaseDomainAdapter

class CosmeticsDomainAdapter(BaseDomainAdapter):
    """Adaptador para o domínio de cosméticos."""
    
    def __init__(self, config):
        super().__init__(name="cosmetics")
        self.config = config
        # Carrega mapeamentos específicos do domínio
        self.field_mappings = config.get("field_mappings", {})
        self.product_categories = config.get("product_categories", {})
        self.skin_types = config.get("skin_types", {})
    
    def adapt_product_query(self, generic_params):
        """Adapta consulta genérica de produto para o esquema específico de cosméticos."""
        adapted_params = {}
        
        # Mapear campos genéricos para campos específicos do domínio
        for generic_field, value in generic_params.items():
            if generic_field in self.field_mappings:
                domain_field = self.field_mappings[generic_field]
                adapted_params[domain_field] = value
        
        # Processamento específico para tipo de pele
        if "skin_type" in generic_params:
            skin_type = generic_params["skin_type"]
            # Mapear para taxonomia específica do domínio
            if skin_type in self.skin_types:
                specific_skin_mapping = self.skin_types[skin_type]
                adapted_params["propriedades.tipo_pele"] = specific_skin_mapping["db_value"]
                
                # Adicionar filtros específicos para o tipo de pele
                if "filters" not in adapted_params:
                    adapted_params["filters"] = []
                adapted_params["filters"].extend(specific_skin_mapping.get("relevant_filters", []))
        
        # Processamento específico para categoria de produto
        if "category" in generic_params:
            category = generic_params["category"]
            if category in self.product_categories:
                adapted_params["categoria"] = self.product_categories[category]["db_value"]
        
        # Adicionar lógica específica para busca vetorial no domínio de cosméticos
        if "vector_search" in generic_params:
            adapted_params["vector_query"] = self._build_vector_query(
                generic_params["vector_search"]
            )
        
        return adapted_params
    
    def adapt_scheduling_query(self, generic_params):
        """Adapta consulta genérica de agendamento para o esquema específico de cosméticos."""
        adapted_params = {}
        
        # Mapear serviço genérico para serviço específico de cosméticos
        if "service" in generic_params:
            service_mappings = {
                "limpeza de pele": "facial_cleansing",
                "hidratação": "hydration_treatment",
                "consulta": "skin_consultation"
                # Outros serviços específicos...
            }
            adapted_params["service_code"] = service_mappings.get(
                generic_params["service"].lower(), 
                "generic_appointment"
            )
        
        # Mapear outros parâmetros
        if "start_date" in generic_params:
            adapted_params["date_from"] = generic_params["start_date"]
        
        if "end_date" in generic_params:
            adapted_params["date_to"] = generic_params["end_date"]
        
        # Adicionar filtros específicos do domínio
        adapted_params["location_type"] = "store"  # Específico para cosméticos
        adapted_params["service_category"] = "beauty"  # Específico para cosméticos
        
        return adapted_params
    
    def _build_vector_query(self, vector_search_params):
        """Constrói consulta vetorial específica para o domínio de cosméticos."""
        # Lógica específica para construir consulta vetorial para produtos cosméticos
        reference_product = vector_search_params.get("reference_product")
        vector_query = {
            "text": reference_product,
            "filter_conditions": {}
        }
        
        # Adaptar filtros para o esquema específico
        filters = vector_search_params.get("filter_conditions", {})
        for filter_name, filter_value in filters.items():
            if filter_name == "skin_type" and filter_value in self.skin_types:
                vector_query["filter_conditions"]["propriedades.tipo_pele"] = self.skin_types[filter_value]["db_value"]
            # Outros mapeamentos de filtros...
        
        return vector_query
3. Exemplo de Configuração de Domínio (YAML)
yaml
CopyInsert
# config/domains/cosmetics.yaml
domain:
  name: cosméticos
  description: Domínio de produtos e serviços cosméticos
  version: 1.0

# Mapeamento de campos genéricos para o esquema específico
field_mappings:
  name: nome_produto
  skin_type: propriedades.tipo_pele
  category: categoria
  price: valor
  brand: marca
  concerns: propriedades.indicacoes

# Taxonomia específica para tipos de pele
skin_types:
  oleosa:
    db_value: "oily"
    description: "Pele com produção excessiva de sebo"
    relevant_filters:
      - { field: "propriedades.controle_oleosidade", value: true }
      - { field: "propriedades.textura", value: "leve" }
  
  seca:
    db_value: "dry"
    description: "Pele com pouca produção de sebo, tendendo a descamação"
    relevant_filters:
      - { field: "propriedades.hidratacao_intensa", value: true }
  
  mista:
    db_value: "combination"
    description: "Pele com oleosidade na zona T e normal/seca nas laterais"
    relevant_filters:
      - { field: "propriedades.balanceamento", value: true }

# Categorias de produtos específicas do domínio
product_categories:
  hidratante:
    db_value: "moisturizer"
    description: "Produtos para hidratação facial"
  
  limpeza:
    db_value: "cleanser"
    description: "Produtos para limpeza facial"
  
  tratamento:
    db_value: "treatment"
    description: "Produtos para tratamentos específicos"

# Serviços específicos do domínio
services:
  limpeza_de_pele:
    db_value: "facial_cleansing"
    duration: 60  # minutos
    providers: ["esteticista", "dermatologista"]
  
  massagem_facial:
    db_value: "facial_massage"
    duration: 30
    providers: ["esteticista"]
  
  consulta:
    db_value: "skin_consultation"
    duration: 45
    providers: ["dermatologista"]

# Plugins específicos para este domínio
plugins:
  - cosmetics_product_recommendation
  - treatment_scheduler
  - skin_analyzer

# Regras de negócio específicas para este domínio
business_rules:
  - rule: "product_recommendation_by_skin_type"
    description: "Recomenda produtos com base no tipo de pele"
    implementation: "plugins.cosmetics.product_recommendation.recommend_for_skin_type"
  
  - rule: "seasonal_product_boost"
    description: "Aumenta relevância de produtos sazonais"
    implementation: "plugins.cosmetics.seasonal_rules.apply_seasonal_boost"
  
  - rule: "cross_selling_rules"
    description: "Regras para venda cruzada de produtos complementares"
    implementation: "plugins.cosmetics.sales_rules.apply_cross_selling"
Esses exemplos demonstram como nossa arquitetura permite a adaptação para diferentes domínios de negócio através de três componentes principais:

Plugins específicos - Implementam lógica de negócio específica do domínio
Adaptadores de domínio - Traduzem consultas genéricas para o esquema específico
Configurações YAML - Definem taxonomias, mapeamentos e regras específicas do domínio
Com essa arquitetura, podemos facilmente adaptar o sistema para outros domínios como saúde, varejo ou alimentação, apenas criando novos adaptadores, plugins e arquivos de configuração, sem alterar o núcleo do sistema ou os agentes principais.

DoneFeedback has been submitted
