# The Cloudy&Shiny Index: Global Market Sentiment Analysis

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/ardakgul/cloudyandshiny)

## Project Overview

The **Cloudy&Shiny Index** is a global market sentiment indicator that analyzes multiple international financial markets. June 2025 revision introduces GDP-adjusted weights and consolidates sentiment into an internal news component. The index provides a unified view of global market conditions on a scale from 0-100.

**Purpose:** Exploration of international market correlations and sentiment analysis

---

## What This Project Does

This Python-based system:
- Analyzes 12 market price components plus 1 sentiment component (13 total logical inputs)
- Calculates technical indicators (moving averages, RSI) for each component
- Combines market data with external sentiment indicators
- Produces a single sentiment score (0-100) with descriptive classification
- Updates in real-time during market hours

### Key Features:

1. **International Market Coverage**: Includes major markets from US, China, Japan, Hong Kong, Germany, France, and Turkey

2. **Sentiment Classification**: 5-level system from "Extreme Cloudy" (0-24) to "Extreme Shiny" (75-100)

3. **Weighted Approach**: GDP-adjusted weights reflecting economic size and market depth (see updated table below)

4. **Real-Time Processing**: Fetches live market data and updates sentiment calculations

## Technical Implementation

### Core Calculation Formula

```
Cloudy&Shiny_Index = Σ(Weight_i × Score_i) / Σ(Active Weights)
```

Where:
- `Weight_i` = Pre-assigned weight for each market component
- `Score_i` = Distance-based score calculated from technical indicators  
All sentiment now captured through the internal news sentiment component (NEWS_SENTIMENT) with an explicit weight. A Reuters Business RSS feed and an optional DistilBERT sentiment model (transformers) enrich headline scoring (graceful fallback if model unavailable).

### Distance-Based Scoring Method

```python
def distance_based_score(current, ma, max_deviation=0.20):
    """
    Calculate sentiment score based on price distance from moving average
    """
    diff_ratio = (current - ma) / ma
    normalized_diff = diff_ratio / max_deviation
    normalized_diff = max(-1, min(1, normalized_diff))
    score = 50 + (normalized_diff * 50)
    return score
```

This method converts price movements relative to moving averages into sentiment scores.

## Market Components & GDP-Adjusted Weights (June 2025)

| Symbol | Name | Weight | Notes |
|--------|------|--------|-------|
| SPY | S&P 500 | 0.159 | US equity (broad) |
| QQQ | NASDAQ 100 | 0.159 | US tech concentration |
| 000001.SS | Shanghai Composite | 0.205 | China equity |
| ^N225 | Nikkei 225 | 0.046 | Japan equity |
| ^HSI | Hang Seng | 0.004 | Hong Kong equity (reduced) |
| XU100.IS | BIST 100 | 0.012 | Turkey equity |
| ^GDAXI | DAX | 0.051 | Germany equity |
| ^FCHI | CAC 40 | 0.034 | France equity |
| ^VIX | Volatility Index | 0.10 | Inverse (risk) |
| TLT | US 20Y Treasury | 0.05 | Inverse (risk-off) |
| GLD | Gold | 0.06 | Inverse (safe haven) |
| DX-Y.NYB | US Dollar Index | 0.04 | Currency strength |
| NEWS_SENTIMENT | Aggregated News Sentiment | 0.08 | Internal sentiment |

Sum = 1.00

## Sentiment Classification

| Range | Classification | Description |
|-------|---------------|-------------|
| **75-100** | **Extreme Shiny** | Very bullish market conditions |
| **51-74** | **Shiny** | Bullish/positive sentiment |
| **50** | **Neutral** | Balanced market conditions |
| **25-49** | **Cloudy** | Bearish/negative sentiment |
| **0-24** | **Extreme Cloudy** | Very bearish market conditions |

## Installation & Usage

### Installation
```bash
# Clone the repository
git clone <repo-url>
cd cloudyandshiny-main

# (Option A) Reproducible environment
python -m venv .venv
".venv/Scripts/Activate.ps1"
pip install -r requirements-prod.txt

# (Option B) Flexible latest versions
pip install -r requirements.txt

# Run
python cloudy_shiny_index.py
```

### Quick CLI Output
Produces CSV/JSON in `data/` and updates `website/data/current_index.json`.

## Deployment Notes (Professor Package)

| Item | Purpose |
|------|---------|
| `cloudy_shiny_index.py` | Core calculator script |
| `requirements-prod.txt` | Pinned reproducible environment |
| `cloudy_shiny_index_documentation.tex/md` | Mathematical & methodology docs |
| `README.md` | Usage & deployment instructions |
| `website/data/current_index.json` | Latest index snapshot |
| `backend/` | FastAPI service exposing index & prediction endpoints |
| `ml/` | ML feature + training stubs |
| `Dockerfile` | Container build for API |
| `docker-compose.yml` | Orchestrates API + TimescaleDB |
| `.env.example` | Environment variable template |

Minimal run steps for evaluation:
1. Create virtual environment
2. `pip install -r requirements-prod.txt`
3. `python cloudy_shiny_index.py`
4. Inspect generated `data/*.json` and `website/data/current_index.json`

Optional: If transformer model download is slow, comment out the `transformers` lines; keyword sentiment will still function.

### API Quickstart (Docker)
```bash
docker build -t cloudy-index .
docker run -p 8000:8000 cloudy-index
# then open http://localhost:8000/index/current
```

### API Endpoints
- `GET /health` – service status
- `GET /index/current?force=true` – latest (re)calculated index
- `GET /index/history?limit=50` – recent historical snapshots
- `GET /model/predict` – placeholder prediction (to be replaced by ML model)


