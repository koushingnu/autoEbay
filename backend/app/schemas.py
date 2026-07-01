from datetime import datetime

from pydantic import BaseModel


class ProductData(BaseModel):
    """取得元（Keepa/モック）が返す内部用の商品データ。DB保存の単位。"""

    asin: str
    jan: str = ""
    title: str = ""
    brand: str = ""
    category: str = ""
    image_url: str = ""
    description: str = ""
    amazon_price: float = 0.0
    currency: str = "JPY"
    sales_rank: int | None = None  # 売れ筋ランク（小さいほど売れている）


class AmazonProduct(BaseModel):
    """API応答用の商品情報（検索結果の1件）。"""

    asin: str
    title: str
    amazon_price: float
    image: str
    brand: str
    description: str = ""
    category: str = ""
    sales_rank: int | None = None


class ProfitInfo(BaseModel):
    """利益計算の結果（単位は円、eBay価格はUSD換算も持つ）。"""

    shipping: int          # 送料
    ebay_fee: int          # eBay手数料
    ebay_price: int        # eBay販売価格(円)
    ebay_price_usd: float  # eBay販売価格(USD換算)
    profit: int            # 利益(円)
    profit_rate: float     # 利益率(%)


class ProductWithProfit(AmazonProduct):
    """商品情報 + 利益計算 + 費用対効果スコア。"""

    profit: ProfitInfo
    score: float = 0.0  # 費用対効果スコア（大きいほど有望）


class ProductSearchResponse(BaseModel):
    keyword: str
    mock: bool  # モックデータかどうか（Keepaキー未設定）
    count: int
    items: list[ProductWithProfit]


class ProductDetailResponse(BaseModel):
    mock: bool
    last_updated: datetime | None
    product: ProductWithProfit


class TranslateRequest(BaseModel):
    title: str
    description: str = ""


class TranslateResponse(BaseModel):
    title_en: str
    description_en: str
    mock: bool  # モック翻訳かどうか（TEST_MODE または キー未設定）


# ---- eBay ----


class EbayStatusResponse(BaseModel):
    connected: bool
    mock: bool
    env: str
    message: str


class ListingPreview(BaseModel):
    asin: str
    title: str
    description: str
    image_url: str
    price_usd: float
    shipping_usd: float
    category: str
    condition: str
    currency: str


class PreviewResponse(BaseModel):
    mock: bool
    preview: ListingPreview


class ListRequest(BaseModel):
    asin: str
    title_en: str = ""
    description_en: str = ""


class ListResponse(BaseModel):
    mock: bool
    ebay_item_id: str
    listing_status: str
    ebay_price_usd: float


class ManagedProduct(BaseModel):
    asin: str
    title: str
    image: str
    amazon_price: float
    ebay_price: int
    ebay_price_usd: float
    profit: int
    profit_rate: float
    sales_rank: int | None = None
    listing_status: str  # not_listed / listed / pending
    ebay_item_id: str | None = None
    is_mock: bool | None = None
    last_updated: datetime | None = None


class ManagedListResponse(BaseModel):
    count: int
    items: list[ManagedProduct]
