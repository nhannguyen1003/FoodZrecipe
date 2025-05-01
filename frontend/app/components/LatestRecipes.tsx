import RecipeCard from './RecipeCard';
import Link from 'next/link';

// Mock data for recipes
const recipes = [
  {
    id: '1',
    title: 'Ranch Chicken Pasta with Fresh Tomatoes',
    image: '/images/recipes/-candy-corn-pumpkin-blondies-51254510.jpg',
    category: 'Dinner',
    readTime: '5 minutes',
    postedTime: '50 mins ago',
    author: {
      name: 'Rachel Greene'
    }
  },
  {
    id: '2',
    title: 'Super Simple Parmesan Arugula Salad Recipe',
    image: '/images/recipes/-chickpea-barley-and-feta-salad-51239040.jpg',
    category: 'Salad',
    readTime: '10 minutes',
    postedTime: '2 days ago',
    author: {
      name: 'Joe Doppler'
    }
  },
  {
    id: '3',
    title: 'Black Bean Corn Avocado Salad with Rice',
    image: '/images/recipes/-chickpea-pancakes-with-leeks-squash-and-yogurt-51260630.jpg',
    category: 'Vegetarian',
    readTime: '10 minutes',
    postedTime: '3 days ago',
    author: {
      name: 'Joe Doppler'
    }
  },
  {
    id: '4',
    title: 'Instant Pot Split Pea Soup (with ham OR vegetarian)',
    image: '/images/recipes/-bloody-mary-tomato-toast-with-celery-and-horseradish-56389813.jpg',
    category: 'Soup',
    readTime: '10 minutes',
    postedTime: '1 week ago',
    author: {
      name: 'Joe Doppler'
    },
    saved: true
  },
  {
    id: '5',
    title: 'A Coffee Date for Spring',
    image: '/images/recipes/-burnt-carrots-and-parsnips-56390131.jpg',
    category: 'Blog',
    readTime: '15 minutes',
    postedTime: 'March 21, 2025',
    author: {
      name: 'Ashley Parker'
    }
  },
  {
    id: '6',
    title: 'Ridiculously Good Air Fryer Broccoli',
    image: '/images/recipes/Best-Air-Fryer-Broccoli.jpg',
    category: 'Vegetarian',
    readTime: '8 minutes',
    postedTime: 'March 13, 2025',
    author: {
      name: 'Chris Johnson'
    }
  },
];

export default function LatestRecipes() {
  return (
    <section className="py-16 bg-[#F2F2F2]">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold text-gray-800">Latest Recipes</h2>
          <Link
            href="/recipes"
            className="text-amber-500 hover:text-amber-600 font-medium flex items-center"
          >
            View more →
          </Link>
        </div>
        
        {/* Recipe grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {recipes.map((recipe) => (
            <RecipeCard
              key={recipe.id}
              id={recipe.id}
              title={recipe.title}
              image={recipe.image}
              category={recipe.category}
              readTime={recipe.readTime}
              postedTime={recipe.postedTime}
              author={recipe.author}
              saved={recipe.saved}
            />
          ))}
        </div>
      </div>
    </section>
  );
} 