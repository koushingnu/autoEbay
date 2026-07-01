"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { logout } from "@/lib/auth";

const NAV = [
  { href: "/", label: "ホーム" },
  { href: "/search", label: "商品検索" },
  { href: "/manage", label: "商品管理" },
];

export default function AppHeader({ username }: { username: string }) {
  const router = useRouter();
  const pathname = usePathname();

  async function handleLogout() {
    await logout().catch(() => {});
    router.replace("/login");
  }

  return (
    <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-4 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-center gap-6">
        <span className="font-semibold text-zinc-900 dark:text-zinc-50">
          Amazon → eBay
        </span>
        <nav className="flex gap-1 text-sm">
          {NAV.map((n) => {
            const active = pathname === n.href;
            return (
              <Link
                key={n.href}
                href={n.href}
                className={`rounded-lg px-3 py-1.5 transition-colors ${
                  active
                    ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                    : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
                }`}
              >
                {n.label}
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="flex items-center gap-4 text-sm">
        <span className="text-zinc-500 dark:text-zinc-400">{username}</span>
        <button
          onClick={handleLogout}
          className="rounded-lg border border-zinc-300 px-3 py-1.5 font-medium text-zinc-700 transition-colors hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
        >
          ログアウト
        </button>
      </div>
    </header>
  );
}
