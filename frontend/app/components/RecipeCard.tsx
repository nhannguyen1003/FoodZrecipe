import Image from 'next/image';
import Link from 'next/link';

type RecipeCardProps = {
  id: string;
  title: string;
  image: string;
  category: string;
  readTime: string;
  postedTime: string;
  author?: {
    name: string;
    avatar?: string;
  };
  saved?: boolean;
};

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
  return (
    <div className="rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-all duration-300 bg-white">
      <div className="relative">
        <Link href={`/recipes/${id}`}>
          <div className="relative h-64 w-full">
            {/* Placeholder div when image is loading */}
            <div className="absolute inset-0 bg-gray-200 animate-pulse" />
            
            {/* Actual image */}
            <Image
              src={image}
              alt={title}
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            />
          </div>
        </Link>
        
        {/* Category badge */}
        <div className="absolute top-4 left-4">
          <Link href={`/recipes/category/${category.toLowerCase()}`}>
            <span className="bg-white text-gray-800 px-3 py-1 rounded-full text-sm font-medium uppercase tracking-wide">
              {category}
            </span>
          </Link>
        </div>
        
        {/* Save button */}
        <button 
          className="absolute top-4 right-4 bg-white p-2 rounded-full shadow-md hover:bg-gray-100"
          aria-label={saved ? 'Unsave recipe' : 'Save recipe'}
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-5 w-5" 
            fill={saved ? "currentColor" : "none"} 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" 
            />
          </svg>
        </button>
      </div>
      
      <div className="p-4">
        <Link href={`/recipes/${id}`}>
          <h3 className="text-xl font-bold mb-2 text-gray-800 hover:text-amber-500 transition-colors">
            {title}
          </h3>
        </Link>
        
        <div className="flex items-center text-gray-500 text-sm">
          <span>{readTime} read</span>
          <span className="mx-2">•</span>
          <span>Posted {postedTime}</span>
        </div>
        
        {author && (
          <div className="flex items-center mt-4">
            {author.name && (
              <span className="text-gray-700 text-sm">{author.name}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 