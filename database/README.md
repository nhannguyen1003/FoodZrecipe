# Database Component

## Overview
The database layer of FoodZrecipe uses PostgreSQL with SQLAlchemy ORM and is designed for high-performance recipe search and retrieval. It implements a repository pattern for data access and supports vector search for similarity-based recipe search.

## Key Components

### `session.py`
- Database connection and session management
- SQLAlchemy engine configuration with connection pooling
- Session dependency for FastAPI routes
- Functions for database initialization and testing

### `base.py`
- Registration of all models for SQLAlchemy
- Ensures models are available for Alembic migrations

### `init_db.py`
- Database initialization script
- Creates initial admin user
- Supports data seeding

### Repositories
Repository pattern implementations for database operations:

#### `repositories/base_repository.py`
- Generic CRUD operations for all models
- Transaction management
- Error handling and logging

#### `repositories/user_repository.py`
- User-specific operations
- Authentication-related operations

#### `repositories/recipe_repository.py`
- Recipe-specific operations
- Text and image-based search capabilities using vector similarity

## Models
Database models are defined in the `backend/models` directory:

### `User` model
- Account management
- Role-based permissions (admin, regular)
- Relationships to recipes

### `Recipe` model
- Comprehensive recipe data
- Support for text and image features
- Vector search capabilities

## Usage

### Initializing the database
```python
# Import initialization function
from database.init_db import init_db
from database.session import SessionLocal

# Get database session
db = SessionLocal()

# Initialize database
init_db(db)
```

### Using repositories
```python
# Import repositories
from database.repositories.user_repository import UserRepository
from database.repositories.recipe_repository import RecipeRepository
from database.session import get_db

# Create repository instances
user_repo = UserRepository()
recipe_repo = RecipeRepository()

# Use repositories in FastAPI endpoint
@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    return user_repo.get(db, user_id)
```

## Search Capabilities
The database layer supports sophisticated search functionality:
- Full-text search
- Vector similarity search for images
- Hybrid search combining text and images
- Locality-Sensitive Hashing (LSH) for efficient similarity search 