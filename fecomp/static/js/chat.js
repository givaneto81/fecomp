ocument.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.querySelector('.chat-messages');
    const messageInput = document.querySelector('.chat-input');
    const sendBtn = document.querySelector('.chat-send-btn');
    const contextSelect = document.getElementById('chat-context'); // <<< NOVO
    
    const converter = new showdown.Converter();

    const loadContexts = async () => {
        const messageInput_loader = document.querySelector('.chat-input');
        const sendBtn_loader = document.querySelector('.chat-send-btn');

        try {
            const response = await fetch('/api/user_contexts');
            if (!response.ok) throw new Error('Falha ao buscar contextos');
            
            const data = await response.json();
            if (data.contexts && data.contexts.length > 0) {
                const group = document.createElement('optgroup');
                group.label = 'Analisar Documentos da Pasta';
                
                data.contexts.forEach(context => {
                    const option = document.createElement('option');
                    option.value = context.id; // ID da Pasta
                    option.textContent = context.name; // Nome (Ex: Pessoal: Mat / Provas)
                    group.appendChild(option);
                });
                contextSelect.appendChild(group);
            }
        } catch (error) {
            console.error("Erro ao carregar contextos:", error);
        } finally {
            messageInput_loader.disabled = false;
            sendBtn_loader.disabled = false;
            messageInput_loader.placeholder = 'Digite sua dúvida...';
        }
    };

    if (chatMessages && messageInput && sendBtn) {
        const sendMessage = async () => {
            const message = messageInput.value.trim();
            if (!message) return;

            // Adiciona a mensagem do usuário
            const userMessageDiv = document.createElement('div');
            userMessageDiv.classList.add('message', 'sender');
            userMessageDiv.textContent = message;
            chatMessages.appendChild(userMessageDiv);

            messageInput.value = '';
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // Adiciona mensagem de "digitando..."
            const loadingDiv = document.createElement('div');
            loadingDiv.classList.add('message', 'receiver', 'loading');
            loadingDiv.innerHTML = '<span></span><span></span><span></span>';
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // --- LÓGICA DE CONTEXTO (PRIORIDADE 5) ---
            const selectedContext = contextSelect.value;
            let apiUrl = '/api/chat';
            let bodyData = { message: message };

            if (selectedContext !== 'general') {
                apiUrl = '/api/chat_contextual';
                bodyData = { message: message, folder_id: selectedContext };
            }
            // --- FIM DA LÓGICA DE CONTEXTO ---

            try {
                const response = await fetch(apiUrl, { // Usa a URL dinâmica
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(bodyData) // Usa o body dinâmico
                });

                chatMessages.removeChild(loadingDiv); // Remove o "digitando"

                if (!response.ok) {
                    throw new Error('Falha na resposta da API');
                }

                const data = await response.json();
                
                const botMessageDiv = document.createElement('div');
                botMessageDiv.classList.add('message', 'receiver');

                if (data.response && data.response.trim() !== "") {
                    botMessageDiv.innerHTML = converter.makeHtml(data.response);
                } else {
                    botMessageDiv.textContent = 'Desculpe, não consegui gerar uma resposta.';
                }
                chatMessages.appendChild(botMessageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;

            } catch (error) {
                console.error("Erro no chat:", error);
                chatMessages.removeChild(loadingDiv);
                const errorMessageDiv = document.createElement('div');
                errorMessageDiv.classList.add('message', 'receiver');
                errorMessageDiv.textContent = 'Ops! Ocorreu um erro ao conectar com a IA. Tente novamente.';
                chatMessages.appendChild(errorMessageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        };

        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });

        // Carrega os contextos quando a página é aberta
        loadContexts();
    }
});