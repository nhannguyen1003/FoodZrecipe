import FeaturedRecipes from './components/FeaturedRecipes';
import CategorySection from './components/CategorySection';
import LatestRecipes from './components/LatestRecipes';
import SearchBar from './components/SearchBar';

export default function Home() {
  return (
    <div>
      {/* Hero Section with Search */}
      <section className="bg-[#734061] py-16 text-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4">
              Find Your Perfect Recipe
            </h1>
            <p className="text-xl max-w-3xl mx-auto opacity-90">
              Search thousands of recipes by keyword or upload a food image to find similar dishes
            </p>
          </div>
          
          <div id="search-container">
            <SearchBar />
          </div>
        </div>
      </section>
      
      <FeaturedRecipes />
      <CategorySection />
      <LatestRecipes />
    </div>
  );
}
