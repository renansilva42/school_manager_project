// Aguarde o DOM carregar
document.addEventListener('DOMContentLoaded', function() {
    // Encontre todos os botões de exclusão
    const deleteButtons = document.querySelectorAll('.btn-delete');
    
    // Adicione evento de clique em cada botão
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Mostre uma confirmação amigável
            const confirmDelete = confirm(
                'Atenção!\n\n' +
                'Você está prestes a excluir este aluno.\n' +
                'Esta ação não poderá ser desfeita.\n\n' +
                'Deseja continuar?'
            );
            
            // Se não confirmar, previna a ação
            if (!confirmDelete) {
                e.preventDefault();
            }
        });
    });
    
    // Adicione feedback visual ao passar o mouse
    deleteButtons.forEach(button => {
        button.addEventListener('mouseover', function() {
            this.classList.add('btn-danger');
        });
        
        button.addEventListener('mouseout', function() {
            this.classList.remove('btn-danger');
        });
    });
});