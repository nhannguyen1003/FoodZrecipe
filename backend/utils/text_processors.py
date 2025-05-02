#!/usr/bin/env python3
"""
Field-specific text processors for recipe data.
This module provides specialized text processing for different recipe fields (title, ingredients, instructions).
"""
import re
import string
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Common stopwords to remove
STOPWORDS = {
    'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 
    'by', 'with', 'in', 'out', 'of', 'this', 'that', 'these', 'those'
}

# Title-specific stopwords (common recipe qualifiers)
TITLE_STOPWORDS = {
    'easy', 'quick', 'simple', 'best', 'homemade', 'delicious', 'healthy', 
    'tasty', 'fast', 'favorite', 'perfect', 'ultimate', 'traditional'
}

# Ingredient measurement terms
MEASUREMENTS = {
    'cup', 'cups', 'tablespoon', 'tablespoons', 'tbsp', 'teaspoon', 'teaspoons', 
    'tsp', 'ounce', 'ounces', 'oz', 'pound', 'pounds', 'lb', 'lbs', 'gram', 
    'grams', 'g', 'kilogram', 'kilograms', 'kg', 'ml', 'milliliter', 'milliliters',
    'l', 'liter', 'liters', 'pinch', 'dash'
}

class TextProcessor:
    """Base class for text processing with common methods"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Basic text normalization common to all fields"""
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def remove_stopwords(tokens: List[str], additional_stopwords: Optional[set] = None) -> List[str]:
        """Remove common stopwords from token list"""
        stopwords_to_remove = STOPWORDS
        if additional_stopwords:
            stopwords_to_remove = stopwords_to_remove.union(additional_stopwords)
            
        return [token for token in tokens if token not in stopwords_to_remove]
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Simple tokenization by splitting on whitespace"""
        return text.split()


class TitleProcessor(TextProcessor):
    """Specialized processor for recipe titles"""
    
    def process(self, title: str) -> str:
        """Process recipe title for improved search relevance"""
        if not title:
            return ""
        
        # Normalize text
        normalized = self.normalize_text(title)
        
        # Tokenize
        tokens = self.tokenize(normalized)
        
        # Remove title-specific stopwords
        filtered_tokens = self.remove_stopwords(tokens, TITLE_STOPWORDS)
        
        # Join tokens back into a string
        return ' '.join(filtered_tokens)


class IngredientsProcessor(TextProcessor):
    """Specialized processor for recipe ingredients"""
    
    @staticmethod
    def extract_ingredient_names(ingredients: List[str]) -> List[str]:
        """Extract main ingredient names from ingredient list"""
        extracted_ingredients = []
        
        for ingredient in ingredients:
            # Skip empty ingredients
            if not ingredient or not ingredient.strip():
                continue
                
            # Normalize the ingredient text
            normalized = TextProcessor.normalize_text(ingredient)
            
            # Split into tokens
            tokens = normalized.split()
            
            # Remove measurement terms
            tokens = [token for token in tokens if token not in MEASUREMENTS]
            
            # Remove numeric values (quantities)
            tokens = [token for token in tokens if not re.match(r'^\d+(\.\d+)?$', token)]
            
            # Remove stopwords
            tokens = [token for token in tokens if token not in STOPWORDS]
            
            # If we have tokens left, join them and add to our list
            if tokens:
                extracted_ingredients.append(' '.join(tokens))
        
        return extracted_ingredients
    
    def process(self, ingredients: List[str]) -> List[str]:
        """Process recipe ingredients list for improved search relevance"""
        if not ingredients:
            return []
        
        # Extract ingredient names
        return self.extract_ingredient_names(ingredients)


class InstructionsProcessor(TextProcessor):
    """Basic processor for recipe instructions (minimal for MVP)"""
    
    def process(self, instructions: str) -> str:
        """Process recipe instructions (basic processing for MVP)"""
        if not instructions:
            return ""
        
        # For MVP, just normalize the text
        return self.normalize_text(instructions)


# Create processor instances
title_processor = TitleProcessor()
ingredients_processor = IngredientsProcessor()
instructions_processor = InstructionsProcessor()


def process_recipe_text_fields(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process all text fields in a recipe with field-specific processors
    Returns a dictionary with processed fields
    """
    processed = {}
    
    # Process title
    title = recipe.get('title', '')
    processed['processed_title'] = title_processor.process(title)
    
    # Process ingredients
    ingredients = recipe.get('ingredients', [])
    if isinstance(ingredients, str):
        # Handle case where ingredients might be a string
        ingredients = [ingredient.strip() for ingredient in ingredients.split(',')]
    
    processed['processed_ingredients'] = ingredients_processor.process(ingredients)
    
    # Process instructions (minimal for MVP)
    instructions = recipe.get('instructions', '')
    processed['processed_instructions'] = instructions_processor.process(instructions)
    
    return processed 