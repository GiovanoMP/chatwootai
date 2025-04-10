# Módulo de Descrições Inteligentes de Produtos

Este módulo adiciona campos estruturados para descrições de produtos otimizadas para IA, facilitando buscas inteligentes e melhorando a experiência do cliente.

## Funcionalidades

- **Descrição do produto otimizada para IA**: Campo para descrição concisa do produto
- **Descrição gerada por IA**: Campo editável para descrições detalhadas geradas automaticamente
- **Principais características**: Lista estruturada de características do produto
- **Cenários de uso**: Lista de casos de uso comuns para o produto
- **Variações e características adicionais**: Tags para facilitar a busca semântica
- **Verificação humana**: Sistema de verificação para garantir qualidade
- **Integração com sistema de vetorização**: Preparado para integração com Qdrant

## Instalação

1. Copie o módulo para o diretório de addons do Odoo
2. Atualize a lista de módulos no Odoo: Aplicativos > Atualizar Lista de Aplicativos
3. Instale o módulo "Descrições Inteligentes de Produtos"

## Uso

1. Acesse qualquer produto no Odoo
2. Vá para a aba "Descrição do Produto para IA"
3. Preencha os campos de descrição, características e casos de uso
4. Clique em "Gerar Descrição com IA" para criar automaticamente uma descrição detalhada
5. Edite a descrição gerada conforme necessário
6. Clique em "Verificar e Aprovar" para marcar a descrição como verificada
7. Use "Sincronizar com Sistema de IA" para enviar ao sistema de vetorização

## Métodos para Integração com MCP e Sistema de Vetorização

Este módulo foi projetado para integração com o MCP (Message Control Program) e sistemas de vetorização como Qdrant. Abaixo estão os principais métodos que facilitam essa integração:

### `generate_semantic_description()`

**Descrição**: Gera automaticamente uma descrição inteligente baseada nos metadados do produto.

**Funcionalidade**:
- Coleta metadados disponíveis do produto (nome, categoria, preço, estoque, etc.)
- Cria uma descrição estruturada combinando esses metadados
- Gera listas de características principais
- Atualiza os campos `semantic_description` e `ai_generated_description`
- Define o status de sincronização como `needs_update`

**Uso para integração**:
```python
# Exemplo de chamada via MCP
product_ids = [1, 2, 3]  # IDs dos produtos
env['product.template'].browse(product_ids).generate_semantic_description()
```

### `verify_semantic_description()`

**Descrição**: Marca a descrição como verificada por um humano.

**Funcionalidade**:
- Define o campo `semantic_description_verified` como `True`
- Atualiza a data da última modificação
- Define o status de sincronização como `needs_update` para indicar que precisa ser sincronizado

**Uso para integração**:
```python
# Exemplo de chamada via MCP
product_id = 1  # ID do produto
env['product.template'].browse(product_id).verify_semantic_description()
```

### `mark_for_sync()`

**Descrição**: Marca o produto para sincronização com o sistema de IA.

**Funcionalidade**:
- Define o status de sincronização como `needs_update`
- Pode ser chamado manualmente ou automaticamente após alterações

**Uso para integração**:
```python
# Exemplo de chamada via MCP
product_id = 1  # ID do produto
env['product.template'].browse(product_id).mark_for_sync()
```

### `get_products_for_sync()`

**Descrição**: Retorna produtos que precisam ser sincronizados com o sistema de vetorização.

**Funcionalidade**:
- Busca produtos com status `needs_update`
- Pode ser usado para sincronização em lote

**Uso para integração**:
```python
# Exemplo de chamada via MCP
products_to_sync = env['product.template'].get_products_for_sync()
# Processar produtos para sincronização com Qdrant
```

### `update_sync_status(product_id, status, vector_id=None)`

**Descrição**: Atualiza o status de sincronização de um produto.

**Funcionalidade**:
- Define o status de sincronização (`synced`, `not_synced`, `needs_update`)
- Opcionalmente, atualiza o ID do vetor no banco de dados vetorial

**Uso para integração**:
```python
# Exemplo de chamada via MCP após sincronização com Qdrant
product_id = 1
vector_id = "vec_12345"
env['product.template'].update_sync_status(product_id, 'synced', vector_id)
```

### `get_product_vector_data(product_id)`

**Descrição**: Retorna dados estruturados do produto para vetorização.

**Funcionalidade**:
- Coleta todos os dados relevantes do produto em formato estruturado
- Inclui descrição, características, casos de uso e tags
- Formata os dados para processamento pelo sistema de vetorização

**Uso para integração**:
```python
# Exemplo de chamada via MCP para obter dados para Qdrant
product_id = 1
vector_data = env['product.template'].get_product_vector_data(product_id)
# Processar vector_data para criar embeddings e armazenar no Qdrant
```

## Integração com MCP

Para integrar este módulo com o MCP, recomendamos criar um endpoint específico no MCP que possa:

1. Receber solicitações para gerar descrições para produtos
2. Buscar produtos que precisam ser sincronizados
3. Atualizar o status de sincronização após processamento
4. Gerenciar a comunicação entre o Odoo e o sistema de vetorização (Qdrant)

Exemplo de fluxo de integração:

```
[Odoo] -> [MCP] -> [Sistema de Vetorização (Qdrant)]
   ^         |              |
   |         v              v
   +-------- + <------------+
```

## Integração com Sistema de Vetorização (Qdrant)

O módulo está preparado para integração com Qdrant através dos seguintes passos:

1. Usar `get_products_for_sync()` para identificar produtos que precisam ser sincronizados
2. Para cada produto, usar `get_product_vector_data()` para obter dados estruturados
3. Processar esses dados para criar embeddings usando OpenAI ou outro modelo
4. Armazenar os embeddings no Qdrant com metadados apropriados
5. Atualizar o status de sincronização usando `update_sync_status()`

## Notas de Desenvolvimento

- O módulo usa campos específicos para facilitar a integração com sistemas de IA
- Os métodos são projetados para serem chamados via XML-RPC ou através do MCP
- O sistema de status de sincronização permite rastrear quais produtos precisam ser atualizados
- A verificação humana garante qualidade antes da sincronização

## Contribuições

Para contribuir com este módulo:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Faça commit das suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Faça push para a branch (`git push origin feature/nova-feature`)
5. Crie um novo Pull Request

## Licença

Este módulo está licenciado sob LGPL-3.
