function openColorModal(folderId, currentColor) {
    const modal = document.getElementById('color-modal');
    const form = document.getElementById('color-form');
    const hexInput = document.getElementById('new_color_hex');
    const pickerInput = document.getElementById('new_color_picker');

    form.action = `/update_folder_color/${folderId}`;
    hexInput.value = currentColor.slice(1);
    pickerInput.value = currentColor;

    // Sincroniza os dois inputs
    hexInput.addEventListener('input', () => pickerInput.value = '#' + hexInput.value);
    pickerInput.addEventListener('input', () => hexInput.value = pickerInput.value.slice(1));

    modal.style.display = 'block';
}

function openRenameModal(folderId, currentName) {
    const modal = document.getElementById('rename-modal');
    const form = document.getElementById('rename-form');
    const input = document.getElementById('new_folder_name');
    form.action = `/rename_folder/${folderId}`;
    input.value = currentName;
    modal.style.display = 'block';
}

function openColorModal(folderId, currentColor) {
    const modal = document.getElementById('color-modal');
    const form = document.getElementById('color-form');
    const input = document.getElementById('new_color');
    form.action = `/update_folder_color/${folderId}`;
    input.value = currentColor;
    modal.style.display = 'block';
}

function openDeleteModal(folderId) {
    const modal = document.getElementById('delete-modal');
    const form = document.getElementById('delete-form');
    form.action = `/delete_folder/${folderId}`;
    modal.style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Event Listeners para os botões e modais
document.addEventListener('DOMContentLoaded', () => {
    // Adiciona evento aos botões de renomear
    document.querySelectorAll('.rename-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const folderId = btn.dataset.folderId;
            const folderName = btn.dataset.folderName;
            openRenameModal(folderId, folderName);
        });
    });

    // Adiciona evento aos botões de cor
    document.querySelectorAll('.color-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const folderId = btn.dataset.folderId;
            const folderColor = btn.dataset.folderColor;
            openColorModal(folderId, folderColor);
        });
    });

    // Adiciona evento aos botões de deletar
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const folderId = btn.dataset.folderId;
            openDeleteModal(folderId);
        });
    });

    // Fecha o modal se o usuário clicar fora dele
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });

    // Adiciona evento aos botões 'X' dos modais
    document.querySelectorAll('.modal .close-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal').style.display = 'none';
        });
    });
}); 