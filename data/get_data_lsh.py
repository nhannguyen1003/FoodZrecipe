#!/usr/bin/env python3
"""
Generate multi-field LSH embeddings for recipes.
Takes sample_recipes_cleaned.json and generates field-specific embeddings for title, ingredients, and instructions.
Also generates image embeddings for recipe images in the static folder.
Outputs the enhanced data to sample_recipes_with_hashed.json in JSONL format (one JSON object per line).
"""
import json
import os
import numpy as np
from pathlib import Path
import re
import logging
import faiss
from typing import List, Dict, Any
import sys
import traceback
import random

# Add the project root to Python path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the shared LSH processor from backend
from backend.utils.lsh_utils import lsh_processor
# Import the text processors for direct access if needed
from backend.utils.text_processors import (
    title_processor,
    ingredients_processor,
    instructions_processor,
    process_recipe_text_fields
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """
    Basic text cleaning (legacy method - using text_processors is preferred)
    """
    if isinstance(text, list):
        text = " ".join(text)
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and extra whitespace
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_recipe(recipe: Dict[str, Any], images_dir: str, available_images: List[str] = None) -> Dict[str, Any]:
    """Process a single recipe to add embeddings for all fields including image using FAISS LSH"""
    try:
        # Check if we're using available images and assign a random one if needed
        if available_images:
            # Assign a random existing image to the recipe
            recipe['image'] = random.choice(available_images)
            logger.info(f"Assigned existing image to recipe: {recipe['image']}")
        else:
            # Check if 'image' field exists and is not empty
            if 'image' in recipe and recipe['image']:
                logger.info(f"Recipe has image: {recipe['image']}")
            elif 'Image_Name' in recipe and recipe['Image_Name']:
                # Handle different field name convention
                recipe['image'] = recipe['Image_Name']
                logger.info(f"Recipe using Image_Name field: {recipe['image']}")
            else:
                logger.warning(f"Recipe has no image field: {recipe.get('Title', 'unknown')}")
            
        # Pre-process the recipe text fields for better embeddings
        # This is now handled within lsh_processor.process_recipe but we can do it here too
        # for direct access to processed fields
        processed_fields = process_recipe_text_fields({
            'title': recipe.get('Title', recipe.get('title', '')),
            'ingredients': recipe.get('Ingredients', recipe.get('ingredients', [])),
            'instructions': recipe.get('Instructions', recipe.get('instructions', ''))
        })
        
        # Store processed text for debugging or reference (optional)
        recipe['processed_title'] = processed_fields['processed_title']
        recipe['processed_ingredients'] = processed_fields['processed_ingredients']
        recipe['processed_instructions'] = processed_fields['processed_instructions']
        
        # Use the shared LSH processor to generate consistent embeddings and hash buckets
        # This now uses our specialized text processors internally
        processed_recipe = lsh_processor.process_recipe(recipe, images_dir)
        
        # Map lsh_* field names to the correct format for database compatibility
        field_mapping = {
            'lsh_title_vector': 'title_feature_vector',
            'lsh_title_hash': 'title_hash_buckets',
            'lsh_ingredients_vector': 'ingredients_feature_vector',
            'lsh_ingredients_hash': 'ingredients_hash_buckets',
            'lsh_instructions_vector': 'instructions_feature_vector',
            'lsh_instructions_hash': 'instructions_hash_buckets',
            'lsh_text_vector': 'text_feature_vector',
            'lsh_text_hash': 'text_hash_buckets',
            'lsh_image_vector': 'image_feature_vector',
            'lsh_image_hash': 'image_hash_buckets',
            'processed_title': 'processed_title',
            'processed_ingredients': 'processed_ingredients',
            'processed_instructions': 'processed_instructions'
        }
        
        # Create a new recipe dictionary with the correct field names
        final_recipe = recipe.copy()
        for lsh_field, db_field in field_mapping.items():
            if lsh_field in processed_recipe:
                final_recipe[db_field] = processed_recipe[lsh_field]
            elif lsh_field in recipe:  # Check if already in the original recipe
                final_recipe[db_field] = recipe[lsh_field]
            else:
                logger.warning(f"Missing field {lsh_field} in processed recipe")
        
        return final_recipe
    except Exception as e:
        logger.error(f"Error in process_recipe: {str(e)}")
        logger.error(traceback.format_exc())
        # Return the original recipe without modifications
        return recipe

def process_recipes(input_file: str, output_file: str, images_dir: str, create_test_recipes: bool = False) -> bool:
    """Process all recipes in the input file and write to output file in JSONL format"""
    try:
        # Read input file line by line (JSONL format - one JSON object per line)
        recipes = []
        line_count = 0
        error_count = 0
        
        with open(input_file, 'r') as f:
            for line_number, line in enumerate(f, 1):
                line_count += 1
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                try:
                    recipe = json.loads(line)
                    recipes.append(recipe)
                except json.JSONDecodeError as e:
                    error_count += 1
                    logger.error(f"Error parsing JSON at line {line_number}: {e}")
                    logger.error(f"Problematic line: {line[:100]}...")
        
        logger.info(f"Loaded {len(recipes)} recipes from {input_file}")
        logger.info(f"Read {line_count} lines, found {error_count} errors")
        logger.info(f"Using images directory: {images_dir}")
        
        # Get available images if needed
        available_images = None
        if create_test_recipes and images_dir:
            available_images = [f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
            logger.info(f"Found {len(available_images)} images to use for test recipes")
            if len(available_images) > 0:
                logger.info(f"Sample images: {available_images[:5]}")
        
        # Process each recipe
        processed_recipes = []
        processed_count = 0
        error_count = 0
        
        for i, recipe in enumerate(recipes):
            try:
                processed_recipe = process_recipe(recipe, images_dir, available_images if create_test_recipes else None)
                processed_recipes.append(processed_recipe)
                processed_count += 1
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1} recipes")
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing recipe {i}: {str(e)}")
                logger.error(f"Recipe data: {recipe}")
        
        # Write output file in JSONL format (one JSON object per line)
        with open(output_file, 'w') as f:
            for recipe in processed_recipes:
                f.write(json.dumps(recipe) + '\n')
        
        logger.info(f"Wrote {len(processed_recipes)} recipes with embeddings to {output_file}")
        logger.info(f"Successfully processed {processed_count} recipes, encountered {error_count} errors")
        return True
        
    except Exception as e:
        logger.error(f"Error processing recipes: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def create_test_output_file(output_file: str, count: int = 10) -> bool:
    """Create a small test output file with a subset of recipes"""
    try:
        recipes = []
        with open(output_file, 'r') as f:
            for line in f:
                recipes.append(json.loads(line))
                if len(recipes) >= count:
                    break
        
        test_output_file = output_file.replace('.json', '_test.json')
        with open(test_output_file, 'w') as f:
            for recipe in recipes:
                f.write(json.dumps(recipe) + '\n')
        
        logger.info(f"Created test file with {len(recipes)} recipes: {test_output_file}")
        return True
    except Exception as e:
        logger.error(f"Error creating test output file: {str(e)}")
        return False

if __name__ == "__main__":
    # Define file paths
    base_dir = Path(__file__).parent
    project_root = base_dir.parent
    input_file = base_dir / "db" / "sample_recipes_cleaned.json"
    output_file = base_dir / "db" / "sample_recipes_with_hashed.json"
    
    # Path to the food images directory
    images_dir = project_root / "backend" / "static" / "food-images"
    
    # Whether to create test recipes with existing images
    create_test_recipes = True
    
    # Ensure the images directory exists
    if not images_dir.exists():
        logger.warning(f"Images directory not found: {images_dir}")
        logger.warning("Will proceed without image embeddings")
        images_dir = None
    else:
        logger.info(f"Found images directory: {images_dir}")
        image_count = len(list(images_dir.glob('*.*')))
        logger.info(f"Number of images: {image_count}")
        
        # Log some sample image names to verify
        sample_images = list(images_dir.glob('*.*'))[:5]
        logger.info(f"Sample images: {[img.name for img in sample_images]}")
    
    logger.info("Starting to generate multi-field LSH embeddings using FAISS (including images)")
    
    # Process recipes
    success = process_recipes(input_file, output_file, str(images_dir) if images_dir else None, create_test_recipes)
    
    if success:
        logger.info("Successfully generated multi-field LSH embeddings")
        
        # Create a small test file with a subset of recipes
        if create_test_recipes:
            create_test_output_file(str(output_file))
    else:
        logger.error("Failed to generate multi-field LSH embeddings")
