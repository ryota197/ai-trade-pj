# コスト試算（個人利用前提）

## 前提条件
- 個人投資用（商用利用なし）
- 日本在住、米国株中心
- できるだけ無料枠を活用
- 月間アクセス: 自分のみ（低トラフィック）

---

## 1. データAPI

### 株価データ

| サービス | 無料枠 | 有料プラン | 備考 |
|---------|--------|-----------|------|
| **Yahoo Finance (yfinance)** | 無制限 | - | 非公式API、レート制限あり、個人利用なら十分 |
| **Alpha Vantage** | 25リクエスト/日 | $49.99/月〜 | 無料枠は厳しい |
| **Polygon.io** | 5 API calls/min | $29/月〜 | リアルタイムが必要なら |
| **Finnhub** | 60 calls/min | $0〜 | 基本データは無料 |
| **Tiingo** | 1000リクエスト/日 | $10/月〜 | コスパ良好 |

**推奨**: yfinance（無料）をメインに、必要に応じてTiingo（$10/月）を追加

### ファンダメンタルデータ（財務諸表等）

| サービス | 無料枠 | 有料プラン | 備考 |
|---------|--------|-----------|------|
| **SEC EDGAR** | 無制限 | - | 10-K/10-Q直接取得、パース必要 |
| **Financial Modeling Prep** | 250リクエスト/日 | $19/月〜 | CAN-SLIMに必要なデータ揃う |
| **Simfin** | 制限あり | €9.99/月〜 | 財務データ特化 |

**推奨**: SEC EDGAR（無料）+ Financial Modeling Prep（無料枠 or $19/月）

---

## 2. インフラ

### Frontend (Next.js)

| サービス | 無料枠 | 有料プラン | 備考 |
|---------|--------|-----------|------|
| **Vercel** | 100GB帯域/月 | $20/月〜 | Next.js最適、個人なら無料枠で十分 |
| **Cloudflare Pages** | 無制限 | - | 完全無料、SSR対応 |

**推奨**: Vercel無料枠（Hobby）で十分

### Backend (Python FastAPI)

| サービス | 無料枠 | 有料プラン | 備考 |
|---------|--------|-----------|------|
| **Railway** | $5クレジット/月 | 従量課金 | 簡単デプロイ |
| **Fly.io** | 3 shared VMs | 従量課金 | 無料枠で小規模OK |
| **Render** | 750時間/月 | $7/月〜 | 無料枠はスリープあり |
| **自宅サーバー** | 電気代のみ | - | 常時稼働なら選択肢 |

**推奨**: Railway or Fly.io（月$0〜5程度）

### Database

| サービス | 無料枠 | 有料プラン | 備考 |
|---------|--------|-----------|------|
| **Supabase** | 500MB, 2GB帯域 | $25/月〜 | PostgreSQL + Auth + Realtime |
| **PlanetScale** | 5GB, 1B reads | $29/月〜 | MySQL互換 |
| **Neon** | 512MB | $19/月〜 | PostgreSQL、無料枠あり |
| **Railway PostgreSQL** | $5クレジット内 | 従量課金 | バックエンドと同居可 |

**推奨**: Supabase無料枠（時系列データが増えたらTimescaleCloud検討）

### キャッシュ (Redis)

| サービス | 無料枠 | 有料プラン | 備考 |
|---------|--------|-----------|------|
| **Upstash** | 10K commands/日 | $0.2/100K cmd | 個人利用なら無料枠で十分 |
| **Railway Redis** | $5クレジット内 | 従量課金 | |

**推奨**: Upstash無料枠

---

## 3. ML/AI（チャートパターン認識）

### 学習フェーズ

| サービス | 無料枠 | 有料プラン | 備考 |
|---------|--------|-----------|------|
| **Google Colab** | 無制限（GPU制限あり） | $9.99/月〜 | 学習には十分 |
| **Kaggle Notebooks** | 30時間GPU/週 | - | 無料でGPU使える |
| **Lambda Labs** | - | $0.50/時間〜 | 本格的な学習時 |
| **ローカルGPU** | 初期費用のみ | 電気代 | RTX 3060〜で可能 |

**推奨**: Google Colab無料枠で開発、必要ならColab Pro（$9.99/月）

### 推論フェーズ

| 方式 | コスト | 備考 |
|-----|--------|------|
| **CPU推論（クラウド）** | $0〜5/月 | 軽量モデルなら十分 |
| **Edge推論（ローカル）** | $0 | ブラウザやローカルPCで実行 |

**推奨**: 軽量モデル + CPU推論（追加コストなし）

---

## 4. その他

| 項目 | コスト | 備考 |
|-----|--------|------|
| ドメイン | $10〜15/年 | 任意（localhost運用も可） |
| SSL証明書 | $0 | Let's Encrypt / Cloudflare |
| 通知（Push） | $0 | Firebase FCM無料枠 |
| メール通知 | $0 | Resend無料枠（100通/日） |

---

## コスト試算まとめ

### パターンPoC: ローカル開発構成（推奨：検証フェーズ）

**コンセプト**: クラウドを使わず、ローカル環境で完結させる

