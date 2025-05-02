#!/usr/bin/env python3
"""
Test script for the multi-field search implementation.
This script demonstrates the field-specific search functionality.
"""
import sys
import os
import json
from pathlib import Path
import numpy as np
from typing import List, Dict, Any

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Import the LSH service and text processors
from backend.services.lsh_service import LSHService, lsh_service
from backend.utils.text_processors import (
    title_processor,
    ingredients_processor,
    instructions_processor
)

# Create sample recipes for testing
def create_sample_recipes():
    """Create sample recipe data for testing"""
    recipes = [
        {
            "id": 1,
            "title": "Chocolate Chip Cookies",
            "ingredients": [
                "2 cups all-purpose flour",
                "1/2 teaspoon baking soda",
                "1/2 teaspoon salt",
                "3/4 cup unsalted butter, melted",
                "1 cup packed brown sugar",
                "1/2 cup white sugar",
                "1 tablespoon vanilla extract",
                "1 egg",
                "1 egg yolk",
                "2 cups semisweet chocolate chips"
            ],
            "instructions": "Preheat the oven to 325°F (165°C). Grease cookie sheets or line with parchment paper. Sift together the flour, baking soda, and salt; set aside. In a medium bowl, cream together the melted butter, brown sugar, and white sugar until well blended. Beat in the vanilla, egg, and egg yolk until light and creamy. Mix in the sifted ingredients until just blended. Stir in the chocolate chips by hand using a wooden spoon. Drop cookie dough 1/4 cup at a time onto the prepared cookie sheets. Cookies should be about 3 inches apart. Bake for 15 to 17 minutes in the preheated oven, or until the edges are lightly toasted. Cool on baking sheets for a few minutes before transferring to wire racks to cool completely."
        },
        {
            "id": 2,
            "title": "Simple Grilled Chicken",
            "ingredients": [
                "4 boneless, skinless chicken breasts",
                "2 tablespoons olive oil",
                "2 cloves garlic, minced",
                "1 teaspoon dried oregano",
                "1/2 teaspoon paprika",
                "1/2 teaspoon salt",
                "1/4 teaspoon black pepper",
                "1 lemon, juiced"
            ],
            "instructions": "In a large bowl, whisk together olive oil, garlic, oregano, paprika, salt, pepper, and lemon juice. Add chicken breasts and toss to coat. Marinate for at least 30 minutes, or up to 4 hours in the refrigerator. Preheat grill to medium-high heat. Oil the grill grates. Remove chicken from marinade and place on the grill. Cook for 5-7 minutes per side, or until the internal temperature reaches 165°F (74°C). Remove from the grill and let rest for 5 minutes before serving."
        },
        {
            "id": 3,
            "title": "Vegetable Pasta Primavera",
            "ingredients": [
                "12 ounces fettuccine pasta",
                "2 tablespoons olive oil",
                "2 cloves garlic, minced",
                "1 red bell pepper, sliced",
                "1 yellow bell pepper, sliced",
                "1 zucchini, sliced",
                "1 cup cherry tomatoes, halved",
                "1/2 cup frozen peas",
                "1/4 cup grated Parmesan cheese",
                "2 tablespoons fresh basil, chopped",
                "Salt and pepper to taste"
            ],
            "instructions": "Cook pasta according to package directions until al dente. Drain and set aside. In a large skillet, heat olive oil over medium heat. Add garlic and cook for 30 seconds until fragrant. Add bell peppers and zucchini, and cook for 5-7 minutes until vegetables begin to soften. Add cherry tomatoes and peas, and cook for an additional 2-3 minutes. Add cooked pasta to the skillet and toss to combine with the vegetables. Sprinkle with Parmesan cheese and fresh basil. Season with salt and pepper to taste. Serve immediately."
        },
        {
            "id": 4,
            "title": "Classic Chocolate Cake",
            "ingredients": [
                "2 cups all-purpose flour",
                "2 cups sugar",
                "3/4 cup unsweetened cocoa powder",
                "2 teaspoons baking soda",
                "1 teaspoon baking powder",
                "1 teaspoon salt",
                "1 cup buttermilk",
                "1/2 cup vegetable oil",
                "2 large eggs",
                "2 teaspoons vanilla extract",
                "1 cup hot coffee"
            ],
            "instructions": "Preheat oven to 350°F (175°C). Grease and flour two 9-inch round cake pans. In a large bowl, combine flour, sugar, cocoa, baking soda, baking powder, and salt. Add buttermilk, oil, eggs, and vanilla. Beat for 2 minutes on medium speed. Stir in hot coffee (batter will be thin). Pour batter into prepared pans. Bake for 30-35 minutes or until a toothpick inserted in the center comes out clean. Cool for 10 minutes, then remove from pans to wire racks to cool completely."
        },
        {
            "id": 5,
            "title": "Garlic Butter Shrimp",
            "ingredients": [
                "1 pound large shrimp, peeled and deveined",
                "2 tablespoons butter",
                "4 cloves garlic, minced",
                "1/4 cup chicken broth",
                "1 tablespoon lemon juice",
                "2 tablespoons fresh parsley, chopped",
                "1/4 teaspoon red pepper flakes (optional)",
                "Salt and pepper to taste"
            ],
            "instructions": "In a large skillet, melt butter over medium-high heat. Add garlic and cook for 30 seconds until fragrant. Add shrimp and cook for 2-3 minutes until they start to turn pink. Add chicken broth, lemon juice, and red pepper flakes (if using). Cook for an additional 1-2 minutes until the shrimp are cooked through and the sauce is slightly reduced. Remove from heat and stir in fresh parsley. Season with salt and pepper to taste. Serve immediately."
        }
    ]
    return recipes

