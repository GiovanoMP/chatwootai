# Estúdio de Produtos com IA

Um módulo Odoo 16 para enriquecimento e otimização de produtos utilizando inteligência artificial, com foco em integração com marketplaces.

## Visão Geral

O **Estúdio de Produtos com IA** é uma solução avançada para o Odoo 16 que potencializa a gestão de produtos através da inteligência artificial, com foco especial na otimização para marketplaces. Este módulo é projetado para ser um complemento ao módulo `product_ai_mass_management`, permitindo um enriquecimento detalhado e personalizado de produtos.

## Principais Funcionalidades

### 1. Enriquecimento de Produtos com IA
- **Enriquecimento Básico**: Vetorização automática para produtos de alto volume, permitindo busca semântica e categorização inteligente.
- **Enriquecimento Avançado**: Geração de descrições detalhadas e otimizadas para marketplaces específicos, com análise competitiva e sugestões de melhorias.

### 2. Integração com Marketplaces
- Conectores para principais marketplaces (Mercado Livre, Amazon, Shopee, etc.)
- Sincronização bidirecional de produtos, estoques e preços
- Mapeamento inteligente de categorias entre o Odoo e os marketplaces

### 3. Otimização de Conteúdo
- Geração de títulos e descrições otimizados para SEO
- Sugestão de palavras-chave relevantes
- Análise de competitividade e recomendações de preços

### 4. Gestão de Imagens
- Sugestão de imagens através de IA
- Otimização automática de imagens para diferentes marketplaces
- Organização e priorização de imagens

### 5. Dashboard de Performance
- Métricas de desempenho dos produtos nos diferentes marketplaces
- Acompanhamento do processo de enriquecimento
- Identificação de oportunidades de melhoria

### 6. Integração com MCP-Qdrant
- Armazenamento e busca vetorial de produtos
- Recomendações baseadas em similaridade semântica
- Categorização automática de produtos

## Arquitetura

Este módulo foi desenvolvido como uma solução independente, focada exclusivamente no enriquecimento de produtos. Ele pode ser acessado a partir de:

1. **Módulo de Produtos Padrão do Odoo**: Através de ações de servidor na visualização de produtos
2. **Módulo Product AI Mass Management**: Através de ações específicas para enriquecimento
3. **Diretamente pelo menu do módulo**: Acesso ao dashboard e todas as funcionalidades

## Modelos Principais

- **EnrichmentProfile**: Gerencia perfis de enriquecimento com configurações específicas para diferentes tipos de produtos
- **ProductMarketplace**: Configura conectores para diferentes marketplaces
- **MarketplaceDescription**: Armazena descrições específicas para cada marketplace
- **ProductEnrichment**: Gerencia o processo de enriquecimento e integração com IA
- **ProductSuggestedImage**: Gerencia imagens sugeridas pela IA

## Integração com MCP-Qdrant

O módulo integra-se com o MCP-Qdrant para armazenamento e busca vetorial de produtos, permitindo:

1. Vetorização automática de produtos
2. Busca semântica de produtos similares
3. Recomendações baseadas em similaridade vetorial

## Requisitos

- Odoo 16
- Módulo `product_ai_mass_management`
- Servidor MCP-Qdrant configurado
- Acesso a APIs de IA (OpenAI, Anthropic, etc.)

## Instalação

1. Clone este repositório na pasta `custom_addons` do seu servidor Odoo
2. Instale as dependências necessárias
3. Ative o módulo através da interface do Odoo
4. Configure os provedores de IA e conectores de marketplace

## Configuração

Após a instalação, é necessário configurar:

1. **Provedores de IA**: Configure as credenciais e modelos a serem utilizados
2. **Conectores de Marketplace**: Configure as credenciais e mapeamentos para cada marketplace
3. **Perfis de Enriquecimento**: Crie perfis para diferentes tipos de produtos
4. **Integração com Qdrant**: Configure a conexão com o servidor MCP-Qdrant

## Uso

O módulo pode ser acessado de três formas:

1. **A partir do módulo de produtos**: Selecione um ou mais produtos e clique em "Enriquecer com IA"
2. **A partir do módulo Product AI Mass Management**: Selecione produtos e clique em "Enriquecer com IA"
3. **Diretamente pelo menu do módulo**: Acesse o dashboard e crie novos enriquecimentos

## Licença

LGPL-3

## Autor

ChatwootAI - https://www.chatwoot.ai
