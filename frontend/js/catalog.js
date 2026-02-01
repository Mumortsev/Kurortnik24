/**
 * Catalog Module - Handles categories, subcategories and products display
 */
const Catalog = {
    // State
    categories: [],
    currentCategory: null,
    currentSubcategory: null,
    currentPage: 1,
    hasMore: true,
    isLoading: false,
    searchQuery: '',
    sortBy: 'newest',
    products: [],

    // Config
    itemsPerPage: 12,

    /**
     * Initialize catalog
     */
    async init() {
        await this.loadCategories();
        this.setupEventListeners();
        await this.loadProducts(true);
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Search
        const searchInput = document.getElementById('searchInput');
        const searchClear = document.getElementById('searchClear');

        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            searchClear.style.display = query ? 'flex' : 'none';

            searchTimeout = setTimeout(() => {
                this.searchQuery = query;
                this.loadProducts(true);
            }, 300);
        });

        searchClear.addEventListener('click', () => {
            searchInput.value = '';
            searchClear.style.display = 'none';
            this.searchQuery = '';
            this.loadProducts(true);
        });

        // Sort
        const sortSelect = document.getElementById('sortSelect');
        sortSelect.addEventListener('change', (e) => {
            this.sortBy = e.target.value;
            this.loadProducts(true);
        });

        // Infinite scroll
        const mainContent = document.getElementById('mainContent');
        mainContent.addEventListener('scroll', () => {
            if (this.isLoading || !this.hasMore) return;

            const scrollTop = mainContent.scrollTop;
            const scrollHeight = mainContent.scrollHeight;
            const clientHeight = mainContent.clientHeight;

            if (scrollTop + clientHeight >= scrollHeight - 200) {
                this.loadMoreProducts();
            }

            // Scroll to top button
            const scrollTopBtn = document.getElementById('scrollTop');
            scrollTopBtn.style.display = scrollTop > 300 ? 'block' : 'none';
        });

        // Scroll to top
        document.getElementById('scrollTop').addEventListener('click', () => {
            mainContent.scrollTo({ top: 0, behavior: 'smooth' });
        });
    },

    /**
     * Load categories
     */
    async loadCategories() {
        try {
            const data = await API.getCategories();
            this.categories = data.categories || data || [];
            this.renderCategories();
        } catch (error) {
            console.error('Failed to load categories:', error);
            this.categories = [];
        }
    },

    /**
     * Render categories
     */
    renderCategories() {
        const container = document.getElementById('categoriesSwipe');

        // "All" chip first
        let html = `<button class="category-chip all ${!this.currentCategory ? 'active' : ''}" data-id="">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="5" cy="5" r="3"/>
                <circle cx="12" cy="5" r="3"/>
                <circle cx="19" cy="5" r="3"/>
                <circle cx="5" cy="12" r="3"/>
                <circle cx="12" cy="12" r="3"/>
                <circle cx="19" cy="12" r="3"/>
            </svg>
            All
        </button>`;

        // Category chips
        this.categories.forEach(cat => {
            const isActive = this.currentCategory === cat.id;
            const icon = this.getCategoryIcon(cat.name);
            html += `<button class="category-chip ${isActive ? 'active' : ''}" data-id="${cat.id}">
                ${icon}
                ${cat.name}
            </button>`;
        });

        container.innerHTML = html;

        // Click handlers
        container.querySelectorAll('.category-chip').forEach(chip => {
            chip.addEventListener('click', () => this.selectCategory(chip.dataset.id));
        });
    },

    /**
     * Get icon for category
     */
    getCategoryIcon(categoryName) {
        const icons = {
            'Зонты': '🏖️',
            'Маски': '🤿',
            'Ласты': '🦈',
            'Обувь': '👟',
            'Палатки': '⛺',
            'Катаны': '⚔️',
            'Сачки': '🎣'
        };

        for (const [key, icon] of Object.entries(icons)) {
            if (categoryName.toLowerCase().includes(key.toLowerCase())) {
                return icon;
            }
        }
        return '';
    },

    /**
     * Select category
     */
    selectCategory(categoryId) {
        const id = categoryId ? parseInt(categoryId) : null;
        this.currentCategory = id;
        this.currentSubcategory = null;

        // Update active state
        document.querySelectorAll('.category-chip').forEach(chip => {
            const chipId = chip.dataset.id ? parseInt(chip.dataset.id) : null;
            chip.classList.toggle('active', chipId === id);
        });

        // Render subcategories
        if (id) {
            const category = this.categories.find(c => c.id === id);
            if (category && category.subcategories && category.subcategories.length > 0) {
                this.renderSubcategories(category.subcategories);
            } else {
                document.getElementById('subcategoriesSwipe').style.display = 'none';
            }
        } else {
            document.getElementById('subcategoriesSwipe').style.display = 'none';
        }

        this.updateHeaderHeight();
        this.loadProducts(true);
    },

    /**
     * Render subcategories
     */
    renderSubcategories(subcategories) {
        const container = document.getElementById('subcategoriesSwipe');

        let html = `<button class="subcategory-chip ${!this.currentSubcategory ? 'active' : ''}" data-id="">Все</button>`;

        subcategories.forEach(sub => {
            if (sub.name === 'Все') return;
            const isActive = this.currentSubcategory === sub.id;
            html += `<button class="subcategory-chip ${isActive ? 'active' : ''}" data-id="${sub.id}">${sub.name}</button>`;
        });

        container.innerHTML = html;
        container.style.display = 'flex';

        container.querySelectorAll('.subcategory-chip').forEach(chip => {
            chip.addEventListener('click', () => this.selectSubcategory(chip.dataset.id));
        });
    },

    /**
     * Select subcategory
     */
    selectSubcategory(subcategoryId) {
        const id = subcategoryId ? parseInt(subcategoryId) : null;
        this.currentSubcategory = id;

        document.querySelectorAll('.subcategory-chip').forEach(chip => {
            const chipId = chip.dataset.id ? parseInt(chip.dataset.id) : null;
            chip.classList.toggle('active', chipId === id);
        });

        this.loadProducts(true);
    },

    /**
     * Update header height
     */
    updateHeaderHeight() {
        const subcats = document.getElementById('subcategoriesSwipe');
        const hasSubcats = subcats.style.display !== 'none';
        document.documentElement.style.setProperty('--header-height', hasSubcats ? '240px' : '200px');
    },

    /**
     * Load products
     */
    async loadProducts(reset = false) {
        if (this.isLoading) return;

        if (reset) {
            this.currentPage = 1;
            this.products = [];
            this.hasMore = true;
            this.showSkeletonLoading();
        }

        this.isLoading = true;
        document.getElementById('productsLoading').style.display = reset ? 'none' : 'flex';
        document.getElementById('noProducts').style.display = 'none';

        try {
            const data = await API.getProducts({
                category: this.currentCategory,
                subcategory: this.currentSubcategory,
                search: this.searchQuery,
                sort: this.sortBy,
                page: this.currentPage,
                limit: this.itemsPerPage
            });

            const products = data.items || data.products || (Array.isArray(data) ? data : []);

            if (products.length < this.itemsPerPage) {
                this.hasMore = false;
            }

            this.products = [...this.products, ...products];
            this.renderProducts(products, !reset);

            if (this.products.length === 0) {
                document.getElementById('noProducts').style.display = 'block';
            }

        } catch (error) {
            console.error('Failed to load products:', error);
            if (reset) {
                document.getElementById('productsGrid').innerHTML =
                    '<div class="no-products"><p>Ошибка загрузки товаров</p></div>';
            }
        } finally {
            this.isLoading = false;
            document.getElementById('productsLoading').style.display = 'none';
        }
    },

    /**
     * Load more products
     */
    loadMoreProducts() {
        if (this.isLoading || !this.hasMore) return;
        this.currentPage++;
        this.loadProducts(false);
    },

    /**
     * Render products grid
     */
    renderProducts(products, append = false) {
        const grid = document.getElementById('productsGrid');

        const html = products.map(product => {
            const qtyInCart = this.getProductQtyInCart(product.id);
            const badgeHtml = product.badge ?
                `<span class="product-badge ${product.badge.type || 'hit'}">${product.badge.text || product.badge}</span>` : '';

            return `
            <div class="product-card" data-id="${product.id}">
                ${badgeHtml}
                <img 
                    class="product-image skeleton" 
                    src="${API.getImageUrl(product.image, 'small')}"
                    alt="${product.name}"
                    onload="this.classList.remove('skeleton'); this.classList.add('loaded');"
                    onerror="this.onerror=null; this.classList.remove('skeleton'); this.classList.add('loaded'); this.src='assets/placeholder.svg'"
                >
                <div class="product-info">
                    <div class="product-name">${product.name}</div>
                    <div class="product-price-row">
                        <div class="product-price">${this.formatPrice(product.price_per_unit)}<span class="currency">₽</span></div>
                    </div>
                    <div class="product-pack">${product.pieces_per_pack} шт/пач</div>
                    <div class="card-controls" onclick="event.stopPropagation();">
                        <div class="card-controls-row">
                            <button class="card-qty-btn small" onclick="Catalog.updateCardQty(${product.id}, -1)" ${qtyInCart === 0 ? 'disabled style="opacity:0.5"' : ''}>−</button>
                            ${qtyInCart > 0 ?
                    `<span class="card-qty" id="grid-qty-${product.id}">${qtyInCart}</span>` :
                    `<button class="card-add-icon-btn" onclick="Catalog.updateCardQty(${product.id}, 1)">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                        <path d="M9 22C9.55228 22 10 21.5523 10 21C10 20.4477 9.55228 20 9 20C8.44772 20 8 20.4477 8 21C8 21.5523 8.44772 22 9 22Z" fill="currentColor"/>
                                        <path d="M20 22C20.5523 22 21 21.5523 21 21C21 20.4477 20.5523 20 20 20C19.4477 20 19 20.4477 19 21C19 21.5523 19.4477 22 20 22Z" fill="currentColor"/>
                                        <path d="M1 1H5L7.68 14.39C7.77 14.83 8.02 15.22 8.38 15.5C8.74 15.78 9.19 15.92 9.64 15.9H19.36C19.81 15.92 20.26 15.78 20.62 15.5C20.98 15.22 21.23 14.83 21.32 14.39L23 6H6"/>
                                    </svg>
                                </button>`
                }
                            <button class="card-qty-btn small" onclick="Catalog.updateCardQty(${product.id}, 1)">+</button>
                        </div>
                    </div>
                </div>
            </div>
        `}).join('');

        if (append) {
            grid.insertAdjacentHTML('beforeend', html);
        } else {
            grid.innerHTML = html;
        }

        // Click handlers for card (open modal)
        grid.querySelectorAll('.product-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // Don't open modal if clicking on controls
                if (e.target.closest('.card-controls')) return;

                const productId = parseInt(card.dataset.id);
                App.openModal(productId);
            });
        });
    },

    /**
     * Add to cart from card
     */
    addToCartFromCard(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;

        Cart.addProduct(product, 1);
        App.updateCartBadge();

        // Re-render the card to show qty controls
        this.refreshCardControls(productId);
    },

    /**
     * Update card quantity
     */
    updateCardQty(productId, delta) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;

        const currentPacks = this.getProductQtyInCart(productId);
        const newPacks = currentPacks + delta;

        if (newPacks <= 0) {
            Cart.removeItem(productId);
        } else {
            if (currentPacks === 0) {
                Cart.addProduct(product, newPacks);
            } else {
                Cart.updateQuantity(productId, newPacks);
            }
        }

        App.updateCartBadge();
        this.refreshCardControls(productId);
    },

    /**
     * Refresh card controls after qty change
     */
    refreshCardControls(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;

        const card = document.querySelector(`.product-card[data-id="${productId}"]`);
        if (!card) return;

        const controlsContainer = card.querySelector('.card-controls');
        const qtyInCart = this.getProductQtyInCart(productId);

        controlsContainer.innerHTML = `
            <div class="card-controls-row">
                <button class="card-qty-btn small" onclick="Catalog.updateCardQty(${productId}, -1)" ${qtyInCart === 0 ? 'disabled style="opacity:0.5"' : ''}>−</button>
                ${qtyInCart > 0 ?
                `<span class="card-qty" id="grid-qty-${productId}">${qtyInCart}</span>` :
                `<button class="card-add-icon-btn" onclick="Catalog.updateCardQty(${productId}, 1)">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                            <path d="M9 22C9.55228 22 10 21.5523 10 21C10 20.4477 9.55228 20 9 20C8.44772 20 8 20.4477 8 21C8 21.5523 8.44772 22 9 22Z" fill="currentColor"/>
                            <path d="M20 22C20.5523 22 21 21.5523 21 21C21 20.4477 20.5523 20 20 20C19.4477 20 19 20.4477 19 21C19 21.5523 19.4477 22 20 22Z" fill="currentColor"/>
                            <path d="M1 1H5L7.68 14.39C7.77 14.83 8.02 15.22 8.38 15.5C8.74 15.78 9.19 15.92 9.64 15.9H19.36C19.81 15.92 20.26 15.78 20.62 15.5C20.98 15.22 21.23 14.83 21.32 14.39L23 6H6"/>
                        </svg>
                    </button>`
            }
                <button class="card-qty-btn small" onclick="Catalog.updateCardQty(${productId}, 1)">+</button>
            </div>
        `;
    },

    /**
     * Show product in modal
     */
    showProductInModal(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;

        // Prepare images
        let imagesHtml = '';
        const hasMultipleImages = product.images && product.images.length > 1;

        let imageSources = [];
        if (product.images && product.images.length > 0) {
            imageSources = product.images.map(img => API.getImageUrl(img.file_id || img.image_url, 'large'));
        } else {
            imageSources = [API.getImageUrl(product.image_file_id || product.image_url || product.image, 'large')];
        }

        if (hasMultipleImages) {
            imagesHtml = `
                <div class="product-images-container">
                    <div class="product-images-slider">
                        ${imageSources.map(src => `
                            <img class="product-detail-image" src="${src}" alt="${product.name}" loading="lazy">
                        `).join('')}
                    </div>
                    <div class="slider-dots">
                        ${imageSources.map((_, i) => `<div class="slider-dot ${i === 0 ? 'active' : ''}"></div>`).join('')}
                    </div>
                </div>
            `;
        } else {
            imagesHtml = `
                <div class="product-images-container">
                    <img class="product-detail-image" src="${imageSources[0]}" alt="${product.name}" onerror="this.src='assets/placeholder.svg'">
                </div>
             `;
        }

        const detail = document.getElementById('modalProductDetail');
        detail.innerHTML = `
            ${imagesHtml}
            <div class="product-detail-content">
                <h1 class="product-detail-name">${product.name}</h1>
                ${product.description ? `<p class="product-detail-description">${product.description}</p>` : ''}
                <div class="product-detail-pack">Пачка: ${product.pieces_per_pack} шт</div>
                
                <div class="quantity-selector" data-product='${JSON.stringify(product)}'>
                    <button class="quantity-btn" data-action="decrease">−</button>
                    <div class="quantity-display">
                        <div class="quantity-packs"><span id="qtyPacks">1</span> пачка</div>
                        <div class="quantity-pieces"><span id="qtyPieces">${product.pieces_per_pack}</span> шт</div>
                        <div class="quantity-total"><span id="qtyTotal">${this.formatPrice(product.price_per_unit * product.pieces_per_pack)}</span>₽</div>
                    </div>
                    <button class="quantity-btn" data-action="increase">+</button>
                </div>
                
                <div class="product-detail-price-row">
                    <div class="product-detail-price">${this.formatPrice(product.price_per_unit)}<span class="currency">₽</span></div>
                </div>
                
                <button class="btn btn-primary btn-block" id="addToCartBtn">Добавить в корзину</button>
            </div>
        `;

        // Slider logic
        if (hasMultipleImages) {
            const slider = detail.querySelector('.product-images-slider');
            slider.addEventListener('scroll', () => {
                const index = Math.round(slider.scrollLeft / slider.offsetWidth);
                detail.querySelectorAll('.slider-dot').forEach((dot, i) => {
                    dot.classList.toggle('active', i === index);
                });
            });
        }

        // Quantity controls
        let quantity = 1;
        const updateQuantity = () => {
            document.getElementById('qtyPacks').textContent = quantity;
            document.getElementById('qtyPieces').textContent = quantity * product.pieces_per_pack;
            document.getElementById('qtyTotal').textContent = this.formatPrice(product.price_per_unit * product.pieces_per_pack * quantity);
            detail.querySelector('[data-action="decrease"]').disabled = quantity <= (product.min_order_packs || 1);
        };

        detail.querySelector('[data-action="decrease"]').addEventListener('click', () => {
            if (quantity > (product.min_order_packs || 1)) {
                quantity--;
                updateQuantity();
            }
        });

        detail.querySelector('[data-action="increase"]').addEventListener('click', () => {
            quantity++;
            updateQuantity();
        });

        // Add to cart
        document.getElementById('addToCartBtn').addEventListener('click', () => {
            Cart.addProduct(product, quantity);
            App.updateCartBadge();
            App.closeModal();
            this.refreshCardControls(product.id);
        });
    },

    /**
     * Show skeleton loading
     */
    showSkeletonLoading() {
        const grid = document.getElementById('productsGrid');
        const skeletonCount = this.itemsPerPage;

        let html = '';
        for (let i = 0; i < skeletonCount; i++) {
            html += `
                <div class="product-card skeleton-card">
                    <div class="product-image skeleton"></div>
                    <div class="product-info">
                        <div class="product-name skeleton-text"></div>
                        <div class="product-price skeleton-text short"></div>
                        <div class="product-pack skeleton-text short"></div>
                    </div>
                </div>
            `;
        }
        grid.innerHTML = html;
    },

    /**
     * Get product packs in cart
     */
    getProductQtyInCart(productId) {
        const item = Cart.items.find(item => item.product.id === productId);
        return item ? item.packs : 0;
    },

    /**
     * Format price
     */
    formatPrice(price) {
        if (!price) return '0';
        return Math.round(price * 100) / 100;
    }
};

// Make it global
window.Catalog = Catalog;
