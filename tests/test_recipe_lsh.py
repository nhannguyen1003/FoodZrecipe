import pytest
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, MetaData
from sqlalchemy.pool import StaticPool
from typing import List

from tests.test_models import TestRecipe, TestUser, UserRole, TestBase
from database.repositories.base_repository import BaseRepository
from backend.schemas.recipe import RecipeCreate, RecipeUpdate

class TestRecipeRepository(BaseRepository[TestRecipe, RecipeCreate, RecipeUpdate]):
    """Test repository class that mimics the actual RecipeRepository but works with SQLite"""
    
    def get_by_user_id(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[TestRecipe]:
        return db.query(TestRecipe).filter(TestRecipe.user_id == user_id).offset(skip).limit(limit).all()
    
    def get_by_category(self, db: Session, *, category: str, skip: int = 0, limit: int = 100) -> List[TestRecipe]:
        return db.query(TestRecipe).filter(TestRecipe.categories.contains([category])).offset(skip).limit(limit).all()
    
    def search_by_text_lsh(self, db: Session, *, hash_buckets: List[int], skip: int = 0, limit: int = 100) -> List[TestRecipe]:
        """Find recipes that share any hash buckets with the query text - SQLite implementation"""
        results = []
        all_recipes = db.query(TestRecipe).all()
        for recipe in all_recipes:
            if recipe.text_hash_buckets:
                # Manual overlap check for SQLite (which doesn't have array overlap)
                if any(bucket in recipe.text_hash_buckets for bucket in hash_buckets):
                    results.append(recipe)
        
        return results[skip:skip+limit]
    
    def search_by_image_lsh(self, db: Session, *, hash_buckets: List[int], skip: int = 0, limit: int = 100) -> List[TestRecipe]:
        """Find recipes that share any hash buckets with the query image - SQLite implementation"""
        results = []
        all_recipes = db.query(TestRecipe).all()
        for recipe in all_recipes:
            if recipe.image_hash_buckets:
                # Manual overlap check for SQLite
                if any(bucket in recipe.image_hash_buckets for bucket in hash_buckets):
                    results.append(recipe)
        
        return results[skip:skip+limit]
    
    def search_by_hybrid_lsh(self, db: Session, *, hash_buckets: List[int], skip: int = 0, limit: int = 100) -> List[TestRecipe]:
        """Find recipes using combined hash buckets or individual hash buckets - SQLite implementation"""
        results = []
        all_recipes = db.query(TestRecipe).all()
        for recipe in all_recipes:
            # Check all three hash bucket types
            has_overlap = False
            
            if recipe.combined_hash_buckets and any(bucket in recipe.combined_hash_buckets for bucket in hash_buckets):
                has_overlap = True
            elif recipe.text_hash_buckets and any(bucket in recipe.text_hash_buckets for bucket in hash_buckets):
                has_overlap = True
            elif recipe.image_hash_buckets and any(bucket in recipe.image_hash_buckets for bucket in hash_buckets):
                has_overlap = True
                
            if has_overlap:
                results.append(recipe)
        
        return results[skip:skip+limit]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5
        
        if mag1 * mag2 == 0:
            return 0.0
            
        return dot_product / (mag1 * mag2)
    
    def rank_by_similarity(self, db: Session, *, query_vector: List[float], candidates: List[TestRecipe], use_image: bool = False) -> List[TestRecipe]:
        """Re-rank recipe candidates based on cosine similarity with query vector"""
        results = []
        for recipe in candidates:
            if use_image:
                vector = recipe.image_feature_vector
            else:
                vector = recipe.text_feature_vector
                
            if vector:
                similarity = self._cosine_similarity(query_vector, vector)
                results.append((recipe, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the recipes in order of similarity
        return [r[0] for r in results]


test_recipe_repository = TestRecipeRepository(TestRecipe)


@pytest.fixture
def db():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestBase.metadata.create_all(bind=engine)
    
    conn = engine.connect()
    transaction = conn.begin()
    
    # Create a Session with the connection
    session = Session(bind=conn)
    
    yield session
    
    # Clean up
    session.close()
    transaction.rollback()
    conn.close()


@pytest.fixture
def test_user(db):
    """Create a test user"""
    user = TestUser(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword",
        role=UserRole.REGULAR,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_recipes(db, test_user):
    """Create several test recipes with LSH data"""
    recipes = [
        TestRecipe(
            title="Pancakes",
            description="Classic breakfast recipe",
            ingredients=["flour", "eggs", "milk", "sugar"],
            instructions=["Mix", "Cook", "Serve"],
            categories=["breakfast", "sweet"],
            prep_time=10,
            cook_time=15,
            servings=4,
            user_id=test_user.id,
            text_feature_vector=[0.1, 0.2, 0.3, 0.4],
            text_hash_buckets=[1, 3, 5],
            image_feature_vector=[0.2, 0.3, 0.4, 0.5],
            image_hash_buckets=[2, 4, 6],
            combined_hash_buckets=[1, 2, 5]
        ),
        TestRecipe(
            title="Spaghetti Carbonara",
            description="Italian pasta dish",
            ingredients=["pasta", "eggs", "cheese", "bacon"],
            instructions=["Cook pasta", "Mix ingredients", "Serve hot"],
            categories=["dinner", "pasta", "italian"],
            prep_time=15,
            cook_time=25,
            servings=2,
            user_id=test_user.id,
            text_feature_vector=[0.3, 0.4, 0.5, 0.6],
            text_hash_buckets=[5, 7, 9],
            image_feature_vector=[0.4, 0.5, 0.6, 0.7],
            image_hash_buckets=[4, 6, 8],
            combined_hash_buckets=[5, 6, 9]
        ),
        TestRecipe(
            title="Chocolate Cake",
            description="Rich dessert",
            ingredients=["flour", "sugar", "chocolate", "eggs"],
            instructions=["Mix dry ingredients", "Add wet ingredients", "Bake", "Frost"],
            categories=["dessert", "baking", "sweet"],
            prep_time=30,
            cook_time=45,
            servings=8,
            user_id=test_user.id,
            text_feature_vector=[0.5, 0.6, 0.7, 0.8],
            text_hash_buckets=[7, 9, 11],
            image_feature_vector=[0.6, 0.7, 0.8, 0.9],
            image_hash_buckets=[6, 8, 10],
            combined_hash_buckets=[7, 8, 11]
        ),
    ]
    
    for recipe in recipes:
        db.add(recipe)
    
    db.commit()
    
    # Refresh the recipes to get their IDs
    for recipe in recipes:
        db.refresh(recipe)
    
    return recipes


class TestRecipeLSH:
    def test_text_lsh_search(self, db, test_recipes):
        """Test searching recipes by text LSH hash buckets"""
        # Search with hash buckets that match the first recipe
        results = test_recipe_repository.search_by_text_lsh(db, hash_buckets=[1, 2])
        assert len(results) == 1
        assert results[0].title == "Pancakes"
        
        # Search with hash buckets that match multiple recipes
        results = test_recipe_repository.search_by_text_lsh(db, hash_buckets=[5, 6])
        assert len(results) == 2
        assert any(r.title == "Pancakes" for r in results)
        assert any(r.title == "Spaghetti Carbonara" for r in results)
        
        # Search with hash buckets that don't match any recipes
        results = test_recipe_repository.search_by_text_lsh(db, hash_buckets=[13, 15])
        assert len(results) == 0
    
    def test_image_lsh_search(self, db, test_recipes):
        """Test searching recipes by image LSH hash buckets"""
        # Search with hash buckets that match the first recipe
        results = test_recipe_repository.search_by_image_lsh(db, hash_buckets=[2, 3])
        assert len(results) == 1
        assert results[0].title == "Pancakes"
        
        # Search with hash buckets that match multiple recipes
        results = test_recipe_repository.search_by_image_lsh(db, hash_buckets=[6, 7])
        assert len(results) == 3
        
        # Search with hash buckets that don't match any recipes
        results = test_recipe_repository.search_by_image_lsh(db, hash_buckets=[12, 14])
        assert len(results) == 0
    
    def test_hybrid_lsh_search(self, db, test_recipes):
        """Test searching recipes using the hybrid LSH approach"""
        # This should match recipes that have any overlap in any bucket type
        results = test_recipe_repository.search_by_hybrid_lsh(db, hash_buckets=[1, 6, 11])
        assert len(results) == 3  # Should match all 3 recipes
        
        # More specific search
        results = test_recipe_repository.search_by_hybrid_lsh(db, hash_buckets=[1])
        assert len(results) == 1
        assert results[0].title == "Pancakes"
    
    def test_similarity_ranking(self, db, test_recipes):
        """Test ranking recipes by vector similarity"""
        # Query vector closer to recipe 3
        query_vector = [0.5, 0.6, 0.7, 0.8]
        
        # Get all recipes as candidates
        candidates = test_recipes
        
        # Rank by text similarity
        ranked_results = test_recipe_repository.rank_by_similarity(
            db, query_vector=query_vector, candidates=candidates, use_image=False
        )
        
        # Expect recipe 3 to be first (highest similarity to query)
        assert ranked_results[0].title == "Chocolate Cake"
        
        # Rank by image similarity (different vectors)
        ranked_results = test_recipe_repository.rank_by_similarity(
            db, query_vector=query_vector, candidates=candidates, use_image=True
        )
        
        # With our test data, still expect recipe 3 to be most similar
        assert ranked_results[0].title == "Chocolate Cake" 