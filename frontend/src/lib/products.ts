import { apiFetch } from "./api";

export type ProfitInfo = {
  shipping: number;
  ebay_fee: number;
  ebay_price: number;
  ebay_price_usd: number;
  profit: number;
  profit_rate: number;
};

export type AmazonProduct = {
  asin: string;
  title: string;
  amazon_price: number;
  image: string;
  brand: string;
  description: string;
  category: string;
  sales_rank: number | null;
};

export type ProductWithProfit = AmazonProduct & {
  profit: ProfitInfo;
  score: number;
};

export type ProductSearchResponse = {
  keyword: string;
  mock: boolean;
  count: number;
  items: ProductWithProfit[];
};

export type SearchOptions = {
  limit?: number;
  sort?: string;
  minProfit?: number;
  minProfitRate?: number;
};

export function searchProducts(keyword: string, opts: SearchOptions = {}) {
  const params = new URLSearchParams({
    keyword,
    limit: String(opts.limit ?? 50),
    sort: opts.sort ?? "balanced",
    min_profit: String(opts.minProfit ?? 0),
    min_profit_rate: String(opts.minProfitRate ?? 0),
  });
  return apiFetch<ProductSearchResponse>(`/api/products/search?${params}`);
}

export type ProductDetailResponse = {
  mock: boolean;
  last_updated: string | null;
  product: ProductWithProfit;
};

export function getProductDetail(asin: string, refresh = false) {
  const params = new URLSearchParams({ refresh: String(refresh) });
  return apiFetch<ProductDetailResponse>(
    `/api/products/detail/${encodeURIComponent(asin)}?${params}`
  );
}

export type TranslateResponse = {
  title_en: string;
  description_en: string;
  mock: boolean;
};

export function translateProduct(title: string, description: string) {
  return apiFetch<TranslateResponse>("/api/products/translate", {
    method: "POST",
    json: { title, description },
  });
}

const LAST_SEARCH_KEY = "lastSearch";

export type LastSearch = {
  keyword: string;
  mock: boolean;
  items: ProductWithProfit[];
};

/** 直近の検索結果を保存し、詳細から戻った時に一覧を復元できるようにする。 */
export function storeLastSearch(data: LastSearch) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(LAST_SEARCH_KEY, JSON.stringify(data));
}

export function loadLastSearch(): LastSearch | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem(LAST_SEARCH_KEY);
  return raw ? (JSON.parse(raw) as LastSearch) : null;
}
