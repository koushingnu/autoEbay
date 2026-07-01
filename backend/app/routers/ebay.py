"""eBay 連携エンドポイント（Phase7-9）+ 商品管理（Phase10）。"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Product
from app.repositories import listing_repo
from app.schemas import (
    EbayStatusResponse,
    ListingPreview,
    ListRequest,
    ListResponse,
    ManagedListResponse,
    ManagedProduct,
    PreviewResponse,
)
from app.services import catalog, ebay, profit

logger = logging.getLogger("app.ebay_router")

router = APIRouter(prefix="/api/ebay", tags=["ebay"])


@router.get("/status", response_model=EbayStatusResponse)
def ebay_status(_user: str = Depends(get_current_user)):
    return EbayStatusResponse(**ebay.status())


@router.get("/preview/{asin}", response_model=PreviewResponse)
def preview(
    asin: str,
    db: Session = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    product, _ = catalog.get_detail(db, asin, refresh=False)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品が見つかりません")

    info = profit.calculate(float(product.amazon_price or 0))
    # 英語タイトル・説明はフロントで翻訳済みを渡す想定。無ければ日本語をそのまま。
    payload = ebay.build_preview(
        asin=product.asin,
        title_en=product.title or "",
        description_en=product.description or "",
        image_url=product.image_url or "",
        ebay_price_usd=info.ebay_price_usd,
        shipping_jpy=info.shipping,
        category=product.category or "",
    )
    return PreviewResponse(mock=ebay.is_mock(), preview=ListingPreview(**payload))


@router.post("/list", response_model=ListResponse)
def create_listing(
    payload: ListRequest,
    db: Session = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    product, _ = catalog.get_detail(db, payload.asin, refresh=False)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品が見つかりません")

    info = profit.calculate(float(product.amazon_price or 0))
    title_en = payload.title_en or product.title or ""
    description_en = payload.description_en or product.description or ""
    preview_payload = ebay.build_preview(
        asin=product.asin,
        title_en=title_en,
        description_en=description_en,
        image_url=product.image_url or "",
        ebay_price_usd=info.ebay_price_usd,
        shipping_jpy=info.shipping,
        category=product.category or "",
    )

    try:
        item_id, is_mock = ebay.create_listing(preview_payload)
    except ebay.EbayError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    listing = listing_repo.upsert(
        db,
        product_id=product.id,
        ebay_item_id=item_id,
        listing_status="listed",
        ebay_price_usd=info.ebay_price_usd,
        title_en=title_en,
        is_mock=is_mock,
    )
    logger.info("出品完了: asin=%s item_id=%s mock=%s", product.asin, item_id, is_mock)

    return ListResponse(
        mock=is_mock,
        ebay_item_id=listing.ebay_item_id or "",
        listing_status=listing.listing_status,
        ebay_price_usd=float(listing.ebay_price_usd or 0),
    )


@router.get("/managed", response_model=ManagedListResponse)
def managed_products(
    db: Session = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    """DBの商品一覧と出品状態を返す（Phase10 商品管理）。"""
    products = db.execute(select(Product).order_by(Product.updated_at.desc())).scalars().all()
    listings = listing_repo.get_map_by_product_ids(db, [p.id for p in products])

    items: list[ManagedProduct] = []
    for p in products:
        info = profit.calculate(float(p.amazon_price or 0))
        listing = listings.get(p.id)
        items.append(
            ManagedProduct(
                asin=p.asin,
                title=p.title or "",
                image=p.image_url or "",
                amazon_price=float(p.amazon_price or 0),
                ebay_price=info.ebay_price,
                ebay_price_usd=info.ebay_price_usd,
                profit=info.profit,
                profit_rate=info.profit_rate,
                sales_rank=p.sales_rank,
                listing_status=listing.listing_status if listing else "not_listed",
                ebay_item_id=listing.ebay_item_id if listing else None,
                is_mock=listing.is_mock if listing else None,
                last_updated=p.last_updated,
            )
        )

    return ManagedListResponse(count=len(items), items=items)
