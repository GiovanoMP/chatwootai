# Personalização Contextual no ChatwootAI

## O que é Personalização Contextual?

A personalização contextual é uma funcionalidade que permite ao sistema oferecer respostas e recomendações altamente personalizadas com base no contexto completo da conversa e no histórico do cliente. Diferente de simples recomendações baseadas apenas no tópico atual, a personalização contextual considera múltiplos fatores:

1. Histórico de compras do cliente
2. Preferências demonstradas em conversas anteriores
3. Comportamento de navegação e busca
4. Agendamentos e serviços utilizados
5. Padrões temporais (sazonalidade, frequência de compra, etc.)
6. Contexto atual da conversa (intenções, produtos mencionados, etc.)

## Como Funciona na Prática?

Para entender como a personalização contextual funciona, vamos analisar um exemplo prático:

### Exemplo: Cliente Interessado em Protetor Solar

**Cenário inicial**: Um cliente pergunta sobre um protetor solar específico.

#### Na Arquitetura Original:

1. O cliente pergunta sobre o protetor solar
2. O sistema fornece informações sobre o produto
3. O cliente decide comprar
4. O sistema processa a compra
5. O cliente menciona interesse em agendar uma consulta
6. O sistema muda completamente de contexto (perde a conexão com a conversa anterior sobre protetor solar)
7. O cliente pergunta sobre riscos de um procedimento
8. O sistema busca informações isoladas sobre o procedimento

#### Na Nova Arquitetura com Personalização Contextual:

1. O cliente pergunta sobre o protetor solar
2. O sistema fornece informações sobre o produto e registra o interesse em proteção solar
3. O cliente decide comprar
4. O sistema processa a compra e atualiza o perfil do cliente
5. O cliente menciona interesse em agendar uma consulta
6. O sistema **conecta os dois assuntos**: "Já que você está interessado em proteção solar, uma consulta dermatológica seria ideal para avaliar o melhor tipo de proteção para sua pele"
7. O cliente pergunta sobre riscos de um procedimento
8. O sistema responde e também sugere: "Após o procedimento, será especialmente importante usar proteção solar adequada como a que você acabou de adquirir"

## Benefícios para o Usuário Final

A personalização contextual traz diversos benefícios para o usuário final:

1. **Experiência mais natural**: As conversas fluem como com um atendente humano que se lembra de tudo
2. **Economia de tempo**: O cliente não precisa repetir informações ou preferências
3. **Descoberta de produtos/serviços relevantes**: Recomendações verdadeiramente úteis baseadas em necessidades reais
4. **Sensação de atenção personalizada**: O cliente sente que é tratado como único
5. **Resolução mais eficiente**: Problemas são resolvidos considerando o contexto completo

## Implementação Técnica

A implementação da personalização contextual envolve vários componentes:

### 1. Sistema de Coleta de Dados

```python
class CustomerInteractionCollector:
    """
    Coleta e armazena interações do cliente para análise posterior.
    """
    
    def __init__(self, data_service_hub):
        self.data_service_hub = data_service_hub
        
    def track_interaction(self, customer_id, interaction_type, data):
        """
        Registra uma interação do cliente.
        
        Args:
            customer_id: ID do cliente
            interaction_type: Tipo de interação (view_product, purchase, appointment, etc.)
            data: Dados da interação
        """
        timestamp = datetime.now()
        
        interaction = {
            'customer_id': customer_id,
            'interaction_type': interaction_type,
            'timestamp': timestamp,
            'data': data
        }
        
        # Armazenar no histórico de interações
        self.data_service_hub.write('customer_interaction', interaction)
        
        # Atualizar perfil do cliente com insights desta interação
        self._update_customer_profile(customer_id, interaction_type, data)
        
    def _update_customer_profile(self, customer_id, interaction_type, data):
        """
        Atualiza o perfil do cliente com insights da interação.
        """
        # Obter perfil atual
        profile = self.data_service_hub.query('customer', {'customer_id': customer_id})
        
        # Atualizar com base no tipo de interação
        if interaction_type == 'view_product':
            category = data.get('category')
            if category:
                if 'categories_of_interest' not in profile:
                    profile['categories_of_interest'] = {}
                
                if category in profile['categories_of_interest']:
                    profile['categories_of_interest'][category] += 1
                else:
                    profile['categories_of_interest'][category] = 1
                    
        elif interaction_type == 'purchase':
            # Registrar compra e atualizar frequência de compra
            # Implementação
            
        elif interaction_type == 'schedule_appointment':
            # Registrar tipo de serviço preferido
            # Implementação
            
        # Salvar perfil atualizado
        self.data_service_hub.write('customer', profile)
```

