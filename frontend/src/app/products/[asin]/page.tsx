"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import AppHeader from "@/components/AppHeader";
import { useRequireAuth } from "@/lib/useAuth";
import {
  getProductDetail,
  translateProduct,
  type ProductWithProfit,
  type TranslateResponse,
} from "@/lib/products";
import {
  getListingPreview,
  createListing,
  type ListingPreview,
  type ListResponse,
} from "@/lib/ebay";

export default function ProductDetailPage({
  params,
}: {
  params: Promise<{ asin: string }>;
}) {
  const { asin } = use(params);
  const { user, checking } = useRequireAuth();

  const [product, setProduct] = useState<ProductWithProfit | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const [translation, setTranslation] = useState<TranslateResponse | null>(null);
  const [translating, setTranslating] = useState(false);
  const [translateError, setTranslateError] = useState<string | null>(null);

  const [preview, setPreview] = useState<ListingPreview | null>(null);
  const [previewMock, setPreviewMock] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [listResult, setListResult] = useState<ListResponse | null>(null);
  const [listing, setListing] = useState(false);
  const [ebayError, setEbayError] = useState<string | null>(null);

  const load = useCallback(
    async (refresh: boolean) => {
      if (refresh) setRefreshing(true);
      else setLoading(true);
      setLoadError(null);
      try {
        const res = await getProductDetail(asin, refresh);
        setProduct(res.product);
        setLastUpdated(res.last_updated);
      } catch (err) {
        setLoadError(err instanceof Error ? err.message : "取得に失敗しました");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [asin]
  );

  useEffect(() => {
    load(false);
  }, [load]);

  async function handleTranslate() {
    if (!product) return;
    setTranslating(true);
    setTranslateError(null);
    try {
      const res = await translateProduct(product.title, product.description);
      setTranslation(res);
    } catch (err) {
      setTranslateError(
        err instanceof Error ? err.message : "英語生成に失敗しました"
      );
    } finally {
      setTranslating(false);
    }
  }

  async function handlePreview() {
    setPreviewing(true);
    setEbayError(null);
    setListResult(null);
    try {
      const res = await getListingPreview(asin);
      setPreview(res.preview);
      setPreviewMock(res.mock);
    } catch (err) {
      setEbayError(err instanceof Error ? err.message : "プレビュー取得に失敗しました");
    } finally {
      setPreviewing(false);
    }
  }

  async function handleList() {
    setListing(true);
    setEbayError(null);
    try {
      const res = await createListing(
        asin,
        translation?.title_en ?? "",
        translation?.description_en ?? ""
      );
      setListResult(res);
    } catch (err) {
      setEbayError(err instanceof Error ? err.message : "出品に失敗しました");
    } finally {
      setListing(false);
    }
  }

  if (checking) {
    return (
      <div className="flex flex-1 items-center justify-center text-zinc-500">
        読み込み中...
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex flex-1 flex-col bg-zinc-50 dark:bg-zinc-950">
      <AppHeader username={user.username} />

      <main className="mx-auto w-full max-w-4xl px-6 py-8">
        <Link
          href="/search"
          className="mb-6 inline-flex text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200"
        >
          ← 検索に戻る
        </Link>

        {loading && (
          <p className="text-sm text-zinc-500">読み込み中...</p>
        )}

        {!loading && loadError && (
          <div className="rounded-xl border border-zinc-200 bg-white p-8 text-center dark:border-zinc-800 dark:bg-zinc-900">
            <p className="mb-4 text-red-600 dark:text-red-400">{loadError}</p>
            <Link
              href="/search"
              className="inline-flex rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
            >
              商品検索へ
            </Link>
          </div>
        )}

        {product && (
          <>
            <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
              <div>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={product.image}
                  alt={product.title}
                  className="w-full rounded-xl border border-zinc-200 bg-zinc-100 object-cover dark:border-zinc-800 dark:bg-zinc-800"
                />
              </div>

              <div className="flex flex-col gap-4">
                <div>
                  <span className="text-sm text-zinc-400">{product.brand}</span>
                  <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                    {product.title}
                  </h1>
                  <div className="mt-1 flex flex-wrap gap-3 text-xs text-zinc-400">
                    <span>ASIN: {product.asin}</span>
                    {product.category && <span>カテゴリー: {product.category}</span>}
                  </div>
                </div>

                <div>
                  <h2 className="mb-1 text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    商品説明
                  </h2>
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
                    {product.description || "（説明なし）"}
                  </p>
                </div>

                <dl className="space-y-1 rounded-xl border border-zinc-200 bg-white p-4 text-sm dark:border-zinc-800 dark:bg-zinc-900">
                  <Row label="Amazon価格" value={`¥${product.amazon_price.toLocaleString()}`} />
                  <Row label="送料" value={`¥${product.profit.shipping.toLocaleString()}`} />
                  <Row label="eBay手数料" value={`¥${product.profit.ebay_fee.toLocaleString()}`} />
                  <Row
                    label="eBay価格"
                    value={`¥${product.profit.ebay_price.toLocaleString()}`}
                    strong
                  />
                  <div className="my-1 border-t border-zinc-100 dark:border-zinc-800" />
                  <div className="flex justify-between">
                    <dt className="text-zinc-500 dark:text-zinc-400">利益</dt>
                    <dd
                      className={`font-semibold ${
                        product.profit.profit >= 0
                          ? "text-green-600 dark:text-green-400"
                          : "text-red-600 dark:text-red-400"
                      }`}
                    >
                      ¥{product.profit.profit.toLocaleString()}（
                      {product.profit.profit_rate}%）
                    </dd>
                  </div>
                </dl>

                <div className="flex items-center gap-3 text-xs text-zinc-400">
                  <span>
                    最終更新:{" "}
                    {lastUpdated
                      ? new Date(lastUpdated + "Z").toLocaleString("ja-JP")
                      : "—"}
                  </span>
                  <button
                    onClick={() => load(true)}
                    disabled={refreshing}
                    className="rounded-lg border border-zinc-300 px-3 py-1 font-medium text-zinc-700 transition-colors hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                  >
                    {refreshing ? "取得中..." : "最新情報を取得"}
                  </button>
                </div>
              </div>
            </div>

            <section className="mt-10 rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
                  英語タイトル / 説明の生成（eBay向け）
                </h2>
                <button
                  onClick={handleTranslate}
                  disabled={translating}
                  className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
                >
                  {translating ? "生成中..." : "英語を生成"}
                </button>
              </div>

              <p className="mb-4 text-xs text-zinc-400">
                ※ この段階では出品しません。内容確認のみです。
              </p>

              {translateError && (
                <p className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600 dark:bg-red-950/40 dark:text-red-400">
                  {translateError}
                </p>
              )}

              {translation && (
                <div className="flex flex-col gap-4">
                  {translation.mock && (
                    <span className="w-fit rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-950/40 dark:text-amber-400">
                      モック翻訳（OPENAI_API_KEY 未設定）
                    </span>
                  )}
                  <div>
                    <h3 className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                      English Title
                    </h3>
                    <p className="rounded-lg bg-zinc-50 px-3 py-2 text-sm text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100">
                      {translation.title_en}
                    </p>
                  </div>
                  <div>
                    <h3 className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                      English Description
                    </h3>
                    <p className="whitespace-pre-wrap rounded-lg bg-zinc-50 px-3 py-2 text-sm text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
                      {translation.description_en}
                    </p>
                  </div>
                </div>
              )}
            </section>

            <section className="mt-6 rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
                  eBay 出品プレビュー
                </h2>
                <button
                  onClick={handlePreview}
                  disabled={previewing}
                  className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                >
                  {previewing ? "作成中..." : "プレビューを作成"}
                </button>
              </div>

              <p className="mb-4 text-xs text-zinc-400">
                ※ 英語を生成済みならその内容が使われます。未生成なら日本語のままです。
              </p>

              {ebayError && (
                <p className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600 dark:bg-red-950/40 dark:text-red-400">
                  {ebayError}
                </p>
              )}

              {preview && (
                <div className="flex flex-col gap-4">
                  {previewMock && (
                    <span className="w-fit rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-950/40 dark:text-amber-400">
                      モードモック（実際には出品されません）
                    </span>
                  )}
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={preview.image_url}
                      alt={preview.title}
                      className="w-full rounded-lg border border-zinc-200 bg-zinc-100 object-cover dark:border-zinc-800 dark:bg-zinc-800"
                    />
                    <dl className="space-y-1 text-sm">
                      <Row label="Title" value={preview.title} />
                      <Row label="Category" value={preview.category || "—"} />
                      <Row label="Condition" value={preview.condition} />
                      <Row
                        label="Price"
                        value={`$${preview.price_usd.toLocaleString()} USD`}
                        strong
                      />
                      <Row
                        label="Shipping"
                        value={`$${preview.shipping_usd.toLocaleString()} USD`}
                      />
                    </dl>
                  </div>
                  <div>
                    <h3 className="mb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                      Description
                    </h3>
                    <p className="whitespace-pre-wrap rounded-lg bg-zinc-50 px-3 py-2 text-sm text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
                      {preview.description || "（説明なし）"}
                    </p>
                  </div>

                  {listResult ? (
                    <div className="rounded-lg bg-green-50 px-4 py-3 text-sm text-green-700 dark:bg-green-950/40 dark:text-green-400">
                      出品しました（{listResult.mock ? "モック" : "実"}）: item_id{" "}
                      <span className="font-mono">{listResult.ebay_item_id}</span>／状態{" "}
                      {listResult.listing_status}
                    </div>
                  ) : (
                    <button
                      onClick={handleList}
                      disabled={listing}
                      className="w-fit rounded-lg bg-zinc-900 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
                    >
                      {listing ? "出品中..." : "この内容で出品する"}
                    </button>
                  )}
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}

function Row({
  label,
  value,
  strong = false,
}: {
  label: string;
  value: string;
  strong?: boolean;
}) {
  return (
    <div className="flex justify-between">
      <dt className="text-zinc-500 dark:text-zinc-400">{label}</dt>
      <dd
        className={
          strong
            ? "font-semibold text-zinc-900 dark:text-zinc-100"
            : "text-zinc-700 dark:text-zinc-300"
        }
      >
        {value}
      </dd>
    </div>
  );
}
