# Calorie Tracker

Single-user calorie and protein tracker. Python/FastAPI backend with a USDA food database integration. MCP server layer lets Claude log and query food conversationally.

## Prerequisites

- Python 3.11+
- A [USDA FoodData Central API key](https://fdc.nal.usda.gov/api-key-signup.html) (free)

## Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "USDA_API_KEY=your_key_here" > .env
```

## Running

```bash
uvicorn main:app --reload
```

API docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

OpenAPI collection (Bruno, Postman, Insomnia, etc.): [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/status` | Server status check |
| `GET` | `/foods/search?q=...` | Search USDA food database |
| `POST` | `/foods` | Save a food to local DB (body: `{"fdc_id": ...}`) |
| `POST` | `/log` | Log a food entry (body: `{"food_id", "grams", "logged_at"}`) |
| `GET` | `/log?start=...&end=...` | List log entries in date range |
| `GET` | `/report?start=...&end=...` | Aggregate calorie + protein totals |

## Data

SQLite database is created automatically at `./data/tracker.db` on first run.
