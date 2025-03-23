document.addEventListener('DOMContentLoaded', function() {
    // Funcionalidad para mostrar nombre de archivo seleccionado
    const fileInput = document.getElementById('file');
    
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = this.files[0] ? this.files[0].name : 'Ningún archivo seleccionado';
            const fileInfo = document.querySelector('.selected-file-info');
            
            if (fileInfo) {
                fileInfo.textContent = 'Archivo seleccionado: ' + fileName;
                if (this.files[0]) {
                    fileInfo.classList.add('has-file');
                } else {
                    fileInfo.classList.remove('has-file');
                }
            }
        });
    }

    // Añadir efectos visuales a la lista de canciones
    const songItems = document.querySelectorAll('.song-item');
    songItems.forEach(item => {
        item.addEventListener('mouseover', function() {
            if (!this.classList.contains('active')) {
                this.style.backgroundColor = 'rgba(142, 68, 173, 0.05)';
            }
        });
        
        item.addEventListener('mouseout', function() {
            if (!this.classList.contains('active')) {
                this.style.backgroundColor = '';
            }
        });
    });
    
    // Sistema de pestañas
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const tabId = this.getAttribute('data-tab');
                
                // Remover clase active de todos los botones y contenidos
                tabBtns.forEach(b => b.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));
                
                // Añadir clase active al botón y contenido actual
                this.classList.add('active');
                document.getElementById(tabId).classList.add('active');
            });
        });
    }
    
    // Ocultar mensajes flash después de 5 segundos
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach(alert => {
                alert.style.opacity = '0';
                setTimeout(() => {
                    alert.style.display = 'none';
                }, 500);
            });
        }, 5000);
    }
    
    // Menú móvil
    const menuToggle = document.getElementById('menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('change', function() {
            if (this.checked) {
                navLinks.style.maxHeight = navLinks.scrollHeight + 'px';
            } else {
                navLinks.style.maxHeight = '0';
            }
        });
        
        // Cerrar menú al hacer clic en un enlace (en móvil)
        const navItems = navLinks.querySelectorAll('a');
        navItems.forEach(item => {
            item.addEventListener('click', function() {
                if (window.innerWidth <= 768) {
                    menuToggle.checked = false;
                    navLinks.style.maxHeight = '0';
                }
            });
        });
    }
    
    // Reproducción en secuencia de canciones
    const audioPlayer = document.querySelector('audio');
    if (audioPlayer) {
        // Reproducir siguiente canción al terminar la actual
        audioPlayer.addEventListener('ended', function() {
            const currentSong = document.querySelector('.song-item.active');
            if (currentSong) {
                const nextSong = currentSong.nextElementSibling;
                if (nextSong) {
                    const playLink = nextSong.querySelector('.btn.play');
                    if (playLink) {
                        window.location.href = playLink.href;
                    }
                }
            }
        });
    }
    
    // Función para ajustar altura del contenido principal
    function adjustMainHeight() {
        const header = document.querySelector('header');
        const footer = document.querySelector('footer');
        const main = document.querySelector('main');
        
        if (header && footer && main) {
            const windowHeight = window.innerHeight;
            const headerHeight = header.offsetHeight;
            const footerHeight = footer.offsetHeight;
            const mainMinHeight = windowHeight - headerHeight - footerHeight - 40; // 40px de margen
            
            main.style.minHeight = mainMinHeight + 'px';
        }
    }
    
    // Ajustar altura inicial y al redimensionar
    adjustMainHeight();
    window.addEventListener('resize', adjustMainHeight);
});