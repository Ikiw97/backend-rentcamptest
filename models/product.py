from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    description: str
    category: str
    price: float
    stock: int = 0
    image: Optional[str] = None
    status: str = "available"

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    image: Optional[str] = None
    status: Optional[str] = None

class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    price: float
    stock: int
    image: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
