# course_management
from fastapi import APIRouter, HTTPException, Depends, status, Request, Form
import motor
from bson import ObjectId
from pydantic import BaseModel
from fastapi.responses import JSONResponse  # Import JSONResponse
from fastapi.templating import Jinja2Templates
router = APIRouter()
templates = Jinja2Templates(directory="templates")
# Database setup - assuming the MongoClient instance is passed from the main app
def get_db(request: Request):
    return request.app.mongodb

class Course(BaseModel):
    name: str
    description: str
    instructor: str

@router.get("/course-management")
async def user_management(request: Request):
    return templates.TemplateResponse("course_managment.html", {"request": request})

# @router.post("/create/", status_code=status.HTTP_201_CREATED)
# async def create_course(course: Course, db=Depends(get_db)):
#     if await db.courses.find_one({"name": course.name}):
#         raise HTTPException(status_code=400, detail="Course already exists")
#     new_course = await db.courses.insert_one(course.dict())
#     created_course = await db.courses.find_one({"_id": new_course.inserted_id})
#     return created_course

@router.post("/create/", status_code=status.HTTP_201_CREATED)
async def create_course(request: Request, course_name: str = Form(...), course_description: str = Form(...), db=Depends(get_db)):
    if await db.courses.find_one({"name": course_name}):
        # raise HTTPException(status_code=400, detail="Course already exists")    
        return templates.TemplateResponse("course_managment.html", {"request": request, "error_message": "Course already exists"})
    # Insert the document into the collection
    new_course_result = await db.courses.insert_one({"name": course_name, "description": course_description})
    # Retrieve the inserted document using its _id
    inserted_id = new_course_result.inserted_id
    created_course = await db.courses.find_one({"_id": inserted_id})    
    # Convert ObjectId to string
    created_course['_id'] = str(created_course['_id'])
    return templates.TemplateResponse("course_managment.html", {"request": request, "course_name": created_course["name"], "course_description": created_course["description"]})
    # return JSONResponse(content=created_course)

@router.get("/courses/")
async def list_courses(db=Depends(get_db)):
    courses_cursor = db.courses.find()
    courses = []
    async for course in courses_cursor:
        # Convert ObjectId to string for JSON serialization
        course['_id'] = str(course['_id'])
        courses.append(course)
    return courses

@router.get("/courses/{course_id}")
async def get_course(course_id: str, db=Depends(get_db)):
    course = await db.courses.find_one({"_id": course_id})
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.put("/courses/{course_id}")
async def update_course(course_id: str, course: Course, db=Depends(get_db)):
    update_result = await db.courses.update_one({"_id": course_id}, {"$set": course.dict()})
    if update_result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return await db.courses.find_one({"_id": course_id})


