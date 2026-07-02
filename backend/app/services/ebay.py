"""eBay 連携サービス。

方針（他サービスと同じ）:
  - TEST_MODE=true もしくは 認証情報が未設定 → モック（実出品しない・安全）
  - TEST_MODE=false かつ 認証情報あり           → eBay 実API

Phase7: 接続確認 status()
Phase8: 出品プレビュー build_preview()
Phase9: 出品 create_listing()（モックは擬似成功、実は Sell API）
"""

import logging
import random
import string

import httpx

from app.config import settings

logger = logging.getLogger("app.ebay")

_API_BASE = {
    "sandbox": "https://api.sandbox.ebay.com",
    "production": "https://api.ebay.com",
}
_SCOPE = "https://api.ebay.com/oauth/api_scope"


def _base() -> str:
    return _API_BASE.get(settings.ebay_env, _API_BASE["sandbox"])


class EbayError(RuntimeError):
    """eBay API 呼び出し失敗。"""


def is_mock() -> bool:
    """モードがモックか（TEST_MODE か 認証情報未設定）。"""
    has_creds = bool(settings.ebay_app_id and settings.ebay_cert_id)
    return settings.test_mode or not has_creds


def _oauth_token() -> str:
    """client_credentials で application token を取得（実API接続確認用）。"""
    url = f"{_base()}/identity/v1/oauth2/token"
    try:
        resp = httpx.post(
            url,
            auth=(settings.ebay_app_id, settings.ebay_cert_id),
            data={"grant_type": "client_credentials", "scope": _SCOPE},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15.0,
        )
    except httpx.HTTPError as e:
        raise EbayError(f"eBayへの接続に失敗しました: {e}") from e

    if resp.status_code != 200:
        raise EbayError(f"eBay認証に失敗しました({resp.status_code}): {resp.text[:200]}")
    token = resp.json().get("access_token")
    if not token:
        raise EbayError("eBayのアクセストークンを取得できませんでした")
    return token


def status() -> dict:
    """接続状態を返す。{connected, mock, env, message}"""
    if is_mock():
        return {
            "connected": True,
            "mock": True,
            "env": settings.ebay_env,
            "message": "モックモード（TEST_MODEまたは認証情報未設定）。実際の出品は行いません。",
        }
    try:
        _oauth_token()
        return {
            "connected": True,
            "mock": False,
            "env": settings.ebay_env,
            "message": f"eBay({settings.ebay_env})に接続できました。",
        }
    except EbayError as e:
        return {
            "connected": False,
            "mock": False,
            "env": settings.ebay_env,
            "message": str(e),
        }


def build_preview(
    *,
    asin: str,
    title_en: str,
    description_en: str,
    image_url: str,
    ebay_price_usd: float,
    shipping_jpy: int,
    category: str,
    brand: str = "",
) -> dict:
    """出品プレビュー用のペイロードを組み立てる。"""
    shipping_usd = (
        round(shipping_jpy / settings.usd_jpy_rate, 2) if settings.usd_jpy_rate > 0 else 0.0
    )
    return {
        "asin": asin,
        "title": title_en,
        "description": description_en,
        "image_url": image_url,
        "price_usd": ebay_price_usd,
        "shipping_usd": shipping_usd,
        "category": category,
        "brand": brand or "Unbranded",
        "condition": "NEW",
        "currency": "USD",
    }


# ---- Sell API 実出品ヘルパー ----


def _sell_headers() -> dict:
    """Sell API 用ヘッダー（ユーザートークン）。"""
    if not settings.ebay_oauth_token:
        raise EbayError(
            "EBAY_OAUTH_TOKEN（ユーザートークン）が未設定です。出品には本人同意の"
            "User token が必要です。"
        )
    return {
        "Authorization": f"Bearer {settings.ebay_oauth_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Content-Language": "en-US",
        "X-EBAY-C-MARKETPLACE-ID": settings.ebay_marketplace_id,
    }


def _request(method: str, path: str, *, json=None, params=None) -> httpx.Response:
    """Sell API 呼び出し。失敗時は EbayError。"""
    url = f"{_base()}{path}"
    try:
        resp = httpx.request(
            method,
            url,
            headers=_sell_headers(),
            json=json,
            params=params,
            timeout=30.0,
        )
    except httpx.HTTPError as e:
        raise EbayError(f"eBay API 通信エラー: {e}") from e

    if resp.status_code >= 400:
        raise EbayError(
            f"eBay API エラー {resp.status_code} [{method} {path}]: {resp.text[:400]}"
        )
    return resp


