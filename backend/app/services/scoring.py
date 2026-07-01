"""費用対効果スコアリング。

需要（売れやすさ）は現状 Keepa の売れ筋ランクを代理指標とする。
将来 eBay の実売データが使えるようになったら demand_score を差し替える。

  demand_score : 売れ筋ランクを 0〜1 に正規化（ランクが小さいほど高い）
  score        : 需要 × 利益率 を 0〜100 目安で算出（大きいほど有望）
"""

import math

from app.schemas import ProfitInfo, ProductWithProfit


def demand_score(sales_rank: int | None) -> float:
    """売れ筋ランク→需要スコア(0〜1)。ランク1で最大、~10^7で最小。"""
    if not sales_rank or sales_rank <= 0:
        return 0.0
    return max(0.0, min(1.0, 1 - math.log10(sales_rank) / 7))


def cost_effectiveness(profit: ProfitInfo, sales_rank: int | None) -> float:
    """表示用の費用対効果スコア（需要 × 利益率）。"""
    demand = demand_score(sales_rank)
    profit_rate_frac = max(profit.profit_rate, 0) / 100
    return round(demand * profit_rate_frac * 100, 2)


def sort_key(item: ProductWithProfit, mode: str):
    """並び替えキー（降順で使用）。"""
    if mode == "profit_rate":
        return item.profit.profit_rate
    if mode == "profit_abs":
        return item.profit.profit
    if mode == "demand":
        return demand_score(item.sales_rank)
    if mode == "price":
        return item.amazon_price
    # balanced（既定）
    return item.score
