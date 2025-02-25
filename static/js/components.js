/**
 * Escola Manager - Componentes Reutilizáveis
 * Este arquivo contém componentes JavaScript reutilizáveis para melhorar a interface do usuário
 */

// Sistema de notificações
class NotificationSystem {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'notification-container';
        document.body.appendChild(this.container);
        
        // Adicionar estilos
        const style = document.createElement('style');
        style.textContent = `
            .notification-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .notification {
                padding: 15px 20px;
                border-radius: 8px;
                color: white;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                display: flex;
                align-items: center;
                min-width: 300px;
                max-width: 450px;
                transform: translateX(120%);
                transition: transform 0.3s ease;
            }
            
            .notification.show {
                transform: translateX(0);
            }
            
            .notification-icon {
                margin-right: 15px;
                font-size: 1.5rem;
            }
            
            .notification-content {
                flex: 1;
            }
            
            .notification-title {
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .notification-close {
                background: transparent;
                border: none;
                color: white;
                cursor: pointer;
                font-size: 1.2rem;
                opacity: 0.7;
                transition: opacity 0.2s;
            }
            
            .notification-close:hover {
                opacity: 1;
            }
            
            .notification-success {
                background-color: #28a745;
            }
            
            .notification-error {
                background-color: #dc3545;
            }
            
            .notification-warning {
                background-color: #ffc107;
                color: #333;
            }
            
            .notification-info {
                background-color: #17a2b8;
            }
            
            @media (max-width: 768px) {
                .notification-container {
                    left: 20px;
                    right: 20px;
                }
                
                .notification {
                    min-width: auto;
                    width: 100%;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    show(message, type = 'info', duration = 5000, title = null) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        let iconClass = 'fas fa-info-circle';
        if (type === 'success') iconClass = 'fas fa-check-circle';
        if (type === 'error') iconClass = 'fas fa-exclamation-circle';
        if (type === 'warning') iconClass = 'fas fa-exclamation-triangle';
        
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="${iconClass}"></i>
            </div>
            <div class="notification-content">
                ${title ? `<div class="notification-title">${title}</div>` : ''}
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" aria-label="Fechar notificação">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        this.container.appendChild(notification);
        
        // Animar entrada
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Configurar botão de fechar
        const closeButton = notification.querySelector('.notification-close');
        closeButton.addEventListener('click', () => {
            this.close(notification);
        });
        
        // Auto-fechar após duração
        if (duration > 0) {
            setTimeout(() => {
                this.close(notification);
            }, duration);
        }
        
        return notification;
    }
    
    close(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }
    
    success(message, duration = 5000, title = 'Sucesso!') {
        return this.show(message, 'success', duration, title);
    }
    
    error(message, duration = 5000, title = 'Erro!') {
        return this.show(message, 'error', duration, title);
    }
    
    warning(message, duration = 5000, title = 'Atenção!') {
        return this.show(message, 'warning', duration, title);
    }
    
    info(message, duration = 5000, title = 'Informação') {
        return this.show(message, 'info', duration, title);
    }
}

// Inicializar sistema de notificações globalmente
window.notifications = new NotificationSystem();

// Componente de confirmação modal
class ConfirmDialog {
    constructor() {
        this.modal = null;
        this.setupModal();
    }
    
    setupModal() {
        // Criar elemento modal
        this.modal = document.createElement('div');
        this.modal.className = 'confirm-dialog-container';
        this.modal.innerHTML = `
            <div class="confirm-dialog">
                <div class="confirm-dialog-header">
                    <h3 class="confirm-dialog-title">Confirmação</h3>
                    <button class="confirm-dialog-close" aria-label="Fechar diálogo">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="confirm-dialog-body">
                    <p class="confirm-dialog-message">Tem certeza que deseja realizar esta ação?</p>
                </div>
                <div class="confirm-dialog-footer">
                    <button class="btn btn-secondary confirm-dialog-cancel">Cancelar</button>
                    <button class="btn btn-primary confirm-dialog-confirm">Confirmar</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.modal);
        
        // Adicionar estilos
        const style = document.createElement('style');
        style.textContent = `
            .confirm-dialog-container {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                opacity: 0;
                visibility: hidden;
                transition: opacity 0.3s, visibility 0.3s;
            }
            
            .confirm-dialog-container.show {
                opacity: 1;
                visibility: visible;
            }
            
            .confirm-dialog {
                background-color: white;
                border-radius: 8px;
                width: 90%;
                max-width: 500px;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
                transform: translateY(-20px);
                transition: transform 0.3s;
            }
            
            .confirm-dialog-container.show .confirm-dialog {
                transform: translateY(0);
            }
            
            .confirm-dialog-header {
                padding: 15px 20px;
                border-bottom: 1px solid #eee;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .confirm-dialog-title {
                margin: 0;
                font-size: 1.2rem;
            }
            
            .confirm-dialog-close {
                background: transparent;
                border: none;
                font-size: 1.2rem;
                cursor: pointer;
                opacity: 0.7;
                transition: opacity 0.2s;
            }
            
            .confirm-dialog-close:hover {
                opacity: 1;
            }
            
            .confirm-dialog-body {
                padding: 20px;
            }
            
            .confirm-dialog-message {
                margin: 0;
                font-size: 1rem;
            }
            
            .confirm-dialog-footer {
                padding: 15px 20px;
                border-top: 1px solid #eee;
                display: flex;
                justify-content: flex-end;
                gap: 10px;
            }
        `;
        document.head.appendChild(style);
        
        // Configurar eventos
        const closeBtn = this.modal.querySelector('.confirm-dialog-close');
        const cancelBtn = this.modal.querySelector('.confirm-dialog-cancel');
        
        closeBtn.addEventListener('click', () => {
            this.hide();
        });
        
        cancelBtn.addEventListener('click', () => {
            this.hide();
        });
        
        // Fechar ao clicar fora do diálogo
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.hide();
            }
        });
    }
    
    show(message, title = 'Confirmação') {
        return new Promise((resolve) => {
            // Atualizar conteúdo
            this.modal.querySelector('.confirm-dialog-title').textContent = title;
            this.modal.querySelector('.confirm-dialog-message').textContent = message;
            
            // Configurar botão de confirmação
            const confirmBtn = this.modal.querySelector('.confirm-dialog-confirm');
            confirmBtn.onclick = () => {
                this.hide();
                resolve(true);
            };
            
            // Configurar botão de cancelamento
            const cancelBtn = this.modal.querySelector('.confirm-dialog-cancel');
            cancelBtn.onclick = () => {
                this.hide();
                resolve(false);
            };
            
            // Mostrar modal
            this.modal.classList.add('show');
        });
    }
    
    hide() {
        this.modal.classList.remove('show');
    }
}

