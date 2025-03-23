// Función para mostrar nombre de archivo seleccionado
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file');
    
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = this.files[0] ? this.files[0].name : 'Ningún archivo seleccionado';
            const fileInfo = document.querySelector('.file-info');
            
            if (fileInfo) {
                fileInfo.textContent = 'Archivo seleccionado: ' + fileName;
            }
        });
    }

    // Añadir efectos visuales a la lista de canciones
    const songItems = document.querySelectorAll('.song-item');
    songItems.forEach(item => {
        item.addEventListener('mouseover', function() {
            this.style.backgroundColor = '#f9f9f9';
        });
        
        item.addEventListener('mouseout', function() {
            if (!this.classList.contains('active')) {
                this.style.backgroundColor = '';
            }
        });
    });
});