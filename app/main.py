from fastapi import FastAPI
import json
import os
from .tasks import simulate_match_task

app = FastAPI()

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "league_state.json")

def load_data():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)

@app.get("/")
def home():
    return {"message": "Football Predictor API is Live"}

@app.get("/predict")
def predict(home_team: str, away_team: str):
    data = load_data()
    
    if home_team not in data or away_team not in data:
        return {"error": "One or both teams not found in league data."}

    home_stats = data[home_team]
    away_stats = data[away_team]

    # Hand off the heavy lifting to the Celery Worker (Person B's muscle)
    task = simulate_match_task.delay(home_stats, away_stats)
    
    return {
        "status": "Simulation Started",
        "task_id": task.id,
        "message": f"Simulating 10,000 matches between {home_team} and {away_team}"
    }