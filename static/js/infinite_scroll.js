/**
 * Script otimizado para gerenciar o scroll infinito na página de lista de alunos
 * com suporte a diferentes modos de visualização e eliminação de duplicatas
 */
document.addEventListener('DOMContentLoaded', function() {
    // Elementos DOM principais
    const contentContainer = document.getElementById('content-container');
    const loadingIndicator = document.getElementById('loading-indicator');
    const endOfListIndicator = document.getElementById('end-of-list');
    const countDisplay = document.getElementById('count-display');
    const viewGrid = document.getElementById('viewGrid');
    const viewList = document.getElementById('viewList');
    
    // Sair se o contêiner principal não existir
    if (!contentContainer) {
        console.warn('Container principal não encontrado. Abortando inicialização do scroll infinito.');
        return;
    }
    
    // Conjunto para rastrear IDs dos alunos já carregados
    const loadedIds = new Set();
    
    // Inicializar conjunto de IDs com alunos já presentes na página
    function initializeLoadedIds() {
        // Limpar IDs anteriores para evitar problemas com mudanças de turma
        loadedIds.clear();
        
        // Adicionar IDs da página atual
        document.querySelectorAll('.aluno-item').forEach(item => {
            const alunoId = item.getAttribute('data-aluno-id');
            if (alunoId) {
                loadedIds.add(alunoId);
            }
        });
        console.log(`IDs inicializados: ${loadedIds.size} alunos`);
        
        // Verificar duplicatas iniciais
        removeDuplicates();
    }
    
    // Estado do scroll infinito
    const state = {
        currentPage: 1,
        isLoading: false,
        hasMoreContent: true,
        viewMode: localStorage.getItem('alunosViewPreference') || 'grid',
        totalLoaded: document.querySelectorAll('.aluno-item').length,
        lastUrl: window.location.href, // Guardar a última URL para detectar mudanças de filtro
        lastFilterHash: calculateFilterHash() // Hash dos filtros atuais
    };
    
    // Detectar dispositivo móvel para ajustes de UI
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    /**
     * Calcular hash dos filtros atuais para detectar mudanças
     */
    function calculateFilterHash() {
        const urlParams = new URLSearchParams(window.location.search);
        // Obter apenas os parâmetros de filtro relevantes
        const filterParams = {
            nivel: urlParams.get('nivel') || '',
            turno: urlParams.get('turno') || '',
            ano: urlParams.get('ano') || '',
            search: urlParams.get('search') || ''
        };
        
        // Criar uma string composta dos valores para usar como hash
        return Object.values(filterParams).join('_');
    }
    
    /**
     * Verificar se os filtros mudaram desde o último carregamento
     */
    function haveFiltersChanged() {
        const currentHash = calculateFilterHash();
        const changed = currentHash !== state.lastFilterHash;
        
        if (changed) {
            console.log('Filtros mudaram, atualizando hash');
            state.lastFilterHash = currentHash;
        }
        
        return changed;
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
     * Mostrar mensagem de fim da lista
     */
    function showEndOfList() {
        if (endOfListIndicator) {
            endOfListIndicator.classList.remove('d-none');
        }
        
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
    }
    
    /**
     * Esconder mensagem de fim da lista
     */
    function hideEndOfList() {
        if (endOfListIndicator) {
            endOfListIndicator.classList.add('d-none');
        }
    }
    
    /**
     * Verificar se a URL mudou (indica mudança de filtros)
     */
    function urlHasChanged() {
        const currentUrl = window.location.href;
        const urlChanged = currentUrl !== state.lastUrl;
        
        if (urlChanged) {
            console.log('URL mudou, atualizando estado do scroll infinito');
            state.lastUrl = currentUrl;
            // Também atualizar o hash dos filtros
            state.lastFilterHash = calculateFilterHash();
        }
        
        return urlChanged;
    }
    
    /**
     * Remover duplicatas da lista atual
     */
    function removeDuplicates() {
        const alunosContainer = contentContainer.querySelector('.row') || contentContainer;
        if (!alunosContainer) return 0;
        
        const seen = new Set();
        let removed = 0;
        
        alunosContainer.querySelectorAll('.aluno-item').forEach(item => {
            const id = item.getAttribute('data-aluno-id');
            if (!id) return;
            
            if (seen.has(id)) {
                // Duplicata encontrada, remover
                item.remove();
                removed++;
            } else {
                seen.add(id);
            }
        });
        
        if (removed > 0) {
            console.log(`Removidas ${removed} duplicatas`);
        }
        
        return removed;
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
     * Aplicar modo de visualização (grid ou lista)
     */
    function applyViewMode(mode) {
        // Validar o modo
        if (mode !== 'grid' && mode !== 'list') {
            mode = 'grid'; // Padrão grid
        }
        
        // Atualizar estado
        state.viewMode = mode;
        
        // Aplicar classes ao container
        contentContainer.classList.remove('alunos-grid', 'alunos-list');
        contentContainer.classList.add(`alunos-${mode}`);
        
        // Atualizar botões
        if (viewGrid && viewList) {
            if (mode === 'grid') {
                viewGrid.classList.add('active');
                viewList.classList.remove('active');
            } else {
                viewList.classList.add('active');
                viewGrid.classList.remove('active');
            }
        }
        
        // Salvar preferência
        localStorage.setItem('alunosViewPreference', mode);
    }
    
    /**
     * Processar HTML recebido do servidor 
     */
    function processHtml(html) {
        // Criar elemento temporário para analisar o HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        // Remover elementos de paginação
        tempDiv.querySelectorAll('.pagination, .pagination-container').forEach(el => el.remove());
        
        // Encontrar o container dos alunos no HTML recebido
        let rowContainer = tempDiv.querySelector('.row');
        if (!rowContainer) {
            // Se não houver container de linha, usar o container principal
            rowContainer = tempDiv;
        }
        
        const alunoElements = rowContainer.querySelectorAll('.aluno-item');
        const fragment = document.createDocumentFragment();
        let newItems = 0;
        let duplicates = 0;
        
        // Processar cada elemento de aluno
        alunoElements.forEach(element => {
            const alunoId = element.getAttribute('data-aluno-id');
            
            if (!alunoId) {
                console.warn('Elemento de aluno sem ID detectado');
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
            }
        });
        
        return { fragment, newItems, duplicates };
    }
    
    /**
     * Carregar mais conteúdo via AJAX
     */
    function loadMoreContent() {
        // Verificar se a URL mudou desde o último carregamento
        // Isso significa que mudamos de página ou aplicamos filtros diferentes
        if (urlHasChanged() || haveFiltersChanged()) {
            console.log('URL ou filtros mudaram, reiniciando estado do scroll infinito');
            resetState();
            // Não carregar conteúdo agora - AlunosManager já deve ter carregado o conteúdo inicial
            return;
        }
        
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
            state.hasMoreContent = data.has_more === true;
            
            // Atualizar contador de resultados
            if (data.total_alunos !== undefined && countDisplay) {
                countDisplay.textContent = data.total_alunos;
            }
            
            if (data.html) {
                // Se for modo replace, limpar conteúdo e IDs
                if (data.mode === 'replace') {
                    // Encontrar o container onde adicionar o conteúdo
                    const rowContainer = contentContainer.querySelector('.row');
                    if (rowContainer) {
                        rowContainer.innerHTML = '';
                    } else {
                        contentContainer.innerHTML = '';
                    }
                    
                    // Limpar IDs carregados
                    loadedIds.clear();
                    state.totalLoaded = 0;
                }
                
                // Processar o HTML recebido
                const { fragment, newItems, duplicates } = processHtml(data.html);
                
                // Adicionar novos elementos ao container
                const rowContainer = contentContainer.querySelector('.row');
                if (rowContainer) {
                    rowContainer.appendChild(fragment);
                } else {
                    contentContainer.appendChild(fragment);
                }
                
                // Log de status
                console.log(`Página ${data.current_page}: ${newItems} novos alunos adicionados, ${duplicates} duplicatas evitadas`);
                
                // Atualizar total carregado
                state.totalLoaded += newItems;
                
                // Atualizar estado
                state.currentPage = data.current_page;
                
                // Reajustar visualização conforme preferência salva
                applyViewMode(state.viewMode);
                
                // Se não adicionamos nenhum item novo, mas ainda há mais páginas,
                // tentar carregar a próxima página automaticamente
                if (newItems === 0 && state.hasMoreContent) {
                    setTimeout(() => {
                        state.isLoading = false;
                        loadMoreContent();
                    }, 300);
                    return;
                }
                
                // Se não há mais conteúdo, mostrar indicador de fim da lista
                if (!state.hasMoreContent) {
                    showEndOfList();
                    console.log(`Carregamento completo: ${state.totalLoaded} alunos carregados no total`);
                }
            } else {
                // Sem HTML recebido
                state.hasMoreContent = false;
                showEndOfList();
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
     * Configurar alternância entre visualizações grid e lista
     */
    function setupViewToggle() {
        if (!viewGrid || !viewList) return;
        
        // Adicionar listeners aos botões
        viewGrid.addEventListener('click', function() {
            applyViewMode('grid');
        });
        
        viewList.addEventListener('click', function() {
            applyViewMode('list');
        });
        
        // Aplicar modo inicial
        applyViewMode(state.viewMode);
    }
    
    /**
     * Configurar listeners para formulários de busca e filtro
     */
    function setupForms() {
        const searchForm = document.getElementById('search-form');
        const filterForm = document.getElementById('filter-form');
        
        // Redefinir o estado do scroll infinito quando há uma mudança de filtro
        function resetFormState() {
            console.log('Form submit detectado, resetando estado do scroll infinito');
            resetState();
        }
        
        if (searchForm) {
            searchForm.addEventListener('submit', resetFormState);
        }
        
        if (filterForm) {
            filterForm.addEventListener('submit', resetFormState);
        }
        
        // Também monitorar alterações em selects de turmas e anos
        const nivelSelect = document.getElementById('nivel');
        const turnoSelect = document.getElementById('turno');
        const anoSelect = document.getElementById('ano');
        
        // Quando qualquer um desses selects mudar, preparamos para uma atualização
        [nivelSelect, turnoSelect, anoSelect].forEach(select => {
            if (select) {
                select.addEventListener('change', function() {
                    console.log('Select de filtro alterado, preparando para resetar scroll infinito');
                    // Não resetamos imediatamente, pois o AlunosManager fará isso ao carregar novos dados
                });
            }
        });
    }
    
    /**
     * Resetar completamente o estado do scroll infinito
     */
    function resetState() {
        console.log('Resetando estado do scroll infinito');
        state.currentPage = 1;
        state.hasMoreContent = true;
        state.isLoading = false;
        state.totalLoaded = 0;
        loadedIds.clear();
        
        // Atualizar URL atual e hash de filtros
        state.lastUrl = window.location.href;
        state.lastFilterHash = calculateFilterHash();
        
        // Esconder indicador de fim da lista
        hideEndOfList();
        
        // Reinicializar IDs carregados
        initializeLoadedIds();
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
        // Verificar se houve mudança de filtros antes de tentar carregar mais
        if (urlHasChanged() || haveFiltersChanged()) {
            console.log('URL ou filtros mudaram, não vamos carregar mais conteúdo automaticamente');
            return;
        }
        
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
     * Limpa o container de alunos e os IDs carregados
     */
    function clearContainer() {
        const rowContainer = contentContainer.querySelector('.row');
        if (rowContainer) {
            rowContainer.innerHTML = '';
        } else {
            contentContainer.innerHTML = '';
        }
        
        loadedIds.clear();
        state.totalLoaded = 0;
        hideEndOfList();
    }
    
    /**
     * Inicializar scroll infinito
     */
    function init() {
        try {
            // Inicializar IDs já carregados
            initializeLoadedIds();
            
            // Configurar alternância de visualização
            setupViewToggle();
            
            // Configurar formulários
            setupForms();
            
            // Adicionar listener de scroll
            window.addEventListener('scroll', debounce(checkEndOfPage, 150), { passive: true });
            
            // Monitorar mudanças na URL (navegação do histórico)
            window.addEventListener('popstate', function() {
                console.log('Navegação do histórico detectada, resetando estado');
                resetState();
            });
            
            // Verificar inicialmente se já deve carregar mais conteúdo
            setTimeout(checkEndOfPage, 500);
            
            console.log('Scroll infinito inicializado com sucesso');
        } catch (e) {
            console.error('Erro ao inicializar scroll infinito:', e);
        }
    }
    
    // Inicializar
    init();
    
    // Expor API pública para uso externo (para integração com AlunosManager)
    window.infiniteScroll = {
        loadMore: loadMoreContent,
        
        reset: function() {
            resetState();
            // Não carregar automaticamente, deixar o AlunosManager controlar isso
        },
        
        fullReset: function() {
            resetState();
            clearContainer();
            loadMoreContent();
        },
        
        clearCache: function() {
            loadedIds.clear();
            console.log('Cache de IDs de alunos limpo');
        },
        
        getState: () => ({...state}),
        
        getLoadedIds: () => [...loadedIds],
        
        setViewMode: applyViewMode,
        
        removeDuplicates: removeDuplicates,
        
        // Método para o AlunosManager registrar novos IDs após uma carga de dados
        registerLoadedIds: function() {
            initializeLoadedIds();
            console.log('IDs recarregados após atualização de dados');
        }
    };
});
