from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]  # /workspaces/kpo_lab

CANDIDATE_HTML = [
    ROOT / "static" / "index.html",
    ROOT / "app" / "static" / "index.html",
]
CANDIDATE_JS = [
    ROOT / "static" / "script.js",
    ROOT / "app" / "static" / "script.js",
]


def _pick_existing(paths: list[Path], kind: str) -> Path:
    for p in paths:
        if p.exists():
            return p
    tried = "\n".join(str(p) for p in paths)
    raise AssertionError(f"{kind} не найден. Проверял:\n{tried}")


HTML_PATH = _pick_existing(CANDIDATE_HTML, "index.html")
JS_PATH = _pick_existing(CANDIDATE_JS, "script.js")


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


HTML = read_text(HTML_PATH)
JS = read_text(JS_PATH)


def assert_re(text: str, pattern: str, msg: str):
    if not re.search(pattern, text, flags=re.S | re.M):
        raise AssertionError(msg + f"\n--- regex ---\n{pattern}\n")


# 1
def test_paths_detected():
    assert HTML_PATH.exists()
    assert JS_PATH.exists()


# 2
def test_html_has_required_ids():
    # Products
    assert_re(HTML, r'id="product-search"', 'В HTML нет поля поиска id="product-search"')
    assert_re(HTML, r'id="add-product-btn"', 'В HTML нет кнопки id="add-product-btn"')
    assert_re(HTML, r'id="product-list"', 'В HTML нет списка id="product-list"')

    # Sales
    assert_re(HTML, r'id="date-from"', 'В HTML нет поля даты id="date-from"')
    assert_re(HTML, r'id="date-to"', 'В HTML нет поля даты id="date-to"')
    assert_re(HTML, r'id="filter-sales-btn"', 'В HTML нет кнопки id="filter-sales-btn"')
    assert_re(HTML, r'id="reset-filter-btn"', 'В HTML нет кнопки id="reset-filter-btn"')
    assert_re(HTML, r'id="add-sale-btn"', 'В HTML нет кнопки id="add-sale-btn"')
    assert_re(HTML, r'id="sales-list"', 'В HTML нет списка id="sales-list"')

    # Modals + forms
    assert_re(HTML, r'id="product-modal"', 'В HTML нет модалки товара id="product-modal"')
    assert_re(HTML, r'id="sale-modal"', 'В HTML нет модалки продажи id="sale-modal"')
    assert_re(HTML, r'id="modal-backdrop"', 'В HTML нет backdrop id="modal-backdrop"')
    assert_re(HTML, r'id="product-form"', 'В HTML нет формы товара id="product-form"')
    assert_re(HTML, r'id="sale-form"', 'В HTML нет формы продажи id="sale-form"')

    # Script include
    assert_re(HTML, r'<script\s+src="script\.js"\s*>\s*</script>', "В HTML не подключён script.js")


# 3
def test_js_binds_search_input_to_fetchProducts():
    assert_re(
        JS,
        r"const\s+productSearch\s*=\s*document\.getElementById\(\s*['\"]product-search['\"]\s*\)",
        "В JS не найдено: const productSearch = document.getElementById('product-search')",
    )
    assert_re(
        JS,
        r"productSearch\.addEventListener\(\s*['\"]input['\"]\s*,\s*\(\s*\)\s*=>\s*fetchProducts\(\s*productSearch\.value\s*\)\s*\)",
        "Поле поиска не привязано к fetchProducts(productSearch.value) на событие input",
    )


# 4
def test_js_binds_sales_filter_and_reset_buttons():
    assert_re(
        JS,
        r"filterSalesBtn\.addEventListener\(\s*['\"]click['\"]\s*,\s*\(\s*\)\s*=>\s*\{.*?fetchSales\(\s*dateFrom\.value\s*,\s*dateTo\.value\s*\)\s*;.*?\}\s*\)",
        "Кнопка 'Фильтр' должна по клику вызывать fetchSales(dateFrom.value, dateTo.value)",
    )
    assert_re(
        JS,
        r"resetFilterBtn\.addEventListener\(\s*['\"]click['\"]\s*,\s*\(\s*\)\s*=>\s*\{.*?dateFrom\.value\s*=\s*['\"]{0,1}['\"]\s*;.*?dateTo\.value\s*=\s*['\"]{0,1}['\"]\s*;.*?fetchSales\(\s*\)\s*;.*?\}\s*\)",
        "Кнопка 'Сбросить' должна чистить даты и вызывать fetchSales()",
    )


# 5
def test_js_binds_add_product_button_to_show_product_modal():
    assert_re(
        JS,
        r"addProductBtn\.addEventListener\(\s*['\"]click['\"]\s*,\s*\(\s*\)\s*=>\s*\{.*?showModal\(\s*productModal\s*\)\s*;.*?\}\s*\)",
        "Кнопка 'Добавить товар' должна открывать productModal через showModal(productModal)",
    )


