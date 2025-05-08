document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatContainer = document.getElementById('chat-container');
    const webhookUrlInput = document.getElementById('webhook-url');
    const conversationIdInput = document.getElementById('conversation-id');
    const contactIdInput = document.getElementById('contact-id');
    const accountIdInput = document.getElementById('account-id');
    const statusDiv = document.getElementById('status');

    // URL do proxy
    const proxyUrl = window.location.href.includes('localhost:8080')
        ? 'http://localhost:8080/webhook'
        : 'http://localhost:8080/webhook';

    // Histórico de mensagens
    let messageHistory = [];

    // Carregar histórico do localStorage se existir
    if (localStorage.getItem('whatsappSimulatorHistory')) {
        try {
            messageHistory = JSON.parse(localStorage.getItem('whatsappSimulatorHistory'));
            renderMessageHistory();
        } catch (e) {
            console.error('Erro ao carregar histórico:', e);
        }
    }

    // Carregar configurações do localStorage se existirem
    if (localStorage.getItem('whatsappSimulatorConfig')) {
        try {
            const config = JSON.parse(localStorage.getItem('whatsappSimulatorConfig'));
            webhookUrlInput.value = config.webhookUrl || webhookUrlInput.value;
            conversationIdInput.value = config.conversationId || conversationIdInput.value;
            contactIdInput.value = config.contactId || contactIdInput.value;
            accountIdInput.value = config.accountId || accountIdInput.value;
        } catch (e) {
            console.error('Erro ao carregar configurações:', e);
        }
    }

    // Salvar configurações quando alteradas
    webhookUrlInput.addEventListener('change', saveConfig);
    conversationIdInput.addEventListener('change', saveConfig);
    contactIdInput.addEventListener('change', saveConfig);
    accountIdInput.addEventListener('change', saveConfig);

    function saveConfig() {
        const config = {
            webhookUrl: webhookUrlInput.value,
            conversationId: conversationIdInput.value,
            contactId: contactIdInput.value,
            accountId: accountIdInput.value
        };
        localStorage.setItem('whatsappSimulatorConfig', JSON.stringify(config));
    }

    // Enviar mensagem quando o botão for clicado
    sendButton.addEventListener('click', function(e) {
        e.preventDefault();
        window.sendMessage();
    });

    // Enviar mensagem quando Enter for pressionado
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            window.sendMessage();
        }
    });

    // Backup para garantir que o Enter funcione
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            window.sendMessage();
        }
    });

    // Tornar a função sendMessage global para que possa ser chamada do HTML
    window.sendMessage = function() {
        console.log('Função sendMessage chamada');
        const messageContent = messageInput.value.trim();
        if (!messageContent) {
            console.log('Mensagem vazia, não enviando');
            return;
        }

        console.log('Enviando mensagem:', messageContent);

        // Desabilitar o botão e o campo de entrada durante o envio
        sendButton.disabled = true;
        messageInput.disabled = true;

        try {
            // Adicionar mensagem do usuário ao chat
            addMessageToChat(messageContent, 'user');

            // Limpar campo de entrada
            messageInput.value = '';

            // Mostrar status de espera
            showStatus('waiting', 'Enviando mensagem e aguardando resposta...');

            // Enviar webhook para o sistema
            sendWebhook(messageContent)
                .then(response => {
                    console.log('Resposta recebida:', response);
                    // Verificar se a resposta contém uma mensagem do bot
                    if (response && response.has_response) {
                        // A resposta real virá como um novo webhook do sistema
                        // Não precisamos fazer nada aqui, pois o sistema enviará um webhook de volta
                        showStatus('success', 'Mensagem enviada com sucesso! Aguardando resposta do sistema...');
                    } else {
                        showStatus('success', 'Mensagem enviada com sucesso! Nenhuma resposta esperada.');
                    }
                })
                .catch(error => {
                    console.error('Erro ao enviar mensagem:', error);
                    showStatus('error', `Erro ao enviar mensagem: ${error.message}`);
                })
                .finally(() => {
                    // Reabilitar o botão e o campo de entrada
                    sendButton.disabled = false;
                    messageInput.disabled = false;
                    messageInput.focus();
                });
        } catch (error) {
            console.error('Erro ao processar envio:', error);
            showStatus('error', `Erro ao processar envio: ${error.message}`);

            // Reabilitar o botão e o campo de entrada
            sendButton.disabled = false;
            messageInput.disabled = false;
            messageInput.focus();
        }
    }

    function sendWebhook(messageContent) {
        // Usar o proxy em vez da URL direta
        const webhookUrl = proxyUrl;
        // Guardar a URL original para referência
        const systemUrl = webhookUrlInput.value;
        const conversationId = parseInt(conversationIdInput.value);
        const contactId = parseInt(contactIdInput.value);
        const accountId = parseInt(accountIdInput.value);
        const timestamp = Math.floor(Date.now() / 1000);

        console.log('Enviando mensagem para:', webhookUrl);
        console.log('Parâmetros:', { conversationId, contactId, accountId });

        // Construir o payload do webhook
        const messageId = Math.floor(Math.random() * 1000) + 100; // ID aleatório para a mensagem

        // Usar apenas o formato que o webhook handler espera
        let webhookData;

        // Formato com campo "message" separado (formato correto)
        console.log("Usando formato de webhook com campo 'message' separado");
        webhookData = {
            "event": "message_created",
            "message": {
                "id": messageId,
                "content": messageContent,
                "content_type": "text",
                "content_attributes": {},
                "created_at": new Date().toISOString(),
                "message_type": "incoming", // Usar string "incoming" em vez de 0
                "private": false,
                "source_id": null,
                "sender_type": "Contact",
                "sender_id": contactId
            },
                "conversation": {
                    "id": conversationId,
                    "inbox_id": 4,
                    "status": "open",
                    "additional_attributes": {},
                    "channel": "Channel::Whatsapp",
                    "contact_inbox": {
                        "id": 3,
                        "contact_id": contactId,
                        "inbox_id": 4,
                        "source_id": "5511977379888",
                        "created_at": "2025-05-01T00:41:46.600Z",
                        "updated_at": "2025-05-01T00:41:46.600Z",
                        "hmac_verified": false,
                        "pubsub_token": "AaTX14w68Yw3atKU3H93S8Vb"
                    },
                    "meta": {
                        "sender": {
                            "id": contactId,
                            "name": "Usuário Simulado",
                            "phone_number": "+5511977379888",
                            "type": "contact"
                        }
                    },
                    "timestamp": timestamp,
                    "created_at": timestamp - 1000,
                    "updated_at": timestamp
                },
                "account": {
                    "id": accountId,
                    "name": "Sprintia"
                },
                "inbox": {
                    "id": 4,
                    "name": "WhatsApp"
                },
                "sender": {
                    "id": contactId,
                    "name": "Usuário Simulado",
                    "email": null,
                    "type": "contact"
                }
            };
        }

        return fetch(webhookUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(webhookData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
    }

    function addMessageToChat(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');

        // Formatar links, negrito, etc.
        const formattedContent = formatMessage(content);
        messageDiv.innerHTML = formattedContent;

        const timeDiv = document.createElement('div');
        timeDiv.classList.add('message-time');
        const now = new Date();
        timeDiv.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;

        messageDiv.appendChild(timeDiv);
        chatContainer.appendChild(messageDiv);

        // Rolar para a última mensagem
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Adicionar ao histórico
        messageHistory.push({
            content: content,
            sender: sender,
            timestamp: now.toISOString()
        });

        // Salvar histórico no localStorage
        localStorage.setItem('whatsappSimulatorHistory', JSON.stringify(messageHistory));
    }

    function formatMessage(content) {
        // Substituir URLs por links clicáveis
        content = content.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');

        // Substituir **texto** por <strong>texto</strong>
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Substituir *texto* por <em>texto</em>
        content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Substituir quebras de linha por <br>
        content = content.replace(/\n/g, '<br>');

        return content;
    }

    function renderMessageHistory() {
        chatContainer.innerHTML = '';
        messageHistory.forEach(message => {
            addMessageToChat(message.content, message.sender);
        });
    }

    function showStatus(type, message) {
        statusDiv.className = 'status';
        statusDiv.innerHTML = '';

        if (type === 'waiting') {
            const loadingSpinner = document.createElement('div');
            loadingSpinner.className = 'loading';
            statusDiv.appendChild(loadingSpinner);
            statusDiv.className = 'status waiting';
        } else if (type === 'success') {
            statusDiv.className = 'status success';
        } else if (type === 'error') {
            statusDiv.className = 'status error';
        }

        statusDiv.appendChild(document.createTextNode(message));

        // Limpar status após 5 segundos se for sucesso
        if (type === 'success') {
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
    }

    // Configurar polling para verificar novas mensagens
    let lastMessageId = 0;

    // Variável para controlar o polling
    let isPolling = true;
    let pollCount = 0;
    const MAX_EMPTY_POLLS = 30; // Após 30 polls sem novas mensagens, reduz a frequência

    function pollForMessages() {
        if (!isPolling) return;

        // Usar a URL relativa para evitar problemas de CORS
        const messagesUrl = window.location.href.includes('localhost:8080')
            ? 'http://localhost:8080/messages'
            : '/messages';

        fetch(messagesUrl)
            .then(response => response.json())
            .then(data => {
                // Verificar se há novas mensagens
                const messages = data.messages || [];
                const newMessages = messages.filter(msg => msg.id > lastMessageId && msg.sender === 'bot');

                if (newMessages.length > 0) {
                    console.log('Novas mensagens encontradas:', newMessages);

                    // Atualizar o último ID de mensagem
                    lastMessageId = Math.max(...messages.map(msg => msg.id));

                    // Adicionar novas mensagens do bot ao chat
                    newMessages.forEach(msg => {
                        addMessageToChat(msg.content, 'bot');
                    });

                    // Resetar contador de polls vazios
                    pollCount = 0;
                } else {
                    // Incrementar contador de polls vazios
                    pollCount++;
                }
            })
            .catch(error => {
                console.error('Erro ao buscar mensagens:', error);
                pollCount++;
            })
            .finally(() => {
                // Continuar polling com intervalo adaptativo
                const pollInterval = pollCount > MAX_EMPTY_POLLS ? 10000 : 2000; // 10s após 30 polls vazios
                setTimeout(pollForMessages, pollInterval);
            });
    }

    // Parar polling quando a página for fechada
    window.addEventListener('beforeunload', () => {
        isPolling = false;
    });

    // Iniciar polling
    pollForMessages();

    // Função para simular a recepção de uma resposta do bot
    // Útil para testes
    window.receiveResponse = function(content) {
        addMessageToChat(content, 'bot');
    };
});
