import { getUserAuth } from "@/lib/auth/utils";
import { protectedProcedure, router } from "@/lib/server/trpc";
export const accountRouter = router({
  getUser: protectedProcedure.query(async () => {
    const { session } = await getUserAuth();
    return session;
  }),
});