def process_recipes_for_lsh(recipes: List[Dict[str, Any]]):
    """Process recipes to create feature vectors and hash buckets for LSH"""
    processed_recipes = []
    
    # Mock Recipe class with attribute access
    class MockRecipe:
        def __init__(self, recipe_dict):
            self.id = recipe_dict["id"]
            
            # Generate feature vectors for each field
            # For this test, we're using character frequency vectors
            
            # Process title
            processed_title = title_processor.process(recipe_dict["title"])
            self.title_feature_vector = create_feature_vector(processed_title, lsh_service.title_dim)
            
            # Process ingredients
            processed_ingredients = ingredients_processor.process(recipe_dict["ingredients"])
            ingredients_text = " ".join(processed_ingredients)
            self.ingredients_feature_vector = create_feature_vector(ingredients_text, lsh_service.ingredients_dim)
            
            # Process instructions
            processed_instructions = instructions_processor.process(recipe_dict["instructions"])
            self.instructions_feature_vector = create_feature_vector(processed_instructions, lsh_service.instructions_dim)
            
            # Create combined text vector
            combined_text = f"{recipe_dict['title']} {' '.join(recipe_dict['ingredients'])} {recipe_dict['instructions']}"
            self.text_feature_vector = create_feature_vector(combined_text, lsh_service.vector_dim)
            
            # Placeholder for image vector
            self.image_feature_vector = None
    
    # Create feature vectors for each recipe
    for recipe in recipes:
        processed_recipes.append(MockRecipe(recipe))
    
    return processed_recipes

def create_feature_vector(text: str, dim: int) -> List[float]:
    """Create a simple feature vector based on character frequencies"""
    char_freq = {}
    for char in text:
        char_freq[char] = char_freq.get(char, 0) + 1
    
    feature_vector = np.zeros(dim, dtype=np.float32)
    total_chars = len(text) or 1  # Avoid division by zero
    
    for i, char in enumerate(sorted(char_freq.keys())):
        idx = hash(char) % dim
        feature_vector[idx] = char_freq[char] / total_chars
    
    return feature_vector.tolist()

def print_separator(title):
    """Print a section separator"""
    print("\n" + "=" * 70)
    print(f" {title} ".center(70, "-"))
    print("=" * 70 + "\n")

