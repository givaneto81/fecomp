document.addEventListener('DOMContentLoaded', () => {
    const themeSwitch = document.getElementById('theme-switch');
    const sidebar = document.querySelector('.sidebar');
    const body = document.body;

    themeSwitch.addEventListener('change', () => {
        if (themeSwitch.checked) {
            sidebar.classList.add('dark-mode');
            body.classList.add('dark-mode-body');
        } else {
            sidebar.classList.remove('dark-mode');
            body.classList.remove('dark-mode-body');
        }
    });
});