### 2. Análise de Contexto Cruzado

O `CrossContextAnalyzer` (já apresentado anteriormente) é o componente central que analisa o contexto da conversa atual junto com o histórico do cliente para identificar oportunidades de personalização.

### 3. Geração de Recomendações Personalizadas

```python
class PersonalizationEngine:
    """
    Motor de personalização que gera recomendações baseadas em contexto.
    """
    
    def __init__(self, data_service_hub, cross_context_analyzer):
        self.data_service_hub = data_service_hub
        self.analyzer = cross_context_analyzer
        self.recommendation_strategies = {
            'cross_sell': self._generate_cross_sell,
            'up_sell': self._generate_up_sell,
            'service_recommendation': self._generate_service_recommendation,
            'timing_based': self._generate_timing_recommendation,
            'health_advice': self._generate_health_advice
        }
        
    def generate_recommendations(self, customer_id, current_context):
        """
        Gera recomendações personalizadas para o cliente.
        
        Args:
            customer_id: ID do cliente
            current_context: Contexto atual da conversa
            
        Returns:
            Lista de recomendações personalizadas
        """
        # Obter histórico de conversas
        conversation_history = self.data_service_hub.query(
            'conversation', {'customer_id': customer_id, 'limit': 5})
        
        # Analisar oportunidades
        opportunities = self.analyzer.analyze(
            customer_id, current_context, conversation_history)
        
        # Gerar recomendações para cada oportunidade
        recommendations = []
        for opportunity in opportunities:
            strategy = self.recommendation_strategies.get(opportunity['type'])
            if strategy:
                recommendation = strategy(customer_id, opportunity, current_context)
                if recommendation:
                    recommendations.append(recommendation)
        
        return recommendations
        
    def _generate_cross_sell(self, customer_id, opportunity, context):
        """Gera recomendação de cross-sell."""
        products = opportunity.get('products', [])
        if not products:
            return None
            
        product = products[0]
        context_note = opportunity.get('context', '')
        
        return {
            'type': 'cross_sell',
            'text': f"Já que você está interessado em {context_note}, "
                   f"talvez também goste de {product['name']}, "
                   f"que muitos clientes utilizam em conjunto.",
            'product_id': product['id'],
            'relevance_score': opportunity.get('relevance_score', 0.7)
        }
        
    # Outros métodos de geração de recomendações...
```

### 4. Integração nos Agentes

Os agentes nas diferentes crews são adaptados para utilizar as recomendações personalizadas:

```python
class SalesAgent(Agent):
    """Agente de vendas com capacidade de personalização."""
    
    def __init__(self, personalization_engine=None, **kwargs):
        self.personalization_engine = personalization_engine
        super().__init__(**kwargs)
        
    def generate_response(self, message, context):
        """Gera resposta para o cliente."""
        customer_id = context.get('customer_id')
        
        # Resposta base
        base_response = self._generate_base_response(message, context)
        
        # Se temos personalização disponível e ID do cliente
        if self.personalization_engine and customer_id:
            recommendations = self.personalization_engine.generate_recommendations(
                customer_id, context)
            
            # Adicionar recomendações relevantes à resposta
            enhanced_response = self._enhance_response_with_recommendations(
                base_response, recommendations, context)
            
            return enhanced_response
        
        return base_response
        
    def _enhance_response_with_recommendations(self, base_response, recommendations, context):
        """Aprimora a resposta base com recomendações personalizadas."""
        if not recommendations:
            return base_response
            
        # Filtrar por relevância e contexto atual
        relevant_recommendations = [r for r in recommendations 
                                   if r.get('relevance_score', 0) > 0.6]
        
        if not relevant_recommendations:
            return base_response
            
        # Ordenar por relevância
        relevant_recommendations.sort(
            key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Adicionar a recomendação mais relevante
        top_recommendation = relevant_recommendations[0]
        
        enhanced_response = base_response + "\n\n" + top_recommendation['text']
        
        return enhanced_response
```

