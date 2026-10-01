from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import (
    admin_users,
    alerts,
    analysis,
    auth,
    clients,
    history,
    reports,
)


app = FastAPI(
    title="FinGuard API",
    version="1.0.0",
    description=(
        "AI-powered financial risk detection "
        "and business intelligence platform."
    ),
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(
    auth.router
)

app.include_router(
    analysis.router
)

app.include_router(
    history.router
)

app.include_router(
    alerts.router
)

app.include_router(
    reports.router
)

app.include_router(
    clients.router
)

app.include_router(
    admin_users.router
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "FinGuard API",
        "status": "running",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }