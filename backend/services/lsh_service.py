# TODO: Implement Locality-Sensitive Hashing (LSH) service
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple, Optional
from config import settings
from backend.models.recipe import Recipe
from backend.utils.text_processors import (
    title_processor,
    ingredients_processor, 
    instructions_processor
)

class LSHService:
    def __init__(self):
        self.text_index = None
        self.image_index = None
        self.title_index = None
        self.ingredients_index = None
        self.instructions_index = None
        self.recipe_ids = []
        self.is_initialized = False
        
        # Initialize dimensions from settings
        # Use FAISS parameters if available, otherwise fall back to original parameters
        self.vector_dim = getattr(settings, 'LSH_VECTOR_DIM', 128)
        self.hash_bits = getattr(settings, 'LSH_HASH_BITS', 32)
        
        # Field-specific dimensions
        self.title_dim = getattr(settings, 'LSH_TITLE_DIM', 128)
        self.ingredients_dim = getattr(settings, 'LSH_INGREDIENTS_DIM', 256)
        self.instructions_dim = getattr(settings, 'LSH_INSTRUCTIONS_DIM', 384)
        
        # Map legacy parameters for tests that might call this directly
        self.hash_size = getattr(settings, 'LSH_HASH_SIZE', 8)
        self.num_tables = getattr(settings, 'LSH_NUM_TABLES', 10)
    
    def initialize(self, vector_dim: Optional[int] = None, hash_bits: Optional[int] = None) -> None:
        """Initialize FAISS LSH indices"""
        if vector_dim is not None:
            self.vector_dim = vector_dim
        if hash_bits is not None:
            self.hash_bits = hash_bits
        
        # Initialize LSH indices
        self.text_index = faiss.IndexLSH(self.vector_dim, self.hash_bits)
        self.image_index = faiss.IndexLSH(self.vector_dim, self.hash_bits)
        
        # Initialize field-specific indices
        self.title_index = faiss.IndexLSH(self.title_dim, self.hash_bits)
        self.ingredients_index = faiss.IndexLSH(self.ingredients_dim, self.hash_bits)
        self.instructions_index = faiss.IndexLSH(self.instructions_dim, self.hash_bits)
        
        self.is_initialized = True
    
    def extract_text_features(self, recipe: Recipe) -> np.ndarray:
        """Extract text features from recipe"""
        if recipe.text_feature_vector:
            return np.array(recipe.text_feature_vector, dtype=np.float32)
        return np.zeros(self.vector_dim, dtype=np.float32)
    
    def extract_title_features(self, recipe: Recipe) -> np.ndarray:
        """Extract title features from recipe"""
        if recipe.title_feature_vector:
            return np.array(recipe.title_feature_vector, dtype=np.float32)
        return np.zeros(self.title_dim, dtype=np.float32)
    
    def extract_ingredients_features(self, recipe: Recipe) -> np.ndarray:
        """Extract ingredients features from recipe"""
        if recipe.ingredients_feature_vector:
            return np.array(recipe.ingredients_feature_vector, dtype=np.float32)
        return np.zeros(self.ingredients_dim, dtype=np.float32)
    
    def extract_instructions_features(self, recipe: Recipe) -> np.ndarray:
        """Extract instructions features from recipe"""
        if recipe.instructions_feature_vector:
            return np.array(recipe.instructions_feature_vector, dtype=np.float32)
        return np.zeros(self.instructions_dim, dtype=np.float32)
    
    def extract_image_features(self, recipe: Recipe) -> np.ndarray:
        """Extract image features from recipe"""
        if recipe.image_feature_vector:
            return np.array(recipe.image_feature_vector, dtype=np.float32)
        return np.zeros(self.vector_dim, dtype=np.float32)
    
    def build_indices(self, recipes: List[Recipe]) -> None:
        """Build FAISS LSH indices from recipes"""
        if not self.is_initialized:
            self.initialize()
        
        # Store recipe IDs
        self.recipe_ids = [recipe.id for recipe in recipes]
        
        # Extract features
        text_vectors = []
        image_vectors = []
        title_vectors = []
        ingredients_vectors = []
        instructions_vectors = []
        
        for recipe in recipes:
            if recipe.text_feature_vector:
                text_vectors.append(self.extract_text_features(recipe))
            if recipe.image_feature_vector:
                image_vectors.append(self.extract_image_features(recipe))
            if recipe.title_feature_vector:
                title_vectors.append(self.extract_title_features(recipe))
            if recipe.ingredients_feature_vector:
                ingredients_vectors.append(self.extract_ingredients_features(recipe))
            if recipe.instructions_feature_vector:
                instructions_vectors.append(self.extract_instructions_features(recipe))
        
        # Build text index
        if text_vectors:
            text_vectors = np.array(text_vectors).astype(np.float32)
            self.text_index.add(text_vectors)
        
        # Build image index
        if image_vectors:
            image_vectors = np.array(image_vectors).astype(np.float32)
            self.image_index.add(image_vectors)
        
        # Build field-specific indices
        if title_vectors:
            title_vectors = np.array(title_vectors).astype(np.float32)
            self.title_index.add(title_vectors)
        
        if ingredients_vectors:
            ingredients_vectors = np.array(ingredients_vectors).astype(np.float32)
            self.ingredients_index.add(ingredients_vectors)
        
        if instructions_vectors:
            instructions_vectors = np.array(instructions_vectors).astype(np.float32)
            self.instructions_index.add(instructions_vectors)
    
    def search_by_text(self, query_vector: np.ndarray, k: int = 10) -> Tuple[List[int], List[float]]:
        """Search for similar recipes using FAISS LSH by text features"""
        if not self.is_initialized or self.text_index.ntotal == 0:
            return [], []
        
        # Reshape query vector for FAISS
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        
        # Search the index
        distances, indices = self.text_index.search(query_vector, k)
        
        # Convert indices to recipe IDs
        recipe_indices = [int(idx) for idx in indices[0] if idx >= 0 and idx < len(self.recipe_ids)]
        recipe_ids = [self.recipe_ids[idx] for idx in recipe_indices]
        recipe_distances = [float(distances[0][i]) for i, idx in enumerate(indices[0]) 
                           if idx >= 0 and idx < len(self.recipe_ids)]
        
        return recipe_ids, recipe_distances
    
    def search_by_title(self, query: str, k: int = 10) -> Tuple[List[int], List[float]]:
        """Search for similar recipes by title"""
        if not self.is_initialized or self.title_index.ntotal == 0:
            return [], []
        
        # Process the query using title processor
        processed_query = title_processor.process(query)
        
        # Create a simple feature vector (same approach as in lsh_utils.py)
        feature_vector = np.zeros(self.title_dim, dtype=np.float32)
        
        # Create character frequency vector
        char_freq = {}
        for char in processed_query:
            char_freq[char] = char_freq.get(char, 0) + 1
        
        # Create feature vector
        total_chars = len(processed_query) or 1  # Avoid division by zero
        for i, char in enumerate(sorted(char_freq.keys())):
            idx = hash(char) % self.title_dim
            feature_vector[idx] = char_freq[char] / total_chars
        
        # Reshape for FAISS
        query_vector = feature_vector.reshape(1, -1).astype(np.float32)
        
        # Search the index
        distances, indices = self.title_index.search(query_vector, k)
        
        # Convert indices to recipe IDs
        recipe_indices = [int(idx) for idx in indices[0] if idx >= 0 and idx < len(self.recipe_ids)]
        recipe_ids = [self.recipe_ids[idx] for idx in recipe_indices]
        recipe_distances = [float(distances[0][i]) for i, idx in enumerate(indices[0]) 
                           if idx >= 0 and idx < len(self.recipe_ids)]
        
        return recipe_ids, recipe_distances
    
    def search_by_ingredients(self, ingredients_query: List[str], k: int = 10) -> Tuple[List[int], List[float]]:
        """Search for similar recipes by ingredients"""
        if not self.is_initialized or self.ingredients_index.ntotal == 0:
            return [], []
        
        # Process the ingredients query
        processed_ingredients = ingredients_processor.process(ingredients_query)
        processed_query = " ".join(processed_ingredients)
        
        # Create a simple feature vector
        feature_vector = np.zeros(self.ingredients_dim, dtype=np.float32)
        
        # Create character frequency vector
        char_freq = {}
        for char in processed_query:
            char_freq[char] = char_freq.get(char, 0) + 1
        
        # Create feature vector
        total_chars = len(processed_query) or 1  # Avoid division by zero
        for i, char in enumerate(sorted(char_freq.keys())):
            idx = hash(char) % self.ingredients_dim
            feature_vector[idx] = char_freq[char] / total_chars
        
        # Reshape for FAISS
        query_vector = feature_vector.reshape(1, -1).astype(np.float32)
        
        # Search the index
        distances, indices = self.ingredients_index.search(query_vector, k)
        
        # Convert indices to recipe IDs
        recipe_indices = [int(idx) for idx in indices[0] if idx >= 0 and idx < len(self.recipe_ids)]
        recipe_ids = [self.recipe_ids[idx] for idx in recipe_indices]
        recipe_distances = [float(distances[0][i]) for i, idx in enumerate(indices[0]) 
                           if idx >= 0 and idx < len(self.recipe_ids)]
        
        return recipe_ids, recipe_distances
    
    def search_by_image(self, query_vector: np.ndarray, k: int = 10) -> Tuple[List[int], List[float]]:
        """Search for similar recipes using FAISS LSH by image features"""
        if not self.is_initialized or self.image_index.ntotal == 0:
            return [], []
        
        # Reshape query vector for FAISS
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        
        # Search the index
        distances, indices = self.image_index.search(query_vector, k)
        
        # Convert indices to recipe IDs
        recipe_indices = [int(idx) for idx in indices[0] if idx >= 0 and idx < len(self.recipe_ids)]
        recipe_ids = [self.recipe_ids[idx] for idx in recipe_indices]
        recipe_distances = [float(distances[0][i]) for i, idx in enumerate(indices[0]) 
                           if idx >= 0 and idx < len(self.recipe_ids)]
        
        return recipe_ids, recipe_distances
    
    def multi_field_search(self, title_query: str = "", ingredients_query: List[str] = None, 
                          instruction_query: str = "", weights: Dict[str, float] = None, 
                          k: int = 10) -> List[int]:
        """
        Search using multiple fields with configurable weights
        Returns a list of recipe IDs sorted by relevance
        """
        if not self.is_initialized:
            return []
        
        # Use default weights if not provided
        if weights is None:
            weights = {
                "title": 0.5,  # Title matches are important
                "ingredients": 0.4,  # Ingredient matches are also important
                "instructions": 0.1  # Instruction matches less important for MVP
            }
        
        results = {}
        
        # Search by title if provided
        if title_query:
            title_ids, title_distances = self.search_by_title(title_query, k=k*2)  # Get more results to merge
            for i, recipe_id in enumerate(title_ids):
                # Lower distance is better, so we convert to a score by inverting
                # Add 1 to avoid division by zero
                score = 1.0 / (1.0 + title_distances[i])
                results[recipe_id] = results.get(recipe_id, 0) + (score * weights["title"])
        
        # Search by ingredients if provided
        if ingredients_query:
            ingredient_ids, ingredient_distances = self.search_by_ingredients(ingredients_query, k=k*2)
            for i, recipe_id in enumerate(ingredient_ids):
                score = 1.0 / (1.0 + ingredient_distances[i])
                results[recipe_id] = results.get(recipe_id, 0) + (score * weights["ingredients"])
        
        # Sort by score (descending)
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        
        # Get top k recipe IDs
        top_recipe_ids = [recipe_id for recipe_id, _ in sorted_results[:k]]
        
        return top_recipe_ids
    
    def update_parameters(self, vector_dim: Optional[int] = None, hash_bits: Optional[int] = None) -> None:
        """Update LSH parameters and rebuild indices"""
        if vector_dim:
            self.vector_dim = vector_dim
        if hash_bits:
            self.hash_bits = hash_bits
        
        # Update legacy parameters for backward compatibility
        self.hash_size = self.hash_bits // 4  # Approximate conversion
        self.num_tables = 10  # Default value
        
        # Re-initialize indices
        self.initialize()
    
    def evaluate(self, query_vectors: np.ndarray, ground_truth: List[List[int]], k: int = 10) -> Dict[str, float]:
        """
        Evaluate LSH performance
        
        Args:
            query_vectors: Query vectors for evaluation
            ground_truth: List of lists containing ground truth recipe IDs for each query
            k: Number of results to return
            
        Returns:
            Dictionary with evaluation metrics (precision, recall, etc.)
        """
        if not self.is_initialized:
            return {"error": "Index not initialized"}
        
        precision_sum = 0.0
        recall_sum = 0.0
        count = 0
        
        for i, query in enumerate(query_vectors):
            # Get ground truth for this query
            gt = set(ground_truth[i])
            if not gt:
                continue
                
            # Search using the query
            results, _ = self.search_by_text(query, k)
            results_set = set(results)
            
            # Calculate precision and recall
            correct = len(results_set.intersection(gt))
            precision = correct / len(results_set) if results_set else 0
            recall = correct / len(gt) if gt else 0
            
            precision_sum += precision
            recall_sum += recall
            count += 1
        
        # Average metrics
        avg_precision = precision_sum / count if count > 0 else 0
        avg_recall = recall_sum / count if count > 0 else 0
        f1_score = 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0
        
        return {
            "precision": avg_precision,
            "recall": avg_recall,
            "f1_score": f1_score,
            "num_queries": count
        }

lsh_service = LSHService()