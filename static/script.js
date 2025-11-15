document.addEventListener('DOMContentLoaded', () => {
    // URLs for API endpoints
    const API_URL = '/api';
    const PRODUCTS_URL = `${API_URL}/products`;
    const SALES_URL = `${API_URL}/sales`;

    // Product elements
    const productList = document.getElementById('product-list');
    const productSearch = document.getElementById('product-search');
    const addProductBtn = document.getElementById('add-product-btn');

    // Sale elements
    const salesList = document.getElementById('sales-list');
    const dateFrom = document.getElementById('date-from');
    const dateTo = document.getElementById('date-to');
    const filterSalesBtn = document.getElementById('filter-sales-btn');
    const resetFilterBtn = document.getElementById('reset-filter-btn');
    const addSaleBtn = document.getElementById('add-sale-btn');

    // Modal elements
    const modalBackdrop = document.getElementById('modal-backdrop');
    const productModal = document.getElementById('product-modal');
    const saleModal = document.getElementById('sale-modal');
    const productForm = document.getElementById('product-form');
    const saleForm = document.getElementById('sale-form');
    const cancelButtons = document.querySelectorAll('.cancel-btn');

    // Product form fields
    const productIdField = document.getElementById('product-id');
    const productNameField = document.getElementById('product-name');
    const productPriceField = document.getElementById('product-price');

    // Sale form fields
    const saleProductSelect = document.getElementById('sale-product');
    const saleQuantityField = document.getElementById('sale-quantity');

    // --- UTILITY FUNCTIONS ---
    const showModal = (modal) => {
        modalBackdrop.classList.remove('hidden');
        modal.classList.remove('hidden');
    };

    const hideModals = () => {
        modalBackdrop.classList.add('hidden');
        productModal.classList.add('hidden');
        saleModal.classList.add('hidden');
    };

    // --- API FUNCTIONS ---
    const fetchProducts = async (query = '') => {
        try {
            const url = query ? `${PRODUCTS_URL}?q=${query}` : PRODUCTS_URL;
            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to fetch products');
            const products = await response.json();
            renderProducts(products);
            updateSaleProductOptions(products);
        } catch (error) {
            console.error('Error fetching products:', error);
        }
    };

    const fetchSales = async (from = '', to = '') => {
        try {
            const params = new URLSearchParams();
            if (from) params.append('date_from', from);
            if (to) params.append('date_to', to);
            const response = await fetch(`${SALES_URL}?${params.toString()}`);
            if (!response.ok) throw new Error('Failed to fetch sales');
            const sales = await response.json();
            renderSales(sales);
        } catch (error) {
            console.error('Error fetching sales:', error);
        }
    };

    // --- RENDER FUNCTIONS ---
    const renderProducts = (products) => {
        productList.innerHTML = '';
        products.forEach(product => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span>${product.name} - ${product.price} руб.</span>
                <div>
                    <button class="edit-product-btn" data-id="${product.id}">✏️</button>
                    <button class="delete-product-btn" data-id="${product.id}">🗑️</button>
                </div>
            `;
            productList.appendChild(li);
        });
    };

    const renderSales = (sales) => {
        salesList.innerHTML = '';
        sales.forEach(sale => {
            const li = document.createElement('li');
            const saleDate = new Date(sale.sale_date).toLocaleDateString();
            // Предполагаем, что сервер вернет детализированную информацию о продаже
            const itemsText = sale.items && sale.items.length > 0 
                ? `${sale.items[0].product.name} x ${sale.items[0].quantity}`
                : 'Детали не загружены';
            li.textContent = `${saleDate}: ${itemsText} = ${sale.total_amount} руб.`;
            salesList.appendChild(li);
        });
    };

    const updateSaleProductOptions = (products) => {
        saleProductSelect.innerHTML = '<option value="">Выберите товар</option>';
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = `${product.name} (${product.price} руб.)`;
            option.dataset.price = product.price; // Сохраняем цену здесь
            saleProductSelect.appendChild(option);
        });
    };

    // --- EVENT LISTENERS ---
    productSearch.addEventListener('input', () => fetchProducts(productSearch.value));
    filterSalesBtn.addEventListener('click', () => fetchSales(dateFrom.value, dateTo.value));
    resetFilterBtn.addEventListener('click', () => {
        dateFrom.value = '';
        dateTo.value = '';
        fetchSales();
    });

    addProductBtn.addEventListener('click', () => {
        productForm.reset();
        productIdField.value = '';
        showModal(productModal);
    });

    addSaleBtn.addEventListener('click', () => {
        saleForm.reset();
        showModal(saleModal);
    });

    cancelButtons.forEach(btn => btn.addEventListener('click', hideModals));
    modalBackdrop.addEventListener('click', hideModals);

    productForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = productIdField.value;
        const productData = {
            name: productNameField.value,
            price: parseFloat(productPriceField.value),
            sku: `SKU-${Date.now()}`, // Генерируем уникальный SKU
            category: 'Default', // Используем категорию по умолчанию
        };

        const method = id ? 'PATCH' : 'POST';
        const url = id ? `${PRODUCTS_URL}/${id}` : PRODUCTS_URL;

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(productData),
            });
            if (!response.ok) throw new Error('Failed to save product');
            hideModals();
            fetchProducts();
        } catch (error) {
            console.error('Error saving product:', error);
        }
    });

    saleForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const selectedOption = saleProductSelect.options[saleProductSelect.selectedIndex];
        if (!selectedOption || !selectedOption.value) {
            alert('Пожалуйста, выберите товар.');
            return;
        }
        const unitPrice = parseFloat(selectedOption.dataset.price);
        const productId = parseInt(saleProductSelect.value);
        const quantity = parseInt(saleQuantityField.value);

        const saleData = {
            items: [
                {
                    product_id: productId,
                    quantity: quantity,
                    unit_price: unitPrice
                }
            ]
        };

        try {
            const response = await fetch(SALES_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(saleData),
            });
            if (!response.ok) {
                const errorData = await response.json();
                console.error('Server validation error:', errorData);
                throw new Error('Failed to create sale');
            }
            hideModals();
            fetchSales();
        } catch (error) {
            console.error('Error creating sale:', error);
        }
    });

    productList.addEventListener('click', async (e) => {
        const target = e.target;
        const id = target.dataset.id;

        if (target.classList.contains('delete-product-btn')) {
            if (confirm('Вы уверены, что хотите удалить этот товар?')) {
                try {
                    const response = await fetch(`${PRODUCTS_URL}/${id}`, { method: 'DELETE' });
                    if (!response.ok) throw new Error('Failed to delete product');
                    fetchProducts();
                } catch (error) {
                    console.error('Error deleting product:', error);
                }
            }
        }

        if (target.classList.contains('edit-product-btn')) {
            try {
                const response = await fetch(`${PRODUCTS_URL}/${id}`);
                if (!response.ok) throw new Error('Failed to fetch product details');
                const product = await response.json();
                productIdField.value = product.id;
                productNameField.value = product.name;
                productPriceField.value = product.price;
                showModal(productModal);
            } catch (error) {
                console.error('Error fetching product details:', error);
            }
        }
    });

    // Initial data load
    fetchProducts();
    fetchSales();
});