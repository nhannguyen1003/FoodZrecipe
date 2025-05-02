'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

export default function SearchBar() {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isImageSearch, setIsImageSearch] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Handle client-side hydration
  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleTextSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      // Set loading state
      setIsLoading(true);
      
      // Redirect to search page with query parameter
      router.push(`/search-results?query=${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleImage(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      handleImage(file);
    }
  };

  const handleImage = (file: File) => {
    // Set loading state
    setIsLoading(true);
    
    const reader = new FileReader();
    reader.onload = () => {
      // Show preview of the image
      setPreviewImage(reader.result as string);
      
      // Store the file in sessionStorage to be used by the search-results page
      if (typeof window !== 'undefined') {
        try {
          console.log('Storing image data in session storage for search');
          sessionStorage.setItem('searchImage', reader.result as string);
        } catch (error) {
          console.error('Failed to store image in session storage:', error);
        }
      }
      
      // Navigate to results page after a short delay to show preview
      setTimeout(() => {
        router.push(`/search-results?type=image`);
      }, 1000);
    };
    reader.readAsDataURL(file);
  };

  const toggleSearchType = () => {
    setIsImageSearch(!isImageSearch);
    setPreviewImage(null);
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  // Return a simple placeholder during server-side rendering
  if (!isMounted) {
    return (
      <div className="w-full max-w-3xl mx-auto">
        <div className="relative">
          <input
            type="text"
            placeholder="Search for recipes, ingredients, or keywords..."
            className="w-full py-4 px-6 pr-12 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#734061] shadow-sm bg-white text-gray-800"
            disabled
          />
          <div className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-500">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-3xl mx-auto">
      {isImageSearch ? (
        <div
          className={`relative p-6 border-2 border-dashed rounded-lg transition-colors ${
            isDragging ? 'border-[#734061] bg-purple-50' : 'border-gray-300 bg-white'
          } ${isLoading ? 'opacity-70' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={triggerFileInput}
        >
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept="image/*"
            onChange={handleImageUpload}
            disabled={isLoading}
          />
          
          {previewImage ? (
            <div className="flex flex-col items-center">
              <div className="relative w-48 h-48 mb-4">
                <Image
                  src={previewImage}
                  alt="Preview"
                  fill
                  className="object-cover rounded-md"
                />
              </div>
              <p className="text-gray-600">Searching for similar recipes...</p>
              
              {isLoading && (
                <div className="mt-4">
                  <div className="w-8 h-8 border-4 border-t-[#734061] border-gray-200 rounded-full animate-spin mx-auto"></div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center cursor-pointer">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
                aria-hidden="true"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4h-8m-12 0h8m-8 0v-8m32 8v-8M12 8v8m0 0v8m32-16v8"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
              <p className="mt-2 text-sm text-gray-600">
                Drag and drop an image here, or click to select a file
              </p>
              <p className="mt-1 text-xs text-gray-500">
                PNG, JPG, GIF up to 10MB
              </p>
            </div>
          )}
        </div>
      ) : (
        <form onSubmit={handleTextSearch} className="relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search for recipes, ingredients, or keywords..."
            className={`w-full py-4 px-6 pr-12 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#734061] shadow-sm bg-white text-gray-800 ${
              isLoading ? 'opacity-70' : ''
            }`}
            disabled={isLoading}
          />
          <button
            type="submit"
            className={`absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-[#734061] ${
              isLoading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            disabled={isLoading}
          >
            {isLoading ? (
              <div className="w-6 h-6 border-2 border-t-[#734061] border-gray-200 rounded-full animate-spin"></div>
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            )}
          </button>
        </form>
      )}

      <div className="mt-4 text-center">
        <button
          onClick={toggleSearchType}
          className="text-white text-sm font-medium hover:underline"
          disabled={isLoading}
        >
          {isImageSearch ? "Switch to text search" : "Search with an image instead"}
        </button>
      </div>
    </div>
  );
} 