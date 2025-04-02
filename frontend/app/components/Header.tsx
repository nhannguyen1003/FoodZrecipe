'use client';

import Link from 'next/link';
import Image from 'next/image';

export default function Header() {
  return (
    <header className="bg-white">
      {/* Top signup bar */}
      <div className="bg-[#734061] text-white py-2 text-center text-sm">
        <p className="flex items-center justify-center">
          <span className="mr-2">♥</span>
          OUR RECIPES, YOUR INBOX. 
          <Link href="/signup" className="ml-2 font-medium">
            SIGN UP
          </Link>
        </p>
      </div>

      <div className="container mx-auto py-4 px-4 bg-white">
        {/* Logo */}
        <div className="flex items-center justify-between">
          <Link href="/" className="text-4xl font-serif italic font-bold text-purple-800">
            Food<span className="text-[#95a5a6]">Z</span>Recipe
          </Link>
          
          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <Link href="/" className="text-gray-800 font-bold hover:text-purple-800 transition-colors uppercase">
              Home
            </Link>
            <Link href="/about" className="text-gray-800 font-bold hover:text-purple-800 transition-colors uppercase">
              About
            </Link>
            <Link href="/recipes" className="text-gray-800 font-bold hover:text-purple-800 transition-colors uppercase">
              Recipes
            </Link>
            <Link href="/login" className="text-gray-800 font-bold hover:text-purple-800 transition-colors uppercase">
              Login
            </Link>
            <button className="text-gray-800">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </button>
          </nav>
        </div>
      </div>
      
      {/* Tagline */}
      <div className="text-center border-t border-b border-gray-200 py-6 bg-white">
        <p className="text-xl">
          <span className="font-bold uppercase mr-2 text-[#2c3e50]">Simple recipes made for</span>
          <span className="italic text-[#734061]">real, actual, everyday life</span>
        </p>
      </div>
    </header>
  );
} 