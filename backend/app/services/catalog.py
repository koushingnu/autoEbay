"""商品取得のオーケストレーション（DB優先 + Keepa最小呼び出し）。

方針:
  検索
    → Keepaのキーワード検索（1回・keyword単位でキャッシュ）で商品を取得
    → 取得結果をDBへ upsert（以降のASIN参照はDBで完結）
    → DBから読み出して返す
  詳細（ASIN指定）
    → DBを確認
        - 存在し鮮度内 → DBを使う（Keepa呼び出しなし）★トークン節約
        - 無い/古い/手動更新 → Keepaで /product 取得 → DB保存

Keepaキーが無い場合はモックを生成してDBへ保存し、以降はDB優先で表示する。
"""

import logging

from sqlalchemy.orm import Session

from app.models import Product
from app.services import amazon, keepa
from app.repositories import product_repo

logger = logging.getLogger("app.catalog")


def search(db: Session, keyword: str, limit: int = 8) -> tuple[list[Product], bool]:
    """(商品リスト, is_mock) を返す。"""
    if amazon.is_mock():
        data = amazon.mock_products(keyword, limit)
    else:
        data = keepa.search_products(keyword, limit)

    if not data:
        return [], amazon.is_mock()

    # 取得結果をDBへ保存し、DBから読み出して返す（ASIN順を維持）
    product_repo.upsert_many(db, data)
    asins = [d.asin for d in data]
    stored = product_repo.get_by_asins(db, asins)
    return [stored[a] for a in asins if a in stored], amazon.is_mock()


def get_detail(db: Session, asin: str, refresh: bool = False) -> tuple[Product | None, bool]:
    """ASIN指定の詳細取得。DB優先。refresh=True で強制的にKeepa再取得。"""
    is_mock = amazon.is_mock()
    product = product_repo.get_by_asin(db, asin)

    need_fetch = refresh or product is None or (
        not is_mock and not product_repo.is_fresh(product)
    )

    if need_fetch and not is_mock:
        fetched = keepa.fetch_products([asin])
        if fetched:
            product_repo.upsert_many(db, fetched)
            product = product_repo.get_by_asin(db, asin)

    return product, is_mock
