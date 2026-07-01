# Amazon → eBay 自動出品システム 実装まとめ

Amazon（Keepa）で商品を取得し、費用対効果でランク付けして eBay へ出品するまでを一気通貫で扱う MVP。
本ドキュメントは Phase1〜10 まで実装した現状の概要と詳細をまとめたもの。

---

## 1. システム概要

| 項目 | 内容 |
| --- | --- |
| フロントエンド | Next.js (App Router) + TypeScript + Tailwind CSS |
| バックエンド | FastAPI (Python 3.11) |
| データベース | MySQL 8 |
| 実行環境 | Docker Compose（`db` / `backend` / `frontend`） |
| 商品データ取得 | Keepa API（amazon.co.jp / domain=5） |
| 英語生成 | OpenAI API（未設定時はモック） |
| 出品先 | eBay Sell API（未設定/TEST_MODE時はモック） |

### 処理の流れ

```
ログイン
  ▼
商品検索（キーワード）
  ▼ Keepa から最大100件取得 → DBへ保存（DB優先キャッシュ）
費用対効果スコアで並び替え・絞り込み
  ▼
商品詳細（利益計算・英語生成）
  ▼
eBay 出品プレビュー（USD価格・送料・画像）
  ▼
出品（listings に記録）
  ▼
商品管理（一覧・状態・利益・更新日）
```

---

## 2. モード切り替えの考え方

各外部サービスは「キー/認証情報の有無」で個別にモック↔実データを切り替える。
`TEST_MODE` は **eBay 実出品の安全装置** として予約している。

| サービス | 実データの条件 | モックの条件 |
| --- | --- | --- |
| Keepa（商品取得） | `KEEPA_API_KEY` あり | キー未設定 |
| OpenAI（英語生成） | `OPENAI_API_KEY` あり | キー未設定 |
| eBay（出品） | `TEST_MODE=false` かつ `EBAY_APP_ID`/`EBAY_CERT_ID` あり | `TEST_MODE=true` または認証情報未設定 |

---

## 3. Keepa 利用方針（トークン節約）

Keepa はトークン消費があるため、**DB優先 + キャッシュ**で呼び出しを最小化する。

- **検索**: キーワード単位で 10 分間のインメモリキャッシュ。ページング（1ページ約10件）で目的件数まで取得し、結果を DB へ upsert。
- **詳細**: まず DB を参照。存在し鮮度内（`PRODUCT_EXPIRY_HOURS`、既定24h）なら Keepa を呼ばない。無い/古い/手動更新のときだけ `/product` を取得して DB 更新。
- **手動更新**: 商品詳細の「最新情報を取得」で `refresh=true`。
- キーは `.env` 管理、呼び出しはエラーハンドリング・ログ出力あり。

---

## 4. 費用対効果スコアリング

海外向けに「売れやすさ × 利益率」で商品を評価する。

- **需要スコア** `demand_score(sales_rank)`: Keepa の売れ筋ランクを 0〜1 に正規化（ランクが小さいほど高い）。
  - 現状は Keepa 売れ筋ランクを需要の代理指標として使用。eBay 連携後に実売データへ差し替え可能な構造。
- **表示スコア** `score = 需要 × 利益率 ×100`（大きいほど有望）。
- **並び替え**: `balanced`(総合) / `demand`(需要) / `profit_rate`(利益率) / `profit_abs`(利益額) / `price`。
- **絞り込み**: 最低利益(円) / 最低利益率(%)。

実装: `backend/app/services/scoring.py`

---

## 5. 利益計算

固定値ベース（単位は円）。eBay 価格は USD 換算も保持。

```
eBay価格 = (Amazon価格 + 送料) / (1 - eBay手数料率 - 目標利益率)
eBay手数料 = eBay価格 × 手数料率
利益 = eBay価格 − Amazon価格 − 送料 − eBay手数料
利益率 = 利益 / eBay価格 × 100
eBay価格(USD) = eBay価格(円) / USD_JPY_RATE
```

既定値: 送料 1,500円 / 手数料率 15% / 目標利益率 20% / 為替 150円。
実装: `backend/app/services/profit.py`

---

## 6. API エンドポイント一覧

| メソッド | パス | 用途 |
| --- | --- | --- |
| GET | `/api/health` | アプリ/DB 疎通確認 |
| POST | `/api/auth/login` | ログイン（admin/admin） |
| POST | `/api/auth/logout` | ログアウト |
| GET | `/api/auth/me` | ログイン中ユーザー取得 |
| GET | `/api/products/search` | 商品検索（`keyword,limit,sort,min_profit,min_profit_rate`） |
| GET | `/api/products/detail/{asin}` | 商品詳細（`refresh`で再取得） |
| POST | `/api/products/translate` | 英語タイトル/説明の生成 |
| GET | `/api/ebay/status` | eBay 接続状態（Phase7） |
| GET | `/api/ebay/preview/{asin}` | 出品プレビュー（Phase8） |
| POST | `/api/ebay/list` | 出品実行（Phase9） |
| GET | `/api/ebay/managed` | 商品管理一覧（Phase10） |

### エラーハンドリング

- Keepa トークン不足 → HTTP 429、その他 Keepa 失敗 → HTTP 502（CORS ヘッダ付きで返す）。
- eBay 失敗 → HTTP 502。認証エラーは 401。

---

## 7. データベース構成

### products

| カラム | 説明 |
| --- | --- |
| id | 主キー |
| asin | ASIN（UNIQUE / INDEX） |
| jan | JANコード |
| title / brand / category | 商品情報 |
| image_url / description | 画像URL / 説明 |
| amazon_price / currency | 価格 / 通貨 |
| sales_rank | 売れ筋ランク |
| last_updated | Keepa 最終取得時刻（鮮度判定・INDEX） |
| created_at / updated_at | 作成/更新 |

