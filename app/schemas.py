from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List, Optional

# --- Product Schemas ---
class ProductBase(BaseModel):
    sku: str = Field(..., examples=["TV-42-001"])
    name: str
    category: str
    price: float

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None

class Product(ProductBase):
    id: int
    class Config:
        from_attributes = True

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int
    class Config:
        from_attributes = True

# --- Sale Schemas ---
class SaleItemBase(BaseModel):
    product_id: int
    quantity: int = 1
    unit_price: float

class SaleItemCreate(SaleItemBase):
    pass

# Новая схема для отображения SaleItem с деталями продукта
class SaleItem(SaleItemBase):
    id: int
    product: Product  # Включаем полную информацию о продукте

    class Config:
        from_attributes = True

class SaleCreate(BaseModel):
    customer_id: Optional[int] = None
    items: List[SaleItemCreate]

# Новая, более полная схема для отображения продажи
class Sale(BaseModel):
    id: int
    sale_date: datetime
    customer_id: Optional[int] = None
    total_amount: float
    items: List[SaleItem]  # Включаем список товаров

    class Config:
        from_attributes = True

class DailySummary(BaseModel):
    date: date
    sales_count: int
    revenue: float
