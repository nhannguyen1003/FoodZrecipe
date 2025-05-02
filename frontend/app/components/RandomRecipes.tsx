'use client';

import { useState, useEffect } from 'react';
import RecipeCard from './RecipeCard';
import Link from 'next/link';
import { recipeApi, formatRecipe, RecipeResponse } from '../utils/api';

export default function RandomRecipes() {
  const [recipes, setRecipes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  const fetchRandomRecipes = async (retryAttempt = false) => {
    try {
      setLoading(true);
      if (retryAttempt) {
        setRetrying(true);
      }
      console.log('Fetching recipes from API...');
      
      // Fetch 20 recipes from the database to have a good pool for randomization
      const data = await recipeApi.getLatest(20); 
      console.log(`Received ${data.length} recipes from API`);
      
      if (data && data.length > 0) {
        // Log some sample data for debugging
        console.log('Sample recipe data:', {
          title: data[0].title,
          id: data[0].id,
          image_name: data[0].image_name || 'MISSING',
          categories: data[0].categories?.join(', ') || 'none'
        });
        
        // Shuffle the recipes to randomize them
        const shuffled = [...data].sort(() => 0.5 - Math.random());
        
        // Take the first 6 (or fewer if we don't have 6 recipes)
        const randomSample = shuffled.slice(0, Math.min(6, shuffled.length));
        console.log('Selected random recipes:', randomSample.map(r => r.title));
        
        // Format each recipe with proper image paths
        const formattedRecipes = randomSample.map(recipe => {
          const formatted = formatRecipe(recipe);
          console.log(`Formatted recipe "${recipe.title}" (ID: ${recipe.id}) with image: ${formatted.image}`);
          return formatted;
        });
        
        setRecipes(formattedRecipes);
        setError(null);
      } else {
        // If we received an empty array, the database might be empty
        setRecipes([]);
        setError('No recipes found in the database');
      }
    } catch (err) {
      console.error('Error fetching recipes:', err);
      setRecipes([]);
      setError('Failed to load recipes: ' + (err instanceof Error ? err.message : String(err)));
    } finally {
      setLoading(false);
      setRetrying(false);
    }
  };

  useEffect(() => {
    fetchRandomRecipes();
  }, []);

  const handleRetry = () => {
    fetchRandomRecipes(true);
  };

  return (
    <section className="py-16 bg-[#F2F2F2]">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold text-gray-800">Recipe Recommendations</h2>
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
        
        {/* Error message */}
        {!loading && error && (
          <div className="text-center py-8">
            <p className="text-red-500">{error}</p>
            <button 
              onClick={handleRetry} 
              disabled={retrying}
              className={`mt-4 px-4 py-2 bg-amber-500 text-white rounded hover:bg-amber-600 ${retrying ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {retrying ? 'Trying again...' : 'Try Again'}
            </button>
          </div>
        )}
        
        {/* Recipe grid */}
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
        
        {/* No recipes found */}
        {!loading && !error && recipes.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">No recipes found in the database</p>
            <button 
              onClick={handleRetry}
              className="mt-4 px-4 py-2 bg-amber-500 text-white rounded hover:bg-amber-600"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </section>
  );
} 