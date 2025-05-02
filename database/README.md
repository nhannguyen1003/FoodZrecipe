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

# Database Management

This directory contains database-related code for the FoodZrecipe application, including schema definitions, migrations, and session management.

## Database Setup

### For New Installations

For new installations, use the comprehensive schema setup script:

```bash
python -m data.put_schemas_to_db [--force]
```

This script:
- Creates all required tables with the correct schema
- Handles table relationships
- Creates a default admin user
- Supports forcing recreation of tables with the `--force` flag

### For Existing Installations

For existing installations that need to update their schema:

```bash
python -m database.run_migrations [--mode MODE]
```

Available modes:
- `schema` (default): Run the comprehensive schema setup
- `migrations`: Run individual migrations
- `all`: Run both schema setup and individual migrations

## Migration System

The migration system has evolved:

### Legacy Approach (Deprecated)

Originally, migrations were handled by:
- `database/migrations.py`: A single script with multiple migration functions
- Individual migration files in `database/migrations/`

### Current Approach

The current approach uses:
- `data/put_schemas_to_db.py`: Comprehensive schema creation/update
- `database/run_migrations.py`: Migration management script
- Individual migration files (for backward compatibility)

## Directory Structure

- `database/session.py`: Database session management
- `database/models/`: SQLAlchemy model definitions
- `database/migrations/`: Individual migration scripts
- `data/put_schemas_to_db.py`: Comprehensive schema setup
- `data/put_data_to_db.py`: Data loading script

## Multi-Field LSH Implementation

The database schema now supports multi-field LSH embeddings for recipe search:

- `title_feature_vector`: 64-dimensional vector for recipe title
- `title_hash_buckets`: Hash buckets for title LSH
- `ingredients_feature_vector`: 128-dimensional vector for ingredients
- `ingredients_hash_buckets`: Hash buckets for ingredients LSH
- `instructions_feature_vector`: 256-dimensional vector for instructions
- `instructions_hash_buckets`: Hash buckets for instructions LSH
- `text_feature_vector`: 128-dimensional vector for full text (legacy)
- `text_hash_buckets`: Hash buckets for full text LSH (legacy)

This implementation provides more precise searching by treating different recipe components separately. 