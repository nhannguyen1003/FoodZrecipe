# TODO: Implement Locality-Sensitive Hashing (LSH) service
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple, Optional
from config import settings
from backend.models.recipe import Recipe

class LSHService:
    def __init__(self):
        self.text_index = None
        self.image_index = None
        self.recipe_ids = []
        self.is_initialized = False
        
        # Initialize dimensions from settings
        # Use FAISS parameters if available, otherwise fall back to original parameters
        self.vector_dim = getattr(settings, 'LSH_VECTOR_DIM', 128)
        self.hash_bits = getattr(settings, 'LSH_HASH_BITS', 32)
        
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
        self.is_initialized = True
    
    def extract_text_features(self, recipe: Recipe) -> np.ndarray:
        """Extract text features from recipe"""
        if recipe.text_feature_vector:
            return np.array(recipe.text_feature_vector, dtype=np.float32)
        return np.zeros(self.vector_dim, dtype=np.float32)
    
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
        
        # Extract text and image features
        text_vectors = []
        image_vectors = []
        
        for recipe in recipes:
            if recipe.text_feature_vector:
                text_vectors.append(self.extract_text_features(recipe))
            if recipe.image_feature_vector:
                image_vectors.append(self.extract_image_features(recipe))
        
        # Build text index
        if text_vectors:
            text_vectors = np.array(text_vectors).astype(np.float32)
            self.text_index.add(text_vectors)
        
        # Build image index
        if image_vectors:
            image_vectors = np.array(image_vectors).astype(np.float32)
            self.image_index.add(image_vectors)
    
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
        self.text_index = faiss.IndexLSH(self.vector_dim, self.hash_bits)
        self.image_index = faiss.IndexLSH(self.vector_dim, self.hash_bits)
    
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