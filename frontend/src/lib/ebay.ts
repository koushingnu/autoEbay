import { apiFetch } from "./api";

export type EbayStatus = {
  connected: boolean;
  mock: boolean;
  env: string;
  message: string;
};

export function getEbayStatus() {
  return apiFetch<EbayStatus>("/api/ebay/status");
}

export type ListingPreview = {
  asin: string;
  title: string;
  description: string;
  image_url: string;
  price_usd: number;
  shipping_usd: number;
  category: string;
  condition: string;
  currency: string;
};

export type PreviewResponse = {
  mock: boolean;
  preview: ListingPreview;
};

export function getListingPreview(asin: string) {
  return apiFetch<PreviewResponse>(
    `/api/ebay/preview/${encodeURIComponent(asin)}`
  );
}

export type ListResponse = {
  mock: boolean;
  ebay_item_id: string;
  listing_status: string;
  ebay_price_usd: number;
};

export function createListing(
  asin: string,
  titleEn = "",
  descriptionEn = ""
) {
  return apiFetch<ListResponse>("/api/ebay/list", {
    method: "POST",
    json: { asin, title_en: titleEn, description_en: descriptionEn },
  });
}

export type ManagedProduct = {
  asin: string;
  title: string;
  image: string;
  amazon_price: number;
  ebay_price: number;
  ebay_price_usd: number;
  profit: number;
  profit_rate: number;
  sales_rank: number | null;
  listing_status: string;
  ebay_item_id: string | null;
  is_mock: boolean | null;
  last_updated: string | null;
};

export type ManagedListResponse = {
  count: number;
  items: ManagedProduct[];
};

export function getManagedProducts() {
  return apiFetch<ManagedListResponse>("/api/ebay/managed");
}
