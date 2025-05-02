import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy.orm import Session

from backend.models.recipe import Recipe
from backend.utils.text_processors import (
    title_processor,
    ingredients_processor,
    instructions_processor,
    process_recipe_text_fields
)
from backend.schemas.recipe import RecipeCreate, RecipeUpdate
from database.repositories.recipe_repository import recipe_repository


class MultiFieldSearchService:
    """Service for multi-field recipe search using LSH and embeddings"""
    
    def __init__(self):
        # Initialize embedding dimensions
        self.title_dim = 64
        self.ingredients_dim = 128
        self.instructions_dim = 256
        
        # Initialize hash dimensions
        self.title_bits = 32
        self.ingredients_bits = 64
        self.instructions_bits = 128
        
        # Initialize indices (these would be FAISS indices in real implementation)
        self.title_index = None
        self.ingredients_index = None
        self.instructions_index = None
        
        # Store recipe IDs for mapping indices to recipes
        self.recipe_ids = []
        
        # Track initialization state
        self.is_initialized = False
    
    def initialize_indices(self):
        """Initialize multi-field LSH indices"""
        # In real implementation, these would be FAISS LSH indices
        self.title_index = {"vectors": [], "dim": self.title_dim, "bits": self.title_bits}
        self.ingredients_index = {"vectors": [], "dim": self.ingredients_dim, "bits": self.ingredients_bits}
        self.instructions_index = {"vectors": [], "dim": self.instructions_dim, "bits": self.instructions_bits}
        self.is_initialized = True
    
    def build_indices(self, db: Session):
        """Build multi-field LSH indices from all recipes in the database"""
        if not self.is_initialized:
            self.initialize_indices()
        
        # Get all recipes from the database
        recipes = recipe_repository.get_all(db)
        
        # Clear existing indices
        self.title_index["vectors"] = []
        self.ingredients_index["vectors"] = []
        self.instructions_index["vectors"] = []
        
        # Store recipe IDs
        self.recipe_ids = [recipe.id for recipe in recipes]
        
        # Add vectors to indices
        for recipe in recipes:
            # Add title vector if available
            if recipe.title_feature_vector:
                vector = np.array(recipe.title_feature_vector, dtype=np.float32)
                self.title_index["vectors"].append((recipe.id, vector))
            
            # Add ingredients vector if available
            if recipe.ingredients_feature_vector:
                vector = np.array(recipe.ingredients_feature_vector, dtype=np.float32)
                self.ingredients_index["vectors"].append((recipe.id, vector))
            
            # Add instructions vector if available
            if recipe.instructions_feature_vector:
                vector = np.array(recipe.instructions_feature_vector, dtype=np.float32)
                self.instructions_index["vectors"].append((recipe.id, vector))
    
    def generate_embeddings_for_recipe(self, recipe: Recipe) -> Recipe:
        """Generate field-specific embeddings for a recipe"""
        # Process recipe fields
        processed = process_recipe_text_fields({
            "title": recipe.title,
            "ingredients": recipe.ingredients,
            "instructions": recipe.instructions
        })
        
        # Generate title embedding
        recipe.title_feature_vector = self._create_feature_vector(
            processed["processed_title"], 
            self.title_dim
        )
        
        # Generate ingredients embedding
        recipe.ingredients_feature_vector = self._create_feature_vector(
            " ".join(processed["processed_ingredients"]), 
            self.ingredients_dim
        )
        
        # Generate instructions embedding
        recipe.instructions_feature_vector = self._create_feature_vector(
            processed["processed_instructions"], 
            self.instructions_dim
        )
        
        # Generate hash buckets
        recipe.title_hash_buckets = self._compute_hash_buckets(
            recipe.title_feature_vector, 
            self.title_bits
        )
        
        recipe.ingredients_hash_buckets = self._compute_hash_buckets(
            recipe.ingredients_feature_vector, 
            self.ingredients_bits
        )
        
        recipe.instructions_hash_buckets = self._compute_hash_buckets(
            recipe.instructions_feature_vector, 
            self.instructions_bits
        )
        
        return recipe
    
    def update_recipe_embeddings(self, db: Session, recipe_id: int) -> Optional[Recipe]:
        """Update embeddings for an existing recipe"""
        # Get the recipe
        recipe = recipe_repository.get(db, id=recipe_id)
        if not recipe:
            return None
        
        # Generate embeddings
        recipe = self.generate_embeddings_for_recipe(recipe)
        
        # Update the recipe in the database
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        
        return recipe
    
    def generate_embeddings_for_all_recipes(self, db: Session):
        """Generate embeddings for all recipes in the database"""
        # Get all recipes
        recipes = recipe_repository.get_all(db)
        
        # Generate embeddings for each recipe
        for recipe in recipes:
            recipe = self.generate_embeddings_for_recipe(recipe)
            db.add(recipe)
        
        # Commit all changes
        db.commit()
        
        # Rebuild indices
        self.build_indices(db)
    
    def search_by_title(self, query: str, k: int = 10) -> Tuple[List[int], List[float]]:
        """Search for similar recipes by title"""
        if not self.is_initialized:
            return [], []
        
        # Process the query text
        processed_query = title_processor.process(query)
        
        # Generate query vector
        query_vector = np.array(self._create_feature_vector(processed_query, self.title_dim), dtype=np.float32)
        
        # Search using title index
        results = []
        for recipe_id, vector in self.title_index["vectors"]:
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_vector, vector)
            results.append((recipe_id, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k recipe IDs and scores
        recipe_ids = [r[0] for r in results[:k]]
        scores = [r[1] for r in results[:k]]
        
        return recipe_ids, scores
    
    def search_by_ingredients(self, ingredients: List[str], k: int = 10) -> Tuple[List[int], List[float]]:
        """Search for similar recipes by ingredients"""
        if not self.is_initialized:
            return [], []
        
        # Process the ingredients
        processed_ingredients = ingredients_processor.process(ingredients)
        ingredients_text = " ".join(processed_ingredients)
        
        # Generate query vector
        query_vector = np.array(self._create_feature_vector(ingredients_text, self.ingredients_dim), dtype=np.float32)
        
        # Search using ingredients index
        results = []
        for recipe_id, vector in self.ingredients_index["vectors"]:
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_vector, vector)
            results.append((recipe_id, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k recipe IDs and scores
        recipe_ids = [r[0] for r in results[:k]]
        scores = [r[1] for r in results[:k]]
        
        return recipe_ids, scores
    
    def search_by_instructions(self, instructions: str, k: int = 10) -> Tuple[List[int], List[float]]:
        """Search for similar recipes by instructions"""
        if not self.is_initialized:
            return [], []
        
        # Process the instructions
        processed_instructions = instructions_processor.process(instructions)
        
        # Generate query vector
        query_vector = np.array(self._create_feature_vector(processed_instructions, self.instructions_dim), dtype=np.float32)
        
        # Search using instructions index
        results = []
        for recipe_id, vector in self.instructions_index["vectors"]:
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_vector, vector)
            results.append((recipe_id, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k recipe IDs and scores
        recipe_ids = [r[0] for r in results[:k]]
        scores = [r[1] for r in results[:k]]
        
        return recipe_ids, scores
    
    def multi_field_search(
        self,
        db: Session,
        title_query: Optional[str] = None,
        ingredients_query: Optional[List[str]] = None,
        instructions_query: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None,
        k: int = 10
    ) -> List[Recipe]:
        """
        Search for recipes using multiple fields with custom weights
        
        Args:
            db: Database session
            title_query: Title search query (optional)
            ingredients_query: List of ingredients to search for (optional)
            instructions_query: Instructions search query (optional)
            weights: Dictionary with weights for each field (e.g. {"title": 0.5, "ingredients": 0.3, "instructions": 0.2})
            k: Number of results to return
            
        Returns:
            List of Recipe objects sorted by weighted similarity
        """
        if not self.is_initialized:
            self.initialize_indices()
            self.build_indices(db)
        
        # Default weights if not provided
        if weights is None:
            weights = {
                "title": 0.3,
                "ingredients": 0.4,
                "instructions": 0.3
            }
        
        # Initialize recipe scores dictionary
        recipe_scores = {}
        
        # Search by title if provided
        if title_query and weights.get("title", 0) > 0:
            title_weight = weights.get("title", 0.3)
            title_ids, title_scores = self.search_by_title(title_query, k=k*2)  # Get more results for later merging
            
            # Add weighted scores to results
            for idx, recipe_id in enumerate(title_ids):
                if recipe_id not in recipe_scores:
                    recipe_scores[recipe_id] = 0
                recipe_scores[recipe_id] += title_scores[idx] * title_weight
        
        # Search by ingredients if provided
        if ingredients_query and weights.get("ingredients", 0) > 0:
            ingredients_weight = weights.get("ingredients", 0.4)
            ingredient_ids, ingredient_scores = self.search_by_ingredients(ingredients_query, k=k*2)
            
            # Add weighted scores to results
            for idx, recipe_id in enumerate(ingredient_ids):
                if recipe_id not in recipe_scores:
                    recipe_scores[recipe_id] = 0
                recipe_scores[recipe_id] += ingredient_scores[idx] * ingredients_weight
        
        # Search by instructions if provided
        if instructions_query and weights.get("instructions", 0) > 0:
            instructions_weight = weights.get("instructions", 0.3)
            instruction_ids, instruction_scores = self.search_by_instructions(instructions_query, k=k*2)
            
            # Add weighted scores to results
            for idx, recipe_id in enumerate(instruction_ids):
                if recipe_id not in recipe_scores:
                    recipe_scores[recipe_id] = 0
                recipe_scores[recipe_id] += instruction_scores[idx] * instructions_weight
        
        # Sort recipes by score (highest first)
        sorted_results = sorted(recipe_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get top k recipe IDs
        top_ids = [r[0] for r in sorted_results[:k]]
        
        # Return Recipe objects for the top IDs
        if top_ids:
            return recipe_repository.get_multi_by_ids(db, ids=top_ids)
        else:
            return []
    
    def _create_feature_vector(self, text: str, dim: int) -> List[float]:
        """
        Create a feature vector for text using a simple embedding approach
        
        In a real implementation, this would use a proper embedding model like Sentence-BERT,
        Word2Vec, or a custom trained embedding model.
        
        This simple implementation uses character frequencies as a placeholder.
        """
        char_freq = {}
        for char in text:
            char_freq[char] = char_freq.get(char, 0) + 1
        
        feature_vector = np.zeros(dim, dtype=np.float32)
        total_chars = len(text) or 1  # Avoid division by zero
        
        for i, char in enumerate(sorted(char_freq.keys())):
            idx = hash(char) % dim
            feature_vector[idx] = char_freq[char] / total_chars
        
        return feature_vector.tolist()
    
    def _compute_hash_buckets(self, feature_vector: List[float], num_bits: int) -> List[int]:
        """
        Compute LSH hash buckets for a feature vector
        
        In a real implementation, this would use a proper LSH algorithm like FAISS.
        This simple implementation uses random projections as a placeholder.
        """
        # Convert to numpy array
        vector = np.array(feature_vector, dtype=np.float32)
        
        # Generate random projection vectors (fixed seed for reproducibility)
        np.random.seed(42)
        projections = np.random.randn(num_bits, len(vector))
        
        # Compute hash buckets
        hash_bits = (np.dot(projections, vector) >= 0).astype(int)
        
        # Convert bit array to integers (buckets)
        # We'll create buckets from groups of 8 bits for efficiency
        hash_buckets = []
        for i in range(0, num_bits, 8):
            if i + 8 <= num_bits:
                # Convert 8 bits to an integer
                bucket = 0
                for j in range(8):
                    if hash_bits[i + j]:
                        bucket |= (1 << j)
                hash_buckets.append(bucket)
        
        return hash_buckets
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm_a = np.linalg.norm(vec1)
        norm_b = np.linalg.norm(vec2)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)


# Create a singleton instance
multi_field_search_service = MultiFieldSearchService() 