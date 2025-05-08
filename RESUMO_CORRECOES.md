# Resumo das Correções no Módulo Business Rules

## Problemas Identificados

1. **Múltiplas Vetorizações**: Quando um documento é carregado, estão sendo criados 4 arquivos no Qdrant para cada documento.
2. **Botão "Carregar documento" vetoriza o documento**: O botão dentro do bloco de upload estava vetorizando o documento imediatamente, quando deveria apenas carregar o documento.
3. **Falta de enriquecimento de documentos**: Parece que a vetorização está ocorrendo diretamente sem o enriquecimento do contexto pelo agente responsável.
4. **Formato dos documentos no Qdrant**: O formato atual pode não ser o mais adequado para busca semântica com agentes de IA.

## Correções Implementadas

1. **Atualização da mensagem no método `action_create_document` do wizard**: Modificamos a mensagem para informar ao usuário que ele precisa usar o botão "Sincronizar com IA" na tela principal para vetorizar o documento.

```python
return {
    'type': 'ir.actions.client',
    'tag': 'display_notification',
    'params': {
        'title': _('Documento Criado'),
        'message': _('Documento "%s" foi criado com sucesso. IMPORTANTE: Use o botão "Sincronizar com IA" na tela principal para vetorizar o documento.') % self.name,
        'sticky': True,
        'type': 'success',
    }
}
```

2. **Verificação do código**: Confirmamos que a linha que chamava a sincronização automática já estava comentada no método `action_create_document` do wizard:

```python
# Não sincronizar automaticamente - isso será feito pelo botão "Sincronizar com IA"
# self.business_rule_id.action_sync_support_documents()
```

## Recomendações para o Sistema de IA

1. **Usar IDs determinísticos**: Modificar o código para usar um ID determinístico baseado no account_id e no document_id do Odoo, em vez de gerar UUIDs aleatórios:

```python
# Usar um ID determinístico baseado no account_id e document_id
document_id = f"{account_id}_{doc_id}"
```

2. **Verificar existência antes de inserir**: Adicionar verificação se o documento já existe no Qdrant antes de inserir um novo:

```python
# Verificar se o documento já existe
existing_points = vector_service.qdrant_client.scroll(
    collection_name=collection_name,
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="account_id",
                match=models.MatchValue(value=account_id)
            ),
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(value=doc_id)
            )
        ]
    ),
    limit=1,
    with_payload=False,
    with_vectors=False,
)[0]

# Se o documento já existe, usar o mesmo ID
if existing_points:
    document_id = existing_points[0].id
else:
    # Usar um ID determinístico
    document_id = f"{account_id}_{doc_id}"
```

3. **Melhorar o formato dos documentos no Qdrant**: Modificar o formato para usar uma estrutura JSON mais estruturada:

```python
payload={
    "metadata": {
        "account_id": account_id,
        "business_rule_id": business_rule_id,
        "document_id": doc_id,
        "name": doc_name,
        "document_type": doc_type,
        "last_updated": datetime.now().isoformat(),
        "ai_processed": original_text != processed_text
    },
    "content": {
        "original": original_text,
        "processed": processed_text
    },
    # Adicionar campos estruturados extraídos pelo agente
    "structured_data": {
        # Aqui o agente poderia extrair informações estruturadas do documento
        # Por exemplo: categorias, tópicos, entidades, etc.
    }
}
```

4. **Verificar o processamento pelo agente**: Garantir que o agente de enriquecimento está processando os documentos corretamente:

```python
# Processar texto do documento usando o agente
try:
    processed_text = await support_doc_agent.process_data(document_data, business_area)
    logger.info(f"Processed document {doc_id} using support document agent")
    
    # Verificar se o processamento foi bem-sucedido
    if not processed_text or processed_text == original_text:
        logger.warning(f"Document {doc_id} was not enriched by the agent")
except Exception as agent_error:
    logger.error(f"Failed to process document with agent: {agent_error}")
    # Usar o texto original como fallback
    processed_text = original_text
```

## Arquivos Criados

1. **RECOMENDACOES_CORRECAO_VETORIZACAO.md**: Recomendações para corrigir os problemas de vetorização no sistema de IA.
2. **CORRECOES_SISTEMA_IA.md**: Implementação detalhada das correções necessárias no sistema de IA.
3. **TESTE_VETORIZACAO_DOCUMENTOS.md**: Passos para testar o fluxo de upload e vetorização de documentos.
4. **RESUMO_CORRECOES.md**: Este arquivo, que resume as correções e recomendações.

## Próximos Passos

1. Implementar as correções no sistema de IA conforme as recomendações.
2. Testar o fluxo completo de upload e vetorização de documentos para garantir que os problemas foram resolvidos.
3. Considerar a implementação de um formato JSON mais estruturado para os documentos no Qdrant para facilitar a busca semântica.
4. Verificar se o agente de enriquecimento está processando os documentos corretamente.
