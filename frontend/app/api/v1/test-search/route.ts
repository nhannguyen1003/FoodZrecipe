import { NextRequest, NextResponse } from 'next/server';

// This is a test endpoint that returns hard-coded recipes
// Useful for debugging when the backend API is not working correctly
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const query = searchParams.get('query') || '';
  
  console.log(`Test search request for: "${query}"`);
  
  // Generate 3 mock recipes for the category
  const mockRecipes = Array.from({ length: 3 }, (_, i) => ({
    id: i + 1,
    title: `Test ${query} Recipe ${i + 1}`,
    description: `This is a test recipe for ${query}`,
    image_name: 'placeholder-recipe',
    categories: [query],
    instructions: ['Step 1', 'Step 2', 'Step 3'],
    ingredients: ['Ingredient 1', 'Ingredient 2', 'Ingredient 3'],
    created_at: new Date().toISOString(),
    prep_time: 15,
    cook_time: 30,
    servings: 4,
    user_id: 1,
    user: {
      username: 'Test User'
    }
  }));
  
  return NextResponse.json(mockRecipes);
} 