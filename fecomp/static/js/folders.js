document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('delete-file-modal');
    const form = document.getElementById('delete-file-form');
    
    document.querySelectorAll('.delete-file-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const fileId = btn.dataset.fileId;
            form.action = `/delete_file/${fileId}`;
            modal.style.display = 'block';
        });
    });

    modal.querySelector('.close-btn').addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });
});