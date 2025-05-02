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
      
      // Fetch recipes based on the mode (search query, category, or image)
      if (query) {
        console.log(`Searching for recipes with query: "${query}"`);
        
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const apiPrefix = '/api/v1';
        const url = `${apiBaseUrl}${apiPrefix}/search/text?query=${encodeURIComponent(query)}&limit=20`;
        console.log(`Search URL: ${url}`);
        
        const response = await fetch(url);
        console.log(`Search response status: ${response.status}`);
        
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`API error ${response.status}: ${errorText}`);
        }
        
        data = await response.json();
        console.log(`Search successful, got ${data.length} recipes`);
      } else if (category) {
        console.log(`Fetching recipes for category slug: "${category}"`);
        
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const apiPrefix = '/api/v1';
        const url = `${apiBaseUrl}${apiPrefix}/search/text?query=${encodeURIComponent(category)}&limit=20`;
        console.log(`Category search URL: ${url}`);
        
        const response = await fetch(url);
        console.log(`Category search response status: ${response.status}`);
        
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`API error ${response.status}: ${errorText}`);
        }
        
        data = await response.json();
        console.log(`Category search successful, got ${data.length} recipes`);
      } else if (window && window.sessionStorage && window.sessionStorage.getItem('searchImage')) {
        // Get image from session storage and perform image search
        console.log('Performing image search');
        try {
          // Get the image data from session storage
          const imageData = window.sessionStorage.getItem('searchImage');
          if (!imageData) {
            throw new Error('No image data found in session storage');
          }
          console.log('Image data found in session storage, length:', imageData.length);
          
          // Convert base64 image data to a Blob for upload
          const base64Response = await fetch(imageData);
          const imageBlob = await base64Response.blob();
          console.log('Converted image data to Blob:', imageBlob.size, 'bytes,', imageBlob.type);
          
          // Create a File object from the Blob
          const imageFile = new File([imageBlob], 'search-image.jpg', { type: 'image/jpeg' });
          console.log('Created File object:', imageFile.name, imageFile.size, 'bytes,', imageFile.type);
          
          // Create FormData for multipart/form-data upload
          const formData = new FormData();
          formData.append('image', imageFile);
          
          // Make the API request
          const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
          const apiPrefix = '/api/v1';
          const url = `${apiBaseUrl}${apiPrefix}/search/image`;
          console.log(`Image search URL: ${url}`);
          
          // Log the actual API URL from env vars for debugging
          console.log('API base URL from env:', process.env.NEXT_PUBLIC_API_URL);
          
          const response = await fetch(url, {
            method: 'POST',
            body: formData
          });
          
          console.log(`Image search response status: ${response.status}`);
          
          if (!response.ok) {
            const errorText = await response.text();
            console.error('Image search error response:', errorText);
            throw new Error(`API error ${response.status}: ${errorText}`);
          }
          
          data = await response.json();
          console.log(`Image search successful, got ${data.length} results:`, data);
        } catch (imageError) {
          console.error('Image search error:', imageError);
          throw imageError;
        }
      } else {
        console.log(`Fetching latest recipes`);
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

  // Only fetch if we don't have prefetched data
  useEffect(() => {
    // Skip fetching if we have prefetched data
    if (prefetchedRecipes !== undefined) {
      return;
    }
    
    fetchRecipes();
  }, [query, category, prefetchedRecipes]);

  const handleRetry = () => {
    fetchRecipes(true);
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
        
        {/* Error state */}
        {error && !loading && !retrying && (
          <div className="text-center py-12">
            <div className="bg-white rounded-lg shadow-md p-8 max-w-xl mx-auto">
              <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <h3 className="text-xl font-bold text-gray-800 mb-2">No Results Found</h3>
              <p className="text-gray-600 mb-4">
                We couldn't find any recipes matching your search criteria. Please try a different search term or browse our categories.
              </p>
              <button
                onClick={handleRetry}
                className="px-4 py-2 bg-amber-500 text-white rounded-md hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                Try Again
              </button>
            </div>
          </div>
        )}
        
        {/* Empty results */}
        {!loading && !error && recipes.length === 0 && (
          <div className="text-center py-12">
            <div className="bg-white rounded-lg shadow-md p-8 max-w-xl mx-auto">
              <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-xl font-bold text-gray-800 mb-2">No recipes found</h3>
              <p className="text-gray-600">
                Try searching for a different term or browse our featured recipes below.
              </p>
            </div>
          </div>
        )}
        
        {/* Results grid */}
        {!loading && !error && recipes.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {recipes.map((recipe) => (
              <RecipeCard key={recipe.id} recipe={recipe} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
} 