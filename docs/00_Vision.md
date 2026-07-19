# Atlas Vision

**Project Name:** Atlas  
**Status:** Living document  
**Audience:** Contributors, future teammates, and anyone evaluating the project

---

## One-line vision

Build an **operating system for machine learning engineering** — where every ML decision is explainable, reproducible, measurable, and improved through evidence.

---

## What Atlas is

Atlas is an **ML Engineering Platform**.

It helps engineers and learners design, evaluate, deploy, monitor, and continuously improve production-ready machine learning systems.

Atlas acts as an intelligent engineering partner: it recommends approaches, runs experiments, compares alternatives, explains trade-offs, and assists users in building systems they can trust.

---

## What Atlas is not

| Atlas is not | Why that matters |
|--------------|------------------|
| Another AutoML black box | Engineers stay in control; Atlas proves recommendations with experiments |
| A generic AI chatbot | Value comes from structured ML workflows, not open-ended chat |
| A no-code ML toy | Real engineering layers, real trade-offs, real production paths |
| A notebook replacement | Notebooks remain for exploration; Atlas owns the lifecycle around them |
| A cloud vendor | Prefer free/open-source tools; no paid lock-in for V1 |

---

## The problem

Building production ML is more than training a model. Teams juggle:

- notebooks and scripts  
- experiment tracking  
- evaluation and explainability  
- deployment and monitoring  
- documentation and tribal knowledge  

Work is fragmented. Experiments are hard to reproduce. Decisions are rarely justified with evidence. New engineers drown in tooling instead of learning judgment.

**Atlas’s bet:** one cohesive platform that turns ML from trial-and-error into **evidence-driven engineering**.

---

## The product experience (north star)

1. **Create a project** and upload a dataset.  
2. **Dataset Intelligence** — Atlas understands the data (missingness, leakage risk, imbalance, bias signals), not just column types.  
3. **Formulate the problem** — multiple valid ML formulations, not a single forced path.  
4. **Experiment Engine** — plan and run comparable experiments; log everything.  
5. **Compare models** on accuracy *and* latency, calibration, memory, explainability.  
6. **Explain** predictions (e.g. SHAP) so users know *why*.  
7. **Deploy** a real API surface (FastAPI + Docker).  
8. **Monitor** basic health: traffic, latency, drift signals, prediction logs.  
9. **Teach while building** — every recommendation includes reasoning and trade-offs.

Longer term: specialized agents (data, ML, evaluation, deployment) that debate options and **settle disagreements with experiments** — not opinions.

---

## Philosophy (non-negotiable)

Every engineering decision in Atlas should be:

1. **Explainable** — why this choice?  
2. **Reproducible** — same inputs → same experiment trail  
3. **Measurable** — metrics over vibes  
4. **Evidence-driven** — recommendations backed by runs, not hype  

Atlas never blindly recommends. It shows the **why**.

---

## Architecture stance (V1)

V1 is a **modular monolith**, not microservices.

```
Browser → React / Next.js → FastAPI Router → Service → Repository → PostgreSQL
```

- **Routers** stay thin (HTTP only).  
- **Services** own business logic.  
- **Repositories** own data access (SQL / storage).  
- **ML modules** live *inside* the backend (profiling, training, evaluation, explainability).  

Atlas is an **application first**. ML is a module — not the other way around.

Infrastructure such as Redis, object storage, GPU workers, and vector DBs are added only when a real V1+ feature requires them.

---

## Success looks like

Someone lands on the repository and thinks: *“I could use this.”*

The repo demonstrates:

- software & backend engineering  
- ML engineering & MLOps judgment  
- clean architecture and documentation  
- production readiness (tests, Docker, CI over time)  

For the builder: by the end, you can discuss system design, ML workflows, evaluation, deployment, and trade-offs in interviews because you **built and understood** them — not only glued frameworks together.

---

## Scope discipline

We build **Atlas V1** with depth, not an unfinished feature zoo.

Full lifecycle dreams (multi-agent debate, enterprise RBAC, cloud deploy) are real — but they are **later phases**. V1 proves the spine: auth → projects → datasets → intelligence → experiments → comparison → explainability → deploy → basic monitoring.

---

## Relationship to other docs

| Document | Role |
|----------|------|
| `00_Vision.md` (this file) | Why Atlas exists and how we think |
| `01_Product_Requirements_Document.md` | What V1 must deliver and what is out of scope |
| `06_System_Architecture.md` | How the system is structured (evolves with code) |
| `15_Roadmap.md` | Roadmap index |
| `19_Project_Walkthrough.md` | End-to-end build narrative |
| `20_Roadmap_Extension.md` | Additive next-evolution roadmap (does not replace this vision) |

Planning is frozen enough to ship. Remaining docs evolve **while coding**.

**Roadmap extension:** After V1 foundation, prioritize engineering workflows, artifact persistence, decision traceability, and research-style experiment reporting over feature count. See [`20_Roadmap_Extension.md`](./20_Roadmap_Extension.md).
