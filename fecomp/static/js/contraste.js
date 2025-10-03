function getTextColorForBackground(hexColor) {
    if (hexColor.startsWith('#')) {
        hexColor = hexColor.slice(1);
    }

    const r = parseInt(hexColor.substr(0, 2), 16);
    const g = parseInt(hexColor.substr(2, 2), 16);
    const b = parseInt(hexColor.substr(4, 2), 16);

    // Fórmula de luminância
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b);

    // Limiar de 186 (pode ser ajustado)
    return luminance > 186 ? '#000000' : '#FFFFFF';
}

function applyContrastToCards() {
    document.querySelectorAll('.contrast-card').forEach(card => {
        const bgColor = card.style.backgroundColor;
        // Converte a cor rgb() para hex
        const hexColor = rgbToHex(bgColor);
        const textColor = getTextColorForBackground(hexColor);

        card.style.color = textColor;
        // Aplica a cor aos ícones dentro do card também
        card.querySelectorAll('.feather').forEach(icon => {
            icon.style.color = textColor;
        });
    });
}

function rgbToHex(rgb) {
    if (!rgb || !rgb.includes('rgb')) return '#007bff'; // Cor padrão
    let [r, g, b] = rgb.match(/\d+/g).map(Number);
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

document.addEventListener('DOMContentLoaded', applyContrastToCards);