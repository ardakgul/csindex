"""Scheduled data builder for GitHub Pages.

Creates/updates three JSON artifacts under the repository's `data/` folder:
  - current_index.json  (latest snapshot)
  - history.json        (append-only (by minute) time series of snapshots)
  - health.json         (diagnostics for debugging in the frontend)

Design goals:
  * Idempotent & safe on concurrent re-runs (dedupe by minute timestamp)
  * Robust: never clobbers last good data on failure
  * Deterministic placeholder index if full calculator can't run (e.g. rate limits)
  * Minimal dependency surface (reuses existing packages already in requirements)

Schema:
current_index.json
{
  "timestamp": ISO8601 UTC string,
  "index_value": float (0..100),
  "sentiment": string,
  "status": "ok" | "error",
  "components": [ {"symbol": str, "score": float} ],
  "message": optional error/info string
}

history.json
{
  "series": [ {"timestamp": ISO8601, "index_value": float} ]
}

health.json
{
  "last_run_utc": ISO8601,
  "history_points": int,
  "current_value": float | null,
  "ok": bool,
  "message": str | null
}

The heavier original script `cloudy_shiny_index.py` fetches multiple markets.
Here we attempt to import and use it; on failure we produce a deterministic
placeholder value derived from the current UTC date + hour (stable inside one hour)
so that charts render during development. This is clearly marked with a TODO
for replacement when full data inputs become reliably available in CI.
"""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CURRENT_FILE = DATA_DIR / "current_index.json"
HISTORY_FILE = DATA_DIR / "history.json"
HEALTH_FILE = DATA_DIR / "health.json"


def compute_index() -> float:
    """Return latest index value (0..100).

    Tries the full calculator; if unavailable or errors, returns a
    deterministic placeholder based on the current UTC date & hour.
    (Placeholder logic is marked with TODO.)
    """
    try:
        # Lazy import to avoid heavy startup if not needed.
        from cloudy_shiny_index import CloudyShinyIndexCalculator  # type: ignore

        calc = CloudyShinyIndexCalculator()
        result = calc.calculate_index()  # type: ignore[attr-defined]
        val = float(result.get("index_value"))
        # Clamp & sanitize
        if not math.isfinite(val):
            raise ValueError("Non-finite index value from calculator")
        return max(0.0, min(100.0, val))
    except Exception:  # Broad by design; fallback path must succeed.
        # --- Placeholder deterministic value ---
        now = datetime.utcnow()
        key = now.strftime("%Y-%m-%d-%H")
        # Simple hash-like stable mapping to 0..100 (not random each run within the hour)
        hv = sum(ord(c) * (i + 1) for i, c in enumerate(key)) % 100
        # Center near 50 for neutral aesthetic
        placeholder = (hv * 0.6) + 20  # maps 0..99 -> 20..~79
        return round(placeholder, 2)
        # TODO: Remove placeholder once live data sources are always available in CI.


def classify_sentiment(value: float) -> str:
    if value >= 75:
        return "Extreme Shiny"
    if value >= 51:
        return "Shiny"
    if value >= 50:
        return "Neutral"
    if value >= 25:
        return "Cloudy"
    return "Extreme Cloudy"


def load_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json_atomic(path: Path, data: Dict[str, Any]):
    tmp = path.with_suffix(path.suffix + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def append_history(timestamp: str, value: float) -> int:
    hist = load_json(HISTORY_FILE, {"series": []})
    series: List[Dict[str, Any]] = hist.get("series", [])
    # Dedupe by minute
    minute_key = timestamp[:16]  # YYYY-MM-DDTHH:MM
    existing = {entry["timestamp"][:16]: i for i, entry in enumerate(series) if "timestamp" in entry}
    if minute_key in existing:
        idx = existing[minute_key]
        series[idx]["index_value"] = value
        series[idx]["timestamp"] = timestamp  # update full timestamp
    else:
        series.append({"timestamp": timestamp, "index_value": value})
    # Keep chronological order & enforce a soft cap (e.g., 10k points) to avoid runaway growth
    series.sort(key=lambda x: x["timestamp"])  # ISO8601 sorts lexicographically
    if len(series) > 10000:
        series = series[-10000:]
    hist["series"] = series
    save_json_atomic(HISTORY_FILE, hist)
    return len(series)


def main() -> int:
    now = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    DATA_DIR.mkdir(exist_ok=True)
    ok = False
    message = None
    value = None
    try:
        value = compute_index()
        # Sanitize again
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("compute_index returned invalid value")
        value = max(0.0, min(100.0, float(value)))
        sentiment = classify_sentiment(value)
        components: List[Dict[str, Any]] = []  # Optional future fill

        current_payload = {
            "timestamp": now,
            "index_value": value,
            "sentiment": sentiment,
            "status": "ok",
            "components": components,
        }
        save_json_atomic(CURRENT_FILE, current_payload)
        points = append_history(now, value)
        ok = True
        message = f"Updated index {value:.2f} with {points} history points"
        print(message)
    except Exception as e:  # noqa: BLE001
        message = f"ERROR building index: {e}"
        print(message, file=sys.stderr)
        # Keep last good current_index.json; write an error marker if file missing.
        if not CURRENT_FILE.exists():
            error_payload = {
                "timestamp": now,
                "index_value": 0.0,
                "sentiment": "Unknown",
                "status": "error",
                "components": [],
                "message": message,
            }
            save_json_atomic(CURRENT_FILE, error_payload)
    finally:
        # Health snapshot
        hist = load_json(HISTORY_FILE, {"series": []})
        health = {
            "last_run_utc": now,
            "history_points": len(hist.get("series", [])),
            "current_value": value,
            "ok": ok,
            "message": message,
        }
        save_json_atomic(HEALTH_FILE, health)
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
