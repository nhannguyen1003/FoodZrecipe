'use client';

import { useSearchParams } from 'next/navigation';
import SearchResults from '../components/SearchResults';

export default function SearchPage() {
  const searchParams = useSearchParams();
  const query = searchParams.get('query') || '';
  
  return (
    <div className="min-h-screen bg-gray-50">
      <SearchResults query={query} />
    </div>
  );
} 