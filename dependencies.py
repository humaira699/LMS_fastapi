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

# import serializer
SECRET_KEY = "Ahng^7*(><iog"
serializer = URLSafeTimedSerializer(SECRET_KEY)

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.lms

async def get_current_user(request: Request):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return None
    try:
        data = serializer.loads(session_cookie)
    except BadSignature:
        return None
    user = await db.users.find_one({"_id": ObjectId(data.get("user_id"))})
    if not user:
        return None
    return user