'use client';

import { useState, useEffect } from 'react';
import RecipeCard from './RecipeCard';
import Link from 'next/link';
import { recipeApi, formatRecipe, RecipeResponse } from '../utils/api';

// Mock data to use if API fails
const FALLBACK_RECIPES = [
  {
    id: '1',
    title: 'Lemon Rosemary Chicken Soup',
    image: 'http://localhost:8000/food-images/lemon-and-rosemary-chicken-minestrone-51155660.jpg',
    category: 'Soups',
    readTime: '30 min prep',
    postedTime: '2 days ago',
    author: { name: 'Chef Jamie' }
  },
  {
    id: '2',
    title: 'Family Style Pita Sandwiches',
    image: 'http://localhost:8000/food-images/herbed-lamb-pita-sandwiches-358489.jpg',
    category: 'Dinner',
    readTime: '15 min prep',
    postedTime: '3 days ago',
    author: { name: 'Chef Alex' }
  },
  {
    id: '3',
    title: 'Cauliflower Black Bean Tostadas',
    image: 'http://localhost:8000/food-images/cauliflower-and-refried-bean-tostadas-51237820.jpg',
    category: 'Vegetarian',
    readTime: '20 min prep',
    postedTime: '1 week ago',
    author: { name: 'Chef Morgan' }
  },
  {
    id: '4',
    title: 'BBQ Pulled Pork',
    image: 'http://localhost:8000/food-images/barbecue-pulled-pork-sandwiches-with-homemade-sauce-51149010.jpg',
    category: 'Dinner',
    readTime: '45 min prep',
    postedTime: '4 days ago',
    author: { name: 'Chef Sam' }
  },
  {
    id: '5',
    title: 'Chocolate Chip Cookies',
    image: 'http://localhost:8000/food-images/chocolate-chip-cookies-237280.jpg',
    category: 'Desserts',
    readTime: '10 min prep',
    postedTime: '5 days ago',
    author: { name: 'Chef Pat' }
  },
  {
    id: '6',
    title: 'Greek Salad',
    image: 'http://localhost:8000/food-images/greek-style-salad-with-bulgur-and-mint-363242.jpg',
    category: 'Salads',
    readTime: '15 min prep',
    postedTime: '2 weeks ago',
    author: { name: 'Chef Jordan' }
  }
];

// IDs of the test recipes we created
const TEST_RECIPE_IDS = [1275, 1276];

export default function LatestRecipes() {
  const [recipes, setRecipes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecipes = async () => {
      try {
        setLoading(true);
        console.log('Fetching latest recipes from API...');
        
        try {
          // First get recipes from the standard endpoint
          const data = await recipeApi.getLatest(6);
          console.log('Received latest recipes:', data);
          
          // Check if we have data
          if (data && data.length > 0) {
            // We have data, format and use it
            setRecipes(data.map(recipe => formatRecipe(recipe)));
            setError(null);
          } else {
            // If no data, try to fetch our specific test recipes
            console.log('No recipes returned from API, trying to fetch test recipes...');
            
            const testRecipes: RecipeResponse[] = [];
            
            // Try to fetch each test recipe
            for (const id of TEST_RECIPE_IDS) {
              try {
                const testRecipe = await recipeApi.getById(id.toString());
                if (testRecipe) {
                  testRecipes.push(testRecipe);
                }
              } catch (e) {
                console.error(`Could not fetch test recipe ${id}:`, e);
              }
            }
            
            if (testRecipes.length > 0) {
              // If we got some test recipes, use them
              console.log('Using test recipes:', testRecipes);
              setRecipes(testRecipes.map(recipe => formatRecipe(recipe)));
              setError(null);
            } else {
              // If all else fails, use fallback data
              console.log('No test recipes available, using fallback data');
              setRecipes(FALLBACK_RECIPES);
            }
          }
        } catch (fetchError) {
          console.error('API fetch error:', fetchError);
          // Use fallback data if there's a fetch error
          console.log('Using fallback recipe data due to fetch error');
          setRecipes(FALLBACK_RECIPES);
        }
      } catch (err) {
        console.error('Error in recipe component:', err);
        setError('Failed to load latest recipes: ' + (err instanceof Error ? err.message : String(err)));
        
        // Fallback to sample data immediately
        console.log('Using fallback recipe data');
        setRecipes(FALLBACK_RECIPES);
      } finally {
        setLoading(false);
      }
    };

    fetchRecipes();
  }, []);

  return (
    <section className="py-16 bg-[#F2F2F2]">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold text-gray-800">Latest Recipes</h2>
          <Link
            href="/recipes"
            className="text-amber-500 hover:text-amber-600 font-medium flex items-center"
          >
            View more →
          </Link>
        </div>
        
        {/* Loading state */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="h-48 bg-gray-200 animate-pulse"></div>
                <div className="p-4">
                  <div className="h-6 bg-gray-200 animate-pulse rounded w-3/4 mb-3"></div>
                  <div className="h-4 bg-gray-200 animate-pulse rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* Error message (only shown if no recipes available) */}
        {!loading && error && recipes.length === 0 && (
          <div className="text-center py-8">
            <p className="text-red-500">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-4 px-4 py-2 bg-amber-500 text-white rounded hover:bg-amber-600"
            >
              Try Again
            </button>
          </div>
        )}
        
        {/* Recipe grid - always shown if recipes are available */}
        {!loading && recipes.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {recipes.map((recipe) => (
              <RecipeCard
                key={recipe.id}
                id={recipe.id}
                title={recipe.title}
                image={recipe.image}
                category={recipe.category}
                readTime={recipe.readTime}
                postedTime={recipe.postedTime}
                author={recipe.author}
                saved={false}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
} 