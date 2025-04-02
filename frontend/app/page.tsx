import FeaturedRecipes from './components/FeaturedRecipes';
import CategorySection from './components/CategorySection';
import LatestRecipes from './components/LatestRecipes';

export default function Home() {
  return (
    <div>
      <FeaturedRecipes />
      <CategorySection />
      <LatestRecipes />
    </div>
  );
}
