from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

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


class FoodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    calories_per_serving: Optional[float]
    protein_per_serving: Optional[float]
    carbs_per_serving: Optional[float]
    fat_per_serving: Optional[float]
    created_at: datetime


class SaveFoodRequest(BaseModel):
    food_name: str
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None


@app.get("/foods", tags=["foods"], response_model=list[FoodResponse])
def list_foods(db: Session = Depends(get_db)):
    return db.query(Food).all()


class UpdateFoodRequest(BaseModel):
    food_name: Optional[str] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None


@app.patch("/foods/{food_id}", tags=["foods"], response_model=FoodResponse)
def update_food(food_id: int, body: UpdateFoodRequest, db: Session = Depends(get_db)):
    food = db.query(Food).filter(Food.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    if body.food_name is not None:
        food.name = body.food_name
    if body.calories is not None:
        food.calories_per_serving = body.calories
    if body.protein is not None:
        food.protein_per_serving = body.protein
    if body.carbs is not None:
        food.carbs_per_serving = body.carbs
    if body.fat is not None:
        food.fat_per_serving = body.fat

    db.commit()
    db.refresh(food)
    return food


@app.post("/foods", tags=["foods"], response_model=FoodResponse)
def save_food(body: SaveFoodRequest, db: Session = Depends(get_db)):
    food = Food(
        name=body.food_name,
        calories_per_serving=body.calories,
        protein_per_serving=body.protein,
        carbs_per_serving=body.carbs,
        fat_per_serving=body.fat,
    )
    db.add(food)
    db.commit()
    db.refresh(food)
    return food


class CreateLogRequest(BaseModel):
    food_id: int
    serving: float


@app.post("/log", tags=["log"])
def create_log(body: CreateLogRequest, db: Session = Depends(get_db)):
    food = db.query(Food).filter(Food.id == body.food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    entry = LogEntry(
        user_id=1,
        food_id=body.food_id,
        serving=body.serving,
        logged_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


class QuickLogRequest(BaseModel):
    note: Optional[str] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None


@app.post("/log/quick", tags=["log"])
def quick_log(body: QuickLogRequest, db: Session = Depends(get_db)):
    entry = LogEntry(
        user_id=1,
        note=body.note,
        calories=body.calories,
        protein=body.protein,
        carbs=body.carbs,
        fat=body.fat,
        logged_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _entry_nutrition(entry, food):
    if food:
        factor = entry.serving or 0
        return (
            round(factor * (food.calories_per_serving or 0), 1),
            round(factor * (food.protein_per_serving or 0), 1),
            round(factor * (food.carbs_per_serving or 0), 1),
            round(factor * (food.fat_per_serving or 0), 1),
        )
    return (entry.calories or 0, entry.protein or 0, entry.carbs or 0, entry.fat or 0)


@app.get("/report", tags=["log"])
def get_report(start: Optional[datetime] = None, end: Optional[datetime] = None, db: Session = Depends(get_db)):
    query = db.query(LogEntry, Food).outerjoin(Food, LogEntry.food_id == Food.id)
    if start:
        query = query.filter(LogEntry.logged_at >= start)
    if end:
        query = query.filter(LogEntry.logged_at <= end)

    total_calories = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0
    for entry, food in query.all():
        cal, pro, carb, fat = _entry_nutrition(entry, food)
        total_calories += cal
        total_protein += pro
        total_carbs += carb
        total_fat += fat

    return {
        "total_calories": round(total_calories, 1),
        "total_protein": round(total_protein, 1),
        "total_carbs": round(total_carbs, 1),
        "total_fat": round(total_fat, 1),
        "start": start,
        "end": end,
    }


@app.get("/log", tags=["log"])
def get_log(start: Optional[datetime] = None, end: Optional[datetime] = None, db: Session = Depends(get_db)):
    query = db.query(LogEntry, Food).outerjoin(Food, LogEntry.food_id == Food.id)
    if start:
        query = query.filter(LogEntry.logged_at >= start)
    if end:
        query = query.filter(LogEntry.logged_at <= end)

    results = []
    for entry, food in query.all():
        cal, pro, carb, fat = _entry_nutrition(entry, food)
        results.append({
            "id": entry.id,
            "food_id": food.id if food else None,
            "food_name": food.name if food else (entry.note or "Quick entry"),
            "serving": entry.serving,
            "calories": cal,
            "protein": pro,
            "carbs": carb,
            "fat": fat,
            "logged_at": entry.logged_at,
        })
    return results


class UpdateSettingsRequest(BaseModel):
    protein_target: Optional[float] = None
    calories_target: Optional[float] = None
    carbs_target: Optional[float] = None
    fat_target: Optional[float] = None


@app.get("/settings", tags=["meta"])
def get_settings(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == 1).first()
    return {
        "protein_target": user.protein_target,
        "calories_target": user.calories_target,
        "carbs_target": user.carbs_target,
        "fat_target": user.fat_target,
    }


@app.patch("/settings", tags=["meta"])
def update_settings(body: UpdateSettingsRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == 1).first()
    user.protein_target = body.protein_target  # type: ignore[assignment]
    user.calories_target = body.calories_target  # type: ignore[assignment]
    user.carbs_target = body.carbs_target  # type: ignore[assignment]
    user.fat_target = body.fat_target  # type: ignore[assignment]
    db.commit()
    db.refresh(user)
    return {
        "protein_target": user.protein_target,
        "calories_target": user.calories_target,
        "carbs_target": user.carbs_target,
        "fat_target": user.fat_target,
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")