### Usage
```python
from cloudy_shiny_index import CloudyShinyIndexCalculator

# Create calculator instance
calculator = CloudyShinyIndexCalculator()

# Get current sentiment
result = calculator.calculate_index()
print(f"Current Index: {result['index_value']:.2f}")
print(f"Sentiment: {result['sentiment']}")
```

### Example Output
```json
{
  "timestamp": "2025-06-08T16:31:47+00:00",
  "index_value": 59.83,
  "sentiment": "Shiny",
  "active_components": 13,
  "total_components": 13
}
```

## Data Sources

- **Market Data**: Yahoo Finance API (yfinance)
- **News Sentiment**: Weighted keyword-based sentiment across multiple financial news sources

## Current Implementation Status

### Implemented Features
- Core sentiment calculation algorithm
- Real-time data fetching from multiple international markets
- Technical analysis indicators (MA, RSI, volatility)
- Integrated news sentiment component
- Web dashboard for visualization
- Data export (JSON/CSV)
-- (Removed) External Fear & Greed adjustment

### Future Enhancements
- Machine learning integration for improved prediction
- Advanced natural language processing for news sentiment
- Additional emerging markets
- Mobile application
- Backtesting framework
- Advanced statistical validation of GDP-adjusted weighting

## Disclaimer

This project is for educational and research purposes. The sentiment analysis provided should not be used for actual investment decisions. Always consult with qualified financial advisors before making investment choices.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Feel free to:
1. Fork the repository
2. Create a feature branch
3. Make your improvements
4. Submit a pull request

## Technical Resources

- [Python for Finance](https://www.python.org/)
- [Technical Analysis Concepts](https://www.investopedia.com/technical-analysis-4689657)
- [Yahoo Finance API](https://pypi.org/project/yfinance/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

---

**Note**: This project demonstrates financial data analysis techniques and international market integration for educational purposes.

## Backend API & Data Pipeline
The `backend` FastAPI service exposes:
- `GET /health`
- `GET /index/current?force=true`
- `GET /index/history?limit=100`
- `GET /model/predict` (placeholder)

Background scheduler recalculates hourly and persists to TimescaleDB if available (falls back to filesystem JSON snapshots).

### Run Locally (Dev)
```powershell
pip install -r requirements.txt
$env:POSTGRES_HOST="localhost"  # optional if DB running
python -m uvicorn backend.main:app --reload
```

### Docker Compose (API + TimescaleDB)
```powershell
docker compose up --build
```

TimescaleDB credentials are in `.env.example` (copy to `.env`).

## Frontend (React + Vite + Tailwind)
Located in `frontend/`.

### Dev Run
```powershell
cd frontend
npm install
npm run dev
```
Configure API base via `.env` (`VITE_API_BASE`).

### Build
```powershell
npm run build
```
Outputs to `dist/` (can be served by any static host or integrated behind reverse proxy with API).

## High-Level Architecture
- Python core index calculator (`cloudy_shiny_index.py`)
- FastAPI backend (`backend/`) with hourly background updates & TimescaleDB persistence
- ML pipeline stub (`ml/`) for future LSTM/Transformer hybrid
- React dashboard (`frontend/`) providing live index, history, components
- Docker / Compose for containerized deployment (API + DB)

### ML Model
Implemented PyTorch LSTM time-series forecaster (hourly / daily horizons). Features include lags, rolling means/std, volatility proxy, sentiment encoding. Trains with early stopping and persists under `models/`.

API:
- `POST /model/train` – train (if enough history)
- `GET /model/predict` – next hour + next day forecasts (auto-trains if no model)

If `torch` not installed, endpoints return 400 until dependency added.

### Rapid History Bootstrap (Synthetic)
To quickly create enough points for an initial LSTM train (synthetic, no real time spacing):

```powershell
python -m scripts.bootstrap_history --runs 50 --sleep 1
```

Then train / predict:
```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/model/train
Invoke-RestMethod http://127.0.0.1:8000/model/predict
```

If PowerShell profile interferes with `-m`, use:
```powershell
python scripts/bootstrap_history.py --runs 50 --sleep 1
```

## Static GitHub Pages Deployment

You can deploy a read-only (API-optional) dashboard to GitHub Pages. The app first tries the live API (`VITE_API_BASE`), then falls back to a static JSON `data/current_index.json` bundled in the build.

### Workflow
Included GitHub Action: `.github/workflows/deploy_pages.yml` – builds the frontend and publishes to Pages on pushes to `main` touching frontend or data.

### Initial Setup
1. Push repository to GitHub.
2. In repo Settings -> Pages, choose GitHub Actions.
3. Merge/push a commit; workflow outputs the URL (e.g. `https://<user>.github.io/<repo>/`).

### Local 30-Minute Data Refresh
Use `scripts/update_pages_data.py` to regenerate and copy the latest `current_index.json` into `frontend/public/data/`.

Schedule (Windows Task Scheduler) every 30 minutes:
```
Action: Start a program
Program/script: powershell.exe
Arguments: -ExecutionPolicy Bypass -NoProfile -Command "cd 'C:\Path\to\repo'; .\.venv\Scripts\activate.ps1; python scripts/update_pages_data.py; git add frontend/public/data/current_index.json website/data/current_index.json; if(git diff --cached --quiet){exit 0}; git commit -m 'chore(data): refresh index'; git push"
```

If you prefer not to store credentials, omit push and commit manually when desired.

### Environment Variable for API (Optional)
Create `frontend/.env`:
```
VITE_API_BASE=https://your-live-api.example.com
```
If unreachable from the user’s browser, the static JSON will still show the last pushed snapshot.

### Manual One-Liner Update
```powershell
python scripts/update_pages_data.py; git add frontend/public/data/current_index.json website/data/current_index.json; git commit -m "chore(data): refresh index"; git push
```

---
