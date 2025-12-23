"""Первичная инициализация БД и создание демо‑данных."""
from .database import Base, engine, SessionLocal
from . import models
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Продукты
        if db.scalar(select(models.Product).limit(1)) is None:
            products = [
                models.Product(
                    sku="TV-43-SAM", 
                    name="Телевизор Samsung 43'", 
                    category="TV", 
                    price=39990.0
                ),
                models.Product(
                    sku="TV-55-LG", 
                    name="Телевизор LG 55'", 
                    category="TV", 
                    price=64990.0
                ),
                models.Product(
                    sku="WM-BOS-7", 
                    name="Стиральная машина Bosch 7 кг", 
                    category="Washer", 
                    price=52990.0
                ),
                models.Product(
                    sku="FR-SAM-300", 
                    name="Холодильник Samsung 300л", 
                    category="Fridge", 
                    price=58990.0
                ),
                models.Product(
                    sku="VAC-PHI", 
                    name="Пылесос Philips", 
                    category="Vacuum", 
                    price=12990.0
                ),
            ]
            db.add_all(products)
            logger.info(f"Создано {len(products)} товаров")

        # Клиенты
        if db.scalar(select(models.Customer).limit(1)) is None:
            customers = [
                models.Customer(
                    name="Иван Петров", 
                    phone="+7-900-000-00-00", 
                    email="ivan@example.com"
                ),
                models.Customer(
                    name="Мария Сидорова", 
                    phone="8-911-123-45-67", 
                    email="maria@example.com"
                ),
                models.Customer(
                    name="Алексей Иванов", 
                    phone="+7-912-345-67-89", 
                    email=None
                ),
            ]
            db.add_all(customers)
            logger.info(f"Создано {len(customers)} клиентов")

        db.commit()
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при инициализации БД: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    ensure_seed()