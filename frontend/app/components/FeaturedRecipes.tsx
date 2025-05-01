import Image from 'next/image';
import Link from 'next/link';

const featuredItems = [
  {
    id: 'healthy',
    title: 'HEALTHY',
    image: '/images/featured/Lemon-Rosemary-Chicken-Soup.jpg',
    href: '/recipes/category/healthy'
  },
  {
    id: 'bowls',
    title: 'BOWLS',
    image: '/images/featured/Crockpot-Chicken-Bowls.jpg',
    href: '/recipes/category/bowls'
  },
  {
    id: 'most-popular',
    title: 'MOST POPULAR',
    image: '/images/featured/Crispy-Rice-Salad-4.jpg',
    href: '/recipes/most-popular'
  },
  {
    id: 'vegetarian',
    title: 'VEGETARIAN',
    image: '/images/featured/Cauliflower-Black-Bean-Tostadas-4.jpg',
    href: '/recipes/category/vegetarian'
  },
];

export default function FeaturedRecipes() {
  return (
    <section className="py-10 bg-white">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {featuredItems.map((item) => (
            <div key={item.id} className="relative group">
              <div className="relative h-96 md:h-80 overflow-hidden">
                {/* Placeholder for image loading */}
                <div className="absolute inset-0 bg-gray-200 animate-pulse" />
                
                <Image
                  src={item.image}
                  alt={item.title}
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                  sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 25vw"
                />
                
                {/* Overlay */}
                <div className="absolute inset-0 bg-black opacity-30 group-hover:opacity-20 transition-opacity" />
              </div>
              
              {/* Button at the bottom */}
              <div className="absolute bottom-10 w-full flex justify-center">
                <Link
                  href={item.href}
                  className="bg-amber-500 text-white px-8 py-3 font-bold text-center tracking-wider hover:bg-amber-600 transition-colors"
                >
                  {item.title}
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
} 