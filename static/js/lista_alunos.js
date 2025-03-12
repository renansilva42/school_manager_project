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
            totalResults: document.getElementById('total-results')
        };
    }

    initializeState() {
        this.state = {
            isLoading: false
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
    }

    initializeEventListeners() {
        // Fix for the filter collapse button
        const filterButton = document.querySelector('[data-bs-toggle="collapse"]');
        if (filterButton) {
            // Initial state setup
            const icon = filterButton.querySelector('.fa-chevron-down');
            if (icon) {
                // Check if the collapse is initially expanded
                const isCollapsed = filterButton.classList.contains('collapsed');
                icon.style.transform = isCollapsed ? 'rotate(0deg)' : 'rotate(180deg)';
                icon.style.transition = 'transform 0.3s ease';
            }
            
            // Add event listener for click
            filterButton.addEventListener('click', () => {
                const icon = filterButton.querySelector('.fa-chevron-down');
                if (icon) {
                    // Toggle rotation based on the current state
                    const isCollapsed = filterButton.classList.contains('collapsed');
                    icon.style.transform = isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)';
                }
            });
        }
        // View toggle listeners
        this.elements.viewGrid.addEventListener('click', () => this.toggleView('grid'));
        this.elements.viewList.addEventListener('click', () => this.toggleView('list'));

        // Form listeners
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
        this.fetchAlunos({
            nivel: nivel.value,
            turno: turno.value,
            ano: ano.value,
            search: search.value.trim()
        });
    }

    handleTurnoChange() {
        const {nivel, turno} = this.elements;
        this.updateAnoChoices(turno.value, nivel.value);
        this.fetchAlunos({
            nivel: nivel.value,
            turno: turno.value
        });
    }

    handleAnoChange() {
        const {nivel, turno, ano} = this.elements;
        this.fetchAlunos({
            nivel: nivel.value,
            turno: turno.value,
            ano: ano.value
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new AlunosManager();
});