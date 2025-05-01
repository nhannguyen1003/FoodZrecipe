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
      
      </div>
    </section>
  );
} 