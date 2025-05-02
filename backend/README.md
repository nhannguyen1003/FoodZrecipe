# FoodZrecipe Backend

The backend for FoodZrecipe is built with FastAPI, providing a high-performance API for the recipe application with both text and image-based search capabilities.

## Architecture

The backend follows a modern, scalable architecture with clear separation of concerns:

- **API**: Endpoints for recipe management, search, authentication and administration
- **Models**: SQLAlchemy ORM models for database interaction
- **Schemas**: Pydantic models for request/response validation
- **Core**: Core functionality and utilities
- **Services**: Business logic services

## Project Structure

```
backend/
├── api/                # API endpoints organized by domain
│   ├── auth.py         # Authentication endpoints
│   ├── recipe.py       # Recipe management endpoints
│   ├── search.py       # Text and image search endpoints
│   └── admin.py        # Admin-only endpoints
├── core/               # Core application functionality
│   ├── security.py     # Security utilities (JWT, password hashing)
│   └── startup.py      # Application startup/initialization logic
├── models/             # SQLAlchemy ORM models
│   ├── user.py         # User model
│   └── recipe.py       # Recipe model
├── schemas/            # Pydantic models for request/response validation
│   ├── user.py         # User schemas
│   └── recipe.py       # Recipe schemas
└── services/           # Business logic services
    └── lsh_service.py  # LSH-based similarity search service
```

## Database

Database functionality is organized in a separate directory at the project root:

```
database/
├── base.py              # Base table definitions and model registration
├── init_db.py           # Database initialization
├── session.py           # SQLAlchemy session management
└── repositories/        # Repository pattern implementation
    ├── base_repository.py     # Generic CRUD operations
    ├── user_repository.py     # User-specific operations
    └── recipe_repository.py   # Recipe-specific operations with LSH
```

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Poetry (optional but recommended for dependency management)

### Setting Up the Development Environment

1. Install required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file:

```
# Database settings
POSTGRES_USER=app_user
POSTGRES_PASSWORD=app_password
POSTGRES_DB=food_recipe
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Security settings
SECRET_KEY=your-secret-key-for-jwt-tokens
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application settings
DEBUG=true
API_PREFIX=/api/v1

# LSH settings
LSH_HASH_SIZE=8
LSH_NUM_TABLES=10
```

3. Initialize the database:

```bash
python database/init_db.py
```

4. Run the development server:

```bash
./scripts/run_backend.py
```

## API Endpoints

The API is structured with a prefix defined in configuration (default: `/api/v1`):

### Authentication

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration

### Recipes

- `GET /api/v1/recipes` - List all recipes
- `GET /api/v1/recipes/{id}` - Get recipe by ID
- `POST /api/v1/recipes` - Create new recipe
- `PUT /api/v1/recipes/{id}` - Update recipe
- `DELETE /api/v1/recipes/{id}` - Delete recipe

### Search

- `GET /api/v1/search/text` - Text-based recipe search
- `POST /api/v1/search/image` - Image-based recipe search

### Admin

- `GET /api/v1/admin/users` - List all users
- `GET /api/v1/admin/stats` - Get application statistics

## Dependency Injection

The backend uses FastAPI's dependency injection system, especially for:

- Database session management
- Authentication and authorization
- Error handling

Example:

```python
@router.get("/recipes/", response_model=List[RecipeOut])
def get_recipes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all recipes for the current user."""
    return recipe_repository.get_multi(db, owner_id=current_user.id)
```

## Testing

Run tests using pytest:

```bash
pytest
```

## Development Guidelines

1. Follow the established structure for new endpoints
2. Add proper validation with Pydantic schemas
3. Use the repository pattern for database operations
4. Document new endpoints in OpenAPI/Swagger
5. Write unit tests for new functionality

## Authentication System

The FoodZrecipe app uses JWT (JSON Web Tokens) for secure authentication. The system supports:

- User registration with secure password hashing using bcrypt
- Login with username/password credentials
- Role-based access control (admin vs regular users)
- Token-based API authentication
- Protected routes that require authentication

### Authentication Flow

1. Register a new user at `/api/v1/auth/register`
2. Login to get a JWT access token at `/api/v1/auth/login`
3. Include the token in subsequent requests using the `Authorization: Bearer <token>` header
4. Use the `/api/v1/auth/me` endpoint to get current user information
5. The token contains role information for role-based permissions

### User Roles

- **Regular Users**: Can create and manage their own recipes, search for recipes
- **Admin Users**: Have access to special admin endpoints, system monitoring, and configuration

### Security Features

- Secure password hashing with bcrypt
- JWT tokens with expiration
- Role-based access control
- Protected API endpoints

### Testing Authentication

You can test the authentication system using the provided test script:

```
python tests/integ/test_auth_api.py
```

Default accounts for testing:
- Admin user: `admin`/`admin`
- Regular user: `user`/`password` 