const Admin = {
    userId: null,
    isAdmin: false,

    async init() {
        // Get user from Telegram WebApp
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.ready();
            const user = window.Telegram.WebApp.initDataUnsafe.user;
            if (user) {
                this.userId = user.id;
                document.getElementById('adminUserInfo').textContent = `${user.first_name} (ID: ${user.id})`;
                await this.checkAuth();
            } else {
                // Dev mode fallback or non-telegram environment
                document.getElementById('adminUserInfo').textContent = 'Dev Mode';
            }
        }

        this.setupTabs();
        this.setupUpload();

        // Always try to load products if we passed checkAuth or in dev
        // In real prod, checkAuth would block this.
        if (this.isAdmin || !window.Telegram.WebApp.initData) {
            // Allow loading in browser for testing if no telegram data
            this.loadProducts();
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
                document.getElementById('productsTab').style.display = 'block';
            } else {
                this.isAdmin = false;
                document.getElementById('authView').style.display = 'block';
                document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
                document.querySelector('.admin-nav').style.display = 'none';
            }
        } catch (e) {
            console.error("Auth check failed", e);
            // Fallback for demo: assume admin if fetch fails (e.g. CORS on localhost)
            // this.isAdmin = true; 
        }
    },

    setupTabs() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');

                btn.classList.add('active');
                document.getElementById(`${btn.dataset.tab}Tab`).style.display = 'block';
            });
        });
    },

    async loadProducts() {
        try {
            const data = await API.getProducts({ limit: 100 });
            const products = data.items || [];
            const tbody = document.getElementById('productsTableBody');

            tbody.innerHTML = products.map(p => `
                <tr>
                    <td>${p.id}</td>
                    <td><img src="${API.getImageUrl(p.image, 'small')}" onerror="this.src='assets/placeholder.svg'"></td>
                    <td>${p.name}</td>
                    <td>${p.price_per_unit}₽</td>
                    <td>${p.pieces_per_pack}</td>
                    <td>${p.in_stock || '∞'}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="Admin.deleteProduct(${p.id})">Del</button>
                    </td>
                </tr>
            `).join('');
        } catch (e) {
            console.error("Failed to load products", e);
        }
    },

    async deleteProduct(id) {
        if (!confirm('Удалить товар?')) return;

        try {
            await fetch(`${API.baseUrl}/products/${id}`, {
                method: 'DELETE'
            });
            this.loadProducts();
        } catch (e) {
            alert('Ошибка удаления');
        }
    },

    setupUpload() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');

        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                this.handleFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                this.handleFile(e.target.files[0]);
            }
        });
    },

    async handleFile(file) {
        const status = document.getElementById('uploadStatus');
        status.textContent = 'Загрузка...';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API.baseUrl}/products/import`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            status.textContent = result.message || 'Готово';
            this.loadProducts();
        } catch (e) {
            status.textContent = 'Ошибка загрузки: ' + e.message;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => Admin.init());
