from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BookingCreate(BaseModel):
    product_id: str
    start_date: str
    end_date: str
    quantity: int = 1
    notes: Optional[str] = None

class BookingUpdate(BaseModel):
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    quantity: Optional[int] = None
    notes: Optional[str] = None

class BookingResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    product_name: Optional[str] = None
    start_date: str
    end_date: str
    quantity: int
    total_price: float
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
