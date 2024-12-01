from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel, Field
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

app = FastAPI()

# MongoDB Configuration
MONGO_DETAILS = "mongodb+srv://vikasgole:bOaWIfVAw0aOIZPJ@cluster0.nffpa7w.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client["student_db"]
students_collection = database.get_collection("students")


# Helper function to parse MongoDB ObjectId
def student_helper(student) -> dict:
    return {
        "id": str(student["_id"]),
        "name": student["name"],
        "age": student["age"],
        "address": student["address"],
    }


# Request and Response Models
class Address(BaseModel):
    city: str
    country: str


class Student(BaseModel):
    name: str
    age: int
    address: Address


class UpdateStudent(BaseModel):
    name: Optional[str]
    age: Optional[int]
    address: Optional[Address]


# API Endpoints
@app.post("/students", status_code=201)
async def create_student(student: Student):
    student_dict = student.dict()
    result = await students_collection.insert_one(student_dict)
    return {"id": str(result.inserted_id)}


@app.get("/students", status_code=200)
async def list_students(
        country: Optional[str] = Query(
            None,
            description="Filter students by their country. If not provided, this filter will not be applied.",
        ),
        age: Optional[int] = Query(
            None,
            description="Filter students whose age is greater than or equal to the specified value. If not provided, this filter will not be applied.",
        ),
):
    """
    List students with optional filters.

    You can use the following filters:
    - **country**: Filter students by their country.
    - **age**: Only include students with age greater than or equal to the provided value.
    """
    query = {}
    if country:
        query["address.country"] = country
    if age is not None:
        query["age"] = {"$gte": age}
    students = await students_collection.find(query).to_list(1000)
    return {"data": [student_helper(student) for student in students]}


@app.get("/students/{id}", status_code=200)
async def fetch_student(id: str = Path(..., title="The ID of the student")):
    student = await students_collection.find_one({"_id": ObjectId(id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student_helper(student)


@app.patch("/students/{id}", status_code=200)
async def update_student(id: str, student: UpdateStudent):
    update_data = {k: v for k, v in student.dict().items() if v is not None}
    if update_data:
        result = await students_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Student not found")
    return {}


@app.delete("/students/{id}", status_code=200)
async def delete_student(id: str):
    result = await students_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"detail": "Student deleted successfully"}
