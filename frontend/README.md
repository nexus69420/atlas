# Atlas Frontend

Next.js UI for the Atlas ML Engineering Platform.

Design direction: dark product shell inspired by modern SaaS (e.g. Astra), with Atlas teal accents and Geist typography.

## Run

```bash
# terminal 1 — API
cd backend
uvicorn app.main:app --reload --port 8000

# terminal 2 — UI
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

## Routes

| Path | Purpose |
|------|---------|
| `/` | Marketing landing |
| `/login` `/register` | Auth |
| `/projects` | Authenticated project list |
| `/projects/[id]` | Datasets + experiments overview |
