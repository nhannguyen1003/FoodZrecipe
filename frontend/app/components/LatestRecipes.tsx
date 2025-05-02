'use client';

import { useState, useEffect } from 'react';
import RecipeCard from './RecipeCard';
import Link from 'next/link';
import { recipeApi, formatRecipe, RecipeResponse } from '../utils/api';

export default function LatestRecipes() {
  const [recipes, setRecipes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  const fetchRecipes = async (retryAttempt = false) => {
    try {
      setLoading(true);
      if (retryAttempt) {
        setRetrying(true);
      }
      console.log('Fetching latest recipes from API...');
      
      // Get recipes from the standard endpoint
      const data = await recipeApi.getLatest(6);
      console.log('Received latest recipes:', data);
      
      // Check if we have data
      if (data && data.length > 0) {
        // We have data, format and use it
        setRecipes(data.map(recipe => formatRecipe(recipe)));
        setError(null);
      } else {
        // No data available
        setRecipes([]);
        setError('No recipes found in the database');
      }
    } catch (err) {
      console.error('Error in recipe component:', err);
      setRecipes([]);
      setError('Failed to load latest recipes: ' + (err instanceof Error ? err.message : String(err)));
    } finally {
      setLoading(false);
      setRetrying(false);
    }
  };

  useEffect(() => {
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
        
        {/* Error message */}
        {!loading && error && (
          <div className="text-center py-8">
            <p className="text-red-500">{error}</p>
            <button 
              onClick={() => fetchRecipes(true)} 
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
              onClick={() => fetchRecipes(true)}
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