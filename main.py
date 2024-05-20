from fastapi import FastAPI, HTTPException, status, Depends
from routes import users_router, courses_router
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer, BadSignature
import hashlib
import bson
from bson import ObjectId
from dependencies import get_current_user
# Secret key for session management
SECRET_KEY = "sdsfe45456@21!!"
serializer = URLSafeTimedSerializer(SECRET_KEY)

app = FastAPI()

app.include_router(users_router.router, prefix="/users")
app.include_router(courses_router.router, prefix="/courses")
# Setup Jinja2Templates for HTML rendering
templates = Jinja2Templates(directory="templates")
# MongoDB setup
client = AsyncIOMotorClient("mongodb://localhost:27017")

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = client
    app.mongodb = client.lms

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

def get_db(request: Request):
    return request.app.mongodb
# Index page route
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.htm", {"request": request})

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()


# async def get_current_user(request: Request,  db=Depends(get_db)):
#     session_cookie = request.cookies.get("session")
#     if not session_cookie:
#         return None
#     try:
#         data = serializer.loads(session_cookie)
#     except BadSignature:
#         return None
#     user = await db.users.find_one({"_id": ObjectId(data.get("user_id"))})
#     if not user:
#         return None
#     return user

def require_login(user = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...), db = Depends(get_db)):
    user = await db.users.find_one({"username": username})
    if not user or user["hashed_password"] != get_password_hash(password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    session_data = {"user_id": str(user["_id"])}
    session_cookie = serializer.dumps(session_data)
    response.set_cookie("session", session_cookie)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("session")
    return response