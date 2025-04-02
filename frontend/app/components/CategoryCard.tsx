import Image from 'next/image';
import Link from 'next/link';

type CategoryCardProps = {
  name: string;
  image: string;
  slug: string;
};

export default function CategoryCard({ name, image, slug }: CategoryCardProps) {
  return (
    <Link 
      href={`/recipes/category/${slug}`}
      className="group flex flex-col items-center"
    >
      <div className="relative h-24 w-24 mb-2 rounded-full overflow-hidden group-hover:scale-105 transition-transform">
        <Image
          src={image || `https://placehold.co/200x200?text=${name}`}
          alt={name}
          fill
          className="object-cover"
        />
      </div>
      <span className="text-center font-medium text-gray-800 group-hover:text-amber-500 transition-colors">
        {name}
      </span>
    </Link>
  );
} 