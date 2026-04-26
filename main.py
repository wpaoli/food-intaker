from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import init_db, SessionLocal, get_db
from models import User, Food, LogEntry

app = FastAPI(title="Food Intaker")

@app.on_event("startup")
def startup():
    init_db()
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.id == 1).first():
            db.add(User(id=1, name="default"))
            db.commit()
    finally:
        db.close()


@app.get("/status", tags=["meta"])
def status():
    return {"status": "ok"}


class SaveFoodRequest(BaseModel):
    food_name: str
    calories: Optional[float] = None
    protein: Optional[float] = None


@app.get("/foods", tags=["foods"])
def list_foods(db: Session = Depends(get_db)):
    return db.query(Food).all()


@app.post("/foods", tags=["foods"])
def save_food(body: SaveFoodRequest, db: Session = Depends(get_db)):
    food = Food(
        name=body.food_name,
        calories_per_serving=body.calories,
        protein_per_serving=body.protein,
    )
    db.add(food)
    db.commit()
    db.refresh(food)
    return food


class CreateLogRequest(BaseModel):
    food_id: int
    serving: float
    logged_at: Optional[datetime] = None


@app.post("/log", tags=["log"])
def create_log(body: CreateLogRequest, db: Session = Depends(get_db)):
    food = db.query(Food).filter(Food.id == body.food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    entry = LogEntry(
        user_id=1,
        food_id=body.food_id,
        serving=body.serving,
        logged_at=body.logged_at or datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.get("/report", tags=["log"])
def get_report(start: Optional[datetime] = None, end: Optional[datetime] = None, db: Session = Depends(get_db)):
    query = db.query(LogEntry, Food).join(Food, LogEntry.food_id == Food.id)
    if start:
        query = query.filter(LogEntry.logged_at >= start)
    if end:
        query = query.filter(LogEntry.logged_at <= end)

    total_calories = 0.0
    total_protein = 0.0
    for entry, food in query.all():
        total_calories += entry.serving * (food.calories_per_serving or 0)
        total_protein += entry.serving * (food.protein_per_serving or 0)

    return {
        "total_calories": round(total_calories, 1),
        "total_protein": round(total_protein, 1),
        "start": start,
        "end": end,
    }


@app.get("/log", tags=["log"])
def get_log(start: Optional[datetime] = None, end: Optional[datetime] = None, db: Session = Depends(get_db)):
    query = db.query(LogEntry, Food).join(Food, LogEntry.food_id == Food.id)
    if start:
        query = query.filter(LogEntry.logged_at >= start)
    if end:
        query = query.filter(LogEntry.logged_at <= end)

    results = []
    for entry, food in query.all():
        results.append({
            "id": entry.id,
            "food_id": food.id,
            "food_name": food.name,
            "serving": entry.serving,
            "calories": round(entry.serving * (food.calories_per_serving or 0), 1),
            "protein": round(entry.serving * (food.protein_per_serving or 0), 1),
            "logged_at": entry.logged_at,
        })
    return results
