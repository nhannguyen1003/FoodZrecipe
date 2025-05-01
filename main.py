import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

from backend.api import auth, recipe, search, admin
from backend.core.startup import init_app

# Create FastAPI app
app = FastAPI(title="Food Recipe App with LSH Search")

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

@app.on_event("startup")
def startup_event():
    """
    Initialize application on startup
    """
    # Initialize LSH indices and other startup tasks
    init_app()

@app.get("/")
def root():
    """
    Root endpoint, can be used for health checks
    """
    return {"message": "Welcome to the Food Recipe API with LSH Search"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 