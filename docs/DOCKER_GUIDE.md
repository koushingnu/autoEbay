# Docker 超入門 & このプロジェクトでの使い方

「Dockerって結局なに？」から、「今このプロジェクトで何が動いていて、どのコマンドで何ができるのか」までを、
例えと図でまとめたドキュメント。

---

## 1. Docker とは？（一言でいうと）

> **アプリを「箱」ごと持ち運べるようにする仕組み。**

ふつう、アプリを動かすにはPCに色々インストールが必要:

- バックエンド → Python 3.11 と各種ライブラリ
- フロント → Node.js
- DB → MySQL

これを全員のPCに手作業で入れると **「私のPCでは動くのに、あなたのPCでは動かない」** が起きる。

Docker はこれを解決する。アプリと必要なもの（言語・ライブラリ・設定）を **1つの箱に丸ごと詰める**。
箱ごと配れば、どのPCでも同じように動く。

### 例え：お弁当 🍱

```
従来のやり方（食材を各家庭で買って自炊）
  → 家によって調味料も鍋も違う → 味がバラバラ（環境依存）

Docker（作り終えたお弁当を配る）
  → 中身はどこで開けても同じ → いつも同じ味（環境が固定される）
```

---

## 2. 3つの重要ワード（イメージ・コンテナ・ボリューム）

| 用語 | 例え | 説明 |
| --- | --- | --- |
| **イメージ (image)** | お弁当の「レシピ＋冷凍弁当」 | アプリを動かすための設計図＋中身。変化しない“型”。 |
| **コンテナ (container)** | レシピから作った「実物の弁当」 | イメージを実際に起動したもの。動いている本体。消しても作り直せる。 |
| **ボリューム (volume)** | 冷蔵庫 | コンテナを消してもデータを残す保存場所。DBの中身はここに入る。 |

```
Dockerfile（レシピ）
     │ build（調理）
     ▼
  イメージ（冷凍弁当）
     │ run / up（温めて出す）
     ▼
  コンテナ（食べられる弁当＝動いてるアプリ）
     ├─ ポートで外とつながる（受け渡し口）
     └─ ボリュームにデータを保存（冷蔵庫）
```

ポイント:
- **コンテナは使い捨てOK**。消してもイメージから何度でも作り直せる。
- **消えてほしくないデータ（DB）はボリュームに置く** ので、コンテナを消しても残る。

---

## 3. このプロジェクトの構成（今なにが動くか）

このアプリは **3つのコンテナ** が協力して動く。指揮者が `docker-compose.yml`。

```
                  あなたのブラウザ
                        │  http://localhost:3000
                        ▼
        ┌───────────────────────────┐
        │  ae_frontend (Next.js)     │  画面
        │  ポート 3000               │
        └───────────────┬───────────┘
                        │  API 通信 (localhost:8000)
                        ▼
        ┌───────────────────────────┐
        │  ae_backend (FastAPI)      │  ロジック・API
        │  ポート 8000               │
        └───────────────┬───────────┘
                        │  SQL 接続
                        ▼
        ┌───────────────────────────┐
        │  ae_db (MySQL)             │  データ保存
        │  ポート 3306               │
        │  volume: db_data（冷蔵庫） │
        └───────────────────────────┘
```

| コンテナ名 | 中身 | 役割 | ポート |
| --- | --- | --- | --- |
| `ae_frontend` | Next.js | 画面（ブラウザに表示） | 3000 |
| `ae_backend` | FastAPI (Python) | API・商品取得・利益計算など | 8000 |
| `ae_db` | MySQL | 商品・出品データの保存 | 3306 |

### 「ポート」ってなに？

コンテナは箱の中に閉じているので、そのままでは外から触れない。
**ポート = 箱に開けた受け渡し窓口**。

```
"3000:3000"  ←  左が「あなたのPC側」、右が「コンテナの中」
   │    │
   PC   コンテナ
```

だから `localhost:3000` をブラウザで開くと、frontend コンテナの中の 3000 につながる。

---

## 4. docker-compose.yml の読み方（このプロジェクト）

`docker-compose.yml` は「3つのコンテナをどう起動するか」を書いた台本。抜粋して解説:

```yaml
services:
  db:                     # ① データベース
    image: mysql:8.0      # 既製イメージ（MySQL公式）をそのまま使う
    ports: ["3306:3306"]  # 受け渡し窓口
    volumes:
      - db_data:/var/lib/mysql                 # 冷蔵庫（データ永続化）
      - ./database/init.sql:/.../init.sql:ro   # 初回起動時にテーブル作成

  backend:                # ② バックエンド
    build: ./backend      # backend/Dockerfile から自前でイメージを作る
    env_file: [./backend/.env]   # APIキーなどの環境変数を読み込む
    volumes: [./backend:/app]    # PCのソースをコンテナに同期（編集が即反映）
    ports: ["8000:8000"]
    depends_on: { db: { condition: service_healthy } }  # DBが元気になってから起動

  frontend:               # ③ フロント
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend] # backend の後に起動

volumes:
  db_data:                # 冷蔵庫の実体
```

