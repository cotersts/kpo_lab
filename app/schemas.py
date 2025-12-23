from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr
from datetime import datetime, date
from typing import List, Optional
import re


# --- Product Schemas ---
class ProductBase(BaseModel):
    sku: str = Field(..., min_length=3, max_length=64, pattern=r'^[A-Za-z0-9\-_]+$',
                    examples=["TV-42-001"], description="Уникальный код товара")
    name: str = Field(..., min_length=2, max_length=255, 
                     examples=["Телевизор Samsung 43'"], description="Название товара")
    category: str = Field(..., min_length=2, max_length=100,
                         examples=["TV"], description="Категория товара")
    price: float = Field(..., gt=0, le=1000000,
                        examples=[39990.0], description="Цена товара (должна быть положительной)")

    @field_validator('sku')
    @classmethod
    def validate_sku(cls, v):
        if not re.match(r'^[A-Za-z0-9\-_]+$', v):
            raise ValueError('SKU может содержать только буквы, цифры, дефисы и подчеркивания')
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Название товара должно содержать минимум 2 символа')
        return v.strip()

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Цена должна быть положительной')
        if v > 1000000:  # Максимальная цена 1 миллион
            raise ValueError('Цена не может превышать 1 000 000')
        return round(v, 2)


class ProductCreate(ProductBase):
    pass


# В файле schemas.py обновите класс ProductUpdate:
class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=3, max_length=64, pattern=r'^[A-Za-z0-9\-_]+$')
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    price: Optional[float] = Field(None, gt=0, le=1000000)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('Название товара должно содержать минимум 2 символа')
        return v.strip() if v else v

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('Цена должна быть положительной')
            if v > 1000000:
                raise ValueError('Цена не может превышать 1 000 000')
            return round(v, 2)
        return v

    @field_validator('sku')
    @classmethod
    def validate_sku(cls, v):
        if v is not None:
            if not re.match(r'^[A-Za-z0-9\-_]+$', v):
                raise ValueError('SKU может содержать только буквы, цифры, дефисы и подчеркивания')
        return v


class Product(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- Customer Schemas ---
class CustomerBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255,
                     examples=["Иван Петров"], description="Имя клиента")
    phone: Optional[str] = Field(None, pattern=r'^(\+7|8)?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$',
                               examples=["+7-900-000-00-00"], description="Номер телефона в формате +7-XXX-XXX-XX-XX")
    email: Optional[EmailStr] = Field(None, examples=["ivan@example.com"], 
                                     description="Электронная почта")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Имя должно содержать минимум 2 символа')
        return v.strip()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            # Очищаем номер от пробелов и дефисов
            cleaned = re.sub(r'[\s\-\(\)]', '', v)
            if not re.match(r'^(\+7|8)\d{10}$', cleaned):
                raise ValueError('Неверный формат телефона. Используйте +7XXXXXXXXXX или 8XXXXXXXXXX')
            return v
        return v


class CustomerCreate(CustomerBase):
    pass


class Customer(CustomerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- Sale Schemas ---
class SaleItemBase(BaseModel):
    product_id: int = Field(..., gt=0, description="ID товара")
    quantity: int = Field(1, gt=0, le=100, 
                         description="Количество товара (от 1 до 100)")
    unit_price: float = Field(..., gt=0, le=1000000,
                             description="Цена за единицу (должна быть положительной)")

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Количество должно быть положительным')
        if v > 100:
            raise ValueError('Количество не может превышать 100')
        return v

    @field_validator('unit_price')
    @classmethod
    def validate_unit_price(cls, v):
        if v <= 0:
            raise ValueError('Цена за единицу должна быть положительной')
        if v > 1000000:
            raise ValueError('Цена за единицу не может превышать 1 000 000')
        return round(v, 2)


class SaleItemCreate(SaleItemBase):
    pass


class SaleItem(SaleItemBase):
    id: int
    product: Product
    model_config = ConfigDict(from_attributes=True)


class SaleCreate(BaseModel):
    customer_id: Optional[int] = Field(None, gt=0, description="ID клиента (опционально)")
    items: List[SaleItemCreate] = Field(..., min_length=1, max_length=20,
                                       description="Список товаров в продаже (от 1 до 20)")

    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if len(v) == 0:
            raise ValueError('Продажа должна содержать хотя бы один товар')
        if len(v) > 20:
            raise ValueError('Продажа не может содержать более 20 товаров')
        
        # Проверяем уникальность product_id в списке
        product_ids = [item.product_id for item in v]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError('Товары в продаже должны быть уникальными')
        
        return v


class Sale(BaseModel):
    id: int
    sale_date: datetime
    customer_id: Optional[int] = None
    total_amount: float
    items: List[SaleItem]
    model_config = ConfigDict(from_attributes=True)


class DailySummary(BaseModel):
    date: date
    sales_count: int = Field(..., ge=0, description="Количество продаж (неотрицательное)")
    revenue: float = Field(..., ge=0, description="Выручка (неотрицательная)")