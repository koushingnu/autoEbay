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

_OAUTH_URLS = {
    "sandbox": "https://api.sandbox.ebay.com/identity/v1/oauth2/token",
    "production": "https://api.ebay.com/identity/v1/oauth2/token",
}
_SCOPE = "https://api.ebay.com/oauth/api_scope"


class EbayError(RuntimeError):
    """eBay API 呼び出し失敗。"""


def is_mock() -> bool:
    """モードがモックか（TEST_MODE か 認証情報未設定）。"""
    has_creds = bool(settings.ebay_app_id and settings.ebay_cert_id)
    return settings.test_mode or not has_creds


def _oauth_token() -> str:
    """client_credentials で application token を取得（実API接続確認用）。"""
    url = _OAUTH_URLS.get(settings.ebay_env, _OAUTH_URLS["sandbox"])
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
        "condition": "NEW",
        "currency": "USD",
    }


def create_listing(preview: dict) -> tuple[str, bool]:
    """出品を実行し (ebay_item_id, is_mock) を返す。"""
    if is_mock():
        rand = "".join(random.choices(string.digits, k=12))
        item_id = f"MOCK-{rand}"
        logger.info("モック出品: asin=%s item_id=%s", preview.get("asin"), item_id)
        return item_id, True

    # 実出品（eBay Sell API）は inventory item→offer→publish の手順が必要。
    # 認証情報・在庫ロケーション・各種ポリシー設定が前提のため、
    # 準備が整うまでは実行を止める（誤出品防止）。
    raise EbayError(
        "実出品はまだ有効化されていません。TEST_MODE=false と eBay Sell API の"
        "在庫ロケーション/ポリシー設定を行ってから実装を有効化してください。"
    )
