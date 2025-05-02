'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { recipeApi, formatRecipe, RecipeResponse } from '../../utils/api';

export default function RecipeDetailPage({ params }: { params: { id: string } }) {
  const [recipe, setRecipe] = useState<RecipeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecipe = async () => {
      try {
        setLoading(true);
        const data = await recipeApi.getById(params.id);
        setRecipe(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching recipe:', err);
        setError('Failed to load recipe details. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchRecipe();
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen flex justify-center items-center">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <div className="h-6 w-32 bg-gray-200 rounded"></div>
          <div className="h-4 w-48 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !recipe) {
    return (
      <div className="min-h-screen flex justify-center items-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Recipe Not Found</h2>
          <p className="text-gray-600 mb-4">{error || 'The recipe you are looking for does not exist.'}</p>
          <Link href="/recipes" className="text-[#734061] hover:underline">
            Return to Recipes
          </Link>
        </div>
      </div>
    );
  }

  const formattedRecipe = formatRecipe(recipe);
  
  // Process instructions: First get as array (either directly or by splitting)
  let rawInstructions: string[] = [];
  if (Array.isArray(recipe.instructions)) {
    rawInstructions = recipe.instructions;
  } else if (typeof recipe.instructions === 'string') {
    rawInstructions = recipe.instructions.split('\n').filter(line => line.trim().length > 0);
  }
  
  // Then split each instruction by sentences and flatten
  const instructionSteps: string[] = [];
  rawInstructions.forEach(instruction => {
    // Split by periods followed by space or end of string, but keep the period
    const sentences = instruction.match(/[^.!?]+[.!?]+(?:\s|$)/g) || [];
    
    // Clean up each sentence and add to steps
    sentences.forEach(sentence => {
      const trimmed = sentence.trim();
      if (trimmed.length > 0) {
        instructionSteps.push(trimmed);
      }
    });
    
    // If no sentences were extracted but there's still content, add the whole thing
    if (sentences.length === 0 && instruction.trim().length > 0) {
      instructionSteps.push(instruction.trim());
    }
  });

  // Calculate total time
  const totalTime = (recipe.prep_time || 0) + (recipe.cook_time || 0);

  return (
    <div className="bg-white min-h-screen">
      {/* Hero Section */}
      <div className="relative h-96 md:h-[500px] bg-gray-100 overflow-hidden">
        <Image
          src={formattedRecipe.image}
          alt={recipe.title}
          fill
          className="object-contain md:object-cover object-center"
          unoptimized={false}
          priority
          quality={90}
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 85vw, 75vw"
        />
        <div className="absolute inset-0 bg-black bg-opacity-30 flex items-end">
          <div className="container mx-auto px-4 pb-12">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4">
              {recipe.title}
            </h1>
            <div className="flex items-center text-white space-x-4">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>
                  {totalTime > 0 ? `${totalTime} mins` : 'Quick Recipe'}
                </span>
              </div>
              {recipe.servings && (
                <div className="flex items-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  <span>{recipe.servings} {recipe.servings === 1 ? 'serving' : 'servings'}</span>
                </div>
              )}
              {recipe.categories && recipe.categories.length > 0 && (
                <div className="flex items-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                  <span>{recipe.categories[0]}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Left Column - Ingredients */}
          <div className="lg:col-span-1">
            <div className="bg-amber-50 p-6 rounded-lg shadow-sm">
              <h2 className="text-2xl font-bold text-[#734061] mb-6">Ingredients</h2>
              <ul className="space-y-3">
                {recipe.ingredients.map((ingredient, index) => (
                  <li key={index} className="flex items-start">
                    <div className="h-6 w-6 rounded-full bg-[#734061] flex-shrink-0 flex items-center justify-center text-white text-sm mr-3 mt-0.5">
                      ✓
                    </div>
                    <span className="text-gray-700">{ingredient}</span>
                  </li>
                ))}
              </ul>

              {recipe.description && (
                <div className="mt-8">
                  <h3 className="text-xl font-bold text-[#734061] mb-3">Description</h3>
                  <p className="text-gray-700">{recipe.description}</p>
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Instructions */}
          <div className="lg:col-span-2">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
              <h2 className="text-2xl font-bold text-[#734061] mb-6">Instructions</h2>
              <ul className="space-y-5 list-disc pl-5">
                {instructionSteps.map((step, index) => (
                  <li key={index} className="text-gray-700 pl-2">
                    {step}
                  </li>
                ))}
              </ul>

              {/* Recipe Meta Information */}
              <div className="mt-12 pt-8 border-t border-gray-200">
                <div className="flex flex-wrap gap-6">
                  {recipe.prep_time && (
                    <div>
                      <h4 className="font-semibold text-gray-800">Prep Time</h4>
                      <p className="text-gray-600">{recipe.prep_time} minutes</p>
                    </div>
                  )}
                  {recipe.cook_time && (
                    <div>
                      <h4 className="font-semibold text-gray-800">Cook Time</h4>
                      <p className="text-gray-600">{recipe.cook_time} minutes</p>
                    </div>
                  )}
                  {totalTime > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-800">Total Time</h4>
                      <p className="text-gray-600">{totalTime} minutes</p>
                    </div>
                  )}
                  {recipe.servings && (
                    <div>
                      <h4 className="font-semibold text-gray-800">Servings</h4>
                      <p className="text-gray-600">{recipe.servings}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Related Recipes Section (Placeholder) */}
      <div className="bg-gray-50 py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-[#734061] mb-10">You Might Also Like</h2>
          <div className="text-center">
            <p className="text-gray-500">Explore more delicious recipes by browsing our categories</p>
            <Link 
              href="/recipes" 
              className="inline-block mt-6 px-6 py-3 bg-[#734061] text-white font-medium rounded-lg hover:bg-[#5c3249] transition duration-300"
            >
              Browse All Recipes
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
} 