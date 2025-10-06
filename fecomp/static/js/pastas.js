
document.addEventListener('DOMContentLoaded', () => {
    // Mapeamento dos modais para evitar repetição
    const modals = {
        rename: document.getElementById('rename-modal'),
        color: document.getElementById('color-modal'),
        delete: document.getElementById('delete-modal')
    };

    // Delegação de eventos no contêiner principal para funcionar com elementos futuros
    document.querySelector('.file-grid').addEventListener('click', (event) => {
        const renameBtn = event.target.closest('.rename-btn');
        const colorBtn = event.target.closest('.color-btn');
        const deleteBtn = event.target.closest('.delete-btn');

        if (renameBtn) {
            const modal = modals.rename;
            const form = modal.querySelector('#rename-form');
            const input = modal.querySelector('#new_folder_name');
            form.action = `/rename_folder/${renameBtn.dataset.folderId}`;
            input.value = renameBtn.dataset.folderName;
            modal.classList.add('active');
        }

        if (colorBtn) {
            const modal = modals.color;
            const form = modal.querySelector('#color-form');
            const hexInput = modal.querySelector('#new_color_hex');
            const pickerInput = modal.querySelector('#new_color_picker');
            const currentColor = colorBtn.dataset.folderColor;

            form.action = `/update_folder_color/${colorBtn.dataset.folderId}`;
            hexInput.value = currentColor.slice(1);
            pickerInput.value = currentColor;
            
            // Sincroniza os inputs de cor
            hexInput.oninput = () => pickerInput.value = '#' + hexInput.value;
            pickerInput.oninput = () => hexInput.value = pickerInput.value.slice(1);

            modal.classList.add('active');
        }

        if (deleteBtn) {
            const modal = modals.delete;
            const form = modal.querySelector('#delete-form');
            form.action = `/delete_folder/${deleteBtn.dataset.folderId}`;
            modal.classList.add('active');
        }
    });

    // Lógica para fechar QUALQUER modal
    document.querySelectorAll('.modal').forEach(modal => {
        // Pelo botão de fechar (X)
        modal.querySelector('.close-btn')?.addEventListener('click', () => {
            modal.classList.remove('active');
        });
    });

    // Clicando fora do modal (no fundo)
    window.addEventListener('click', (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.classList.remove('active');
        }
    });
});