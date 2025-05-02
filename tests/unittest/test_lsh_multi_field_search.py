import pytest
import json
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, MetaData
from sqlalchemy.pool import StaticPool
from typing import List, Dict, Any, Optional

from tests.unittest.test_models import TestRecipe, TestUser, UserRole, TestBase
from database.repositories.base_repository import BaseRepository
from backend.schemas.recipe import RecipeCreate, RecipeUpdate


class TestMultiFieldRecipe(TestRecipe):
    """Extended test recipe model with multi-field feature vectors"""
    
    # Add field-specific feature vectors
    title_feature_vector = None
    ingredients_feature_vector = None
    instructions_feature_vector = None
    
    # Add field-specific hash buckets
    title_hash_buckets = None
    ingredients_hash_buckets = None
    instructions_hash_buckets = None


class MockMultiFieldLSHService:
    """Mock LSH service for multi-field testing"""
    
    def __init__(self):
        # Initialize basic parameters
        self.title_dim = 64
        self.title_bits = 32
        self.ingredients_dim = 128
        self.ingredients_bits = 64
        self.instructions_dim = 256
        self.instructions_bits = 128
        
        # Initialize indices (these would be FAISS indices in real implementation)
        self.title_index = None
        self.ingredients_index = None
        self.instructions_index = None
        
        # Store recipe IDs for mapping FAISS indices to recipes
        self.recipe_ids = []
        
        # Track initialization state
        self.is_initialized = False
    
    def initialize_indices(self):
        """Initialize multi-field LSH indices"""
        # In real implementation, these would be FAISS LSH indices
        # For testing, we'll just use simple mock objects
        self.title_index = {"vectors": [], "dim": self.title_dim, "bits": self.title_bits}
        self.ingredients_index = {"vectors": [], "dim": self.ingredients_dim, "bits": self.ingredients_bits}
        self.instructions_index = {"vectors": [], "dim": self.instructions_dim, "bits": self.instructions_bits}
        self.is_initialized = True
    
    def build_indices(self, recipes: List[TestMultiFieldRecipe]) -> None:
        """Build multi-field LSH indices from recipes"""
        if not self.is_initialized:
            self.initialize_indices()
        
        # Store recipe IDs
        self.recipe_ids = [recipe.id for recipe in recipes]
        
        # Clear existing vectors
        self.title_index["vectors"] = []
        self.ingredients_index["vectors"] = []
        self.instructions_index["vectors"] = []
        
        # Add vectors to indices
        for recipe in recipes:
            # Add title vector if available
            if recipe.title_feature_vector:
                vector = np.array(json.loads(recipe.title_feature_vector), dtype=np.float32)
                self.title_index["vectors"].append((recipe.id, vector))
            
            # Add ingredients vector if available
            if recipe.ingredients_feature_vector:
                vector = np.array(json.loads(recipe.ingredients_feature_vector), dtype=np.float32)
                self.ingredients_index["vectors"].append((recipe.id, vector))
            
            # Add instructions vector if available
            if recipe.instructions_feature_vector:
                vector = np.array(json.loads(recipe.instructions_feature_vector), dtype=np.float32)
                self.instructions_index["vectors"].append((recipe.id, vector))
    
    def search_by_title(self, query_vector: np.ndarray, k: int = 10) -> List[int]:
        """Search for similar recipes by title vector"""
        if not self.is_initialized:
            return []
        
        results = []
        # Simple mock implementation using cosine similarity
        for recipe_id, vector in self.title_index["vectors"]:
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_vector, vector)
            results.append((recipe_id, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k recipe IDs
        return [r[0] for r in results[:k]]
    
    def search_by_ingredients(self, query_vector: np.ndarray, k: int = 10) -> List[int]:
        """Search for similar recipes by ingredients vector"""
        if not self.is_initialized:
            return []
        
        results = []
        # Simple mock implementation using cosine similarity
        for recipe_id, vector in self.ingredients_index["vectors"]:
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_vector, vector)
            results.append((recipe_id, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k recipe IDs
        return [r[0] for r in results[:k]]
    
    def search_by_instructions(self, query_vector: np.ndarray, k: int = 10) -> List[int]:
        """Search for similar recipes by instructions vector"""
        if not self.is_initialized:
            return []
        
        results = []
        # Simple mock implementation using cosine similarity
        for recipe_id, vector in self.instructions_index["vectors"]:
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_vector, vector)
            results.append((recipe_id, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k recipe IDs
        return [r[0] for r in results[:k]]
    
    def weighted_search(self, 
                       title_vector: Optional[np.ndarray] = None, 
                       ingredients_vector: Optional[np.ndarray] = None, 
                       instructions_vector: Optional[np.ndarray] = None, 
                       weights: Optional[Dict[str, float]] = None, 
                       k: int = 10) -> List[int]:
        """
        Search for similar recipes using weighted combination of field-specific searches
        
        Args:
            title_vector: Title embedding vector (optional)
            ingredients_vector: Ingredients embedding vector (optional)
            instructions_vector: Instructions embedding vector (optional)
            weights: Dictionary with weights for each field (optional)
            k: Number of results to return
            
        Returns:
            List of recipe IDs sorted by weighted similarity
        """
        if not self.is_initialized:
            return []
        
        # Default weights if not provided
        if weights is None:
            weights = {
                "title": 0.3,
                "ingredients": 0.4,
                "instructions": 0.3
            }
        
        # Initialize results dictionary to track scores
        recipe_scores = {}
        
        # Search title index if vector provided
        if title_vector is not None and weights.get("title", 0) > 0:
            title_weight = weights.get("title", 0.3)
            title_results = []
            
            for recipe_id, vector in self.title_index["vectors"]:
                similarity = self._cosine_similarity(title_vector, vector)
                title_results.append((recipe_id, similarity))
            
            # Add weighted scores to results
            for recipe_id, similarity in title_results:
                if recipe_id not in recipe_scores:
                    recipe_scores[recipe_id] = 0
                recipe_scores[recipe_id] += similarity * title_weight
        
        # Search ingredients index if vector provided
        if ingredients_vector is not None and weights.get("ingredients", 0) > 0:
            ingredients_weight = weights.get("ingredients", 0.4)
            ingredients_results = []
            
            for recipe_id, vector in self.ingredients_index["vectors"]:
                similarity = self._cosine_similarity(ingredients_vector, vector)
                ingredients_results.append((recipe_id, similarity))
            
            # Add weighted scores to results
            for recipe_id, similarity in ingredients_results:
                if recipe_id not in recipe_scores:
                    recipe_scores[recipe_id] = 0
                recipe_scores[recipe_id] += similarity * ingredients_weight
        
        # Search instructions index if vector provided
        if instructions_vector is not None and weights.get("instructions", 0) > 0:
            instructions_weight = weights.get("instructions", 0.3)
            instructions_results = []
            
            for recipe_id, vector in self.instructions_index["vectors"]:
                similarity = self._cosine_similarity(instructions_vector, vector)
                instructions_results.append((recipe_id, similarity))
            
            # Add weighted scores to results
            for recipe_id, similarity in instructions_results:
                if recipe_id not in recipe_scores:
                    recipe_scores[recipe_id] = 0
                recipe_scores[recipe_id] += similarity * instructions_weight
        
        # Sort recipes by score
        sorted_results = sorted(recipe_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top k recipe IDs
        return [r[0] for r in sorted_results[:k]]
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm_a = np.linalg.norm(vec1)
        norm_b = np.linalg.norm(vec2)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)


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
def test_multi_field_recipes(db, test_user):
    """Create test recipes with field-specific feature vectors"""
    recipes = [
        TestMultiFieldRecipe(
            title="Pancakes with Maple Syrup",
            description="Classic breakfast recipe",
            ingredients=json.dumps(["flour", "eggs", "milk", "sugar", "maple syrup"]),
            instructions=json.dumps(["Mix dry ingredients", "Add wet ingredients", "Cook on griddle", "Serve with syrup"]),
            categories=json.dumps(["breakfast", "sweet"]),
            prep_time=10,
            cook_time=15,
            servings=4,
            user_id=test_user.id,
            # Original single-field vectors
            text_feature_vector=json.dumps([0.1, 0.2, 0.3, 0.4]),
            text_hash_buckets=json.dumps([1, 3, 5]),
            # New field-specific vectors
            title_feature_vector=json.dumps([0.1, 0.3, 0.2, 0.4, 0.1, 0.3, 0.1, 0.2]),
            ingredients_feature_vector=json.dumps([0.2, 0.3, 0.1, 0.5, 0.4, 0.2, 0.1, 0.3, 0.5, 0.2, 0.1, 0.4]),
            instructions_feature_vector=json.dumps([0.1, 0.4, 0.2, 0.3, 0.5, 0.1, 0.2, 0.4, 0.3, 0.1, 0.5, 0.2, 0.3, 0.4, 0.1, 0.2]),
            title_hash_buckets=json.dumps([1, 4, 7]),
            ingredients_hash_buckets=json.dumps([2, 5, 8]),
            instructions_hash_buckets=json.dumps([3, 6, 9])
        ),
        TestMultiFieldRecipe(
            title="Spaghetti Carbonara",
            description="Italian pasta dish",
            ingredients=json.dumps(["pasta", "eggs", "cheese", "bacon", "black pepper"]),
            instructions=json.dumps(["Cook pasta al dente", "Fry bacon until crisp", "Mix eggs and cheese", "Combine all ingredients", "Serve hot with black pepper"]),
            categories=json.dumps(["dinner", "pasta", "italian"]),
            prep_time=15,
            cook_time=25,
            servings=2,
            user_id=test_user.id,
            # Original single-field vectors
            text_feature_vector=json.dumps([0.3, 0.4, 0.5, 0.6]),
            text_hash_buckets=json.dumps([5, 7, 9]),
            # New field-specific vectors
            title_feature_vector=json.dumps([0.5, 0.3, 0.1, 0.4, 0.6, 0.2, 0.1, 0.5]),
            ingredients_feature_vector=json.dumps([0.4, 0.2, 0.6, 0.1, 0.5, 0.3, 0.2, 0.4, 0.1, 0.6, 0.3, 0.2]),
            instructions_feature_vector=json.dumps([0.3, 0.5, 0.1, 0.4, 0.2, 0.6, 0.3, 0.1, 0.5, 0.2, 0.4, 0.6, 0.3, 0.1, 0.5, 0.2]),
            title_hash_buckets=json.dumps([10, 13, 16]),
            ingredients_hash_buckets=json.dumps([11, 14, 17]),
            instructions_hash_buckets=json.dumps([12, 15, 18])
        ),
        TestMultiFieldRecipe(
            title="Chocolate Cake",
            description="Rich dessert",
            ingredients=json.dumps(["flour", "sugar", "chocolate", "eggs", "butter", "baking powder"]),
            instructions=json.dumps(["Preheat oven", "Mix dry ingredients", "Add wet ingredients", "Bake for 45 minutes", "Let cool before frosting"]),
            categories=json.dumps(["dessert", "baking", "sweet"]),
            prep_time=30,
            cook_time=45,
            servings=8,
            user_id=test_user.id,
            # Original single-field vectors
            text_feature_vector=json.dumps([0.5, 0.6, 0.7, 0.8]),
            text_hash_buckets=json.dumps([7, 9, 11]),
            # New field-specific vectors
            title_feature_vector=json.dumps([0.2, 0.5, 0.7, 0.1, 0.3, 0.6, 0.4, 0.2]),
            ingredients_feature_vector=json.dumps([0.3, 0.6, 0.2, 0.5, 0.1, 0.7, 0.4, 0.3, 0.2, 0.5, 0.6, 0.1]),
            instructions_feature_vector=json.dumps([0.4, 0.1, 0.6, 0.2, 0.5, 0.3, 0.7, 0.2, 0.4, 0.6, 0.1, 0.5, 0.3, 0.2, 0.7, 0.4]),
            title_hash_buckets=json.dumps([19, 22, 25]),
            ingredients_hash_buckets=json.dumps([20, 23, 26]),
            instructions_hash_buckets=json.dumps([21, 24, 27])
        ),
        TestMultiFieldRecipe(
            title="Grilled Chicken Salad",
            description="Healthy lunch option",
            ingredients=json.dumps(["chicken breast", "lettuce", "tomatoes", "cucumber", "olive oil", "lemon juice"]),
            instructions=json.dumps(["Grill chicken until cooked through", "Chop vegetables", "Combine all ingredients", "Dress with olive oil and lemon juice"]),
            categories=json.dumps(["lunch", "healthy", "salad"]),
            prep_time=20,
            cook_time=15,
            servings=2,
            user_id=test_user.id,
            # Original single-field vectors
            text_feature_vector=json.dumps([0.4, 0.5, 0.6, 0.7]),
            text_hash_buckets=json.dumps([6, 8, 10]),
            # New field-specific vectors
            title_feature_vector=json.dumps([0.6, 0.2, 0.4, 0.3, 0.5, 0.1, 0.7, 0.2]),
            ingredients_feature_vector=json.dumps([0.5, 0.2, 0.7, 0.3, 0.6, 0.1, 0.4, 0.5, 0.2, 0.3, 0.7, 0.1]),
            instructions_feature_vector=json.dumps([0.2, 0.7, 0.3, 0.5, 0.1, 0.4, 0.6, 0.2, 0.3, 0.7, 0.1, 0.5, 0.4, 0.6, 0.2, 0.3]),
            title_hash_buckets=json.dumps([28, 31, 34]),
            ingredients_hash_buckets=json.dumps([29, 32, 35]),
            instructions_hash_buckets=json.dumps([30, 33, 36])
        ),
    ]
    
    for recipe in recipes:
        db.add(recipe)
    
    db.commit()
    
    # Refresh the recipes to get their IDs
    for recipe in recipes:
        db.refresh(recipe)
    
    return recipes


@pytest.fixture
def mock_lsh_service(test_multi_field_recipes):
    """Create a mock LSH service with test recipes loaded"""
    service = MockMultiFieldLSHService()
    service.initialize_indices()
    service.build_indices(test_multi_field_recipes)
    return service


class TestMultiFieldLSH:
    def test_service_initialization(self, mock_lsh_service):
        """Test initialization of multi-field LSH service"""
        assert mock_lsh_service.is_initialized == True
        assert mock_lsh_service.title_index is not None
        assert mock_lsh_service.ingredients_index is not None
        assert mock_lsh_service.instructions_index is not None
        
        # Check dimensions
        assert mock_lsh_service.title_dim == 64
        assert mock_lsh_service.title_bits == 32
        assert mock_lsh_service.ingredients_dim == 128
        assert mock_lsh_service.ingredients_bits == 64
        assert mock_lsh_service.instructions_dim == 256
        assert mock_lsh_service.instructions_bits == 128
    
    def test_indices_populated(self, mock_lsh_service, test_multi_field_recipes):
        """Test that indices are properly populated with vectors"""
        # Check that title index has vectors
        assert len(mock_lsh_service.title_index["vectors"]) == len(test_multi_field_recipes)
        
        # Check that ingredients index has vectors
        assert len(mock_lsh_service.ingredients_index["vectors"]) == len(test_multi_field_recipes)
        
        # Check that instructions index has vectors
        assert len(mock_lsh_service.instructions_index["vectors"]) == len(test_multi_field_recipes)
    
    def test_title_search(self, mock_lsh_service, test_multi_field_recipes):
        """Test searching recipes by title"""
        # Create a query vector similar to "Chocolate Cake"
        query_vector = np.array([0.2, 0.5, 0.7, 0.2, 0.3, 0.6, 0.4, 0.2], dtype=np.float32)
        
        # Search by title
        results = mock_lsh_service.search_by_title(query_vector, k=2)
        
        # Results should have chocolate cake as the top result
        assert len(results) == 2
        assert results[0] == test_multi_field_recipes[2].id  # Chocolate Cake
    
    def test_ingredients_search(self, mock_lsh_service, test_multi_field_recipes):
        """Test searching recipes by ingredients"""
        # Create a query vector similar to a recipe with "flour, sugar, chocolate"
        query_vector = np.array([0.3, 0.6, 0.2, 0.5, 0.1, 0.7, 0.4, 0.3, 0.2, 0.5, 0.6, 0.1], dtype=np.float32)
        
        # Search by ingredients
        results = mock_lsh_service.search_by_ingredients(query_vector, k=2)
        
        # Results should have chocolate cake as the top result
        assert len(results) == 2
        assert results[0] == test_multi_field_recipes[2].id  # Chocolate Cake
    
    def test_instructions_search(self, mock_lsh_service, test_multi_field_recipes):
        """Test searching recipes by instructions"""
        # Create a query vector similar to pasta cooking instructions
        query_vector = np.array([0.3, 0.5, 0.1, 0.4, 0.2, 0.6, 0.3, 0.1, 0.5, 0.2, 0.4, 0.6, 0.3, 0.1, 0.5, 0.2], dtype=np.float32)
        
        # Search by instructions
        results = mock_lsh_service.search_by_instructions(query_vector, k=2)
        
        # Results should have spaghetti carbonara as the top result
        assert len(results) == 2
        assert results[0] == test_multi_field_recipes[1].id  # Spaghetti Carbonara
    
    def test_weighted_search_equal_weights(self, mock_lsh_service, test_multi_field_recipes):
        """Test weighted search with equal weights"""
        # Create query vectors
        title_vector = np.array([0.2, 0.5, 0.7, 0.1, 0.3, 0.6, 0.4, 0.2], dtype=np.float32)  # Similar to Chocolate Cake
        ingredients_vector = np.array([0.5, 0.2, 0.7, 0.3, 0.6, 0.1, 0.4, 0.5, 0.2, 0.3, 0.7, 0.1], dtype=np.float32)  # Similar to Grilled Chicken
        
        # Search with equal weights
        weights = {"title": 0.5, "ingredients": 0.5, "instructions": 0.0}
        results = mock_lsh_service.weighted_search(
            title_vector=title_vector,
            ingredients_vector=ingredients_vector,
            weights=weights,
            k=3
        )
        
        # Both Chocolate Cake and Grilled Chicken should be in top results
        assert len(results) == 3
        assert test_multi_field_recipes[2].id in results  # Chocolate Cake
        assert test_multi_field_recipes[3].id in results  # Grilled Chicken
    
    def test_weighted_search_title_priority(self, mock_lsh_service, test_multi_field_recipes):
        """Test weighted search with higher title weight"""
        # Create query vectors
        title_vector = np.array([0.2, 0.5, 0.7, 0.1, 0.3, 0.6, 0.4, 0.2], dtype=np.float32)  # Similar to Chocolate Cake
        ingredients_vector = np.array([0.5, 0.2, 0.7, 0.3, 0.6, 0.1, 0.4, 0.5, 0.2, 0.3, 0.7, 0.1], dtype=np.float32)  # Similar to Grilled Chicken
        
        # Search with title prioritized
        weights = {"title": 0.8, "ingredients": 0.2, "instructions": 0.0}
        results = mock_lsh_service.weighted_search(
            title_vector=title_vector,
            ingredients_vector=ingredients_vector,
            weights=weights,
            k=2
        )
        
        # Chocolate Cake should be the top result
        assert len(results) == 2
        assert results[0] == test_multi_field_recipes[2].id  # Chocolate Cake
    
    def test_weighted_search_ingredients_priority(self, mock_lsh_service, test_multi_field_recipes):
        """Test weighted search with higher ingredients weight"""
        # Create query vectors
        title_vector = np.array([0.2, 0.5, 0.7, 0.1, 0.3, 0.6, 0.4, 0.2], dtype=np.float32)  # Similar to Chocolate Cake
        ingredients_vector = np.array([0.5, 0.2, 0.7, 0.3, 0.6, 0.1, 0.4, 0.5, 0.2, 0.3, 0.7, 0.1], dtype=np.float32)  # Similar to Grilled Chicken
        
        # Search with ingredients prioritized
        weights = {"title": 0.2, "ingredients": 0.8, "instructions": 0.0}
        results = mock_lsh_service.weighted_search(
            title_vector=title_vector,
            ingredients_vector=ingredients_vector,
            weights=weights,
            k=2
        )
        
        # Grilled Chicken should be the top result
        assert len(results) == 2
        assert results[0] == test_multi_field_recipes[3].id  # Grilled Chicken
    
    def test_weighted_search_all_fields(self, mock_lsh_service, test_multi_field_recipes):
        """Test weighted search using all fields"""
        # Create query vectors for pancake-like breakfast
        title_vector = np.array([0.1, 0.3, 0.2, 0.4, 0.1, 0.3, 0.1, 0.2], dtype=np.float32)
        ingredients_vector = np.array([0.2, 0.3, 0.1, 0.5, 0.4, 0.2, 0.1, 0.3, 0.5, 0.2, 0.1, 0.4], dtype=np.float32)
        instructions_vector = np.array([0.1, 0.4, 0.2, 0.3, 0.5, 0.1, 0.2, 0.4, 0.3, 0.1, 0.5, 0.2, 0.3, 0.4, 0.1, 0.2], dtype=np.float32)
        
        # Search with balanced weights
        weights = {"title": 0.3, "ingredients": 0.4, "instructions": 0.3}
        results = mock_lsh_service.weighted_search(
            title_vector=title_vector,
            ingredients_vector=ingredients_vector,
            instructions_vector=instructions_vector,
            weights=weights,
            k=1
        )
        
        # Pancakes should be the top result
        assert len(results) == 1
        assert results[0] == test_multi_field_recipes[0].id  # Pancakes
    
    def test_null_vector_handling(self, mock_lsh_service, test_multi_field_recipes):
        """Test handling of null vectors in weighted search"""
        # Create one query vector for ingredients only
        ingredients_vector = np.array([0.3, 0.6, 0.2, 0.5, 0.1, 0.7, 0.4, 0.3, 0.2, 0.5, 0.6, 0.1], dtype=np.float32)
        
        # Search with only ingredients
        weights = {"title": 0.0, "ingredients": 1.0, "instructions": 0.0}
        results = mock_lsh_service.weighted_search(
            ingredients_vector=ingredients_vector,
            weights=weights,
            k=1
        )
        
        # Should still return a result
        assert len(results) == 1
        assert results[0] == test_multi_field_recipes[2].id  # Chocolate Cake 