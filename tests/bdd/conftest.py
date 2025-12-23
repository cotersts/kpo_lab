import ast
import json
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, when, then, parsers
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


from app.main import app, get_db  # noqa
from app.models import Base  # noqa


# ------------------ TEST DB (SQLite in-memory, shared) ------------------
TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # важно для in-memory между потоками TestClient
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _prepare_database():
    """
    Перед каждым тестом: пересоздаём таблицы -> "чистое API".
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # можно не дропать после, но пусть будет чисто
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """
    TestClient с переопределённой зависимостью get_db.
    """
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ------------------ helpers ------------------
def _parse_payload(json_str: str) -> Any:
    
    s = json_str.strip()

    # 1) нормальный JSON
    try:
        return json.loads(s)
    except Exception:
        pass

    # 2) почти python-литерал
    s2 = (
        s.replace(": null", ": None")
        .replace(": true", ": True")
        .replace(": false", ": False")
    )
    try:
        return ast.literal_eval(s2)
    except Exception as e:
        raise ValueError(f"Не смог распарсить JSON из feature: {json_str}") from e


def _set_response(request, resp):
    request._bdd_response = resp


def _get_response(request):
    return getattr(request, "_bdd_response", None)


# ------------------ GIVEN ------------------
@given("чистое API")
def given_clean_api():
    # База и так пересоздаётся autouse фикстурой.
    return True


@given(parsers.parse("существует клиент с email {email}"))
def given_customer_exists(client: TestClient, email: str):
    email = email.strip('"')
    resp = client.post(
        "/api/customers",
        json={"name": "Existing", "phone": "+7-900-000-00-99", "email": email},
    )
    
    assert resp.status_code in (201, 400), resp.text


@given(parsers.parse("существует товар с SKU {sku}"))
def given_product_exists(client: TestClient, sku: str):
    sku = sku.strip('"')
    resp = client.post(
        "/api/products",
        json={"sku": sku, "name": "Existing product", "category": "TV", "price": 1000.0},
    )
    assert resp.status_code in (201, 400), resp.text


@given("существует товар и клиент и продажа на этот товар")
def given_product_customer_sale(client: TestClient):
    # 1) product
    pr = client.post(
        "/api/products",
        json={"sku": "LOCK-001", "name": "Товар для продажи", "category": "TV", "price": 5000.0},
    )
    assert pr.status_code == 201, pr.text
    product_id = pr.json()["id"]

    # 2) customer
    cu = client.post(
        "/api/customers",
        json={"name": "Покупатель", "phone": "+7-900-111-22-33", "email": "buyer@example.com"},
    )
    assert cu.status_code == 201, cu.text
    customer_id = cu.json()["id"]

    # 3) sale
    
    sl = client.post(
        "/api/sales",
        json={
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 1, "unit_price": 5000.0}],
        },
    )
    assert sl.status_code == 201, sl.text


# ------------------ WHEN (requests) ------------------
@when(parsers.parse('я отправляю POST "{path}" с JSON: {json_str}'))
def post_json(client: TestClient, request, path: str, json_str: str):
    payload = _parse_payload(json_str)
    resp = client.post(path, json=payload)
    _set_response(request, resp)


@when(parsers.parse('я отправляю GET "{path}"'))
def get_request(client: TestClient, request, path: str):
    resp = client.get(path)
    _set_response(request, resp)


@when(parsers.parse('я отправляю PATCH "{path}" с JSON: {json_str}'))
def patch_json(client: TestClient, request, path: str, json_str: str):
    payload = _parse_payload(json_str)
    resp = client.patch(path, json=payload)
    _set_response(request, resp)


@when(parsers.parse('я отправляю DELETE "{path}"'))
def delete_request(client: TestClient, request, path: str):
    resp = client.delete(path)
    _set_response(request, resp)


# ------------------ THEN (assertions) ------------------
@then(parsers.parse("статус ответа = {status:d}"))
def assert_status(request, status: int):
    resp = _get_response(request)
    assert resp is not None, "Нет сохранённого ответа (request._bdd_response)"
    assert resp.status_code == status, resp.text


@then(parsers.parse('в ответе JSON поле "{field}" существует'))
def assert_json_field_exists(request, field: str):
    resp = _get_response(request)
    data = resp.json()
    assert field in data, data


@then(parsers.parse('в ответе detail содержит "{text}"'))
def assert_detail_contains(request, text: str):
    resp = _get_response(request)
    data = resp.json()
    detail = data.get("detail")
    if isinstance(detail, (list, dict)):
        detail = json.dumps(detail, ensure_ascii=False)
    assert text in str(detail), data


@then(
    parsers.re(
        r'в ответе JSON поле "(?P<field>[^"]+)" = (?P<value>.+)'
    )
)
def assert_json_field_equals_any(request, field: str, value: str):
    """
    Работает для:
    - "строк" в кавычках
    - чисел без кавычек (в т.ч. 12345.670000)
    - true/false/null 
    """
    resp = _get_response(request)
    data: Dict[str, Any] = resp.json()

    assert field in data, data

    raw = value.strip()

    # строка в кавычках
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        expected = raw[1:-1]
        assert str(data[field]) == expected, data
        return

    # null/true/false
    low = raw.lower()
    if low == "null":
        assert data[field] is None, data
        return
    if low == "true":
        assert data[field] is True, data
        return
    if low == "false":
        assert data[field] is False, data
        return

    # число
    try:
        expected_num = float(raw)
        actual_num = float(data[field])
        assert abs(actual_num - expected_num) < 1e-6, data
        return
    except Exception:
        # fallback: просто сравнение как строки
        assert str(data[field]) == raw, data


@then(parsers.parse("total_amount продажи равен {amount:g}"))
def assert_total_amount(request, amount: float):
    resp = _get_response(request)
    data = resp.json()
    assert "total_amount" in data, data
    assert abs(float(data["total_amount"]) - float(amount)) < 1e-6, data
