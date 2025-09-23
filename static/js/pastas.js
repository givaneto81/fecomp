// fecomp/static/js/pastas.js (VERSÃO CORRIGIDA E LIMPA)

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
    const hexInput = document.getElementById('new_color_hex');
    const pickerInput = document.getElementById('new_color_picker');
    
    form.action = `/update_folder_color/${folderId}`;
    
    // Garante que o valor inicial esteja correto
    const cleanColor = currentColor.startsWith('#') ? currentColor : '#' + currentColor;
    hexInput.value = cleanColor.slice(1);
    pickerInput.value = cleanColor;

    // Limpa eventos antigos para evitar múltiplos gatilhos
    const newHexInput = hexInput.cloneNode(true);
    hexInput.parentNode.replaceChild(newHexInput, hexInput);
    const newPickerInput = pickerInput.cloneNode(true);
    pickerInput.parentNode.replaceChild(newPickerInput, pickerInput);

    // Sincroniza os dois inputs
    newHexInput.addEventListener('input', () => newPickerInput.value = '#' + newHexInput.value);
    newPickerInput.addEventListener('input', () => newHexInput.value = newPickerInput.value.slice(1));

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
    document.querySelectorAll('.rename-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            openRenameModal(btn.dataset.folderId, btn.dataset.folderName);
        });
    });

    document.querySelectorAll('.color-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            openColorModal(btn.dataset.folderId, btn.dataset.folderColor);
        });
    });

    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            openDeleteModal(btn.dataset.folderId);
        });
    });

    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });

    document.querySelectorAll('.modal .close-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal').style.display = 'none';
        });
    });
});