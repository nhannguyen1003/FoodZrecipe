'use client';

import CategoryCard from './CategoryCard';

// Fixed categories as specified without fallback
const FIXED_CATEGORIES = [
  { id: 1, name: 'Gluten-Free', slug: 'gluten-free' },
  { id: 2, name: 'Desserts', slug: 'desserts' },
  { id: 3, name: 'Healthy', slug: 'healthy' },
  { id: 4, name: 'Crowd-Pleasing', slug: 'crowd-pleasing' },
  { id: 5, name: 'Low-Carb', slug: 'low-carb' },
  { id: 6, name: 'Kid-Friendly', slug: 'kid-friendly' }
];

// Map category slugs to appropriate image files
const CATEGORY_IMAGE_MAP: Record<string, string> = {
  'gluten-free': 'vegetarian.jpg', // Using vegetarian as fallback for gluten-free
  'desserts': 'desserts.jpg',
  'healthy': 'healthy.jpg',
  'crowd-pleasing': 'dinner.jpg', // Using dinner as fallback for crowd-pleasing
  'low-carb': 'healthy.jpg', // Using healthy as fallback for low-carb
  'kid-friendly': 'quick-easy.jpg' // Using quick-easy as fallback for kid-friendly
};

export default function CategorySection() {
  // Get image for a category using the mapping or default
  const getCategoryImage = (slug: string): string => {
    return CATEGORY_IMAGE_MAP[slug] || 'default-category.jpg';
  };

  return (
    <section className="py-16 bg-gray-50">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">Popular Categories</h2>
        
        <div className="grid grid-cols-3 md:grid-cols-3 lg:grid-cols-6 gap-8">
          {FIXED_CATEGORIES.map((category) => (
            <CategoryCard
              key={category.slug}
              name={category.name}
              image={getCategoryImage(category.slug)}
              slug={category.slug}
            />
          ))}
        </div>
      </div>
    </section>
  );
} 