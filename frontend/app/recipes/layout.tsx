import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Recipes | FoodZ Recipe",
  description: "Browse our collection of delicious recipes organized by categories",
};

export default function RecipesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      {children}
    </>
  );
} 