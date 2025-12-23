import sys
import os
from datetime import datetime, date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException
from pydantic import ValidationError

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base
from app import crud, schemas, models


# --- Настройка тестовой БД ---

# Используем отдельную in-memory SQLite БД
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # один и тот же коннект для всех сессий
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """
    Создаём все таблицы один раз перед запуском тестов
    и удаляем после завершения.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """
    Отдельная сессия БД для каждого теста.
    Перед тестом очищаем все таблицы.
    """
    session = TestingSessionLocal()

    # Очистка таблиц (в обратном порядке из-за внешних ключей)
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    try:
        yield session
    finally:
        session.close()


# --- Вспомогательные функции для создания данных ---

def create_sample_product(
    db,
    sku: str = "SKU-TEST-1",
    name: str = "Test Product",
    category: str = "TV",
    price: float = 1000.0,
) -> models.Product:
    product_in = schemas.ProductCreate(
        sku=sku,
        name=name,
        category=category,
        price=price,
    )
    return crud.create_product(db, product_in)


def create_sample_customer(
    db,
    name: str = "Иван Тестовый",
    phone: str | None = None,
    email: str | None = None,
) -> models.Customer:
    customer_in = schemas.CustomerCreate(
        name=name,
        phone=phone,
        email=email,
    )
    return crud.create_customer(db, customer_in)


def create_sample_sale(
    db,
    product: models.Product,
    customer: models.Customer | None = None,
    quantity: int = 2,
    unit_price: float | None = None,
) -> models.Sale:
    if unit_price is None:
        unit_price = product.price

    sale_in = schemas.SaleCreate(
        customer_id=customer.id if customer else None,
        items=[
            schemas.SaleItemCreate(
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
            )
        ],
    )
    return crud.create_sale(db, sale_in)


# --- ТЕСТЫ ДЛЯ ПРОДУКТОВ ---

def test_create_and_get_product(db):
    """Тест 1: Создание и получение товара"""
    # Arrange
    product_in = schemas.ProductCreate(
        sku="TV-43-TEST",
        name="Телевизор Test 43\"",
        category="TV",
        price=39990.0,
    )

    # Act
    created = crud.create_product(db, product_in)
    fetched = crud.get_product(db, created.id)

    # Assert
    assert created.id is not None
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.sku == "TV-43-TEST"
    assert fetched.name == "Телевизор Test 43\""
    assert fetched.category == "TV"
    assert fetched.price == pytest.approx(39990.0)


def test_create_product_with_invalid_sku_should_fail():
    """Тест 8: Создание товара с некорректным SKU должно вызвать ошибку валидации Pydantic"""
    # Arrange & Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        schemas.ProductCreate(
            sku="INVALID@#$",
            name="Товар",
            category="TV",
            price=1000.0,
        )
    
    # Проверяем что ошибка связана с валидацией SKU
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'][0] == 'sku'
    assert 'pattern' in errors[0]['type']


def test_create_product_with_high_price_should_fail():
    """Тест 9: Создание товара с ценой > 1,000,000 должно вызвать ошибку валидации Pydantic"""
    # Arrange & Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        schemas.ProductCreate(
            sku="HIGH-PRICE",
            name="Дорогой товар",
            category="Other",
            price=2000000.0,
        )
    
    # Проверяем что ошибка связана с валидацией цены
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'][0] == 'price'
    assert 'less_than_equal' in errors[0]['type']


def test_create_product_with_duplicate_sku_should_fail(db):
    """Тест 16: Создание товара с дублирующимся SKU должно вызвать ошибку бизнес-логики"""
    # Arrange
    product1_in = schemas.ProductCreate(
        sku="DUPLICATE-SKU",
        name="Товар 1",
        category="TV",
        price=1000.0,
    )
    crud.create_product(db, product1_in)
    
    product2_in = schemas.ProductCreate(
        sku="DUPLICATE-SKU",
        name="Товар 2",
        category="TV",
        price=2000.0,
    )
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        crud.create_product(db, product2_in)
    
    assert exc_info.value.status_code == 400
    assert "уже существует" in exc_info.value.detail


def test_list_products_with_query_filters_by_name_and_sku(db):
    """Тест 13: Поиск товаров по названию и SKU"""
    # Arrange
    create_sample_product(db, sku="TV-SAM-43", name="Samsung 43", category="TV")
    create_sample_product(db, sku="TV-LG-55", name="LG 55", category="TV")
    create_sample_product(db, sku="WM-BOSCH", name="Bosch Washer", category="Washer")

    # Act
    # поиск по части имени (должны найти только Samsung 43)
    by_name = crud.list_products(db, q="sams")
    # поиск по части sku (должен найти только WM-BOSCH)
    by_sku = crud.list_products(db, q="bosch")
    # поиск по категории
    by_category = crud.list_products(db, q="washer")

    # Assert
    assert len(by_name) == 1
    assert by_name[0].name == "Samsung 43"

    assert len(by_sku) == 1
    assert by_sku[0].sku == "WM-BOSCH"
    
    assert len(by_category) == 1
    assert by_category[0].category == "Washer"


def test_update_product_updates_only_provided_fields(db):
    """Тест 14: Обновление только указанных полей товара"""
    # Arrange
    product = create_sample_product(
        db,
        sku="SKU-OLD",
        name="Old Name",
        category="OldCategory",
        price=100.0,
    )
    update_data = schemas.ProductUpdate(
        name="New Name"  # меняем только имя
        # category и price не задаём
    )

    # Act
    updated = crud.update_product(db, product.id, update_data)

    # Assert
    assert updated is not None
    assert updated.id == product.id
    assert updated.name == "New Name"
    # остальные поля не изменились
    assert updated.sku == "SKU-OLD"
    assert updated.category == "OldCategory"
    assert updated.price == pytest.approx(100.0)


def test_update_product_with_invalid_sku_should_fail():
    """Обновление товара с некорректным SKU должно вызвать ошибку Pydantic"""
    # Arrange & Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        schemas.ProductUpdate(
            sku="INVALID@#$"
        )
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'][0] == 'sku'


def test_update_product_returns_none_for_missing_product(db):
    """Обновление несуществующего товара должно вернуть None"""
    # Arrange
    update_data = schemas.ProductUpdate(name="Does not matter")

    # Act
    result = crud.update_product(db, product_id=9999, data=update_data)

    # Assert
    assert result is None


def test_delete_product_removes_it_and_returns_true(db):
    """Тест 6: Удаление товара"""
    # Arrange
    product = create_sample_product(db)

    # Act
    ok = crud.delete_product(db, product.id)
    deleted = crud.get_product(db, product.id)

    # Assert
    assert ok is True
    assert deleted is None


def test_delete_product_used_in_sales_should_fail(db):
    """Удаление товара, используемого в продажах, должно вызвать ошибку"""
    # Arrange
    product = create_sample_product(db)
    customer = create_sample_customer(db)
    create_sample_sale(db, product, customer)
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        crud.delete_product(db, product.id)
    
    assert exc_info.value.status_code == 400
    assert "используется в продажах" in exc_info.value.detail


def test_delete_product_returns_false_for_missing_product(db):
    """Удаление несуществующего товара должно вернуть False"""
    # Arrange / Act
    ok = crud.delete_product(db, product_id=12345)

    # Assert
    assert ok is False


# --- ТЕСТЫ ДЛЯ КЛИЕНТОВ ---

def test_create_and_list_customers(db):
    """Создание и получение списка клиентов"""
    # Arrange
    create_sample_customer(db, name="Петров Петр")
    create_sample_customer(db, name="Иванов Иван")

    # Act
    customers = crud.list_customers(db)

    # Assert
    names = {c.name for c in customers}
    assert {"Петров Петр", "Иванов Иван"}.issubset(names)


def test_create_customer_with_invalid_email_should_fail():
    """Тест 20: Создание клиента с некорректным email должно вызвать ошибку Pydantic"""
    # Arrange & Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        schemas.CustomerCreate(
            name="Тестовый Клиент",
            phone="+79990000000",
            email="неправильный@email",  # Некорректный email
        )
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'][0] == 'email'


def test_create_customer_with_duplicate_email_should_fail(db):
    """Создание клиента с дублирующимся email должно вызвать ошибку бизнес-логики"""
    # Arrange
    customer1_in = schemas.CustomerCreate(
        name="Клиент 1",
        phone="+79990000001",
        email="test@example.com",
    )
    crud.create_customer(db, customer1_in)
    
    customer2_in = schemas.CustomerCreate(
        name="Клиент 2",
        phone="+79990000002",
        email="test@example.com",  # Дублирующийся email
    )
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        crud.create_customer(db, customer2_in)
    
    assert exc_info.value.status_code == 400
    assert "уже существует" in exc_info.value.detail


# --- ТЕСТЫ ДЛЯ ПРОДАЖ ---

def test_create_sale_calculates_total_and_creates_items(db):
    """Тест 5: Создание продажи с расчетом общей суммы"""
    # Arrange
    product = create_sample_product(db, price=5000.0)
    customer = create_sample_customer(db)
    # 3 товара по цене 5000 каждый
    quantity = 3
    unit_price = 5000.0

    sale_in = schemas.SaleCreate(
        customer_id=customer.id,
        items=[
            schemas.SaleItemCreate(
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
            )
        ],
    )

    # Act
    sale = crud.create_sale(db, sale_in)

    # Assert
    assert sale.id is not None
    assert sale.customer_id == customer.id
    assert sale.total_amount == pytest.approx(quantity * unit_price)
    assert len(sale.items) == 1
    item = sale.items[0]
    assert item.product_id == product.id
    assert item.quantity == quantity
    assert item.unit_price == pytest.approx(unit_price)


def test_create_sale_with_zero_quantity_should_fail():
    """Тест 11: Создание продажи с количеством 0 должно вызвать ошибку Pydantic"""
    # Arrange & Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        schemas.SaleItemCreate(
            product_id=1,
            quantity=0,  # Некорректное количество
            unit_price=1000.0,
        )
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'][0] == 'quantity'
    assert 'greater_than' in errors[0]['type']


def test_create_sale_with_high_quantity_should_fail():
    """Тест 12: Создание продажи с количеством > 100 должно вызвать ошибку Pydantic"""
    # Arrange & Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        schemas.SaleItemCreate(
            product_id=1,
            quantity=101,  # Некорректное количество
            unit_price=1000.0,
        )
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'][0] == 'quantity'
    assert 'less_than_equal' in errors[0]['type']


def test_create_sale_with_empty_items_should_fail():
    """Тест 19: Создание продажи без товаров должно вызвать ошибку Pydantic"""
    # Arrange & Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        schemas.SaleCreate(
            customer_id=None,
            items=[],  # Пустой список
        )
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'][0] == 'items'
    assert 'too_short' in errors[0]['type']


def test_create_sale_with_duplicate_products_should_fail():
    """Создание продажи с дублирующимися товарами должно вызвать ошибку валидации"""
    # Arrange
    sale_item1 = schemas.SaleItemCreate(
        product_id=1,
        quantity=1,
        unit_price=1000.0,
    )
    sale_item2 = schemas.SaleItemCreate(
        product_id=1,  # Дублирующийся product_id
        quantity=2,
        unit_price=1000.0,
    )
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        schemas.SaleCreate(
            customer_id=None,
            items=[sale_item1, sale_item2],
        )
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'][0] == 'items'
    assert 'value_error' in errors[0]['type']


def test_create_sale_with_nonexistent_product_should_fail(db):
    """Тест 17: Создание продажи с несуществующим товаром должно вызвать ошибку бизнес-логики"""
    # Arrange
    customer = create_sample_customer(db)
    sale_in = schemas.SaleCreate(
        customer_id=customer.id,
        items=[
            schemas.SaleItemCreate(
                product_id=99999,  # Несуществующий товар
                quantity=1,
                unit_price=1000.0,
            )
        ],
    )
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        crud.create_sale(db, sale_in)
    
    assert exc_info.value.status_code == 404
    assert "не найден" in exc_info.value.detail


def test_create_sale_with_nonexistent_customer_should_fail(db):
    """Тест 18: Создание продажи с несуществующим клиентом должно вызвать ошибку бизнес-логики"""
    # Arrange
    product = create_sample_product(db, price=1000.0)
    sale_in = schemas.SaleCreate(
        customer_id=99999,  # Несуществующий клиент
        items=[
            schemas.SaleItemCreate(
                product_id=product.id,
                quantity=1,
                unit_price=1000.0,
            )
        ],
    )
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        crud.create_sale(db, sale_in)
    
    assert exc_info.value.status_code == 404
    assert "не найден" in exc_info.value.detail


def test_list_sales_filters_by_date_range(db):
    """Тест 7: Фильтрация продаж по дате"""
    # Arrange
    product = create_sample_product(db, price=1000.0)
    customer = create_sample_customer(db)

    sale1 = create_sample_sale(db, product, customer, quantity=1, unit_price=1000.0)
    sale2 = create_sample_sale(db, product, customer, quantity=2, unit_price=2000.0)

    # жёстко выставляем даты продаж для контроля
    sale1.sale_date = datetime(2024, 1, 10, 12, 0, 0)
    sale2.sale_date = datetime(2024, 1, 12, 18, 0, 0)
    db.commit()

    # Act
    # продажи только за 10–11 января
    sales_10_11 = crud.list_sales(
        db,
        date_from=date(2024, 1, 10),
        date_to=date(2024, 1, 12),  # верхняя граница НЕ включается
    )
    # продажи начиная с 12 января
    sales_from_12 = crud.list_sales(
        db,
        date_from=date(2024, 1, 12),
        date_to=None,
    )

    # Assert
    assert [s.id for s in sales_10_11] == [sale1.id]
    assert [s.id for s in sales_from_12] == [sale2.id]


def test_list_sales_loads_items_and_products(db):
    """Продажи должны загружаться с товарами и информацией о продуктах"""
    # Arrange
    product = create_sample_product(db, sku="SKU-ITEM-1", name="Товар для продажи")
    sale = create_sample_sale(db, product, quantity=2, unit_price=1234.0)

    # Act
    sales = crud.list_sales(db)
    assert len(sales) == 1
    loaded_sale = sales[0]

    # Assert
    # items и product должны быть доступны (joinedload в list_sales)
    assert len(loaded_sale.items) == 1
    item = loaded_sale.items[0]
    assert item.product is not None
    assert item.product.sku == "SKU-ITEM-1"
    assert item.product.name == "Товар для продажи"


def test_daily_summary_returns_correct_count_and_revenue(db):
    """Получение дневной статистики по продажам"""
    # Arrange
    product = create_sample_product(db, price=1000.0)
    customer = create_sample_customer(db)

    sale1 = create_sample_sale(db, product, customer, quantity=1, unit_price=1000.0)
    sale2 = create_sample_sale(db, product, customer, quantity=3, unit_price=500.0)

    # обе продажи относятся к одному и тому же дню
    target_day = date(2024, 2, 1)
    sale1.sale_date = datetime(2024, 2, 1, 10, 0, 0)
    sale2.sale_date = datetime(2024, 2, 1, 15, 30, 0)
    db.commit()

    expected_revenue = 1 * 1000.0 + 3 * 500.0

    # Act
    count, revenue = crud.daily_summary(db, target_day)

    # Assert
    assert count == 2
    assert revenue == pytest.approx(expected_revenue)


def test_daily_summary_for_empty_day(db):
    """Статистика за день без продаж должна вернуть 0"""
    # Arrange
    empty_day = date(2024, 1, 1)

    # Act
    count, revenue = crud.daily_summary(db, empty_day)

    # Assert
    assert count == 0
    assert revenue == pytest.approx(0.0)


def test_create_product_with_negative_price_should_fail():
    """Тест 2: Создание товара с отрицательной ценой должно вызвать ошибку Pydantic"""
    # Arrange & Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        schemas.ProductCreate(
            sku="NEG-PRICE",
            name="Товар с отрицательной ценой",
            category="Test",
            price=-5000.0,
        )
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'][0] == 'price'
    assert 'greater_than' in errors[0]['type']


def test_create_product_with_zero_price_should_fail():
    """Тест 3: Создание товара с нулевой ценой должно вызвать ошибку Pydantic"""
    # Arrange & Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        schemas.ProductCreate(
            sku="ZERO-PRICE",
            name="Товар с нулевой ценой",
            category="Test",
            price=0.0,
        )
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'][0] == 'price'
    assert 'greater_than' in errors[0]['type']


def test_create_product_with_fractional_price_success():
    """Тест 4: Создание товара с дробной ценой должно быть успешным"""
    # Arrange & Act
    product = schemas.ProductCreate(
        sku="FRACTIONAL",
        name="Товар с дробной ценой",
        category="Test",
        price=5.55,
    )
    
    # Assert
    assert product.price == 5.55
    assert isinstance(product.price, float)


def test_create_product_with_short_name_should_fail():
    """Создание товара с слишком коротким названием должно вызвать ошибку Pydantic"""
    # Arrange & Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        schemas.ProductCreate(
            sku="SHORT",
            name="A",  # Слишком короткое название
            category="Test",
            price=1000.0,
        )
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['loc'][0] == 'name'
    assert 'string_too_short' in errors[0]['type']