/**
 * Script otimizado para rolagem infinita na lista de alunos
 * Com suporte aprimorado para dispositivos móveis e maior compatibilidade com filtros
 */

document.addEventListener('DOMContentLoaded', function() {
    // Configurações
    const config = {
        contentContainer: '#content-container',
        loadingIndicator: '#loading-indicator',
        loadThreshold: 200, // Carregar quando estiver a 200px do final
        debounceDelay: 150  // Atraso para o debounce em ms
    };
    
    // Estado
    let state = {
        loading: false,
        currentPage: 1,
        hasMore: true,
        touching: false,
        url: window.location.href,
        viewMode: localStorage.getItem('alunosViewPreference') || 'grid'
    };
    
    // Elementos
    const contentContainer = document.querySelector(config.contentContainer);
    const loadingIndicator = document.querySelector(config.loadingIndicator);
    
    // Detectar dispositivo móvel
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    // Aplicar classes específicas para mobile
    if (isMobile) {
        document.body.classList.add('mobile-device');
        
        // Aumentar área de toque para elementos interativos
        document.querySelectorAll('.btn, .card-header, select, a').forEach(el => {
            el.classList.add('mobile-touch-target');
        });
    }
    
    /**
     * Função para obter parâmetros da URL atual
     */
    function getUrlParameters() {
        const url = new URL(state.url);
        const params = new URLSearchParams(url.search);
        
        // Adicionar parâmetro de scroll infinito
        params.set('infinite_scroll', 'true');
        
        return params;
    }
    
    /**
     * Função para carregar mais conteúdo
     */
    function loadMoreContent() {
        if (state.loading || !state.hasMore) return;
        
        state.loading = true;
        showLoading();
        
        // Obter parâmetros da URL
        const params = getUrlParameters();
        params.set('page', state.currentPage + 1);
        
        // Fazer requisição AJAX
        fetch(`${window.location.pathname}?${params.toString()}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.html) {
                // Atualizar contagem de resultados se disponível
                if (data.total_alunos !== undefined) {
                    const countDisplay = document.getElementById('count-display');
                    if (countDisplay) {
                        countDisplay.textContent = data.total_alunos;
                    }
                }
                
                // Adicionar conteúdo
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = data.html;
                
                // Adicionar eventos a novos botões
                setupCardEvents(tempDiv);
                
                // Anexar ao contêiner
                if (data.mode === 'replace') {
                    contentContainer.innerHTML = '';
                    Array.from(tempDiv.children).forEach(child => {
                        contentContainer.appendChild(child);
                    });
                } else {
                    Array.from(tempDiv.children).forEach(child => {
                        contentContainer.appendChild(child);
                    });
                }
                
                // Atualizar estado
                state.currentPage = data.current_page;
                state.hasMore = data.has_more;
                
                // Aplicar visualização atual (grid ou lista)
                applyViewMode();
                
                // Se não houver mais páginas, remover o indicador de carregamento
                if (!state.hasMore) {
                    loadingIndicator?.classList.add('d-none');
                }
            }
        })
        .catch(error => {
            console.error('Erro ao carregar mais alunos:', error);
            showError('Houve um erro ao carregar mais alunos. Tente novamente.');
        })
        .finally(() => {
            state.loading = false;
            hideLoading();
        });
    }
    
    /**
     * Aplicar modo de visualização atual (grid ou lista)
     */
    function applyViewMode() {
        if (contentContainer) {
            contentContainer.classList.remove('grid-view', 'list-view');
            contentContainer.classList.add(`${state.viewMode}-view`);
        }
    }
    
    /**
     * Função para mostrar o indicador de carregamento
     */
    function showLoading() {
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }
    }
    
    /**
     * Função para esconder o indicador de carregamento
     */
    function hideLoading() {
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
    }
    
    /**
     * Função para mostrar mensagem de erro
     */
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger mt-3 mx-3';
        errorDiv.textContent = message;
        
        // Remover após 5 segundos
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
        
        contentContainer.parentNode.insertBefore(errorDiv, contentContainer.nextSibling);
    }
    
    /**
     * Função para configurar eventos nos cards de alunos
     */
    function setupCardEvents(container) {
        const cards = container.querySelectorAll('.aluno-card');
        
        cards.forEach(card => {
            // Melhorar comportamento em dispositivos móveis
            if (isMobile) {
                // Prevenir comportamento fantasma (ghost clicks)
                card.addEventListener('touchstart', function(e) {
                    state.touching = true;
                    state.touchStartX = e.touches[0].clientX;
                    state.touchStartY = e.touches[0].clientY;
                }, { passive: true });
                
                card.addEventListener('touchmove', function(e) {
                    if (!state.touching) return;
                    
                    // Calcular a distância do movimento
                    const touchX = e.touches[0].clientX;
                    const touchY = e.touches[0].clientY;
                    const diffX = Math.abs(touchX - state.touchStartX);
                    const diffY = Math.abs(touchY - state.touchStartY);
                    
                    // Se moveu mais de 10px, considerar como scroll e não como toque
                    if (diffX > 10 || diffY > 10) {
                        state.touching = false;
                    }
                }, { passive: true });
                
                card.addEventListener('touchend', function(e) {
                    if (state.touching) {
                        // Encontrar o link de detalhes e navegar para ele
                        const detailsLink = this.querySelector('.view-details');
                        if (detailsLink && detailsLink.href) {
                            e.preventDefault();
                            window.location.href = detailsLink.href;
                        }
                    }
                    state.touching = false;
                });
            }
            
            // Melhorar acessibilidade
            card.setAttribute('tabindex', '0');
            card.setAttribute('role', 'button');
            
            // Adicionar navegação por teclado
            card.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const detailsLink = this.querySelector('.view-details');
                    if (detailsLink && detailsLink.href) {
                        window.location.href = detailsLink.href;
                    }
                }
            });
        });
    }
    
    /**
     * Function de debounce para otimizar eventos de scroll
     */
    function debounce(func, delay) {
        let timer;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timer);
            timer = setTimeout(() => func.apply(context, args), delay);
        };
    }
    
    /**
     * Verificar se chegou ao final da página
     */
    function checkEndOfPage() {
        if (!state.hasMore || state.loading) return;
        
        const scrollHeight = Math.max(
            document.body.scrollHeight,
            document.documentElement.scrollHeight
        );
        
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const clientHeight = window.innerHeight || document.documentElement.clientHeight;
        
        // Ajustar threshold para carregar mais cedo em dispositivos móveis
        const threshold = isMobile ? config.loadThreshold * 1.5 : config.loadThreshold;
        
        if (scrollHeight - scrollTop - clientHeight <= threshold) {
            loadMoreContent();
        }
    }
    
    // Monitorar alterações nos dropdowns de filtro
    const filterForm = document.getElementById('filter-form');
    const searchForm = document.getElementById('search-form');
    
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            // Reiniciar estado ao aplicar filtros
            state.currentPage = 1;
            state.hasMore = true;
            state.loading = false;
        });
    }
    
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            // Reiniciar estado ao aplicar busca
            state.currentPage = 1;
            state.hasMore = true;
            state.loading = false;
        });
    }
    
    // Monitore mudanças na visualização (grid/list)
    document.querySelectorAll('#viewGrid, #viewList').forEach(button => {
        button.addEventListener('click', function() {
            if (this.id === 'viewGrid') {
                state.viewMode = 'grid';
            } else {
                state.viewMode = 'list';
            }
            applyViewMode();
        });
    });
    
    // Configurar eventos
    window.addEventListener('scroll', debounce(checkEndOfPage, config.debounceDelay), { passive: true });
    window.addEventListener('resize', debounce(checkEndOfPage, config.debounceDelay), { passive: true });
    
    // Configurar eventos para cards iniciais
    setupCardEvents(document);
    
    // Aplicar modo de visualização inicial
    applyViewMode();
    
    // Checar inicialmente se precisa carregar mais (para telas grandes)
    setTimeout(checkEndOfPage, 500);
    
    // Expor funções para uso global, se necessário
    window.infiniteScroll = {
        loadMore: loadMoreContent,
        refresh: function() {
            state.currentPage = 1;
            state.hasMore = true;
            state.loading = false;
            loadMoreContent();
        }
    };
});
