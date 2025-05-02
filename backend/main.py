import uvicorn
import sys
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Add parent directory to path to allow imports from project root
sys.path.append(str(Path(__file__).parent.parent))
from config import settings

# Import API routers
from api import auth, recipe, search, admin, health, category, image
from core.startup import init_app
from core.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize LSH indices and other startup tasks
    logger.info("Starting application...")
    init_app()
    logger.info("Application startup completed")
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

# Mount static directories
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    # Mount food-images directory
    food_images_dir = os.path.join(static_dir, "food-images")
    if os.path.exists(food_images_dir):
        app.mount("/food-images", StaticFiles(directory=food_images_dir), name="food-images")
        logger.info(f"Mounted food images directory at {food_images_dir}")
    else:
        logger.warning(f"Food images directory not found at {food_images_dir}")
        os.makedirs(food_images_dir, exist_ok=True)
        logger.info(f"Created food images directory at {food_images_dir}")
    
    # Mount categories directory
    categories_dir = os.path.join(static_dir, "categories")
    if os.path.exists(categories_dir):
        app.mount("/categories", StaticFiles(directory=categories_dir), name="categories")
        logger.info(f"Mounted categories directory at {categories_dir}")
    else:
        logger.warning(f"Categories directory not found at {categories_dir}")
        os.makedirs(categories_dir, exist_ok=True)
        logger.info(f"Created categories directory at {categories_dir}")
    
    # Mount placeholders directory
    placeholders_dir = os.path.join(static_dir, "placeholders")
    if os.path.exists(placeholders_dir):
        app.mount("/placeholders", StaticFiles(directory=placeholders_dir), name="placeholders")
        logger.info(f"Mounted placeholders directory at {placeholders_dir}")
    else:
        logger.warning(f"Placeholders directory not found at {placeholders_dir}")
        os.makedirs(placeholders_dir, exist_ok=True)
        logger.info(f"Created placeholders directory at {placeholders_dir}")
else:
    logger.warning(f"Static directory not found at {static_dir}")
    os.makedirs(static_dir, exist_ok=True)
    logger.info(f"Created static directory at {static_dir}")

# For backwards compatibility, still mount the original dirs if they exist
if os.path.exists(settings.FOOD_IMAGES_DIR):
    app.mount("/original-food-images", StaticFiles(directory=settings.FOOD_IMAGES_DIR), name="original-food-images")
    logger.info(f"Mounted original food images directory at {settings.FOOD_IMAGES_DIR}")

if os.path.exists(settings.SIMPLE_IMAGES_DIR):
    app.mount("/original-images", StaticFiles(directory=settings.SIMPLE_IMAGES_DIR), name="original-images")
    logger.info(f"Mounted original images directory at {settings.SIMPLE_IMAGES_DIR}")

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