def _ensure_location() -> str:
    """在庫ロケーションを確認し、無ければ作成してキーを返す。

    sandbox は GET が一時的に 500 を返すことがあるため、取得失敗時も作成を試みる。
    既に存在する場合のエラーは無視する。
    """
    key = settings.ebay_merchant_location_key
    try:
        resp = _request("GET", "/sell/inventory/v1/location", params={"limit": 100})
        for loc in resp.json().get("locations", []):
            if loc.get("merchantLocationKey") == key:
                return key
    except EbayError as e:
        logger.warning("ロケーション取得に失敗（作成を試行）: %s", e)

    body = {
        "location": {
            "address": {
                "addressLine1": "1 Main St",
                "city": "San Jose",
                "stateOrProvince": "CA",
                "postalCode": "95131",
                "country": "US",
            }
        },
        "locationInstructions": "Auto-created by autoEbay",
        "name": "autoEbay Warehouse",
        "merchantLocationStatus": "ENABLED",
        "locationTypes": ["WAREHOUSE"],
    }
    try:
        _request("POST", f"/sell/inventory/v1/location/{key}", json=body)
        logger.info("在庫ロケーションを作成: %s", key)
    except EbayError as e:
        # 既に存在する場合(25801等)は無視。それ以外は再送出。
        if "already exists" in str(e).lower() or "25801" in str(e):
            logger.info("在庫ロケーションは既存: %s", key)
        else:
            raise
    return key


_CATEGORY_TYPES = [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}]


def _default_policy_body(kind: str) -> dict:
    """未作成時に作る最小ポリシー本文（EBAY_US 想定）。"""
    mkt = settings.ebay_marketplace_id
    if kind == "fulfillment":
        return {
            "name": "autoEbay-fulfillment",
            "marketplaceId": mkt,
            "categoryTypes": _CATEGORY_TYPES,
            "handlingTime": {"unit": "DAY", "value": 3},
            "shippingOptions": [
                {
                    "optionType": "DOMESTIC",
                    "costType": "FLAT_RATE",
                    "shippingServices": [
                        {
                            "sortOrder": 1,
                            "shippingCarrierCode": "USPS",
                            "shippingServiceCode": "USPSPriority",
                            "shippingCost": {"value": "0.00", "currency": settings.ebay_currency},
                            "freeShipping": True,
                        }
                    ],
                }
            ],
        }
    if kind == "payment":
        return {
            "name": "autoEbay-payment",
            "marketplaceId": mkt,
            "categoryTypes": _CATEGORY_TYPES,
        }
    # return
    return {
        "name": "autoEbay-return",
        "marketplaceId": mkt,
        "categoryTypes": _CATEGORY_TYPES,
        "returnsAccepted": False,
    }


def _policy_id(kind: str, configured: str) -> str:
    """business policy ID を取得。設定済み→それ、既存あり→先頭、無し→自動作成。

    kind: "fulfillment" / "payment" / "return"
    """
    if configured:
        return configured
    path = f"/sell/account/v1/{kind}_policy"
    resp = _request("GET", path, params={"marketplace_id": settings.ebay_marketplace_id})
    policies = resp.json().get(f"{kind}Policies", [])
    if policies:
        return policies[0][f"{kind}PolicyId"]

    # 無ければ既定ポリシーを作成
    created = _request("POST", path, json=_default_policy_body(kind))
    pid = created.json().get(f"{kind}PolicyId")
    if not pid:
        raise EbayError(f"{kind} ポリシーの作成に失敗しました: {created.text[:200]}")
    logger.info("%s ポリシーを自動作成: %s", kind, pid)
    return pid


_tree_id_cache: str | None = None
_aspects_cache: dict[str, dict] = {}


def _category_tree_id() -> str:
    """マーケットプレイスの既定カテゴリツリーIDを取得（キャッシュ）。"""
    global _tree_id_cache
    if _tree_id_cache:
        return _tree_id_cache
    resp = _request(
        "GET",
        "/commerce/taxonomy/v1/get_default_category_tree_id",
        params={"marketplace_id": settings.ebay_marketplace_id},
    )
    _tree_id_cache = resp.json()["categoryTreeId"]
    return _tree_id_cache


