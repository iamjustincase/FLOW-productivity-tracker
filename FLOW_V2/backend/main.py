from fastapi import FastAPI
from core.focus_engine import get_today_data, calculate_daily_stats

app = FastAPI()

@app.get("/")
def home():
    return {"message": "FLOW API is running"}

@app.get("/stats/today")
def get_today_stats():
    stats = calculate_daily_stats()
    return stats