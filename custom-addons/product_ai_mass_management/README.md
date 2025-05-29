# Gerenciamento em Massa de Produtos no Sistema de IA

## Visão Geral

Este módulo estende as funcionalidades do Odoo para permitir o gerenciamento em massa de produtos no Sistema de IA. Ele fornece uma interface intuitiva para sincronizar produtos, gerenciar descrições geradas por IA e ajustar preços específicos para o sistema de IA.

O módulo é projetado para trabalhar em conjunto com o módulo `semantic_product_description`, oferecendo uma visão consolidada e ferramentas de gerenciamento em massa para produtos que utilizam descrições semânticas e preços específicos para sistemas de IA.

## Características Principais

### 1. Interface de Gerenciamento em Massa

- **Vista de Lista Otimizada**: Interface especializada para gerenciar múltiplos produtos simultaneamente
- **Indicadores Visuais**: Badges coloridos para status de sincronização, qualidade da descrição, status de preço e popularidade
- **Filtros Avançados**: Filtros para cada status, permitindo fácil segmentação de produtos
- **Agrupamentos Inteligentes**: Opções para agrupar produtos por diferentes critérios relacionados ao sistema de IA

### 2. Status de Sincronização

Acompanhe o status de sincronização de cada produto com o sistema de IA:

- **Verde**: Sincronizado e atualizado
- **Amarelo**: Precisa de atualização
- **Vermelho**: Nunca sincronizado
- **Azul**: Em processo de sincronização

### 3. Qualidade da Descrição

Monitore a qualidade das descrições geradas pela IA:

- **Verde**: Descrição verificada por humano
- **Amarelo**: Descrição gerada mas não verificada
- **Cinza**: Sem descrição

### 4. Gerenciamento de Preços

Gerencie preços específicos para o sistema de IA:

- **Preço Padrão**: Preço regular do produto
- **Preço IA**: Preço específico para uso no sistema de IA
- **Status de Preço**: Badge indicando se o produto tem preço personalizado, usa o preço padrão ou não tem preço definido

### 5. Popularidade no Sistema de IA

Acompanhe a popularidade dos produtos nas buscas do sistema de IA:

- **Verde**: Alta popularidade
- **Amarelo**: Média popularidade
- **Vermelho**: Baixa popularidade
- **Azul**: Novo no sistema (ainda sem dados)

### 6. Operações em Massa

Execute operações em múltiplos produtos simultaneamente:

- **Sincronização em Massa**: Sincronize múltiplos produtos com o sistema de IA
- **Geração de Descrições**: Gere descrições para múltiplos produtos de uma vez
- **Ajuste de Preços**: Ajuste preços para o sistema de IA em massa (percentual ou valor fixo)

## Instalação

1. Instale o módulo `semantic_product_description` (dependência)
2. Instale este módulo (`product_ai_mass_management`)
3. Acesse o menu "Sistema de IA > Gerenciamento em Massa de Produtos"

## Configuração

### Pré-requisitos

- Módulo `semantic_product_description` instalado e configurado
- Conexão com o serviço de IA para geração de descrições e sincronização de produtos

### Configurações Recomendadas

1. **Sincronização Automática**: Configure a sincronização automática de produtos com o sistema de IA
2. **Verificação de Descrições**: Estabeleça um fluxo de trabalho para verificação de descrições geradas pela IA
3. **Estratégia de Preços**: Defina uma estratégia para preços específicos no sistema de IA

## Uso

### Acesso ao Módulo

O módulo pode ser acessado de três maneiras:

1. Menu principal: **Sistema de IA > Gerenciamento em Massa de Produtos**
2. Menu de Vendas: **Vendas > Produtos > Gerenciamento em Massa de Produtos no Sistema de IA**
3. Menu de Estoque: **Estoque > Controle de Inventário > Gerenciamento em Massa de Produtos no Sistema de IA**

### Fluxo de Trabalho Recomendado

1. **Filtrar Produtos**: Use os filtros para selecionar produtos que precisam de atenção
2. **Sincronizar Produtos**: Selecione os produtos e use o botão "Sincronizar Selecionados"
3. **Gerar Descrições**: Para produtos sem descrição, use o botão "Gerar Descrições"
4. **Ajustar Preços**: Use o assistente de ajuste de preços para definir preços específicos para o sistema de IA
5. **Verificar Descrições**: Clique no botão "Ver/Editar" para verificar e ajustar descrições individuais

### Dicas de Uso

- Use o agrupamento por "Status de Sincronização" para identificar rapidamente produtos que precisam de atenção
- Filtre por "Não Sincronizados" para encontrar produtos que ainda não estão disponíveis no sistema de IA
- Use o badge de "Popularidade" para identificar produtos populares que podem precisar de descrições otimizadas

## Integração com Outros Módulos

- **semantic_product_description**: Fornece a base para descrições semânticas e sincronização com o sistema de IA
- **sale**: Integração com o módulo de vendas para acesso rápido a partir do catálogo de produtos
- **stock**: Integração com o módulo de estoque para acesso a partir do controle de inventário
- **purchase**: Integração com o módulo de compras para produtos compráveis

## Desenvolvimento Técnico

### Modelos Principais

- **product.template**: Estende o modelo de produto com campos adicionais para o sistema de IA
- **product.ai.price.wizard**: Assistente para ajuste de preços em massa

### Campos Adicionados

- **ai_price**: Preço específico para o sistema de IA
- **ai_price_difference**: Diferença percentual entre o preço padrão e o preço IA
- **semantic_sync_status**: Status de sincronização com o sistema de IA
- **ai_description_quality**: Qualidade da descrição no sistema de IA
- **ai_price_status**: Status do preço no sistema de IA
- **ai_popularity**: Popularidade do produto nas buscas do sistema de IA

### Métodos Principais

- **action_view_product**: Abre o formulário do produto para edição
- **sync_with_ai_mass**: Sincroniza múltiplos produtos com o sistema de IA
- **generate_descriptions_mass**: Gera descrições para múltiplos produtos
- **adjust_ai_prices_mass**: Ajusta preços para o sistema de IA em massa

## Suporte e Contribuições

Para suporte, relatórios de bugs ou contribuições, entre em contato com a equipe de desenvolvimento.

## Licença

LGPL-3
