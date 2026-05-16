# Tiny CRM

Small CRM with a Vue 3 SPA and a FastAPI backend. Contacts, deals (kanban + table), activities, Telegram chat, basic analytics, and ML scoring (lead conversion + churn) on bundled scikit-learn models.

**Stack:** Vue 3, Vite, TypeScript, Tailwind, Pinia · FastAPI, SQLAlchemy, Alembic · PostgreSQL or SQLite.

## Run locally

**Frontend** (Node 18+):

```bash
npm install
npm run dev
```

Opens on `http://localhost:5173`. By default the Vite dev server proxies `/api` to the backend on port 8000, so you usually do not need env vars for a local combo.

If the API runs elsewhere, set in a root `.env` file:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Leave it unset (or empty) when the SPA is served behind nginx with `/api` on the same host.

**Backend:**

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate   |   macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL, CORS_ORIGINS, etc.
alembic upgrade head
uvicorn app.main:app --reload
```

API: `http://127.0.0.1:8000` · OpenAPI: `http://127.0.0.1:8000/docs` · Liveness: `GET /healthz` · DB check: `GET /readyz`.

**Useful env (see `backend/.env.example`):**

- `DATABASE_URL` — `sqlite:///./tinycrm.db` or a Postgres URL  
- `SECRET_KEY` — required when `APP_ENV=production`  
- `CORS_ORIGINS` — comma-separated front-end origins  
- `TELEGRAM_BOT_TOKEN` — optional, for Telegram bridge  
- `ML_MODELS_PATH` — defaults to `models/` under `backend/`  

Demo data (optional):

```bash
cd backend
python scripts/seed_demo_data.py --force
```

## Docker

From the repo root:

```bash
docker compose up --build
```

Use strong `POSTGRES_PASSWORD` and `SECRET_KEY` before anything public. The backend image runs migrations on startup.

## CI

GitHub Actions runs Ruff, pytest, an Alembic migration smoke check, `vue-tsc`, Vitest, and `npm run build`. Optional secret `DEPLOY_URL` if you add a post-deploy health check.

## Production build

```bash
npm run build
npm run preview
```

## Repo layout

```text
src/
  components/   # UI (dashboard, deals, layout, chat, …)
  router/
  stores/       # Pinia
  services/     # HTTP helpers (e.g. analytics)
  views/
  lib/
backend/
  app/          # FastAPI app, routers, services
  alembic/
  scripts/      # seed scripts
```

More detail: [`docs/API.md`](docs/API.md) (endpoint list), PlantUML in [`docs/`](docs/).

## Contributing

Issues and PRs are welcome.

## License

[MIT](LICENSE)
