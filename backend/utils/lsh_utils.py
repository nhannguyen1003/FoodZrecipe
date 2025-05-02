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

# Constants - these must match the backend configuration
EMBEDDING_DIM_TITLE = 64
EMBEDDING_DIM_INGREDIENTS = 128
EMBEDDING_DIM_INSTRUCTIONS = 256
EMBEDDING_DIM_TEXT = 128

# LSH parameters
HASH_BITS = 8  # Number of bits for each hash code

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
        self.text_index = None
        
        # Initialize the indices
        self.initialize_indices()
    
    def initialize_indices(self):
        """Initialize LSH indices for each field using FAISS"""
        try:
            # Create LSH indices with specified dimensions and bits
            self.title_index = faiss.IndexLSH(EMBEDDING_DIM_TITLE, HASH_BITS)
            self.ingredients_index = faiss.IndexLSH(EMBEDDING_DIM_INGREDIENTS, HASH_BITS)
            self.instructions_index = faiss.IndexLSH(EMBEDDING_DIM_INSTRUCTIONS, HASH_BITS)
            self.text_index = faiss.IndexLSH(EMBEDDING_DIM_TEXT, HASH_BITS)
            
            logger.info("Initialized FAISS LSH indices for all fields")
            return True
        except Exception as e:
            logger.error(f"Error initializing FAISS LSH indices: {e}")
            return False
    
    def generate_hash_buckets(self, feature_vector: List[float], index: faiss.IndexLSH) -> List[int]:
        """
        Generate LSH hash buckets for a given feature vector
        
        Args:
            feature_vector: Feature vector to hash
            index: FAISS LSH index to use for hashing
            
        Returns:
            List of integer hash codes
        """
        if not feature_vector:
            return []
            
        # Convert to numpy array and reshape for FAISS
        feature_vector_np = np.array(feature_vector).astype('float32').reshape(1, -1)
        
        # Generate hash codes
        hash_codes = np.zeros((1, HASH_BITS), dtype=np.int32)
        index.sa_encode(feature_vector_np, hash_codes)
        
        # Convert hash codes to integers
        hash_buckets = hash_codes.flatten().tolist()
        
        return hash_buckets
    
    def process_text_field(self, text: str, index: faiss.IndexLSH, dim: int) -> Tuple[List[float], List[int]]:
        """
        Process a text field to create feature vector and hash buckets
        
        Args:
            text: Text to process
            index: FAISS LSH index to use for hashing
            dim: Dimension of feature vector
            
        Returns:
            Tuple of (feature_vector, hash_buckets)
        """
        # In a real implementation, this would use a text embedding model
        # For now, we'll generate random vectors (this is just a placeholder)
        feature_vector = np.random.random(dim).tolist()
        hash_buckets = self.generate_hash_buckets(feature_vector, index)
        
        return feature_vector, hash_buckets
    
    def process_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a recipe to add multi-field LSH embeddings
        
        Args:
            recipe: Recipe dictionary
            
        Returns:
            Recipe with added LSH embeddings
        """
        # Extract components
        title = recipe.get('Title', '')
        ingredients = ' '.join(recipe.get('Ingredients', []))
        instructions = recipe.get('Instructions', '')
        
        # Generate full text embedding
        full_text = f"{title} {ingredients} {instructions}"
        text_feature_vector, text_hash_buckets = self.process_text_field(
            full_text, self.text_index, EMBEDDING_DIM_TEXT)
        
        # Generate field-specific embeddings
        title_feature_vector, title_hash_buckets = self.process_text_field(
            title, self.title_index, EMBEDDING_DIM_TITLE)
        
        ingredients_feature_vector, ingredients_hash_buckets = self.process_text_field(
            ingredients, self.ingredients_index, EMBEDDING_DIM_INGREDIENTS)
        
        instructions_feature_vector, instructions_hash_buckets = self.process_text_field(
            instructions, self.instructions_index, EMBEDDING_DIM_INSTRUCTIONS)
        
        # Add embeddings to recipe
        recipe['text_feature_vector'] = text_feature_vector
        recipe['text_hash_buckets'] = text_hash_buckets
        recipe['title_feature_vector'] = title_feature_vector
        recipe['title_hash_buckets'] = title_hash_buckets
        recipe['ingredients_feature_vector'] = ingredients_feature_vector
        recipe['ingredients_hash_buckets'] = ingredients_hash_buckets
        recipe['instructions_feature_vector'] = instructions_feature_vector
        recipe['instructions_hash_buckets'] = instructions_hash_buckets
        
        return recipe

# Create a singleton instance
lsh_processor = LSHProcessor() 