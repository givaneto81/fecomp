const themeSwitch = document.getElementById('theme-switch');

const sidebar = document.querySelector('.sidebar');

themeSwitch.addEventListener('change', function() {
    if (this.checked) {
        sidebar.classList.add('dark-mode');
    } else {
        sidebar.classList.remove('dark-mode');
    }
});