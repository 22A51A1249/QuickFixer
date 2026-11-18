"""Main FastAPI application entry point for QuickFixer Enterprise."""

from __future__ import annotations

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.auth import router as auth_router
from backend.api.chat import router as chat_router
from backend.api.tickets import router as tickets_router
from backend.api.dashboard import router as dashboard_router
from backend.api.users import router as users_router
from backend.api.knowledge import router as knowledge_router
from backend.api.settings import router as settings_router

app = FastAPI(
    title="QuickFixer Enterprise IT Support API",
    description="AI-Powered Enterprise IT Support & Intelligent Issue Resolution Platform REST API",
    version="3.0.0",
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(tickets_router)
app.include_router(dashboard_router)
app.include_router(users_router)
app.include_router(knowledge_router)
app.include_router(settings_router)

# Mount frontend build directory if built
FRONTEND_DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIST_DIR.exists() and (FRONTEND_DIST_DIR / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API routes to be handled by routers
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        target_file = FRONTEND_DIST_DIR / full_path
        if target_file.exists() and target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(FRONTEND_DIST_DIR / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "name": "QuickFixer Enterprise IT Support API",
            "tagline": "Identify. Diagnose. Resolve.",
            "status": "operational",
            "docs": "/docs",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

