from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import uvicorn
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.routes import user, analysis, data_product, model_training
from app.core.exceptions import ResourceNotFoundException
from app.core.database import create_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle events for the FastAPI application
    """
    # Create database tables on startup
    create_tables()
    logger.info("Database tables created")
    yield
    # Cleanup on shutdown
    logger.info("Application shutting down")


app = FastAPI(
    title="AgReX API",
    description="API for agricultural data analysis and model training",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response


# Exception handler for ResourceNotFoundException
@app.exception_handler(ResourceNotFoundException)
async def resource_not_found_exception_handler(request: Request, exc: ResourceNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"message": str(exc)},
    )


# Include API routers
app.include_router(user.router, prefix="/api/users", tags=["Users"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(data_product.router, prefix="/api/data-products", tags=["Data Products"])
app.include_router(model_training.router, prefix="/api/model-training", tags=["Model Training"])


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify API is running
    """
    return {"status": "healthy", "version": settings.VERSION}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)