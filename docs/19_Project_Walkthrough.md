# Atlas — Project Walkthrough

**Audience:** contributors, interviewers, future-you  
**Status:** Living document (reflects the V1 spine as of the frontend landing)  
**Repo:** https://github.com/nexus69420/atlas

---

## 1. What Atlas is

**Atlas** is an open-source **ML Engineering Platform** — not AutoML, not a chatbot, not a no-code toy.

**Problem it solves:** Real ML work is fragmented across notebooks, scripts, trackers, evaluation tools, deployment stacks, and monitoring dashboards. Decisions are often gut-feel. Experiments are hard to reproduce. New engineers drown in tooling instead of learning judgment.

**Atlas’s bet:** One cohesive product where every recommendation is **explainable, reproducible, measurable, and evidence-driven**.

**North star:**

> An operating system for machine learning engineering.

Related docs:

| Document | Role |
|----------|------|
| [`00_Vision.md`](./00_Vision.md) | Why Atlas exists and how we think |
| [`01_Product_Requirements_Document.md`](./01_Product_Requirements_Document.md) | What V1 must deliver / non-goals |
| This file | End-to-end narrative of what was built and what comes next |

---

## 2. Product philosophy (non-negotiable)

| Principle | Meaning in Atlas |
|-----------|------------------|
| Evidence over intuition | Compare models with metrics + trade-offs; don’t crown a winner blindly |
| Explain every decision | Warnings and SHAP include *why it matters* |
| Reproducibility by default | Same seed / split / config stored on experiments |
| Continuous improvement | Iterate experiments; don’t one-shot train |
| Learn while building | API and UI teach engineering judgment |

**Explicit non-goals:** replace ML engineers, guarantee “optimal” models, become a generic LLM chat wrapper, become a notebook replacement, become a cloud vendor.

---

## 3. Architecture (and why)

```
Browser (Next.js)
    → FastAPI routers (thin)
        → Services (business rules)
            → Repositories (SQL only)
                → PostgreSQL

ML lives inside the backend as modules:
  profiling / training / evaluation / explainability / deployment
```

### Design decisions

1. **Modular monolith for V1** — one deployable API, clear module boundaries. Microservices would be premature complexity.
2. **Service → Repository split** — services don’t know SQL; repositories don’t mint JWTs or run SHAP. Storage can change later without rewriting product logic.
3. **App-first, ML-second** — Atlas is a real product (users, projects, auth). ML is a capability *inside* it, not a notebook with a website taped on.
4. **Sync experiments for V1** — small CSVs finish quickly; Celery / workers when jobs get long enough to need a queue.
5. **Local disk storage for V1** — MinIO / S3 can wait; keep a single storage interface (`LocalStorage`) so the swap is localized.

### Stack (free / open source)

| Layer | Choice |
|-------|--------|
| API | FastAPI |
| ORM / migrations | SQLAlchemy 2 + Alembic |
| DB | PostgreSQL |
| ML | pandas, scikit-learn, SHAP |
| Frontend | Next.js + Tailwind + Geist |
| Quality | Ruff, Black, pytest |
| Local infra | Docker Compose |

---

## 4. How we built it (chronological spine)

### Phase 0 — Vision & freeze planning

- Agreed: **depth over breadth** for V1.
- Enough design to avoid disasters; remaining docs evolve while coding.
- Working rule: **~20% teaching / ~80% building**.

### Phase 1 — Backend foundation

- FastAPI app factory, pydantic-settings, SQLAlchemy session, Alembic
- Docker Compose (API + Postgres)
- Ruff / Black
- `GET /health` → `{"status": "healthy"}`

**Why first:** Auth and projects need DB, config, and migrations. Skipping foundation forces rewrites.

### Phase 2 — Auth

- User model, bcrypt password hashing, JWT access tokens
- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- Layers: `AuthService` → `UserRepository`

**Why:** Every project belongs to someone.

### Phase 3 — Projects

- Authenticated CRUD; `owner_id` foreign key; unique name per owner
- Other users’ projects return **404** (no existence leak)

**Why:** Container for datasets, experiments, and deployments.

### Phase 4 — Datasets

- CSV upload (multipart), local disk via `LocalStorage`
- Metadata: row count, column count, dtype schema
- Preview endpoint; unique name per project; default size cap

### Phase 5 — Dataset profiling (“Atlas Report”)

- Pure ML module `profile_dataframe()` (no HTTP / DB concerns)
- Missingness, inferred types, stats, strong correlations, duplicate / constant / ID-like / imbalance warnings
- Optional `target_column` for class-imbalance analysis
- Persisted in `dataset_profiles`

