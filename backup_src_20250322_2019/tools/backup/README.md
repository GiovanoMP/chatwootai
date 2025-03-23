# Arquivos de Backup

Este diretório contém arquivos que foram substituídos ou removidos durante o desenvolvimento do projeto.

## tool_wrappers.py

O arquivo `tool_wrappers.py` foi removido porque decidimos refatorar nossas ferramentas para herdar diretamente de `BaseTool` do CrewAI, em vez de usar wrappers para adaptá-las.

### Motivos para a mudança:

1. **Simplificação do código**: Elimina uma camada de indireção, tornando o código mais fácil de entender.
2. **Consistência**: Todas as ferramentas agora seguem o mesmo padrão, facilitando o trabalho para novos desenvolvedores.
3. **Manutenção**: Reduz a quantidade de código a ser mantido, já que não precisamos mais manter classes wrapper separadas.
4. **Extensibilidade**: Facilita a adição de novas ferramentas no futuro, pois elas podem ser criadas diretamente como subclasses de BaseTool.

### Ferramentas refatoradas:

- `QdrantVectorSearchTool` em `src/tools/vector_tools.py`
- `PGSearchTool` em `src/tools/database_tools.py`
- `TwoLevelCache` em `src/tools/cache_tools.py`

Cada uma dessas ferramentas agora herda diretamente de `BaseTool` e implementa o método `_run` necessário para compatibilidade com o CrewAI.
