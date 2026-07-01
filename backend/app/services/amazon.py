"""モック商品プロバイダ（Keepaキー未設定時のフォールバック）。

Keepaキーがある場合は catalog + keepa 経由で実データを使う。
"""

import hashlib
import random

from app.config import settings
from app.schemas import ProductData

_BRANDS = ["SONY", "Panasonic", "Nintendo", "Canon", "Anker", "Logicool"]
_CATEGORIES = ["家電", "カメラ", "ゲーム", "オーディオ", "PC周辺機器", "生活家電"]


def is_mock() -> bool:
    """モックデータを使うか（= Keepaキー未設定か）。"""
    return not settings.keepa_api_key


def mock_products(keyword: str, limit: int = 8) -> list[ProductData]:
    """キーワードから決定的にモック商品を生成する（同じ語なら同じ結果）。"""
    seed = int(hashlib.md5(keyword.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed)

    items: list[ProductData] = []
    for i in range(limit):
        asin = "B" + "".join(rng.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(9))
        price = round(rng.uniform(1000, 30000), 0)
        brand = rng.choice(_BRANDS)
        category = rng.choice(_CATEGORIES)
        items.append(
            ProductData(
                asin=asin,
                jan="",
                title=f"{brand} {keyword} モデル {i + 1}",
                brand=brand,
                category=category,
                image_url=f"https://picsum.photos/seed/{asin}/300/300",
                description=(
                    f"{brand}の{keyword}。高品質な{category}カテゴリの商品です。"
                    f"型番相当のモデル{i + 1}。状態は新品、日本国内正規品を想定したモックデータです。"
                ),
                amazon_price=price,
                currency="JPY",
                sales_rank=rng.randint(1, 500_000),
            )
        )
    return items
