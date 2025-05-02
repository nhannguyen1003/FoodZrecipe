import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Search Results | FoodZ Recipe",
  description: "Find delicious recipes matching your search on FoodZ Recipe",
};

export default function SearchResultsLayout({
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