// static/js/lista_alunos.js
// Constants and configurations
// Flag global para evitar requisições AJAX duplicadas no carregamento inicial
let initialPageLoadComplete = false;

const ANO_OPTIONS = {
    EFI: {
        M: [
            {value: '3', label: '3º Ano'},
            {value: '4', label: '4º Ano'},
            {value: '5', label: '5º Ano'}
        ]
    },
    EFF: {
        M: [
            {value: '6', label: '6º Ano - Manhã'},
            {value: '7', label: '7º Ano - Manhã'},
            {value: '8', label: '8º Ano - Manhã'}
        ],
        T: [
            {value: '6', label: '6º Ano - Tarde'},
            {value: '7', label: '7º Ano - Tarde'},
            {value: '8', label: '8º Ano - Tarde'},
            {value: '901', label: '9º Ano - Turma 901'},
            {value: '902', label: '9º Ano - Turma 902'}
        ]
    }
};

class AlunosManager {
    constructor() {
        // Indica que este gerenciador está ativo na página
        window.alunosManagerActive = true;
        
        this.initializeElements();
        this.initializeState();
        
        // Flag já está ativa desde o início para permitir requisições do usuário
        
        this.initializeEventListeners();
        this.initializeView();
    }

    initializeElements() {
        this.elements = {
            filterForm: document.getElementById('filterForm'),
            nivel: document.getElementById('nivel'),
            turno: document.getElementById('turno'),
            ano: document.getElementById('ano'),
            search: document.getElementById('search'),
            alunosContainer: document.getElementById('alunos-container'),
            loadingOverlay: document.querySelector('.loading-overlay'),
            viewGrid: document.getElementById('viewGrid'),
            viewList: document.getElementById('viewList'),
            totalResults: document.getElementById('total-results'),
            pagination: document.querySelector('.pagination')
        };
    }

    initializeState() {
        // Configurar estado inicial a partir da URL
        const urlParams = new URLSearchParams(window.location.search);
        
        // Verifica se há dados de alunos já carregados na página
        const hasInitialData = document.querySelector('#alunos-container .aluno-card') !== null;
        
        this.state = {
            isLoading: false,
            currentPage: parseInt(urlParams.get('page')) || 1,
            totalPages: parseInt(document.querySelector('.pagination')?.dataset.totalPages) || 1,
            // Flag para evitar requisições duplicadas
            requestInProgress: false,
            // Indica se a página já tem dados carregados do servidor
            initialDataLoaded: hasInitialData,
            // Flag para skip da primeira requisição AJAX
            skipInitialAjaxRequest: hasInitialData,
            // Flag para indicar se a requisição foi iniciada pelo usuário
            userInitiatedRequest: false
        };
        
        console.log('AlunosManager state initialized:', {
            currentPage: this.state.currentPage,
            totalPages: this.state.totalPages,
            initialDataLoaded: this.state.initialDataLoaded
        });
    }

    initializeView() {
        const savedView = localStorage.getItem('alunosView') || 'grid';
        this.toggleView(savedView);

        const urlParams = new URLSearchParams(window.location.search);
        
        // Configurar os filtros com base nos parâmetros da URL
        if (urlParams.has('nivel')) {
            this.elements.nivel.value = urlParams.get('nivel');
            this.updateTurnoChoices(this.elements.nivel.value, false);
            
            // Se também tiver turno na URL
            if (urlParams.has('turno')) {
                this.elements.turno.value = urlParams.get('turno');
                this.updateAnoChoices(this.elements.turno.value, this.elements.nivel.value);
                
                // Se também tiver ano na URL
                if (urlParams.has('ano')) {
                    this.elements.ano.value = urlParams.get('ano');
                }
            }
        }
        
        // Atualizar a UI de paginação com base no estado atual
        this.updatePaginationUI();
    }

