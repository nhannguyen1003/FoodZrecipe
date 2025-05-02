'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useState } from 'react';

interface CategoryCardProps {
  name: string;
  image: string;
  slug: string;
}

export default function CategoryCard({ name, image, slug }: CategoryCardProps) {
  const [imageError, setImageError] = useState(false);
  
  const handleImageError = () => {
    console.error(`Failed to load image for category: ${name}, path: ${image}`);
    setImageError(true);
  };

  // Simplified image handling - using local static files
  const imageUrl = `/categories/${image}`;

  // Use a client-side route that will use our proxy API
  return (
    <Link href={`/category/${slug}`} className="flex flex-col items-center group">
      <div className="w-20 h-20 rounded-full overflow-hidden bg-gray-100 relative mb-2">
        {!imageError ? (
          <Image
            src={imageUrl}
            alt={name}
            width={80}
            height={80}
            className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-300"
            onError={handleImageError}
            unoptimized={true} // Skip Next.js image optimization for these images
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-amber-100 text-amber-800 font-bold text-lg">
            {name.charAt(0)}
          </div>
        )}
      </div>
      <span className="text-center text-gray-700 font-medium text-sm group-hover:text-amber-500 transition-colors">
        {name}
      </span>
    </Link>
  );
} 