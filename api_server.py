"""Simple FastAPI server exposing Cloudy&Shiny Index data & ML prediction placeholder.

Run: python api_server.py
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import uvicorn
import threading
import time
from datetime import datetime, timezone
from cloudy_shiny_index import CloudyShinyIndexCalculator
from ml_forecast import advanced_forecast

DATA_DIR = Path('website/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Cloudy&Shiny Index API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_json(name: str, default):
    p = DATA_DIR / name
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text())
    except Exception:
        return default


@app.get("/api/index/current")
def current_index():
    return _read_json('current_index.json', {"status": "unavailable"})


@app.get("/api/index/history")
def index_history():
    return _read_json('history.json', {"series": []})


@app.get("/api/index/components")
def index_components():
    data = _read_json('current_index.json', {})
    return {"components": data.get('components', [])}


@app.get("/api/index/health")
def index_health():
    return _read_json('health.json', {"status": "unavailable"})


@app.get("/api/news/sentiment")
def news_sentiment():
    return _read_json('news_sentiment.json', {"score": None})


@app.get("/api/index/predict")
def predict(next_minutes: int = 60):
    """Advanced AR-based forecast (fallback to naive delta)."""
    hist = _read_json('history.json', {"series": []}).get('series', [])
    values = [p['index_value'] for p in hist if 'index_value' in p]
    if len(values) < 5:
        return {"prediction": values[-1] if values else None, "model": "insufficient-data", "look_ahead_minutes": next_minutes}
    fc = advanced_forecast(values, steps=1)
    fc["look_ahead_minutes"] = next_minutes
    return fc


@app.post("/api/index/recalculate")
def recalc():
    calc = CloudyShinyIndexCalculator()
    result = calc.calculate_index()
    calc.save_results(result)
    return {"status": "ok", "index_value": result['index_value']}


if __name__ == "__main__":
    # Start aligned scheduler thread
    def scheduler_loop():
        while True:
            now = datetime.now(timezone.utc)
            # Compute seconds until next :00 or :30 mark
            minute = now.minute
            next_minute = 30 if minute < 30 else 60
            wait_minutes = (next_minute - minute) if next_minute != 60 else (60 - minute)
            # target time at either XX:30 or next hour (XX+1:00)
            target = (now.replace(second=0, microsecond=0) + 
                      timedelta(minutes=wait_minutes))
            sleep_seconds = (target - datetime.now(timezone.utc)).total_seconds()
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            try:
                calc = CloudyShinyIndexCalculator()
                result = calc.calculate_index()
                calc.save_results(result)
            except Exception:
                pass
            # After execution, immediately compute next cycle

    from datetime import timedelta  # local import to keep top tidy
    threading.Thread(target=scheduler_loop, daemon=True).start()
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
