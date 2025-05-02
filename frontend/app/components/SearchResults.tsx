'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import RecipeCard from './RecipeCard';
import { recipeApi, formatRecipe, RecipeResponse, fetchApi } from '../utils/api';

interface SearchResultsProps {
  query?: string;
  category?: string;
  categoryDisplayName?: string;
  limit?: number;
  prefetchedRecipes?: any[];
  prefetchedLoading?: boolean;
  prefetchedError?: string | null;
}

export default function SearchResults({ query, category, categoryDisplayName, limit = 20, prefetchedRecipes, prefetchedLoading, prefetchedError }: SearchResultsProps) {
  // Log props for debugging
  console.log("SearchResults Component Props:", {
    hasQuery: !!query,
    query,
    hasCategory: !!category,
    category,
    categoryDisplayName,
    hasPrefetchedRecipes: !!prefetchedRecipes,
    prefetchedRecipesCount: prefetchedRecipes?.length,
    prefetchedLoading,
    prefetchedError
  });
  
  // Initialize state from prefetched data if available
  const [recipes, setRecipes] = useState<any[]>(prefetchedRecipes || []);
  const [loading, setLoading] = useState(prefetchedLoading !== undefined ? prefetchedLoading : true);
  const [error, setError] = useState<string | null>(prefetchedError || null);
  const [retrying, setRetrying] = useState(false);

  const fetchRecipes = async (retryAttempt = false) => {
    try {
      setLoading(true);
      if (retryAttempt) {
        setRetrying(true);
      }
      
      let data: RecipeResponse[] = [];
      
      // Fetch recipes based on the mode (search query, category, or latest)
      if (query) {
        console.log(`Searching for recipes with query: "${query}"`);
        data = await recipeApi.search(query);
      } else if (category) {
        console.log(`Fetching recipes for category slug: "${category}"`);
        
        try {
          // Try search endpoint with category as the query
          data = await recipeApi.search(category);
          console.log(`Found ${data.length} recipes for category: ${category}`);
        } catch (categoryError) {
          console.error('Category search error:', categoryError);
          // Don't use fallback data, just propagate the error
          throw categoryError;
        }
      } else {
        console.log(`Fetching latest ${limit} recipes`);
        data = await recipeApi.getLatest(limit);
      }
      
      console.log(`Received ${data.length} recipes from API`);
      
      if (data && data.length > 0) {
        // Format each recipe with proper image paths
        const formattedRecipes = data.map(recipe => {
          const formatted = formatRecipe(recipe);
          return formatted;
        });
        
        setRecipes(formattedRecipes);
        setError(null);
      } else {
        setRecipes([]);
        setError('No recipes found matching your criteria');
      }
    } catch (err) {
      console.error('Error fetching recipes:', err);
      // Improved error handling to avoid [object Object]
      let errorMessage = 'Failed to load recipes';
      if (err instanceof Error) {
        errorMessage += `: ${err.message}`;
      } else if (typeof err === 'string') {
        errorMessage += `: ${err}`;
      } else if (err && typeof err === 'object') {
        // Try to extract more details from the error object
        const details = JSON.stringify(err, null, 2);
        errorMessage += `: ${details}`;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
      setRetrying(false);
    }
  };

  // Direct API fetch without fallbacks
  const tryDirectFetch = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Trying direct fetch approach');
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const apiPrefix = '/api/v1';
      
      let url = '';
      
      if (category) {
        // Search for recipes using the category as a search term
        url = `${apiBaseUrl}${apiPrefix}/recipes/search/?query=${encodeURIComponent(category)}&limit=${limit}`;
      } else if (query) {
        // If we have a search query, use the search endpoint
        url = `${apiBaseUrl}${apiPrefix}/recipes/search/?query=${encodeURIComponent(query)}&limit=${limit}`;
      } else {
        // Otherwise, get latest recipes
        url = `${apiBaseUrl}${apiPrefix}/recipes/?limit=${limit}`;
      }
      
      console.log(`Direct fetch URL: ${url}`);
      
      const response = await fetch(url);
      console.log(`Direct fetch response status: ${response.status}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error ${response.status}: ${errorText}`);
      }
      
      const data = await response.json();
      console.log(`Direct fetch success, got ${data.length} recipes`);
      
      if (data && data.length > 0) {
        // Format recipes from direct fetch
        const formattedRecipes = data.map((recipe: RecipeResponse) => formatRecipe(recipe));
        setRecipes(formattedRecipes);
      } else {
        setRecipes([]);
        setError('No recipes found for this category');
      }
    } catch (err) {
      console.error('Direct fetch error:', err);
      // Improved error handling to avoid [object Object]
      let errorMessage = 'Search failed';
      if (err instanceof Error) {
        errorMessage += `: ${err.message}`;
      } else if (typeof err === 'string') {
        errorMessage += `: ${err}`;
      } else if (err && typeof err === 'object') {
        // Try to extract more details from the error object
        const details = JSON.stringify(err, null, 2);
        errorMessage += `: ${details}`;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Only fetch if we don't have prefetched data
  useEffect(() => {
    // Skip fetching if we have prefetched data
    if (prefetchedRecipes !== undefined) {
      return;
    }
    
    // Always use direct fetch for categories for more consistent results
    if (category) {
      tryDirectFetch();
    } else if (query) {
      // For explicit text queries, also use direct fetch for consistency
      tryDirectFetch();
    } else {
      fetchRecipes();
    }
  }, [query, category, prefetchedRecipes]);

  const handleRetry = () => {
    if (category || query) {
      tryDirectFetch();
    } else {
      fetchRecipes(true);
    }
  };

  // Determine title based on search mode
  const getTitle = () => {
    if (query) {
      return `Search Results for "${query}"`;
    } else if (category || categoryDisplayName) {
      // Use the explicit display name if provided
      if (categoryDisplayName) {
        return `${categoryDisplayName} Recipes`;
      }
      // Otherwise format the slug
      const displayName = category ? 
        category.split('-')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ') : 'Category';
      return `${displayName} Recipes`;
    } else {
      return 'Latest Recipes';
    }
  };

  return (
    <section className="py-8">
      <div className="container mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">{getTitle()}</h1>
        
        {/* Breadcrumb */}
        <div className="mb-8 text-sm">
          <Link href="/" className="text-amber-500 hover:underline">
            Home
          </Link>
          {category && (
            <>
              <span className="mx-2">›</span>
              <Link href="/recipes" className="text-amber-500 hover:underline">
                Recipes
              </Link>
            </>
          )}
          <span className="mx-2">›</span>
          <span className="text-gray-500">
            {query ? 'Search Results' : category ? (categoryDisplayName || category) : 'All Recipes'}
          </span>
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
            <p className="text-red-500 mb-2">{error}</p>
            <div className="bg-gray-100 p-4 rounded-lg max-w-lg mx-auto mb-4 text-sm text-left overflow-auto">
              <code className="whitespace-pre-wrap">
                Try using a different search term or category
              </code>
            </div>
            <button 
              onClick={handleRetry} 
              className="mt-2 px-4 py-2 bg-amber-500 text-white rounded hover:bg-amber-600"
            >
              Try Again
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
            <p className="text-gray-500">No recipes found for this category</p>
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