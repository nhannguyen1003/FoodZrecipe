import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # PostgreSQL Database Settings
    POSTGRES_USER: str = "app_user"
    POSTGRES_PASSWORD: str = "app_password"
    POSTGRES_DB: str = "food_recipe"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    
    # Constructed database URL
    @property
    def DATABASE_URL(self) -> str:
        """
        Constructs and returns the PostgreSQL connection URL.
        Format: postgresql://{user}:{password}@{host}:{port}/{db}
        """
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-for-jwt-tokens"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application settings
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    # File upload settings - original paths (for backwards compatibility)
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "data", "uploads")
    FOOD_IMAGES_DIR: str = os.path.join(os.getcwd(), "data", "db", "Food Images", "Food Images")
    SIMPLE_IMAGES_DIR: str = os.path.join(os.getcwd(), "data", "images")
    
    # Static files settings - new structure
    STATIC_DIR: str = os.path.join(os.getcwd(), "backend", "static")
    STATIC_FOOD_IMAGES_DIR: str = os.path.join(STATIC_DIR, "food-images")
    STATIC_CATEGORIES_DIR: str = os.path.join(STATIC_DIR, "categories")
    STATIC_PLACEHOLDERS_DIR: str = os.path.join(STATIC_DIR, "placeholders")
    
    # Set the upload directory to the food-images directory
    _image_upload_dir: str = None
    
    @property
    def IMAGE_UPLOAD_DIR(self) -> str:
        """
        Returns the directory where uploaded images should be stored.
        This is set to the food-images directory since uploaded images are for recipes.
        """
        if self._image_upload_dir is not None:
            return self._image_upload_dir
        return self.STATIC_FOOD_IMAGES_DIR
        
    @IMAGE_UPLOAD_DIR.setter
    def IMAGE_UPLOAD_DIR(self, value: str) -> None:
        """
        Sets the directory where uploaded images should be stored.
        """
        self._image_upload_dir = value
    
    # LSH parameters - Original names (for backwards compatibility with tests)
    LSH_HASH_SIZE: int = 8
    LSH_NUM_TABLES: int = 10
    
    # FAISS LSH parameters (used by the application)
    LSH_VECTOR_DIM: int = 128   # Dimensionality of feature vectors
    LSH_HASH_BITS: int = 32     # Number of bits for LSH hashing
    
    # Multi-field LSH parameters
    LSH_TITLE_DIM: int = 64     # Dimensionality for title vectors
    LSH_TITLE_BITS: int = 32    # Hash bits for title vectors
    LSH_INGREDIENTS_DIM: int = 128  # Dimensionality for ingredients vectors
    LSH_INGREDIENTS_BITS: int = 64  # Hash bits for ingredients vectors
    LSH_INSTRUCTIONS_DIM: int = 256  # Dimensionality for instructions vectors
    LSH_INSTRUCTIONS_BITS: int = 128  # Hash bits for instructions vectors
    
    # Feature flag for multi-field search
    USE_MULTI_FIELD_SEARCH: bool = True  # Enable by default
    
    # Model config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",  # Allow extra fields to avoid validation errors
    )

# Create settings instance
settings = Settings() 