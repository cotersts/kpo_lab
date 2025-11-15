# tests/test_unit_crud.py
from datetime import datetime, date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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


def test_list_products_with_query_filters_by_name_and_sku(db):
    # Arrange
    create_sample_product(db, sku="TV-SAM-43", name="Samsung 43", category="TV")
    create_sample_product(db, sku="TV-LG-55", name="LG 55", category="TV")
    create_sample_product(db, sku="WM-BOSCH", name="Bosch Washer", category="Washer")

    # Act
    # поиск по части имени (должны найти только Samsung 43)
    by_name = crud.list_products(db, q="sams")
    # поиск по части sku (должен найти только WM-BOSCH)
    by_sku = crud.list_products(db, q="bosch")

    # Assert
    assert len(by_name) == 1
    assert by_name[0].name == "Samsung 43"

    assert len(by_sku) == 1
    assert by_sku[0].sku == "WM-BOSCH"


def test_update_product_updates_only_provided_fields(db):
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
    assert updated.category == "OldCategory"
    assert updated.price == pytest.approx(100.0)


def test_update_product_returns_none_for_missing_product(db):
    # Arrange
    update_data = schemas.ProductUpdate(name="Does not matter")

    # Act
    result = crud.update_product(db, product_id=9999, data=update_data)

    # Assert
    assert result is None


def test_delete_product_removes_it_and_returns_true(db):
    # Arrange
    product = create_sample_product(db)

    # Act
    ok = crud.delete_product(db, product.id)
    deleted = crud.get_product(db, product.id)

    # Assert
    assert ok is True
    assert deleted is None


def test_delete_product_returns_false_for_missing_product(db):
    # Arrange / Act
    ok = crud.delete_product(db, product_id=12345)

    # Assert
    assert ok is False


# --- ТЕСТЫ ДЛЯ КЛИЕНТОВ ---


def test_create_and_list_customers(db):
    # Arrange
    create_sample_customer(db, name="Петров Петр")
    create_sample_customer(db, name="Иванов Иван")

    # Act
    customers = crud.list_customers(db)

    # Assert
    names = {c.name for c in customers}
    assert {"Петров Петр", "Иванов Иван"}.issubset(names)


# --- ТЕСТЫ ДЛЯ ПРОДАЖ ---


def test_create_sale_calculates_total_and_creates_items(db):
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


def test_list_sales_filters_by_date_range(db):
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
