// API constants and utility functions
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1'; // Add API prefix from backend configuration

// Add debugging to check environment variables
console.log('API Config:', { 
  API_BASE_URL,
  API_PREFIX,
  NODE_ENV: process.env.NODE_ENV
});

// Types
export interface Author {
  name: string;
}

export interface RecipeResponse {
  id: number;
  title: string;
  description?: string;
  image_name?: string;
  image_url?: string;
  categories: string[];
  prep_time?: number;
  cook_time?: number;
  servings?: number;
  ingredients: string[];
  instructions: string | string[];
  created_at: string;
  updated_at: string;
  user_id: number;
  user?: {
    email: string;
    username?: string;
  };
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description?: string;
  recipe_count: number;
}

// Generate image URL with robust handling
export const getImageUrl = (imagePath: string | undefined): string => {
  // For debugging
  console.log('getImageUrl input:', imagePath);
  
  // Default image if no path provided
  if (!imagePath) {
    console.log('No image path provided, using default placeholder');
    return `/placeholders/placeholder-recipe.jpg`;
  }
  
  // If it's already a full URL, just return it
  if (imagePath.startsWith('http')) {
    console.log('Image path is already a full URL');
    return imagePath;
  }
  
  // If it's an image filename from our database, use the food-images path
  if (imagePath.includes('.jpg') || imagePath.includes('.png') || imagePath.includes('.jpeg')) {
    // Remove any leading slashes to avoid double slashes in the URL
    const cleanedPath = imagePath.startsWith('/') ? imagePath.substring(1) : imagePath;
    const foodImageUrl = `${API_BASE_URL}/food-images/${cleanedPath}`;
    console.log('Using food image URL:', foodImageUrl);
    return foodImageUrl;
  }
  
  // Otherwise just return the path directly
  console.log('Using path directly:', imagePath);
  return imagePath;
};

// Special function for recipe image handling based on API response
export const getRecipeImageUrl = (recipe: RecipeResponse): string => {
  // Use image_name from API if available (the correct way)
  if (recipe.image_name) {
    // Make sure image_name has a file extension (.jpg is most common)
    let imageName = recipe.image_name;
    
    // If imageName doesn't have an extension, add .jpg
    if (!imageName.match(/\.(jpg|jpeg|png|gif)$/i)) {
      imageName = `${imageName}.jpg`;
    }
    
    // Remove any leading slashes to avoid double slashes in the URL
    const cleanedPath = imageName.startsWith('/') ? imageName.substring(1) : imageName;
    
    // The image URL should point directly to the static file server
    const imageUrl = `${API_BASE_URL}/food-images/${cleanedPath}`;
    
    console.log(`Using image_name for "${recipe.title}" (ID: ${recipe.id}): ${imageUrl}`);
    return imageUrl;
  }
  
  // Use image_url if available
  if (recipe.image_url) {
    const imageUrl = getImageUrl(recipe.image_url);
    console.log(`Using image_url for "${recipe.title}" (ID: ${recipe.id}): ${imageUrl}`);
    return imageUrl;
  }
  
  // If no image information is available, return empty string
  console.log(`No image available for "${recipe.title}" (ID: ${recipe.id})`);
  return "";
};

// Function to format the recipe for the UI from API response
export const formatRecipe = (recipe: RecipeResponse) => {
  // Handle instructions that could be either string or array
  let formattedInstructions = '';
  if (Array.isArray(recipe.instructions)) {
    formattedInstructions = recipe.instructions.join('\n\n');
  } else {
    formattedInstructions = recipe.instructions || '';
  }

  const imageUrl = getRecipeImageUrl(recipe);
  console.log(`Formatted recipe ${recipe.title} with image: ${imageUrl}`);

  return {
    id: recipe.id.toString(),
    title: recipe.title,
    image: imageUrl,
    category: recipe.categories?.[0] || 'Uncategorized',
    readTime: recipe.prep_time ? `${recipe.prep_time} min prep` : '5 minutes',
    postedTime: formatDate(recipe.created_at),
    author: {
      name: recipe.user?.username || 'Anonymous'
    },
    instructions: formattedInstructions
  };
};

// Helper to format date
const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
    if (diffHours === 0) {
      const diffMinutes = Math.floor(diffTime / (1000 * 60));
      return `${diffMinutes} min${diffMinutes !== 1 ? 's' : ''} ago`;
    }
    return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  } else if (diffDays < 7) {
    return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  } else {
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  }
};

