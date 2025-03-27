// static/js/mobile-pagination.js
/**
 * mobile-pagination.js
 * Implementa navegação otimizada para dispositivos móveis com suporte a gestos de deslize
 * e carregamento assíncrono de conteúdo.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Verificar se o AlunosManager está ativo antes de inicializar
    // Aguarda um momento para garantir que o AlunosManager tenha tempo de ser inicializado
    setTimeout(() => {
        initializeMobilePagination();
    }, 100);
    
    function initializeMobilePagination() {
        // Elementos principais
        const alunosContainer = document.getElementById('alunos-container');
        const loadingSpinner = document.getElementById('loading-spinner');
        const prevButton = document.querySelector('.prev-page');
        const nextButton = document.querySelector('.next-page');
        
        // Verificar se o AlunosManager está ativo
        const alunosManagerActive = window.alunosManagerActive === true;
        
        // Adicionar estilos CSS dinamicamente (isso sempre é necessário)
        addMobilePaginationStyles();
        
        // Inicializar eventos de toque para deslize (sempre necessário para mobile)
        initSwipeEvents();
        
        // Inicializar feedback tátil (sempre necessário para mobile)
        initHapticFeedback();
        
        // Se o AlunosManager estiver ativo, usaremos apenas recursos de UI móvel
        // sem o comportamento AJAX duplicado
        if (!alunosManagerActive) {
            // Inicializar eventos de clique para botões de paginação apenas 
            // se o AlunosManager não estiver ativo
            initPaginationButtons();
        } else {
            // Apenas conecte os eventos de botões móveis ao manipulador do AlunosManager
            connectMobileButtonsToAlunosManager();
        }
        
        // Variáveis para controle de deslize
        let touchStartX = 0;
        let touchEndX = 0;
        let isSwiping = false;
    
        /**
         * Conecta os botões de navegação móvel ao manipulador do AlunosManager
         */
        // Em mobile-pagination.js
