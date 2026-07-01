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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


settings = Settings()
