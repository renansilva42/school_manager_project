// static/js/pagination.js
document.addEventListener('DOMContentLoaded', function() {
    const pagination = document.querySelector('.pagination');
    
    if (pagination) {
        // Adiciona loading state aos links
        pagination.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', function(e) {
                if (!this.classList.contains('disabled') && !this.parentElement.classList.contains('disabled')) {
                    // Adicionar spinner apenas se for um link válido
                    const hasSpinner = this.querySelector('.spinner-border');
                    if (!hasSpinner) {
                        const spinner = document.createElement('span');
                        spinner.className = 'spinner-border spinner-border-sm ms-2';
                        spinner.setAttribute('role', 'status');
                        spinner.setAttribute('aria-hidden', 'true');
                        this.appendChild(spinner);
                    }
                }
            });
        });

        // Mantém os parâmetros de filtro na URL
        const currentUrl = new URL(window.location.href);
        const filterParams = new URLSearchParams(currentUrl.search);
        
        pagination.querySelectorAll('.page-link').forEach(link => {
            if (link.href && link.href !== '#') {
                try {
                    const url = new URL(link.href);
                    
                    // Preservar parâmetros de filtro existentes (exceto page)
                    filterParams.forEach((value, key) => {
                        if (key !== 'page') {
                            url.searchParams.set(key, value);
                        }
                    });
                    
                    // Atualizar href
                    link.href = url.toString();
                    
                    // Extrair e armazenar o número da página para uso mais fácil
                    const page = url.searchParams.get('page');
                    if (page) {
                        link.setAttribute('data-page', page);
                    }
                } catch (e) {
                    console.error('Erro ao processar URL de paginação:', e);
                }
            }
        });
        
        // Verificar se o AlunosManager está ativo
        if (window.alunosManagerActive) {
            // Interceptar cliques na paginação para usar o AlunosManager
            interceptPaginationClicks();
        }
    }
    
    // Melhorar a apresentação em dispositivos móveis
    enhanceMobileDisplay();
    /**
     * Intercepta cliques na paginação para usar o AlunosManager
     */
    function interceptPaginationClicks() {
        pagination.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', function(e) {
                // Prevenir navegação padrão
                e.preventDefault();
                
                // Verificar se é um item desabilitado
                if (this.classList.contains('disabled') || this.parentElement.classList.contains('disabled')) {
                    return;
                }
                
                // Usar o manipulador global de paginação
                if (window.handlePaginationClick) {
                    window.handlePaginationClick(e, this.href);
                }
            });
        });
    }
    
    /**
     * Melhora a apresentação em dispositivos móveis
     */
    function enhanceMobileDisplay() {
        // Verificar se é um dispositivo móvel (viewport pequeno)
        const isMobile = window.innerWidth < 768;
        
        if (isMobile && pagination) {
            // Em dispositivos móveis, simplificar a exibição
            const pageItems = pagination.querySelectorAll('.page-item');
            
            // Esconder alguns números para economizar espaço
            pageItems.forEach(item => {
                // Não esconder primeira, última, atual e controles
                const isControl = item.classList.contains('first') || 
                                 item.classList.contains('last') ||
                                 item.classList.contains('prev') ||
                                 item.classList.contains('next');
                
                const isActive = item.classList.contains('active');
                const link = item.querySelector('.page-link');
                
                // Mostrar apenas controles, página atual e reticências
                if (!isControl && !isActive && link) {
                    // Se é um número de página (não reticências)
                    if (link.textContent.trim() !== '...') {
                        // Verificar se está muito longe da página atual
                        const currentPage = document.querySelector('.page-item.active');
                        if (currentPage) {
                            const currentIndex = Array.from(pageItems).indexOf(currentPage);
                            const thisIndex = Array.from(pageItems).indexOf(item);
                            
                            // Manter visíveis apenas as páginas próximas
                            if (Math.abs(currentIndex - thisIndex) > 1) {
                                // Manter primeira e última páginas visíveis
                                const isFirst = link.getAttribute('data-page') === '1';
                                const isLast = pagination.dataset.totalPages && 
                                              link.getAttribute('data-page') === pagination.dataset.totalPages;
                                
                                if (!isFirst && !isLast) {
                                    item.classList.add('d-none', 'd-md-block');
                                }
                            }
                        }
                    }
                }
            });
        }
    }
});

// Garantir que a paginação seja atualizada quando a página for redimensionada
window.addEventListener('resize', function() {
    // Usar debounce para evitar muitas chamadas
    clearTimeout(window.resizeTimer);
    window.resizeTimer = setTimeout(function() {
        const pagination = document.querySelector('.pagination');
        if (pagination) {
            // Recalcular a exibição móvel
            const pageItems = pagination.querySelectorAll('.page-item');
            
            // Resetar visibilidade
            pageItems.forEach(item => {
                item.classList.remove('d-none', 'd-md-block');
            });
            
            // Verificar se é móvel
            if (window.innerWidth < 768) {
                const currentPage = document.querySelector('.page-item.active');
                if (currentPage) {
                    const currentIndex = Array.from(pageItems).indexOf(currentPage);
                    
                    pageItems.forEach((item, index) => {
                        // Não esconder controles, página atual e reticências
                        const isControl = item.classList.contains('first') || 
                                         item.classList.contains('last') ||
                                         item.classList.contains('prev') ||
                                         item.classList.contains('next');
                        
                        const isActive = item.classList.contains('active');
                        const link = item.querySelector('.page-link');
                        
                        if (!isControl && !isActive && link && link.textContent.trim() !== '...') {
                            if (Math.abs(currentIndex - index) > 1) {
                                const isFirst = link.getAttribute('data-page') === '1';
                                const isLast = pagination.dataset.totalPages && 
                                              link.getAttribute('data-page') === pagination.dataset.totalPages;
                                
                                if (!isFirst && !isLast) {
                                    item.classList.add('d-none', 'd-md-block');
                                }
                            }
                        }
                    });
                }
            }
        }
    }, 250);
});
