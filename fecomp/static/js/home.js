// fecomp/static/js/home.js (VERSÃO CORRIGIDA E UNIFICADA)

document.addEventListener('DOMContentLoaded', () => {
    const addSubjectForm = document.getElementById('add-subject-form');

    // --- Lógica para Adicionar Matéria com AJAX ---
    if (addSubjectForm) {
        addSubjectForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const subjectNameInput = addSubjectForm.querySelector('input[name="subject_name"]');
            const subjectName = subjectNameInput.value.trim();
            if (!subjectName) return;

            try {
                const response = await fetch('/api/add_subject', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ subject_name: subjectName }),
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error);
                
                createNewSubjectCard(data.subject);
                subjectNameInput.value = '';
            } catch (error) {
                console.error('Erro:', error);
                alert('Não foi possível adicionar a matéria.');
            }
        });
    }

    // --- Lógica para os Modais de Apagar e Mudar a Cor ---
    const subjectGrid = document.querySelector('.subject-grid');
    const deleteModal = document.getElementById('delete-subject-modal');
    const colorModal = document.getElementById('color-subject-modal');

    subjectGrid.addEventListener('click', (event) => {
        const deleteBtn = event.target.closest('.delete-subject-btn');
        const colorBtn = event.target.closest('.color-subject-btn');

        if (deleteBtn && deleteModal) {
            const subjectId = deleteBtn.dataset.subjectId;
            const form = deleteModal.querySelector('#delete-subject-form');
            form.action = `/delete_subject/${subjectId}`;
            deleteModal.classList.add('active');
        }

        if (colorBtn && colorModal) {
            const subjectId = colorBtn.dataset.subjectId;
            const currentColor = colorBtn.dataset.subjectColor;
            const form = colorModal.querySelector('#color-subject-form');
            const hexInput = colorModal.querySelector('#new_subject_color_hex');
            const pickerInput = colorModal.querySelector('#new_subject_color_picker');
            
            form.action = `/update_subject_color/${subjectId}`;
            hexInput.value = currentColor.slice(1);
            pickerInput.value = currentColor;
            
            hexInput.oninput = () => pickerInput.value = '#' + hexInput.value;
            pickerInput.oninput = () => hexInput.value = pickerInput.value.slice(1);
            
            colorModal.classList.add('active');
        }
    });

    // --- Lógica genérica para fechar qualquer modal ---
    document.querySelectorAll('.modal').forEach(modal => {
        modal.querySelector('.close-btn')?.addEventListener('click', () => {
            modal.classList.remove('active');
        });
    });
    window.addEventListener('click', (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.classList.remove('active');
        }
    });
});

function createNewSubjectCard(subject) {
    const grid = document.querySelector('.subject-grid');
    if (!grid) return;

    const cardDiv = document.createElement('div');
    cardDiv.className = 'subject-card contrast-card';
    cardDiv.style.backgroundColor = subject.color;

    cardDiv.innerHTML = `
        <a href="${subject.urls.pastas}" class="subject-link">${subject.name}</a>
        <div class="subject-actions">
            <button class="action-btn color-subject-btn" data-subject-id="${subject.id}" data-subject-color="${subject.color}"><i data-feather="droplet"></i></button>
            <button class="action-btn delete-subject-btn" data-subject-id="${subject.id}"><i data-feather="trash-2"></i></button>
        </div>
    `;

    document.querySelector('.empty-message')?.remove();
    grid.appendChild(cardDiv);
    feather.replace();

    // Re-aplica a lógica de contraste de cor
    if (typeof applyContrastToCards === 'function') {
        applyContrastToCards();
    }
}