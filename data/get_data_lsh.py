#!/usr/bin/env python3
"""
Generate multi-field LSH embeddings for recipes.
Takes sample_recipes_cleaned.json and generates field-specific embeddings for title, ingredients, and instructions.
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

# Add the project root to Python path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the shared LSH processor from backend
from backend.utils.lsh_utils import lsh_processor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Basic text cleaning"""
    if isinstance(text, list):
        text = " ".join(text)
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and extra whitespace
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_recipe(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single recipe to add embeddings for all fields using FAISS LSH"""
    # Use the shared LSH processor to generate consistent embeddings and hash buckets
    return lsh_processor.process_recipe(recipe)

def process_recipes(input_file: str, output_file: str) -> bool:
    """Process all recipes in the input file and write to output file in JSONL format"""
    try:
        # Read input file line by line (JSONL format - one JSON object per line)
        recipes = []
        with open(input_file, 'r') as f:
            for line in f:
                try:
                    recipe = json.loads(line.strip())
                    recipes.append(recipe)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON line: {e}")
                    logger.error(f"Problematic line: {line[:100]}...")
        
        logger.info(f"Loaded {len(recipes)} recipes from {input_file}")
        
        # Process each recipe
        processed_recipes = []
        for i, recipe in enumerate(recipes):
            try:
                processed_recipe = process_recipe(recipe)
                processed_recipes.append(processed_recipe)
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1} recipes")
            except Exception as e:
                logger.error(f"Error processing recipe {i}: {e}")
                logger.error(f"Recipe data: {recipe}")
        
        # Write output file in JSONL format (one JSON object per line)
        with open(output_file, 'w') as f:
            for recipe in processed_recipes:
                f.write(json.dumps(recipe) + '\n')
        
        logger.info(f"Wrote {len(processed_recipes)} recipes with embeddings to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing recipes: {e}")
        return False

if __name__ == "__main__":
    # Define file paths
    base_dir = Path(__file__).parent
    input_file = base_dir / "db" / "sample_recipes_cleaned.json"
    output_file = base_dir / "db" / "sample_recipes_with_hashed.json"
    
    logger.info("Starting to generate multi-field LSH embeddings using FAISS")
    
    # Process recipes
    success = process_recipes(input_file, output_file)
    
    if success:
        logger.info("Successfully generated multi-field LSH embeddings")
    else:
        logger.error("Failed to generate multi-field LSH embeddings")
