document.addEventListener('DOMContentLoaded', () => {
    const modalMapping = {
        'edit-name-btn': 'edit-name-modal',
        'change-password-btn': 'change-password-modal',
        'delete-account-btn': 'delete-account-modal'
    };

    for (const btnId in modalMapping) {
        const btn = document.getElementById(btnId);
        const modalId = modalMapping[btnId];
        const modal = document.getElementById(modalId);
        
        if (btn && modal) {
            btn.addEventListener('click', () => {
                modal.style.display = 'block';
            });
        }
    }

    document.querySelectorAll('.modal .close-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.target.closest('.modal').style.display = 'none';
        });
    });

    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
});