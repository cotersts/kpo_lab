from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

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

class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int = 1
    unit_price: float

class SaleCreate(BaseModel):
    customer_id: Optional[int] = None
    items: List[SaleItemCreate]

class Sale(BaseModel):
    id: int
    sale_date: datetime
    customer_id: Optional[int] = None
    total_amount: float

    class Config:
        from_attributes = True

class DailySummary(BaseModel):
    date: datetime
    sales_count: int
    revenue: float