// Inicializar diálogo de confirmação globalmente
window.confirmDialog = new ConfirmDialog();

// Componente de carregamento
class LoadingIndicator {
    constructor() {
        this.element = null;
        this.setupElement();
    }
    
    setupElement() {
        this.element = document.createElement('div');
        this.element.className = 'loading-indicator';
        this.element.innerHTML = `
            <div class="loading-spinner"></div>
            <p class="loading-text">Carregando...</p>
        `;
        
        document.body.appendChild(this.element);
        
        // Adicionar estilos
        const style = document.createElement('style');
        style.textContent = `
            .loading-indicator {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(255, 255, 255, 0.8);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                opacity: 0;
                visibility: hidden;
                transition: opacity 0.3s, visibility 0.3s;
            }
            
            .loading-indicator.show {
                opacity: 1;
                visibility: visible;
            }
            
            .loading-spinner {
                width: 50px;
                height: 50px;
                border: 5px solid #f3f3f3;
                border-top: 5px solid var(--primary-color);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            .loading-text {
                margin-top: 15px;
                font-size: 1.1rem;
                color: var(--primary-color);
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
    
    show(text = 'Carregando...') {
        this.element.querySelector('.loading-text').textContent = text;
        this.element.classList.add('show');
    }
    
    hide() {
        this.element.classList.remove('show');
    }
}

// Inicializar indicador de carregamento globalmente
window.loadingIndicator = new LoadingIndicator();

// Utilitário para melhorar a acessibilidade
class AccessibilityHelper {
    static enhanceTabIndex() {
        // Garantir que todos os elementos interativos tenham tabindex adequado
        const interactiveElements = document.querySelectorAll('a, button, input, select, textarea');
        interactiveElements.forEach(element => {
            if (!element.hasAttribute('tabindex') && !element.disabled) {
                element.setAttribute('tabindex', '0');
            }
        });
    }
    
    static enhanceAriaLabels() {
        // Adicionar aria-labels a elementos que não têm
        const buttons = document.querySelectorAll('button:not([aria-label])');
        buttons.forEach(button => {
            if (button.textContent.trim()) {
                button.setAttribute('aria-label', button.textContent.trim());
            }
        });
        
        // Adicionar aria-labels a ícones
        const iconButtons = document.querySelectorAll('a > i, button > i');
        iconButtons.forEach(icon => {
            const parent = icon.parentElement;
            if (!parent.getAttribute('aria-label') && parent.textContent.trim()) {
                parent.setAttribute('aria-label', parent.textContent.trim());
            }
        });
    }
    
    static init() {
        // Inicializar melhorias de acessibilidade quando o DOM estiver pronto
        document.addEventListener('DOMContentLoaded', () => {
            this.enhanceTabIndex();
            this.enhanceAriaLabels();
        });
    }
}

// Inicializar helper de acessibilidade
AccessibilityHelper.init();

// Animações para elementos da interface
class UIAnimations {
    static animateEntrances() {
        // Animar elementos ao entrarem na viewport
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated-in');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        const elements = document.querySelectorAll('.card, .btn-group, .table, .form-group');
        elements.forEach(element => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            observer.observe(element);
        });
    }
    
    static addHoverEffects() {
        // Adicionar efeitos de hover a elementos interativos
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            button.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-3px)';
                this.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = '';
                this.style.boxShadow = '';
            });
        });
    }
    
    static init() {
        // Inicializar animações quando o DOM estiver pronto
        document.addEventListener('DOMContentLoaded', () => {
            // Adicionar estilos para animações
            const style = document.createElement('style');
            style.textContent = `
                .animated-in {
                    opacity: 1 !important;
                    transform: translateY(0) !important;
                }
            `;
            document.head.appendChild(style);
            
            this.animateEntrances();
            this.addHoverEffects();
        });
    }
}

// Inicializar animações de UI
UIAnimations.init();