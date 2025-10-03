document.addEventListener('DOMContentLoaded', () => {
    const themeSwitch = document.getElementById('theme-switch-checkbox');
    const body = document.body;

    // Função para aplicar o tema
    const applyTheme = (theme) => {
        if (theme === 'dark') {
            body.classList.add('dark-mode');
            if (themeSwitch) themeSwitch.checked = true;
        } else {
            body.classList.remove('dark-mode');
            if (themeSwitch) themeSwitch.checked = false;
        }
    };

    // Verifica se já existe um tema salvo no localStorage
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);

    // Adiciona o evento de clique no interruptor
    if (themeSwitch) {
        themeSwitch.addEventListener('change', () => {
            const newTheme = themeSwitch.checked ? 'dark' : 'light';
            localStorage.setItem('theme', newTheme); // Salva a nova preferência
            applyTheme(newTheme);
        });
    }
});