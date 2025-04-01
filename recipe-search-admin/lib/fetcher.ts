import { getFetch } from "@trpc/client";
import { apiInfo } from "./utils";

type ApiInfo = ReturnType<typeof apiInfo>;

export class Fetcher {
  private endpoint: string;
  private token: string;

  constructor(endpoint: string, token: string) {
    this.endpoint = endpoint;
    this.token = token;
  }

  public async fetchApi<
    T extends ApiInfo,
    E extends T["bodyType"],
    S extends T["responseType"]
  >(
    info: T,
    init?: { payload?: E; options?: Omit<RequestInit, "body"> }
  ): Promise<{ data: S; error: null } | { data: null; error: string }> {
    const fetch = getFetch();
    const url = new URL(info.input, this.endpoint);
    try {
      const body = init?.payload
        ? this.jsonToFormData(init?.payload)
        : undefined;
      const response = await fetch(url, {
        ...init?.options,
        body,
        method: info.method,
        headers: {
          "Content-Type": "application/json",
          Accept: "*",
          ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
          ...init?.options?.headers,
        },
      });

      return { data: response.json() as S, error: null };
    } catch (e) {
      return {
        data: null,
        error: "Something went wrong",
      };
    }
  }

  private jsonToFormData(
    obj: Record<string, any>,
    formData = new FormData(),
    parentKey?: string
  ): FormData {
    for (const key of Object.keys(obj)) {
      const propName = parentKey ? `${parentKey}[${key}]` : key;
      const propValue = obj[key];

      if (propValue instanceof File) {
        formData.append(propName, propValue);
      } else if (propValue instanceof Date) {
        formData.append(propName, propValue.toISOString());
      } else if (typeof propValue === "object" && propValue !== null) {
        this.jsonToFormData(propValue, formData, propName);
      } else {
        formData.append(propName, propValue?.toString() ?? "");
      }
    }

    return formData;
  }
}
