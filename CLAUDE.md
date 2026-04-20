# CLAUDE.md

Context for Claude Code. Loaded automatically at session start.

## Project

Single-user calorie and protein tracker. Python backend API, then an MCP server on top so Claude can log and query food conversationally. Learning project — the real goal is MCP fluency.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy + SQLite
- USDA FoodData Central API (requires key, set as `USDA_API_KEY` env var)
- MCP Python SDK (`mcp` package)

## Conventions

- Single user, hardcoded `user_id=1` for now. But every user-owned row has a `user_id` FK column from day one. Do not skip this.
- No auth. No middleware. No frontend.
- One repo, flat structure. No microservices, no Docker yet.
- SQLite file lives at `./data/tracker.db`. Gitignore the `data/` dir.
- Config via `.env` file + `python-dotenv`. Never commit `.env`.
- Use FastAPI's built-in `/docs` for manual testing. Don't build a test suite yet.

## Data model

Three tables only:
- `users` (id, name, created_at) — one row, hardcoded
- `foods` (id, usda_fdc_id, name, calories_per_100g, protein_per_100g, created_at) — local cache of USDA foods
- `log_entries` (id, user_id, food_id, grams, logged_at, created_at)

Calories and protein only. No sugar, fat, or other nutrients.

## API endpoints (v1)

- `GET /foods/search?q=...` — proxy to USDA, return top 5 results with fdc_id, name, data type, calories_per_100g, protein_per_100g
- `POST /foods` — save a USDA food to local DB (input: fdc_id)
- `POST /log` — create log entry (input: food_id, grams, logged_at)
- `GET /log?start=...&end=...` — list entries in range
- `GET /report?start=...&end=...` — aggregate calorie + protein totals

## MCP tools (phase 5)

- `search_food(query)` → `/foods/search`
- `log_food(food_name_or_id, grams, when)` → `/foods` + `/log`
- `get_daily_totals(date)` → `/report`
- `get_range_report(start, end)` → `/report`

## Build phases

Finish each phase before starting the next. Ask before skipping ahead.

1. Scaffolding: repo init, venv, FastAPI hello world, SQLite connected, `GET /health` works.
2. Data model: three tables via SQLAlchemy, seed user_id=1, manual insert/query works.
3. USDA integration: `GET /foods/search` and `POST /foods` working, results parsed correctly.
4. Logging + reports: `POST /log`, `GET /log`, `GET /report` working. Verified via `/docs`.
5. MCP server: wrap the API with MCP tools. Test via Claude Desktop locally.
6. Claude connector: expose MCP server as a remote connector in Claude.ai.

## Working style

- User has ADHD. Keep responses tight. Bullets over prose. No preamble.
- User has deep software background but is out of practice. Assume concepts are understood, don't over-explain syntax.
- User is here to learn MCP specifically. When we hit MCP concepts, slow down and explain the "why," not just the "how."
- Use Plan Mode for anything architectural. Auto-accept is fine for boilerplate.
- Never use em dashes.

## Out of scope (do not build)

- Auth, OAuth, API keys for the backend
- Frontend of any kind
- Sugar, fat, carbs, micronutrients
- Barcode scanning, OCR
- Tests, CI, Docker, deployment tooling
- Multi-user features
