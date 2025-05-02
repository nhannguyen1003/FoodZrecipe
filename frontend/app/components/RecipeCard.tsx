'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';

interface RecipeCardProps {
  id: string;
  title: string;
  image: string;
  category: string;
  readTime: string;
  postedTime: string;
  author: {
    name: string;
  };
  saved?: boolean;
}

export default function RecipeCard({
  id,
  title,
  image,
  category,
  readTime,
  postedTime,
  author,
  saved = false,
}: RecipeCardProps) {
  const [isSaved, setIsSaved] = useState(saved);
  const [imageError, setImageError] = useState(false);
  
  // Format the category display name (e.g., convert "gluten-free" to "Gluten Free")
  const formattedCategory = category
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
  
  // Log the image path when component mounts to help with debugging
  useEffect(() => {
    console.log(`RecipeCard: Loading image for "${title}" (ID: ${id}): ${image}`);
  }, [title, image, id]);
  
  const handleImageError = () => {
    console.error(`Failed to load image for recipe: ${title}, URL: ${image}`);
    setImageError(true);
  };
  
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Recipe image */}
      <Link href={`/recipes/${id}`} className="block relative h-48 overflow-hidden">
        {imageError ? (
          <div className="w-full h-full flex items-center justify-center bg-gray-100 text-gray-400">
            <div className="text-center px-4">
              <p className="font-medium">{title}</p>
              <p className="text-sm mt-2">{formattedCategory}</p>
            </div>
          </div>
        ) : (
          <Image
            src={image}
            alt={title}
            fill
            className="object-cover hover:scale-105 transition-transform duration-300"
            onError={handleImageError}
            unoptimized={false} // Enable Next.js image optimization
            referrerPolicy="no-referrer" // Help with CORS issues
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            priority={false} // Don't prioritize loading
            quality={85} // Higher quality for recipe card images
          />
        )}
      </Link>
      
      {/* Recipe details */}
      <div className="p-4">
        <div className="flex justify-between items-start">
          <div>
            <Link href={`/category/${category.toLowerCase()}`} className="text-xs font-semibold text-amber-500 uppercase tracking-wider hover:text-amber-600">
              {formattedCategory}
            </Link>
            <Link href={`/recipes/${id}`} className="block mt-2 mb-3">
              <h3 className="text-lg font-bold text-gray-800 line-clamp-2 hover:text-amber-500 transition-colors">
                {title}
              </h3>
            </Link>
          </div>
          
          <button 
            onClick={() => setIsSaved(!isSaved)}
            className="text-gray-400 hover:text-red-500 transition-colors"
            aria-label={isSaved ? "Unsave recipe" : "Save recipe"}
          >
            {/* Simple SVG heart icon */}
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="h-6 w-6" 
              fill={isSaved ? "currentColor" : "none"} 
              viewBox="0 0 24 24" 
              stroke="currentColor"
              strokeWidth={isSaved ? "0" : "2"}
              style={{ color: isSaved ? "#ef4444" : "#9ca3af" }}
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" 
              />
            </svg>
          </button>
        </div>
        
        <div className="flex items-center text-gray-500 text-xs mt-3">
          <span className="mr-3">{readTime}</span>
          <span className="mr-3">•</span>
          <span>{postedTime}</span>
        </div>
        
        <div className="mt-4 flex items-center text-gray-700 text-sm">
          <span className="inline-block h-6 w-6 rounded-full bg-gray-200 flex items-center justify-center mr-2">
            {author.name.charAt(0)}
          </span>
          <span>by {author.name}</span>
        </div>
      </div>
    </div>
  );
} 