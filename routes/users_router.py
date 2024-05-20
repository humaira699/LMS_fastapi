from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import motor
from pydantic import BaseModel
import hashlib
import os
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi import Form, Request
from fastapi.templating import Jinja2Templates
import pydantic
import bson
from bson import ObjectId
from dependencies import get_current_user

router = APIRouter()

# Get the directory path of the current script (routes/users_router.py)
# current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the templates directory
# templates = os.path.join(current_dir, '..', 'templates')
templates = Jinja2Templates(directory="templates")
# print(templates)
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db(request: Request):
    return request.app.mongodb

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Pydantic models
class User(BaseModel):
    username: str
    password: str

class UserInDB(User):
    hashed_password: str

# Helper functions
async def verify_password(plain_password, hashed_password):
    return get_password_hash(plain_password) == hashed_password

# async def authenticate_user(username: str, password: str, db = Depends(get_db)):    
#     users_collection = db.users
#     user = await users_collection.find_one({"username": username})
#     if user and await verify_password(password, user['hashed_password']):
#         return user
#     return None

@router.get("/user-management")
async def user_management(request: Request, user=Depends(get_current_user), db=Depends(get_db)):
    if user:
        users_collection = db.users
        users = await users_collection.find().to_list(length=None)
        return templates.TemplateResponse("user_managment.html", {"request": request, "users": users, "display_table": bool(users)})
    return RedirectResponse("/login")
    
@router.post("/register")
async def register_user(request: Request, username: str = Form(...), password: str = Form(...), db=Depends(get_db), user=Depends(get_current_user)):
    users_collection = db.users
    # Hash the password
    hashed_password = get_password_hash(password)
    # Check if the username is already registered
    existing_user = await users_collection.find_one({"username": username})
    if existing_user:
        return templates.TemplateResponse("user_managment.html", 
                                           {"request": request, "error_message": "Username already registered"},
                                           status_code=400)        
    # Insert the new user into the database    
    await users_collection.insert_one({"username": username, "hashed_password": hashed_password})
    # Fetch all users from the database
    all_users = await users_collection.find().to_list(length=None)

    # Return the user_management.html template with all users
    return templates.TemplateResponse("user_managment.html", 
                                   {"request": request, "display_table": True, "users": all_users},
                                   status_code=201)


@router.post("/update/{user_id}")
async def update_user(request: Request, user_id: str, username: str = Form(...), db=Depends(get_db)):
    # Find the user by user_id
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return templates.TemplateResponse("user_managment.html", 
                                           {"request": request, "error_message": "Username not found"},
                                           status_code=400)
    
    # Update the username
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"username": username}})

    # Fetch all users from the database
    users_cursor = db.users.find()
    users = await users_cursor.to_list(length=100)  # Adjust length as needed

    # Render the user management page with the success message
    success_message = f"User with ID {user_id} updated successfully"
    return templates.TemplateResponse("user_managment.html", 
                                      {"request": request, "users": users, "display_table": True, "success_message": success_message})


@router.get("/update/{user_id}")
async def update_user_page(user_id: str, request: Request, db=Depends(get_db)):
    # Fetch user data by ID
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        # If user not found, redirect with error message
         return templates.TemplateResponse("update_user.html", 
                                           {"request": request, "error_message": "Username not found"},
                                           status_code=400)
    return templates.TemplateResponse("update_user.html", {"request": request, "display_table": True, "user": user})


@router.post("/delete/{user_id}")
async def delete_user(request: Request, user_id: str, db=Depends(get_db)):
    # Find the user by user_id
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Delete the user
    await db.users.delete_one({"_id": ObjectId(user_id)})    
    success_message = f"User with Username {user["username"]} deleted successfully"    
    # Fetch all users from the database    
    users = await db.users.find().to_list(length=None)
    if users is None:
        # If user not found, redirect with error message
         return templates.TemplateResponse("user_managment.html", 
                                           {"request": request, "error_message": "No users found"},
                                           status_code=400)
    return templates.TemplateResponse("user_managment.html", {"request": request, "display_table": True, "users": users, "success_message": success_message})

