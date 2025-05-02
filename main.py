import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
import os

from backend.api import auth, recipe, search, admin, health, category, image
from backend.core.startup import init_app
from backend.core.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize LSH indices and other startup tasks
    logger.info("Starting application...")
    init_app()
    logger.info("Application startup completed")

    # Mount Food Images directory
    if os.path.exists(settings.FOOD_IMAGES_DIR):
        app.mount("/food-images", StaticFiles(directory=settings.FOOD_IMAGES_DIR), name="food-images")
        logger.info(f"Mounted food images directory at {settings.FOOD_IMAGES_DIR}")
    else:
        logger.warning(f"Food images directory not found at {settings.FOOD_IMAGES_DIR}")
        
    # Mount Static Food Images directory
    if os.path.exists(settings.STATIC_FOOD_IMAGES_DIR):
        app.mount("/static/food-images", StaticFiles(directory=settings.STATIC_FOOD_IMAGES_DIR), name="static-food-images")
        logger.info(f"Mounted static food images directory at {settings.STATIC_FOOD_IMAGES_DIR}")
    else:
        logger.warning(f"Static food images directory not found at {settings.STATIC_FOOD_IMAGES_DIR}")

    # Mount Simple Images directory
    if os.path.exists(settings.SIMPLE_IMAGES_DIR):
        app.mount("/images", StaticFiles(directory=settings.SIMPLE_IMAGES_DIR), name="images")
        logger.info(f"Mounted simple images directory at {settings.SIMPLE_IMAGES_DIR}")
    else:
        logger.warning(f"Simple images directory not found at {settings.SIMPLE_IMAGES_DIR}")

    # Mount frontend public images directory for fallback images
    frontend_public_images = os.path.join(os.getcwd(), "frontend", "public", "images")
    if os.path.exists(frontend_public_images):
        app.mount("/public/images", StaticFiles(directory=frontend_public_images), name="public-images")
        logger.info(f"Mounted frontend public images directory at {frontend_public_images}")
    else:
        logger.warning(f"Frontend public images directory not found at {frontend_public_images}")

    yield
    logger.info("Application shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Food Recipe App with LSH Search",
    description="A recipe application with text and image-based search capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["authentication"])
app.include_router(recipe.router, prefix=f"{settings.API_PREFIX}/recipes", tags=["recipes"])
app.include_router(search.router, prefix=f"{settings.API_PREFIX}/search", tags=["search"])
app.include_router(admin.router, prefix=f"{settings.API_PREFIX}/admin", tags=["admin"])
app.include_router(health.router, prefix=f"{settings.API_PREFIX}/health", tags=["health"])
app.include_router(category.router, prefix=f"{settings.API_PREFIX}/categories", tags=["categories"])
app.include_router(image.router, prefix=f"{settings.API_PREFIX}/images", tags=["images"])

@app.get("/")
def root():
    """
    Root endpoint, can be used for health checks
    """
    logger.debug("Root endpoint called")
    return {"message": "Welcome to the Food Recipe API with LSH Search"}

if __name__ == "__main__":
    logger.info(f"Starting server on port 8000, debug mode: {settings.DEBUG}")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG) 