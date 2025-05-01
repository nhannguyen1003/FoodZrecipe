'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';

// Mock data for search results
const searchResults = [
  {
    id: '1',
    title: 'Spicy Garlic Shrimp Pasta',
    image: '/images/recipes/Best-Air-Fryer-Broccoli.jpg',
    category: 'Pasta',
    prepTime: '15 mins',
    cookTime: '20 mins',
    rating: 4.8,
    reviews: 245,
    description: 'A delicious pasta dish with fresh shrimp, spicy peppers, and a garlic butter sauce.'
  },
  {
    id: '2',
    title: 'Honey Garlic Chicken Stir-Fry',
    image: '/images/recipes/-carbonnade-a-la-flamande-short-ribs-358557.jpg',
    category: 'Main Course',
    prepTime: '10 mins',
    cookTime: '15 mins',
    rating: 4.7,
    reviews: 189,
    description: 'Quick and easy honey garlic chicken with colorful vegetables in a sweet and savory sauce.'
  },
  {
    id: '3',
    title: 'Vegetable Lentil Soup',
    image: '/images/recipes/Whipped-Feta.jpg',
    category: 'Soup',
    prepTime: '15 mins',
    cookTime: '40 mins',
    rating: 4.6,
    reviews: 312,
    description: 'Hearty lentil soup packed with vegetables and warming spices - perfect for cold days.'
  },
  {
    id: '4',
    title: 'Crispy Baked Potato Wedges',
    image: '/images/recipes/-chickpea-barley-and-feta-salad-51239040.jpg',
    category: 'Side Dish',
    prepTime: '10 mins',
    cookTime: '35 mins',
    rating: 4.9,
    reviews: 156,
    description: 'Perfectly seasoned potato wedges that are crispy on the outside and fluffy on the inside.'
  },
  {
    id: '5',
    title: 'Blueberry Banana Smoothie Bowl',
    image: '/images/recipes/-chickpea-pancakes-with-leeks-squash-and-yogurt-51260630.jpg',
    category: 'Breakfast',
    prepTime: '5 mins',
    cookTime: '0 mins',
    rating: 4.5,
    reviews: 128,
    description: 'A nutritious smoothie bowl topped with fresh fruits, granola, and a drizzle of honey.'
  },
  {
    id: '6',
    title: 'Avocado Toast with Poached Eggs',
    image: '/images/recipes/-bloody-mary-tomato-toast-with-celery-and-horseradish-56389813.jpg',
    category: 'Breakfast',
    prepTime: '5 mins',
    cookTime: '10 mins',
    rating: 4.8,
    reviews: 176,
    description: 'Creamy avocado spread on toasted sourdough bread, topped with perfectly poached eggs.'
  },
];

// Function to render star rating
function StarRating({ rating }: { rating: number }) {
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.5;
  
  return (
    <div className="flex items-center">
      {[...Array(5)].map((_, i) => (
        <span key={i} className="text-amber-400">
          {i < fullStars ? (
            <span className="text-lg">★</span>
          ) : i === fullStars && hasHalfStar ? (
            <span className="text-lg">★</span>
          ) : (
            <span className="text-lg">☆</span>
          )}
        </span>
      ))}
    </div>
  );
}

export default function SearchResultsPage() {
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const query = searchParams.get('q') || '';
  const searchType = searchParams.get('type') || 'text';
  
  useEffect(() => {
    // Simulate loading state for a more realistic experience
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1500);
    
    return () => clearTimeout(timer);
  }, []);
  
  // Get search title based on the type of search
  const getSearchTitle = () => {
    if (searchType === 'image') {
      return 'Image Search Results';
    } else if (query) {
      return `Search Results for "${query}"`;
    } else {
      return 'All Recipes';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4">
        {/* Breadcrumb */}
        <div className="mb-8 text-sm">
          <Link href="/" className="text-[#734061] hover:underline">
            Home
          </Link>
          <span className="mx-2">›</span>
          <span className="text-gray-500">Search Results</span>
        </div>
        
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          {getSearchTitle()}
        </h1>
        
        {searchType === 'image' && (
          <p className="text-gray-600 mb-8">
            Showing recipes that visually match your uploaded image
          </p>
        )}
        
        {isLoading ? (
          // Loading skeleton
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[...Array(6)].map((_, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md overflow-hidden animate-pulse">
                <div className="h-48 bg-gray-200"></div>
                <div className="p-4">
                  <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-5/6 mb-4"></div>
                  <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          // Actual results
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {searchResults.map((recipe) => (
              <div key={recipe.id} className="bg-white rounded-lg shadow-md overflow-hidden transition-transform hover:scale-[1.02] hover:shadow-lg">
                <Link href={`/recipes/${recipe.id}`}>
                  <div className="relative h-48 w-full">
                    <Image
                      src={recipe.image}
                      alt={recipe.title}
                      fill
                      className="object-cover"
                    />
                  </div>
                </Link>
                
                <div className="p-4">
                  <Link href={`/recipes/${recipe.id}`}>
                    <h2 className="text-xl font-bold mb-2 text-gray-800 hover:text-[#734061]">
                      {recipe.title}
                    </h2>
                  </Link>
                  
                  <div className="flex items-center gap-2 mb-2">
                    <StarRating rating={recipe.rating} />
                    <span className="text-gray-500 text-sm">
                      {recipe.reviews} reviews
                    </span>
                  </div>
                  
                  <div className="flex items-center text-gray-500 text-sm mb-4">
                    <span>Prep: {recipe.prepTime}</span>
                    <span className="mx-2">•</span>
                    <span>Cook: {recipe.cookTime}</span>
                  </div>
                  
                  <p className="text-gray-600 line-clamp-2">
                    {recipe.description}
                  </p>
                  
                  <Link 
                    href={`/recipes/${recipe.id}`}
                    className="mt-4 inline-block text-[#734061] font-medium hover:underline"
                  >
                    View Recipe →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 