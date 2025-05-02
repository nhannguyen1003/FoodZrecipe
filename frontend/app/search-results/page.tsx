'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import SearchResults from '../components/SearchResults';
import SearchBar from '../components/SearchBar';
import Image from 'next/image';
import Link from 'next/link';

export default function SearchResultsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  // Support both 'q' and 'query' parameters for backwards compatibility
  const query = searchParams.get('query') || searchParams.get('q') || '';
  const type = searchParams.get('type') || 'text';
  
  const [isLoading, setIsLoading] = useState(true);
  const [searchImage, setSearchImage] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  // Popular search suggestions
  const suggestions = [
    'Pasta', 'Chicken', 'Vegetarian', 'Slow Cooker', 
    'Breakfast', 'Dessert', 'Ham', 'Quick Dinner'
  ];
  
  useEffect(() => {
    // Load the image from sessionStorage for image search
    if (type === 'image' && typeof window !== 'undefined') {
      try {
        const storedImage = sessionStorage.getItem('searchImage');
        if (storedImage) {
          console.log('Found stored image for search');
          setSearchImage(storedImage);
        } else {
          console.warn('No image found in session storage');
          setError('No image found for search. Please try uploading an image again.');
        }
      } catch (error) {
        console.error('Failed to retrieve image from session storage:', error);
      }
    }
    
    // Set loading state when the query or type changes
    setIsLoading(true);
    setShowSuggestions(false);
    
    const timer = setTimeout(() => {
      setIsLoading(false);
      // Show suggestions after 3 seconds
      setTimeout(() => setShowSuggestions(true), 3000);
    }, 800);
    
    return () => clearTimeout(timer);
  }, [query, type]);
  
  const handleSuggestionClick = (suggestion: string) => {
    router.push(`/search?query=${encodeURIComponent(suggestion)}`);
  };
  
  const handleTryAgain = () => {
    if (type === 'image') {
      // Clear the image from session storage and redirect back to search
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem('searchImage');
      }
      router.push('/search');
    } else {
      // Refresh the current page
      window.location.reload();
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-4">
            {type === 'image' ? 'Image Search Results' : `Search Results for "${query}"`}
          </h1>
          <SearchBar />
          
          {/* Display the image being searched for in image search mode */}
          {type === 'image' && searchImage && (
            <div className="mt-6 p-4 bg-white rounded-lg shadow-sm">
              <p className="text-gray-700 mb-2">Searching for recipes similar to:</p>
              <div className="relative w-24 h-24 inline-block">
                <Image
                  src={searchImage}
                  alt="Search reference"
                  fill
                  className="object-cover rounded-md"
                />
              </div>
            </div>
          )}
        </div>
        
        <div className="mt-6">
          <SearchResults 
            query={type === 'text' ? query : undefined}
            prefetchedLoading={isLoading}
          />
        </div>
        
        {/* Popular suggestions that appear if search has no results after a delay */}
        {showSuggestions && (
          <div className="mt-8 bg-white rounded-lg shadow-md p-6 max-w-2xl mx-auto">
            <h2 className="text-lg font-medium text-gray-800 mb-3">Try these popular searches</h2>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="px-3 py-1 bg-amber-100 text-amber-800 rounded-full hover:bg-amber-200 transition text-sm"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Try again button if the search might have failed */}
        {!isLoading && showSuggestions && (
          <div className="mt-4 text-center">
            <button
              onClick={handleTryAgain}
              className="text-amber-600 hover:text-amber-800 font-medium mr-4"
            >
              Try Again
            </button>
            <Link 
              href="/"
              className="text-amber-600 hover:text-amber-800 font-medium"
            >
              Return to Home Page
            </Link>
          </div>
        )}
      </div>
    </div>
  );
} 