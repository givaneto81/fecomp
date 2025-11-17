document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.querySelector('.sidebar');
    const mainContainer = document.querySelector('.main-container');
    const menuToggle = document.getElementById('menu-toggle');
    const content = document.querySelector('.content');

    const isMobile = () => window.innerWidth <= 992;

    function setupSidebar() {
        if (isMobile()) {
            // Em dispositivos móveis, a sidebar começa recolhida e fora do ecrã
            sidebar.classList.remove('collapsed');
            mainContainer.classList.remove('sidebar-collapsed');
        } else {
            // Em desktop, a sidebar fica visível
            sidebar.classList.remove('active');
            mainContainer.classList.add('sidebar-collapsed'); // Começa recolhida
            sidebar.classList.add('collapsed'); // <-- A LINHA NO LUGAR CERTO!

            // Expande ao passar o rato
            sidebar.addEventListener('mouseenter', () => {
                if (!isMobile()) {
                    sidebar.classList.remove('collapsed');
                    mainContainer.classList.remove('sidebar-collapsed');
                    // TIREI O ERRO DAQUI
                }
            });

            // Recolhe ao tirar o rato
            sidebar.addEventListener('mouseleave', () => {
                if (!isMobile()) {
                    sidebar.classList.add('collapsed');
                    mainContainer.classList.add('sidebar-collapsed');
                }
            });
        }
    }

    // Lógica para o botão de menu em ecrãs pequenos
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    // Lógica para fechar a sidebar ao clicar fora dela em modo móvel
    content.addEventListener('click', () => {
        if (isMobile() && sidebar.classList.contains('active')) {
            sidebar.classList.remove('active');
        }
    });


    // Configura a sidebar ao carregar e ao redimensionar a janela
    setupSidebar();
    window.addEventListener('resize', setupSidebar);
});