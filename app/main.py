from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date

from .database import Base, engine, get_db
from . import models, crud, schemas

# Создаём таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Appliance Store Sales System", version="0.1.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routes ---

@app.post("/api/products", response_model=schemas.Product, status_code=201, tags=["products"])
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, payload)

@app.get("/api/products", response_model=list[schemas.Product], tags=["products"])
def list_products(q: str | None = None, db: Session = Depends(get_db)):
    return crud.list_products(db, q)

@app.get("/api/products/{product_id}", response_model=schemas.Product, tags=["products"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    obj = crud.get_product(db, product_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    return obj

@app.patch("/api/products/{product_id}", response_model=schemas.Product, tags=["products"])
def update_product(product_id: int, payload: schemas.ProductUpdate, db: Session = Depends(get_db)):
    obj = crud.update_product(db, product_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    return obj

@app.delete("/api/products/{product_id}", status_code=204, tags=["products"])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_product(db, product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Product not found")
    return None

@app.post("/api/sales", response_model=schemas.Sale, status_code=201, tags=["sales"])
def create_sale(payload: schemas.SaleCreate, db: Session = Depends(get_db)):
    return crud.create_sale(db, payload)

@app.get("/api/sales", response_model=list[schemas.Sale], tags=["sales"])
def list_sales(date_from: date | None = None, date_to: date | None = None, db: Session = Depends(get_db)):
    return crud.list_sales(db, date_from, date_to)

@app.get("/api/sales/daily-summary", response_model=schemas.DailySummary, tags=["sales"])
def get_daily_summary(day: date, db: Session = Depends(get_db)):
    count, revenue = crud.daily_summary(db, day)
    return schemas.DailySummary(date=day, sales_count=count, revenue=revenue)

@app.get("/api/health", tags=["health"])
def health_check():
    return {"ok": True, "service": "appliance_store_sales"}

# Подключаем статику в самом конце
app.mount("/", StaticFiles(directory="static", html=True), name="static")
