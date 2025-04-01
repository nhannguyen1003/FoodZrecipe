import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { customAlphabet } from "nanoid";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(input: string | number): string {
  const date = new Date(input);
  return date.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export function absoluteUrl(path: string) {
  return `${process.env.NEXT_PUBLIC_SITE_URL}${path}`;
}

export const nanoid = customAlphabet("abcdefghijklmnopqrstuvwxyz0123456789");

export const apiInfo = <T, E>(
  input: string,
  method: "GET" | "POST" | "PATCH" | "DELETE"
) => {
  return {
    input,
    method,
    bodyType: {} as T,
    responseType: {} as E,
  };
};
