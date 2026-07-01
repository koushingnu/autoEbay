"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppHeader from "@/components/AppHeader";
import { useRequireAuth } from "@/lib/useAuth";
import {
  searchProducts,
  storeLastSearch,
  loadLastSearch,
  type ProductWithProfit,
} from "@/lib/products";

export default function SearchPage() {
  const { user, checking } = useRequireAuth();

  const [keyword, setKeyword] = useState("");
  const [items, setItems] = useState<ProductWithProfit[]>([]);
  const [mock, setMock] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const [limit, setLimit] = useState(50);
  const [sort, setSort] = useState("balanced");
  const [minProfit, setMinProfit] = useState(0);
  const [minProfitRate, setMinProfitRate] = useState(0);

  useEffect(() => {
    const last = loadLastSearch();
    if (last) {
      setKeyword(last.keyword);
      setItems(last.items);
      setMock(last.mock);
      setSearched(true);
    }
  }, []);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!keyword.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await searchProducts(keyword.trim(), {
        limit,
        sort,
        minProfit,
        minProfitRate,
      });
      setItems(res.items);
      setMock(res.mock);
      setSearched(true);
      storeLastSearch({ keyword: keyword.trim(), mock: res.mock, items: res.items });
    } catch (err) {
      setError(err instanceof Error ? err.message : "検索に失敗しました");
    } finally {
      setLoading(false);
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

      <main className="mx-auto w-full max-w-5xl px-6 py-8">
        <div className="mb-6 flex items-center gap-3">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
            Amazon 商品検索
          </h2>
          {mock ? (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-950/40 dark:text-amber-400">
              モックデータ
            </span>
          ) : (
            <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-950/40 dark:text-green-400">
              Keepa 実データ
            </span>
          )}
        </div>

        <form onSubmit={handleSearch} className="mb-8 space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="キーワードを入力（例: ヘッドホン）"
              className="flex-1 rounded-lg border border-zinc-300 px-4 py-2 text-zinc-900 outline-none focus:border-zinc-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 dark:focus:border-zinc-400"
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-zinc-900 px-6 py-2 font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
            >
              {loading ? "検索中..." : "検索"}
            </button>
          </div>

          <div className="flex flex-wrap items-end gap-3 text-xs text-zinc-500">
            <label className="flex flex-col gap-1">
              <span>取得件数</span>
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="rounded-md border border-zinc-300 px-2 py-1.5 text-zinc-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              >
                {[10, 20, 50, 100].map((n) => (
                  <option key={n} value={n}>
                    {n}件
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1">
              <span>並び替え（費用対効果）</span>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value)}
                className="rounded-md border border-zinc-300 px-2 py-1.5 text-zinc-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              >
                <option value="balanced">総合スコア（需要×利益率）</option>
                <option value="demand">需要（売れ筋ランク）</option>
                <option value="profit_rate">利益率</option>
                <option value="profit_abs">利益額</option>
                <option value="price">Amazon価格</option>
              </select>
            </label>
            <label className="flex flex-col gap-1">
              <span>最低利益(円)</span>
              <input
                type="number"
                value={minProfit}
                min={0}
                onChange={(e) => setMinProfit(Number(e.target.value))}
                className="w-24 rounded-md border border-zinc-300 px-2 py-1.5 text-zinc-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span>最低利益率(%)</span>
              <input
                type="number"
                value={minProfitRate}
                min={0}
                onChange={(e) => setMinProfitRate(Number(e.target.value))}
                className="w-24 rounded-md border border-zinc-300 px-2 py-1.5 text-zinc-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              />
            </label>
          </div>
        </form>

        {searched && !loading && items.length > 0 && (
          <p className="mb-4 text-sm text-zinc-500">
            {items.length} 件を費用対効果順に表示中
          </p>
        )}

        {error && (
          <p className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600 dark:bg-red-950/40 dark:text-red-400">
            {error}
          </p>
        )}

        {searched && !loading && items.length === 0 && !error && (
          <p className="text-sm text-zinc-500">該当する商品がありませんでした。</p>
        )}

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {items.map((p) => (
            <Link
              href={`/products/${p.asin}`}
              key={p.asin}
              className="block overflow-hidden rounded-xl border border-zinc-200 bg-white transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900"
            >
              <div className="relative">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={p.image}
                  alt={p.title}
                  className="aspect-square w-full bg-zinc-100 object-cover dark:bg-zinc-800"
                />
                <span className="absolute right-2 top-2 rounded-full bg-zinc-900/80 px-2 py-0.5 text-xs font-semibold text-white">
                  スコア {p.score}
                </span>
              </div>
              <div className="flex flex-col gap-1 p-3">
                <span className="text-xs text-zinc-400">{p.brand}</span>
                <h3 className="line-clamp-2 text-sm font-medium text-zinc-900 dark:text-zinc-100">
                  {p.title}
                </h3>
                <span className="text-xs text-zinc-400">ASIN: {p.asin}</span>

                <dl className="mt-2 space-y-0.5 border-t border-zinc-100 pt-2 text-xs dark:border-zinc-800">
                  <div className="flex justify-between">
                    <dt className="text-zinc-400">Amazon価格</dt>
                    <dd className="text-zinc-700 dark:text-zinc-300">
                      ¥{p.amazon_price.toLocaleString()}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-zinc-400">送料</dt>
                    <dd className="text-zinc-700 dark:text-zinc-300">
                      ¥{p.profit.shipping.toLocaleString()}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-zinc-400">eBay価格</dt>
                    <dd className="font-medium text-zinc-900 dark:text-zinc-100">
                      ¥{p.profit.ebay_price.toLocaleString()}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-zinc-400">利益</dt>
                    <dd
                      className={`font-semibold ${
                        p.profit.profit >= 0
                          ? "text-green-600 dark:text-green-400"
                          : "text-red-600 dark:text-red-400"
                      }`}
                    >
                      ¥{p.profit.profit.toLocaleString()}（{p.profit.profit_rate}%）
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-zinc-400">売れ筋ランク</dt>
                    <dd className="text-zinc-700 dark:text-zinc-300">
                      {p.sales_rank ? `#${p.sales_rank.toLocaleString()}` : "—"}
                    </dd>
                  </div>
                </dl>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
