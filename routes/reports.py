from fastapi import APIRouter, HTTPException, Depends, Request
from utils.auth_utils import require_admin
from datetime import datetime, timedelta
from bson import ObjectId

router = APIRouter()

@router.get("/stats")
async def get_stats(request: Request, admin: dict = Depends(require_admin)):
    db = request.app.state.db
    
    # Count totals
    total_users = await db.users.count_documents({"role": "user"})
    total_products = await db.products.count_documents({})
    total_bookings = await db.bookings.count_documents({})
    
    # Count by status
    pending_bookings = await db.bookings.count_documents({"status": "pending"})
    confirmed_bookings = await db.bookings.count_documents({"status": "confirmed"})
    completed_bookings = await db.bookings.count_documents({"status": "completed"})
    
    # Calculate total revenue
    total_revenue = 0
    async for payment in db.payments.find({"status": "completed"}):
        total_revenue += payment.get("amount", 0)
    
    # Calculate pending revenue
    pending_revenue = 0
    async for payment in db.payments.find({"status": "pending"}):
        pending_revenue += payment.get("amount", 0)
    
    return {
        "users": {
            "total": total_users
        },
        "products": {
            "total": total_products,
            "available": await db.products.count_documents({"status": "available"}),
            "unavailable": await db.products.count_documents({"status": "unavailable"})
        },
        "bookings": {
            "total": total_bookings,
            "pending": pending_bookings,
            "confirmed": confirmed_bookings,
            "completed": completed_bookings
        },
        "revenue": {
            "total": total_revenue,
            "pending": pending_revenue,
            "completed": total_revenue
        }
    }

@router.get("/revenue")
async def get_revenue_data(request: Request, admin: dict = Depends(require_admin)):
    db = request.app.state.db
    
    # Get revenue for last 12 months
    revenue_data = []
    
    for i in range(12):
        date = datetime.utcnow() - timedelta(days=30 * i)
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if i == 0:
            month_end = datetime.utcnow()
        else:
            month_end = month_start + timedelta(days=31)
            month_end = month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate revenue for the month
        monthly_revenue = 0
        async for payment in db.payments.find({
            "status": "completed",
            "created_at": {"$gte": month_start, "$lt": month_end}
        }):
            monthly_revenue += payment.get("amount", 0)
        
        revenue_data.insert(0, {
            "month": month_start.strftime("%b %Y"),
            "revenue": monthly_revenue
        })
    
    return revenue_data

@router.get("/bookings-trend")
async def get_bookings_trend(request: Request, admin: dict = Depends(require_admin)):
    db = request.app.state.db
    
    # Get bookings for last 30 days
    trend_data = []
    
    for i in range(30):
        date = datetime.utcnow() - timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        # Count bookings for the day
        daily_bookings = await db.bookings.count_documents({
            "created_at": {"$gte": day_start, "$lt": day_end}
        })
        
        trend_data.insert(0, {
            "date": day_start.strftime("%Y-%m-%d"),
            "bookings": daily_bookings
        })
    
    return trend_data

@router.get("/popular-products")
async def get_popular_products(request: Request, admin: dict = Depends(require_admin)):
    db = request.app.state.db
    
    # Aggregate bookings by product
    product_bookings = {}
    
    async for booking in db.bookings.find():
        product_id = booking["product_id"]
        if product_id not in product_bookings:
            product_bookings[product_id] = 0
        product_bookings[product_id] += booking.get("quantity", 1)
    
    # Get product details and sort
    popular = []
    for product_id, count in product_bookings.items():
        try:
            product = await db.products.find_one({"_id": ObjectId(product_id)})
            if product:
                popular.append({
                    "id": str(product["_id"]),
                    "name": product["name"],
                    "bookings": count,
                    "revenue": count * product["price"]
                })
        except:
            continue
    
    # Sort by bookings count
    popular.sort(key=lambda x: x["bookings"], reverse=True)
    
    return popular[:10]  # Return top 10