## Como Implementar em seu Negócio

Para implementar a personalização contextual no seu negócio, siga este passo a passo:

### 1. Preparação de Dados

Identifique e colete:
- Histórico de compras
- Preferências explícitas (declaradas pelo cliente)
- Preferências implícitas (derivadas do comportamento)
- Categorias de produtos/serviços de interesse
- Padrões temporais (frequência de compra, sazonalidade)

### 2. Definição de Oportunidades

Defina os tipos de oportunidades de personalização relevantes para seu negócio:
- Cross-sell (produtos complementares)
- Up-sell (versões premium)
- Recomendações de serviços
- Lembretes baseados em tempo
- Dicas de saúde/uso

### 3. Criação de Regras Contextuais

Desenvolva regras para quando cada tipo de recomendação deve ser apresentado:
- Em qual momento da conversa
- Com qual gatilho específico
- Com qual contexto anterior necessário
- Com qual prioridade em relação a outras recomendações

### 4. Integração com CRM

Conecte o sistema de personalização ao seu CRM para:
- Alimentar o sistema com dados históricos
- Atualizar o perfil do cliente com novas interações
- Medir a eficácia das recomendações (taxa de conversão)

### 5. Testes e Refinamento

- Teste diferentes abordagens de personalização
- Meça a aceitação das recomendações
- Refine as regras com base nos resultados
- Evolua o sistema para incorporar aprendizado de máquina

## Exemplos por Domínio de Negócio

### Domínio de Cosméticos

**Cenário**: Cliente comprou protetor solar e está perguntando sobre hidratantes.

**Personalização**: "Vejo que você comprou nosso protetor solar FPS 50 recentemente. Para otimizar seu uso, recomendo o hidratante Aqua Fresh, que funciona perfeitamente com proteção solar e não causa oleosidade. Além disso, como está se aproximando o verão, que tal agendar uma avaliação dermatológica para garantir a melhor proteção para sua pele?"

### Domínio de Saúde

**Cenário**: Cliente está perguntando sobre um medicamento para dores de cabeça.

**Personalização**: "Com base no seu histórico, notei que você costuma buscar medicamentos para dores de cabeça com frequência. Além do medicamento que você perguntou, gostaria de sugerir uma consulta com nosso neurologista para investigar a causa das dores recorrentes? Muitos pacientes conseguem reduzir significativamente as dores com o tratamento adequado."

### Domínio de Varejo

**Cenário**: Cliente está comprando tênis de corrida.

**Personalização**: "Ótima escolha de tênis de corrida! Como você comprou meias esportivas no mês passado, quer aproveitar nossa promoção especial de 20% em uma segunda unidade? Também notei que você costuma se exercitar regularmente - temos uma linha nova de camisetas com tecnologia de resfriamento que pode melhorar seu conforto durante os treinos."

## Conclusão

A personalização contextual é uma das grandes vantagens da nova arquitetura proposta para o ChatwootAI. Ao manter o contexto completo das interações e utilizar um sistema inteligente de análise, podemos oferecer uma experiência verdadeiramente personalizada que se aproxima de um atendimento humano de alta qualidade, mas com a escala e consistência que só a tecnologia pode proporcionar.

Este documento serve como guia para a implementação desta funcionalidade, que representará um diferencial competitivo significativo para empresas que desejam aprimorar o relacionamento com seus clientes.
