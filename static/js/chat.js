// fecomp/static/js/chat.js
document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.querySelector('.chat-messages');
    const messageInput = document.querySelector('.chat-input');
    const sendBtn = document.querySelector('.chat-send-btn');
    
    // Inicializa o conversor de Markdown
    const converter = new showdown.Converter();

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
            loadingDiv.innerHTML = '<span></span><span></span><span></span>'; // Animação de "digitando"
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });

                chatMessages.removeChild(loadingDiv); // Remove o "digitando"

                if (!response.ok) {
                    throw new Error('Falha na resposta da API');
                }

                const data = await response.json();
                
                const botMessageDiv = document.createElement('div');
                botMessageDiv.classList.add('message', 'receiver');

                if (data.response && data.response.trim() !== "") {
                    // CONVERTE A RESPOSTA EM HTML E INSERE
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
                e.preventDefault(); // Impede de pular linha
                sendMessage();
            }
        });
    }
});