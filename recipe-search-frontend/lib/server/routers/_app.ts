import { router } from "@/lib/server/trpc";
import { accountRouter } from "./account";
import { productRouter } from "./product";

export const appRouter = router({
  account: accountRouter,
  product: productRouter,
});

export type AppRouter = typeof appRouter;
