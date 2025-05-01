import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign Up | FoodZ Recipe",
  description: "Create an account to save your favorite recipes, create collections, and more",
};

export default function SignupLayout({
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