#!/usr/bin/env python3
"""
Shared LSH utility functions using FAISS.
This module ensures consistent LSH hashing logic across the application.
"""
import numpy as np
import faiss
import logging
import json
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for embedding dimensions - must match backend configurations
TITLE_DIM = 64
INGREDIENTS_DIM = 128
INSTRUCTIONS_DIM = 256
TEXT_DIM = 128  # Legacy dimension

# Constants for hash bits - must match backend configurations
TITLE_BITS = 32
INGREDIENTS_BITS = 64
INSTRUCTIONS_BITS = 128
TEXT_BITS = 32  # Legacy bits

class LSHProcessor:
    """
    LSH processor for consistent hashing logic using FAISS.
    Uses the same parameters as the backend LSH service.
    """
    
    def __init__(self):
        # Initialize the LSH indices
        self.title_index = None
        self.ingredients_index = None
        self.instructions_index = None
        self.text_index = None  # Legacy index
        
        # Initialize the indices
        self.initialize_indices()
    
    def initialize_indices(self):
        """Initialize LSH indices for each field using FAISS"""
        try:
            # Create LSH indices with specified dimensions and bits
            self.title_index = faiss.IndexLSH(TITLE_DIM, TITLE_BITS)
            self.ingredients_index = faiss.IndexLSH(INGREDIENTS_DIM, INGREDIENTS_BITS)
            self.instructions_index = faiss.IndexLSH(INSTRUCTIONS_DIM, INSTRUCTIONS_BITS)
            self.text_index = faiss.IndexLSH(TEXT_DIM, TEXT_BITS)
            
            logger.info("Initialized FAISS LSH indices for all fields")
            return True
        except Exception as e:
            logger.error(f"Error initializing FAISS LSH indices: {e}")
            return False
    
    def generate_hash_buckets(self, feature_vector: np.ndarray, index: faiss.IndexLSH) -> List[int]:
        """
        Generate LSH hash buckets using FAISS for a feature vector.
        
        Args:
            feature_vector: The feature vector to hash
            index: The FAISS LSH index to use
            
        Returns:
            List of hash bucket integers
        """
        if feature_vector is None or len(feature_vector) == 0:
            return []
        
        try:
            # Reshape for FAISS (expects a 2D array)
            vector = feature_vector.reshape(1, -1).astype(np.float32)
            
            # Use FAISS to compute the binary codes
            n_bits = index.d
            code = np.zeros((1, (n_bits + 7) // 8), dtype=np.uint8)
            index.sa_encode(vector, code)
            
            # Convert binary code to hash buckets
            hash_buckets = []
            for i in range(min(n_bits, 32)):  # Use at most 32 bits for hash buckets
                bucket = 0
                byte_idx = i // 8
                bit_idx = i % 8
                if byte_idx < code.shape[1]:
                    bucket = (code[0, byte_idx] >> bit_idx) & 1
                    bucket = bucket << i  # Shift the bit to its position
                hash_buckets.append(int(bucket))
            
            return hash_buckets
        except Exception as e:
            logger.error(f"Error generating hash buckets: {e}")
            return []
    
    def process_text_field(self, text: str, dimensions: int, index: faiss.IndexLSH) -> Tuple[List[float], List[int]]:
        """
        Process a text field to generate its feature vector and hash buckets.
        
        Args:
            text: The text to process
            dimensions: The vector dimensions
            index: The FAISS LSH index
            
        Returns:
            Tuple of (feature_vector, hash_buckets)
        """
        # Generate a simple deterministic feature vector
        # In production, this would use a proper embedding model
        feature_vector = self._generate_simple_vector(text, dimensions)
        
        # Generate hash buckets using the FAISS index
        hash_buckets = self.generate_hash_buckets(feature_vector, index)
        
        return feature_vector.tolist(), hash_buckets
    
    def _generate_simple_vector(self, text: str, dimensions: int) -> np.ndarray:
        """
        Generate a simple deterministic feature vector from text.
        This is a placeholder for a proper embedding model.
        """
        if not text:
            return np.zeros(dimensions, dtype=np.float32)
        
        # Simple hash-based approach for demo purposes
        # In production, replace with a proper embedding model
        hash_val = hash(text) % 1000000
        np.random.seed(hash_val)
        return np.random.rand(dimensions).astype(np.float32)
    
    def process_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a recipe to add multi-field LSH embeddings.
        
        Args:
            recipe: The recipe data dictionary
            
        Returns:
            Recipe with added embedding fields
        """
        # Extract recipe components
        title = recipe.get('title', '')
        
        # Handle ingredients
        ingredients = recipe.get('ingredients', [])
        if isinstance(ingredients, str):
            try:
                ingredients = json.loads(ingredients)
            except (json.JSONDecodeError, NameError):
                ingredients = [ingredients]
        ingredients_text = " ".join(ingredients) if isinstance(ingredients, list) else str(ingredients)
        
        # Handle instructions
        instructions = recipe.get('instructions', '')
        if isinstance(instructions, list):
            instructions = " ".join(instructions)
        
        # Generate legacy text embedding (combined fields)
        all_text = f"{title} {ingredients_text} {instructions}"
        text_vector, text_hash = self.process_text_field(all_text, TEXT_DIM, self.text_index)
        
        # Generate field-specific embeddings
        title_vector, title_hash = self.process_text_field(title, TITLE_DIM, self.title_index)
        ingredients_vector, ingredients_hash = self.process_text_field(ingredients_text, INGREDIENTS_DIM, self.ingredients_index)
        instructions_vector, instructions_hash = self.process_text_field(instructions, INSTRUCTIONS_DIM, self.instructions_index)
        
        # Add vectors and hashes to recipe
        recipe['text_feature_vector'] = text_vector
        recipe['text_hash_buckets'] = text_hash
        
        recipe['title_feature_vector'] = title_vector
        recipe['ingredients_feature_vector'] = ingredients_vector
        recipe['instructions_feature_vector'] = instructions_vector
        
        recipe['title_hash_buckets'] = title_hash
        recipe['ingredients_hash_buckets'] = ingredients_hash
        recipe['instructions_hash_buckets'] = instructions_hash
        
        return recipe

# Create a singleton instance
lsh_processor = LSHProcessor() 