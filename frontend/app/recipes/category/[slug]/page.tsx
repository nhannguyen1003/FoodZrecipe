'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import SearchResults from '../../../components/SearchResults';

export default function CategoryPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [debugInfo, setDebugInfo] = useState<string>('');
  const [showDebug, setShowDebug] = useState(false);
  
  useEffect(() => {
    // Debug logging for slug
    console.log('DEBUG: Category page params:', params);
    console.log('DEBUG: Category slug:', slug);
    console.log('DEBUG: Slug type:', typeof slug);
    
    // If slug is an array, log additional details
    if (Array.isArray(slug)) {
      console.log('DEBUG: Slug is an array:', slug);
    }
  }, [params, slug]);
  
  // Debug function to test API directly
  const testApiDirectly = async () => {
    setDebugInfo('Testing API endpoints...');
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    try {
      // Try health endpoint
      const healthResponse = await fetch(`${apiBaseUrl}/api/v1/health/`);
      const healthData = await healthResponse.text();
      setDebugInfo(prev => prev + `\nHealth endpoint: ${healthResponse.status} ${healthData}`);
      
      // Try recipes endpoint
      const recipesResponse = await fetch(`${apiBaseUrl}/api/v1/recipes/?limit=1`);
      const recipesStatus = recipesResponse.status;
      setDebugInfo(prev => prev + `\nRecipes endpoint: ${recipesStatus}`);
      
      // Try categories endpoint
      const categoriesResponse = await fetch(`${apiBaseUrl}/api/v1/categories/categories/`);
      const categoriesStatus = categoriesResponse.status;
      setDebugInfo(prev => prev + `\nCategories endpoint: ${categoriesStatus}`);
      
      // Try direct category recipes endpoint
      const categoryResponse = await fetch(`${apiBaseUrl}/api/v1/recipes/?category=${slug}&limit=5`);
      const categoryStatus = categoryResponse.status;
      setDebugInfo(prev => prev + `\nCategory query endpoint: ${categoryStatus}`);
      
    } catch (error) {
      setDebugInfo(prev => prev + `\nError testing API: ${error instanceof Error ? error.message : String(error)}`);
    }
  };
  
  // Convert slug to display name for UI purposes only (e.g., 'italian-cuisine' to 'Italian Cuisine')
  const categoryDisplayName = slug
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Debug controls */}
      <div className="container mx-auto p-4">
        <button 
          onClick={() => setShowDebug(!showDebug)} 
          className="bg-gray-200 px-3 py-1 rounded text-sm mb-2"
        >
          {showDebug ? 'Hide Debug' : 'Show Debug'}
        </button>
        
        {showDebug && (
          <div className="mb-4">
            <button 
              onClick={testApiDirectly}
              className="bg-blue-500 text-white px-3 py-1 rounded text-sm mr-2"
            >
              Test API Directly
            </button>
            
            <pre className="bg-gray-800 text-green-400 p-3 rounded text-xs mt-2 overflow-auto max-h-60">
              {debugInfo || 'Click "Test API Directly" button to debug'}
            </pre>
          </div>
        )}
      </div>
      
      <SearchResults category={slug} categoryDisplayName={categoryDisplayName} />
    </div>
  );
} 