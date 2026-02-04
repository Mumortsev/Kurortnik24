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
    sortBy: 'name_asc',
    products: [],
    localQuantities: {}, // Track local selection for cards

    // Config
    itemsPerPage: 12,

    /**
     * Initialize catalog
     */
    async init() {
        await this.loadCategories();
        this.setupEventListeners();
        this.setupMenu();
        await this.loadProducts(true);
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Search
        const searchInput = document.getElementById('searchInput');
        const searchClear = document.getElementById('searchClear');

        // Debounce utility
        const debounce = (func, wait) => {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        };

        // Search execution function
        const performSearch = () => {
            if (!searchInput) return;
            const query = searchInput.value.trim();
            this.searchQuery = query;
            this.loadProducts(true);
        };

        // Debounced search
        const debouncedSearch = debounce(() => performSearch(), 400);

        // Input handler - Real-time search
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value;
                if (searchClear) searchClear.style.display = query ? 'flex' : 'none';
                debouncedSearch();
            });
        }

        if (searchClear && searchInput) {
            searchClear.addEventListener('click', () => {
                searchInput.value = '';
                searchClear.style.display = 'none';
                this.searchQuery = '';
                this.loadProducts(true);
                searchInput.focus();
            });
        }

        // Sort
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortBy = e.target.value;
                this.loadProducts(true);
            });
        }

        // Infinite scroll
        window.addEventListener('scroll', () => {
            if (this.isLoading || !this.hasMore) return;

            const scrollTop = window.scrollY || document.documentElement.scrollTop;
            const scrollHeight = document.documentElement.scrollHeight;
            const clientHeight = window.innerHeight;

            // Load more when user is near bottom (300px buffer)
            if (scrollTop + clientHeight >= scrollHeight - 300) {
                this.loadMoreProducts();
            }
        }, { passive: true });

        // Load More Button (Manual Fallback)
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => {
                this.loadMoreProducts();
            });
        }
    },

    /**
     * Setup menu event listeners
     */
    setupMenu() {
        const closeBtn = document.getElementById('menuCloseBtn');
        const backBtn = document.getElementById('menuBackBtn');

        if (closeBtn) closeBtn.addEventListener('click', () => this.closeMenu());
        if (backBtn) backBtn.addEventListener('click', () => this.showMenuCategories());
    },

    /**
     * Open Catalog Menu
     */
    openMenu() {
        const menu = document.getElementById('catalogMenuModal');
        menu.classList.add('active');
        this.showMenuCategories();
        document.body.style.overflow = 'hidden';
    },

    /**
     * Close Catalog Menu
     */
    closeMenu() {
        const menu = document.getElementById('catalogMenuModal');
        menu.classList.remove('active');
        document.body.style.overflow = '';
    },

    /**
     * Show main categories in menu
     */
    showMenuCategories() {
        console.log('Rendering menu categories. Count:', this.categories.length);
        const title = document.getElementById('menuTitle');
        const backBtn = document.getElementById('menuBackBtn');
        const container = document.getElementById('catalogMenuContent');

        title.textContent = 'Каталог';
        backBtn.style.display = 'none';

        let html = `
            <div class="catalog-menu-item" onclick="Catalog.handleMenuSelection(null, null)">
                <span class="catalog-menu-item-text">Все товары</span>
                <span class="catalog-menu-item-icon">→</span>
            </div>
        `;

        if (!this.categories || this.categories.length === 0) {
            html += `<div style="padding: 20px; text-align: center; color: #999;">Нет категорий</div>`;
        } else {
            this.categories.forEach(cat => {
                const hasSub = cat.subcategories && cat.subcategories.length > 0;
                const clickAction = hasSub ?
                    `Catalog.showMenuSubcategories(${cat.id})` :
                    `Catalog.handleMenuSelection(${cat.id}, null)`;

                html += `
                    <div class="catalog-menu-item" onclick="${clickAction}">
                        <span class="catalog-menu-item-text">${cat.name}</span>
                        <span class="catalog-menu-item-icon">${hasSub ? '→' : ''}</span>
                    </div>
                `;
            });
        }

        container.innerHTML = html;
    },

    /**
     * Show subcategories for a category
     */
    showMenuSubcategories(categoryId) {
        const category = this.categories.find(c => c.id === categoryId);
        if (!category) return;

        const title = document.getElementById('menuTitle');
        const backBtn = document.getElementById('menuBackBtn');
        const container = document.getElementById('catalogMenuContent');

        title.textContent = category.name;
        backBtn.style.display = 'flex';

        let html = `
            <div class="catalog-menu-item" onclick="Catalog.handleMenuSelection(${category.id}, null)">
                <span class="catalog-menu-item-text">Все в категории "${category.name}"</span>
                <span class="catalog-menu-item-icon">→</span>
            </div>
        `;

        category.subcategories.forEach(sub => {
            if (sub.name === 'Все') return;
            html += `
                <div class="catalog-menu-item" onclick="Catalog.handleMenuSelection(${category.id}, ${sub.id})">
                    <span class="catalog-menu-item-text">${sub.name}</span>
                </div>
            `;
        });

        container.innerHTML = html;
    },

    /**
     * Handle selection from menu
     */
    handleMenuSelection(categoryId, subcategoryId) {
        this.closeMenu();
        App.showCatalog(); // Ensure we are on listing page

        if (categoryId === null) {
            // "All Products"
            this.selectCategory(null);
        } else if (subcategoryId === null) {
            // "All in Category"
            this.selectCategory(categoryId);
        } else {
            // Specific subcategory
            this.selectCategory(categoryId); // This renders subcat chips
            setTimeout(() => {
                this.selectSubcategory(subcategoryId); // This selects specific chip and reloads
            }, 50);
        }
    },

    /**
     * Load categories
     */
    async loadCategories() {
        try {
            console.log('Loading categories...');
            const data = await API.getCategories();
            console.log('Categories API response:', data);

            this.categories = data.categories || data || [];
            console.log('Parsed categories:', this.categories);

            // Debug output to screen if debug console exists
            const debugEl = document.getElementById('debug-console');
            if (debugEl) {
                debugEl.innerHTML += `Cats loaded: ${this.categories.length}<br>`;
            }

            this.renderCategories();
        } catch (error) {
            console.error('Failed to load categories:', error);
            const debugEl = document.getElementById('debug-console');
            if (debugEl) {
                debugEl.innerHTML += `Err loading cats: ${error.message}<br>`;
            }
            this.categories = [];
        }
    },

    /**
     * Render categories
     */
    /**
     * Render categories - Only for internal state, logic moved to Menu
     */
    renderCategories() {
        // Legacy chip rendering removed
    },

    /**
     * Select category
     */
    selectCategory(categoryId) {
        const id = categoryId ? parseInt(categoryId) : null;
        this.currentCategory = id;
        this.currentSubcategory = null;
        this.loadProducts(true);
    },

    /**
     * Format price
     */
    formatPrice(price) {
        if (!price) return '0';
        return Math.round(price * 100) / 100;
    },

    /**
     * Select subcategory
     */
    selectSubcategory(subcategoryId) {
        const id = subcategoryId ? parseInt(subcategoryId) : null;
        this.currentSubcategory = id;
        this.loadProducts(true);
    },

    /**
     * Update header height - No longer needed
     */
    updateHeaderHeight() {
        // No-op
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

            // Update Load More Button visibility
            const loadMoreBtn = document.getElementById('loadMoreBtn');
            if (loadMoreBtn) {
                loadMoreBtn.style.display = this.hasMore ? 'block' : 'none';
            }
        }
    },

    /**
     * Load more products
     */
    loadMoreProducts() {
        if (!this.hasMore) return;
        if (this.isLoading) return;

        console.log('Loading more products page:', this.currentPage + 1);
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
                <div class="product-image-wrapper">
                    <img 
                        class="product-image skeleton" 
                        src="${API.getImageUrl(product.images?.[0]?.file_id || product.images?.[0]?.image_url || product.image_file_id || product.image_url, 'small')}"
                        alt="${product.name}"
                        onload="this.classList.remove('skeleton'); this.classList.add('loaded');"
                        onerror="this.onerror=null; this.classList.remove('skeleton'); this.classList.add('loaded'); this.src='assets/placeholder.svg'"
                    >
                    <!-- Cart Button on Image (Bottom Right) -->
                    <button class="card-add-btn" onclick="Catalog.addToCartFromCard(${product.id}); event.stopPropagation();">
                         <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 22C9.55228 22 10 21.5523 10 21C10 20.4477 9.55228 20 9 20C8.44772 20 8 20.4477 8 21C8 21.5523 8.44772 22 9 22Z" />
                            <path d="M20 22C20.5523 22 21 21.5523 21 21C21 20.4477 20.5523 20 20 20C19.4477 20 19 20.4477 19 21C19 21.5523 19.4477 22 20 22Z" />
                            <path d="M1 1H5L7.68 14.39C7.77 14.83 8.02 15.22 8.38 15.5C8.74 15.78 9.19 15.92 9.64 15.9H19.36C19.81 15.92 20.26 15.78 20.62 15.5C20.98 15.22 21.23 14.83 21.32 14.39L23 6H6" />
                        </svg>
                    </button>
                </div>
                
                <div class="product-info">
                    <div class="product-name">${product.name}</div>
                    <div class="product-pack">${product.pieces_per_pack} шт/пач</div>
                    
                    <div class="product-footer">
                        <div class="product-price">${this.formatPrice(product.price_per_unit)}<span class="currency">₽</span></div>
                        
                        <!-- Quantity Controls (Right) -->
                        <div class="card-qty-controls" onclick="event.stopPropagation();">
                            <button class="card-qty-btn" onclick="Catalog.adjustLocalQty(${product.id}, -1)">−</button>
                            <span class="card-qty" id="grid-qty-${product.id}">${this.localQuantities[product.id] || 1}</span>
                            <button class="card-qty-btn" onclick="Catalog.adjustLocalQty(${product.id}, 1)">+</button>
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

        // Check if we need to load more to fill the screen
        if (this.hasMore && !this.isLoading) {
            const scrollHeight = document.documentElement.scrollHeight;
            const clientHeight = window.innerHeight;
            if (scrollHeight <= clientHeight + 100) {
                setTimeout(() => this.loadMoreProducts(), 100);
            }
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
     * Add to cart from card (using local selection)
     */
    addToCartFromCard(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;

        const qtyToAdd = this.localQuantities[productId] || 1;

        Cart.addProduct(product, qtyToAdd);
        App.updateCartBadge();

        // Optional: Reset local counter to 1 for visual feedback? 
        this.localQuantities[productId] = 1;
        this.refreshCardControls(productId);
    },

    /**
     * Adjust local quantity on card
     */
    adjustLocalQty(productId, delta) {
        if (!this.localQuantities[productId]) {
            this.localQuantities[productId] = 1;
        }

        const current = this.localQuantities[productId];
        const product = this.products.find(p => p.id === productId);
        const min = product?.min_order_packs || 1;

        let newQty = current + delta;
        if (newQty < min) newQty = min;

        this.localQuantities[productId] = newQty;
        this.refreshCardControls(productId);
    },

    /**
     * Refresh card controls
     */
    refreshCardControls(productId) {
        const qtyDisplay = document.getElementById(`grid-qty-${productId}`);
        if (qtyDisplay) {
            qtyDisplay.textContent = this.localQuantities[productId] || 1;
        }
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
