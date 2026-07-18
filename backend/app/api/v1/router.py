"""Aggregate all v1 route modules into a single router.

Health lives at the app root (`/health`), not under `/api/v1`,
so load balancers get a stable, unversioned probe path.
"""

from fastapi import APIRouter

from app.api.v1.routes import auth, datasets, deployments, experiments, projects

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(datasets.router)
api_router.include_router(experiments.router)
api_router.include_router(deployments.router)
