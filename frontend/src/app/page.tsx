"use client";

import Link from "next/link";
import AppHeader from "@/components/AppHeader";
import { useRequireAuth } from "@/lib/useAuth";

export default function DashboardPage() {
  const { user, checking } = useRequireAuth();

  if (checking) {
    return (
      <div className="flex flex-1 items-center justify-center text-zinc-500">
        読み込み中...
      </div>
    );
  }

  if (!user) return null;

  const phases = [
    { done: true, label: "Phase1: 環境構築" },
    { done: true, label: "Phase2: ログイン・管理画面" },
    { done: true, label: "Phase3: Amazon商品検索・一覧" },
    { done: true, label: "Phase4: 利益計算" },
    { done: true, label: "Phase5: 商品詳細" },
    { done: true, label: "Phase6: 英語タイトル/説明生成" },
    { done: true, label: "Phase7: eBay API接続" },
    { done: true, label: "Phase8: 出品プレビュー" },
    { done: true, label: "Phase9: eBay出品" },
    { done: true, label: "Phase10: 商品管理" },
  ];

  return (
    <div className="flex flex-1 flex-col bg-zinc-50 dark:bg-zinc-950">
      <AppHeader username={user.username} />

      <main className="mx-auto w-full max-w-3xl px-6 py-10">
        <h2 className="mb-2 text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          ようこそ、{user.username} さん
        </h2>
        <p className="mb-6 text-sm text-zinc-500 dark:text-zinc-400">
          開発フェーズの進捗です。1機能ずつ実装していきます。
        </p>

        <Link
          href="/search"
          className="mb-8 inline-flex rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          商品検索へ →
        </Link>

        <ul className="divide-y divide-zinc-200 overflow-hidden rounded-xl border border-zinc-200 bg-white dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-900">
          {phases.map((p) => (
            <li
              key={p.label}
              className="flex items-center gap-3 px-4 py-3 text-sm text-zinc-700 dark:text-zinc-200"
            >
              <span
                className={`inline-flex h-5 w-5 items-center justify-center rounded-full text-xs ${
                  p.done
                    ? "bg-green-500 text-white"
                    : "bg-zinc-200 text-zinc-400 dark:bg-zinc-700"
                }`}
              >
                {p.done ? "✓" : ""}
              </span>
              {p.label}
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
