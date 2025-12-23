document.addEventListener('DOMContentLoaded', () => {
    // URLs for API endpoints
    const API_URL = '/api';
    const PRODUCTS_URL = `${API_URL}/products`;
    const SALES_URL = `${API_URL}/sales`;
    const CUSTOMERS_URL = `${API_URL}/customers`;

    // Utility functions
    const showError = (message) => {
        alert(`Ошибка: ${message}`);
    };

    const showSuccess = (message) => {
        alert(`Успех: ${message}`);
    };

    const validateForm = (formData) => {
        const errors = [];
        
        // Валидация цены
        if (formData.price && (formData.price <= 0 || formData.price > 1000000)) {
            errors.push('Цена должна быть от 0.01 до 1 000 000');
        }
        
        // Валидация количества
        if (formData.quantity && (formData.quantity < 1 || formData.quantity > 100)) {
            errors.push('Количество должно быть от 1 до 100');
        }
        
        return errors;
    };

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
    const productSkuField = document.getElementById('product-sku');
    const productCategoryField = document.getElementById('product-category');

    // Sale form fields
    const saleProductSelect = document.getElementById('sale-product');
    const saleQuantityField = document.getElementById('sale-quantity');
    const saleCustomerSelect = document.getElementById('sale-customer');

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
            const url = query ? `${PRODUCTS_URL}?q=${encodeURIComponent(query)}` : PRODUCTS_URL;
            const response = await fetch(url);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to fetch products');
            }
            const products = await response.json();
            renderProducts(products);
            updateSaleProductOptions(products);
            return products;
        } catch (error) {
            console.error('Error fetching products:', error);
            showError(`Не удалось загрузить товары: ${error.message}`);
        }
    };

    const fetchCustomers = async () => {
        try {
            const response = await fetch(CUSTOMERS_URL);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to fetch customers');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching customers:', error);
            return [];
        }
    };

    const fetchSales = async (from = '', to = '') => {
        try {
            const params = new URLSearchParams();
            if (from) params.append('date_from', from);
            if (to) params.append('date_to', to);
            
            const response = await fetch(`${SALES_URL}?${params.toString()}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to fetch sales');
            }
            const sales = await response.json();
            renderSales(sales);
            return sales;
        } catch (error) {
            console.error('Error fetching sales:', error);
            showError(`Не удалось загрузить продажи: ${error.message}`);
        }
    };

    // --- RENDER FUNCTIONS ---
    const renderProducts = (products) => {
        productList.innerHTML = '';
        products.forEach(product => {
            const li = document.createElement('li');
            li.innerHTML = `
                <div>
                    <strong>${product.name}</strong><br>
                    <small>Артикул: ${product.sku} | Категория: ${product.category}</small><br>
                    Цена: ${product.price.toFixed(2)} руб.
                </div>
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
            const saleDate = new Date(sale.sale_date).toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            const itemsText = sale.items && sale.items.length > 0 
                ? sale.items.map(item => 
                    `${item.product.name} × ${item.quantity}`
                ).join(', ')
                : 'Нет товаров';
            
            li.innerHTML = `
                <div>
                    <strong>${saleDate}</strong><br>
                    Товары: ${itemsText}<br>
                    Итого: ${sale.total_amount.toFixed(2)} руб.
                </div>
            `;
            salesList.appendChild(li);
        });
    };

    const updateSaleProductOptions = (products) => {
        saleProductSelect.innerHTML = '<option value="">Выберите товар</option>';
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = `${product.name} (${product.price.toFixed(2)} руб.)`;
            option.dataset.price = product.price;
            saleProductSelect.appendChild(option);
        });
    };

    const updateCustomerOptions = async () => {
        const customers = await fetchCustomers();
        saleCustomerSelect.innerHTML = '<option value="">Без клиента</option>';
        customers.forEach(customer => {
            const option = document.createElement('option');
            option.value = customer.id;
            option.textContent = `${customer.name} ${customer.phone ? `(${customer.phone})` : ''}`;
            saleCustomerSelect.appendChild(option);
        });
    };

    // --- EVENT LISTENERS ---
    productSearch.addEventListener('input', () => fetchProducts(productSearch.value));
    
    filterSalesBtn.addEventListener('click', () => {
        if (dateFrom.value && dateTo.value && dateFrom.value > dateTo.value) {
            showError('Дата начала не может быть позже даты окончания');
            return;
        }
        fetchSales(dateFrom.value, dateTo.value);
    });
    
    resetFilterBtn.addEventListener('click', () => {
        dateFrom.value = '';
        dateTo.value = '';
        fetchSales();
    });

    addProductBtn.addEventListener('click', () => {
        productForm.reset();
        productIdField.value = '';
        productSkuField.value = `SKU-${Date.now().toString().slice(-6)}`;
        showModal(productModal);
    });

    addSaleBtn.addEventListener('click', async () => {
        saleForm.reset();
        await updateCustomerOptions();
        showModal(saleModal);
    });

    cancelButtons.forEach(btn => btn.addEventListener('click', hideModals));
    modalBackdrop.addEventListener('click', hideModals);

    productForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            sku: productSkuField.value,
            name: productNameField.value,
            category: productCategoryField.value || 'Other',
            price: parseFloat(productPriceField.value)
        };

        // Валидация на клиенте
        const errors = validateForm(formData);
        if (errors.length > 0) {
            showError(errors.join('\n'));
            return;
        }

        const id = productIdField.value;
        const method = id ? 'PATCH' : 'POST';
        const url = id ? `${PRODUCTS_URL}/${id}` : PRODUCTS_URL;

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(formData),
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to save product');
            }
            
            hideModals();
            showSuccess(id ? 'Товар обновлен' : 'Товар добавлен');
            fetchProducts();
        } catch (error) {
            console.error('Error saving product:', error);
            showError(`Не удалось сохранить товар: ${error.message}`);
        }
    });

    saleForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const selectedOption = saleProductSelect.options[saleProductSelect.selectedIndex];
        if (!selectedOption || !selectedOption.value) {
            showError('Пожалуйста, выберите товар');
            return;
        }

        const formData = {
            productId: parseInt(saleProductSelect.value),
            quantity: parseInt(saleQuantityField.value),
            customerId: saleCustomerSelect.value ? parseInt(saleCustomerSelect.value) : null
        };

        // Валидация на клиенте
        const errors = validateForm(formData);
        if (errors.length > 0) {
            showError(errors.join('\n'));
            return;
        }

        const saleData = {
            customer_id: formData.customerId,
            items: [
                {
                    product_id: formData.productId,
                    quantity: formData.quantity,
                    unit_price: parseFloat(selectedOption.dataset.price)
                }
            ]
        };

        try {
            const response = await fetch(SALES_URL, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(saleData),
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create sale');
            }
            
            hideModals();
            showSuccess('Продажа успешно оформлена');
            fetchSales();
        } catch (error) {
            console.error('Error creating sale:', error);
            showError(`Не удалось оформить продажу: ${error.message}`);
        }
    });

    productList.addEventListener('click', async (e) => {
        const target = e.target;
        const id = target.dataset.id;

        if (target.classList.contains('delete-product-btn')) {
            if (confirm('Вы уверены, что хотите удалить этот товар?')) {
                try {
                    const response = await fetch(`${PRODUCTS_URL}/${id}`, { 
                        method: 'DELETE' 
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || 'Failed to delete product');
                    }
                    
                    showSuccess('Товар удален');
                    fetchProducts();
                } catch (error) {
                    console.error('Error deleting product:', error);
                    showError(`Не удалось удалить товар: ${error.message}`);
                }
            }
        }

        if (target.classList.contains('edit-product-btn')) {
            try {
                const response = await fetch(`${PRODUCTS_URL}/${id}`);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to fetch product details');
                }
                
                const product = await response.json();
                productIdField.value = product.id;
                productSkuField.value = product.sku;
                productNameField.value = product.name;
                productCategoryField.value = product.category;
                productPriceField.value = product.price;
                showModal(productModal);
            } catch (error) {
                console.error('Error fetching product details:', error);
                showError(`Не удалось загрузить данные товара: ${error.message}`);
            }
        }
    });

    // Установка текущей даты по умолчанию для фильтров
    const today = new Date().toISOString().split('T')[0];
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    const weekAgoStr = weekAgo.toISOString().split('T')[0];
    
    dateFrom.value = weekAgoStr;
    dateTo.value = today;

    // Initial data load
    fetchProducts();
    fetchSales(weekAgoStr, today);
});