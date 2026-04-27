# Food Intaker

Personal nutrition tracker. Log what you eat, track calories, protein, carbs, and fat. Foods are fully custom -- you define the nutrition values per serving.

## Prerequisites

- Python 3.11+

## Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running

```bash
uvicorn main:app --reload
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

OpenAPI collection (Bruno, Postman, Insomnia, etc.): [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/status` | Server status check |
| `GET` | `/foods` | List all saved foods |
| `POST` | `/foods` | Add a food with custom nutrition per serving |
| `PATCH` | `/foods/{id}` | Update a food |
| `POST` | `/log` | Log a saved food entry (`food_id`, `serving`) |
| `POST` | `/log/quick` | Log nutrition directly, no food required |
| `GET` | `/log?start=...&end=...` | List log entries, optionally filtered by date |
| `GET` | `/report?start=...&end=...` | Aggregate calorie + protein totals |

## Data

SQLite database is created automatically at `./data/tracker.db` on first run.
