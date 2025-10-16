from fastapi import FastAPI
from .database import Base, engine
from .routers import products, sales

# Создаём таблицы (для учебного проекта без миграций)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Appliance Store Sales System", version="0.1.0")

app.include_router(products.router)
app.include_router(sales.router)

@app.get("/")
def root():
    return {"ok": True, "service": "appliance_store_sales"}
