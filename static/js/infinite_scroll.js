/**
 * Script otimizado para rolagem infinita na lista de alunos
 * Com suporte aprimorado para dispositivos móveis
 */

document.addEventListener('DOMContentLoaded', function() {
    // Configurações
    const config = {
        contentContainer: '#content-container',
        loadingIndicator: '#loading-indicator',
        loadThreshold: 200, // Carregar quando estiver a 200px do final
        debounceDelay: 100  // Atraso para o debounce em ms
    };
    
    // Estado
    let state = {
        loading: false,
        currentPage: 1,
        hasMore: true,
        touching: false,
        url: window.location.href
    };
    
    // Elementos
    const contentContainer = document.querySelector(config.contentContainer);
    const loadingIndicator = document.querySelector(config.loadingIndicator);
    
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
        .then(response => response.json())
        .then(data => {
            if (data.html) {
                // Adicionar conteúdo
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = data.html;
                
                // Adicionar eventos a novos botões
                setupCardEvents(tempDiv);
                
                // Anexar ao contêiner
                if (data.mode === 'replace') {
                    contentContainer.innerHTML = tempDiv.innerHTML;
                } else {
                    contentContainer.appendChild(tempDiv);
                }
                
                // Atualizar estado
                state.currentPage = data.current_page;
                state.hasMore = data.has_more;
                
                // Se não houver mais páginas, remover o indicador de carregamento
                if (!state.hasMore) {
                    loadingIndicator?.remove();
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
        errorDiv.className = 'alert alert-danger mt-3';
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
            // Melhor maneira de lidar com eventos de toque em dispositivos móveis
            card.addEventListener('touchstart', function() {
                state.touching = true;
            }, { passive: true });
            
            card.addEventListener('touchend', function(e) {
                if (state.touching) {
                    // Prevenir propagação para evitar comportamentos inesperados
                    e.stopPropagation();
                    
                    // Encontrar o link de detalhes e navegar para ele
                    const detailsLink = this.querySelector('.view-details');
                    if (detailsLink) {
                        window.location.href = detailsLink.href;
                    }
                }
                state.touching = false;
            }, { passive: false });
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
        
        if (scrollHeight - scrollTop - clientHeight <= config.loadThreshold) {
            loadMoreContent();
        }
    }
    
    // Configurar eventos
    window.addEventListener('scroll', debounce(checkEndOfPage, config.debounceDelay), { passive: true });
    window.addEventListener('resize', debounce(checkEndOfPage, config.debounceDelay), { passive: true });
    
    // Configurar eventos para cards iniciais
    setupCardEvents(document);
    
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
