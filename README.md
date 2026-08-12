# Atlas

**Atlas** is an open-source **ML Engineering Platform**.  
It turns ML from trial-and-error into evidence-driven engineering.

Atlas is **not** AutoML, a chatbot, or a no-code builder.  
It is an intelligent partner for engineers building production ML systems — profile data, compare models with trade-offs, explain with SHAP, deploy with an artifact + Docker bundle, and log predictions.

---

## Why this repo (interview / hire signal)

| Signal | Where it shows up |
|--------|-------------------|
| Evidence over automation | Atlas Report, experiment comparison + trade-offs |
| Explainability | SHAP per model on completed experiments |
| Reproducibility | Experiment artifacts (`config.json`, `metrics.json`, train-split pipelines) |
| Serving | Deployment artifacts + exportable Docker bundle |
| Auditability | Prediction logs on every `predict` call |
| Engineering discipline | Thin routers → services → repos; Alembic; CI |

Full narrative: [`docs/19_Project_Walkthrough.md`](docs/19_Project_Walkthrough.md)  
Roadmap (additive): [`docs/20_Roadmap_Extension.md`](docs/20_Roadmap_Extension.md)

---

## Architecture (V1)

```
Browser → Next.js → FastAPI (thin routers) → Services → Repositories → PostgreSQL
                         └─ app/ml/ (profile, train, eval, SHAP, deploy)
```

---

## Demo path (10 minutes)

1. Start Postgres + API + UI (see Quick start).
2. Register → create a project → upload a CSV.
3. **Profile** the dataset (Atlas Report).
4. **Run an experiment** (multi-model classification/regression).
5. Open the experiment → comparison + **SHAP**.
6. **Deploy** the winner → call **predict** → check prediction logs.

Offline / CI-friendly script (downloads public Telco churn when online):

```bash
cd backend
.venv\Scripts\activate   # or: source .venv/bin/activate
python scripts/e2e_churn_flow.py
# or fully offline:
python scripts/e2e_churn_flow.py --offline
```

---

## Current status

| Area | Status |
|------|--------|
| Backend V1 spine (auth → profile → experiment → SHAP → deploy → predict logs) | Done |
| Experiment artifact persistence | Done |
| Prediction logging | Done |
| Frontend (landing + projects + dataset report + experiment workspace) | Done |
| CI (pytest + frontend build) | Done |

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

UI: http://localhost:3000 · API: http://127.0.0.1:8000

### API surface

```http
GET  /health

POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me

POST|GET|PATCH|DELETE /api/v1/projects...
POST|GET|DELETE       /api/v1/projects/{id}/datasets...
POST|GET              /api/v1/projects/{id}/datasets/{id}/profile
POST|GET              /api/v1/projects/{id}/experiments...
GET                   /api/v1/projects/{id}/experiments/{id}/comparison
POST|GET              /api/v1/projects/{id}/experiments/{id}/explain...
POST|GET              /api/v1/projects/{id}/deployments...
POST                  /api/v1/projects/{id}/deployments/{id}/predict
GET                   /api/v1/projects/{id}/deployments/{id}/predictions
POST                  /api/v1/projects/{id}/deployments/{id}/deactivate
```

After Postgres is up:

```bash
cd backend
alembic upgrade head
```

---

## Quick start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (optional, for local non-Docker runs)
- Node 20+ (frontend)

### Run with Docker Compose

```bash
docker compose up --build
```

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

### Local backend (without Docker for the API)

```bash
docker compose up -d db
cp .env.example .env

cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Tests & lint

```bash
cd backend
pytest
ruff check .
python scripts/e2e_churn_flow.py --offline
```

```bash
cd frontend
npm ci
npm run build
```

---

## Repository layout

```
atlas/
├── backend/
│   ├── app/           # api, services, repos, ml, models
│   ├── alembic/
│   ├── scripts/       # e2e_churn_flow.py
│   └── tests/
├── frontend/          # Next.js product UI
├── docs/
├── .github/workflows/ # CI
└── docker-compose.yml
```

---

## Stack (V1)

| Layer | Choice |
|-------|--------|
| API | FastAPI |
| DB | PostgreSQL + SQLAlchemy 2 + Alembic |
| ML | pandas, scikit-learn, SHAP, joblib |
| Frontend | Next.js + Tailwind |
| CI | GitHub Actions |

---

## License

Open source — license TBD.
