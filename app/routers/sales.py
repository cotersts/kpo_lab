from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud

router = APIRouter(prefix="/sales", tags=["sales"])

@router.post("/", response_model=schemas.Sale, status_code=201)
def create_sale(payload: schemas.SaleCreate, db: Session = Depends(get_db)):
    return crud.create_sale(db, payload)

@router.get("/", response_model=list[schemas.Sale])
def list_sales(date_from: date | None = None, date_to: date | None = None, db: Session = Depends(get_db)):
    return crud.list_sales(db, date_from, date_to)

@router.get("/daily-summary", response_model=schemas.DailySummary)
def get_daily_summary(day: date, db: Session = Depends(get_db)):
    count, revenue = crud.daily_summary(db, day)
    return schemas.DailySummary(date=day, sales_count=count, revenue=revenue)
