from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PaymentCreate(BaseModel):
    booking_id: str
    amount: float
    method: str
    notes: Optional[str] = None

class PaymentUpdate(BaseModel):
    status: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None

class PaymentResponse(BaseModel):
    id: str
    booking_id: str
    amount: float
    method: str
    status: str
    transaction_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
