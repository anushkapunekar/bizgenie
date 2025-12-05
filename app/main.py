"""
BizGenie - Main FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.database import init_db
from app.routes import chat, business, tools, appointments

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="BizGenie API",
    description="Micro-SaaS small-business support AI agent",
    version="1.0.0",
)

# CORS for frontend http://localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(chat.router)
app.include_router(business.router)
app.include_router(tools.router)
app.include_router(appointments.router)


@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Database tables verified/created")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down BizGenie application")


@app.get("/")
async def root():
    return {
        "message": "Welcome to BizGenie API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