# 6
def test_js_binds_add_sale_button_to_update_customers_and_show_sale_modal():
    assert_re(
        JS,
        r"addSaleBtn\.addEventListener\(\s*['\"]click['\"]\s*,\s*async\s*\(\s*\)\s*=>\s*\{.*?await\s+updateCustomerOptions\(\s*\)\s*;.*?showModal\(\s*saleModal\s*\)\s*;.*?\}\s*\)",
        "Кнопка 'Оформить продажу' должна обновлять клиентов и открывать saleModal",
    )


# 7 (новый) — кнопки отмены и клик по backdrop закрывают модалки
def test_js_binds_cancel_and_backdrop_to_hideModals():
    assert_re(
        JS,
        r"cancelButtons\.forEach\(\s*btn\s*=>\s*btn\.addEventListener\(\s*['\"]click['\"]\s*,\s*hideModals\s*\)\s*\)",
        "Кнопки .cancel-btn должны быть привязаны к hideModals()",
    )
    assert_re(
        JS,
        r"modalBackdrop\.addEventListener\(\s*['\"]click['\"]\s*,\s*hideModals\s*\)",
        "Клик по modal-backdrop должен закрывать модалки (hideModals)",
    )


# 8 (новый) — submit товара отправляет POST/PATCH на /api/products и потом вызывает fetchProducts()
def test_js_product_form_submit_sends_request_and_refreshes_products():
    # метод выбирается по наличию id
    assert_re(
        JS,
        r"const\s+method\s*=\s*id\s*\?\s*['\"]PATCH['\"]\s*:\s*['\"]POST['\"]",
        "В productForm submit должно быть: method = id ? 'PATCH' : 'POST'",
    )
    assert_re(
        JS,
        r"const\s+url\s*=\s*id\s*\?\s*`?\$\{PRODUCTS_URL\}/\$\{id\}`?\s*:\s*PRODUCTS_URL",
        "В productForm submit должно быть: url = id ? `${PRODUCTS_URL}/${id}` : PRODUCTS_URL",
    )
    assert_re(
        JS,
        r"fetch\(\s*url\s*,\s*\{\s*method:\s*method\s*,",
        "В productForm submit должен вызываться fetch(url, { method })",
    )
    assert_re(
        JS,
        r"showSuccess\(\s*id\s*\?\s*['\"][^'\"]*обновл[её]н[^'\"]*['\"]\s*:\s*['\"][^'\"]*добавл[её]н[^'\"]*['\"]\s*\)",
        "После сохранения товара должен быть showSuccess(...) с разными сообщениями для PATCH/POST",
    )
    assert_re(
        JS,
        r"fetchProducts\(\s*\)",
        "После сохранения товара должен вызываться fetchProducts()",
    )


# 9 (новый) — submit продажи отправляет POST на /api/sales и потом вызывает fetchSales()
def test_js_sale_form_submit_posts_sales_and_refreshes_sales():
    assert_re(
        JS,
        r"fetch\(\s*SALES_URL\s*,\s*\{\s*method:\s*['\"]POST['\"]",
        "В saleForm submit должен быть fetch(SALES_URL, { method: 'POST', ... })",
    )
    assert_re(
        JS,
        r"showSuccess\(\s*['\"][^'\"]*Продажа[^'\"]*['\"]\s*\)",
        "После оформления продажи должен быть showSuccess('...')",
    )
    assert_re(
        JS,
        r"fetchSales\(\s*\)",
        "После оформления продажи должен вызываться fetchSales()",
    )


# 10 (новый) — клик по списку товаров обрабатывает delete/edit и вызывает нужные API
def test_js_product_list_click_handles_delete_and_edit():
    # delete -> fetch(`${PRODUCTS_URL}/${id}`, { method: 'DELETE' })
    assert_re(
        JS,
        r"if\s*\(\s*target\.classList\.contains\(\s*['\"]delete-product-btn['\"]\s*\)\s*\)\s*\{.*?fetch\(\s*`?\$\{PRODUCTS_URL\}/\$\{id\}`?\s*,\s*\{\s*method:\s*['\"]DELETE['\"]\s*\}\s*\)",
        "Удаление товара должно делать fetch(`${PRODUCTS_URL}/${id}`, { method: 'DELETE' })",
    )
    # edit -> fetch(`${PRODUCTS_URL}/${id}`) + showModal(productModal)
    assert_re(
        JS,
        r"if\s*\(\s*target\.classList\.contains\(\s*['\"]edit-product-btn['\"]\s*\)\s*\)\s*\{.*?fetch\(\s*`?\$\{PRODUCTS_URL\}/\$\{id\}`?\s*\)\s*;.*?showModal\(\s*productModal\s*\)",
        "Редактирование должно загружать товар через fetch(`${PRODUCTS_URL}/${id}`) и открывать productModal",
    )
