// static/js/pagination.js
document.addEventListener('DOMContentLoaded', function() {
    const pagination = document.querySelector('.pagination');
    
    if (pagination) {
        // Adiciona loading state aos links
        pagination.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', function(e) {
                if (!this.classList.contains('disabled')) {
                    this.innerHTML += '<span class="spinner-border spinner-border-sm ms-2"></span>';
                }
            });
        });

        // Mantém os parâmetros de filtro na URL
        const currentUrl = new URL(window.location.href);
        const filterParams = new URLSearchParams(currentUrl.search);
        
        pagination.querySelectorAll('.page-link').forEach(link => {
            if (link.href) {
                const url = new URL(link.href);
                filterParams.forEach((value, key) => {
                    if (key !== 'page') {
                        url.searchParams.set(key, value);
                    }
                });
                link.href = url.toString();
                
                // Adicionar atributo data-page para referência mais fácil
                const page = url.searchParams.get('page');
                if (page) {
                    link.setAttribute('data-page', page);
                    
                    // Se o link não tem texto (como o botão da página 1)
                    // adicionar o número da página como conteúdo
                    if (link.textContent.trim() === '' && 
                        !link.parentElement.classList.contains('prev') && 
                        !link.parentElement.classList.contains('next')) {
                        link.textContent = page;
                    }
                }
            }
        });
        
        // Melhorar a visibilidade dos botões da paginação
        enhancePaginationVisibility(pagination);
    }
    
    /**
     * Melhora a exibição dos botões de paginação para mostrar mais opções
     */
    function enhancePaginationVisibility(pagination) {
        const currentPage = getCurrentPage();
        const totalPages = getTotalPages(pagination);
        
        if (!totalPages) return;
        
        // Array para armazenar as páginas que devem ser visíveis
        let visiblePages = [];
        
        // Sempre mostrar a primeira página
        visiblePages.push(1);
        
        // Sempre mostrar a última página
        if (totalPages > 1) {
            visiblePages.push(totalPages);
        }
        
        // Determinar o intervalo de páginas em torno da página atual
        const range = 2; // Páginas antes e depois da atual
        
        // Incluir páginas próximas da atual
        for (let i = Math.max(2, currentPage - range); i <= Math.min(totalPages - 1, currentPage + range); i++) {
            visiblePages.push(i);
        }
        
        // Garantir que não haja "buracos" de apenas uma página
        if (visiblePages.includes(3) && !visiblePages.includes(2)) {
            visiblePages.push(2);
        }
        
        if (visiblePages.includes(totalPages - 2) && !visiblePages.includes(totalPages - 1)) {
            visiblePages.push(totalPages - 1);
        }
        
        // Ordenar as páginas
        visiblePages.sort((a, b) => a - b);
        
        // Adicionar reticências apenas onde necessário
        let pagesWithEllipsis = [];
        let lastPage = 0;
        
        for (let i = 0; i < visiblePages.length; i++) {
            const page = visiblePages[i];
            
            // Se houver um salto maior que 1, adicionar reticências
            if (page - lastPage > 1) {
                pagesWithEllipsis.push('...');
            }
            
            pagesWithEllipsis.push(page);
            lastPage = page;
        }
        
        // Aplicar a visibilidade
        const pageItems = pagination.querySelectorAll('.page-item');
        
        pageItems.forEach(item => {
            // Ignorar botões prev e next
            if (item.classList.contains('prev') || item.classList.contains('next')) {
                return;
            }
            
            const link = item.querySelector('.page-link');
            if (!link) return;
            
            let pageNumber;
            let isEllipsis = link.textContent.trim() === '...';
            
            // Determinar o número da página deste botão
            if (link.dataset.page) {
                pageNumber = parseInt(link.dataset.page);
            } else if (!isEllipsis) {
                const pageText = link.textContent.trim();
                if (!isNaN(pageText)) {
                    pageNumber = parseInt(pageText);
                }
            }
            
            // Decidir se deve mostrar ou ocultar este botão
            if (pageNumber) {
                // Se for a página atual, marcar como ativa
                if (pageNumber === currentPage) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
                
                // Mostrar apenas se estiver nas páginas visíveis
                if (visiblePages.includes(pageNumber)) {
                    item.style.display = '';
                    
                    // Garantir que o link tenha um número visível
                    if (link.textContent.trim() === '') {
                        link.textContent = pageNumber;
                    }
                } else {
                    // Se não estiver nas páginas visíveis, ocultar
                    item.style.display = 'none';
                }
            } else if (isEllipsis) {
                // Verificar se precisamos de reticências neste ponto
                if (pagesWithEllipsis.includes('...')) {
                    item.style.display = '';
                    pagesWithEllipsis.splice(pagesWithEllipsis.indexOf('...'), 1);
                } else {
                    item.style.display = 'none';
                }
            }
        });
        
        // Atualizar os botões prev e next
        updatePrevNextButtons(pagination, currentPage, totalPages);
    }
    
    /**
     * Atualiza os botões de anterior e próximo
     */
    function updatePrevNextButtons(pagination, currentPage, totalPages) {
        const prevButton = pagination.querySelector('.page-item.prev');
        const nextButton = pagination.querySelector('.page-item.next');
        
        if (prevButton) {
            if (currentPage === 1) {
                prevButton.classList.add('disabled');
            } else {
                prevButton.classList.remove('disabled');
            }
        }
        
        if (nextButton) {
            if (currentPage === totalPages) {
                nextButton.classList.add('disabled');
            } else {
                nextButton.classList.remove('disabled');
            }
        }
    }
    
    /**
     * Obtém a página atual através da URL
     */
    function getCurrentPage() {
        const urlParams = new URLSearchParams(window.location.search);
        const pageFromUrl = urlParams.get('page');
        if (pageFromUrl) return parseInt(pageFromUrl);
        
        // Tenta obter do elemento ativo na paginação
        const activePage = document.querySelector('.pagination .page-item.active');
        if (activePage) {
            const pageLink = activePage.querySelector('.page-link');
            if (pageLink) {
                const dataPage = pageLink.getAttribute('data-page');
                if (dataPage) return parseInt(dataPage);
                
                // Ou extrair do texto do link
                const pageText = pageLink.textContent.trim();
                if (!isNaN(pageText)) return parseInt(pageText);
            }
        }
        
        // Valor padrão
        return 1;
    }
    
    /**
     * Obtém o número total de páginas
     */
    function getTotalPages(pagination) {
        // Verificar se há um atributo data-total-pages
        if (pagination.dataset.totalPages) {
            return parseInt(pagination.dataset.totalPages);
        }
        
        // Tentar encontrar o último botão numérico
        const pageLinks = Array.from(pagination.querySelectorAll('.page-link'));
        let maxPage = 0;
        
        pageLinks.forEach(link => {
            if (link.dataset.page) {
                const page = parseInt(link.dataset.page);
                if (page > maxPage) maxPage = page;
            } else {
                const pageText = link.textContent.trim();
                if (!isNaN(pageText)) {
                    const page = parseInt(pageText);
                    if (page > maxPage) maxPage = page;
                }
            }
        });
        
        return maxPage || 1;
    }
});
