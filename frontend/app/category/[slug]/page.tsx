'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import SearchResults from '../../components/SearchResults';

// API constants - make sure we have the correct base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function CategoryPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [loading, setLoading] = useState(true);
  const [recipes, setRecipes] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  console.log("CategoryPage mounted with slug:", slug);
  
  useEffect(() => {
    const fetchCategoryRecipes = async () => {
      try {
        console.log("Fetching recipes for category:", slug);
        setLoading(true);
        
        // Use our internal API proxy route
        let response = await fetch(`/api/v1/category-search?query=${encodeURIComponent(slug)}`);
        
        // If the real API fails, try the test endpoint
        if (!response.ok) {
          console.log("Main API failed, trying test endpoint");
          response = await fetch(`/api/v1/test-search?query=${encodeURIComponent(slug)}`);
          
          // If that also fails, throw an error
          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API error ${response.status}: ${errorText}`);
          }
        }
        
        const data = await response.json();
        console.log(`Found ${data.length} recipes for category: ${slug}`, data);
        
        if (data.length === 0) {
          console.log("No recipes found for category:", slug);
          setError(`No recipes found for ${slug}`);
          setRecipes([]);
          setLoading(false);
          return;
        }
        
        // Format recipes for display
        const formattedRecipes = data.map((recipe: any) => {
          // Generate proper image URL using the backend API
          let imageUrl = '/placeholders/placeholder-recipe.jpg';
          if (recipe.image_name) {
            // Add .jpg extension if not present
            let imageName = recipe.image_name;
            if (!imageName.match(/\.(jpg|jpeg|png|gif)$/i)) {
              imageName = `${imageName}.jpg`;
            }
            // Use the backend API URL for images
            imageUrl = `${API_BASE_URL}/food-images/${imageName}`;
          }
          
          return {
            id: recipe.id.toString(),
            title: recipe.title,
            image: imageUrl,
            category: slug,
            readTime: recipe.prep_time ? `${recipe.prep_time} min prep` : '5 minutes',
            postedTime: recipe.created_at ? formatDate(recipe.created_at) : 'Recently',
            author: {
              name: recipe.user?.username || 'Anonymous'
            }
          };
        });
        
        console.log("Formatted recipes:", formattedRecipes);
        setRecipes(formattedRecipes);
        setError(null);
      } catch (err) {
        console.error('Error fetching category recipes:', err);
        setError(`Failed to load recipes: ${err instanceof Error ? err.message : String(err)}`);
      } finally {
        setLoading(false);
      }
    };
    
    if (slug) {
      fetchCategoryRecipes();
    }
  }, [slug]);
  
  // Format the display name (e.g., convert "gluten-free" to "Gluten Free")
  const categoryDisplayName = slug
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
  
  // Simple date formatter
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return 'Today';
    } else if (diffDays < 7) {
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      });
    }
  };
  
  console.log("CategoryPage rendering with:", { 
    categoryDisplayName, 
    recipes: recipes.length, 
    loading, 
    error 
  });
  
  // Make sure we're showing loading state or error state if needed
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-amber-500 mx-auto"></div>
          <p className="mt-4 text-lg text-gray-700">Loading {categoryDisplayName} recipes...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Pass our pre-fetched data directly to SearchResults */}
      <SearchResults 
        categoryDisplayName={categoryDisplayName}
        category={slug}
        prefetchedRecipes={recipes}
        prefetchedLoading={loading}
        prefetchedError={error}
      />
    </div>
  );
} 