    initializeEventListeners() {
        // Filter collapse button
        const filterButton = document.querySelector('[data-bs-toggle="collapse"]');
        if (filterButton) {
            const icon = filterButton.querySelector('.fa-chevron-down');
            if (icon) {
                const isCollapsed = filterButton.classList.contains('collapsed');
                icon.style.transform = isCollapsed ? 'rotate(0deg)' : 'rotate(180deg)';
                icon.style.transition = 'transform 0.3s ease';
                
                filterButton.addEventListener('click', () => {
                    const isCollapsed = filterButton.classList.contains('collapsed');
                    icon.style.transform = isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)';
                });
            }
        }
    
        // View toggles
        this.elements.viewGrid.addEventListener('click', () => this.toggleView('grid'));
        this.elements.viewList.addEventListener('click', () => this.toggleView('list'));
    
        // Form handlers
        this.elements.filterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            // Marcar como requisição iniciada pelo usuário
            this.state.userInitiatedRequest = true;
            this.handleFormSubmit();
        });
        this.elements.nivel.addEventListener('change', () => {
            // Marcar como requisição iniciada pelo usuário
            this.state.userInitiatedRequest = true;
            this.updateTurnoChoices(this.elements.nivel.value, true);
        });
        this.elements.turno.addEventListener('change', () => {
            // Marcar como requisição iniciada pelo usuário
            this.state.userInitiatedRequest = true;
            this.handleTurnoChange();
        });
        this.elements.ano.addEventListener('change', () => {
            // Marcar como requisição iniciada pelo usuário
            this.state.userInitiatedRequest = true;
            this.handleAnoChange();
        });
    
        // Intercepta todos os cliques de paginação
        this.setupPaginationInterception();
    }
    
    setupPaginationInterception() {
        // Método para gerenciar clicks em links de paginação
        const handlePaginationClick = (e) => {
            e.preventDefault();
            
            if (this.state.requestInProgress) return;
            
            // Marcar como requisição iniciada pelo usuário
            this.state.userInitiatedRequest = true;
            
            let page;
            let url;
            
            // Determinar a página a partir do elemento clicado
            const pageLink = e.currentTarget;
            
            if (pageLink.hasAttribute('data-page')) {
                page = pageLink.getAttribute('data-page');
            } else if (pageLink.href) {
                url = new URL(pageLink.href);
                page = url.searchParams.get('page') || 1;
            } else {
                // Se não tem href nem data-page, verifique se o botão tem um valor específico
                const pageText = pageLink.textContent.trim();
                if (!isNaN(pageText) && pageText !== '') {
                    page = pageText;
                }
            }
            
            if (page) {
                // Criar parâmetros mantendo os filtros atuais
                const currentParams = {
                    nivel: this.elements.nivel.value,
                    turno: this.elements.turno.value,
                    ano: this.elements.ano.value,
                    search: this.elements.search.value.trim(),
                    page: page
                };
                
                // Atualizar estado e buscar alunos
                this.state.currentPage = parseInt(page);
                this.fetchAlunos(currentParams);
                
                return true;
            }
            
            return false;
        };
        
        // Aplicar o interceptor aos links de paginação existentes
        this.attachPaginationHandlers(handlePaginationClick.bind(this));
        
        // Salvar o método para uso posterior (quando a paginação for atualizada)
        this.handlePaginationClick = handlePaginationClick.bind(this);
        
        // Também expor o método globalmente para compatibilidade com código existente
        window.handlePaginationClick = (e, pageUrl) => {
            if (e) e.preventDefault();
            
            if (this.state.requestInProgress) return;
            
            this.state.userInitiatedRequest = true;
            
            if (pageUrl) {
                const url = new URL(pageUrl, window.location.origin);
                const page = url.searchParams.get('page') || 1;
                
                const currentParams = {
                    nivel: this.elements.nivel.value,
                    turno: this.elements.turno.value,
                    ano: this.elements.ano.value,
                    search: this.elements.search.value.trim(),
                    page: page
                };
                
                this.state.currentPage = parseInt(page);
                this.fetchAlunos(currentParams);
                
                return true;
            }
            
            if (e && e.currentTarget) {
                return this.handlePaginationClick(e);
            }
            
            return false;
        };
    }
    
    // Método para anexar manipuladores de eventos aos links de paginação
    attachPaginationHandlers(handler) {
        if (!this.elements.pagination) return;
        
        // Primeiro, selecionamos todos os elementos que precisam de handlers de paginação
        const paginationLinks = this.elements.pagination.querySelectorAll('.page-link');
        const pageItems = this.elements.pagination.querySelectorAll('.page-item');
        
        paginationLinks.forEach(link => {
            // Remover manipuladores antigos para evitar duplicação
            link.removeEventListener('click', handler);
            // Adicionar novo manipulador
            link.addEventListener('click', handler);
            
            // Garantir que o link tenha conteúdo visível
            if (link.textContent.trim() === '' && link.parentElement.classList.contains('page-item') && 
                !link.parentElement.classList.contains('prev') && !link.parentElement.classList.contains('next')) {
                // Se for um item de página numérica sem texto, adicione o número da página
                const dataPage = link.getAttribute('data-page');
                if (dataPage) {
                    link.textContent = dataPage;
                } else if (link.href) {
                    const url = new URL(link.href);
                    const page = url.searchParams.get('page');
                    if (page) {
                        link.textContent = page;
                    }
                }
            }
        });
        
        // Também adicione handlers aos itens de página (para melhorar a área clicável)
        pageItems.forEach(item => {
            // Só adicione se não for um item que já contenha um link
            if (!item.querySelector('.page-link')) {
                item.removeEventListener('click', handler);
                item.addEventListener('click', handler);
            }
        });
    }
    

    toggleView(view) {
        const {alunosContainer, viewGrid, viewList} = this.elements;
        
        // Reset all button states first
        viewGrid.classList.remove('active', 'btn-primary');
        viewList.classList.remove('active', 'btn-primary');
        viewGrid.classList.add('btn-outline-secondary');
        viewList.classList.add('btn-outline-secondary');
        
        if (view === 'grid') {
            // Apply grid view
            alunosContainer.classList.remove('list-view');
            // Update button states
            viewGrid.classList.add('active', 'btn-primary');
            viewGrid.classList.remove('btn-outline-secondary');
        } else {
            // Apply list view
            alunosContainer.classList.add('list-view');
            // Update button states
            viewList.classList.add('active', 'btn-primary');
            viewList.classList.remove('btn-outline-secondary');
        }
        
        // Save preference
        localStorage.setItem('alunosView', view);
    }

    async fetchAlunos(params = {}) {
        // Permitir requisições iniciadas pelo usuário mesmo durante a inicialização
        if (!this.state.userInitiatedRequest && !initialPageLoadComplete && this.state.skipInitialAjaxRequest) {
            console.log('Skipping initial AJAX request - page already loaded with data');
            return;
        }
        
        // Prevenir requisições simultâneas
        if (this.state.isLoading || this.state.requestInProgress) {
            return;
        }
        
        try {
            this.state.isLoading = true;
            this.state.requestInProgress = true;
            this.elements.loadingOverlay.style.display = 'flex';
            
            const queryParams = new URLSearchParams(
                Object.entries(params).filter(([_, value]) => value)
            );
            
            console.log('Fetching alunos with params:', queryParams.toString());
            
            const response = await fetch(`/alunos/buscar/?${queryParams.toString()}`, {
                headers: {'X-Requested-With': 'XMLHttpRequest'}
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}, message: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Verificar se o JSON contém a propriedade html
            if (!data.html) {
                console.error('Invalid response format - missing html property:', data);
                throw new Error('Formato de resposta inválido');
            }
            
            this.elements.alunosContainer.innerHTML = data.html;
            
            if (data.total_alunos !== undefined) {
                this.elements.totalResults.textContent = data.total_alunos;
            }
            
            // Marcar que os dados foram carregados
            this.state.initialDataLoaded = true;
            this.state.skipInitialAjaxRequest = false; // Desativar o skip após a primeira requisição
            
            // Update URL with new parameters
            const newUrl = new URL(window.location.href);
            Object.entries(params).forEach(([key, value]) => {
                if (value) {
                    newUrl.searchParams.set(key, value);
                } else {
                    newUrl.searchParams.delete(key);
                }
            });
            window.history.pushState({}, '', newUrl);
            
            // Update pagination state
            if (data.current_page) {
                this.state.currentPage = parseInt(data.current_page);
            }
            if (data.total_pages) {
                this.state.totalPages = parseInt(data.total_pages);
            }
            
            // Atualizar a paginação no DOM se estiver presente na resposta
            if (data.pagination_html) {
                if (this.elements.pagination) {
                    this.elements.pagination.outerHTML = data.pagination_html;
                    // Atualizar a referência ao elemento de paginação
                    this.elements.pagination = document.querySelector('.pagination');
                }
            }
            
            // Update pagination UI
            this.updatePaginationUI();

        } catch (error) {
            console.error('Error fetching alunos:', error);
            this.elements.alunosContainer.innerHTML = `
                <div class="alert alert-danger">
                    <h5>Erro ao carregar os alunos</h5>
                    <p>Por favor, tente novamente.</p>
                    <small class="text-muted">${error.message}</small>
                </div>
            `;
        } finally {
            // Resetar a flag de requisição iniciada pelo usuário
            this.state.userInitiatedRequest = false;
            
            // Atraso pequeno para evitar cliques rápidos
            setTimeout(() => {
                this.state.isLoading = false;
                this.state.requestInProgress = false;
                this.elements.loadingOverlay.style.display = 'none';
            }, 300);
        }
    }
    
    updatePaginationUI() {
        if (!this.elements.pagination) return;
        
        // Update active state
        const currentPage = this.state.currentPage;
        const totalPages = this.state.totalPages;
        
        // Inicializar os links de paginação corretamente
        // Verificar se os botões numéricos têm texto visível
        const pageItems = this.elements.pagination.querySelectorAll('.page-item');
        
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
        
        // Agora, atualize a exibição da paginação
        pageItems.forEach(item => {
            item.classList.remove('active');
            
            // Pular botões prev e next
            if (item.classList.contains('prev') || item.classList.contains('next')) {
                return;
            }
            
            // Verificar se deve mostrar este item
            const link = item.querySelector('.page-link');
            if (link) {
                let pageNumber;
                
                // Determinar o número da página deste botão
                if (item.dataset.page) {
                    pageNumber = parseInt(item.dataset.page);
                } else if (link.dataset.page) {
                    pageNumber = parseInt(link.dataset.page);
                } else if (link.textContent.trim() !== '...') {
                    pageNumber = parseInt(link.textContent.trim());
                }
                
                if (pageNumber) {
                    // Se for a página atual, marcar como ativa
                    if (pageNumber === currentPage) {
                        item.classList.add('active');
                    }
                    
                    // Decidir se deve mostrar ou ocultar este botão
                    if (visiblePages.includes(pageNumber)) {
                        item.style.display = '';
                        
                        // Garantir que o botão tenha um número visível
                        if (link.textContent.trim() === '') {
                            link.textContent = pageNumber;
                        }
                    } else {
                        // Se não estiver nas páginas visíveis, ocultar
                        item.style.display = 'none';
                    }
                } else if (link.textContent.trim() === '...') {
                    // Se for um botão de reticências, mostrar apenas se necessário
                    if (pagesWithEllipsis.includes('...')) {
                        item.style.display = '';
                        pagesWithEllipsis.splice(pagesWithEllipsis.indexOf('...'), 1);
                    } else {
                        item.style.display = 'none';
                    }
                }
            }
        });
        
        // Disable/enable previous and next buttons
        const prevButton = this.elements.pagination.querySelector('.page-item.prev');
        const nextButton = this.elements.pagination.querySelector('.page-item.next');
        
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
        
        // Atualizar os links de paginação para usar os filtros atuais
        this.updatePaginationLinks();
        
        // Reattach event handlers to pagination links
        if (this.handlePaginationClick) {
            this.attachPaginationHandlers(this.handlePaginationClick);
        }
    }
    
    updatePaginationLinks() {
        if (!this.elements.pagination) return;
        
        // Obter os filtros atuais
        const currentFilters = {
            nivel: this.elements.nivel.value,
            turno: this.elements.turno.value,
            ano: this.elements.ano.value,
            search: this.elements.search.value.trim()
        };
        
        // Filtrar apenas os não vazios
        const activeFilters = Object.fromEntries(
            Object.entries(currentFilters).filter(([_, v]) => v)
        );
        
        // Atualizar os links de paginação para incluir os filtros atuais
        const paginationLinks = this.elements.pagination.querySelectorAll('.page-link[href]');
        
        paginationLinks.forEach(link => {
            const url = new URL(link.getAttribute('href'), window.location.origin);
            
            // Preservar o parâmetro de página
            const page = url.searchParams.get('page');
            
            // Limpar parâmetros existentes
            url.search = '';
            
            // Adicionar os filtros ativos
            Object.entries(activeFilters).forEach(([key, value]) => {
                url.searchParams.set(key, value);
            });
            
            // Adicionar o parâmetro de página de volta
            if (page) {
                url.searchParams.set('page', page);
            }
            
            // Atualizar o href
            link.setAttribute('href', url.toString());
            
            // Também adicionar data-page para facilitar acesso
            if (page && !link.hasAttribute('data-page')) {
                link.setAttribute('data-page', page);
            }
        });
    }

    updateTurnoChoices(nivel, shouldFetchData = true) {
        const {turno} = this.elements;
        turno.innerHTML = '<option value="">Selecione o Turno</option>';
        
        if (nivel === 'EFI') {
            this.addOption(turno, 'M', 'Manhã');
            turno.value = 'M';
            turno.disabled = true;
            
            // Sempre buscar dados quando explicitamente solicitado
            if (shouldFetchData) {
                this.fetchAlunos({nivel, turno: 'M'});
            }
        } else if (nivel === 'EFF') {
            turno.disabled = false;
            ['M', 'T'].forEach(value => {
                this.addOption(turno, value, value === 'M' ? 'Manhã' : 'Tarde');
            });
            
            // Sempre buscar dados quando explicitamente solicitado
            if (shouldFetchData) {
                this.fetchAlunos({nivel});
            }
        } else {
            turno.disabled = true;
            this.elements.ano.disabled = true;
            
            // Sempre buscar dados quando explicitamente solicitado
            if (shouldFetchData) {
                this.fetchAlunos();
            }
        }
        
        this.updateAnoChoices(turno.value, nivel);
    }

    updateAnoChoices(turno, nivel) {
        const {ano} = this.elements;
        ano.innerHTML = '<option value="">Selecione o Ano</option>';
        
        if (nivel && turno && ANO_OPTIONS[nivel]?.[turno]) {
            ano.disabled = false;
            ANO_OPTIONS[nivel][turno].forEach(({value, label}) => {
                this.addOption(ano, value, label);
            });
        } else {
            ano.disabled = true;
        }
    }

    addOption(select, value, label) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = label;
        select.appendChild(option);
    }

    handleFormSubmit() {
        const {nivel, turno, ano, search} = this.elements;
        // Reset to page 1 when applying new filters
        this.state.currentPage = 1;
        this.fetchAlunos({
            nivel: nivel.value,
            turno: turno.value,
            ano: ano.value,
            search: search.value.trim(),
            page: 1
        });
    }

    handleTurnoChange() {
        const {nivel, turno} = this.elements;
        this.updateAnoChoices(turno.value, nivel.value);
        // Reset to page 1 when changing filters
        this.state.currentPage = 1;
        this.fetchAlunos({
            nivel: nivel.value,
            turno: turno.value,
            page: 1
        });
    }

    handleAnoChange() {
        const {nivel, turno, ano} = this.elements;
        // Reset to page 1 when changing filters
        this.state.currentPage = 1;
        this.fetchAlunos({
            nivel: nivel.value,
            turno: turno.value,
            ano: ano.value,
            page: 1
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new AlunosManager();
    // Marcar que o carregamento inicial está completo
    initialPageLoadComplete = true;
});
