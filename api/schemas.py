# api/schemas.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class ProductBase(BaseModel):
    name: str
    category: str
    quantity: int
    unit_price: Optional[float] = None
    entry_date: date
    description: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str]
    category: Optional[str]
    quantity: Optional[int]
    unit_price: Optional[float]
    entry_date: Optional[date]
    description: Optional[str]

class ProductRead(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
