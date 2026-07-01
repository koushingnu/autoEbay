from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリ全体の設定。環境変数(.env)から読み込む。"""

    # 動作モード: True の場合は eBay など外部APIを呼ばずJSON生成で完結させる
    test_mode: bool = True

    # データベース接続
    db_host: str = "db"
    db_port: int = 3306
    db_user: str = "app"
    db_password: str = "app_password"
    db_name: str = "amazon_ebay"

    # CORS 許可オリジン（フロントエンド）
    frontend_origin: str = "http://localhost:3000"

    # 簡易ログイン（単一ユーザー想定）
    admin_username: str = "admin"
    admin_password: str = "admin"
    session_secret: str = "change-me-in-env"
    session_cookie_name: str = "ae_session"

    # Keepa API（Amazon商品取得に使用）
    keepa_api_key: str = ""
    keepa_domain: int = 5  # 5 = amazon.co.jp（日本）
    product_expiry_hours: int = 24  # この時間を過ぎたDB商品は古いとみなし再取得

    # 利益計算（MVPは固定値。単位は円）
    shipping_cost: int = 1500        # 国際送料（固定）
    ebay_fee_rate: float = 0.15      # eBay手数料率
    target_profit_rate: float = 0.20  # 目標利益率
    usd_jpy_rate: float = 150.0       # 為替(1USD=xxJPY)。eBay価格のUSD換算に使用

    # eBay API
    ebay_app_id: str = ""       # Client ID
    ebay_cert_id: str = ""      # Client Secret
    ebay_dev_id: str = ""
    ebay_oauth_token: str = ""  # ユーザートークン(Sell API用)
    ebay_env: str = "sandbox"   # sandbox / production

    # AI 翻訳（英語タイトル/説明生成）
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


settings = Settings()
