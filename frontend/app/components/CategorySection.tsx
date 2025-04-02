import CategoryCard from './CategoryCard';

const categories = [
  { name: 'Quick and Easy', slug: 'quick-easy', image: '/images/categories/Buffalo-Chicken-Burgers-3-225x225.jpg' },
  { name: 'Dinner', slug: 'dinner', image: '/images/categories/Family-Style-Pitas-2.jpg' },
  { name: 'Vegetarian', slug: 'vegetarian', image: '/images/categories/Cauliflower-Black-Bean-Tostadas-4.jpg' },
  { name: 'Healthy', slug: 'healthy', image: '/images/categories/Lemon-Rosemary-Chicken-Soup-225x225.jpg' },
  { name: 'Instant Pot', slug: 'instant-pot', image: '/images/categories/Tortilla-Soup.jpg' },
  { name: 'Chicken', slug: 'chicken', image: '/images/categories/Chicken-Tinga-Tacos-5.jpg' },
  { name: 'Meal Prep', slug: 'meal-prep', image: '/images/categories/Meal-Prep-Pasta-with-Cauliflower.jpg' },
  { name: 'Soups', slug: 'soups', image: '/images/categories/Tortilla-Soup.jpg' },
  { name: 'Salads', slug: 'salads', image: '/images/categories/Kale-Apple-Salad-6-2.jpg' },
];

export default function CategorySection() {
  return (
    <section className="py-16 bg-gray-50">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-9 gap-8">
          {categories.map((category) => (
            <CategoryCard
              key={category.slug}
              name={category.name}
              image={category.image}
              slug={category.slug}
            />
          ))}
        </div>
        
        <div className="mt-12 flex justify-center">
          <div className="relative">
            <input
              type="text"
              placeholder="Search our recipes"
              className="w-full md:w-[500px] p-3 pr-10 border border-gray-300 rounded-l shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
            <button className="absolute right-0 top-0 h-full px-3 flex items-center text-gray-500">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </button>
          </div>
          
          <span className="mx-4 flex items-center text-gray-600">or</span>
          
          <a
            href="/recipes"
            className="bg-purple-700 text-white px-6 py-3 rounded font-medium hover:bg-purple-800 transition-colors"
          >
            VIEW ALL RECIPES
          </a>
        </div>
      </div>
    </section>
  );
} 