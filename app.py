from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, Float, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional

# Initialize FastAPI app
app = FastAPI(title="FastAPI Demo with In-Memory SQLite",
              description="REST API with SQLAlchemy in-memory database",
              version="1.0.0")

# SQLAlchemy setup with in-memory SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# SQLAlchemy model
class ItemModel(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(String(500), nullable=True)
    price = Column(Float)


# Create tables in the database
Base.metadata.create_all(bind=engine)


# Pydantic models for request/response
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

    class Config:
        orm_mode = True


class ItemCreate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: int


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Seed some data
def seed_data():
    db = SessionLocal()
    sample_items = [
        ItemModel(name="Laptop", description="A powerful laptop for development", price=1299.99),
        ItemModel(name="Smartphone", description="Latest smartphone model", price=899.99),
        ItemModel(name="Headphones", description="Noise-cancelling headphones", price=249.99)
    ]
    for item in sample_items:
        db.add(item)
    db.commit()
    db.close()


# Call the seed function
seed_data()


# API Endpoints
@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to FastAPI with SQLite in-memory database!"}


@app.get("/items", response_model=List[ItemResponse], status_code=status.HTTP_200_OK, tags=["Items"])
async def get_all_items(db: Session = Depends(get_db)):
    items = db.query(ItemModel).all()
    return items


@app.get("/items/{item_id}", response_model=ItemResponse, status_code=status.HTTP_200_OK, tags=["Items"])
async def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )
    return item


@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED, tags=["Items"])
async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    new_item = ItemModel(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@app.put("/items/{item_id}", response_model=ItemResponse, status_code=status.HTTP_200_OK, tags=["Items"])
async def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )

    # Update item attributes
    for key, value in item.model_dump().items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Items"])
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )

    db.delete(db_item)
    db.commit()
    return None


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)