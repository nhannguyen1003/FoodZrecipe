import Link from 'next/link';
import Image from 'next/image';
import RecipeCard from '../components/RecipeCard';

// Mock data for top rated recipes
const topRatedRecipes = [
  {
    id: '1',
    title: 'The Best Soft Chocolate Chip Cookies',
    image: '/images/recipes/Chocolate-Chip-Cookies-400x400.jpg',
    reviews: 1872,
    rating: 4.5
  },
  {
    id: '2',
    title: 'The Best Sunday Chili',
    image: '/images/recipes/Sunday-Chili-400x400.jpg',
    reviews: 115,
    rating: 4.9
  },
  {
    id: '3',
    title: 'Miracle No Knead Bread',
    image: '/images/recipes/Miracle-No-Knead-Bread-3-2-400x400.jpg',
    reviews: 578,
    rating: 4.8
  },
  {
    id: '4',
    title: 'Best Anytime Baked Chicken Meatballs',
    image: '/images/recipes/Baked-Chicken-Meatball-Feature-1-225x225.jpg',
    reviews: 737,
    rating: 4.9
  },
  {
    id: '5',
    title: 'The Best Chicken Tinga Tacos',
    image: '/images/recipes/Chicken-Tinga-Tacos-6-400x400.jpg',
    reviews: 185,
    rating: 4.9
  },
  {
    id: '6',
    title: 'The Best Detox Crockpot Lentil Soup',
    image: '/images/recipes/Crockpot-Lentil-Soup-3-Homepage-400x400.jpg',
    reviews: 373,
    rating: 4.8
  },
  {
    id: '7',
    title: 'Vegetarian Shepherd\'s Pie',
    image: '/images/recipes/vegetarian-shepherds-pie-225x225.jpg',
    reviews: 397,
    rating: 4.8
  },
  {
    id: '8',
    title: 'Fruit Pizza',
    image: '/images/recipes/Fruit-Pizza-Design-1-400x400.jpg',
    reviews: 67,
    rating: 4.8
  },
  {
    id: '9',
    title: 'Fluffiest Blueberry Pancakes',
    image: '/images/recipes/Taking-a-Bite-of-Blueberry-Pancakes-400x400.jpg',
    reviews: 356,
    rating: 4.8
  },
];

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
    <div>
      {/* Hero Section with Search */}
      <section className="bg-[#734061] py-16 text-white text-center">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-6xl font-serif mb-8">Recipes</h1>
            <p className="text-xl mb-12 max-w-3xl mx-auto">
              We've organized these recipes every way we could think of so you don't have to! Dietary
              restrictions, weeknight dinners, meal prep recipes, some of our most tried-and-true... no
              matter how you browse, we're sure you'll find just what you were looking for.
            </p>
            
            {/* Search Box */}
            <div className="relative max-w-2xl mx-auto">
              <input
                type="text"
                placeholder="Search by keyword or drop an image"
                className="w-full py-4 px-6 rounded-lg text-[#2c3e50] text-lg focus:outline-none"
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-4">
                <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Top Rated Recipes Section */}
      <section className="py-16 bg-[#F2F2F2]">
        <div className="container mx-auto px-4">
          <div className="flex flex-col items-center mb-10">
            <div className="mb-4">
              <svg width="48" height="48" viewBox="0 0 24 24" className="text-[#734061]" fill="currentColor">
                <path d="M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94.63 1.5 1.98 2.63 3.61 2.96V19H7v2h10v-2h-4v-3.1c1.63-.33 2.98-1.46 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2zM5 8V7h2v3.82C5.84 10.4 5 9.3 5 8zm14 0c0 1.3-.84 2.4-2 2.82V7h2v1z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-[#734061] uppercase">Top Rated Recipes</h2>
            <p className="text-gray-600 mt-4 text-center max-w-3xl">
              Out of all the many recipes on FoodZ Recipe, these are our shining stars - the
              recipes we come back to again and again (and again).
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {topRatedRecipes.slice(0, 9).map((recipe) => (
              <div key={recipe.id} className="mb-8">
                <Link href={`/recipes/${recipe.id}`} className="block">
                  <div className="mb-3 relative h-56 overflow-hidden rounded-md">
                    <Image 
                      src={recipe.image} 
                      alt={recipe.title} 
                      fill 
                      className="object-cover transition-transform hover:scale-105 duration-300" 
                    />
                  </div>
                  <h3 className="text-xl font-bold mb-2 text-[#2c3e50]">{recipe.title}</h3>
                </Link>
                <div className="flex items-center gap-2 mb-1">
                  <StarRating rating={recipe.rating} />
                </div>
                <div className="text-gray-500 text-sm">
                  {recipe.reviews} REVIEWS / {recipe.rating} AVERAGE
                </div>
              </div>
            ))}
          </div>

        </div>
      </section>

      {/* Categories Section */}
      <section className="py-12 bg-gray-100">
        <div className="container mx-auto px-4">
          <h2 className="text-2xl font-bold mb-8 uppercase text-[#734061]">Popular Categories</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-y-4">
            {categories.map((category) => (
              <div key={category.slug} className="flex items-center">
                <div className="w-2 h-2 bg-[#734061] rounded-full mr-3"></div>
                <Link 
                  href={`/recipes/category/${category.slug}`} 
                  className="text-gray-700 hover:text-[#734061]"
                >
                  {category.name}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* All Recipes Section */}
      <section className="py-16 bg-[#F2F2F2]">
        <div className="container mx-auto px-4">
          <div className="flex flex-col items-center mb-12">
            <div className="mb-4">
              <svg width="48" height="48" viewBox="0 0 24 24" className="text-[#734061]" fill="currentColor">
                <path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-[#734061] uppercase">All Recipes</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {allRecipes.map((recipe) => (
              <div key={recipe.id} className="mb-8">
                <Link href={`/recipes/${recipe.id}`} className="block">
                  <div className="mb-3 relative h-64 overflow-hidden rounded-md ">
                    <Image 
                      src={recipe.image} 
                      alt={recipe.title} 
                      fill 
                      className="object-cover transition-transform hover:scale-105 duration-300" 
                    />
                  </div>
                </Link>
                <div className="flex items-center gap-2 mb-1">
                  <StarRating rating={recipe.rating} />
                </div>
                <div className="text-gray-500 text-sm mb-2">
                  {recipe.reviews} REVIEWS / {recipe.rating} AVERAGE
                </div>
                <Link href={`/recipes/${recipe.id}`} className="block">
                  <h3 className="text-xl font-bold hover:text-[#734061] text-[#2c3e50]">{recipe.title}</h3>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
} 