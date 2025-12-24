from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import users

app = FastAPI(
    title="Mithaly Project Management API",
    description="Production API - Converted from educational examples to real system",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
# future routers: projects, tasks


@app.get("/")
async def root():
    return {
        "message": "Welcome to Mithaly Project Management API",
        "version": "2.0.0",
        "status": "production",
        "note": "This is a real FastAPI application, not educational examples",
    }


@app.get("/health")
async def health_check():
    from datetime import datetime

    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
