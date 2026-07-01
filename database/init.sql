-- Amazon → eBay 自動出品システム 初期スキーマ

CREATE DATABASE IF NOT EXISTS amazon_ebay CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE amazon_ebay;

-- 商品キャッシュ（Keepa取得結果を保存し、DB優先で参照する）
CREATE TABLE IF NOT EXISTS products (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    asin         VARCHAR(20) NOT NULL,
    jan          VARCHAR(20),
    title        VARCHAR(512),
    brand        VARCHAR(255),
    category     VARCHAR(255),
    image_url    VARCHAR(1024),
    description  TEXT,
    amazon_price DECIMAL(12, 2),
    currency     VARCHAR(8) DEFAULT 'JPY',
    sales_rank   INT,                                        -- 売れ筋ランク（小さいほど売れている）
    last_updated DATETIME,                                   -- Keepaから取得した最終時刻
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_asin (asin),
    KEY idx_last_updated (last_updated)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS listings (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id     BIGINT NOT NULL,
    ebay_item_id   VARCHAR(64),
    listing_status VARCHAR(32) DEFAULT 'pending',
    ebay_price_usd DECIMAL(12, 2),
    title_en       VARCHAR(512),
    is_mock        TINYINT(1) DEFAULT 1,
    listed_at      DATETIME,
    updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_listings_product FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS logs (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    type       VARCHAR(32),
    message    TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
