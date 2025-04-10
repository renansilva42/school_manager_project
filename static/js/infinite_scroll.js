/**
 * Script para gerenciar o scroll infinito na página de lista de alunos
 * Versão final com controle rigoroso de duplicatas
 */
document.addEventListener('DOMContentLoaded', function() {
    // Elementos DOM
    const contentContainer = document.getElementById('content-container');
    const alunosContainer = document.querySelector('#content-container .row');
    const loadingIndicator = document.getElementById('loading-indicator');
    const endOfListIndicator = document.getElementById('end-of-list');
    const countDisplay = document.getElementById('count-display');
    
    // Inicialização apenas se o container existir
    if (!contentContainer) {
        console.warn('Contêiner de conteúdo não encontrado');
        return;
    }
    
    // Conjunto para rastrear IDs dos alunos já renderizados
    const loadedIds = new Set();
    
    // Inicializar loadedIds com os IDs já presentes na página
    function initializeLoadedIds() {
        document.querySelectorAll('.aluno-item').forEach(item => {
            const alunoId = item.getAttribute('data-aluno-id');
            if (alunoId) {
                loadedIds.add(alunoId);
            }
        });
        console.log(`IDs inicializados: ${loadedIds.size}`);
    }
    
    // Estado do scroll infinito
    const state = {
        currentPage: 1,
        isLoading: false,
        hasMoreContent: true,
        duplicatesDetected: 0,
        totalLoaded: 0
    };
    
    // Detectar dispositivo móvel para ajustes de UI
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    // Verificar se o atributo infinite_scroll existe
    const hasInfiniteScroll = contentContainer.hasAttribute('data-infinite-scroll') || 
                             window.location.search.includes('infinite_scroll=true');
    
    if (!hasInfiniteScroll) {
        console.log('Scroll infinito não ativado nesta página');
        return;
    }
    
    // Aplicar classes específicas para mobile
    if (isMobile) {
        document.body.classList.add('mobile-device');
    }
    
    /**
     * Obter parâmetros da URL atual para a próxima requisição
     */
    function getUrlParams() {
        const urlSearchParams = new URLSearchParams(window.location.search);
        const params = Object.fromEntries(urlSearchParams.entries());
        
        // Adicionar parâmetro de scroll infinito
        params.infinite_scroll = 'true';
        
        // Sempre solicitar a próxima página
        params.page = state.currentPage + 1;
        
        return params;
    }
    
    /**
     * Converter objeto de parâmetros para string de consulta
     */
    function buildQueryString(params) {
        return Object.keys(params)
            .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
            .join('&');
    }
    
    /**
     * Mostrar indicador de carregamento
     */
    function showLoading() {
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }
    }
    
    /**
     * Ocultar indicador de carregamento
     */
    function hideLoading() {
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
    }
    
    /**
     * Mostrar indicador de fim da lista
     */
    function showEndOfList() {
        if (endOfListIndicator) {
            endOfListIndicator.classList.remove('d-none');
        }
    }
    
    /**
     * Mostrar mensagem de notificação
     */
    function showNotification(message, type = 'info') {
        // Criar elemento de notificação
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        notification.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
        `;
        
        // Adicionar ao body
        document.body.appendChild(notification);
        
        // Remover após 5 segundos
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 500);
        }, 5000);
    }
    
    /**
     * Extrair e processar elementos de alunos do HTML recebido
     */
    function processAlunosHtml(html) {
        // Criar elemento temporário para analisar o HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        // Remover elementos de paginação se presentes
        tempDiv.querySelectorAll('.pagination, .pagination-container').forEach(el => el.remove());
        
        // Obter todos os elementos de alunos
        const alunoElements = tempDiv.querySelectorAll('.aluno-item');
        const fragment = document.createDocumentFragment();
        let newItems = 0;
        let duplicates = 0;
        
        // Array para armazenar IDs para verificação de duplicatas no console
        const idList = [];
        
        alunoElements.forEach(element => {
            const alunoId = element.getAttribute('data-aluno-id');
            
            // Registrar todos os IDs para debug
            if (alunoId) {
                idList.push(alunoId);
            }
            
            if (!alunoId) {
                console.warn('Elemento de aluno sem ID detectado:', element);
                return;
            }
            
            if (!loadedIds.has(alunoId)) {
                // Este é um novo aluno, adicionar ao fragmento
                fragment.appendChild(element);
                loadedIds.add(alunoId);
                newItems++;
            } else {
                // Este é um aluno duplicado, ignorar
                duplicates++;
                console.log(`Aluno duplicado ignorado (ID: ${alunoId})`);
            }
        });
        
        // Verificar duplicatas no lote recebido
        const uniqueIds = new Set(idList);
        if (idList.length !== uniqueIds.size) {
            console.warn(`Aviso: ${idList.length - uniqueIds.size} duplicatas encontradas no HTML recebido.`);
        }
        
        state.duplicatesDetected += duplicates;
        state.totalLoaded += newItems;
        
        return { fragment, newItems, duplicates };
    }
    
    /**
     * Carregar mais conteúdo via AJAX
     */
    function loadMoreContent() {
        if (state.isLoading || !state.hasMoreContent) return;
        
        state.isLoading = true;
        showLoading();
        
        // Construir URL com parâmetros
        const params = getUrlParams();
        const queryString = buildQueryString(params);
        const url = `${window.location.pathname}?${queryString}`;
        
        console.log(`Carregando página ${params.page}...`);
        
        // Realizar a solicitação AJAX
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            hideLoading();
            
            // Verificar se há mais conteúdo
            state.hasMoreContent = data.has_more;
            
            // Atualizar contador de resultados
            if (data.total_alunos !== undefined && countDisplay) {
                countDisplay.textContent = data.total_alunos;
            }
            
            if (data.html) {
                // Se for para substituir, limpar conteúdo e IDs carregados
                if (data.mode === 'replace') {
                    if (alunosContainer) {
                        alunosContainer.innerHTML = '';
                    } else if (contentContainer) {
                        // Encontrar o container de linha ou criar um
                        let rowContainer = contentContainer.querySelector('.row');
                        if (!rowContainer) {
                            rowContainer = document.createElement('div');
                            rowContainer.className = 'row g-3';
                            contentContainer.appendChild(rowContainer);
                        }
                        rowContainer.innerHTML = '';
                    }
                    loadedIds.clear();
                }
                
                // Processar o HTML recebido
                const { fragment, newItems, duplicates } = processAlunosHtml(data.html);
                
                // Adicionar novos elementos ao contêiner
                const targetContainer = alunosContainer || contentContainer.querySelector('.row');
                
                if (targetContainer) {
                    targetContainer.appendChild(fragment);
                    
                    // Log de status
                    console.log(`Página ${data.current_page}: ${newItems} novos alunos adicionados, ${duplicates} duplicatas ignoradas.`);
                    
                    // Se adicionamos itens, então atualizar o comportamento dos elementos
                    if (newItems > 0) {
                        // Aqui você pode adicionar comportamentos específicos para os novos elementos
                    }
                } else {
                    console.error('Container para alunos não encontrado');
                }
                
                // Se não adicionamos nenhum item novo, mas ainda há mais páginas,
                // tentar carregar a próxima página automaticamente
                if (newItems === 0 && state.hasMoreContent) {
                    state.currentPage++;
                    setTimeout(() => {
                        state.isLoading = false;
                        loadMoreContent();
                    }, 300);
                    return;
                }
                
                // Atualizar estado
                state.currentPage = data.current_page;
            } else {
                state.hasMoreContent = false;
            }
            
            // Verificar se terminamos todo o conteúdo
            if (!state.hasMoreContent) {
                showEndOfList();
                
                // Se detectamos duplicatas durante o carregamento, mostrar aviso no console
                if (state.duplicatesDetected > 0) {
                    console.warn(`Total de ${state.duplicatesDetected} cards duplicados foram ignorados durante o carregamento.`);
                }
                
                console.log(`Carregamento completo: ${state.totalLoaded} alunos carregados no total.`);
            }
        })
        .catch(error => {
            console.error('Erro ao carregar mais alunos:', error);
            hideLoading();
            showNotification('Erro ao carregar mais alunos. Tente novamente.', 'danger');
        })
        .finally(() => {
            state.isLoading = false;
        });
    }
    
    /**
     * Alternar entre visualizações de grid e lista
     */
    function setupViewToggle() {
        const gridButton = document.getElementById('viewGrid');
        const listButton = document.getElementById('viewList');
        
        if (!gridButton || !listButton) return;
        
        // Obter preferência salva ou usar grid como padrão
        const savedView = localStorage.getItem('alunosViewPreference') || 'grid';
        
        // Função para aplicar a visualização
        function applyView(view) {
            if (contentContainer) {
                contentContainer.classList.remove('alunos-grid', 'alunos-list');
                contentContainer.classList.add(`alunos-${view}`);
                
                // Atualizar estado dos botões
                if (view === 'grid') {
                    gridButton.classList.add('active');
                    listButton.classList.remove('active');
                } else {
                    listButton.classList.add('active');
                    gridButton.classList.remove('active');
                }
                
                // Salvar preferência
                localStorage.setItem('alunosViewPreference', view);
            }
        }
        
        // Aplicar visualização inicial
        applyView(savedView);
        
        // Adicionar event listeners
        gridButton.addEventListener('click', () => applyView('grid'));
        listButton.addEventListener('click', () => applyView('list'));
    }
    
    // Referência para compatibilidade com código existente
    function applyViewMode() {
        setupViewToggle();
    }
    
    /**
     * Function de debounce para otimizar eventos de scroll
     */
    function debounce(func, wait) {
        let timeout;
        return function() {
            const context = this, args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }
    
    /**
     * Verificar se chegou ao final da página
     */
    function checkEndOfPage() {
        if (!state.hasMoreContent || state.isLoading) return;
        
        const scrollHeight = Math.max(
            document.body.scrollHeight,
            document.documentElement.scrollHeight
        );
        
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const clientHeight = window.innerHeight || document.documentElement.clientHeight;
        
        // Ajustar threshold para carregar mais cedo em dispositivos móveis
        const threshold = isMobile ? 500 : 300;
        
        if (scrollHeight - scrollTop - clientHeight <= threshold) {
            loadMoreContent();
        }
    }
    
    /**
     * Limpar duplicatas que possam ter escapado do backend
     */
    function cleanupDuplicates() {
        const container = alunosContainer || contentContainer.querySelector('.row');
        if (!container) return;
        
        const idSet = new Set();
        let removed = 0;
        
        container.querySelectorAll('.aluno-item').forEach(el => {
            const id = el.getAttribute('data-aluno-id');
            if (!id) return;
            
            if (idSet.has(id)) {
                // É uma duplicata
                el.remove();
                removed++;
            } else {
                idSet.add(id);
            }
        });
        
        if (removed > 0) {
            console.warn(`Limpeza final: ${removed} duplicatas removidas do DOM`);
        }
    }
    
    /**
     * Inicializar scroll infinito
     */
    function init() {
        try {
            // Inicializar conjunto de IDs já carregados
            initializeLoadedIds();
            
            // Configurar alternância de visualização (grid/list)
            setupViewToggle();
            
            // Remover elementos de paginação existentes
            document.querySelectorAll('.pagination, .pagination-container').forEach(el => {
                el.remove();
            });
            
            // Garantir que não haja duplicatas no DOM inicial
            cleanupDuplicates();
            
            // Monitorar formulários de filtro e busca
            const filterForm = document.getElementById('filter-form');
            const searchForm = document.getElementById('search-form');
            
            function resetState() {
                state.currentPage = 1;
                state.hasMoreContent = true;
                state.isLoading = false;
                state.duplicatesDetected = 0;
                state.totalLoaded = 0;
                loadedIds.clear();
            }
            
            if (filterForm) {
                filterForm.addEventListener('submit', resetState);
            }
            
            if (searchForm) {
                searchForm.addEventListener('submit', resetState);
            }
            
            // Adicionar listener de scroll
            window.addEventListener('scroll', debounce(checkEndOfPage, 100), { passive: true });
            
            // Verificar inicialmente se precisamos carregar mais conteúdo
            window.addEventListener('load', () => {
                // Verificar após o carregamento completo da página
                setTimeout(checkEndOfPage, 500);
            });
            
            // Adicionar listener de redimensionamento
            window.addEventListener('resize', debounce(() => {
                checkEndOfPage();
            }, 200), { passive: true });
            
            console.log('Scroll infinito inicializado com sucesso');
        } catch (e) {
            console.error('Erro ao inicializar scroll infinito:', e);
        }
    }
    
    // Inicializar
    init();
    
    // Expor API pública
    window.infiniteScroll = {
        loadMore: loadMoreContent,
        reset: function() {
            resetState();
            
            if (alunosContainer) {
                alunosContainer.innerHTML = '';
            }
            
            loadMoreContent();
        },
        getLoadedIds: () => [...loadedIds],
        getState: () => ({...state}),
        cleanup: cleanupDuplicates
    };
});
