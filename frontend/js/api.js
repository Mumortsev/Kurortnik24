/**
 * API Client for Telegram Mini App Store
 */
const API = {
    // Base URL - change to your server
    baseUrl: window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : '/api',

    /**
     * Make API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;

        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * Get all categories with subcategories
     */
    async getCategories() {
        return this.request('/api/categories');
    },

    /**
     * Get products with filters and pagination
     */
    async getProducts({
        category = null,
        subcategory = null,
        search = '',
        sort = 'newest',
        page = 1,
        limit = 12
    } = {}) {
        const params = new URLSearchParams();
        if (category) params.append('category', category);
        if (subcategory) params.append('subcategory', subcategory);
        if (search) params.append('q', search);
        params.append('sort', sort);
        params.append('page', page);
        params.append('limit', limit);

        return this.request(`/api/products?${params.toString()}`);
    },

    /**
     * Get single product
     */
    async getProduct(id) {
        return this.request(`/api/products/${id}`);
    },

    /**
     * Validate cart before checkout
     */
    async validateCart(items) {
        return this.request('/api/cart/validate', {
            method: 'POST',
            body: JSON.stringify({ items })
        });
    },

    /**
     * Create order
     */
    async createOrder(orderData) {
        return this.request('/api/orders', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    },

    /**
     * Get user orders
     */
    async getOrders(telegramId = null) {
        const params = telegramId ? `?telegram_id=${telegramId}` : '';
        return this.request(`/api/orders${params}`);
    },

    /**
     * Get image URL from file_id
     */
    getImageUrl(fileIdOrUrl, size = 'medium') {
        if (!fileIdOrUrl) return 'assets/placeholder.svg';

        // If it's already a URL
        if (fileIdOrUrl.startsWith('http')) {
            return fileIdOrUrl;
        }

        // If it's a file path
        if (fileIdOrUrl.startsWith('/') || fileIdOrUrl.startsWith('assets/')) {
            return fileIdOrUrl;
        }

        // Telegram file_id - get via API proxy
        return `${this.baseUrl}/api/images/${fileIdOrUrl}?size=${size}`;
    }
};

// Make it globally available
window.API = API;
