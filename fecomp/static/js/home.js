document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('delete-subject-modal');
    const closeBtn = document.getElementById('close-delete-subject-modal');
    const form = document.getElementById('delete-subject-form');

    // Abre o modal
    document.querySelectorAll('.delete-subject-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const subjectId = btn.dataset.subjectId;
            // Define a action do formulário para a rota correta
            form.action = `/delete_subject/${subjectId}`;
            modal.style.display = 'block';
        });
    });

    // Fecha o modal pelo botão 'X'
    if (closeBtn) {
        closeBtn.onclick = () => {
            modal.style.display = 'none';
        };
    }

    // Fecha o modal clicando fora
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };

    // Adiciona evento para o botão de cor
    document.querySelectorAll('.color-subject-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const subjectId = btn.dataset.subjectId;
            const subjectColor = btn.dataset.subjectColor;
            openColorSubjectModal(subjectId, subjectColor);
        });
    });
});

// Adicione esta função e o event listener em home.js
function openColorSubjectModal(subjectId, currentColor) {
    const modal = document.getElementById('color-subject-modal');
    const form = document.getElementById('color-subject-form');
    const hexInput = document.getElementById('new_subject_color_hex');
    const pickerInput = document.getElementById('new_subject_color_picker');

    form.action = `/update_subject_color/${subjectId}`;
    hexInput.value = currentColor.slice(1);
    pickerInput.value = currentColor;

    hexInput.addEventListener('input', () => pickerInput.value = '#' + hexInput.value);
    pickerInput.addEventListener('input', () => hexInput.value = pickerInput.value.slice(1));

    modal.style.display = 'block';
}