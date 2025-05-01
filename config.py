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
    
    # File upload settings
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "data", "uploads")
    
    # LSH parameters - Original names (for backwards compatibility with tests)
    LSH_HASH_SIZE: int = 8
    LSH_NUM_TABLES: int = 10
    
    # FAISS LSH parameters (used by the application)
    LSH_VECTOR_DIM: int = 128   # Dimensionality of feature vectors
    LSH_HASH_BITS: int = 32     # Number of bits for LSH hashing
    
    # Model config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",  # Allow extra fields to avoid validation errors
    )

# Create settings instance
settings = Settings() 