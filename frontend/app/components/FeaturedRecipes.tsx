'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { categoryApi, Category, getImageUrl } from '../utils/api';

// Define featured categories to show (these are fixed)
const FEATURED_CATEGORIES = ['healthy', 'dinner', 'vegetarian', 'desserts'];

export default function FeaturedRecipes() {
  const [featuredItems, setFeaturedItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFeaturedCategories = async () => {
      try {
        setLoading(true);
        console.log('Fetching featured categories...');
        const allCategories = await categoryApi.getAll();
        console.log('Received categories for featured section:', allCategories);
        
        // Filter to get only our featured categories
        const featured = allCategories
          .filter(cat => FEATURED_CATEGORIES.includes(cat.slug))
          .map(cat => ({
            id: cat.id,
            name: cat.name,
            slug: cat.slug,
            recipe_count: cat.recipe_count || 0,
            image: `${cat.slug}.jpg` // Use slug-based image naming pattern
          }));
        
        console.log('Filtered featured categories:', featured);
        setFeaturedItems(featured);
        setError(null);
      } catch (err) {
        console.error('Error fetching featured categories:', err);
        setError('Failed to load featured categories: ' + (err instanceof Error ? err.message : String(err)));
      } finally {
        setLoading(false);
      }
    };

    fetchFeaturedCategories();
  }, []);

  // Handle loading and error states
  if (loading) {
    return (
      <section className="py-12 bg-white">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">Featured Categories</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-gray-100 p-4 rounded-lg animate-pulse flex flex-col items-center justify-center" style={{ height: '250px' }}>
                <div className="w-full h-32 bg-gray-200 rounded mb-4"></div>
                <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="py-12 bg-white">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">Featured Categories</h2>
          <div className="text-center py-8">
            <p className="text-red-500">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-4 px-4 py-2 bg-amber-500 text-white rounded hover:bg-amber-600"
            >
              Try Again
            </button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="py-12 bg-white">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">Featured Categories</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {featuredItems.length > 0 ? (
            featuredItems.map((item) => (
              <Link 
                key={item.slug} 
                href={`/recipes/category/${item.slug}`}
                className="bg-white rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-shadow duration-300"
              >
                <div className="h-48 overflow-hidden relative">
                  <Image 
                    src={getImageUrl(item.image)} 
                    alt={item.name}
                    fill
                    className="object-cover"
                    onError={(e) => {
                      e.currentTarget.src = getImageUrl('default-category.jpg');
                    }}
                  />
                </div>
                <div className="p-4">
                  <h3 className="text-xl font-bold text-gray-800 mb-2">{item.name}</h3>
                  <p className="text-gray-600">{item.recipe_count} Recipes</p>
                </div>
              </Link>
            ))
          ) : (
            <div className="col-span-4 text-center py-8">
              <p className="text-gray-500">No featured categories found</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
} 