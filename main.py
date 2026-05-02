from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer, BadSignature

from database import init_db, SessionLocal, get_db
from models import User, Food, LogEntry

app = FastAPI(title="Food Intaker")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()
SECRET_KEY = os.environ["SECRET_KEY"]
TOKEN_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def make_token(user_id: int) -> str:
    return URLSafeTimedSerializer(SECRET_KEY).dumps(user_id)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        user_id = URLSafeTimedSerializer(SECRET_KEY).loads(
            credentials.credentials, max_age=TOKEN_MAX_AGE
        )
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.on_event("startup")
def startup():
    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            user = User(id=1, name="default")
            db.add(user)
            db.commit()
            db.refresh(user)
        if not user.email:
            user.email = "wpaoli@gmail.com"  # type: ignore[assignment]
            user.hashed_password = pwd_context.hash("12345!")  # type: ignore[assignment]
            db.commit()
    finally:
        db.close()


@app.get("/status", tags=["meta"])
def status():
    return {"status": "ok"}


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str


@app.post("/login", tags=["auth"])
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not user.hashed_password or not pwd_context.verify(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"token": make_token(user.id)}


@app.post("/register", tags=["auth"])
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).count() >= 3:
        raise HTTPException(status_code=403, detail="User limit reached")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        name=body.email.split("@")[0],
        email=body.email,
        hashed_password=pwd_context.hash(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": make_token(user.id)}


# ── Foods ─────────────────────────────────────────────────────────────────────

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
        food.name = body.food_name  # type: ignore[assignment]
    if body.calories is not None:
        food.calories_per_serving = body.calories  # type: ignore[assignment]
    if body.protein is not None:
        food.protein_per_serving = body.protein  # type: ignore[assignment]
    if body.carbs is not None:
        food.carbs_per_serving = body.carbs  # type: ignore[assignment]
    if body.fat is not None:
        food.fat_per_serving = body.fat  # type: ignore[assignment]

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


# ── Log ───────────────────────────────────────────────────────────────────────

class CreateLogRequest(BaseModel):
    food_id: int
    serving: float


@app.post("/log", tags=["log"])
def create_log(
    body: CreateLogRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    food = db.query(Food).filter(Food.id == body.food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    entry = LogEntry(
        user_id=current_user.id,
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
def quick_log(
    body: QuickLogRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = LogEntry(
        user_id=current_user.id,
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
def get_report(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(LogEntry, Food)
        .outerjoin(Food, LogEntry.food_id == Food.id)
        .filter(LogEntry.user_id == current_user.id)
    )
    if start:
        query = query.filter(LogEntry.logged_at >= start)
    if end:
        query = query.filter(LogEntry.logged_at <= end)

    total_calories = total_protein = total_carbs = total_fat = 0.0
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
def get_log(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(LogEntry, Food)
        .outerjoin(Food, LogEntry.food_id == Food.id)
        .filter(LogEntry.user_id == current_user.id)
    )
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


# ── Settings ──────────────────────────────────────────────────────────────────

class UpdateSettingsRequest(BaseModel):
    protein_target: Optional[float] = None
    calories_target: Optional[float] = None
    carbs_target: Optional[float] = None
    fat_target: Optional[float] = None


@app.get("/settings", tags=["meta"])
def get_settings(
    current_user: User = Depends(get_current_user),
):
    return {
        "protein_target": current_user.protein_target,
        "calories_target": current_user.calories_target,
        "carbs_target": current_user.carbs_target,
        "fat_target": current_user.fat_target,
    }


@app.patch("/settings", tags=["meta"])
def update_settings(
    body: UpdateSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.protein_target = body.protein_target  # type: ignore[assignment]
    current_user.calories_target = body.calories_target  # type: ignore[assignment]
    current_user.carbs_target = body.carbs_target  # type: ignore[assignment]
    current_user.fat_target = body.fat_target  # type: ignore[assignment]
    db.commit()
    db.refresh(current_user)
    return {
        "protein_target": current_user.protein_target,
        "calories_target": current_user.calories_target,
        "carbs_target": current_user.carbs_target,
        "fat_target": current_user.fat_target,
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")