**Why this is the first “real ML” moment:** evidence about data *before* training.

### Phase 6 — Experiment Engine (heart of Atlas)

- Train multiple sklearn models (logistic regression, random forest, gradient boosting; regression variants too)
- Shared preprocessing (impute / scale / one-hot); drop likely ID columns
- Metrics + ranking (macro-F1 / R²) + **trade-off explanations**
- Synchronous run; failures stored as `status: failed` with message

**Why multiple models:** Atlas compares alternatives; it does not hide behind one AutoML black box.

### Phase 7 — Model comparison API polish

- `GET /api/v1/projects/{id}/experiments/{id}/comparison`
- UI-ready cards: rank, pros / cons, `delta_vs_winner`, metric table
- List endpoint returns lightweight summaries (no heavy result blobs)

### Phase 8 — SHAP explainability

- Retrain selected model with the experiment’s config, then compute SHAP
- Tree / Linear explainers when possible
- Global mean-|SHAP| ranking + optional per-instance contributions
- Persisted per `(experiment_id, model_key)`

### Phase 9 — Deployment

- Deploy comparison winner (or explicit `model_key`)
- Fit on **full dataset** for serving (model *selection* still rests on experiment evidence)
- Live `POST .../predict`
- Export a **Docker bundle** (`Dockerfile`, standalone FastAPI app, `model.joblib`, README)
- Deactivate + `prediction_count` counter

### Phase 10 — Frontend (Astra-inspired product UI)

- Next.js 15 + Tailwind + Geist
- Dark product shell: brand-first landing, teal accent dots, sidebar workspace
- Auth + projects list / create + project detail (CSV upload, dataset & experiment listings)
- CORS enabled on the API for local Next.js (`localhost:3000`)

---

## 5. Feature map (what exists today)

### Backend API

| Area | Capabilities |
|------|----------------|
| Health | `GET /health` (public) |
| Auth | register, login (JWT), me |
| Projects | create, list, get, update, delete |
| Datasets | upload CSV, list, get, preview, delete |
| Profiling | generate / get Atlas Report |
| Experiments | create + run, list, get |
| Comparison | polished comparison payload |
| Explainability | SHAP generate / get |
| Deployments | create, list, get, predict, deactivate |

### Frontend routes

| Path | Purpose |
|------|---------|
| `/` | Marketing landing + product preview |
| `/login`, `/register` | Auth |
| `/projects` | Authenticated project list / create |
| `/projects/[id]` | Datasets upload + experiments overview |

### Engineering quality already in place

- Layered architecture and type hints
- Alembic migrations through deployments / explanations
- pytest coverage across health → deploy
- Docker Compose for local Postgres / API
- Meaningful git commits on `main`

---

## 6. End-to-end user journey (today)

1. Open the UI → register / login  
2. Create a **project**  
3. Upload a **CSV**  
4. *(API)* Generate a **profile** (optional target column)  
5. *(API)* Run an **experiment** → multiple models + comparison  
6. *(API)* **SHAP**-explain a model  
7. *(API)* **Deploy** the winner → predict live or `docker build` the bundle  

The UI currently covers steps 1–3 deeply. Steps 4–7 are API-complete and are the natural next UI depth.

---

## 7. What we can add next (prioritized)

### Near-term (highest leverage)

1. UI for experiments — run form, comparison table, winner cards  
2. UI for profiling — Atlas Report visualization  
3. UI for SHAP — feature-importance bars + instance view  
4. UI for deploy / predict — one-click deploy + predict playground  
5. Basic monitoring — prediction logs, latency, simple drift signals  
6. CI (GitHub Actions) — pytest + frontend build on PR  
7. Persist fitted pipelines on experiment (faster explain / deploy, stronger artifact lineage)

### Medium-term (V1+ / V2)

- Dataset versioning  
- Cross-validation / Optuna-style HPO  
- XGBoost / LightGBM in the model registry  
- Async job queue (Celery / Redis / Temporal) for long training  
- First-class model registry beyond the deployment row  
- Team workspaces / RBAC  

### Long-term (vision)

- Multi-agent debate (data / ML / eval agents) settled by experiments  
- Continuous retraining loops  
- Plugin architecture  
- Enterprise audit logs / cloud deploy targets  

---

## 8. How to talk about Atlas (resume / interviews)

**One-liner:**

> Built Atlas, an open-source ML engineering platform (FastAPI + Next.js) that turns ML from trial-and-error into evidence-driven workflows: profiling → multi-model experiments → SHAP → deployable artifacts.

**Strong talking points:**