```
┌─────────────────────────────────────────────────┐
│              Local Development                   │
├─────────────────────────────────────────────────┤
│  Next.js (localhost:3000)                       │
│  FastAPI (localhost:8000)                       │
│  Docker: PostgreSQL + Redis                      │
│  yfinance (無料API)                              │
│  Google Colab / ローカルGPU (ML学習)             │
└─────────────────────────────────────────────────┘
```

| 項目 | 構成 | コスト |
|-----|------|--------|
| 株価データ | yfinance | $0 |
| 財務データ | SEC EDGAR + FMP無料枠 | $0 |
| Frontend | Next.js (localhost) | $0 |
| Backend | FastAPI (localhost) | $0 |
| Database | PostgreSQL (Docker) | $0 |
| ML学習 | Google Colab Free / ローカル | $0 |
| **合計** | | **$0（電気代のみ）** |

**Docker Compose構成例**:
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: trader
      POSTGRES_PASSWORD: localdev
      POSTGRES_DB: trading
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

※ Redisは必要になった時点で追加すればOK

**メリット**:
- 完全無料（電気代のみ）
- ネットワーク遅延なし（高速）
- データ容量制限なし
- オフラインでも開発可能
- 本番移行時もDocker構成をそのまま活用可能

**制約**:
- PCを起動している時のみ動作
- 外出先からアクセス不可（Tailscale等で解決可能）
- スマホ通知を受けるには別途工夫が必要

**PoC検証項目**:
1. yfinanceのデータ取得が安定しているか
2. CAN-SLIMスクリーニングが実用的か
3. チャートパターン認識の精度
4. 実際のトレードで利益が出るか（ペーパートレード）

---

### パターンA: 完全無料構成

| 項目 | サービス | 月額 |
|-----|---------|------|
| 株価データ | yfinance | $0 |
| 財務データ | SEC EDGAR + FMP無料枠 | $0 |
| Frontend | Vercel Hobby | $0 |
| Backend | Fly.io / Railway | $0〜5 |
| Database | Supabase Free | $0 |
| Cache | Upstash Free | $0 |
| ML学習 | Google Colab Free | $0 |
| **合計** | | **$0〜5/月** |

**制約**:
- APIレート制限により、リアルタイム更新は難しい
- DBストレージ上限あり（500MB）
- バックエンドがスリープする可能性

### パターンB: 実用的な低コスト構成（推奨）

| 項目 | サービス | 月額 |
|-----|---------|------|
| 株価データ | yfinance + Tiingo | $10 |
| 財務データ | Financial Modeling Prep | $0〜19 |
| Frontend | Vercel Hobby | $0 |
| Backend | Railway | $5〜10 |
| Database | Supabase Free → Pro | $0〜25 |
| Cache | Upstash Free | $0 |
| ML学習 | Colab Pro | $10 |
| **合計** | | **$25〜75/月** |

**メリット**:
- 十分なAPI呼び出し回数
- 安定したバックエンド稼働
- データ蓄積の余裕あり

### パターンC: フル機能構成

| 項目 | サービス | 月額 |
|-----|---------|------|
| 株価データ | Polygon.io | $29 |
| 財務データ | Financial Modeling Prep | $19 |
| Frontend | Vercel Pro | $20 |
| Backend | Railway Pro | $20 |
| Database | Supabase Pro | $25 |
| Cache | Upstash Pay-as-you-go | $5 |
| ML | Colab Pro+ | $50 |
| **合計** | | **$170/月程度** |

---

## 推奨アプローチ

### Phase 0: PoC（$0/月）← 現在地
- **目的**: リターン向上の仮説検証
- **期間目安**: 実際のトレード検証に数ヶ月
- **構成**: 完全ローカル（Docker + localhost）
- **検証内容**:
  - [ ] yfinanceでのデータ取得検証
  - [ ] CAN-SLIMスクリーニングロジック実装
  - [ ] チャートパターン認識のPoC
  - [ ] ペーパートレードで戦略検証（3〜6ヶ月）
- **成功基準**: ペーパートレードでS&P500を上回るリターン

### Phase 1: MVP（$0〜5/月）
- **移行条件**: PoCで有効性が確認できた場合
- 完全無料クラウド構成
- yfinance + Supabase + Vercel + Fly.io
- 外出先からのアクセス、通知機能追加

### Phase 2: 実運用（$25〜50/月）
- **移行条件**: 実際のトレードで利益が出ている場合
- データ品質向上（Tiingo追加）
- バックエンド安定化
- 機能が固まったら移行

### Phase 3: 必要に応じて拡張
- リアルタイムデータが必要ならPolygon.io
- MLモデルが複雑化したらGPUリソース追加

---

## 投資対効果の考え方

現状のリターン: 年15%（S&P500タイミング投資）

仮に$100,000運用の場合:
- 年間リターン: $15,000
- アプリ運用コスト: $300〜600/年（パターンB）
- **コスト比率: 2〜4%**

エントリーポイント改善で個別株リターンが7%→15%に改善できれば、十分にペイする投資と言える。
