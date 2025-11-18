document.addEventListener('DOMContentLoaded', () => {
    // Seleciona ambos os controlos de tema
    const themeSwitchCheckbox = document.getElementById('theme-switch-checkbox');
    const themeToggleButton = document.getElementById('theme-toggle-btn');
    const body = document.body;

    // Função para aplicar o tema e atualizar o estado do interruptor (checkbox)
    const applyTheme = (theme) => {
        if (theme === 'dark') {
            body.classList.add('dark-mode');
            if (themeSwitchCheckbox) themeSwitchCheckbox.checked = true;
        } else {
            body.classList.remove('dark-mode');
            if (themeSwitchCheckbox) themeSwitchCheckbox.checked = false;
        }
    };

    // Carrega o tema salvo ao iniciar
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);

    // Função centralizada para gerir a mudança de tema
    const handleThemeChange = (newTheme) => {
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    };

    // Evento para o interruptor on/off (checkbox)
    if (themeSwitchCheckbox) {
        themeSwitchCheckbox.addEventListener('change', () => {
            const newTheme = themeSwitchCheckbox.checked ? 'dark' : 'light';
            handleThemeChange(newTheme);
        });
    }

    // Evento para o botão de ícone único
    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', () => {
            const isDarkMode = body.classList.contains('dark-mode');
            const newTheme = isDarkMode ? 'light' : 'dark';
            handleThemeChange(newTheme);
        });
    }

    // --- CÓDIGO NOVO (PONTO 3) ---
    // --- LÓGICA PARA MENSAGENS FLASH ---
    const flashMessages = document.querySelectorAll('.alert-flash');
    flashMessages.forEach(function(message) {
        // Define um timeout para fazer a mensagem desaparecer
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s ease-out';
            message.style.opacity = '0';
            // Remove o elemento do DOM após a transição
            setTimeout(() => { 
                message.style.display = 'none'; 
            }, 500); // Tempo da transição
        }, 5000); // 5 segundos
    });
    // --- FIM DA LÓGICA FLASH ---
});