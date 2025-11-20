from fastapi import APIRouter, HTTPException, Depends, Request
from models.payment import PaymentCreate, PaymentUpdate, PaymentResponse
from utils.auth_utils import get_current_user, require_admin
from bson import ObjectId
from datetime import datetime
from typing import List
import uuid

router = APIRouter()

@router.get("/", response_model=List[PaymentResponse])
async def get_payments(request: Request, current_user: dict = Depends(get_current_user)):
    db = request.app.state.db
    payments = []
    
    # Admin sees all, users see only their own
    if current_user["role"] == "admin":
        query = {}
    else:
        # Get user's bookings first
        user_bookings = []
        async for booking in db.bookings.find({"user_id": current_user["user_id"]}):
            user_bookings.append(str(booking["_id"]))
        query = {"booking_id": {"$in": user_bookings}}
    
    async for payment in db.payments.find(query):
        payments.append({
            "id": str(payment["_id"]),
            "booking_id": payment["booking_id"],
            "amount": payment["amount"],
            "method": payment["method"],
            "status": payment["status"],
            "transaction_id": payment.get("transaction_id"),
            "notes": payment.get("notes"),
            "created_at": payment.get("created_at")
        })
    
    return payments

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    db = request.app.state.db
    
    try:
        payment = await db.payments.find_one({"_id": ObjectId(payment_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid payment ID")
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Check ownership for non-admin users
    if current_user["role"] != "admin":
        booking = await db.bookings.find_one({"_id": ObjectId(payment["booking_id"])})
        if not booking or booking["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "id": str(payment["_id"]),
        "booking_id": payment["booking_id"],
        "amount": payment["amount"],
        "method": payment["method"],
        "status": payment["status"],
        "transaction_id": payment.get("transaction_id"),
        "notes": payment.get("notes"),
        "created_at": payment.get("created_at")
    }

@router.post("/", response_model=PaymentResponse)
async def create_payment(payment: PaymentCreate, request: Request, current_user: dict = Depends(get_current_user)):
    db = request.app.state.db
    
    # Check if booking exists
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(payment.booking_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid booking ID")
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check ownership
    if current_user["role"] != "admin" and booking["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if payment already exists
    existing_payment = await db.payments.find_one({"booking_id": payment.booking_id})
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment already exists for this booking")
    
    # Generate transaction ID
    transaction_id = f"TRX-{uuid.uuid4().hex[:12].upper()}"
    
    payment_doc = {
        "booking_id": payment.booking_id,
        "amount": payment.amount,
        "method": payment.method,
        "status": "pending",
        "transaction_id": transaction_id,
        "notes": payment.notes,
        "created_at": datetime.utcnow()
    }
    
    result = await db.payments.insert_one(payment_doc)
    
    return {
        "id": str(result.inserted_id),
        "booking_id": payment.booking_id,
        "amount": payment.amount,
        "method": payment.method,
        "status": "pending",
        "transaction_id": transaction_id,
        "notes": payment.notes,
        "created_at": payment_doc["created_at"]
    }

@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(payment_id: str, payment: PaymentUpdate, request: Request, admin: dict = Depends(require_admin)):
    db = request.app.state.db
    
    try:
        obj_id = ObjectId(payment_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid payment ID")
    
    # Get existing payment
    existing = await db.payments.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Update only provided fields
    update_data = {k: v for k, v in payment.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.payments.update_one({"_id": obj_id}, {"$set": update_data})
    
    # If payment is confirmed, update booking status
    if payment.status == "completed":
        await db.bookings.update_one(
            {"_id": ObjectId(existing["booking_id"])},
            {"$set": {"status": "confirmed"}}
        )
    
    # Get updated payment
    updated = await db.payments.find_one({"_id": obj_id})
    
    return {
        "id": str(updated["_id"]),
        "booking_id": updated["booking_id"],
        "amount": updated["amount"],
        "method": updated["method"],
        "status": updated["status"],
        "transaction_id": updated.get("transaction_id"),
        "notes": updated.get("notes"),
        "created_at": updated.get("created_at")
    }

@router.delete("/{payment_id}")
async def delete_payment(payment_id: str, request: Request, admin: dict = Depends(require_admin)):
    db = request.app.state.db
    
    try:
        obj_id = ObjectId(payment_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid payment ID")
    
    result = await db.payments.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {"message": "Payment deleted successfully"}
