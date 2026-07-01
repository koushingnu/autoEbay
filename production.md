Amazon → eBay 自動出品システム 開発手順書（MVP）

1. プロジェクト概要

目的

Amazonの商品情報を取得し、利益計算を行い、条件を満たした商品をeBayへ出品できるWebアプリを開発する。

最終的にはCloud Schedulerによる自動実行を目指すが、まずはWebアプリ上から手動で操作・テストできるMVPを完成させる。

⸻

2. 技術構成

Frontend

* Next.js
* TypeScript
* Tailwind CSS

Backend

* Python
* FastAPI

Database

* MySQL（Cloud SQL想定）

Deploy

* Cloud Run

API

* eBay Developer API
* Amazon商品取得（実装方法は後で選定）

⸻

3. 開発方針

重要なのは、

「自動化」ではなく「まず動くものを作る」

Cloud Schedulerは後回し。

まずは

ボタンを押す
↓
Amazon取得
↓
利益計算
↓
eBay出品

が完成すれば成功。

⸻

4. ディレクトリ構成

amazon-ebay-system
frontend/
    Next.js
backend/
    FastAPI
database/
docs/
docker-compose.yml
README.md

⸻

5. 開発フェーズ

Phase1

環境構築

完了条件

* Next.js起動
* FastAPI起動
* MySQL接続
* Docker起動

⸻

Phase2

ログイン画面

今回は簡易的で良い

管理画面

のみ作成。

⸻

Phase3

Amazon商品検索

画面

キーワード
[検索]
-------------------
商品一覧

表示項目

* 商品名
* ASIN
* Amazon価格
* 商品画像
* ブランド

⸻

Phase4

利益計算

画面に追加

利益
利益率
送料
eBay価格

利益計算は一旦固定値でも良い。

例

Amazon価格
送料
eBay手数料
利益

⸻

Phase5

商品詳細画面

表示内容

* タイトル
* 商品説明
* 画像
* 利益
* カテゴリー

⸻

Phase6

英語タイトル生成

AIで

* タイトル
* 商品説明

を英語化。

まだ出品しない。

画面確認のみ。

⸻

Phase7

eBay API接続

最初は

接続成功

だけ確認。

まだ出品しない。

⸻

Phase8

出品プレビュー

表示

画像
タイトル
価格
説明
カテゴリー
配送
[出品]

この画面で内容確認。

⸻

Phase9

eBay出品

初めてAPI実行。

成功したら

出品成功

表示。

⸻

Phase10

商品管理画面

一覧

Amazon価格
eBay価格
利益
状態
更新日

⸻

6. テストモード

必須。

TEST_MODE=true

の場合

Amazon取得

↓

利益計算

↓

eBayデータ生成

↓

JSON表示

↓

終了

APIは呼ばない。

⸻

7. 本番モード

TEST_MODE=false

だけ

eBay API

実行。

⸻

8. ログ

全処理を保存。

例

取得開始
取得完了
利益計算
翻訳開始
翻訳完了
出品開始
出品成功
エラー

⸻

9. データベース

products

id
asin
title
description
amazon_price
ebay_price
profit
profit_rate
brand
category
image
status
created_at
updated_at

⸻

listings

id
product_id
ebay_item_id
listing_status
listed_at
updated_at

⸻

logs

id
type
message
created_at

⸻

10. MVP完成条件

以下が全て動けば完成。

✅ Amazon商品検索

✅ 商品一覧表示

✅ 利益計算

✅ 英語タイトル生成

✅ 出品プレビュー

✅ eBayへ手動出品

⸻

11. Phase2（MVP完成後）

* Amazon価格自動更新
* 在庫同期
* eBay価格更新
* 出品停止
* エラーログ画面
* ダッシュボード
* 売上管理

⸻

12. Phase3（自動化）

Cloud Scheduler

↓

Cloud Run

↓

FastAPI

↓

価格更新

↓

出品更新

↓

ログ保存

⸻

13. Cursorへの実装ルール

* 1機能ずつ実装する（検索→利益計算→翻訳→出品の順）
* 各機能で必ず動作確認を行ってから次へ進む
* APIキーやシークレットは .env に保存し、ソースコードへ直接記述しない
* フロントエンドとバックエンドは責務を分離し、API経由で通信する
* 例外処理とログ出力を必ず実装する
* Gitで細かくコミットする（各フェーズ完了ごと）
* まずは「動くMVP」を優先し、最適化や自動化は後から行う