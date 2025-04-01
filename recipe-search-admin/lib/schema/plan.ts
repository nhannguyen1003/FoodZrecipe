import { DiscountTypeEnum, PaymentIntervalEnum } from "@/types/enums";
import { z } from "zod";

export const planSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().min(1, "Description is required"),
  basePrice: z.preprocess(
    (val) => (val === "" ? undefined : parseFloat(val as string)),
    z.number({ invalid_type_error: "Price must be a number" })
  ),
  isActive: z.preprocess((val) => (val === "true" ? true : false), z.boolean()),
  features: z
    .array(z.string().min(1, "Feature is required"))
    .min(1, "At least one feature is required"),
  appConfig: z
    .array(
      z.object({
        value: z.string().min(1, "Value is required"),
        type: z.string().min(1, "Type is required"),
      })
    )
    .min(1, "At least one app config is required"),
  paymentInterval: z
    .array(
      z.object({
        interval: z.nativeEnum(PaymentIntervalEnum),
        discount: z.preprocess(
          (val) => (val === "" ? undefined : parseFloat(val as string)),
          z
            .number({ invalid_type_error: "Discount must be a number" })
            .min(0, "Discount is required")
        ),
        type: z.nativeEnum(DiscountTypeEnum),
      })
    )
    .min(1, "At least one payment interval is required"),
  regionalPrice: z
    .array(
      z.object({
        region: z.string().min(1, "Region is required"),
        discount: z.preprocess(
          (val) => (val === "" ? undefined : parseFloat(val as string)),
          z
            .number({ invalid_type_error: "Discount must be a number" })
            .min(0, "Discount is required")
        ),
        type: z.nativeEnum(DiscountTypeEnum),
      })
    )
    .min(1, "At least one region is required"),
});
export type PlanInput = z.infer<typeof planSchema>;
