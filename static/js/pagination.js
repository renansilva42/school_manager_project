// static/js/pagination.js
document.addEventListener('DOMContentLoaded', function() {
    const pagination = document.querySelector('.pagination');
    
    if (pagination) {
        // Adiciona loading state aos links
        pagination.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', function(e) {
                if (!this.classList.contains('disabled')) {
                    this.innerHTML += '<span class="spinner-border spinner-border-sm ms-2"></span>';
                }
            });
        });

        // Mantém os parâmetros de filtro na URL
        const currentUrl = new URL(window.location.href);
        const filterParams = new URLSearchParams(currentUrl.search);
        
        pagination.querySelectorAll('.page-link').forEach(link => {
            if (link.href) {
                const url = new URL(link.href);
                filterParams.forEach((value, key) => {
                    if (key !== 'page') {
                        url.searchParams.set(key, value);
                    }
                });
                link.href = url.toString();
            }
        });
    }
});