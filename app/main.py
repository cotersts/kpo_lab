from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import date
import logging

from .database import Base, engine, get_db
from . import models, crud, schemas

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Appliance Store Sales System",
    version="0.1.0",
    description="Система учета продаж магазина бытовой техники с валидацией данных"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальный обработчик ошибок
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"},
    )

# --- API Routes ---

@app.post("/api/products", 
          response_model=schemas.Product, 
          status_code=201, 
          tags=["products"],
          summary="Создать новый товар",
          description="Создает новый товар с валидацией данных")
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_product(db, payload)
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        raise

@app.get("/api/products", 
         response_model=list[schemas.Product], 
         tags=["products"],
         summary="Получить список товаров",
         description="Возвращает список товаров с возможностью поиска")
def list_products(q: str | None = None, db: Session = Depends(get_db)):
    try:
        # Валидация поискового запроса
        if q and len(q.strip()) > 100:
            raise HTTPException(
                status_code=400,
                detail="Поисковый запрос слишком длинный (максимум 100 символов)"
            )
        return crud.list_products(db, q.strip() if q else None)
    except Exception as e:
        logger.error(f"Error listing products: {str(e)}")
        raise

@app.get("/api/products/{product_id}", 
         response_model=schemas.Product, 
         tags=["products"],
         summary="Получить товар по ID",
         description="Возвращает информацию о товаре по его ID")
def get_product(product_id: int, db: Session = Depends(get_db)):
    try:
        obj = crud.get_product(db, product_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Товар не найден")
        return obj
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {str(e)}")
        raise

@app.patch("/api/products/{product_id}", 
           response_model=schemas.Product, 
           tags=["products"],
           summary="Обновить товар",
           description="Обновляет информацию о товаре с валидацией данных")
def update_product(product_id: int, payload: schemas.ProductUpdate, db: Session = Depends(get_db)):
    try:
        obj = crud.update_product(db, product_id, payload)
        if not obj:
            raise HTTPException(status_code=404, detail="Товар не найден")
        return obj
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {str(e)}")
        raise

@app.delete("/api/products/{product_id}", 
            status_code=204, 
            tags=["products"],
            summary="Удалить товар",
            description="Удаляет товар, если он не используется в продажах")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    try:
        ok = crud.delete_product(db, product_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Товар не найден")
        return None
    except Exception as e:
        logger.error(f"Error deleting product {product_id}: {str(e)}")
        raise

@app.post("/api/sales", 
          response_model=schemas.Sale, 
          status_code=201, 
          tags=["sales"],
          summary="Создать продажу",
          description="Создает новую продажу с валидацией товаров и количеств")
def create_sale(payload: schemas.SaleCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_sale(db, payload)
    except Exception as e:
        logger.error(f"Error creating sale: {str(e)}")
        raise

@app.get("/api/sales", 
         response_model=list[schemas.Sale], 
         tags=["sales"],
         summary="Получить список продаж",
         description="Возвращает список продаж с фильтрацией по датам")
def list_sales(
    date_from: date | None = None, 
    date_to: date | None = None, 
    db: Session = Depends(get_db)
):
    try:
        return crud.list_sales(db, date_from, date_to)
    except Exception as e:
        logger.error(f"Error listing sales: {str(e)}")
        raise

@app.get("/api/sales/daily-summary", 
         response_model=schemas.DailySummary, 
         tags=["sales"],
         summary="Получить дневную статистику",
         description="Возвращает количество продаж и выручку за указанный день")
def get_daily_summary(day: date, db: Session = Depends(get_db)):
    try:
        count, revenue = crud.daily_summary(db, day)
        return schemas.DailySummary(date=day, sales_count=count, revenue=revenue)
    except Exception as e:
        logger.error(f"Error getting daily summary for {day}: {str(e)}")
        raise

# Добавим новые endpoints для клиентов
@app.post("/api/customers", 
          response_model=schemas.Customer, 
          status_code=201, 
          tags=["customers"],
          summary="Создать нового клиента",
          description="Создает нового клиента с валидацией данных")
def create_customer(payload: schemas.CustomerCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_customer(db, payload)
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise

@app.get("/api/customers", 
         response_model=list[schemas.Customer], 
         tags=["customers"],
         summary="Получить список клиентов",
         description="Возвращает список всех клиентов")
def list_customers(db: Session = Depends(get_db)):
    try:
        return crud.list_customers(db)
    except Exception as e:
        logger.error(f"Error listing customers: {str(e)}")
        raise

@app.get("/api/health", tags=["health"])
def health_check():
    return {"ok": True, "service": "appliance_store_sales", "version": "0.1.0"}

# Подключаем статику в самом конце
app.mount("/", StaticFiles(directory="static", html=True), name="static")