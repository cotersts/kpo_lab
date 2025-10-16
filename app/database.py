from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./sales.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # только для SQLite + многопоточность Uvicorn
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# Зависимость FastAPI для транзакций
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
