"""Keepa API 連携（トークン節約のため呼び出しを最小化する）。

- search_products(keyword) : キーワード検索（全商品を返すのでそのまま利用）。keyword単位でキャッシュ
- fetch_products(asins)    : /product でまとめて商品詳細を取得（詳細のDB優先/手動更新用）

価格は「対象ロケールの最小通貨単位の整数」。日本(domain=5)は円そのまま、
それ以外は /100。参考: Keepa 公式 Product.java コメント
  price: 4900 => $49.00（domainId=5 の日本なら ¥4900）
"""

import logging
import time

import httpx

from app.config import settings
from app.schemas import ProductData

logger = logging.getLogger("app.keepa")

KEEPA_SEARCH_URL = "https://api.keepa.com/search"
KEEPA_PRODUCT_URL = "https://api.keepa.com/product"
IMAGE_BASE = "https://m.media-amazon.com/images/I/"

# stats.current の CsvType インデックス
_CSV_AMAZON = 0
_CSV_NEW = 1
_CSV_SALES_RANK = 3
_CSV_BUY_BOX = 18

# キーワード検索の短期キャッシュ（同一検索の再消費を防ぐ）
_SEARCH_CACHE_TTL_SEC = 600
_search_cache: dict[tuple[str, int], tuple[float, list["ProductData"]]] = {}


class KeepaTokenError(RuntimeError):
    """Keepa のトークン残量不足など、利用制限に関するエラー。"""


class KeepaError(RuntimeError):
    """Keepa API のその他のエラー。"""


def _currency() -> str:
    return "JPY" if settings.keepa_domain == 5 else "USD"


def _price_to_local(raw: int | None) -> float | None:
    if raw is None or raw < 0:
        return None
    if settings.keepa_domain == 5:
        return float(raw)
    return round(raw / 100, 2)


def _pick_price(current: list[int] | None) -> float | None:
    if not current:
        return None
    for idx in (_CSV_AMAZON, _CSV_NEW, _CSV_BUY_BOX):
        if idx < len(current):
            price = _price_to_local(current[idx])
            if price is not None:
                return price
    return None


def _first_image(product: dict) -> str:
    images = product.get("images")
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, dict):
            name = first.get("l") or first.get("m")
            if name:
                return f"{IMAGE_BASE}{name}"
    images_csv = product.get("imagesCSV")
    if images_csv:
        name = images_csv.split(",")[0].strip()
        if name:
            return f"{IMAGE_BASE}{name}"
    return ""


def _category(product: dict) -> str:
    tree = product.get("categoryTree") or []
    if tree and isinstance(tree[-1], dict):
        return tree[-1].get("name") or ""
    return ""


def _sales_rank(product: dict) -> int | None:
    """現在の売れ筋ランクを返す（stats.current[3]）。無ければ None。"""
    stats = product.get("stats") or {}
    current = stats.get("current")
    if current and _CSV_SALES_RANK < len(current):
        rank = current[_CSV_SALES_RANK]
        if rank is not None and rank > 0:
            return int(rank)
    return None


def _jan(product: dict) -> str:
    for key in ("eanList", "upcList"):
        vals = product.get(key)
        if isinstance(vals, list) and vals:
            return str(vals[0])
    return ""


def _require_key() -> None:
    if not settings.keepa_api_key:
        raise KeepaError("KEEPA_API_KEY が未設定です")


def _get(url: str, params: dict) -> dict:
    params = {"key": settings.keepa_api_key, "domain": settings.keepa_domain, **params}
    try:
        with httpx.Client(timeout=60.0) as client:
            res = client.get(url, params=params)
    except httpx.HTTPError as e:
        raise KeepaError(f"Keepaへの接続に失敗しました: {e}") from e

    if res.status_code == 429:
        raise KeepaTokenError(
            "Keepaのトークン残量が不足しています。残量が回復するまで少し待つか、"
            "プランのトークン数をご確認ください。"
        )
    if res.status_code >= 400:
        raise KeepaError(f"Keepa APIエラー (HTTP {res.status_code})")

    data = res.json()
    logger.info("Keepa %s tokensLeft=%s consumed=%s", url, data.get("tokensLeft"), data.get("tokensConsumed"))
    return data


def search_products(keyword: str, limit: int = 8) -> list[ProductData]:
    """キーワード検索して商品データを返す（keyword単位でキャッシュ）。

    Keepa検索は1ページあたり最大10件程度。limitに達するまでページを進める
    （page 0-9、最大100件）。ページ数だけトークンを消費する点に注意。
    """
    _require_key()
    cache_key = (keyword, limit)
    cached = _search_cache.get(cache_key)
    if cached and (time.time() - cached[0]) < _SEARCH_CACHE_TTL_SEC:
        logger.info("Keepa検索(キャッシュ): keyword=%s", keyword)
        return cached[1]

    items: list[ProductData] = []
    for page in range(0, 10):  # 最大10ページ = 最大100件
        if len(items) >= limit:
            break
        data = _get(
            KEEPA_SEARCH_URL,
            {"type": "product", "term": keyword, "stats": 1, "page": page},
        )
        page_products = data.get("products") or []
        for p in page_products:
            parsed = _parse_product(p)
            if parsed:
                items.append(parsed)
        if len(page_products) < 10:  # これ以上ページが無い
            break

    items = items[:limit]
    _search_cache[cache_key] = (time.time(), items)
    return items


def _parse_product(p: dict) -> ProductData | None:
    asin = p.get("asin")
    if not asin:
        return None
    stats = p.get("stats") or {}
    price = _pick_price(stats.get("current"))
    return ProductData(
        asin=asin,
        jan=_jan(p),
        title=p.get("title") or "",
        brand=p.get("brand") or "",
        category=_category(p),
        image_url=_first_image(p),
        description=p.get("description") or "",
        amazon_price=price if price is not None else 0.0,
        currency=_currency(),
        sales_rank=_sales_rank(p),
    )


def fetch_products(asins: list[str]) -> list[ProductData]:
    """指定ASINの商品詳細をまとめて取得（Keepaは最大100件/リクエスト）。"""
    _require_key()
    if not asins:
        return []

    result: list[ProductData] = []
    for i in range(0, len(asins), 100):
        chunk = asins[i : i + 100]
        data = _get(KEEPA_PRODUCT_URL, {"asin": ",".join(chunk), "stats": 1})
        for p in data.get("products") or []:
            parsed = _parse_product(p)
            if parsed:
                result.append(parsed)
    return result
