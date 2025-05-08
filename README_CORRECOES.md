# Correções no Sistema de IA para Vetorização de Documentos

Este documento descreve as correções implementadas no sistema de IA para resolver o problema de múltiplas vetorizações de documentos.

## Problema

Quando um documento de suporte era sincronizado com o sistema de IA, estavam sendo criados 4 vetores diferentes no Qdrant para o mesmo documento. Isso causava problemas de duplicação e poderia afetar a qualidade das respostas do sistema de IA.

## Correções Implementadas

1. **Uso de IDs determinísticos**: Substituímos a geração de UUIDs aleatórios por IDs determinísticos baseados no account_id e document_id.

2. **Verificação e limpeza de duplicatas**: Adicionamos verificação se o documento já existe no Qdrant antes de inserir um novo, e implementamos lógica para excluir duplicatas existentes.

3. **Melhoria no formato dos documentos**: Melhoramos o formato dos documentos no Qdrant para facilitar a busca semântica, usando uma estrutura JSON mais organizada.

4. **Compatibilidade com código existente**: Mantivemos campos de compatibilidade com o código existente para evitar quebrar outras partes do sistema.

5. **Logs detalhados**: Adicionamos logs detalhados para facilitar a depuração.

6. **Melhoria no agente de enriquecimento**: Modificamos o agente para estruturar os documentos em formato JSON, facilitando a análise por agentes de IA.

## Arquivos Modificados

- `odoo_api/modules/business_rules/services.py`: Modificamos o método `sync_support_documents_with_data` para usar IDs determinísticos, verificar a existência de documentos antes de inserir novos e excluir duplicatas. Também atualizamos os métodos `get_processed_support_document` e `get_all_processed_support_documents` para lidar com o novo formato de payload.

- `odoo_api/embedding_agents/business_rules/support_docs_agent.py`: Modificamos o agente para estruturar os documentos em formato JSON.

- `addons/business_rules/models/business_rules.py`: Atualizamos o método `_call_mcp_sync_support_docs` para usar o endpoint correto.

## Scripts de Teste e Utilitários

Criamos os seguintes scripts para testar as correções e limpar duplicatas:

1. `testar_correcoes.py`: Script para testar as correções implementadas no sistema de IA. Este script limpa os vetores existentes no Qdrant, sincroniza um documento e verifica se apenas um vetor foi criado.

2. `limpar_vetores_qdrant.py`: Script para limpar todos os vetores existentes no Qdrant para um determinado account_id.

3. `verificar_vetores_qdrant.py`: Script para verificar os vetores no Qdrant.

4. `limpar_duplicatas.py`: Script para identificar e remover documentos duplicados no Qdrant, mantendo apenas um vetor por documento.

## Como Testar

### 1. Limpar os vetores existentes

```bash
python limpar_vetores_qdrant.py --account_id=account_1
```

### 2. Testar as correções

```bash
python testar_correcoes.py --api-url=http://localhost:8001 --account-id=account_1 --business-rule-id=1 --document-id=1
```

**Nota**: O script usa o endpoint `/api/v1/business-rules/sync-support-documents` para sincronizar documentos de suporte.

### 3. Verificar os vetores no Qdrant

```bash
python verificar_vetores_qdrant.py --account_id=account_1 --document_id=1
```

### 4. Limpar duplicatas existentes

```bash
python limpar_duplicatas.py --account_id=account_1
```

Para apenas verificar as duplicatas sem excluí-las, use a opção `--dry-run`:

```bash
python limpar_duplicatas.py --account_id=account_1 --dry-run
```

## Resultados Esperados

1. Após limpar os vetores existentes, não deve haver nenhum vetor no Qdrant para o account_id e document_id especificados.

2. Após sincronizar um documento, deve haver apenas um vetor no Qdrant para o account_id e document_id especificados.

3. O ID do vetor deve ser determinístico, no formato `{account_id}_{document_id}`.

4. O payload do vetor deve conter a estrutura melhorada, com campos `metadata`, `content` e `structured_data`.

5. Após executar o script `limpar_duplicatas.py`, não deve haver duplicatas no Qdrant.

## Conclusão

Estas correções resolvem o problema de múltiplas vetorizações no sistema de IA. Agora, quando um documento é sincronizado, apenas um vetor é criado no Qdrant, usando um ID determinístico baseado no account_id e document_id.

Se o documento já existe no Qdrant, o vetor existente é atualizado, em vez de criar um novo vetor. Isso evita a duplicação de vetores e melhora a qualidade das respostas do sistema de IA.

Além disso, o script `limpar_duplicatas.py` permite limpar duplicatas existentes, garantindo que haja apenas um vetor por documento no Qdrant.
