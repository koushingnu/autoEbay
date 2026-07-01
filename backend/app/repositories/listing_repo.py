"""出品(listings)テーブルへのアクセス。"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Listing


def get_by_product_id(db: Session, product_id: int) -> Listing | None:
    return db.execute(
        select(Listing).where(Listing.product_id == product_id)
    ).scalar_one_or_none()


def get_map_by_product_ids(db: Session, product_ids: list[int]) -> dict[int, Listing]:
    if not product_ids:
        return {}
    rows = (
        db.execute(select(Listing).where(Listing.product_id.in_(product_ids)))
        .scalars()
        .all()
    )
    return {r.product_id: r for r in rows}


def upsert(
    db: Session,
    *,
    product_id: int,
    ebay_item_id: str,
    listing_status: str,
    ebay_price_usd: float,
    title_en: str,
    is_mock: bool,
) -> Listing:
    listing = get_by_product_id(db, product_id)
    if listing is None:
        listing = Listing(product_id=product_id)
        db.add(listing)
    listing.ebay_item_id = ebay_item_id
    listing.listing_status = listing_status
    listing.ebay_price_usd = ebay_price_usd
    listing.title_en = title_en
    listing.is_mock = is_mock
    listing.listed_at = datetime.utcnow()
    db.commit()
    db.refresh(listing)
    return listing
