from fastapi import APIRouter, HTTPException, Depends, Request
from models.product import ProductCreate, ProductUpdate, ProductResponse
from utils.auth_utils import get_current_user, require_admin
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter()

@router.get("/", response_model=List[ProductResponse])
async def get_products(request: Request, current_user: dict = Depends(get_current_user)):
    db = request.app.state.db
    products = []
    
    async for product in db.products.find():
        products.append({
            "id": str(product["_id"]),
            "name": product["name"],
            "description": product["description"],
            "category": product["category"],
            "price": product["price"],
            "stock": product["stock"],
            "image": product.get("image"),
            "status": product["status"],
            "created_at": product.get("created_at")
        })
    
    return products

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    db = request.app.state.db
    
    try:
        product = await db.products.find_one({"_id": ObjectId(product_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": str(product["_id"]),
        "name": product["name"],
        "description": product["description"],
        "category": product["category"],
        "price": product["price"],
        "stock": product["stock"],
        "image": product.get("image"),
        "status": product["status"],
        "created_at": product.get("created_at")
    }

@router.post("/", response_model=ProductResponse)
async def create_product(product: ProductCreate, request: Request, admin: dict = Depends(require_admin)):
    db = request.app.state.db
    
    product_doc = {
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "price": product.price,
        "stock": product.stock,
        "image": product.image,
        "status": product.status,
        "created_at": datetime.utcnow()
    }
    
    result = await db.products.insert_one(product_doc)
    product_doc["id"] = str(result.inserted_id)
    
    return {
        "id": str(result.inserted_id),
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "price": product.price,
        "stock": product.stock,
        "image": product.image,
        "status": product.status,
        "created_at": product_doc["created_at"]
    }

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, product: ProductUpdate, request: Request, admin: dict = Depends(require_admin)):
    db = request.app.state.db
    
    try:
        obj_id = ObjectId(product_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    # Get existing product
    existing = await db.products.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update only provided fields
    update_data = {k: v for k, v in product.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.products.update_one({"_id": obj_id}, {"$set": update_data})
    
    # Get updated product
    updated = await db.products.find_one({"_id": obj_id})
    
    return {
        "id": str(updated["_id"]),
        "name": updated["name"],
        "description": updated["description"],
        "category": updated["category"],
        "price": updated["price"],
        "stock": updated["stock"],
        "image": updated.get("image"),
        "status": updated["status"],
        "created_at": updated.get("created_at")
    }

@router.delete("/{product_id}")
async def delete_product(product_id: str, request: Request, admin: dict = Depends(require_admin)):
    db = request.app.state.db
    
    try:
        obj_id = ObjectId(product_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    result = await db.products.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted successfully"}
