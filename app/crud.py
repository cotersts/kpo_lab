from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, and_
from datetime import datetime, date
from fastapi import HTTPException
from . import models, schemas


# Products
def create_product(db: Session, data: schemas.ProductCreate) -> models.Product:
    # Проверка на существующий SKU
    existing = db.scalar(
        select(models.Product).where(models.Product.sku == data.sku)
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Товар с SKU '{data.sku}' уже существует"
        )
    
    obj = models.Product(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_products(db: Session, q: str | None = None):
    stmt = select(models.Product)
    if q:
        q_like = f"%{q}%"
        stmt = stmt.where(
            models.Product.name.ilike(q_like) | 
            models.Product.sku.ilike(q_like) |
            models.Product.category.ilike(q_like)
        )
    return db.scalars(stmt).all()


def get_product(db: Session, product_id: int):
    return db.get(models.Product, product_id)


def update_product(db: Session, product_id: int, data: schemas.ProductUpdate):
    obj = db.get(models.Product, product_id)
    if not obj:
        return None
    
    # Если обновляется SKU, проверяем уникальность
    if data.sku is not None and data.sku != obj.sku:
        existing = db.scalar(
            select(models.Product).where(
                and_(
                    models.Product.sku == data.sku,
                    models.Product.id != product_id
                )
            )
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Товар с SKU '{data.sku}' уже существует"
            )
    
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete_product(db: Session, product_id: int) -> bool:
    obj = db.get(models.Product, product_id)
    if not obj:
        return False
    
    # Проверяем, не используется ли товар в продажах
    used_in_sales = db.scalar(
        select(func.count(models.SaleItem.id)).where(
            models.SaleItem.product_id == product_id
        )
    )
    if used_in_sales > 0:
        raise HTTPException(
            status_code=400,
            detail="Невозможно удалить товар, который используется в продажах"
        )
    
    db.delete(obj)
    db.commit()
    return True


# Customers
def create_customer(db: Session, data: schemas.CustomerCreate) -> models.Customer:
    # Проверка уникальности email
    if data.email:
        existing = db.scalar(
            select(models.Customer).where(models.Customer.email == data.email)
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Клиент с email '{data.email}' уже существует"
            )
    
    obj = models.Customer(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_customers(db: Session):
    return db.scalars(select(models.Customer)).all()


# Sales
def create_sale(db: Session, data: schemas.SaleCreate) -> models.Sale:
    # Проверяем существование клиента
    if data.customer_id:
        customer = db.get(models.Customer, data.customer_id)
        if not customer:
            raise HTTPException(
                status_code=404,
                detail=f"Клиент с ID {data.customer_id} не найден"
            )
    
    # Проверяем существование товаров и их доступность
    for item in data.items:
        product = db.get(models.Product, item.product_id)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Товар с ID {item.product_id} не найден"
            )
        
        # Можно добавить проверку на наличие товара на складе
        # if product.stock_quantity < item.quantity:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"Недостаточно товара '{product.name}' на складе"
        #     )
    
    sale = models.Sale(customer_id=data.customer_id)
    db.add(sale)
    db.flush()  # получаем sale.id

    total = 0.0
    for item in data.items:
        # Получаем информацию о товаре для логирования
        product = db.get(models.Product, item.product_id)
        
        si = models.SaleItem(
            sale_id=sale.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        total += item.quantity * item.unit_price
        db.add(si)
        
        # Можно обновить количество товара на складе
        # product.stock_quantity -= item.quantity

    sale.total_amount = total
    db.commit()
    
    # Загружаем связанные данные для возврата
    db.refresh(sale)
    sale = db.scalar(
        select(models.Sale)
        .options(
            joinedload(models.Sale.items)
            .joinedload(models.SaleItem.product)
        )
        .where(models.Sale.id == sale.id)
    )
    
    return sale


def list_sales(db: Session, date_from: date | None = None, date_to: date | None = None):
    stmt = (
        select(models.Sale)
        .options(
            joinedload(models.Sale.items)
            .joinedload(models.SaleItem.product)
        )
    )
    
    # Валидация дат
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=400,
            detail="Дата начала не может быть позже даты окончания"
        )
    
    if date_from:
        stmt = stmt.where(models.Sale.sale_date >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        stmt = stmt.where(models.Sale.sale_date < datetime.combine(date_to, datetime.min.time()))
    
    stmt = stmt.order_by(models.Sale.sale_date.desc())
    return db.scalars(stmt).unique().all()


def daily_summary(db: Session, day: date):
    start = datetime.combine(day, datetime.min.time())
    end = datetime.combine(day, datetime.max.time())
    
    stmt = (
        select(
            func.count(models.Sale.id),
            func.coalesce(func.sum(models.Sale.total_amount), 0.0),
        )
        .where(models.Sale.sale_date >= start, models.Sale.sale_date <= end)
    )
    
    count, revenue = db.execute(stmt).one()
    return count, float(revenue or 0.0)


def get_sale(db: Session, sale_id: int):
    return db.scalar(
        select(models.Sale)
        .options(
            joinedload(models.Sale.items)
            .joinedload(models.SaleItem.product)
        )
        .where(models.Sale.id == sale_id)
    )