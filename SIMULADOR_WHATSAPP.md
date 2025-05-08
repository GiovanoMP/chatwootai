# Simulador de WhatsApp para Testes

Este simulador permite testar o sistema de integração Chatwoot-CrewAI sem depender da API oficial do WhatsApp. Ele simula mensagens do WhatsApp enviando webhooks para o sistema exatamente como o Chatwoot faria quando recebe uma mensagem real.

## Funcionalidades

- Interface web semelhante ao WhatsApp
- Envio de mensagens simuladas para o sistema
- Exibição das respostas do sistema
- Configuração de parâmetros como Account ID, Conversation ID e Contact ID
- Histórico de mensagens salvo localmente

## Como Usar

1. **Inicie o simulador**:
   ```bash
   ./start_simulator.sh
   ```

2. **Acesse a interface web**:
   O navegador abrirá automaticamente em `http://localhost:8080/simulator`

3. **Configure o simulador**:
   - **URL do Webhook**: URL do seu sistema (padrão: `http://localhost:8001/webhook`)
   - **ID da Conversa**: ID da conversa no Chatwoot (padrão: 4)
   - **ID do Contato**: ID do contato no Chatwoot (padrão: 3)
   - **ID da Conta**: ID da conta no Chatwoot (padrão: 1)

4. **Envie mensagens**:
   - Digite sua mensagem na caixa de texto e pressione Enter ou clique no botão de enviar
   - A mensagem será enviada para seu sistema como se fosse uma mensagem do WhatsApp
   - O sistema processará a mensagem e enviará uma resposta
   - A resposta aparecerá automaticamente no simulador

## Como Funciona

O simulador consiste em três componentes principais:

1. **Interface Web** (`whatsapp_simulator.html` e `whatsapp_simulator.js`):
   - Simula a interface do WhatsApp
   - Permite enviar mensagens e ver respostas
   - Salva configurações e histórico localmente

2. **Servidor Proxy** (`whatsapp_proxy.py`):
   - Recebe mensagens da interface web
   - Encaminha para o sistema como webhooks do Chatwoot
   - Monitora os logs para capturar respostas
   - Envia as respostas de volta para a interface web

3. **Script de Inicialização** (`start_simulator.sh`):
   - Inicia o servidor proxy
   - Abre o navegador com a interface web
   - Gerencia dependências e processos

## Parâmetros Importantes

### Account ID

O parâmetro `Account ID` é especialmente importante, pois é usado pelo sistema para:

- Identificar o cliente (tenant) no sistema multitenancy
- Carregar as configurações específicas do cliente
- Direcionar a mensagem para a crew correta

Certifique-se de usar o Account ID correto para testar diferentes configurações de cliente.

## Dicas para Testes

1. **Teste diferentes Account IDs**:
   - Use diferentes Account IDs para testar o comportamento multitenancy do sistema
   - Verifique se cada Account ID carrega as configurações corretas

2. **Teste diferentes tipos de perguntas**:
   - Perguntas simples para testar o fluxo básico
   - Perguntas complexas para testar a capacidade de processamento
   - Perguntas específicas de domínio para testar o conhecimento do sistema

3. **Observe os logs**:
   - Monitore os logs do sistema para ver como ele processa as mensagens
   - Verifique os tempos de resposta para identificar gargalos

4. **Teste cenários de erro**:
   - Envie mensagens malformadas para testar a robustez do sistema
   - Teste com Account IDs inexistentes para ver como o sistema lida com erros

## Solução de Problemas

Se o simulador não estiver funcionando corretamente, verifique:

1. **Servidor do sistema está rodando?**
   - Certifique-se de que seu sistema está rodando na URL configurada

2. **Porta correta?**
   - Verifique se a porta do servidor proxy (8080) está disponível

3. **Logs do proxy**:
   - Verifique os logs do servidor proxy para identificar problemas

4. **Conexão com o sistema**:
   - Verifique se o proxy consegue se conectar ao sistema

## Limitações

1. **Detecção de respostas**:
   - O simulador monitora os logs para detectar respostas, o que pode não ser 100% confiável
   - Em alguns casos, pode ser necessário atualizar a página para ver novas respostas

2. **Simulação parcial**:
   - O simulador não replica todos os aspectos da API do WhatsApp, apenas o necessário para testar o sistema

3. **Funcionalidades avançadas**:
   - Não suporta mídia (imagens, áudio, vídeo)
   - Não simula grupos ou listas de transmissão