def test_title_search():
    """Test search by title"""
    print_separator("Search by Title")
    
    # Test queries
    queries = [
        "chocolate cookies",
        "chicken",
        "pasta with vegetables"
    ]
    
    for query in queries:
        print(f"Query: '{query}'")
        recipe_ids, _ = lsh_service.search_by_title(query, k=3)
        
        # Print results
        print("Results:")
        if not recipe_ids:
            print("  No results found")
        else:
            for recipe_id in recipe_ids:
                recipe = next((r for r in sample_recipes if r["id"] == recipe_id), None)
                if recipe:
                    print(f"  - {recipe['title']} (ID: {recipe_id})")
        print()

def test_ingredients_search():
    """Test search by ingredients"""
    print_separator("Search by Ingredients")
    
    # Test queries
    queries = [
        ["flour", "sugar", "chocolate chips"],
        ["chicken", "olive oil", "garlic"],
        ["pasta", "bell pepper", "zucchini"]
    ]
    
    for query in queries:
        print(f"Query ingredients: {', '.join(query)}")
        recipe_ids, _ = lsh_service.search_by_ingredients(query, k=3)
        
        # Print results
        print("Results:")
        if not recipe_ids:
            print("  No results found")
        else:
            for recipe_id in recipe_ids:
                recipe = next((r for r in sample_recipes if r["id"] == recipe_id), None)
                if recipe:
                    print(f"  - {recipe['title']} (ID: {recipe_id})")
        print()

def test_multi_field_search():
    """Test multi-field search with custom weights"""
    print_separator("Multi-Field Search")
    
    # Test cases
    test_cases = [
        {
            "title_query": "chocolate",
            "ingredients_query": ["flour", "sugar"],
            "weights": {"title": 0.7, "ingredients": 0.3, "instructions": 0.0},
            "description": "Search for chocolate recipes with flour and sugar (title weighted higher)"
        },
        {
            "title_query": "pasta",
            "ingredients_query": ["bell pepper", "tomatoes"],
            "weights": {"title": 0.3, "ingredients": 0.7, "instructions": 0.0},
            "description": "Search for pasta with bell peppers and tomatoes (ingredients weighted higher)"
        },
        {
            "title_query": "chicken",
            "ingredients_query": ["garlic", "lemon"],
            "weights": {"title": 0.5, "ingredients": 0.5, "instructions": 0.0},
            "description": "Search for chicken with garlic and lemon (equal weights)"
        }
    ]
    
    for test_case in test_cases:
        print(f"Test case: {test_case['description']}")
        print(f"  Title query: '{test_case['title_query']}'")
        print(f"  Ingredients query: {', '.join(test_case['ingredients_query'])}")
        print(f"  Weights: {test_case['weights']}")
        
        recipe_ids = lsh_service.multi_field_search(
            title_query=test_case['title_query'],
            ingredients_query=test_case['ingredients_query'],
            weights=test_case['weights'],
            k=3
        )
        
        # Print results
        print("Results:")
        if not recipe_ids:
            print("  No results found")
        else:
            for recipe_id in recipe_ids:
                recipe = next((r for r in sample_recipes if r["id"] == recipe_id), None)
                if recipe:
                    print(f"  - {recipe['title']} (ID: {recipe_id})")
        print()

def main():
    """Run the test script"""
    global sample_recipes
    
    print("Initializing multi-field LSH search test...")
    
    # Create sample recipes
    sample_recipes = create_sample_recipes()
    print(f"Created {len(sample_recipes)} sample recipes")
    
    # Process recipes for LSH
    processed_recipes = process_recipes_for_lsh(sample_recipes)
    print("Processed recipes for LSH")
    
    # Initialize the LSH service
    lsh_service.initialize()
    print("Initialized LSH service")
    
    # Build the LSH indices
    lsh_service.build_indices(processed_recipes)
    print("Built LSH indices")
    
    # Run tests
    test_title_search()
    test_ingredients_search()
    test_multi_field_search()
    
    print_separator("Tests Completed")

if __name__ == "__main__":
    main() 