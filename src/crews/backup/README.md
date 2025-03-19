# Arquivos de Backup

Este diretório contém arquivos que foram substituídos ou removidos do projeto principal para evitar duplicação e confusão.

## hub_crew.py.bak

Este arquivo era uma implementação alternativa do HubCrew que foi substituída pela implementação em `src/core/hub.py`. 

### Razões para a substituição:

1. **Duplicação de funcionalidade**: A classe HubCrew em `src/crews/hub_crew.py` era redundante, pois já tínhamos uma implementação mais completa em `src/core/hub.py`.

2. **Dependência circular**: O arquivo `hub_crew.py` importava componentes de `src/core/hub.py`, o que criava uma dependência circular confusa.

3. **Assinaturas de métodos incompatíveis**: As assinaturas dos métodos (como `process_message`) eram diferentes entre as duas implementações, causando erros quando o webhook tentava chamar esses métodos.

4. **Manutenção da arquitetura**: A implementação em `src/core/hub.py` segue melhor as práticas de engenharia de software e a arquitetura hub-and-spoke definida no projeto.

### Data da substituição:

18 de março de 2025
