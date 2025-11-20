from fastapi import APIRouter, HTTPException, Depends, Request
from models.user import UserResponse, UserUpdate
from utils.auth_utils import require_admin, hash_password
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def get_users(request: Request, admin: dict = Depends(require_admin)):
    db = request.app.state.db
    users = []
    
    async for user in db.users.find():
        users.append({
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "created_at": user.get("created_at")
        })
    
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, request: Request, admin: dict = Depends(require_admin)):
    db = request.app.state.db
    
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "created_at": user.get("created_at")
    }

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user: UserUpdate, request: Request, admin: dict = Depends(require_admin)):
    db = request.app.state.db
    
    try:
        obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    # Get existing user
    existing = await db.users.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if email is being changed and if it's already taken
    if user.email and user.email != existing["email"]:
        email_taken = await db.users.find_one({"email": user.email})
        if email_taken:
            raise HTTPException(status_code=400, detail="Email already taken")
    
    # Update only provided fields
    update_data = {k: v for k, v in user.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.users.update_one({"_id": obj_id}, {"$set": update_data})
    
    # Get updated user
    updated = await db.users.find_one({"_id": obj_id})
    
    return {
        "id": str(updated["_id"]),
        "email": updated["email"],
        "name": updated["name"],
        "role": updated["role"],
        "created_at": updated.get("created_at")
    }

@router.delete("/{user_id}")
async def delete_user(user_id: str, request: Request, admin: dict = Depends(require_admin)):
    db = request.app.state.db
    
    try:
        obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    # Prevent deleting yourself
    if user_id == admin["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    result = await db.users.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}
