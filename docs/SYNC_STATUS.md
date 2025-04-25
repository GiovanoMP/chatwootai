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

## Problemas Conhecidos

### 1. Documentos Desativados

- Atualmente, quando um documento é desativado (botão `active` = False), ele desaparece da interface do usuário.
- O comportamento desejado é que o documento permaneça visível na interface, mas seja marcado como inativo e seja removido do Qdrant.
- Este problema será corrigido em uma atualização futura.

## Próximos Passos

1. **Corrigir a visualização de documentos inativos**:
   - Modificar as visualizações para mostrar documentos inativos na interface
   - Adicionar um filtro para alternar entre mostrar todos os documentos ou apenas os ativos

2. **Melhorar a documentação**:
   - Adicionar instruções detalhadas sobre como gerenciar documentos
   - Explicar a diferença entre desativação e exclusão permanente

3. **Adicionar testes automatizados**:
   - Implementar testes para verificar se documentos inativos são removidos do Qdrant
   - Implementar testes para verificar se documentos excluídos são removidos do Qdrant
