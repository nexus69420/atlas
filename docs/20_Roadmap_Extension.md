# Atlas Roadmap Extension — Engineering OS Evolution

**Status:** Additive extension (does **not** replace Vision, PRD, or prior planning)  
**Audience:** Contributors making future product and technical decisions  
**Depends on:** [`00_Vision.md`](./00_Vision.md), [`01_Product_Requirements_Document.md`](./01_Product_Requirements_Document.md), [`19_Project_Walkthrough.md`](./19_Project_Walkthrough.md)

---

## How to use this document

Keep the original vision, philosophy, architecture, coding standards, and development workflow **exactly as already described**.

This file **extends** that foundation. It should influence:

- future feature design  
- documentation  
- implementation order  
- technical decisions  

It does **not** rewrite or discard the V1 plan.

---

## Current project assessment

Atlas V1 has successfully established its engineering foundation.

Complete (or substantially complete):

- core backend architecture  
- authentication  
- project management  
- dataset management  
- profiling  
- experiment execution  
- explainability  
- comparison  
- deployment  
- frontend skeleton  

**New focus:** stop adding random features. Make Atlas feel like a **real ML engineering platform**.

Prioritize **depth, polish, reproducibility, and engineering workflows** over feature count.

---

## Product direction

Atlas continues evolving into an **engineering operating system**, not an AutoML platform.

Every feature should answer:

> Does this help an engineer make better machine learning decisions?

If the answer is no, reconsider implementing it.

**Evidence remains more important than automation.**

---

## Updated engineering principles

Continue following the original principles:

- Evidence over intuition  
- Explainability first  
- Reproducibility by default  
- Simple production-quality implementations  
- Modular architecture  
- Thin routers / fat services / repository pattern  
- Clean code  
- Free and open-source tooling  

Additionally prioritize:

- Engineering workflows  
- Decision traceability  
- Experiment reproducibility  
- Knowledge accumulation  
- Research-style reporting  
- Production readiness  
- Excellent developer experience  

---

## Major missing pieces (higher priority than more algorithms)

These matter more than expanding the model zoo.

### 1. Experiment artifacts

Every experiment should persist its complete output, for example:

- trained pipeline  
- preprocessing pipeline  
- model weights  
- scaler / encoder  
- metrics  
- SHAP outputs  
- configuration  
- logs  
- metadata  

Each experiment should be reproducible independently.

Example layout:

```text
experiments/
  exp_001/
    config.json
    metrics.json
    pipeline.pkl
    model.pkl
    shap.pkl
    report.json
    logs.txt
```

Future MinIO / S3 storage should reuse the same abstraction (extend `LocalStorage` / artifact interfaces — do not fork a parallel storage story).

### 2. Experiment lineage

Experiments should become connected rather than isolated.

Atlas should eventually know:

- which experiment inspired another  
- what changed  
- why it changed  
- what improved  
- what became worse  

Think of experiment history like **Git history**, eventually visualized as an **experiment graph**.

### 3. Experiment reports

Every completed experiment should automatically generate a structured engineering report.

Possible sections:

- Objective  
- Dataset Summary  
- Feature Engineering  
- Preprocessing  
- Models Evaluated  
- Metrics  
- Comparison  
- SHAP Insights  
- Trade-offs  
- Winner  
- Deployment Decision  
- Conclusion  

The report should resemble a **concise research paper**.

This should become one of Atlas’ defining features.

### 4. Decision journal

Atlas should maintain a permanent engineering decision log.

Every important recommendation should record:

- recommendation  
- reasoning  
- supporting evidence  
- alternatives considered  
- confidence level  

Example shape:

```text
Decision #18
Recommended: Random Forest
Reason: Dataset contains many nonlinear relationships
Evidence: Compared against Logistic Regression and Gradient Boosting
Rejected alternatives because: ...
Confidence: High
```

Atlas should always explain **WHY**, never only **WHAT**.

### 5. Knowledge accumulation (future milestone)

Long-term: Atlas gradually learns from prior experiments, e.g.:

- Random Forest consistently weak on highly sparse data  
- Tree / boosting models often strong with many categoricals  
- Certain preprocessing pipelines repeatedly outperform alternatives  

This knowledge should emerge from **experiment history**, not hardcoded rules.

### 6. Prediction logging

Deployment should not end at serving.

Eventually capture:

- prediction history  
- timestamps  
- model / deployment version  
- request metadata  
- prediction count  
- optional feedback  

Enables monitoring and future **retraining recommendations** (recommend, don’t auto-force).

### 7. Drift monitoring

Future versions analyze prediction / feature history for:

- data drift  
- concept drift  
- feature distribution shifts  
- performance degradation  

Atlas should **recommend** retraining and explain the evidence — never silently retrain as a black box.

### 8. Reproducibility depth

Store enough to re-run cleanly:

- random seed  
- model parameters  
- preprocessing configuration  
- feature list  
- dataset version  
- metrics  
- execution time  

Re-running an experiment should be straightforward.

### 9. Engineering workflow (UX)

Atlas should feel like an engineering workspace, not a dashboard of buttons.

Example experiment page contents:

- hypothesis  
- experiment configuration  
- preprocessing steps  
- models  
- metrics  
- SHAP explanations  
- comparison  
- deployment status  
- generated report  

Engineers should feel like they are **documenting research**, not clicking through a wizard.

---

## Philosophy of experiments

**Today:** benchmarking (train several models, compare metrics).

**Long-term:** experimentation as an iterative learning cycle:

```text
Hypothesis
  → Configuration
  → Training
  → Evaluation
  → Comparison
  → Conclusion
  → Knowledge Update
```

Experiments become connected learning cycles, not isolated model runs.

---

## Prioritized roadmap

### P0 — Complete V1

- Polish frontend  
- Profiling UI  
- Experiment runner UI  
- Comparison UI  
- SHAP visualization UI  
- Deployment UI  
- Prediction endpoint UI  
- Prediction logging  
- Artifact persistence  
- GitHub Actions  
- Better testing  

### P1

- Cross-validation  
- Optuna hyperparameter optimization  
- Pipeline persistence (deeper than V1 artifacts)  
- Experiment reports  
- Decision journal  
- Experiment lineage  

### P2

- Interactive experiment graph  
- Drift detection  
- Dataset versioning  
- Model cards  
- Retraining recommendations  

### P3

- Knowledge accumulation  
- Continuous retraining  
- Team collaboration  
- Enterprise RBAC  
- Plugin SDK  
- Multi-agent experiment planning  
- Multi-agent debate mode  

---

## Development guidance

Continue the existing architecture.

- Do not introduce unnecessary complexity  
- Avoid microservices  
- Prefer extending the modular monolith  

When implementing:

- Keep routers thin  
- Business logic in services  
- Database operations in repositories  
- ML logic under `app/ml/`  
- Prefer composition over duplication  
- Keep modules cohesive  

---

## Product identity check

Atlas should never feel like an AutoML tool.

Atlas should feel like a **senior ML engineer sitting beside the user**.

It should help engineers:

- think  
- experiment  
- compare  
- explain  
- reproduce  
- deploy  
- learn  

Every feature should reinforce that identity.

If a future feature does not strengthen Atlas as an **ML Engineering Platform**, question whether it belongs in the product.
