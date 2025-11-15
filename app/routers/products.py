from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud

router = APIRouter(tags=["products"])

@router.post("/", response_model=schemas.Product, status_code=201)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, payload)

@router.get("/", response_model=list[schemas.Product])
def list_products(q: str | None = None, db: Session = Depends(get_db)):
    return crud.list_products(db, q)

@router.get("/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    obj = crud.get_product(db, product_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    return obj

@router.patch("/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, payload: schemas.ProductUpdate, db: Session = Depends(get_db)):
    obj = crud.update_product(db, product_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    return obj

@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_product(db, product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Product not found")
    return None
