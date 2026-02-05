/**
 * Cart management module
 */
const Cart = {
    items: [],
    storageKey: 'shop_cart',

    /**
     * Initialize cart from localStorage
     */
    init() {
        try {
            const saved = localStorage.getItem(this.storageKey);
            if (saved) {
                this.items = JSON.parse(saved);
            }
        } catch (e) {
            console.error('Failed to load cart:', e);
            this.items = [];
        }
        this.updateBadge();
    },

    /**
     * Save cart to localStorage
     */
    save() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.items));
        } catch (e) {
            console.error('Failed to save cart:', e);
        }
        this.updateBadge();
    },

    /**
     * Add product to cart
     */
    addProduct(product, packs = 1) {
        const existingIndex = this.items.findIndex(item => item.product.id === product.id);

        if (existingIndex >= 0) {
            this.items[existingIndex].packs += packs;
        } else {
            this.items.push({
                product: product,
                packs: packs
            });
        }

        this.save();
        App.showToast(`✅ ${product.name} добавлен в корзину`);
    },

    /**
     * Update item quantity
     */
    updateQuantity(productId, packs) {
        const item = this.items.find(item => item.product.id === productId);
        if (item) {
            item.packs = Math.max(1, packs);
            this.save();
        }
    },

    /**
     * Remove item from cart
     */
    removeItem(productId) {
        this.items = this.items.filter(item => item.product.id !== productId);
        this.save();
    },

    /**
     * Clear cart
     */
    clear() {
        this.items = [];
        this.save();
    },

    /**
     * Get cart items for API
     */
    getApiItems() {
        return this.items.map(item => ({
            product_id: item.product.id,
            quantity_packs: item.packs
        }));
    },

    /**
     * Calculate total
     */
    getTotal() {
        return this.items.reduce((sum, item) => {
            const pieces = item.packs * item.product.pieces_per_pack;
            return sum + (pieces * item.product.price_per_unit);
        }, 0);
    },

    /**
     * Get total items count
     */
    getItemsCount() {
        return this.items.reduce((sum, item) => sum + item.packs, 0);
    },

    /**
     * Update cart badge
     */
    updateBadge() {
        const badge = document.getElementById('cartBadge');
        if (!badge) return;
        const count = this.getItemsCount();

        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    },

    /**
     * Render cart view
     */
    render() {
        const cartItems = document.getElementById('cartItems');
        const cartEmpty = document.getElementById('cartEmpty');
        const cartFooter = document.getElementById('cartFooter');
        const cartTotal = document.getElementById('cartTotal');

        if (this.items.length === 0) {
            cartItems.innerHTML = '';
            cartEmpty.style.display = 'block';
            cartFooter.style.display = 'none';
            return;
        }

        cartEmpty.style.display = 'none';
        cartFooter.style.display = 'block';

        cartItems.innerHTML = this.items.map(item => {
            const pieces = item.packs * item.product.pieces_per_pack;
            const subtotal = pieces * item.product.price_per_unit;

            return `
                <div class="cart-item" data-product-id="${item.product.id}">
                    <img class="cart-item-image" 
                         src="${API.getImageUrl(item.product)}" 
                         alt="${item.product.name}"
                         loading="lazy">
                    <div class="cart-item-info">
                        <div class="cart-item-name">${item.product.name}</div>
                        <div class="cart-item-details">
                            ${item.packs} пач. (${pieces} шт) × ${item.product.price_per_unit}₽
                        </div>
                        <div class="cart-item-controls">
                            <button class="cart-qty-btn" 
                                    onclick="Cart.updateQuantity(${item.product.id}, ${item.packs - 1}); Cart.render();"
                                    ${item.packs <= 1 ? 'disabled' : ''}>−</button>
                            <span class="cart-item-qty">${item.packs}</span>
                            <button class="cart-qty-btn" 
                                    onclick="Cart.updateQuantity(${item.product.id}, ${item.packs + 1}); Cart.render();">+</button>
                            <span class="cart-item-price">${subtotal.toFixed(0)}₽</span>
                            <button class="cart-item-remove" 
                                    onclick="Cart.removeItem(${item.product.id}); Cart.render();">🗑</button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        cartTotal.textContent = `${this.getTotal().toFixed(0)}₽`;
    },

    /**
     * Render checkout summary
     */
    renderCheckoutSummary() {
        const summary = document.getElementById('checkoutSummary');

        let html = this.items.map(item => {
            const pieces = item.packs * item.product.pieces_per_pack;
            const subtotal = pieces * item.product.price_per_unit;

            return `
                <div class="checkout-summary-item">
                    <span>${item.product.name} × ${item.packs} пач.</span>
                    <span>${subtotal.toFixed(0)}₽</span>
                </div>
            `;
        }).join('');

        html += `
            <div class="checkout-summary-total">
                <span>Итого:</span>
                <span>${this.getTotal().toFixed(0)}₽</span>
            </div>
        `;

        summary.innerHTML = html;
    }
};

// Export
window.Cart = Cart;
