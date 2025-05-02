import Link from 'next/link';
import Image from 'next/image';
import RecipeCard from '../components/RecipeCard';
import SearchResults from '../components/SearchResults';
import dynamic from 'next/dynamic';

// Import the TopRatedRecipes component dynamically with no SSR to ensure it fetches from the client
const TopRatedRecipes = dynamic(() => import('../components/TopRatedRecipes'), { ssr: false });

// Categories
const categories = [
  { name: 'Quick and Easy', slug: 'quick-easy' },
  { name: 'Instant Pot', slug: 'instant-pot' },
  { name: 'Meal Prep', slug: 'meal-prep' },
  { name: 'Vegan', slug: 'vegan' },
  { name: 'Vegetarian', slug: 'vegetarian' },
  { name: 'Sugar-Free', slug: 'sugar-free' },
  { name: 'Pasta', slug: 'pasta' },
  { name: 'Tacos', slug: 'tacos' },
  { name: 'Bowls', slug: 'bowls' },
  { name: 'Soups', slug: 'soups' },
  { name: 'Salads', slug: 'salads' },
  { name: 'Dinner', slug: 'dinner' },
  { name: 'Kid-Friendly', slug: 'kid-friendly' },
  { name: 'Most Popular', slug: 'most-popular' },
  { name: 'All Recipes', slug: '' }
];

// All recipes (paginated)
const allRecipes = [
  {
    id: '1',
    title: 'Ridiculously Good Air Fryer Broccoli',
    image: '/images/recipes/Best-Air-Fryer-Broccoli.jpg',
    reviews: 9,
    rating: 4.7
  },
  {
    id: '2',
    title: 'My New Favorite Pizza Has a Cottage Cheese Crust',
    image: '/images/recipes/-carbonnade-a-la-flamande-short-ribs-358557.jpg',
    reviews: 25,
    rating: 4.8
  },
  {
    id: '3',
    title: 'Mixed Berry Muffins with Sugary Tops',
    image: '/images/recipes/Whipped-Feta.jpg',
    reviews: 29,
    rating: 4.5
  },
  {
    id: '4',
    title: 'Sweet Potato Soup with Roasted Cauliflower Crumbles',
    image: '/images/recipes/-candy-corn-pumpkin-blondies-51254510.jpg',
    reviews: 13,
    rating: 4.7
  }
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

export default function RecipesPage() {
  return (
    <main className="min-h-screen">
      <div className="container mx-auto px-4 py-12">
        <h1 className="text-4xl font-bold mb-8">All Recipes</h1>
        
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-6">Top Rated Recipes</h2>
          <TopRatedRecipes />
        </section>
        
        <section>
          <h2 className="text-2xl font-semibold mb-6">Latest Recipes</h2>
          <SearchResults limit={12} />
        </section>
      </div>
    </main>
  );
} 