覚えておくと良い設定:
- `image:` … 既製の箱を使う（MySQLはこれ）。
- `build:` … 自分の `Dockerfile` から箱を作る（backend / frontend はこれ）。
- `volumes: ./backend:/app` … **PCのコードとコンテナ内を同期**。コードを直すと即反映（開発が楽）。
- `depends_on` … 起動の順番（DB → backend → frontend）。

### Dockerfile（backend の例）＝ 箱の作り方

```dockerfile
FROM python:3.11-slim          # ベースは Python入り の箱
WORKDIR /app                   # 作業場所
COPY requirements.txt .        # 必要ライブラリ一覧をコピー
RUN pip install -r requirements.txt   # ライブラリを入れる
COPY . .                       # アプリ本体をコピー
CMD ["uvicorn", "app.main:app", ...]  # 起動コマンド
```

= 「Pythonの箱を用意 → ライブラリを入れる → コードを入れる → 起動する」というレシピ。

---

## 5. コマンド早見表（今つかっているもの）

すべて **プロジェクトのルート**（`docker-compose.yml` がある場所）で実行する。

| コマンド | 何をする | 例え |
| --- | --- | --- |
| `docker compose up -d` | 3コンテナをまとめて起動（バックグラウンド） | 全員出勤 |
| `docker compose up -d --build` | イメージを作り直してから起動 | レシピ更新→作り直して出勤 |
| `docker compose stop` | 停止（データは残る） | 一旦帰宅（机はそのまま） |
| `docker compose start` | 停止中のを再開 | 再出勤 |
| `docker compose down` | 停止＋コンテナ削除（ボリュームは残る） | 撤収（冷蔵庫は残す） |
| `docker compose down -v` | 停止＋コンテナ＋**ボリューム削除** | 冷蔵庫も空に（DB全消し⚠️） |
| `docker compose ps` | 起動状況を見る | 出勤簿 |
| `docker compose logs -f backend` | backend のログを流し見 | 実況中継 |
| `docker compose restart backend` | backend だけ再起動 | 一人だけ再出勤 |
| `docker compose exec db bash` | 起動中コンテナの中に入る | 中に様子を見に行く |

### `-d` ってなに？
`-d` = detached（バックグラウンド実行）。付けないとターミナルが占有され、ログが流れ続ける。

### ⚠️ 一番注意すべきコマンド
`docker compose down -v` の **`-v`** は **ボリューム（＝DBデータ）まで消す**。
「テーブル構成を変えたので作り直したい」ときだけ使う。普段の停止は `stop` で十分。

---

## 6. このプロジェクトでの典型的な操作フロー

```
【毎日の開発】
  docker compose up -d        # 起動
      ↓ ブラウザで localhost:3000 を開いて開発
      ↓ コードを編集 → volume同期で自動反映（backendは --reload）
  docker compose stop         # 終わったら停止（データは残る）

【DBのテーブル定義(init.sql)を変えたとき】
  docker compose down -v      # ボリューム削除（初期化）⚠️
  docker compose up -d --build

【調子が悪い / エラーを見たい】
  docker compose ps           # 状態確認
  docker compose logs -f backend   # ログ確認
```

### 今の状態（このドキュメント作成時点）
- 直前に `docker compose stop` を実行 → **3コンテナは停止中**。
- ボリューム `db_data` は残っているので **DBの中身は保持**。
- 再開するなら `docker compose start`（または `up -d`）。

---

## 7. よくある疑問

**Q. コンテナを消したらデータも消える？**
A. DBデータは `db_data` ボリューム（冷蔵庫）にあるので、`down`（-vなし）や `stop` では消えない。
   消えるのは `down -v` を使ったときだけ。

**Q. コードを直したら毎回 build が必要？**
A. 基本は不要。`volumes: ./backend:/app` でソースが同期され、backend は `--reload` で自動反映。
   ただし **ライブラリ追加（requirements.txt / package.json 変更）時は `--build` が必要**。

**Q. `up` と `start` の違いは？**
A. `up` = 「無ければ作って起動」。`start` = 「すでに作ってある停止中のものを再開」。
   初回や設定変更後は `up`、単に再開なら `start`。

**Q. ポートがぶつかる（already in use）と出たら？**
A. 3000/8000/3306 を他のアプリが使っている。そのアプリを止めるか、`docker-compose.yml` の左側ポート番号を変える。

---

## 8. まとめ（3行）

1. Docker は **アプリを箱（コンテナ）ごと動かす**仕組み。環境差をなくせる。
2. このプロジェクトは **frontend / backend / db の3コンテナ**を `docker compose` でまとめて起動している。
3. 普段は **`up -d` で起動 / `stop` で停止**。DBを作り直すときだけ **`down -v`** を使う。
