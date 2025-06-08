# 🌟 文豪ゆかり地図システム v3.0

青空文庫と Wikipedia から文豪作品の地名情報を自動抽出し、地図上で可視化する統合システム

![Python](https://img.shields.io/badge/python-v3.12+-blue.svg)
![GitHub](https://img.shields.io/badge/license-MIT-green.svg)

## 🌟 主要機能

### データ収集・構築
- **青空文庫データベース構築**: 公式CSVファイルからの大規模データベース構築
- **Wikipedia連携**: 作家・作品情報の自動抽出
- **手動データ追加**: カスタム作者・作品・地名の登録機能
- **高精度地名抽出**: GiNZA NLP / MeCab による日本語地名認識
- **座標自動取得**: Google Maps API による緯度経度データ取得

### 検索・分析
- **3階層検索**: 作家 ↔ 作品 ↔ 地名の双方向検索
- **地理的分析**: 作品別・作家別の舞台地分布
- **時代別分析**: 出版年代による地名トレンド

### データエクスポート
- **GeoJSON**: 地図可視化対応形式
- **CSV/Excel**: データ分析対応形式
- **統計レポート**: システム利用状況

## 🚀 クイックスタート

### 1. システムセットアップ

```bash
# リポジトリクローン
git clone https://github.com/yourusername/bungo_map.git
cd bungo_map

# 依存関係インストール
pip install -r requirements.txt

# データベース初期化
python main.py status
```

### 2. 青空文庫データベース構築

```bash
# 主要5作家のデータベース構築（推奨）
python main.py aozora build-database --authors "夏目漱石,芥川竜之介,太宰治,宮沢賢治,森鴎外" --limit 5

# 特定作家のみ
python main.py aozora build-database --authors "夏目漱石" --limit 10

# テストモード（実際の登録なし）
python main.py aozora build-database --authors "夏目漱石" --limit 3 --test
```

### 3. 座標データ取得

```bash
# 地名の座標を自動取得
python main.py geocode --limit 50

# 座標設定状況確認
python main.py geocode --status
```

### 4. 手動データ追加

```bash
# 作者を手動追加
python main.py add author --name "新作者" --birth-year 1900 --death-year 1980

# 作品を手動追加  
python main.py add work --title "新作品" --author-id 1 --publication-year 1950

# 地名を手動追加
python main.py add place --name "新地名" --latitude 35.6762 --longitude 139.6503

# 対話式追加モード
python main.py add author --interactive

# 追加テンプレート表示
python main.py add template
```

### 5. データ検索・分析

```bash
# 作家検索
python main.py search authors "夏目"

# 作品検索
python main.py search works "坊っちゃん"

# 地名検索
python main.py search places "松山"
```

### 6. データエクスポート

```bash
# GeoJSONエクスポート（地図可視化用）
python main.py export --format geojson -o bungo_map.geojson

# CSVエクスポート（データ分析用）
python main.py export --format csv -o bungo_data.csv
```

## 📊 統計情報

現在のシステム統計（2025年6月時点）：

```bash
python main.py aozora stats
```

- **作家数**: 21名（主要文豪）
- **作品数**: 178作品
- **地名数**: 1,924箇所
- **URL設定率**: 92.7%
- **コンテンツ設定率**: 83.7%

## 🏗️ システム構成

### コアモジュール
```
bungo_map/
├── core/           # データベース・モデル
├── extractors/     # 地名抽出エンジン
├── geo/           # 地理情報処理
├── cli/           # コマンドライン管理
├── utils/         # ユーティリティ
└── api/           # REST API（予定）
```

### 主要コマンド

| コマンド | 機能 | 例 |
|---------|------|----| 
| `main.py aozora` | 青空文庫データベース構築 | `build-database`, `download-csv`, `stats` |
| `main.py add` | 手動データ追加 | `author`, `work`, `place`, `template` |
| `main.py search` | データ検索 | `authors`, `works`, `places` |
| `main.py geocode` | 座標データ取得 | `--all`, `--limit 50`, `--status` |
| `main.py export` | データエクスポート | `--format geojson`, `--format csv` |
| `main.py collect` | 従来データ収集 | `--author "夏目漱石"`, `--demo` |

## 🛠️ 技術スタック

### データ処理
- **Python 3.12+**: メイン開発言語
- **SQLite**: 軽量データベース
- **pandas**: データ分析・処理
- **aiohttp**: 非同期HTTP通信

### NLP・地名抽出
- **GiNZA**: 高精度日本語自然言語処理
- **spaCy**: NLPフレームワーク
- **MeCab**: 形態素解析（補助）

### Web・API
- **requests**: HTTP通信
- **BeautifulSoup4**: HTMLパース
- **googlemaps**: 座標取得API

### CLI・UI
- **Click**: コマンドライン管理
- **Rich**: 高機能コンソール出力
- **tqdm**: プログレスバー

## 💡 使用例

### 1. 青空文庫大規模データベース構築

```bash
# 主要10作家の全作品（フィルタ適用）
python main.py aozora build-database \
  --authors "夏目漱石,芥川竜之介,太宰治,宮沢賢治,森鴎外,中島敦,梶井基次郎,坂口安吾,与謝野晶子,中原中也"

# 実行結果例：
# ✅ 91作品追加
# 📊 URL設定率: 90.4%
# 📊 コンテンツ設定率: 83.7%
```

### 2. 地名データ分析

```bash
# 松山市関連の地名検索
python main.py search places "松山"

# 坊っちゃん関連作品の舞台地
python main.py search works "坊っちゃん"
```

### 3. 地図可視化用データ生成

```bash
# 座標付き地名をGeoJSONエクスポート
python main.py geocode --limit 100
python main.py export --format geojson -o literary_map.geojson

# Webマップで可視化可能
```

### 4. 手動データ追加の活用例

```bash
# 青空文庫にない作者を追加
python main.py add author --name "田中太郎" --birth-year 1925 --death-year 1990 \
  --wikipedia-url "https://ja.wikipedia.org/wiki/田中太郎"

# 個人創作作品を追加
python main.py add work --title "新しい物語" --author-id 197 \
  --publication-year 1960 --url "https://example.com/story.txt"

# 特定の地名を詳細情報付きで追加
python main.py add place --name "架空の街" --latitude 35.6762 --longitude 139.6503 \
  --work-id 403 --context "物語の舞台となる街" --confidence 0.9

# 対話式で詳細入力
python main.py add author --interactive
```

## 📈 パフォーマンス

### 青空文庫データベース構築
- **処理時間**: 153.1秒（91作品）
- **成功率**: 83.7%（コンテンツ取得）
- **メモリ使用量**: < 500MB

### 地名抽出
- **GiNZA**: 高精度、やや低速
- **MeCab**: 高速、中精度
- **辞書ベース**: 最高速、基本精度

## 🎯 データ追加方法

システムでは3つの方法でデータを追加できます：

### 1. 青空文庫自動追加（推奨）
```bash
# 公式データベースから自動構築
python main.py aozora build-database --authors "中原中也"
```
- **メリット**: 大量データ、高品質、全自動
- **対象**: 青空文庫収録作品（19,356作品）

### 2. 手動データ追加
```bash
# カスタムデータを個別追加
python main.py add author --name "新作者"
python main.py add work --title "新作品" --author-id 1
```
- **メリット**: 完全カスタマイズ、青空文庫外対応
- **対象**: 現代作家、個人創作、研究資料

### 3. 従来システム（レガシー）
```bash
# Wikipedia連携の従来機能
python main.py collect --author "夏目漱石" --demo
```
- **メリット**: Wikipedia情報活用
- **対象**: 既存データ拡充

## 🎯 今後の展開

### v3.1 予定機能
- [ ] FastAPI REST APIサーバー
- [ ] React.js Webフロントエンド
- [ ] リアルタイム地図可視化
- [ ] 機械学習による地名分類
- [ ] 一括インポート機能（CSV/JSON）

### v4.0 構想
- [ ] 明治～現代文学への対象拡大
- [ ] 海外文学の日本舞台作品対応
- [ ] 時系列地名変化トラッキング
- [ ] 観光連携API

## 🤝 貢献

プルリクエスト歓迎！以下の分野で貢献可能：

- **データ品質向上**: 地名抽出精度改善
- **機能追加**: 新しい分析機能
- **パフォーマンス**: 処理速度最適化
- **ドキュメント**: 使用例・チュートリアル

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照

## 🙏 謝辞

- **青空文庫**: 貴重な文学テキスト提供
- **国語研・GiNZA**: 高品質日本語NLP
- **Wikipedia**: 包括的作家・作品情報

---

**文豪ゆかり地図システム**: 日本文学の地理的世界を探索する統合プラットフォーム