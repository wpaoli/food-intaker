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

## Deployment

Live: **https://food-intaker.onrender.com**

| Service | Details |
|---------|---------|
| Render | Web service — config in `render.yaml` — [dashboard](https://dashboard.render.com) |
| Supabase | PostgreSQL — [project dashboard](https://supabase.com/dashboard/project/cwxkbrthlimlekyfiqlp) |

### Environment variables

Set `DATABASE_URL` in `.env` locally or as a Render environment variable. Use the Supabase **Session Pooler** URL (not the direct connection) for IPv4 compatibility with Render:

```
DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-1-us-west-2.pooler.supabase.com:5432/postgres
```

### DB migrations

SQLAlchemy's `create_all` creates tables but won't ALTER existing ones. After adding new columns to models, run in the [Supabase SQL editor](https://supabase.com/dashboard/project/cwxkbrthlimlekyfiqlp/sql):

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS calories_target FLOAT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS carbs_target FLOAT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS fat_target FLOAT;
```
