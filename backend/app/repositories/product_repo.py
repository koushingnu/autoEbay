"""商品テーブルへのアクセス（取得・保存・鮮度判定）。

取得処理（Keepa）とDB保存処理の責務を分離するための層。
"""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Product
from app.schemas import ProductData


def get_by_asin(db: Session, asin: str) -> Product | None:
    return db.execute(select(Product).where(Product.asin == asin)).scalar_one_or_none()


def get_by_asins(db: Session, asins: list[str]) -> dict[str, Product]:
    if not asins:
        return {}
    rows = db.execute(select(Product).where(Product.asin.in_(asins))).scalars().all()
    return {p.asin: p for p in rows}


def is_fresh(product: Product) -> bool:
    """last_updated が有効期限内かどうか。"""
    if product.last_updated is None:
        return False
    expiry = timedelta(hours=settings.product_expiry_hours)
    return (datetime.utcnow() - product.last_updated) < expiry


def upsert_many(db: Session, items: list[ProductData]) -> None:
    """ProductData のリストを asin をキーに upsert し、last_updated を更新する。"""
    if not items:
        return
    now = datetime.utcnow()
    existing = get_by_asins(db, [i.asin for i in items])

    for data in items:
        product = existing.get(data.asin)
        if product is None:
            product = Product(asin=data.asin)
            db.add(product)
        product.jan = data.jan or None
        product.title = data.title
        product.brand = data.brand
        product.category = data.category
        product.image_url = data.image_url
        product.description = data.description
        product.amazon_price = data.amazon_price
        product.currency = data.currency
        product.sales_rank = data.sales_rank
        product.last_updated = now

    db.commit()