function connectMobileButtonsToAlunosManager() {
    const prevButton = document.querySelector('.prev-page');
    const nextButton = document.querySelector('.next-page');
    
    if (prevButton) {
        prevButton.addEventListener('click', function(e) {
            e.preventDefault();
            if (window.handlePaginationClick) {
                window.handlePaginationClick(e, this.dataset.url);
            }
        });
    }
    
    if (nextButton) {
        nextButton.addEventListener('click', function(e) {
            e.preventDefault();
            if (window.handlePaginationClick) {
                window.handlePaginationClick(e, this.dataset.url);
            }
        });
    }
}
        
        /**
         * Inicializa eventos de deslize para navegação entre páginas
         */
        function initSwipeEvents() {
            if (!alunosContainer) return;
            
            // Criar elementos de feedback visual para deslize
            const leftFeedback = document.createElement('div');
            leftFeedback.className = 'swipe-feedback left';
            
            const rightFeedback = document.createElement('div');
            rightFeedback.className = 'swipe-feedback right';
            
            alunosContainer.appendChild(leftFeedback);
            alunosContainer.appendChild(rightFeedback);
            
            // Eventos de toque
            alunosContainer.addEventListener('touchstart', handleTouchStart, { passive: true });
            alunosContainer.addEventListener('touchmove', handleTouchMove, { passive: true });
            alunosContainer.addEventListener('touchend', handleTouchEnd, { passive: true });
            
            function handleTouchStart(e) {
                touchStartX = e.touches[0].clientX;
                isSwiping = true;
            }
            
            function handleTouchMove(e) {
                if (!isSwiping) return;
                
                touchEndX = e.touches[0].clientX;
                const diffX = touchStartX - touchEndX;
                
                // Mostrar feedback visual baseado na direção do deslize
                if (diffX > 50) {
                    rightFeedback.classList.add('active');
                    leftFeedback.classList.remove('active');
                } else if (diffX < -50) {
                    leftFeedback.classList.add('active');
                    rightFeedback.classList.remove('active');
                } else {
                    leftFeedback.classList.remove('active');
                    rightFeedback.classList.remove('active');
                }
            }
            
            function handleTouchEnd(e) {
                if (!isSwiping) return;
                
                const diffX = touchStartX - touchEndX;
                const minSwipeDistance = 100; // Distância mínima para considerar um deslize
                
                // Remover feedback visual
                leftFeedback.classList.remove('active');
                rightFeedback.classList.remove('active');
                
                // Verificar se o AlunosManager está ativo
                if (alunosManagerActive && window.handlePaginationClick) {
                    // Deslize para a direita (próxima página)
                    if (diffX > minSwipeDistance && nextButton && !nextButton.classList.contains('disabled')) {
                        triggerHapticFeedback();
                        
                        // Usar o manipulador centralizado de paginação
                        const mockEvent = { 
                            currentTarget: nextButton, 
                            preventDefault: function() {} 
                        };
                        window.handlePaginationClick(mockEvent, nextButton.dataset.url);
                    }
                    
                    // Deslize para a esquerda (página anterior)
                    if (diffX < -minSwipeDistance && prevButton && !prevButton.classList.contains('disabled')) {
                        triggerHapticFeedback();
                        
                        // Usar o manipulador centralizado de paginação
                        const mockEvent = { 
                            currentTarget: prevButton, 
                            preventDefault: function() {} 
                        };
                        window.handlePaginationClick(mockEvent, prevButton.dataset.url);
                    }
                } else {
                    // Comportamento legado
                    // Deslize para a direita (próxima página)
                    if (diffX > minSwipeDistance && nextButton && !nextButton.classList.contains('disabled')) {
                        triggerHapticFeedback();
                        legacyLoadPage(nextButton.dataset.url);
                    }
                    
                    // Deslize para a esquerda (página anterior)
                    if (diffX < -minSwipeDistance && prevButton && !prevButton.classList.contains('disabled')) {
                        triggerHapticFeedback();
                        legacyLoadPage(prevButton.dataset.url);
                    }
                }
                
                isSwiping = false;
            }
        }
        
        /**
         * Inicializa eventos de clique para botões de paginação (modo legado)
         */
        function initPaginationButtons() {
            // Botão de página anterior
            if (prevButton) {
                prevButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    triggerHapticFeedback();
                    legacyLoadPage(this.dataset.url);
                });
            }
            
            // Botão de próxima página
            if (nextButton) {
                nextButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    triggerHapticFeedback();
                    legacyLoadPage(this.dataset.url);
                });
            }
            
            // Converter links de paginação desktop para AJAX
            document.querySelectorAll('.pagination .page-link').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    legacyLoadPage(this.getAttribute('href'));
                });
            });
        }
    
        /**
         * Carrega uma página de forma assíncrona usando AJAX (comportamento legado)
         * @param {string} url - URL da página a ser carregada
         */
        function legacyLoadPage(url) {
            if (!url) return;
            
            // Mostrar indicador de carregamento
            if (loadingSpinner) {
                loadingSpinner.style.display = 'block';
            }
            
            // Adicionar classe de transição para efeito visual
            if (alunosContainer) {
                alunosContainer.classList.add('page-transition');
            }
            
            // Fazer requisição AJAX
            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                // Criar um DOM temporário para extrair o conteúdo
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                // Atualizar o conteúdo dos alunos
                const newContent = doc.getElementById('alunos-container');
                if (newContent && alunosContainer) {
                    alunosContainer.innerHTML = newContent.innerHTML;
                }
                
                // Atualizar a paginação
                updatePaginationControls(doc);
                
                // Atualizar a URL no histórico do navegador
                window.history.pushState({}, '', url);
                
                // Atualizar contador de resultados
                const totalResults = doc.getElementById('total-results');
                if (totalResults) {
                    document.getElementById('total-results').textContent = totalResults.textContent;
                }
            })
            .catch(error => {
                console.error('Erro ao carregar a página:', error);
            })
            .finally(() => {
                // Ocultar indicador de carregamento
                if (loadingSpinner) {
                    loadingSpinner.style.display = 'none';
                }
                
                // Remover classe de transição
                if (alunosContainer) {
                    alunosContainer.classList.remove('page-transition');
                }
                
                // Rolar para o topo da lista
                document.getElementById('results-container').scrollIntoView({ behavior: 'smooth' });
            });
        }
        
        /**
         * Atualiza os controles de paginação com base na nova página carregada
         * @param {Document} doc - Documento DOM da nova página
         */
        function updatePaginationControls(doc) {
            // Atualizar botões de paginação mobile
            const newPrevButton = doc.querySelector('.prev-page');
            const newNextButton = doc.querySelector('.next-page');
            const newCurrentPage = doc.querySelector('.current-page');
            
            if (newPrevButton && prevButton) {
                if (newPrevButton.classList.contains('disabled')) {
                    prevButton.classList.add('disabled');
                    prevButton.removeAttribute('data-url');
                } else {
                    prevButton.classList.remove('disabled');
                    prevButton.dataset.url = newPrevButton.dataset.url;
                }
            }
            
            if (newNextButton && nextButton) {
                if (newNextButton.classList.contains('disabled')) {
                    nextButton.classList.add('disabled');
                    nextButton.removeAttribute('data-url');
                } else {
                    nextButton.classList.remove('disabled');
                    nextButton.dataset.url = newNextButton.dataset.url;
                }
            }
            
            if (newCurrentPage) {
                document.querySelector('.current-page').textContent = newCurrentPage.textContent;
            }
            
            // Atualizar paginação desktop
            const newDesktopPagination = doc.querySelector('.pagination');
            if (newDesktopPagination) {
                document.querySelector('.pagination').innerHTML = newDesktopPagination.innerHTML;
                
                // Se o AlunosManager não estiver ativo, reconecte os eventos aqui
                if (!alunosManagerActive) {
                    // Reconectar eventos de clique apenas no modo legado
                    document.querySelectorAll('.pagination .page-link').forEach(link => {
                        link.addEventListener('click', function(e) {
                            e.preventDefault();
                            legacyLoadPage(this.getAttribute('href'));
                        });
                    });
                }
            }
        }
        
        /**
         * Inicializa feedback tátil (vibração) se disponível no dispositivo
         */
        function initHapticFeedback() {
            // Verificar se a API de vibração está disponível
            if ('vibrate' in navigator) {
                // Adicionar feedback tátil aos botões
                document.querySelectorAll('.btn-pagination').forEach(btn => {
                    btn.addEventListener('touchstart', function() {
                        if (!this.classList.contains('disabled')) {
                            navigator.vibrate(20); // Vibração curta de 20ms
                        }
                    });
                });
            }
        }
        
        /**
         * Aciona feedback tátil (vibração) se disponível
         */
        function triggerHapticFeedback() {
            if ('vibrate' in navigator) {
                navigator.vibrate(20);
            }
        }
        
        /**
         * Adiciona estilos CSS para paginação mobile dinamicamente
         */
        function addMobilePaginationStyles() {
            // Verificar se o arquivo CSS já foi carregado
            if (!document.querySelector('link[href*="mobile-pagination.css"]')) {
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = '/static/css/mobile-pagination.css';
                document.head.appendChild(link);
            }
        }
    }
});

// Esta função permanece acessível globalmente
function preloadNextPage() {
    // Apenas execute se AlunosManager não estiver ativo
    if (window.alunosManagerActive) return;
    
    const nextButton = document.querySelector('.next-page');
    if (nextButton && nextButton.dataset.url) {
        const nextUrl = nextButton.dataset.url;
        fetch(nextUrl, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
    }
}
