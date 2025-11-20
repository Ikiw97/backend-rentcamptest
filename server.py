from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Import routes
from routes.auth import router as auth_router
from routes.products import router as products_router
from routes.bookings import router as bookings_router
from routes.payments import router as payments_router
from routes.users import router as users_router
from routes.reports import router as reports_router

load_dotenv()

# Database client
db_client = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_client, db
    db_client = AsyncIOMotorClient(os.getenv('MONGO_URI'))
    db = db_client.outdoorcamp
    app.state.db = db
    print("✅ Connected to MongoDB")
    
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.products.create_index("name")
    await db.bookings.create_index("user_id")
    await db.payments.create_index("booking_id")
    
    # Create default admin if not exists
    admin = await db.users.find_one({"email": "admin@outdoorcamp.id"})
    if not admin:
        from utils.auth_utils import hash_password
        await db.users.insert_one({
            "email": "admin@outdoorcamp.id",
            "name": "Admin",
            "password": hash_password("password123"),
            "role": "admin"
        })
        print("✅ Default admin created")
    
    yield
    
    # Shutdown
    db_client.close()
    print("❌ Disconnected from MongoDB")

app = FastAPI(
    title="OutdoorCamp API",
    description="Backend API untuk aplikasi rental camping",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(products_router, prefix="/api/products", tags=["Products"])
app.include_router(bookings_router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])

@app.get("/")
async def root():
    return {
        "message": "OutdoorCamp API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected" if db is not None else "disconnected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
