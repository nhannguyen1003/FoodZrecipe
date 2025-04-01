import { env } from "../env.mjs";

export function getBaseUrl() {
  if (typeof window !== "undefined") return "";
  if (env.APP_URL) return `https://${env.APP_URL}`;
  return "http://localhost:3000";
}

export function getUrl() {
  return getBaseUrl() + "/api/trpc";
}
