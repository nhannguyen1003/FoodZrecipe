import { NextRequest, NextResponse } from 'next/server';

// API constants
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

export async function GET(request: NextRequest) {
  try {
    // Get query parameters
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('query') || '';
    
    // Log the request for debugging
    console.log(`Category search proxy request for: "${query}"`);
    
    // Create the search URL with the text endpoint which we've tested works
    const url = `${API_BASE_URL}${API_PREFIX}/search/text?query=${encodeURIComponent(query)}`;
    
    // Forward the request to the API
    console.log(`Forwarding to: ${url}`);
    
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store', // Disable caching to ensure fresh results
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API error ${response.status}: ${errorText}`);
      
      // Create a proper error response
      return NextResponse.json(
        { error: `Failed to search: ${errorText || response.statusText}` },
        { status: response.status }
      );
    }
    
    // Parse and return the JSON response
    try {
      const data = await response.json();
      console.log(`Found ${data.length} results for "${query}"`);
      
      // Return the data with CORS headers
      return NextResponse.json(data, {
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Access-Control-Allow-Origin': '*',
        }
      });
    } catch (parseError) {
      console.error('Error parsing API response:', parseError);
      return NextResponse.json(
        { error: 'Invalid response from backend API' },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Category search error:', error);
    return NextResponse.json(
      { error: 'Failed to search for recipes' },
      { status: 500 }
    );
  }
} 