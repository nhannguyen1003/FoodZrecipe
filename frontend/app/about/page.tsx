import Image from 'next/image';
import Link from 'next/link';

export default function AboutPage() {
  return (
    <div className="bg-white">
      
      {/* Spacer/Margin */}
      <div className="h-12"></div>
      
      {/* Main content */}
      <div className="container mx-auto px-4 pb-16">
        <div className="grid md:grid-cols-2 gap-8">
          {/* Left column - Image */}
          <div>
            <Image 
              src="/images/about/kitchen.jpg" 
              alt="Profile image"
              width={600}
              height={800}
              className="w-full object-cover"
            />
          </div>
          
          {/* Right column - Content */}
          <div>
            <h1 className="text-5xl font-serif text-[#734061] mb-6">About Us</h1>
            
            <div className="mb-6">              
              <p className="text-gray-700 mb-4">
                And FoodZ Recipe is my little corner of the internet!
              </p>
              
              <p className="text-gray-700 mb-4">
              Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum
              </p>
              
            </div>
            
          </div>
        </div>
      </div>
    </div>
  );
} 