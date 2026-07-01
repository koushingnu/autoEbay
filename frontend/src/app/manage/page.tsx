"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import AppHeader from "@/components/AppHeader";
import { useRequireAuth } from "@/lib/useAuth";
import {
  getManagedProducts,
  getEbayStatus,
  type ManagedProduct,
  type EbayStatus,
} from "@/lib/ebay";

const STATUS_LABEL: Record<string, string> = {
  not_listed: "未出品",
  listed: "出品済み",
  pending: "処理中",
};

export default function ManagePage() {
  const { user, checking } = useRequireAuth();

  const [items, setItems] = useState<ManagedProduct[]>([]);
  const [ebay, setEbay] = useState<EbayStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [managed, status] = await Promise.all([
        getManagedProducts(),
        getEbayStatus(),
      ]);
      setItems(managed.items);
      setEbay(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "取得に失敗しました");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) load();
  }, [user, load]);

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

      <main className="mx-auto w-full max-w-6xl px-6 py-8">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
            商品管理
          </h2>
          {ebay && (
            <span
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                ebay.connected
                  ? "bg-green-100 text-green-700 dark:bg-green-950/40 dark:text-green-400"
                  : "bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400"
              }`}
              title={ebay.message}
            >
              eBay: {ebay.connected ? "接続OK" : "未接続"}
              {ebay.mock ? "（モック）" : `（${ebay.env}）`}
            </span>
          )}
        </div>

        {ebay && (
          <p className="mb-6 rounded-lg bg-zinc-100 px-4 py-2 text-xs text-zinc-500 dark:bg-zinc-900 dark:text-zinc-400">
            {ebay.message}
          </p>
        )}

        {error && (
          <p className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600 dark:bg-red-950/40 dark:text-red-400">
            {error}
          </p>
        )}

        {loading && <p className="text-sm text-zinc-500">読み込み中...</p>}

        {!loading && items.length === 0 && !error && (
          <p className="text-sm text-zinc-500">
            まだ商品がありません。
            <Link href="/search" className="ml-1 underline">
              商品検索
            </Link>
            から商品を取得してください。
          </p>
        )}

        {items.length > 0 && (
          <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
            <table className="w-full text-sm">
              <thead className="border-b border-zinc-200 text-left text-xs text-zinc-500 dark:border-zinc-800">
                <tr>
                  <th className="px-4 py-3">商品</th>
                  <th className="px-4 py-3 text-right">Amazon</th>
                  <th className="px-4 py-3 text-right">eBay(USD)</th>
                  <th className="px-4 py-3 text-right">利益</th>
                  <th className="px-4 py-3 text-right">売れ筋</th>
                  <th className="px-4 py-3">状態</th>
                  <th className="px-4 py-3">更新日</th>
                </tr>
              </thead>
              <tbody>
                {items.map((p) => (
                  <tr
                    key={p.asin}
                    className="border-b border-zinc-100 last:border-0 dark:border-zinc-800"
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/products/${p.asin}`}
                        className="flex items-center gap-3"
                      >
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={p.image}
                          alt={p.title}
                          className="h-10 w-10 rounded bg-zinc-100 object-cover dark:bg-zinc-800"
                        />
                        <span className="line-clamp-2 max-w-xs text-zinc-900 hover:underline dark:text-zinc-100">
                          {p.title}
                        </span>
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-right text-zinc-700 dark:text-zinc-300">
                      ¥{p.amazon_price.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right text-zinc-700 dark:text-zinc-300">
                      ${p.ebay_price_usd.toLocaleString()}
                    </td>
                    <td
                      className={`px-4 py-3 text-right font-medium ${
                        p.profit >= 0
                          ? "text-green-600 dark:text-green-400"
                          : "text-red-600 dark:text-red-400"
                      }`}
                    >
                      ¥{p.profit.toLocaleString()}（{p.profit_rate}%）
                    </td>
                    <td className="px-4 py-3 text-right text-zinc-500">
                      {p.sales_rank ? `#${p.sales_rank.toLocaleString()}` : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          p.listing_status === "listed"
                            ? "bg-green-100 text-green-700 dark:bg-green-950/40 dark:text-green-400"
                            : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                        }`}
                      >
                        {STATUS_LABEL[p.listing_status] ?? p.listing_status}
                        {p.listing_status === "listed" && p.is_mock ? "（モック）" : ""}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-zinc-400">
                      {p.last_updated
                        ? new Date(p.last_updated + "Z").toLocaleString("ja-JP")
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
