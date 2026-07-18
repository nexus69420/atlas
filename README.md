# Atlas

**Atlas** is an autonomous machine learning engineering platform.  
It turns ML from trial-and-error into evidence-driven engineering.

Atlas is **not** AutoML, a chatbot, or a no-code builder.  
It is an **ML Engineering Platform** — an intelligent partner for engineers building production ML systems.

---

## Architecture (V1)

Modular monolith (not microservices):

```
Browser → React / Next.js → FastAPI → Services → Repositories → PostgreSQL
```

ML components (profiling, training, evaluation, explainability) live as modules inside the backend.

---

## Current status

| Area | Status |
|------|--------|
| Backend V1 spine (auth → deploy) | Done |
| Frontend (landing + app shell + projects) | In progress |

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

UI: http://localhost:3000 · API: http://127.0.0.1:8000

### Sprint 1 deliverable

```http
GET /health
```

```json
{ "status": "healthy" }
```

### Auth (in progress)

```http
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

### Projects

```http
POST   /api/v1/projects
GET    /api/v1/projects
GET    /api/v1/projects/{id}
PATCH  /api/v1/projects/{id}
DELETE /api/v1/projects/{id}
```

### Datasets

```http
POST   /api/v1/projects/{project_id}/datasets
GET    /api/v1/projects/{project_id}/datasets
GET    /api/v1/projects/{project_id}/datasets/{id}
GET    /api/v1/projects/{project_id}/datasets/{id}/preview
POST   /api/v1/projects/{project_id}/datasets/{id}/profile
GET    /api/v1/projects/{project_id}/datasets/{id}/profile
DELETE /api/v1/projects/{project_id}/datasets/{id}
```

### Experiments

```http
POST   /api/v1/projects/{project_id}/experiments
GET    /api/v1/projects/{project_id}/experiments
GET    /api/v1/projects/{project_id}/experiments/{id}
GET    /api/v1/projects/{project_id}/experiments/{id}/comparison
POST   /api/v1/projects/{project_id}/experiments/{id}/explain
GET    /api/v1/projects/{project_id}/experiments/{id}/explanations/{model_key}
```

### Deployments

```http
POST   /api/v1/projects/{project_id}/deployments
GET    /api/v1/projects/{project_id}/deployments
GET    /api/v1/projects/{project_id}/deployments/{id}
POST   /api/v1/projects/{project_id}/deployments/{id}/predict
POST   /api/v1/projects/{project_id}/deployments/{id}/deactivate
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

### Run with Docker Compose

```bash
docker compose up --build
```

Then open:

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

### Local backend (without Docker for the API)

```bash
# start Postgres only
docker compose up -d db

cp .env.example .env

cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Tests & lint

```bash
cd backend
pytest
ruff check .
black --check .
```

### Database migrations

Alembic is wired to the same `DATABASE_URL` as the app.  
No models yet in Sprint 1 — first revision lands with auth/projects.

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

---

## Repository layout

```
atlas/
├── backend/
│   ├── app/
│   │   ├── api/          # HTTP routes (thin)
│   │   ├── core/         # settings, shared infra
│   │   ├── db/           # engine, session, Base
│   │   ├── models/       # SQLAlchemy ORM
│   │   ├── schemas/      # Pydantic API contracts
│   │   ├── repositories/ # DB queries
│   │   ├── services/     # business logic
│   │   ├── ml/           # profiling, training, eval, explainability
│   │   ├── workers/      # background jobs (later)
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/         # Next.js UI (Astra-inspired dark product shell)
├── docs/
├── docker-compose.yml
└── .env.example
```

---

## Stack (V1)

| Layer | Choice | Why |
|-------|--------|-----|
| API | FastAPI | Typed, fast, excellent OpenAPI |
| DB | PostgreSQL + SQLAlchemy 2 + Alembic | Production default; migrations as code |
| Config | pydantic-settings | Fail fast on bad env |
| Containers | Docker Compose | Reproducible local stack |
| Lint / format | Ruff + Black | Fast + consistent |
| Frontend | Next.js + Tailwind | Dark product UI; talks to FastAPI |

---

## License

Open source — license TBD.
