// fecomp/static/js/perfil.js (VERSÃO CORRIGIDA)

document.addEventListener('DOMContentLoaded', () => {
    // Mapeia os botões aos seus respectivos modais
    const modalMapping = {
        'edit-name-btn': 'edit-name-modal',
        'change-password-btn': 'change-password-modal',
        'delete-account-btn': 'delete-account-modal'
    };

    // Adiciona o evento de clique para cada botão abrir seu modal
    for (const btnId in modalMapping) {
        const btn = document.getElementById(btnId);
        const modal = document.getElementById(modalMapping[btnId]);
        
        if (btn && modal) {
            btn.addEventListener('click', () => {
                modal.classList.add('active'); // Abre usando a classe
            });
        }
    }

    // Adiciona o evento de clique para fechar qualquer modal pelo botão 'X'
    document.querySelectorAll('.modal .close-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal').classList.remove('active'); // Fecha usando a classe
        });
    });

    // Adiciona o evento de clique para fechar qualquer modal clicando no fundo
    window.addEventListener('click', (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.classList.remove('active'); // Fecha usando a classe
        }
    });
});