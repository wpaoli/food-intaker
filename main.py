from dotenv import load_dotenv
load_dotenv()

import os
import requests
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import init_db, SessionLocal, get_db
from models import User, Food

app = FastAPI()

USDA_BASE = "https://api.nal.usda.gov/fdc/v1"


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


@app.get("/health")
def health():
    return {"status": "ok"}


def _usda_key() -> str:
    key = os.getenv("USDA_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="USDA_API_KEY not configured")
    return key


def _extract_nutrient_search(nutrients: list, number: str) -> float:
    """Parse nutrients from /foods/search response."""
    for n in nutrients:
        if str(n.get("nutrientNumber", "")) == number:
            return float(n.get("value") or 0)
    return 0.0


def _extract_nutrient_detail(nutrients: list, number: str) -> float:
    """Parse nutrients from /food/{fdcId} response."""
    for n in nutrients:
        if str(n.get("nutrient", {}).get("number", "")) == number:
            return float(n.get("amount") or 0)
    return 0.0


@app.get("/foods/search")
def search_foods(q: str):
    key = _usda_key()
    resp = requests.get(
        f"{USDA_BASE}/foods/search",
        params={"api_key": key, "query": q, "pageSize": 5},
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for food in data.get("foods", []):
        nutrients = food.get("foodNutrients", [])
        results.append({
            "fdc_id": food["fdcId"],
            "name": food["description"],
            "data_type": food.get("dataType", ""),
            "calories_per_100g": _extract_nutrient_search(nutrients, "208"),
            "protein_per_100g": _extract_nutrient_search(nutrients, "203"),
        })
    return results


class SaveFoodRequest(BaseModel):
    fdc_id: int


@app.post("/foods")
def save_food(body: SaveFoodRequest, db: Session = Depends(get_db)):
    existing = db.query(Food).filter(Food.usda_fdc_id == body.fdc_id).first()
    if existing:
        return existing

    key = _usda_key()
    resp = requests.get(
        f"{USDA_BASE}/food/{body.fdc_id}",
        params={"api_key": key},
    )
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Food not found in USDA database")
    resp.raise_for_status()
    data = resp.json()

    nutrients = data.get("foodNutrients", [])
    food = Food(
        usda_fdc_id=body.fdc_id,
        name=data["description"],
        calories_per_100g=_extract_nutrient_detail(nutrients, "208"),
        protein_per_100g=_extract_nutrient_detail(nutrients, "203"),
    )
    db.add(food)
    db.commit()
    db.refresh(food)
    return food
