// chat.js
document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.querySelector('.chat-messages');
    const messageInput = document.querySelector('.chat-input');
    const sendBtn = document.querySelector('.chat-send-btn');

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

            // Adiciona mensagem de carregando
            const loadingDiv = document.createElement('div');
            loadingDiv.classList.add('message', 'receiver');
            loadingDiv.textContent = 'Aguardando resposta...';
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                const botResponse = data.response;

                // Remove mensagem de carregando
                chatMessages.removeChild(loadingDiv);

                const botMessageDiv = document.createElement('div');
                botMessageDiv.classList.add('message', 'receiver');

                if (botResponse && botResponse.trim() !== "") {
                    botMessageDiv.textContent = botResponse;
                } else {
                    botMessageDiv.textContent = 'Desculpe, não consegui gerar uma resposta.';
                }
                chatMessages.appendChild(botMessageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;

            } catch (error) {
                chatMessages.removeChild(loadingDiv);
                const errorMessageDiv = document.createElement('div');
                errorMessageDiv.classList.add('message', 'receiver');
                errorMessageDiv.textContent = 'Desculpe, não consegui me conectar com a IA.';
                chatMessages.appendChild(errorMessageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        };

        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }
});