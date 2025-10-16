"""Первичная инициализация БД и создание демо‑данных."""
from .database import Base, engine, SessionLocal
from . import models
from sqlalchemy import select

def ensure_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Продукты
        if db.scalar(select(models.Product).limit(1)) is None:
            products = [
                models.Product(sku="TV-43-SAM", name="Телевизор Samsung 43'", category="TV", price=39990),
                models.Product(sku="TV-55-LG", name="Телевизор LG 55'", category="TV", price=64990),
                models.Product(sku="WM-BOS-7", name="Стиральная машина Bosch 7 кг", category="Washer", price=52990),
                models.Product(sku="FR-SAM-300", name="Холодильник Samsung 300л", category="Fridge", price=58990),
                models.Product(sku="VAC-PHI", name="Пылесос Philips", category="Vacuum", price=12990),
            ]
            db.add_all(products)

        # Клиент
        if db.scalar(select(models.Customer).limit(1)) is None:
            db.add(models.Customer(name="Иван Петров", phone="+7-900-000-00-00", email="ivan@example.com"))

        db.commit()
        print("Seed OK")
    finally:
        db.close()

if __name__ == "__main__":
    ensure_seed()
