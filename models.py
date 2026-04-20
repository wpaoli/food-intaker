from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Food(Base):
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True)
    usda_fdc_id = Column(Integer, nullable=False, unique=True)
    name = Column(String, nullable=False)
    calories_per_100g = Column(Float, nullable=False)
    protein_per_100g = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=False)
    grams = Column(Float, nullable=False)
    logged_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
