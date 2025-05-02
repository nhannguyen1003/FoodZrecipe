#!/usr/bin/env python3
"""
Shared LSH utility functions using FAISS.
This module provides common functionality for locality-sensitive hashing
across different parts of the application.
"""
import numpy as np
import faiss
import logging
import json
import os
from pathlib import Path
from PIL import Image
from typing import List, Dict, Any, Optional, Tuple

# Import our new text processors
from backend.utils.text_processors import (
    title_processor, 
    ingredients_processor, 
    instructions_processor, 
    process_recipe_text_fields
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for embeddings dimensions - must match backend configs
EMBEDDING_DIM_TITLE = 128
EMBEDDING_DIM_INGREDIENTS = 256
EMBEDDING_DIM_INSTRUCTIONS = 384
EMBEDDING_DIM_TEXT = 512
EMBEDDING_DIM_IMAGE = 512

# Constants for hash bits - must match backend configs
HASH_BITS = 64

class LSHProcessor:
    """Process recipes and other data using FAISS LSH for similarity search"""
    
    def __init__(self):
        """Initialize LSH indices for each field"""
        logger.info("Initializing FAISS LSH indices")
        
        # Initialize LSH indices for each field - use the same number of hash bits
        # but different dimension sizes based on the complexity of the field
        self.title_index = faiss.IndexLSH(EMBEDDING_DIM_TITLE, HASH_BITS)
        self.ingredients_index = faiss.IndexLSH(EMBEDDING_DIM_INGREDIENTS, HASH_BITS)
        self.instructions_index = faiss.IndexLSH(EMBEDDING_DIM_INSTRUCTIONS, HASH_BITS)
        self.text_index = faiss.IndexLSH(EMBEDDING_DIM_TEXT, HASH_BITS)
        self.image_index = faiss.IndexLSH(EMBEDDING_DIM_IMAGE, HASH_BITS)
        
        logger.info("FAISS LSH indices initialized")
    
    def generate_hash_buckets(self, feature_vector: np.ndarray, field_type: str) -> List[int]:
        """
        Generate hash buckets from a feature vector using appropriate LSH index
        Returns a list of integers representing LSH hash buckets
        """
        try:
            # Ensure the feature vector is properly shaped
            if feature_vector.size == 0:
                logger.warning(f"Empty feature vector for {field_type}")
                return []
            
            # Reshape to a 2D array with a single row as required by FAISS
            feature_vector = feature_vector.reshape(1, -1).astype(np.float32)
            
            # Use the appropriate index based on field type
            if field_type == 'title':
                # Make sure it's the right size
                if feature_vector.shape[1] != EMBEDDING_DIM_TITLE:
                    logger.warning(f"Title feature vector has wrong dimension: {feature_vector.shape[1]}, expected {EMBEDDING_DIM_TITLE}")
                    # Resize if needed
                    feature_vector = np.resize(feature_vector, (1, EMBEDDING_DIM_TITLE))
                index = self.title_index
            elif field_type == 'ingredients':
                # Make sure it's the right size
                if feature_vector.shape[1] != EMBEDDING_DIM_INGREDIENTS:
                    logger.warning(f"Ingredients feature vector has wrong dimension: {feature_vector.shape[1]}, expected {EMBEDDING_DIM_INGREDIENTS}")
                    feature_vector = np.resize(feature_vector, (1, EMBEDDING_DIM_INGREDIENTS))
                index = self.ingredients_index
            elif field_type == 'instructions':
                # Make sure it's the right size
                if feature_vector.shape[1] != EMBEDDING_DIM_INSTRUCTIONS:
                    logger.warning(f"Instructions feature vector has wrong dimension: {feature_vector.shape[1]}, expected {EMBEDDING_DIM_INSTRUCTIONS}")
                    feature_vector = np.resize(feature_vector, (1, EMBEDDING_DIM_INSTRUCTIONS))
                index = self.instructions_index
            elif field_type == 'image':
                # Make sure it's the right size for image
                if feature_vector.shape[1] != EMBEDDING_DIM_IMAGE:
                    logger.warning(f"Image feature vector has wrong dimension: {feature_vector.shape[1]}, expected {EMBEDDING_DIM_IMAGE}")
                    feature_vector = np.resize(feature_vector, (1, EMBEDDING_DIM_IMAGE))
                index = self.image_index
            else:  # default to text
                # Make sure it's the right size
                if feature_vector.shape[1] != EMBEDDING_DIM_TEXT:
                    logger.warning(f"Text feature vector has wrong dimension: {feature_vector.shape[1]}, expected {EMBEDDING_DIM_TEXT}")
                    feature_vector = np.resize(feature_vector, (1, EMBEDDING_DIM_TEXT))
                index = self.text_index
            
            # Get the binary codes
            codes = index.sa_encode(feature_vector)
            
            # Convert binary codes to bucket IDs (list of ints)
            buckets = codes.tolist()[0]
            
            logger.debug(f"Generated {len(buckets)} hash buckets for {field_type}")
            return buckets
            
        except Exception as e:
            logger.error(f"Error generating hash buckets for {field_type}: {str(e)}")
            return []
    
    def process_text_field(self, text: str, field_type: str) -> Tuple[List[float], List[int]]:
        """
        Process a text field to create feature vector and hash buckets
        Returns tuple of (feature_vector, hash_buckets)
        """
        try:
            # Basic validation
            if not text:
                logger.warning(f"Empty {field_type} text")
                return [], []
                
            if not isinstance(text, str) and not isinstance(text, list):
                logger.warning(f"Invalid {field_type} text type: {type(text)}")
                return [], []
            
            # Process text according to field type using our specialized processors
            if field_type == 'title':
                # Process title text
                processed_text = title_processor.process(text)
                dim = EMBEDDING_DIM_TITLE
            elif field_type == 'ingredients':
                # Process ingredients - handle both string and list formats
                if isinstance(text, str):
                    # Convert comma-separated string to list
                    ingredients_list = [ingredient.strip() for ingredient in text.split(',')]
                else:
                    ingredients_list = text
                    
                processed_text = ' '.join(ingredients_processor.process(ingredients_list))
                dim = EMBEDDING_DIM_INGREDIENTS
            elif field_type == 'instructions':
                # Process instructions with minimal processing for MVP
                processed_text = instructions_processor.process(text)
                dim = EMBEDDING_DIM_INSTRUCTIONS
            else:  # default to combined text
                # For combined text, do basic normalization
                if isinstance(text, list):
                    text = ' '.join(text)
                processed_text = text.lower().strip()
                dim = EMBEDDING_DIM_TEXT
            
            # Create a feature vector from the processed text
            # For MVP, use a simple character frequency approach
            # This would be replaced with proper embeddings in production
            char_freq = {}
            for char in processed_text:
                char_freq[char] = char_freq.get(char, 0) + 1
            
            # Create a normalized frequency vector
            feature_vector = np.zeros(dim, dtype=np.float32)
            total_chars = len(processed_text) or 1  # Avoid division by zero
            
            for i, char in enumerate(sorted(char_freq.keys())):
                idx = hash(char) % dim  # Map character to vector index
                feature_vector[idx] = char_freq[char] / total_chars  # Normalize
            
            # Generate hash buckets
            hash_buckets = self.generate_hash_buckets(feature_vector, field_type)
            
            # Return as Python list for JSON serialization
            return feature_vector.tolist(), hash_buckets
            
        except Exception as e:
            logger.error(f"Error processing {field_type} text: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return [], []

    def process_image(self, image_name: str, images_dir: str) -> Tuple[List[float], List[int]]:
        """
        Process an image to create feature vector and hash buckets
        Returns tuple of (feature_vector, hash_buckets)
        """
        try:
            # Check if images directory is provided
            if not images_dir:
                logger.warning("No images directory provided")
                return [], []
                
            # Construct the full image path
            image_path = os.path.join(images_dir, image_name)
            logger.debug(f"Processing image: {image_path}")
            
            # Check if image file exists
            if not os.path.exists(image_path):
                logger.warning(f"Image file not found: {image_path}")
                return [], []
                
            try:
                # Load and process the image
                image = Image.open(image_path)
                logger.debug(f"Loaded image with size: {image.size}, mode: {image.mode}")
                
                # Convert to RGB if needed
                if image.mode != 'RGB':
                    logger.debug(f"Converting image from {image.mode} to RGB")
                    image = image.convert('RGB')
                
                # Resize to standard dimensions
                image = image.resize((224, 224))
                
                # Convert to numpy array and normalize
                img_array = np.array(image).astype(np.float32)
                img_array /= 255.0  # Normalize to [0,1]
                
                # Flatten to 1D array for feature vector
                feature_vector = img_array.flatten()
                
                # Check vector size
                if feature_vector.size > EMBEDDING_DIM_IMAGE:
                    logger.debug(f"Truncating image feature vector from {feature_vector.size} to {EMBEDDING_DIM_IMAGE}")
                    feature_vector = feature_vector[:EMBEDDING_DIM_IMAGE]
                elif feature_vector.size < EMBEDDING_DIM_IMAGE:
                    logger.debug(f"Padding image feature vector from {feature_vector.size} to {EMBEDDING_DIM_IMAGE}")
                    padding = np.zeros(EMBEDDING_DIM_IMAGE - feature_vector.size, dtype=np.float32)
                    feature_vector = np.concatenate([feature_vector, padding])
                
                # Generate hash buckets
                hash_buckets = self.generate_hash_buckets(feature_vector, 'image')
                
                logger.debug(f"Successfully processed image: {image_name}")
                # Return as Python list for JSON serialization
                return feature_vector.tolist(), hash_buckets
                
            except Exception as e:
                logger.error(f"Error processing image {image_name}: {str(e)}")
                return [], []
                
        except Exception as e:
            logger.error(f"Error in process_image for {image_name}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return [], []

    def process_recipe(self, recipe: Dict[str, Any], images_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a recipe to add multi-field LSH embeddings
        Extracts components and generates embeddings for title, ingredients, instructions, and image
        """
        try:
            # Create a copy of the recipe to avoid modifying the original
            recipe_copy = recipe.copy()
            
            # Extract fields using appropriate keys (handle different naming conventions)
            title = recipe_copy.get('Title', recipe_copy.get('title', ''))
            
            ingredients = recipe_copy.get('Ingredients', recipe_copy.get('ingredients', ''))
            if isinstance(ingredients, str):
                ingredients = [ingredient.strip() for ingredient in ingredients.split(',')]
                
            instructions = recipe_copy.get('Instructions', recipe_copy.get('instructions', ''))
            
            # Process fields with our specialized processors
            processed_fields = process_recipe_text_fields({
                'title': title,
                'ingredients': ingredients,
                'instructions': instructions
            })
            
            # Add processed fields to recipe for reference
            recipe_copy['processed_title'] = processed_fields['processed_title']
            recipe_copy['processed_ingredients'] = processed_fields['processed_ingredients']
            recipe_copy['processed_instructions'] = processed_fields['processed_instructions']
            
            # Process title for LSH
            title_vector, title_hash = self.process_text_field(processed_fields['processed_title'], 'title')
            recipe_copy['lsh_title_vector'] = title_vector
            recipe_copy['lsh_title_hash'] = title_hash
            
            # Process ingredients for LSH
            ingredients_vector, ingredients_hash = self.process_text_field(processed_fields['processed_ingredients'], 'ingredients')
            recipe_copy['lsh_ingredients_vector'] = ingredients_vector
            recipe_copy['lsh_ingredients_hash'] = ingredients_hash
            
            # Process instructions for LSH (minimal for MVP)
            instructions_vector, instructions_hash = self.process_text_field(processed_fields['processed_instructions'], 'instructions')
            recipe_copy['lsh_instructions_vector'] = instructions_vector
            recipe_copy['lsh_instructions_hash'] = instructions_hash
            
            # Create a combined text string for backward compatibility
            combined_text = f"{title} {' '.join(ingredients) if isinstance(ingredients, list) else ingredients} {instructions}"
            combined_vector, combined_hash = self.process_text_field(combined_text, 'text')
            recipe_copy['lsh_text_vector'] = combined_vector
            recipe_copy['lsh_text_hash'] = combined_hash
            
            # Process image if available
            image_name = recipe_copy.get('Image_Name', recipe_copy.get('image_name', ''))
            if image_name and images_dir:
                image_vector, image_hash = self.process_image(image_name, images_dir)
                recipe_copy['lsh_image_vector'] = image_vector
                recipe_copy['lsh_image_hash'] = image_hash
            
            logger.debug(f"Successfully processed recipe: {title}")
            return recipe_copy
            
        except Exception as e:
            logger.error(f"Error in process_recipe: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return recipe.copy()  # Return original recipe on error

# Create a singleton instance for consistent access
lsh_processor = LSHProcessor() 