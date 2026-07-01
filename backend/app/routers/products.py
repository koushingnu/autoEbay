import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Product
from app.schemas import (
    AmazonProduct,
    ProductDetailResponse,
    ProductSearchResponse,
    ProductWithProfit,
    TranslateRequest,
    TranslateResponse,
)
from app.services import catalog, profit, scoring, translate
from app.services.keepa import KeepaError, KeepaTokenError

logger = logging.getLogger("app.products")

router = APIRouter(prefix="/api/products", tags=["products"])


def _to_with_profit(p: Product) -> ProductWithProfit:
    price = float(p.amazon_price or 0)
    info = profit.calculate(price)
    base = AmazonProduct(
        asin=p.asin,
        title=p.title or "",
        amazon_price=price,
        image=p.image_url or "",
        brand=p.brand or "",
        description=p.description or "",
        category=p.category or "",
        sales_rank=p.sales_rank,
    )
    return ProductWithProfit(
        **base.model_dump(),
        profit=info,
        score=scoring.cost_effectiveness(info, p.sales_rank),
    )


@router.get("/search", response_model=ProductSearchResponse)
def search(
    keyword: str = Query(..., min_length=1, description="検索キーワード"),
    limit: int = Query(50, ge=1, le=100),
    sort: str = Query("balanced", description="balanced/demand/profit_rate/profit_abs/price"),
    min_profit: int = Query(0, ge=0, description="最低利益(円)で絞り込み"),
    min_profit_rate: float = Query(0.0, ge=0, description="最低利益率(%)で絞り込み"),
    db: Session = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    try:
        products, is_mock = catalog.search(db, keyword, limit)
    except KeepaTokenError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except (KeepaError, NotImplementedError) as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    items = [_to_with_profit(p) for p in products]
    items = [
        it
        for it in items
        if it.profit.profit >= min_profit and it.profit.profit_rate >= min_profit_rate
    ]
    items.sort(key=lambda it: scoring.sort_key(it, sort), reverse=True)

    return ProductSearchResponse(
        keyword=keyword, mock=is_mock, count=len(items), items=items
    )


@router.get("/detail/{asin}", response_model=ProductDetailResponse)
def detail(
    asin: str,
    refresh: bool = Query(False, description="Trueでキャッシュを無視してKeepa再取得"),
    db: Session = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    try:
        product, is_mock = catalog.get_detail(db, asin, refresh)
    except KeepaTokenError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except (KeepaError, NotImplementedError) as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="商品が見つかりませんでした"
        )

    return ProductDetailResponse(
        mock=is_mock,
        last_updated=product.last_updated,
        product=_to_with_profit(product),
    )


@router.post("/translate", response_model=TranslateResponse)
def translate_product(
    payload: TranslateRequest,
    _user: str = Depends(get_current_user),
):
    try:
        title_en, description_en, is_mock = translate.translate(
            payload.title, payload.description
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"翻訳に失敗しました: {e}",
        )

    return TranslateResponse(
        title_en=title_en, description_en=description_en, mock=is_mock
    )
