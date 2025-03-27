// Constants and configurations
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
        this.initializeElements();
        this.initializeState();
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
        this.state = {
            isLoading: false,
            currentPage: 1,
            totalPages: 1
        };
    }

    initializeView() {
        const savedView = localStorage.getItem('alunosView') || 'grid';
        this.toggleView(savedView);

        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('nivel')) {
            this.elements.nivel.value = urlParams.get('nivel');
            this.updateTurnoChoices(this.elements.nivel.value);
        } else {
            this.fetchAlunos();
        }
        
        // Set initial pagination state from URL
        if (urlParams.has('page')) {
            this.state.currentPage = parseInt(urlParams.get('page')) || 1;
        }
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
            this.handleFormSubmit();
        });
        this.elements.nivel.addEventListener('change', () => {
            this.updateTurnoChoices(this.elements.nivel.value);
        });
        this.elements.turno.addEventListener('change', () => {
            this.handleTurnoChange();
        });
        this.elements.ano.addEventListener('change', () => {
            this.handleAnoChange();
        });
    
        // Pagination
        document.addEventListener('click', (e) => {
            if (e.target.matches('.pagination .page-link')) {
                e.preventDefault();
                // Get page number either from data-page attribute or from URL
                let page;
                if (e.target.hasAttribute('data-page')) {
                    page = e.target.getAttribute('data-page');
                } else if (e.target.href) {
                    const url = new URL(e.target.href);
                    page = url.searchParams.get('page');
                }
                
                if (page) {
                    // Update current page state
                    this.state.currentPage = parseInt(page);
                    
                    const currentParams = {
                        nivel: this.elements.nivel.value,
                        turno: this.elements.turno.value,
                        ano: this.elements.ano.value,
                        search: this.elements.search.value.trim(),
                        page: page
                    };
                    
                    this.fetchAlunos(currentParams);
                }
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
        if (this.state.isLoading) return;
        
        try {
            this.state.isLoading = true;
            this.elements.loadingOverlay.style.display = 'flex';
            
            const queryParams = new URLSearchParams(
                Object.entries(params).filter(([_, value]) => value)
            );
            
            const response = await fetch(`/alunos/buscar/?${queryParams.toString()}`, {
                headers: {'X-Requested-With': 'XMLHttpRequest'}
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            this.elements.alunosContainer.innerHTML = data.html;
            this.elements.totalResults.textContent = data.total_alunos;
            
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
                </div>
            `;
        } finally {
            this.state.isLoading = false;
            this.elements.loadingOverlay.style.display = 'none';
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
        
        // Re-attach click handlers to all pagination links
        document.querySelectorAll('.pagination .page-link').forEach(link => {
            // Clear any previous click handlers
            const newLink = link.cloneNode(true);
            link.parentNode.replaceChild(newLink, link);
        });
    }

    updateTurnoChoices(nivel) {
        const {turno} = this.elements;
        turno.innerHTML = '<option value="">Selecione o Turno</option>';
        
        if (nivel === 'EFI') {
            this.addOption(turno, 'M', 'Manhã');
            turno.value = 'M';
            turno.disabled = true;
            this.fetchAlunos({nivel, turno: 'M'});
        } else if (nivel === 'EFF') {
            turno.disabled = false;
            ['M', 'T'].forEach(value => {
                this.addOption(turno, value, value === 'M' ? 'Manhã' : 'Tarde');
            });
            this.fetchAlunos({nivel});
        } else {
            turno.disabled = true;
            this.elements.ano.disabled = true;
            this.fetchAlunos();
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
