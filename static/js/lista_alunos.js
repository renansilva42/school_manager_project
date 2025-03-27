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
        // Método global para gerenciar clicks em links de paginação
        // Isso permite que outros scripts como mobile-pagination.js se conectem a ele
        window.handlePaginationClick = (e, pageUrl) => {
            e.preventDefault();
            
            if (this.state.requestInProgress) return;
            
            // Marcar como requisição iniciada pelo usuário
            this.state.userInitiatedRequest = true;
            
            let page;
            let url;
            
            // Determinar a página a partir do evento ou da URL fornecida
            if (pageUrl) {
                url = new URL(pageUrl, window.location.origin);
                page = url.searchParams.get('page') || 1;
            } else if (e.currentTarget.hasAttribute('data-page')) {
                page = e.currentTarget.getAttribute('data-page');
            } else if (e.currentTarget.href) {
                url = new URL(e.currentTarget.href);
                page = url.searchParams.get('page') || 1;
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
                
                return true; // Indica que o evento foi manipulado
            }
            
            return false; // Indica que o evento não foi manipulado
        };
        
        // Aplicar o interceptor aos links de paginação
        document.addEventListener('click', (e) => {
            if (e.target.matches('.pagination .page-link')) {
                window.handlePaginationClick(e);
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
        
        // Set active page
        $('.pagination .page-item').removeClass('active');
        $(`.pagination .page-item[data-page="${currentPage}"]`).addClass('active');
        
        // Disable/enable previous and next buttons
        $('.pagination .page-item.prev').toggleClass('disabled', currentPage === 1);
        $('.pagination .page-item.next').toggleClass('disabled', currentPage === totalPages);
        
        // Atualizar os links de paginação para usar os filtros atuais
        this.updatePaginationLinks();
    }
    
    updatePaginationLinks() {
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
        document.querySelectorAll('.pagination .page-link').forEach(link => {
            if (link.hasAttribute('href')) {
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
});
