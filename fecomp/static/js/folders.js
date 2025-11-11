document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('delete-file-modal');
    const form = document.getElementById('delete-file-form');
    
    document.querySelectorAll('.delete-file-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const fileId = btn.dataset.fileId;
            form.action = `/delete_file/${fileId}`;
            modal.classList.add('active');
        });
    });

    modal.querySelector('.close-btn').addEventListener('click', () => {
        modal.classList.remove('active');
    });

    window.addEventListener('click', (event) => {
        if (event.target == modal) {
            modal.classList.remove('active');
        }
    });

    // --- LÓGICA DO CHAT CONTEXTUAL (PROPOSTA 1) ---
    const contextModal = document.getElementById('context-chat-modal');
    const openBtn = document.getElementById('context-chat-open-btn');
    const closeBtn = contextModal.querySelector('.close-btn');
    const submitBtn = document.getElementById('context-chat-submit-btn');
    const input = document.getElementById('context-chat-input');
    const responseArea = document.getElementById('context-chat-response-area');
    
    // Converte Markdown para HTML
    const converter = new showdown.Converter();

    if (openBtn) {
        openBtn.addEventListener('click', () => {
            contextModal.classList.add('active');
            input.focus();
        });
    }

    closeBtn.addEventListener('click', () => {
        contextModal.classList.remove('active');
    });

    window.addEventListener('click', (event) => {
        if (event.target == contextModal) {
            contextModal.classList.remove('active');
        }
    });

    const handleContextChatSubmit = async () => {
        const message = input.value.trim();
        const folderId = openBtn.dataset.folderId;
        if (!message) return;

        input.value = '';
        input.disabled = true;
        submitBtn.disabled = true;

        // Adiciona mensagem do usuário
        const userMessageDiv = document.createElement('div');
        userMessageDiv.classList.add('message', 'sender');
        userMessageDiv.textContent = message;
        responseArea.appendChild(userMessageDiv);
        responseArea.scrollTop = responseArea.scrollHeight;

        // Adiciona "digitando..."
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'receiver', 'loading');
        loadingDiv.innerHTML = '<span></span><span></span><span></span>';
        responseArea.appendChild(loadingDiv);
        responseArea.scrollTop = responseArea.scrollHeight;

        try {
            const response = await fetch('/api/chat_contextual', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, folder_id: folderId })
            });
            
            responseArea.removeChild(loadingDiv); // Remove o "digitando"

            if (!response.ok) throw new Error('Falha na resposta da API');

            const data = await response.json();
            const botMessageDiv = document.createElement('div');
            botMessageDiv.classList.add('message', 'receiver');
            
            // Converte a resposta (que vem em Markdown) para HTML
            botMessageDiv.innerHTML = converter.makeHtml(data.response);
            
            responseArea.appendChild(botMessageDiv);
        
        } catch (error) {
            console.error("Erro no chat contextual:", error);
            responseArea.removeChild(loadingDiv); // Remove o "digitando"
            const errorDiv = document.createElement('div');
            errorDiv.classList.add('message', 'receiver');
            errorDiv.textContent = 'Ops! Ocorreu um erro ao conectar com a IA. Tente novamente.';
            responseArea.appendChild(errorDiv);
        } finally {
            input.disabled = false;
            submitBtn.disabled = false;
            input.focus();
            responseArea.scrollTop = responseArea.scrollHeight;
        }
    };

    submitBtn.addEventListener('click', handleContextChatSubmit);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleContextChatSubmit();
        }
    });
    // --- FIM DA LÓGICA (PROPOSTA 1) ---
});