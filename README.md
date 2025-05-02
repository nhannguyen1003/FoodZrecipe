# FoodZrecipe

A recipe application with text and image-based search capabilities.

## Project Structure

The application follows a clean architecture with clear separation of concerns:

- **Frontend**: React-based UI for recipe browsing and searching
- **Backend**: FastAPI for API endpoints and business logic
- **Database**: PostgreSQL for data storage with SQLAlchemy ORM

## Database Repository Pattern

The application implements the repository pattern to provide a consistent interface for database operations:

### Base Repository

The `BaseRepository` class in `database/repositories/base_repository.py` provides:

- Standard CRUD operations (Create, Read, Update, Delete)
- Transaction support for multi-operation tasks
- Error handling with detailed logging
- Pagination for list operations
- Filter-based queries

### Usage

Example of using the repository pattern:

```python
# Create a repository for a specific model
user_repository = BaseRepository[User, UserCreate, UserUpdate](User)

# Get a user by ID
user = user_repository.get(db, id=user_id)

# Create a new user
new_user = user_repository.create(db, obj_in=user_data)

# Update a user
updated_user = user_repository.update(db, db_obj=user, obj_in=update_data)

# Use a transaction for multi-operation tasks
with user_repository.transaction(db) as tx_db:
    user1 = user_repository.create(tx_db, obj_in=user1_data)
    user2 = user_repository.create(tx_db, obj_in=user2_data)
```

## Data Seeding

The application includes a data seeding mechanism that:

1. Creates admin and regular user accounts
2. Loads recipe data from `data/db/processed_data.json`
3. Generates feature vectors and LSH hash buckets for each recipe
4. Inserts the data into the database

### Running the Seeding Process

You can run the seeding process in several ways:

1. **Automatically** - The application will run seeding on startup if the database is empty
2. **Manual CLI** - Run the seeding script directly:
   ```bash
   python scripts/run_seeding.py
   ```
3. **During DB initialization** - Using the `--seed` flag:
   ```bash
   python database/init_db.py --seed
   ```
4. **Forced reseeding** - Set the `FORCE_SEED` environment variable to force reseeding:
   ```bash
   FORCE_SEED=true python main.py
   ```

### Customizing Seed Data

The seeding process:
- Uses admin/regular users with predefined credentials
- Processes all recipes in the JSON file
- Generates LSH hash buckets automatically for efficient search
- Assigns recipes to both admin and regular users for testing

## Testing

Run tests using pytest:

```bash
cd tests
python -m pytest
```

## Documentation

The project includes various documentation:

1. Recipe data model documentation
2. API endpoint documentation
3. LSH search algorithm documentation 
4. Multi-field search implementation details
5. [Multi-field search limitations](docs/multi_field_search_limitations.md) - Known limitations of the current MVP implementation

## License

MIT
