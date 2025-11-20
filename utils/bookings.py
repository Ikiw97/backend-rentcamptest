from fastapi import APIRouter, HTTPException, Depends, Request
from models.booking import BookingCreate, BookingUpdate, BookingResponse
from utils.auth_utils import get_current_user, require_admin
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter()

@router.get("/", response_model=List[BookingResponse])
async def get_bookings(request: Request, current_user: dict = Depends(get_current_user)):
    db = request.app.state.db
    bookings = []
    
    # Admin sees all, users see only their own
    query = {}
    if current_user["role"] != "admin":
        query["user_id"] = current_user["user_id"]
    
    async for booking in db.bookings.find(query):
        # Get product name
        product = await db.products.find_one({"_id": ObjectId(booking["product_id"])})
        product_name = product["name"] if product else "Unknown"
        
        bookings.append({
            "id": str(booking["_id"]),
            "user_id": booking["user_id"],
            "product_id": booking["product_id"],
            "product_name": product_name,
            "start_date": booking["start_date"],
            "end_date": booking["end_date"],
            "quantity": booking["quantity"],
            "total_price": booking["total_price"],
            "status": booking["status"],
            "notes": booking.get("notes"),
            "created_at": booking.get("created_at")
        })
    
    return bookings

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    db = request.app.state.db
    
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid booking ID")
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check ownership
    if current_user["role"] != "admin" and booking["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get product name
    product = await db.products.find_one({"_id": ObjectId(booking["product_id"])})
    product_name = product["name"] if product else "Unknown"
    
    return {
        "id": str(booking["_id"]),
        "user_id": booking["user_id"],
        "product_id": booking["product_id"],
        "product_name": product_name,
        "start_date": booking["start_date"],
        "end_date": booking["end_date"],
        "quantity": booking["quantity"],
        "total_price": booking["total_price"],
        "status": booking["status"],
        "notes": booking.get("notes"),
        "created_at": booking.get("created_at")
    }

@router.post("/", response_model=BookingResponse)
async def create_booking(booking: BookingCreate, request: Request, current_user: dict = Depends(get_current_user)):
    db = request.app.state.db
    
    # Get product
    try:
        product = await db.products.find_one({"_id": ObjectId(booking.product_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check stock
    if product["stock"] < booking.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    # Calculate total price (simplified: price * quantity)
    total_price = product["price"] * booking.quantity
    
    booking_doc = {
        "user_id": current_user["user_id"],
        "product_id": booking.product_id,
        "start_date": booking.start_date,
        "end_date": booking.end_date,
        "quantity": booking.quantity,
        "total_price": total_price,
        "status": "pending",
        "notes": booking.notes,
        "created_at": datetime.utcnow()
    }
    
    result = await db.bookings.insert_one(booking_doc)
    
    # Update stock
    await db.products.update_one(
        {"_id": ObjectId(booking.product_id)},
        {"$inc": {"stock": -booking.quantity}}
    )
    
    return {
        "id": str(result.inserted_id),
        "user_id": current_user["user_id"],
        "product_id": booking.product_id,
        "product_name": product["name"],
        "start_date": booking.start_date,
        "end_date": booking.end_date,
        "quantity": booking.quantity,
        "total_price": total_price,
        "status": "pending",
        "notes": booking.notes,
        "created_at": booking_doc["created_at"]
    }

@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(booking_id: str, booking: BookingUpdate, request: Request, current_user: dict = Depends(get_current_user)):
    db = request.app.state.db
    
    try:
        obj_id = ObjectId(booking_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid booking ID")
    
    # Get existing booking
    existing = await db.bookings.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check ownership (users can only update their own, admins can update all)
    if current_user["role"] != "admin" and existing["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update only provided fields
    update_data = {k: v for k, v in booking.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.bookings.update_one({"_id": obj_id}, {"$set": update_data})
    
    # Get updated booking
    updated = await db.bookings.find_one({"_id": obj_id})
    
    # Get product name
    product = await db.products.find_one({"_id": ObjectId(updated["product_id"])})
    product_name = product["name"] if product else "Unknown"
    
    return {
        "id": str(updated["_id"]),
        "user_id": updated["user_id"],
        "product_id": updated["product_id"],
        "product_name": product_name,
        "start_date": updated["start_date"],
        "end_date": updated["end_date"],
        "quantity": updated["quantity"],
        "total_price": updated["total_price"],
        "status": updated["status"],
        "notes": updated.get("notes"),
        "created_at": updated.get("created_at")
    }

@router.delete("/{booking_id}")
async def cancel_booking(booking_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    db = request.app.state.db
    
    try:
        obj_id = ObjectId(booking_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid booking ID")
    
    # Get booking
    booking = await db.bookings.find_one({"_id": obj_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check ownership
    if current_user["role"] != "admin" and booking["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Restore stock
    await db.products.update_one(
        {"_id": ObjectId(booking["product_id"])},
        {"$inc": {"stock": booking["quantity"]}}
    )
    
    # Delete booking
    await db.bookings.delete_one({"_id": obj_id})
    
    return {"message": "Booking cancelled successfully"}
