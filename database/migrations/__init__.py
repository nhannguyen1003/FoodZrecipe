"""
Database migrations package.

This package contains database migration scripts for the FoodZrecipe application.

Note: Many of these migrations are now redundant with the introduction of 
the comprehensive schema creation script at data/put_schemas_to_db.py.

For new installations, it's recommended to use the put_schemas_to_db.py script
instead of running individual migrations.
"""

# Import migrations for backward compatibility
from database.migrations.add_multi_field_lsh import migrate_recipes_for_multi_field_lsh
from database.migrations.add_categories import migrate_recipes_for_categories

__all__ = [
    'migrate_recipes_for_multi_field_lsh',
    'migrate_recipes_for_categories',
]