def _required_aspects(category_id: str, brand: str) -> dict:
    """カテゴリの必須 Item Specifics を取得し、値を自動補完して返す。

    Brand は商品ブランド、選択肢がある必須項目は先頭候補、その他は "Does Not Apply"。
    """
    if category_id in _aspects_cache:
        base = dict(_aspects_cache[category_id])
    else:
        tree = _category_tree_id()
        resp = _request(
            "GET",
            f"/commerce/taxonomy/v1/category_tree/{tree}/get_item_aspects_for_category",
            params={"category_id": category_id},
        )
        base = {}
        for a in resp.json().get("aspects", []):
            con = a.get("aspectConstraint", {}) or {}
            if not con.get("aspectRequired"):
                continue
            name = a.get("localizedAspectName")
            values = a.get("aspectValues") or []
            if values:
                base[name] = [values[0].get("localizedValue")]
            else:
                base[name] = ["Does Not Apply"]
        _aspects_cache[category_id] = dict(base)

    base["Brand"] = [brand or "Unbranded"]
    return base


def _create_inventory_item(preview: dict) -> str:
    """在庫アイテムを登録し SKU を返す。"""
    sku = preview["asin"]
    title = (preview.get("title") or "")[:80]  # eBay タイトルは80文字まで
    image = preview.get("image_url")
    brand = preview.get("brand") or "Unbranded"
    aspects = _required_aspects(settings.ebay_category_id, brand)
    body = {
        "availability": {"shipToLocationAvailability": {"quantity": 1}},
        "condition": preview.get("condition", "NEW"),
        "product": {
            "title": title or sku,
            "description": preview.get("description") or title or sku,
            "imageUrls": [image] if image else [],
            "aspects": aspects,
        },
    }
    _request("PUT", f"/sell/inventory/v1/inventory_item/{sku}", json=body)
    return sku


def _create_offer(preview: dict, sku: str) -> str:
    """オファーを作成し offerId を返す。既存があれば再利用。"""
    price = f"{float(preview.get('price_usd') or 0):.2f}"
    body = {
        "sku": sku,
        "marketplaceId": settings.ebay_marketplace_id,
        "format": "FIXED_PRICE",
        "availableQuantity": 1,
        "categoryId": settings.ebay_category_id,
        "listingDescription": preview.get("description") or preview.get("title") or sku,
        "listingPolicies": {
            "fulfillmentPolicyId": _policy_id("fulfillment", settings.ebay_fulfillment_policy_id),
            "paymentPolicyId": _policy_id("payment", settings.ebay_payment_policy_id),
            "returnPolicyId": _policy_id("return", settings.ebay_return_policy_id),
        },
        "pricingSummary": {
            "price": {"value": price, "currency": settings.ebay_currency}
        },
        "merchantLocationKey": settings.ebay_merchant_location_key,
    }
    try:
        resp = _request("POST", "/sell/inventory/v1/offer", json=body)
        return resp.json()["offerId"]
    except EbayError as e:
        # 既に同一SKUのオファーがある場合は取得して再利用
        if "25002" in str(e) or "already exists" in str(e).lower():
            got = _request(
                "GET",
                "/sell/inventory/v1/offer",
                params={"sku": sku, "marketplace_id": settings.ebay_marketplace_id},
            )
            offers = got.json().get("offers", [])
            if offers:
                return offers[0]["offerId"]
        raise


def create_listing(preview: dict) -> tuple[str, bool]:
    """出品を実行し (ebay_item_id, is_mock) を返す。

    モック: 擬似ID。実: eBay Sell API で inventory→offer→publish。
    """
    if is_mock():
        rand = "".join(random.choices(string.digits, k=12))
        item_id = f"MOCK-{rand}"
        logger.info("モック出品: asin=%s item_id=%s", preview.get("asin"), item_id)
        return item_id, True

    _ensure_location()
    sku = _create_inventory_item(preview)
    offer_id = _create_offer(preview, sku)
    resp = _request("POST", f"/sell/inventory/v1/offer/{offer_id}/publish")
    listing_id = resp.json().get("listingId", offer_id)
    logger.info("eBay出品完了: sku=%s offer=%s listing=%s", sku, offer_id, listing_id)
    return listing_id, False
