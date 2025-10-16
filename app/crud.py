from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime, date
from . import models, schemas

# Products
def create_product(db: Session, data: schemas.ProductCreate) -> models.Product:
    obj = models.Product(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def list_products(db: Session, q: str | None = None):
    stmt = select(models.Product)
    if q:
        q_like = f"%{q}%"
        stmt = stmt.where(models.Product.name.ilike(q_like) | models.Product.sku.ilike(q_like))
    return db.scalars(stmt).all()

def get_product(db: Session, product_id: int):
    return db.get(models.Product, product_id)

def update_product(db: Session, product_id: int, data: schemas.ProductUpdate):
    obj = db.get(models.Product, product_id)
    if not obj:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

def delete_product(db: Session, product_id: int) -> bool:
    obj = db.get(models.Product, product_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True

# Customers
def create_customer(db: Session, data: schemas.CustomerCreate) -> models.Customer:
    obj = models.Customer(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def list_customers(db: Session):
    return db.scalars(select(models.Customer)).all()

# Sales
def create_sale(db: Session, data: schemas.SaleCreate) -> models.Sale:
    sale = models.Sale(customer_id=data.customer_id)
    db.add(sale)
    db.flush()  # получаем sale.id

    total = 0.0
    for item in data.items:
        si = models.SaleItem(
            sale_id=sale.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        total += item.quantity * item.unit_price
        db.add(si)

    sale.total_amount = total
    db.commit()
    db.refresh(sale)
    return sale

def list_sales(db: Session, date_from: date | None = None, date_to: date | None = None):
    stmt = select(models.Sale)
    if date_from:
        stmt = stmt.where(models.Sale.sale_date >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        stmt = stmt.where(models.Sale.sale_date < datetime.combine(date_to, datetime.min.time()))
    stmt = stmt.order_by(models.Sale.sale_date.desc())
    return db.scalars(stmt).all()

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
