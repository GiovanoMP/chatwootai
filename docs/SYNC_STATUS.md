# Status da Sincronização de Documentos

Este documento descreve o estado atual da sincronização de documentos entre o Odoo e o sistema de IA (Qdrant).

## Funcionalidades Implementadas

### 1. Remoção de Documentos Não Selecionados

- Documentos que não estão selecionados na interface do usuário (não estão na lista `support_document_ids`) são removidos do Qdrant durante a sincronização.
- Isso garante que apenas os documentos explicitamente selecionados pelo usuário sejam vetorizados e usados pelo sistema de IA.

### 2. Exclusão Permanente de Documentos

- O botão "Excluir Permanentemente" remove completamente o documento do banco de dados do Odoo.
- Na próxima sincronização, o documento é automaticamente removido do Qdrant.
- Esta ação é irreversível - o documento não pode ser recuperado após a exclusão.

## Funcionalidades Recém-Implementadas

### 1. Visualização de Documentos Inativos

- Documentos desativados (botão `active` = False) agora permanecem visíveis na interface do usuário, mas são marcados como inativos.
- Documentos inativos são automaticamente removidos do Qdrant durante a sincronização.
- Isso permite que os usuários vejam todos os documentos, incluindo os inativos, mas apenas os documentos ativos são usados pelo sistema de IA.

### 2. Filtros para Documentos Ativos/Inativos

- Adicionados filtros para mostrar documentos ativos, inativos ou ambos.
- Adicionada opção para agrupar documentos por status de ativação.
- Por padrão, a visualização mostra todos os documentos (ativos e inativos).

## Próximos Passos

2. **Melhorar a documentação**:
   - Adicionar instruções detalhadas sobre como gerenciar documentos
   - Explicar a diferença entre desativação e exclusão permanente

3. **Adicionar testes automatizados**:
   - Implementar testes para verificar se documentos inativos são removidos do Qdrant
   - Implementar testes para verificar se documentos excluídos são removidos do Qdrant
