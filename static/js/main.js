document.addEventListener('DOMContentLoaded', function() {
    // Funcionalidad para mostrar nombre de archivo seleccionado
    const fileInput = document.getElementById('file');
    
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = this.files[0] ? this.files[0].name : 'Ningún archivo seleccionado';
            const fileInfo = document.querySelector('.selected-file-info');
            
            if (fileInfo) {
                fileInfo.textContent = 'Archivo: ' + fileName;
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
    
    // Mejorado: Ocultar mensajes flash con animación
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach(alert => {
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-10px)';
                setTimeout(() => {
                    alert.style.display = 'none';
                }, 500);
            });
        }, 5000);
    }
    
    // Mejorado: Menú móvil con mejor control para evitar apertura accidental
    const menuToggle = document.getElementById('menu-toggle');
    const menuIcon = document.querySelector('.menu-icon');
    const navLinks = document.querySelector('.nav-links');
    
    if (menuToggle && navLinks) {
        // Asegurarse de que el checkbox no esté marcado al cargar
        menuToggle.checked = false;
        
        // Manejar el clic en el icono del menú con un umbral para evitar aperturas accidentales
        let touchStartX = 0;
        let touchEndX = 0;
        const swipeThreshold = 40; // Umbral en píxeles para considerar un deslizamiento intencional
        
        // Prevenir apertura accidental con deslizamientos laterales
        document.addEventListener('touchstart', function(e) {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });
        
        document.addEventListener('touchend', function(e) {
            touchEndX = e.changedTouches[0].screenX;
            // Solo activar el menú si estamos cerca del borde derecho y el deslizamiento es suficientemente largo
            const windowWidth = window.innerWidth;
            const swipeDistance = touchStartX - touchEndX;
            const isEdgeSwipe = touchStartX > windowWidth * 0.85; // Solo detecta swipes desde el 85% derecho de la pantalla
            
            if (swipeDistance > swipeThreshold && isEdgeSwipe && !menuToggle.checked) {
                menuToggle.checked = true;
                e.preventDefault();
            } else if (touchEndX - touchStartX > swipeThreshold && menuToggle.checked) {
                // Cerrar con deslizamiento hacia la derecha
                menuToggle.checked = false;
                e.preventDefault();
            }
        }, { passive: false });
        
        // Clic en el icono del menú
        menuIcon.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            menuToggle.checked = !menuToggle.checked;
        });
        
        // Cerrar menú al hacer clic fuera de él
        document.addEventListener('click', function(event) {
            if (!event.target.closest('.nav-links') && !event.target.closest('.menu-icon') && menuToggle.checked) {
                menuToggle.checked = false;
            }
        });
        
        // Cerrar menú al hacer clic en un enlace (en móvil)
        const navItems = navLinks.querySelectorAll('a');
        navItems.forEach(item => {
            item.addEventListener('click', function() {
                if (window.innerWidth <= 768) {
                    menuToggle.checked = false;
                }
            });
        });
        
        // Añadir soporte para escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && menuToggle.checked) {
                menuToggle.checked = false;
            }
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
        
        // Añadir gestor de errores
        audioPlayer.addEventListener('error', function() {
            showNotification('Error al reproducir el archivo de audio', 'error');
        });
    }
    
    // Función para mostrar notificaciones
    window.showNotification = function(message, type = 'info') {
        const container = document.getElementById('notifications-container');
        
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        
        // Mostrar la notificación con un pequeño retraso para permitir la animación
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Ocultar y eliminar después de 5 segundos
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    };
    
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
    
    // Mejora: Detectar si está en modo oscuro
    function updateDarkModeStatus() {
        const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.body.classList.toggle('dark-mode', isDarkMode);
    }
    
    // Ajustar altura inicial y al redimensionar
    adjustMainHeight();
    updateDarkModeStatus();
    
    window.addEventListener('resize', adjustMainHeight);
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateDarkModeStatus);
});