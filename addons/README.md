# Módulos Odoo para Integração com Sistema de IA

Este diretório contém módulos Odoo desenvolvidos para integração com o sistema de IA ChatwootAI. Estes módulos permitem personalizar o comportamento dos agentes de IA, gerenciar produtos e configurar regras de negócio.

## Módulos Disponíveis

### 1. Descrição Semântica de Produtos (semantic_product_description)

Módulo para enriquecer as descrições de produtos com metadados semânticos, permitindo buscas mais precisas no sistema de IA. Este módulo adiciona campos para descrições enriquecidas e integra-se com o sistema de vetorização para busca semântica.

**Principais funcionalidades:**
- Adição de descrições enriquecidas para produtos
- Interface para edição de descrições
- Sincronização com o sistema de vetorização
- Integração com Qdrant para busca semântica

### 2. Gerenciamento em Massa de Produtos no Sistema de IA (product_ai_mass_management)

Módulo para gerenciar múltiplos produtos no sistema de IA de forma eficiente, com interface visual e indicadores de status.

**Principais funcionalidades:**
- Vista de lista com seleção múltipla
- Badges coloridos para status visual rápido
- Sincronização em massa de produtos
- Ajustes de preço em massa
- Monitoramento de popularidade de produtos

### 3. Regras de Negócio para Sistema de IA (business_rules)

Módulo para configurar regras de negócio específicas que personalizam o comportamento dos agentes de IA de acordo com as necessidades de cada empresa.

**Principais funcionalidades:**
- Configuração de informações básicas da empresa
- Definição de regras de atendimento
- Seleção de modelo de negócio com regras pré-configuradas
- Criação de regras personalizadas e temporárias
- Upload e processamento de documentos
- Sincronização com o sistema de IA

## Instalação

Cada módulo possui seu próprio script de instalação. Para instalar um módulo:

1. Execute o script de instalação correspondente:
   ```
   ./install_semantic_module.sh
   ./install_product_ai_mass_management.sh
   ./install_business_rules.sh
   ```

2. Atualize a lista de módulos no Odoo e instale o módulo desejado

## Dependências

Alguns módulos requerem dependências específicas:

- **business_rules**: Requer `python-docx==0.8.11` e `PyPDF2==1.26.0` para processamento de documentos

## Arquitetura

Estes módulos fazem parte de uma arquitetura maior que inclui:

- **MCP (Multi-Client Protocol)**: Camada de abstração para comunicação com diferentes ERPs
- **CrewAI**: Sistema de agentes de IA para processamento de solicitações
- **Qdrant**: Banco de dados vetorial para busca semântica
- **Redis**: Cache para armazenamento de credenciais e resultados de busca

## Desenvolvimento

Para contribuir com o desenvolvimento destes módulos:

1. Clone o repositório
2. Crie uma nova branch para suas alterações
3. Implemente as mudanças
4. Execute os testes
5. Envie um pull request

---

**Desenvolvido por:** ChatwootAI Team  
**Versão:** 1.0  
**Compatibilidade:** Odoo 14.0
