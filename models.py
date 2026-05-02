from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    protein_target = Column(Float, nullable=True)
    calories_target = Column(Float, nullable=True)
    carbs_target = Column(Float, nullable=True)
    fat_target = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Food(Base):
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    calories_per_serving = Column(Float, nullable=True)
    protein_per_serving = Column(Float, nullable=True)
    carbs_per_serving = Column(Float, nullable=True)
    fat_per_serving = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=True)
    serving = Column(Float, nullable=True)
    note = Column(String, nullable=True)
    calories = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    carbs = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    logged_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
