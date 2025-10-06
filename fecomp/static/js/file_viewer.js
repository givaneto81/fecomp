function openFileViewer(filePath, fileName) {
    const modal = document.getElementById('file-viewer-modal');
    const container = document.getElementById('viewer-container');

    // Limpa o conteúdo anterior
    container.innerHTML = '';

    // Determina o tipo de arquivo pela extensão
    const fileExtension = filePath.split('.').pop().toLowerCase();

    if (['png', 'jpg', 'jpeg', 'gif', 'svg'].includes(fileExtension)) {
        const img = document.createElement('img');
        img.src = filePath;
        img.alt = fileName;
        container.appendChild(img);
    } else if (['mp4', 'webm', 'ogg'].includes(fileExtension)) {
        const video = document.createElement('video');
        video.src = filePath;
        video.controls = true;
        container.appendChild(video);
    } else if (fileExtension === 'pdf') {
        const iframe = document.createElement('iframe');
        iframe.src = filePath;
        iframe.width = '100%';
        iframe.height = '100%';
        container.appendChild(iframe);
    } else {
        // Para outros tipos de arquivo, mostra um link para download
        container.innerHTML = `<p>Visualização não suportada.</p><a href="${filePath}" class="profile-btn" download>Baixar ${fileName}</a>`;
    }

    modal.classList.add('active');
}

document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('file-viewer-modal');
    const closeBtn = document.getElementById('close-viewer-btn');

    if (modal && closeBtn) {
        closeBtn.onclick = () => {
            modal.classList.remove('active');
            // Para o vídeo se o modal for fechado
            const video = modal.querySelector('video');
            if (video) video.pause();
        };
    }

    window.onclick = (event) => {
        if (event.target == modal) {
            modal.classList.remove('active');
            const video = modal.querySelector('video');
            if (video) video.pause();
        }
    };
});