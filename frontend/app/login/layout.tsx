import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Login | FoodZ Recipe",
  description: "Sign in to your FoodZ Recipe account to save your favorite recipes and more",
};

export default function LoginLayout({
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