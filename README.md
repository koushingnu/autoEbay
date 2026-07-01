# Amazon → eBay 自動出品システム (MVP)

Amazonの商品情報を取得し、利益計算を行い、条件を満たした商品をeBayへ手動出品できるWebアプリ。
開発手順は [`production.md`](./production.md) を参照。

## 技術構成

- Frontend: Next.js / TypeScript / Tailwind CSS
- Backend: Python / FastAPI
- Database: MySQL 8.0
- 実行環境: Docker Compose（将来的に Cloud Run）

## ディレクトリ構成

```
autoEbay/
├── frontend/          # Next.js
├── backend/           # FastAPI
│   └── app/
├── database/          # init.sql (スキーマ)
├── docker-compose.yml
└── production.md      # 開発手順書
```

## セットアップ

### 1. 環境変数

```bash
cp backend/.env.example backend/.env
# 必要に応じて frontend/.env.local を編集
```

### 2. Docker で起動

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend:  http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health:   http://localhost:8000/api/health

### ローカル (Docker を使わない場合)

Backend:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# DB_HOST=127.0.0.1 に変更した .env を用意して実行
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## 開発フェーズ

`production.md` の Phase1〜Phase10 に沿って1機能ずつ実装する。

- [x] Phase1: 環境構築
- [ ] Phase2: ログイン(簡易)・管理画面
- [ ] Phase3: Amazon商品検索・一覧表示
- [ ] Phase4: 利益計算
- [ ] Phase5: 商品詳細画面
- [ ] Phase6: 英語タイトル/説明生成
- [ ] Phase7: eBay API接続確認
- [ ] Phase8: 出品プレビュー
- [ ] Phase9: eBay出品(手動)
- [ ] Phase10: 商品管理画面

## テストモード

`TEST_MODE=true` の場合、eBay等の外部APIは呼ばず、生成データをJSONで確認して終了する。
本番出品時のみ `TEST_MODE=false` にする。