- Modular monolith with clean Service / Repository boundaries  
- Evidence-first experiment comparison (not black-box AutoML)  
- Production habits: migrations, tests, Docker, typed APIs, CORS, JWT auth  
- Explainability and deployment as first-class product features  

---

## 9. ChatGPT / LLM context prompt

Copy-paste the block below when you want another model to understand Atlas deeply (interview prep, feature design, docs, or code aligned with this repo).

````text
You are a senior ML engineer, staff backend engineer, and technical interviewer.

I want you to deeply understand my open-source project **Atlas** so you can help me explain it, improve it, prepare interview answers, write docs, and design next features.

## What Atlas is
Atlas is an ML Engineering Platform (NOT AutoML, NOT a chatbot, NOT no-code).
Vision: an operating system for machine learning engineering where every decision is explainable, reproducible, measurable, and evidence-driven.

Repo: https://github.com/nexus69420/atlas

## Architecture (V1 modular monolith)
Browser (Next.js)
→ FastAPI routers (thin)
→ Services (business logic)
→ Repositories (SQL only)
→ PostgreSQL

ML modules live inside the backend:
profiling, training, evaluation, explainability, deployment.

Stack: Python, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Docker Compose, pandas, scikit-learn, SHAP, Next.js, Tailwind, Ruff/Black, pytest.
Budget constraint: free/open-source only.

## Product philosophy
- Evidence over intuition
- Explain every recommendation (include WHY)
- Reproducibility by default
- Continuous improvement via experiments
- Teach while building
Non-goals: replace engineers, guarantee optimal models, generic AI chat.

## What is already built (V1 spine)

### Backend
1. Foundation: FastAPI, settings, SQLAlchemy, Alembic, Docker Compose, health endpoint
2. Auth: register/login/me with bcrypt + JWT
3. Projects: authenticated CRUD, ownership isolation
4. Datasets: CSV upload to local storage, metadata, preview
5. Profiling: Atlas Report (missingness, correlations, duplicates, ID-like columns, imbalance warnings) with optional target_column
6. Experiment Engine: train multiple models (logistic regression, random forest, gradient boosting; regression variants), metrics, ranking, trade-off explanations; sync execution
7. Comparison API: polished UI-ready comparison cards (pros/cons, delta vs winner, metric table)
8. Explainability: SHAP global + optional local explanations, persisted per experiment/model
9. Deployment: deploy winner or selected model, full-data fit artifact, live predict endpoint, Docker export bundle, deactivate + prediction_count
10. CORS enabled for local Next.js

### Frontend
- Astra-inspired dark product UI (Geist, teal accents)
- Landing page, login/register
- App shell with sidebar
- Projects list/create
- Project detail: CSV upload + dataset/experiment listings
- API client in lib/api.ts using JWT in localStorage

## How it was built
Engineering-first workflow: freeze high-level architecture early, then ship in sprints (foundation → auth → projects → datasets → profiling → experiments → comparison → SHAP → deploy → UI). Depth over breadth. ~20% teaching / ~80% implementation. Clean layered code, meaningful git commits, tests alongside features.

## Important design decisions
- Modular monolith, not microservices
- Service/Repository separation so storage can change later
- Local disk storage for V1 (MinIO/S3 later behind same interface)
- Sync training for V1 (async workers later)
- Comparison and SHAP emphasize explanations, not just numbers
- Deployment fits on full data for serving, while experiment metrics remain selection evidence

## What is NOT done yet (good next work)
- Full UI for profiling, experiment runner, comparison, SHAP, deploy/predict
- Prediction logging / drift monitoring UI
- GitHub Actions CI
- Persist trained pipelines as experiment artifacts
- HPO / cross-validation / stronger model zoo
- Multi-agent debate mode, enterprise RBAC, continuous retraining

## How I want you to help
When I ask questions:
1. Stay aligned with Atlas philosophy (evidence-driven, explainable, not AutoML theater)
2. Prefer simple production-quality designs over overengineering
3. Call out trade-offs clearly
4. Help me explain architecture and decisions for interviews
5. Propose next features in priority order with rationale
6. If generating code, match existing patterns: thin routers, fat services, repositories for DB, ML logic under app/ml/

Confirm you understand Atlas at this level, then summarize the system in your own words in under 15 bullets, and ask me what I want to do next (docs, interview prep, feature design, or code).
````

---

## 10. Quick links

| Resource | Location |
|----------|----------|
| Vision | [`docs/00_Vision.md`](./00_Vision.md) |
| PRD | [`docs/01_Product_Requirements_Document.md`](./01_Product_Requirements_Document.md) |
| Backend | `backend/` |
| Frontend | `frontend/` |
| Compose | `docker-compose.yml` |
| Root README | [`README.md`](../README.md) |
