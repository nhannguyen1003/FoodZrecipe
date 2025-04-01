import { subscriptionApi } from "@/config/api";
import { db } from "@/lib/db";
import { products, productSchema } from "@/lib/db/schema/product";
import { Fetcher } from "@/lib/fetcher";
import { planSchema } from "@/lib/schema/plan";
import { protectedProcedure, router } from "@/lib/server/trpc";
import { DiscountTypeEnum, PaymentIntervalEnum } from "@/types/enums";
import { TRPCError } from "@trpc/server";
import { count, eq, getTableColumns } from "drizzle-orm";
import { z } from "zod";

export const productRouter = router({
  getProducts: protectedProcedure
    .input(
      z.object({
        offset: z.number().min(1).max(100).optional(),
        page: z.number().min(1).optional(),
      })
    )
    .query(async ({ input }) => {
      const { offset = 10, page = 1 } = input;

      const [{ count: total }] = await db
        .select({ count: count() })
        .from(products);
      const result = await db
        .select()
        .from(products)
        .limit(offset)
        .offset((page - 1) * offset);

      return {
        data: result,
        pagination: {
          total,
        },
      };
    }),
  getProduct: protectedProcedure
    .input(z.object({ id: z.number() }))
    .query(async ({ input }) => {
      const { id } = input;

      const [product] = await db
        .select()
        .from(products)
        .where(eq(products.id, id));

      if (!product) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Product Id not found",
        });
      }

      return product;
    }),
  addProduct: protectedProcedure
    .input(productSchema)
    .mutation(async ({ input }) => {
      const [product] = await db
        .insert(products)
        .values({
          ...input,
        })
        .returning();

      return {
        id: product.id,
      };
    }),
  updateProduct: protectedProcedure
    .input(
      z.object({
        id: z.number(),
        payload: productSchema.partial(),
      })
    )
    .mutation(async ({ input }) => {
      const { id, payload } = input;
      const [product] = await db
        .update(products)
        .set(payload)
        .where(eq(products.id, id))
        .returning();
      return {
        id: product.id,
      };
    }),
  deleteProduct: protectedProcedure
    .input(z.object({ id: z.number() }))
    .mutation(async ({ input }) => {
      const { id } = input;

      const [product] = await db
        .delete(products)
        .where(eq(products.id, id))
        .returning();

      return {
        id: product.id,
      };
    }),
  getPlans: protectedProcedure
    .input(
      z.object({ productId: z.number(), offset: z.number(), page: z.number() })
    )
    .query(async ({ input }) => {
      const { productId, offset, page } = input;

      const [product] = await db
        .select()
        .from(products)
        .where(eq(products.id, productId));

      if (!product) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Product Id not found",
        });
      }

      // const fetcher = new Fetcher(product.endpoint, product.token);
      // const plans = await fetcher.fetchApi(
      //   subscriptionApi.getPlans({ offset, page })
      // );

      // if (plans.error) {
      //   throw new TRPCError({
      //     code: "BAD_REQUEST",
      //     message: "Something went wrong",
      //   });
      // }

      const plansData = {
        data: [
          {
            id: 1,
            name: "Hobby",
            description: "Hobby plans...",
            basePrice: 1000,
            isActive: true,
            features: ["5 users", "2 teams"],
          },
          {
            id: 2,
            name: "Pro",
            description: "Pro plans...",
            basePrice: 1500,
            isActive: true,
            features: ["10 users", "5 teams"],
          },
        ],
        pagination: {
          total: 2,
        },
      };

      return {
        data: plansData.data,
        pagination: plansData.pagination,
      };
    }),
  getPlanDetail: protectedProcedure
    .input(z.object({ productId: z.number(), planId: z.number() }))
    .query(async ({ input }) => {
      const { productId, planId } = input;

      const [product] = await db
        .select()
        .from(products)
        .where(eq(products.id, productId));

      if (!product) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Product Id not found",
        });
      }

      const fetcher = new Fetcher(product.endpoint, product.token);
      const planDetail = await fetcher.fetchApi(
        subscriptionApi.getPlanDetail({ id: planId })
      );

      if (planDetail.error) {
        throw new TRPCError({
          code: "BAD_REQUEST",
          message: "Something went wrong",
        });
      }

      if (!planDetail.data) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Plan Id not found",
        });
      }

      return planDetail.data;
    }),
  addPlan: protectedProcedure
    .input(z.object({ productId: z.number(), payload: planSchema }))
    .mutation(async ({ input }) => {
      const { productId, payload } = input;

      const [product] = await db
        .select()
        .from(products)
        .where(eq(products.id, productId));

      if (!product) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Product Id not found",
        });
      }

      const fetcher = new Fetcher(product.endpoint, product.token);
      const result = await fetcher.fetchApi(subscriptionApi.createPlan(), {
        payload,
      });

      if (result.error) {
        throw new TRPCError({
          code: "BAD_REQUEST",
          message: "Something went wrong",
        });
      }

      return { id: result.data?.id };
    }),
  updatePlan: protectedProcedure
    .input(
      z.object({
        productId: z.number(),
        planId: z.number(),
        payload: planSchema.deepPartial(),
      })
    )
    .mutation(async ({ input }) => {
      const { productId, planId, payload } = input;

      const [product] = await db
        .select()
        .from(products)
        .where(eq(products.id, productId));

      if (!product) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Product Id not found",
        });
      }

      const fetcher = new Fetcher(product.endpoint, product.token);
      const result = await fetcher.fetchApi(
        subscriptionApi.updatePlan({ id: planId }),
        {
          payload,
        }
      );

      if (result.error) {
        throw new TRPCError({
          code: "BAD_REQUEST",
          message: "Something went wrong",
        });
      }

      return { id: result.data?.id };
    }),
});
