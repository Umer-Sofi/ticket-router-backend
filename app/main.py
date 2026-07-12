"""FastAPI entrypoint. Uvicorn runs THIS module (`app.main:app`).

For now it only exposes /health. Later phases will register the
ticket-routing router here.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Ticket Router")

# CORS = which browser origins may call this API. The Next.js dev server runs
# on http://localhost:3000, and browsers block cross-origin calls unless the
# server explicitly allows them. Without this, the frontend fetch fails in
# Phase 11. (Tighten this list before deploying.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Liveness check: proves the server process is up. Touches nothing else."""
    return {"status": "ok"}
