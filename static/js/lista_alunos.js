document.addEventListener('DOMContentLoaded', function() {
    const searchButton = document.getElementById('search-button');
    const searchInput = document.getElementById('search-input');
    const nivelFilter = document.getElementById('nivel-filter');
    const turnoFilter = document.getElementById('turno-filter');
    const anoFilter = document.getElementById('ano-filter');
    
    // Função para buscar alunos
    function fetchAlunos(params) {
        fetch(`/alunos/buscar?${new URLSearchParams(params)}`)
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('alunos-container');
                container.innerHTML = data.html;
            })
            .catch(error => {
                console.error('Erro ao buscar alunos:', error);
                notificationSystem.showError('Erro ao buscar alunos');
            });
    }
    
    // Event listener para o botão de busca
    searchButton.addEventListener('click', () => {
        const params = {
            search: searchInput.value,
            nivel: nivelFilter.value,
            turno: turnoFilter.value,
            ano: anoFilter.value
        };
        fetchAlunos(params);
    });
    
    // Event listeners para os filtros dropdown
    [nivelFilter, turnoFilter, anoFilter].forEach(filter => {
        filter.addEventListener('change', () => {
            const params = {
                nivel: nivelFilter.value,
                turno: turnoFilter.value,
                ano: anoFilter.value
            };
            fetchAlunos(params);
        });
    });
});