// API fetch function with error handling
export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${API_PREFIX}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  
  console.log(`DEBUG: Fetching from: ${url}`);
  
  try {
    // Add timeout to prevent hanging requests
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 seconds timeout
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      // Add credentials if needed for cookies
      credentials: 'include',
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    console.log(`DEBUG: Response status: ${response.status} for ${url}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.log(`DEBUG: Error response body: "${errorText}"`);
      
      let errorData;
      try {
        errorData = JSON.parse(errorText);
        console.log('DEBUG: Parsed error JSON:', errorData);
      } catch (e) {
        console.log('DEBUG: Could not parse error as JSON, using as plain text');
        errorData = { detail: errorText };
      }
      
      // Log additional details for 500 errors
      if (response.status === 500) {
        console.error(`DEBUG: Server error (500) for ${url} - This is likely a backend issue`);
        
        // Try to check if the API is available at all
        try {
          const healthCheck = await fetch(`${API_BASE_URL}${API_PREFIX}/health/`);
          const isApiUp = healthCheck.ok;
          console.log(`DEBUG: API health check result: ${isApiUp ? 'UP' : 'DOWN'}`);
        } catch (healthError) {
          console.error('DEBUG: API health check failed:', healthError);
        }
      }
      
      console.error(`API error ${response.status} for ${url}:`, errorData);
      
      // Create more detailed error messages
      let errorMessage = '';
      if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        // Handle FastAPI validation error format which is an array of objects
        errorMessage = errorData.detail.map((err: any) => 
          `${err.loc?.join('.')} - ${err.msg}`
        ).join('; ');
      } else {
        errorMessage = `API error: ${response.status}`;
      }
      
      throw new Error(errorMessage);
    }
    
    const result = await response.json();
    console.log(`API success for ${url}:`, result);
    return result;
  } catch (error: unknown) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.error(`Request timeout for ${url}`);
      throw new Error(`Request timed out: ${url}`);
    }
    console.error(`Error fetching ${url}:`, error);
    
    // Ensure error is properly formatted
    if (error instanceof Error) {
      throw error; // Already well-formatted
    } else if (typeof error === 'string') {
      throw new Error(error);
    } else {
      throw new Error(`Unknown error occurred: ${JSON.stringify(error)}`);
    }
  }
}

// Recipe API functions
export const recipeApi = {
  // Get latest recipes
  getLatest: async (limit = 6): Promise<RecipeResponse[]> => {
    // Use proper endpoint with trailing slash
    return fetchApi<RecipeResponse[]>(`/recipes/?skip=0&limit=${limit}`);
  },
  
  // Get recipes by category
  getByCategory: async (category: string, limit = 10): Promise<RecipeResponse[]> => {
    try {
      // Log detailed info about the category parameter
      console.log('DEBUG: getByCategory called with:', {
        category,
        type: typeof category,
        limit
      });
      
      // First, try to directly get recipes by category name/slug (original approach)
      console.log('DEBUG: Trying direct API call for category name/slug');
      try {
        const directResult = await fetchApi<RecipeResponse[]>(`/recipes/?category=${encodeURIComponent(category)}&limit=${limit}`);
        console.log('DEBUG: Direct category API call succeeded');
        return directResult;
      } catch (directError) {
        console.error('DEBUG: Direct category API call failed:', directError);
        // Continue to the next approach
      }
      
      // Second, try to find the category ID and then get recipes
      try {
        console.log('DEBUG: Trying to get all categories');
        const categories = await categoryApi.getAll();
        console.log('DEBUG: Got categories:', categories);
        
        const categoryObj = categories.find(cat => {
          // Try multiple matching approaches
          const matchBySlug = cat.slug?.toLowerCase() === category.toLowerCase();
          const matchByName = cat.name?.toLowerCase() === category.toLowerCase();
          
          console.log('DEBUG: Category match check:', {
            categoryId: cat.id,
            categoryName: cat.name,
            categorySlug: cat.slug,
            matchBySlug,
            matchByName
          });
          
          return matchBySlug || matchByName;
        });
        
        if (!categoryObj) {
          console.error(`DEBUG: Category not found: ${category}`);
          throw new Error(`Category not found: ${category}`);
        }
        
        // Then we fetch recipes by category ID
        console.log(`DEBUG: Fetching recipes for category ID: ${categoryObj.id}`);
        return fetchApi<RecipeResponse[]>(`/categories/categories/${categoryObj.id}/recipes?limit=${limit}`);
      } catch (categoryApiError) {
        console.error('DEBUG: Category ID approach failed:', categoryApiError);
        throw categoryApiError;
      }
    } catch (error) {
      console.error('DEBUG: Final error in getByCategory:', error);
      throw error;
    }
  },
  
  // Get recipe by ID
  getById: async (id: string): Promise<RecipeResponse> => {
    return fetchApi<RecipeResponse>(`/recipes/${id}/`);
  },
  
  // Search recipes
  search: async (query: string, categories?: string[]): Promise<RecipeResponse[]> => {
    try {
      // Log the search request details for debugging
      console.log('Searching recipes with query:', query, 'and categories:', categories);
      
      let url = `/recipes/search/?query=${encodeURIComponent(query)}`;
      if (categories && categories.length > 0) {
        categories.forEach(cat => {
          url += `&categories=${encodeURIComponent(cat)}`;
        });
      }
      
      // Add a 6-second timeout specifically for search requests
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);
      
      try {
        const result = await fetchApi<RecipeResponse[]>(url);
        clearTimeout(timeoutId);
        return result;
      } catch (innerError) {
        clearTimeout(timeoutId);
        console.error('Search endpoint failed:', innerError);
        throw innerError; // Don't try fallback, propagate the error
      }
    } catch (error) {
      console.error('Recipe search failed:', error);
      
      // Add better error formatting
      if (error instanceof Error) {
        throw error;
      } else {
        throw new Error(`Search failed: ${JSON.stringify(error)}`);
      }
    }
  },
  
  // Image search function
  searchByImage: async (imageFile: File): Promise<RecipeResponse[]> => {
    try {
      console.log('Searching recipes by image upload');
      
      // Create FormData for multipart/form-data upload
      const formData = new FormData();
      formData.append('image', imageFile);
      
      // Upload the image to the backend search endpoint
      const url = `/search/image`;
      
      // Log the request for debugging
      console.log(`Image search API URL: ${url}`);
      console.log(`Image file: ${imageFile.name}, size: ${imageFile.size}, type: ${imageFile.type}`);
      
      // Set up custom options for the fetch call
      const options: RequestInit = {
        method: 'POST',
        body: formData,
        // No need to set Content-Type header - browser sets it with boundary for FormData
        // Add credentials if needed for cookies
        credentials: 'include',
      };
      
      // Use a longer timeout for image uploads (15 seconds)
      const controller = new AbortController();
      const signal = controller.signal;
      options.signal = signal;
      const timeoutId = setTimeout(() => controller.abort(), 15000);
      
      try {
        const result = await fetchApi<RecipeResponse[]>(url, options);
        clearTimeout(timeoutId);
        return result;
      } catch (innerError) {
        clearTimeout(timeoutId);
        console.error('Image search endpoint failed:', innerError);
        throw innerError;
      }
    } catch (error) {
      console.error('Image search failed:', error);
      
      // Add better error formatting
      if (error instanceof Error) {
        throw error;
      } else {
        throw new Error(`Image search failed: ${JSON.stringify(error)}`);
      }
    }
  }
};

// Category API functions
export const categoryApi = {
  // Get all categories
  getAll: async (): Promise<Category[]> => {
    try {
      console.log('DEBUG: getAll categories - trying official endpoint');
      // Try the official endpoint first
      try {
        const categories = await fetchApi<Category[]>('/categories/categories/');
        console.log('DEBUG: Official categories endpoint succeeded:', categories);
        return categories;
      } catch (error) {
        console.error('DEBUG: Official categories endpoint failed:', error);
      }
      
      // Try alternative endpoint
      try {
        console.log('DEBUG: Trying categories search endpoint');
        const categoryNames = await fetchApi<string[]>('/search/categories');
        console.log('DEBUG: Categories search endpoint succeeded:', categoryNames);
        
        // Convert to the expected Category structure
        return categoryNames.map((name, index) => ({
          id: index + 1,
          name: name,
          slug: name.toLowerCase().replace(/\s+/g, '-'),
          description: '',
          recipe_count: 0
        }));
      } catch (error) {
        console.error('DEBUG: Categories search endpoint failed:', error);
      }
      
      // Return empty array instead of fake data for debugging
      console.error('DEBUG: All category endpoints failed, returning empty array');
      return [];
    } catch (error) {
      console.error('DEBUG: Critical error in getAll categories:', error);
      throw error;
    }
  },
  
  // Get category by ID
  getById: async (id: string): Promise<Category> => {
    return fetchApi<Category>(`/categories/categories/${id}`);
  },
  
  // Get recipes in a category
  getRecipes: async (id: string, limit = 20, offset = 0): Promise<RecipeResponse[]> => {
    return fetchApi<RecipeResponse[]>(`/categories/categories/${id}/recipes?limit=${limit}&offset=${offset}`);
  }
}; 