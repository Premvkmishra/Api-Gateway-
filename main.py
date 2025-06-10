from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn

from routes.auth import router as auth_router
from routes.services import router as services_router
from routes.admin import router as admin_router
from routes.dashboard import router as dashboard_router
from middleware.logging import logging_middleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("IntelliRoute API Gateway starting up...")
    yield
    print("IntelliRoute API Gateway shutting down...")

app = FastAPI(
    title="IntelliRoute API Gateway",
    description="Intelligent API Router with authentication, rate limiting, and logging",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(logging_middleware)

app.include_router(auth_router)
app.include_router(services_router)
app.include_router(admin_router)
app.include_router(dashboard_router)

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    import os
    os.makedirs("static", exist_ok=True)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)