### listings

| カラム | 説明 |
| --- | --- |
| id | 主キー |
| product_id | products への外部キー |
| ebay_item_id | eBay アイテムID（モックは `MOCK-xxxx`） |
| listing_status | `not_listed` / `pending` / `listed` |
| ebay_price_usd | 出品価格(USD) |
| title_en | 出品タイトル（英語） |
| is_mock | モック出品かどうか |
| listed_at / updated_at | 出品/更新時刻 |

DDL: `database/init.sql`

---

## 8. 画面構成（フロントエンド）

| ルート | 画面 | 機能 |
| --- | --- | --- |
| `/login` | ログイン | admin/admin で認証 |
| `/` | ホーム | フェーズ進捗一覧 |
| `/search` | 商品検索 | 件数/並び替え/絞り込み、スコア・ランク表示、`sessionStorage`で結果保持 |
| `/products/[asin]` | 商品詳細 | 利益内訳、最新取得、英語生成、出品プレビュー→出品 |
| `/manage` | 商品管理 | DB商品一覧、eBay接続バッジ、出品状態・利益・更新日 |

---

## 9. ディレクトリ構成

```
autoEbay/
├─ docker-compose.yml
├─ database/init.sql
├─ backend/
│  ├─ app/
│  │  ├─ main.py            # FastAPI 起動・ルーター登録・health
│  │  ├─ config.py          # 設定（.env）
│  │  ├─ database.py        # DB接続・セッション
│  │  ├─ models.py          # Product / Listing（ORM）
│  │  ├─ schemas.py         # Pydantic スキーマ
│  │  ├─ auth.py            # Cookie セッション認証
│  │  ├─ routers/           # auth / products / ebay
│  │  ├─ services/          # keepa / amazon(mock) / catalog / profit / scoring / translate / ebay
│  │  └─ repositories/      # product_repo / listing_repo
│  ├─ requirements.txt / Dockerfile / .env(.example)
└─ frontend/
   └─ src/
      ├─ app/               # login / (home) / search / products/[asin] / manage
      ├─ components/AppHeader.tsx
      └─ lib/               # api / auth / useAuth / products / ebay
```

主な責務分離:
- `services/keepa.py` … Keepa API 呼び出し・パース・キャッシュ
- `services/amazon.py` … Keepa キー未設定時のモック商品生成
- `services/catalog.py` … 取得オーケストレーション（DB優先 + Keepa最小呼び出し）
- `services/profit.py` … 利益計算（USD換算含む）
- `services/scoring.py` … 費用対効果スコア
- `services/ebay.py` … 接続確認・プレビュー生成・出品（mock/実）
- `repositories/*` … DB アクセス（取得・upsert・鮮度判定）

---

## 10. 環境変数（`.env`）

```
TEST_MODE=true              # eBay 実出品の安全装置
DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME
FRONTEND_ORIGIN=http://localhost:3000
ADMIN_USERNAME=admin / ADMIN_PASSWORD=admin / SESSION_SECRET=...
KEEPA_API_KEY=...           # あれば実データ
KEEPA_DOMAIN=5              # 5=amazon.co.jp
OPENAI_API_KEY=             # あれば実翻訳
EBAY_APP_ID= / EBAY_CERT_ID= / EBAY_DEV_ID= / EBAY_OAUTH_TOKEN=
EBAY_ENV=sandbox           # sandbox / production
USD_JPY_RATE=150           # eBay価格のUSD換算
```

---

## 11. 起動・確認手順

```bash
# 起動（DBスキーマ変更時は -v で作り直し）
docker compose up -d --build

# 疎通確認
curl localhost:8000/api/health

# ログイン → 検索 → 出品プレビュー → 出品 → 管理 の一連は
# フロント http://localhost:3000 から操作
```

動作確認済み（実データ疎通）:
- ログイン / eBay接続(mock) / Keepa実データ検索(スコア順・USD価格) /
  プレビュー / モック出品(item_id発行) / 管理一覧への `listed` 反映。

---

## 12. フェーズ進捗

| Phase | 内容 | 状態 |
| --- | --- | --- |
| 1 | 環境構築（Docker/DB/骨組み） | 完了 |
| 2 | 簡易ログイン・管理UI | 完了 |
| 3 | Amazon(Keepa)商品検索・一覧 | 完了 |
| 4 | 利益計算 | 完了 |
| 5 | 商品詳細 | 完了 |
| 6 | 英語タイトル/説明生成 | 完了 |
| 7 | eBay API 接続確認 | 完了（mock、実は認証設定で有効化） |
| 8 | 出品プレビュー | 完了 |
| 9 | eBay 出品 | 完了（mock、実出品は誤出品防止で無効化中） |
| 10 | 商品管理 | 完了 |
| + | 大量取得(100件)・費用対効果スコア・USD換算 | 完了 |

---

## 13. 今後のTODO（実運用に向けて）

- **eBay 実出品の有効化**: eBay Developer 登録 → `EBAY_APP_ID`/`CERT_ID`/`OAUTH_TOKEN` 設定 → 接続確認 → `services/ebay.py` の `create_listing` に在庫→オファー→公開の実処理を実装。
- **需要判定の高度化**: `scoring.py` の `demand_score` を eBay 実売データ（販売履歴・ウォッチ数など）へ差し替え。
- **為替の自動取得**: `USD_JPY_RATE` を外部レートAPIで動的化。
- **定期更新バッチ**: Cloud Scheduler → 期限切れ商品を Keepa 再取得（DB優先方針の運用面）。
- **本番デプロイ**: Cloud Run + Cloud SQL 等への展開。
