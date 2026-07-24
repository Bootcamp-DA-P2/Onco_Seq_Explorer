/* ============================================
   ONCOSLENS TOUR - NAVEGACIÓN
   ============================================ */

// Mapeo de apartados
const TOUR_APARTADOS = [
    { id: 1, titulo: 'Introducción', url: '/tour/01-introduccion/', nombre: 'introduccion' },
    { id: 2, titulo: 'Datos y Metodología', url: '/tour/02-datos-metodologia/', nombre: 'datos-metodologia' },
    { id: 3, titulo: 'Resultados Clave', url: '/tour/03-resultados/', nombre: 'resultados' },
    { id: 4, titulo: 'Demo', url: '/tour/04-demo/', nombre: 'demo' },
    { id: 5, titulo: 'Limitaciones', url: '/tour/05-limitaciones/', nombre: 'limitaciones' },
    { id: 6, titulo: 'Desarrollos Futuros', url: '/tour/06-desarrollos/', nombre: 'desarrollos' },
    { id: 7, titulo: 'Equipo y Agradecimientos', url: '/tour/07-equipo/', nombre: 'equipo' }
];

// Detectar apartado actual
function detectarApartadoActual() {
    const pathname = window.location.pathname;
    return TOUR_APARTADOS.find(apt => pathname.includes(apt.nombre));
}

// Actualizar indicador de progreso
function actualizarProgreso() {
    const apartado = detectarApartadoActual();
    const progressEl = document.querySelector('.tour-progress');
    
    if (progressEl && apartado) {
        progressEl.textContent = `${String(apartado.id).padStart(2, '0')} / 07`;
    }
}

// Navegar al siguiente apartado
function nextApartado() {
    const apartado = detectarApartadoActual();
    
    if (!apartado) {
        console.warn('No se pudo detectar el apartado actual');
        return;
    }
    
    const siguiente = TOUR_APARTADOS[apartado.id];
    
    if (siguiente) {
        window.location.href = siguiente.url;
    } else {
        // Si es el último apartado, ir al inicio
        console.log('Fin del tour');
        window.location.href = '/';
    }
}

// Navegación por teclado
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault();
        nextApartado();
    }
    
    if (e.key === 'ArrowLeft') {
        e.preventDefault();
        prevApartado();
    }
});

// Navegar al apartado anterior
function prevApartado() {
    const apartado = detectarApartadoActual();
    
    if (!apartado) return;
    
    const anterior = TOUR_APARTADOS[apartado.id - 2]; // -2 porque índice empieza en 0
    
    if (anterior) {
        window.location.href = anterior.url;
    }
}

// Gestión de scroll snap
function handleScrollSnap() {
    const container = document.querySelector('.tour-container');
    
    if (!container) return;
    
    // Detectar si el usuario llegó al final
    container.addEventListener('scroll', () => {
        const scrollHeight = container.scrollHeight;
        const scrollTop = container.scrollTop;
        const clientHeight = container.clientHeight;
        
        // Si está cerca del final, mostrar opción de ir al siguiente
        if (scrollTop + clientHeight >= scrollHeight - 100) {
            // Automáticamente mostrar/destacar botón next
            const btnNext = document.querySelector('.tour-btn-next');
            if (btnNext) {
                btnNext.style.opacity = '1';
            }
        }
    });
}

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    actualizarProgreso();
    handleScrollSnap();
    
    // Agregar event listener al botón siguiente
    const btnNext = document.querySelector('.tour-btn-next');
    if (btnNext) {
        btnNext.addEventListener('click', nextApartado);
    }
    
    // Swipe gestures para móvil (opcional)
    setupSwipeGestures();
});

// Gestos táctiles para móvil
function setupSwipeGestures() {
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    }, false);
    
    document.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, false);
    
    function handleSwipe() {
        if (touchEndX < touchStartX - 50) {
            // Swipe izquierda = siguiente
            nextApartado();
        }
        if (touchEndX > touchStartX + 50) {
            // Swipe derecha = anterior
            prevApartado();
        }
    }
}

// Funciones útiles para navegación avanzada
function irApartado(numero) {
    if (numero < 1 || numero > TOUR_APARTADOS.length) {
        console.warn('Número de apartado inválido');
        return;
    }
    window.location.href = TOUR_APARTADOS[numero - 1].url;
}

function mostrarMenuApartados() {
    const menu = TOUR_APARTADOS.map((apt, idx) => 
        `<a href="${apt.url}" class="tour-menu-item">${apt.id}. ${apt.titulo}</a>`
    ).join('');
    
    console.log('Apartados disponibles:', menu);
}

// Analítica simple (opcional)
function registrarVisita() {
    const apartado = detectarApartadoActual();
    if (apartado && window.gtag) {
        gtag('event', 'tour_apartado', {
            apartado_id: apartado.id,
            apartado_nombre: apartado.titulo
        });
    }
}

// Ejecutar al cargar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', registrarVisita);
} else {
    registrarVisita();
}
