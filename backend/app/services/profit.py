"""利益計算サービス（MVP・固定値ベース）。

計算モデル（単位は円）:
  base       = amazon_price + shipping
  ebay_price = base / (1 - ebay_fee_rate - target_profit_rate)   # 目標利益率を確保する販売価格
  ebay_fee   = ebay_price * ebay_fee_rate
  profit     = ebay_price - amazon_price - shipping - ebay_fee
  profit_rate= profit / ebay_price * 100

固定値（送料・手数料率・目標利益率）は config で調整可能。
将来は為替(USD)や実際のeBay手数料体系に差し替える。
"""

import math

from app.config import settings
from app.schemas import ProfitInfo


def calculate(amazon_price: float) -> ProfitInfo:
    shipping = settings.shipping_cost
    fee_rate = settings.ebay_fee_rate
    target = settings.target_profit_rate

    base = amazon_price + shipping
    denominator = max(1 - fee_rate - target, 0.01)  # 0除算・負数を防ぐ
    ebay_price = math.ceil(base / denominator)
    ebay_fee = round(ebay_price * fee_rate)
    profit = ebay_price - int(amazon_price) - shipping - ebay_fee
    profit_rate = round(profit / ebay_price * 100, 1) if ebay_price > 0 else 0.0
    ebay_price_usd = (
        round(ebay_price / settings.usd_jpy_rate, 2) if settings.usd_jpy_rate > 0 else 0.0
    )

    return ProfitInfo(
        shipping=shipping,
        ebay_fee=ebay_fee,
        ebay_price=ebay_price,
        ebay_price_usd=ebay_price_usd,
        profit=profit,
        profit_rate=profit_rate,
    )
