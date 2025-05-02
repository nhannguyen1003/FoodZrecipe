'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import SearchBar from '../components/SearchBar';
import Link from 'next/link';

export default function SearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const query = searchParams.get('query') || '';
  
  // Popular search suggestions
  const suggestions = [
    'Pasta', 'Chicken', 'Vegetarian', 'Quick Dinner', 
    'Breakfast', 'Dessert', 'Slow Cooker', 'Ham'
  ];
  
  useEffect(() => {
    // Redirect to search-results if a query is provided
    if (query) {
      router.push(`/search-results?query=${encodeURIComponent(query)}`);
    }
  }, [query, router]);
  
  const handleSuggestionClick = (suggestion: string) => {
    router.push(`/search-results?query=${encodeURIComponent(suggestion)}`);
  };
  
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-4">Recipe Search</h1>
          <SearchBar />
          
          {/* Search tips */}
          <div className="mt-3 text-sm text-gray-500">
            <p>Tips: Try keywords like ingredients, dish types, or cooking methods</p>
          </div>
        </div>
        
        <div className="text-center py-8">
          <p className="text-gray-600 mb-6">Enter a search term above to find recipes</p>
          
          <div className="bg-white rounded-lg shadow-md p-6 max-w-2xl mx-auto">
            <h2 className="text-xl font-bold text-gray-800 mb-4">Popular Searches</h2>
            <div className="flex flex-wrap gap-2 justify-center">
              {suggestions.map((suggestion) => (
                <button 
                  key={suggestion}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="px-4 py-2 bg-amber-100 text-amber-800 rounded-full hover:bg-amber-200 transition"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 