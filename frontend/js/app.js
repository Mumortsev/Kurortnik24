/**
 * Main App Module - Navigation, Auth, Checkout, Modal
 */
const App = {
    // State
    currentView: 'productsView',
    user: null,
    isAuthorized: false,

    /**
     * Initialize app
     */
    async init() {
        // Initialize cart first
        Cart.init();

        // Telegram WebApp
        this.initTelegramWebApp();

        // Initialize modules
        await Catalog.init();

        // Setup event listeners
        this.setupEventListeners();

        // Update cart badges
        this.updateCartBadge();

        // Check for existing session
        this.checkAuth();

        // Update welcome message
        this.updateWelcomeMessage();
    },

    /**
     * Initialize Telegram WebApp
     */
    initTelegramWebApp() {
        if (window.Telegram && Telegram.WebApp) {
            const tg = Telegram.WebApp;

            // Expand to full height
            tg.expand();

            // Set theme colors
            document.documentElement.style.setProperty('--tg-bg-color', tg.backgroundColor || '#F5F0E8');
            document.documentElement.style.setProperty('--tg-text-color', tg.textColor || '#1a1a2e');

            // Get user from Telegram
            if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
                this.user = tg.initDataUnsafe.user;
                this.isAuthorized = true;
                this.updateProfileUI();
            }

            // Enable closing confirmation
            tg.enableClosingConfirmation();

            // Back button handler
            tg.BackButton.onClick(() => this.goBack());
        }
    },

    /**
     * Update welcome message with user name
     */
    updateWelcomeMessage() {
        const welcomeEl = document.getElementById('welcomeMessage');
        if (this.user && this.user.first_name) {
            welcomeEl.textContent = `Добро пожаловать, ${this.user.first_name}!`;
        } else {
            welcomeEl.textContent = 'Добро пожаловать!';
        }
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Back buttons
        document.getElementById('productBackBtn').addEventListener('click', () => this.showCatalog());
        document.getElementById('cartBackBtn').addEventListener('click', () => this.showCatalog());
        document.getElementById('checkoutBackBtn').addEventListener('click', () => this.showCart());
        document.getElementById('profileBackBtn').addEventListener('click', () => this.showCatalog());

        // Checkout button
        document.getElementById('checkoutBtn').addEventListener('click', () => {
            this.showView('checkoutView');
            this.renderCheckoutSummary();
        });

        // Customer type change
        document.getElementById('customerType').addEventListener('change', (e) => {
            const orgGroup = document.getElementById('orgNameGroup');
            const orgInput = document.getElementById('customerOrg');

            if (e.target.value === 'company' || e.target.value === 'sole_proprietor') {
                orgGroup.style.display = 'block';
                orgInput.required = true;
            } else {
                orgGroup.style.display = 'none';
                orgInput.required = false;
                orgInput.value = '';
            }
        });

        // Checkout form
        document.getElementById('checkoutForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitOrder();
        });

        // Telegram auth button
        document.getElementById('telegramAuthBtn').addEventListener('click', () => {
            this.telegramAuth();
        });

        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.logout();
        });

        // Bottom navigation
        this.setupBottomNav();

        // Product modal
        this.setupModal();
    },

    /**
     * Setup bottom navigation
     */
    setupBottomNav() {
        const navItems = document.querySelectorAll('.nav-item[data-view]');

        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const viewId = item.dataset.view;

                // Update active state
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                item.classList.add('active');

                // Show view
                if (viewId === 'cartView') {
                    this.showCart();
                } else if (viewId === 'profileView') {
                    this.showView('profileView');
                } else {
                    this.showCatalog();
                }
            });
        });


    },

    /**
     * Setup product modal
     */
    setupModal() {
        const modal = document.getElementById('productModal');
        const backdrop = document.getElementById('modalBackdrop');
        const closeBtn = document.getElementById('modalCloseBtn');
        const cartBtn = document.getElementById('modalCartBtn');

        // Close on backdrop click
        backdrop.addEventListener('click', () => this.closeModal());

        // Close button
        closeBtn.addEventListener('click', () => this.closeModal());

        // Cart button in modal
        cartBtn.addEventListener('click', () => {
            this.closeModal();
            this.showCart();
        });

        // Handle swipe down to close
        let startY = 0;
        const content = modal.querySelector('.product-modal-content');

        content.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
        }, { passive: true });

        content.addEventListener('touchmove', (e) => {
            const deltaY = e.touches[0].clientY - startY;
            if (deltaY > 100) {
                this.closeModal();
            }
        }, { passive: true });
    },

    /**
     * Open product modal
     */
    openModal(productId) {
        const modal = document.getElementById('productModal');
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';

        // Load product details
        Catalog.showProductInModal(productId);

        // Update modal cart badge
        this.updateModalCartBadge();
    },

    /**
     * Close product modal
     */
    closeModal() {
        const modal = document.getElementById('productModal');
        modal.classList.remove('active');
        document.body.style.overflow = '';
    },

    /**
     * Update modal cart badge
     */
    updateModalCartBadge() {
        const badge = document.getElementById('modalCartBadge');
        const count = Cart.getItemsCount();

        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    },

    /**
     * Check for saved session
     */
    checkAuth() {
        const savedUser = localStorage.getItem('shop_user');
        if (savedUser) {
            try {
                this.user = JSON.parse(savedUser);
                this.isAuthorized = true;
                this.updateProfileUI();
                this.updateWelcomeMessage();
            } catch (e) {
                localStorage.removeItem('shop_user');
            }
        }
    },

    /**
     * Telegram auth
     */
    telegramAuth() {
        if (window.Telegram && Telegram.WebApp) {
            const tg = Telegram.WebApp;

            if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
                this.user = tg.initDataUnsafe.user;
                this.isAuthorized = true;
                localStorage.setItem('shop_user', JSON.stringify(this.user));
                this.updateProfileUI();
                this.updateWelcomeMessage();
                this.showToast('Вы авторизованы!');
            } else {
                this.showToast('Откройте приложение через Telegram');
            }
        } else {
            // Demo mode
            this.user = {
                id: 12345678,
                first_name: 'Гость',
                username: 'demo_user'
            };
            this.isAuthorized = true;
            localStorage.setItem('shop_user', JSON.stringify(this.user));
            this.updateProfileUI();
            this.updateWelcomeMessage();
            this.showToast('Демо авторизация');
        }
    },

    /**
     * Logout
     */
    logout() {
        this.user = null;
        this.isAuthorized = false;
        localStorage.removeItem('shop_user');
        this.updateProfileUI();
        this.updateWelcomeMessage();
        this.showToast('Вы вышли из аккаунта');
    },

    /**
     * Update profile UI
     */
    updateProfileUI() {
        const authSection = document.getElementById('profileAuth');
        const infoSection = document.getElementById('profileInfo');

        if (this.isAuthorized && this.user) {
            authSection.style.display = 'none';
            infoSection.style.display = 'block';

            document.getElementById('profileName').textContent =
                this.user.first_name + (this.user.last_name ? ' ' + this.user.last_name : '');
            document.getElementById('profileId').textContent = 'ID: ' + this.user.id;

            this.loadOrders();
        } else {
            authSection.style.display = 'block';
            infoSection.style.display = 'none';
        }
    },

    /**
     * Load user orders
     */
    async loadOrders() {
        if (!this.user) {
            document.getElementById('ordersEmpty').style.display = 'block';
            document.getElementById('ordersList').innerHTML = '';
            return;
        }

        try {
            const orders = await API.getOrders(this.user.id);

            // Handle wrapped response {orders: []} or array []
            const ordersList = orders.orders ? orders.orders : orders;

            if (!ordersList || !Array.isArray(ordersList) || ordersList.length === 0) {
                document.getElementById('ordersEmpty').style.display = 'block';
                document.getElementById('ordersList').innerHTML = '';
                return;
            }

            document.getElementById('ordersEmpty').style.display = 'none';

            const html = ordersList.map(order => {
                const itemsHtml = order.items.map(item => `
                    <div class="order-item-row">
                        <span>${item.product_name} x ${item.quantity_packs}</span>
                        <span>${item.subtotal}₽</span>
                    </div>
                `).join('');

                return `
                <div class="order-card">
                    <div class="order-header">
                        <span class="order-id">Заказ #${order.id}</span>
                        <span class="order-status ${order.status}">${this.getStatusLabel(order.status)}</span>
                    </div>
                    <div class="order-items-list">
                        ${itemsHtml}
                    </div>
                    <div class="order-footer">
                        <span class="order-total-label">Итого:</span>
                        <span class="order-total">${order.total_amount || order.total}₽</span>
                    </div>
                     <div class="order-date-row">
                        <span class="order-date">${this.formatDate(order.created_at)}</span>
                    </div>
                </div>
            `}).join('');

            document.getElementById('ordersList').innerHTML = html;
        } catch (error) {
            console.error('Failed to load orders:', error);
            document.getElementById('ordersEmpty').style.display = 'block';
        }
    },

    /**
     * Get status label
     */
    getStatusLabel(status) {
        const labels = {
            'new': 'Новый',
            'accepted': 'Принят',
            'rejected': 'Отклонён',
            'completed': 'Выполнен'
        };
        return labels[status] || status;
    },

    /**
     * Format date
     */
    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
    },

    /**
     * Show view
     */
    showView(viewId) {
        // Hide all views
        document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));

        // Show target view
        const view = document.getElementById(viewId);
        if (view) {
            view.classList.remove('hidden');
            this.currentView = viewId;
        }

        // Toggle header visibility
        const header = document.querySelector('.header');
        const hideHeaderViews = ['checkoutView', 'cartView', 'profileView'];

        if (hideHeaderViews.includes(viewId)) {
            header.style.display = 'none';
        } else {
            header.style.display = 'block';
        }

        // Update back button
        this.updateBackButton();

        // Update nav active state
        this.updateNavActiveState(viewId);
    },

    /**
     * Update nav active state
     */
    updateNavActiveState(viewId) {
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

        if (viewId === 'productsView') {
            document.getElementById('navHome').classList.add('active');
        } else if (viewId === 'cartView') {
            document.getElementById('navCart').classList.add('active');
        } else if (viewId === 'profileView') {
            document.getElementById('navProfile').classList.add('active');
        }
    },

    /**
     * Update Telegram back button
     */
    updateBackButton() {
        if (window.Telegram && Telegram.WebApp) {
            if (this.currentView !== 'productsView') {
                Telegram.WebApp.BackButton.show();
            } else {
                Telegram.WebApp.BackButton.hide();
            }
        }
    },

    /**
     * Go back
     */
    goBack() {
        switch (this.currentView) {
            case 'productView':
            case 'profileView':
            case 'cartView':
                this.showCatalog();
                break;
            case 'checkoutView':
                this.showCart();
                break;
            default:
                this.showCatalog();
        }
    },

    /**
     * Show catalog
     */
    showCatalog() {
        this.showView('productsView');
    },

    /**
     * Show cart
     */
    showCart() {
        this.showView('cartView');
        this.renderCart();
    },

    /**
     * Render cart
     */
    renderCart() {
        const items = Cart.items;
        const container = document.getElementById('cartItems');
        const emptyMsg = document.getElementById('cartEmpty');
        const footer = document.getElementById('cartFooter');

        if (items.length === 0) {
            container.innerHTML = '';
            emptyMsg.style.display = 'block';
            footer.style.display = 'none';
            return;
        }

        emptyMsg.style.display = 'none';
        footer.style.display = 'block';

        const html = items.map(item => {
            const pieces = item.packs * item.product.pieces_per_pack;
            const subtotal = pieces * item.product.price_per_unit;

            return `
            <div class="cart-item" data-id="${item.product.id}">
                <img class="cart-item-image" src="${API.getImageUrl(item.product.image, 'small')}" 
                     alt="${item.product.name}"
                     onerror="this.src='assets/placeholder.png'">
                <div class="cart-item-info">
                    <div class="cart-item-name">${item.product.name}</div>
                    <div class="cart-item-details">${item.packs} пач. × ${item.product.pieces_per_pack} шт = ${pieces} шт</div>
                    <div class="cart-item-controls">
                        <button class="cart-qty-btn" data-action="decrease" ${item.packs <= 1 ? 'disabled' : ''}>−</button>
                        <span class="cart-item-qty">${item.packs}</span>
                        <button class="cart-qty-btn" data-action="increase">+</button>
                        <span class="cart-item-price">${subtotal.toFixed(0)}₽</span>
                        <button class="cart-item-remove" data-action="remove">🗑</button>
                    </div>
                </div>
            </div>
        `}).join('');

        container.innerHTML = html;

        // Update total
        document.getElementById('cartTotal').textContent = Cart.getTotal().toFixed(0) + '₽';

        // Add handlers
        container.querySelectorAll('.cart-item').forEach(el => {
            const productId = parseInt(el.dataset.id);

            el.querySelector('[data-action="decrease"]').addEventListener('click', () => {
                const item = Cart.items.find(i => i.product.id === productId);
                if (item && item.packs > 1) {
                    Cart.updateQuantity(productId, item.packs - 1);
                    this.renderCart();
                    this.updateCartBadge();
                }
            });

            el.querySelector('[data-action="increase"]').addEventListener('click', () => {
                const item = Cart.items.find(i => i.product.id === productId);
                if (item) {
                    Cart.updateQuantity(productId, item.packs + 1);
                    this.renderCart();
                    this.updateCartBadge();
                }
            });

            el.querySelector('[data-action="remove"]').addEventListener('click', () => {
                Cart.removeItem(productId);
                this.renderCart();
                this.updateCartBadge();
                this.showToast('Товар удалён');
            });
        });
    },

    /**
     * Render checkout summary
     */
    renderCheckoutSummary() {
        const items = Cart.items;
        const container = document.getElementById('checkoutSummary');

        let html = items.map(item => {
            const pieces = item.packs * item.product.pieces_per_pack;
            const subtotal = pieces * item.product.price_per_unit;

            return `
            <div class="checkout-summary-item">
                <span>${item.product.name} × ${item.packs} пач.</span>
                <span>${subtotal.toFixed(0)}₽</span>
            </div>
        `}).join('');

        html += `
            <div class="checkout-summary-total">
                <span>Итого:</span>
                <span>${Cart.getTotal().toFixed(0)}₽</span>
            </div>
        `;

        container.innerHTML = html;

        // Pre-fill form if authorized
        if (this.user) {
            const nameInput = document.getElementById('customerName');
            if (!nameInput.value && this.user.first_name) {
                nameInput.value = this.user.first_name + (this.user.last_name ? ' ' + this.user.last_name : '');
            }
        }
    },

    /**
     * Submit order
     */
    async submitOrder() {
        const items = Cart.items;
        if (items.length === 0) {
            this.showToast('Корзина пуста');
            return;
        }

        const name = document.getElementById('customerName').value.trim();
        const phone = document.getElementById('customerPhone').value.trim();
        const customerType = document.getElementById('customerType').value;
        const orgName = document.getElementById('customerOrg').value.trim();
        const comment = document.getElementById('customerComment').value.trim();

        if (!name) {
            this.showToast('Введите имя');
            return;
        }
        if (!phone) {
            this.showToast('Введите телефон');
            return;
        }
        if (!customerType) {
            this.showToast('Выберите тип клиента');
            return;
        }
        if ((customerType === 'company' || customerType === 'sole_proprietor') && !orgName) {
            this.showToast('Введите название организации');
            return;
        }

        const orderData = {
            telegram_user_id: this.user?.id || 0,
            customer_name: name,
            customer_phone: phone,
            customer_organization: orgName || null,
            items: items.map(item => ({
                product_id: item.product.id,
                quantity_packs: item.packs
            }))
        };

        try {
            await API.createOrder(orderData);
            Cart.clear();
            this.updateCartBadge();
            this.showToast('Заказ оформлен!');
            this.showCatalog();

            if (this.isAuthorized) {
                setTimeout(() => {
                    this.showView('profileView');
                    this.loadOrders();
                }, 1000);
            }

        } catch (error) {
            console.error('Order failed:', error);
            this.showToast('Ошибка оформления заказа');
        }
    },

    /**
     * Update all cart badges
     */
    updateCartBadge() {
        const count = Cart.getItemsCount();

        // Header badge
        const headerBadge = document.getElementById('cartBadge');
        if (headerBadge) {
            if (count > 0) {
                headerBadge.textContent = count;
                headerBadge.style.display = 'flex';
            } else {
                headerBadge.style.display = 'none';
            }
        }

        // Nav badge
        const navBadge = document.getElementById('navCartBadge');
        if (navBadge) {
            if (count > 0) {
                navBadge.textContent = count;
                navBadge.style.display = 'flex';
            } else {
                navBadge.style.display = 'none';
            }
        }

        // Modal badge
        this.updateModalCartBadge();
    },

    /**
     * Show toast message
     */
    showToast(message) {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.classList.add('show');

        setTimeout(() => {
            toast.classList.remove('show');
        }, 2500);
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});

// Make it global
window.App = App;
