-- Amazon → eBay 自動出品システム 初期スキーマ

CREATE DATABASE IF NOT EXISTS amazon_ebay CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE amazon_ebay;

CREATE TABLE IF NOT EXISTS products (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    asin         VARCHAR(20) NOT NULL,
    title        VARCHAR(512),
    description  TEXT,
    amazon_price DECIMAL(12, 2),
    ebay_price   DECIMAL(12, 2),
    profit       DECIMAL(12, 2),
    profit_rate  DECIMAL(6, 2),
    brand        VARCHAR(255),
    category     VARCHAR(255),
    image        VARCHAR(1024),
    status       VARCHAR(32) DEFAULT 'draft',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_asin (asin)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS listings (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id     BIGINT NOT NULL,
    ebay_item_id   VARCHAR(64),
    listing_status VARCHAR(32) DEFAULT 'pending',
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
