const Admin = {
    userId: null,
    isAdmin: false,
    categories: [],
    products: [],
    currentCategoryId: null,
    editingProductId: null,
    editingCategoryId: null,

    async init() {
        // Init Telegram
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand(); // Use full screen
            const user = window.Telegram.WebApp.initDataUnsafe.user;
            if (user) {
                this.userId = user.id;
                document.getElementById('adminUserInfo').textContent = `${user.first_name} (ID: ${user.id})`;
                await this.checkAuth();
            } else {
                document.getElementById('adminUserInfo').textContent = 'Dev Mode';
            }
        }

        this.setupTabs();
        this.setupUpload();

        if (this.isAdmin || !window.Telegram.WebApp.initData) {
            this.loadCategories();
            this.loadProducts(); // Preload for search
        }
    },

    async checkAuth() {
        if (!this.userId) return;
        try {
            const response = await fetch(`${API.baseUrl}/admin/check`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: this.userId })
            });

            if (response.ok) {
                this.isAdmin = true;
                document.getElementById('authView').style.display = 'none';
                document.getElementById('categoriesTab').style.display = 'block';
            } else {
                this.authFailed();
            }
        } catch (e) {
            console.error("Auth check failed", e);
            // this.authFailed(); // Uncomment for strict prod
            // For Demo/Dev we allow:
            this.isAdmin = true;
        }
    },

    authFailed() {
        this.isAdmin = false;
        document.getElementById('authView').style.display = 'block';
        document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
        document.querySelector('.admin-nav').style.display = 'none';
    },

    setupTabs() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');

                btn.classList.add('active');
                const tabId = btn.dataset.tab + 'Tab';
                document.getElementById(tabId).style.display = 'block';

                if (btn.dataset.tab === 'categories') this.loadCategories();
                if (btn.dataset.tab === 'products') this.loadProducts();
            });
        });
    },

    // --- Categories ---

    async loadCategories() {
        this.currentCategoryId = null; // Reset drill down
        document.getElementById('categoryProductsSection').style.display = 'none';
        document.getElementById('breadcrumbs').style.display = 'none';

        try {
            const data = await API.getCategories();
            this.categories = data.categories || [];
            this.renderCategories(this.categories);
        } catch (e) {
            console.error(e);
        }
    },

    renderCategories(categories) {
        const list = document.getElementById('categoriesList');
        list.innerHTML = categories.map(c => `
            <div class="category-card" onclick="Admin.openCategory(${c.id})">
                <div class="category-name">${c.name}</div>
                <div class="category-info" style="font-size:12px; color:#888;">
                    ${c.subcategories ? c.subcategories.length : 0} подкат.
                </div>
                <div class="category-actions" onclick="event.stopPropagation()">
                    <button class="btn-icon" onclick="Admin.openCategoryModal(${c.id})">✏️</button>
                    <button class="btn-icon" style="color:red;" onclick="Admin.deleteCategory(${c.id})">🗑</button>
                </div>
            </div>
        `).join('');
    },

    openCategory(catId) {
        this.currentCategoryId = catId;
        const category = this.categories.find(c => c.id === catId);
        if (!category) return;

        // Update Breadcrumbs
        document.getElementById('breadcrumbs').style.display = 'block';
        document.getElementById('breadcrumbCurrent').textContent = ` > ${category.name}`;

        // Hide top level categories list (simulating drill down)
        document.getElementById('categoriesList').innerHTML = ''; // Clear or hide?
        // Actually better to just show products of this category and subcategories

        // Show subcategories if any
        if (category.subcategories && category.subcategories.length > 0) {
            document.getElementById('categoriesList').innerHTML = category.subcategories.map(s => `
                <div class="category-card">
                    <div class="category-name">${s.name}</div>
                    <div class="category-actions">
                        <button class="btn-icon">✏️</button>
                        <button class="btn-icon" style="color:red;" onclick="Admin.deleteSubcategory(${s.id})">🗑</button>
                    </div>
                </div>
            `).join('') + `
            <div class="category-card" style="border-style:dashed; opacity:0.7;" onclick="Admin.openSubcategoryModal(${catId})">
                <div class="category-name" style="margin:auto;">+ Подкатегория</div>
            </div>`;
        } else {
            document.getElementById('categoriesList').innerHTML = `
             <div class="category-card" style="border-style:dashed; opacity:0.75; min-height:80px;" onclick="Admin.openSubcategoryModal(${catId})">
                <div class="category-name" style="margin:auto;">+ Добавить подкатегорию</div>
            </div>`;
        }

        // Show Products in this category
        document.getElementById('categoryProductsSection').style.display = 'block';
        this.loadCategoryProducts(catId);
    },

    async loadCategoryProducts(catId) {
        try {
            const data = await API.getProducts({ category: catId, limit: 100 });
            const products = data.items || [];
            const tbody = document.getElementById('categoryProductsBody');

            if (products.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">Товаров нет</td></tr>';
                return;
            }

            tbody.innerHTML = products.map(p => this.renderProductRow(p)).join('');
        } catch (e) {
            console.error(e);
        }
    },

    // --- Products ---

    async loadProducts() {
        try {
            const data = await API.getProducts({ limit: 100 });
            this.products = data.items || [];
            this.renderProductsTable(this.products);
        } catch (e) {
            console.error(e);
        }
    },

    renderProductsTable(products) {
        const tbody = document.getElementById('productsTableBody');
        tbody.innerHTML = products.map(p => this.renderProductRow(p)).join('');
    },

    renderProductRow(p) {
        return `
            <tr>
                <td><img src="${API.getImageUrl(p.image, 'small')}" onerror="this.src='assets/placeholder.svg'"></td>
                <td>
                    <div style="font-weight:600;">${p.name}</div>
                    <div style="font-size:12px; color:#888;">Цена: ${p.price_per_unit}₽</div>
                </td>
                <td>${p.sku || '-'}</td>
                <td>
                    <button class="btn-icon" onclick="Admin.openProductModal(${p.id})">✏️</button>
                    <button class="btn-icon" style="color:red;" onclick="Admin.deleteProduct(${p.id})">🗑</button>
                </td>
            </tr>
        `;
    },

    searchProducts(query) {
        if (!query) {
            this.renderProductsTable(this.products);
            return;
        }
        const lower = query.toLowerCase();
        const filtered = this.products.filter(p => p.name.toLowerCase().includes(lower));
        this.renderProductsTable(filtered);
    },

    // --- Modals & Saving ---

    openCategoryModal(catId = null) {
        this.editingCategoryId = catId;
        document.getElementById('catModalTitle').textContent = catId ? 'Изменить категорию' : 'Создать категорию';
        document.getElementById('catNameInput').value = '';

        if (catId) {
            const cat = this.categories.find(c => c.id === catId);
            if (cat) document.getElementById('catNameInput').value = cat.name;
        }

        document.getElementById('categoryModal').classList.add('active');
    },

    async saveCategory() {
        const name = document.getElementById('catNameInput').value;
        if (!name) return alert('Введите название');

        try {
            if (this.editingCategoryId) {
                // Update
                await fetch(`${API.baseUrl}/categories/${this.editingCategoryId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name })
                });
            } else {
                // Create
                await fetch(`${API.baseUrl}/categories`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name })
                });
            }
            this.closeModal('categoryModal');
            this.loadCategories(); // Refresh
        } catch (e) {
            alert('Ошибка при сохранении: ' + e);
        }
    },

    async openProductModal(prodId = null, preselectCatId = null) {
        this.editingProductId = prodId;
        document.getElementById('prodModalTitle').textContent = prodId ? 'Редактировать товар' : 'Новый товар';

        // Reset form
        document.getElementById('prodName').value = '';
        document.getElementById('prodPrice').value = '';
        document.getElementById('prodPack').value = '1';
        document.getElementById('prodStock').value = '';
        document.getElementById('prodSku').value = '';
        document.getElementById('prodCountry').value = '';
        document.getElementById('prodDesc').value = '';

        // Load categories into select
        const catSelect = document.getElementById('prodCategory');
        catSelect.innerHTML = '<option value="">Выберите категорию</option>';
        this.categories.forEach(c => {
            catSelect.innerHTML += `<option value="${c.id}">${c.name}</option>`;
        });

        if (preselectCatId) {
            catSelect.value = preselectCatId;
            this.onCategoryChange(); // Load subcats
        }

        if (prodId) {
            // Load detail
            const p = await API.getProduct(prodId);
            document.getElementById('prodName').value = p.name;
            document.getElementById('prodPrice').value = p.price_per_unit;
            document.getElementById('prodPack').value = p.pieces_per_pack;
            if (p.in_stock !== null) document.getElementById('prodStock').value = p.in_stock;
            if (p.sku) document.getElementById('prodSku').value = p.sku;
            if (p.country) document.getElementById('prodCountry').value = p.country;
            if (p.description) document.getElementById('prodDesc').value = p.description;

            catSelect.value = p.category_id;
            this.onCategoryChange();
            if (p.subcategory_id) {
                document.getElementById('prodSubcategory').value = p.subcategory_id;
            }
        }

        document.getElementById('productModal').classList.add('active');
    },

    onCategoryChange() {
        const catId = parseInt(document.getElementById('prodCategory').value);
        const subSelect = document.getElementById('prodSubcategory');
        subSelect.innerHTML = '<option value="">(Нет)</option>';

        const cat = this.categories.find(c => c.id === catId);
        if (cat && cat.subcategories) {
            cat.subcategories.forEach(s => {
                subSelect.innerHTML += `<option value="${s.id}">${s.name}</option>`;
            });
        }
    },

    async saveProduct() {
        const data = {
            name: document.getElementById('prodName').value,
            category_id: parseInt(document.getElementById('prodCategory').value),
            subcategory_id: document.getElementById('prodSubcategory').value ? parseInt(document.getElementById('prodSubcategory').value) : null,
            price_per_unit: parseFloat(document.getElementById('prodPrice').value),
            pieces_per_pack: parseInt(document.getElementById('prodPack').value) || 1,
            in_stock: document.getElementById('prodStock').value ? parseInt(document.getElementById('prodStock').value) : null,
            sku: document.getElementById('prodSku').value,
            country: document.getElementById('prodCountry').value,
            description: document.getElementById('prodDesc').value
        };

        if (!data.name || !data.category_id || isNaN(data.price_per_unit)) {
            return alert('Заполните обязательные поля (Название, Категория, Цена)');
        }

        try {
            if (this.editingProductId) {
                await fetch(`${API.baseUrl}/products/${this.editingProductId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            } else {
                await fetch(`${API.baseUrl}/products`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            }
            this.closeModal('productModal');
            if (this.currentCategoryId) this.loadCategoryProducts(this.currentCategoryId);
            this.loadProducts(); // refresh all list too
            alert('Сохранено!');
        } catch (e) {
            alert('Ошибка: ' + e);
        }
    },

    async deleteProduct(id) {
        if (!confirm('Удалить?')) return;
        await fetch(`${API.baseUrl}/products/${id}`, { method: 'DELETE' });
        if (this.currentCategoryId) this.loadCategoryProducts(this.currentCategoryId);
        this.loadProducts();
    },

    async deleteCategory(id) {
        if (!confirm('Удалить категорию?')) return;
        await fetch(`${API.baseUrl}/categories/${id}`, { method: 'DELETE' });
        this.loadCategories();
    },

    closeModal(id) {
        document.getElementById(id).classList.remove('active');
    },

    // --- Upload ---
    setupUpload() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');

        dropZone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) this.handleFile(e.target.files[0]);
        });
    },

    async handleFile(file) {
        const status = document.getElementById('uploadStatus');
        status.textContent = 'Загрузка...';
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API.baseUrl}/products/import`, { method: 'POST', body: formData });
            const res = await response.json();
            status.textContent = res.message || 'Готово';
        } catch (e) {
            status.textContent = 'Ошибка: ' + e;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => Admin.init());
