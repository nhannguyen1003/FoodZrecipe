#!/usr/bin/env python3
"""
Test script for field-specific text processors.
This script demonstrates how the specialized text processors work on sample recipe data.
"""
import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Import text processors
from backend.utils.text_processors import (
    title_processor,
    ingredients_processor,
    instructions_processor,
    process_recipe_text_fields
)

def print_separator(title):
    """Print a section separator"""
    print("\n" + "=" * 70)
    print(f" {title} ".center(70, "-"))
    print("=" * 70 + "\n")

def test_title_processor():
    """Test the title processor on sample titles"""
    print_separator("Title Processor Test")
    
    sample_titles = [
        "Easy Homemade Chicken Parmesan",
        "The Best Quick and Simple Chocolate Chip Cookies",
        "Delicious Traditional Italian Pasta",
        "Healthy Vegetarian Stir Fry",
        "Ultimate Perfect Apple Pie"
    ]
    
    print("Sample titles and their processed versions:\n")
    for title in sample_titles:
        processed = title_processor.process(title)
        print(f"Original: {title}")
        print(f"Processed: {processed}")
        print()

def test_ingredients_processor():
    """Test the ingredients processor on sample ingredient lists"""
    print_separator("Ingredients Processor Test")
    
    sample_ingredient_lists = [
        [
            "2 cups all-purpose flour",
            "1/2 cup granulated sugar",
            "1 tablespoon baking powder",
            "1/2 teaspoon salt",
            "1 cup milk",
            "1/4 cup vegetable oil",
            "2 large eggs"
        ],
        [
            "500g boneless chicken breast, diced",
            "2 tbsp olive oil",
            "1 large onion, chopped",
            "3 cloves garlic, minced",
            "1 red bell pepper, sliced",
            "1 tsp dried oregano",
            "400g can diced tomatoes",
            "Salt and pepper to taste"
        ]
    ]
    
    print("Sample ingredient lists and their processed versions:\n")
    for i, ingredients in enumerate(sample_ingredient_lists):
        processed = ingredients_processor.process(ingredients)
        print(f"Original ingredient list {i+1}:")
        for ingredient in ingredients:
            print(f"  - {ingredient}")
        print("\nProcessed ingredient names:")
        for ingredient in processed:
            print(f"  - {ingredient}")
        print()

def test_instructions_processor():
    """Test the instructions processor on sample instructions"""
    print_separator("Instructions Processor Test")
    
    sample_instructions = [
        "Preheat the oven to 350°F (175°C). Grease a 9-inch round cake pan. In a large bowl, whisk together the flour, sugar, baking powder, and salt. Add the milk, oil, and eggs, and beat until smooth. Pour into the prepared pan and bake for 30-35 minutes.",
        "Heat oil in a large skillet over medium-high heat. Add chicken and cook until browned, about 5 minutes. Remove chicken and set aside. In the same skillet, add onion and cook until softened, about 3 minutes. Add garlic and cook for 30 seconds. Add bell pepper and oregano, and cook for 2 minutes. Return chicken to the skillet, add tomatoes, and season with salt and pepper. Simmer for 15 minutes, stirring occasionally."
    ]
    
    print("Sample instructions and their processed versions:\n")
    for i, instructions in enumerate(sample_instructions):
        processed = instructions_processor.process(instructions)
        print(f"Original instructions {i+1}:")
        print(f"  {instructions[:100]}...")
        print("\nProcessed instructions:")
        print(f"  {processed[:100]}...")
        print()

def test_full_recipe_processing():
    """Test processing a complete recipe with all fields"""
    print_separator("Full Recipe Processing Test")
    
    sample_recipe = {
        "title": "Easy Homemade Chicken Curry",
        "ingredients": [
            "2 tablespoons vegetable oil",
            "1 large onion, finely chopped",
            "3 cloves garlic, minced",
            "1 tablespoon fresh ginger, grated",
            "2 tablespoons curry powder",
            "1 teaspoon ground cumin",
            "1/2 teaspoon turmeric",
            "1/4 teaspoon cayenne pepper",
            "500g boneless chicken thighs, cut into chunks",
            "1 can (400ml) coconut milk",
            "1 can (400g) diced tomatoes",
            "Salt and black pepper to taste",
            "Fresh cilantro for garnish"
        ],
        "instructions": "Heat oil in a large pot over medium heat. Add onion and cook until softened, about 5 minutes. Add garlic and ginger, and cook for 1 minute. Stir in curry powder, cumin, turmeric, and cayenne pepper, and cook for 30 seconds until fragrant. Add chicken and cook until browned on all sides, about 5 minutes. Pour in coconut milk and tomatoes. Season with salt and black pepper. Bring to a simmer, then reduce heat to low and cook for 20-25 minutes, or until chicken is cooked through and sauce has thickened. Garnish with cilantro before serving."
    }
    
    print("Sample recipe:")
    print(f"Title: {sample_recipe['title']}")
    print("Ingredients:")
    for ingredient in sample_recipe['ingredients'][:5]:
        print(f"  - {ingredient}")
    print("  ...")
    print(f"Instructions: {sample_recipe['instructions'][:100]}...")
    
    processed = process_recipe_text_fields(sample_recipe)
    
    print("\nProcessed recipe fields:")
    print(f"Processed title: {processed['processed_title']}")
    print("Processed ingredients:")
    for ingredient in processed['processed_ingredients']:
        print(f"  - {ingredient}")
    print(f"Processed instructions: {processed['processed_instructions'][:100]}...")

def main():
    """Run all tests"""
    test_title_processor()
    test_ingredients_processor()
    test_instructions_processor()
    test_full_recipe_processing()
    
    print_separator("Tests Completed")

if __name__ == "__main__":
    main() 