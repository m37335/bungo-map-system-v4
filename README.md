# 🌟 文豪ゆかり地図システム v3.0

> **自動ジオコーディング統合版** - 日本文学作品から地名を抽出し、自動座標付与で地図化するシステム

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)
[![Geocoding](https://img.shields.io/badge/座標カバー率-62.9%25-brightgreen.svg)](https://github.com)
[![Places](https://img.shields.io/badge/地名数-1,612件-blue.svg)](https://github.com)

## 🚀 v3.0重要アップデート: 自動ジオコーディング統合！

**完全自動化達成**: 地名抽出 → 自動座標付与 → 地図データ生成までワンコマンド実行

| 指標 | アップデート前 | アップデート後 | 改善効果 |
|------|---------------|---------------|----------|
| **🗺️ 座標カバー率** | 57.6% | **62.9%** | **+5.3pt** |
| **📍 総地名数** | 1,300件 | **1,612件** | **+312件** |
| **🎯 座標付き地名** | 660件 | **1,014件** | **+354件** |
| **⚡ 処理フロー** | 手動2段階 | **完全自動化** | **ワンコマンド** |
| **🧠 座標データベース** | 212地名 | **200+地名** | **文学特化** |

## 📋 概要

文豪ゆかり地図システムは、青空文庫の文学作品から地名を自動抽出し、インテリジェントジオコーディングで座標を付与、地理的データとして管理・可視化するシステムです。

**✨ v3.0 の主要改善点**:
- 🔗 **統合パイプライン**: 地名抽出 + 自動ジオコーディング + 統計レポート
- 📊 **拡張座標データベース**: 200+地名の日本地理データ内蔵
- 🧠 **スマートマッチング**: 完全一致 + 部分一致による座標付与
- 📈 **リアルタイム進捗**: 各地名の座標更新をリアルタイム表示
- 🗺️ **高カバー率**: 62.9%の地名に座標付与完了

### 📈 実行結果

**🟢 統合システム（最新実行結果）**:
```bash
🚀 文豪ゆかり地図システム - 完全データ拡充開始
📊 座標データベース: 200+件の地名を準備
��️ 4. 自動ジオコーディング実行
✅ 東京: 座標更新 (35.6762, 139.6503)
✅ 神田: 座標更新 (35.6914, 139.7706)
✅ 新橋: 座標更新 (35.6668, 139.7587)
✅ 鎌倉: 座標更新 (35.3192, 139.5469)
✅ 箱根: 座標更新 (35.2322, 139.1069)
✅ 江戸: 座標更新 (35.7041, 139.8681) [部分マッチ: 江戸川]

📊 データベース最終状況:
   📚 作者: 10件
   📖 作品: 30件
   🏞️ 地名: 1,612件
   🗺️ 座標あり: 1,014件 (62.9%)
   🎯 今回更新: 354件
   ⏱️ 実行時間: 265.9秒
```

**作者別地名分布（座標付き）**:
- **夏目漱石**: 502件 (76.1%) - 東京中心の明治期地名
- **太宰治**: 143件 (21.7%) - 青森・東京の昭和期地名  
- **芥川龍之介**: 8件 (1.2%) - 京都・東京の大正期地名
- **宮沢賢治**: 7件 (1.1%) - 岩手・北海道の地名

## 🚀 クイックスタート

### 🐳 統合パイプライン（推奨）

```bash
# Docker環境起動
docker-compose up -d

# 🚀 完全自動化パイプライン実行（地名抽出+ジオコーディング）
docker-compose exec bungo-dev python run_full_extraction.py

# 📊 最新GeoJSONエクスポート
docker-compose exec bungo-dev python export_updated_geojson.py

# 📈 データベース統計確認
docker-compose exec bungo-dev sqlite3 data/bungo_production.db \
  "SELECT COUNT(*) as total_places, 
   SUM(CASE WHEN lat IS NOT NULL THEN 1 ELSE 0 END) as geocoded_places,
   ROUND(100.0 * SUM(CASE WHEN lat IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as coverage_rate 
   FROM places;"
```

### 🔧 個別実行（開発用）

```bash
# 環境セットアップ
pip install -r requirements.txt
python -m spacy download ja_ginza

# 地名抽出のみ実行
python run_full_extraction.py

# ジオコーディングのみ実行  
python bulk_geocoding_update.py

# GeoJSONエクスポート
python export_updated_geojson.py
```

## 🏗️ システム構成

### 🆕 統合データフロー
```
青空文庫テキスト → 地名抽出 → 自動ジオコーディング → データベース → GeoJSON
     (30作品)      ↓           ↓              ↓          ↓
               GiNZA + 正規表現  200+地名DB    SQLite    地図可視化
               (1,612地名)     (62.9%成功)   (3階層)   (MapKit対応)
```

### ディレクトリ構成
```
bungo_project_v3/
├── bungo_map/                    # メインパッケージ
│   ├── core/                     # データベース・モデル
│   │   ├── database.py           # 🆕 ジオコーディング対応DB
│   │   └── models.py             
│   ├── extractors/               # 地名抽出エンジン
│   │   ├── ginza_place_extractor.py
│   │   ├── simple_place_extractor.py
│   │   └── aozora_extractor.py
│   └── utils/                    # ユーティリティ
├── run_full_extraction.py        # 🆕 統合パイプライン（地名抽出+ジオコーディング）
├── bulk_geocoding_update.py      # 従来のジオコーディング（比較用）
├── export_updated_geojson.py     # GeoJSONエクスポート
├── data/                         # データベース
│   └── bungo_production.db       # SQLite（1,612地名・1,014座標）
└── output/                       # 出力ファイル
    └── bungo_map_updated_*.geojson
```

## 🔧 主要機能

### 🆕 統合ジオコーディングエンジン

**内蔵座標データベース（200+地名）**
```python
coordinates_db = {
    # 歴史的・古典地名
    "武蔵": (35.6762, 139.6503),    # 東京
    "相模": (35.3392, 139.3949),    # 神奈川
    "甲斐": (35.6642, 138.5684),    # 山梨
    "越後": (37.9022, 139.0237),    # 新潟
    "山城": (35.0116, 135.7681),    # 京都
    "薩摩": (31.5966, 130.5571),    # 鹿児島
    
    # 東京詳細地名
    "神田": (35.6914, 139.7706),
    "銀座": (35.6762, 139.7653),
    "新橋": (35.6668, 139.7587),
    "浅草": (35.7148, 139.7967),
    "上野": (35.7090, 139.7753),
    "本郷": (35.7090, 139.7619),
    
    # 文学ゆかり地
    "鎌倉": (35.3192, 139.5469),
    "箱根": (35.2322, 139.1069),
    "軽井沢": (36.3427, 138.6297),
    "日光": (36.7581, 139.6206),
    # ... 200+地名
}
```

**スマートマッチングアルゴリズム**
1. **完全一致**: `東京` → 直接座標取得
2. **部分マッチ**: `東京市` → `東京`の座標使用
3. **成功ログ**: `✅ 東京市: 座標更新 (35.6762, 139.6503) [部分マッチ: 東京]`

### 地名抽出エンジン

**GiNZA NLP抽出器**
- 文脈理解による高精度抽出（信頼度0.75-0.95）
- 固有表現認識 (LOC/GPE)
- 30KB自動分割処理

**正規表現抽出器（3種類）**
- **regex_都道府県**: 47都道府県パターン（信頼度0.70）
- **regex_市区町村**: 市区町村パターン（信頼度0.90）
- **regex_有名地名**: 観光地・歴史地名（信頼度0.65）

### データベース設計

```sql
-- 3階層正規化設計（拡張版）
authors (作者) 1 ← N works (作品) 1 ← N places (地名)

-- 拡張placesテーブル
CREATE TABLE places (
    place_id INTEGER PRIMARY KEY,
    work_id INTEGER REFERENCES works(work_id),
    place_name TEXT NOT NULL,
    lat REAL, lng REAL,             -- 🆕 座標情報
    before_text TEXT,               -- 前文脈
    sentence TEXT,                  -- 該当文
    after_text TEXT,                -- 後文脈
    confidence REAL,                -- 信頼度 (0.0-1.0)
    extraction_method TEXT,         -- 抽出方法
    aozora_url TEXT,               -- 青空文庫URL
    created_at TIMESTAMP
);
```

## 📊 統合ジオコーディング結果

### 🟢 成功例（座標付与完了）
```
✅ 東京: 座標更新 (35.6762, 139.6503)
✅ 神田: 座標更新 (35.6914, 139.7706)
✅ 新橋: 座標更新 (35.6668, 139.7587)
✅ 鎌倉: 座標更新 (35.3192, 139.5469)
✅ 箱根: 座標更新 (35.2322, 139.1069)
✅ 江戸: 座標更新 (35.7041, 139.8681) [部分マッチ: 江戸川]
✅ 甲斐: 座標更新 (35.6642, 138.5684)
✅ 薩摩: 座標更新 (31.5966, 130.5571)
✅ 京都: 座標更新 (35.0116, 135.7681)
✅ 大阪: 座標更新 (34.6937, 135.5023)
✅ 広島: 座標更新 (34.3853, 132.4553)
✅ 名古屋: 座標更新 (35.1815, 136.9066)
✅ 日光: 座標更新 (36.7581, 139.6206)
✅ 軽井沢: 座標更新 (36.3427, 138.6297)
✅ 松山: 座標更新 (33.8416, 132.7658)
```

### 🔍 未対応例（今後の拡張対象）
```
🔍 小石川: 座標不明 → 今後追加予定
🔍 四日市: 座標不明 → 三重県四日市市
🔍 豊橋: 座標不明 → 愛知県豊橋市
🔍 浜松: 座標不明 → 静岡県浜松市
🔍 金沢: 座標不明 → 石川県金沢市
```

### 📈 抽出方法別統計
| 抽出方法 | 件数 | 割合 | 座標成功率 |
|---------|------|------|-----------|
| **regex_有名地名** | 396件 | 60.0% | **高** |
| **ginza_nlp** | 205件 | 31.1% | **中** |
| **regex_市区町村** | 41件 | 6.2% | **高** |
| **regex_都道府県** | 13件 | 2.0% | **最高** |

## 🎯 GeoJSONエクスポート

### 📁 出力ファイル
- **ファイル名**: `bungo_map_updated_YYYYMMDD_HHMMSS.geojson`
- **ファイルサイズ**: 632.8KB
- **対応フォーマット**: MapKit, Leaflet, Google Maps対応

### 📊 GeoJSON統計情報
```json
{
  "type": "FeatureCollection",
  "metadata": {
    "total_places": 1612,
    "geocoded_places": 1014,
    "coverage_rate": 62.9,
    "authors": {
      "夏目漱石": 502,
      "太宰治": 143, 
      "芥川龍之介": 8,
      "宮沢賢治": 7
    },
    "extraction_methods": {
      "regex_有名地名": 396,
      "ginza_nlp": 205,
      "regex_市区町村": 41,
      "regex_都道府県": 13
    }
  },
  "features": [ ... ]
}
```

## 🛠️ コマンドリファレンス

### データ拡充
```bash
# 完全自動化パイプライン
docker-compose exec bungo-dev python run_full_extraction.py

# 地名抽出のみ（ジオコーディングなし）
docker-compose exec bungo-dev python -c "
from bungo_map.extractors.aozora_extractor import AozoraExtractor
extractor = AozoraExtractor()
extractor.run_extraction()
"

# ジオコーディングのみ
docker-compose exec bungo-dev python bulk_geocoding_update.py
```

### データ確認・統計
```bash
# データベース統計
docker-compose exec bungo-dev sqlite3 data/bungo_production.db "
SELECT 
  COUNT(*) as total_places,
  SUM(CASE WHEN lat IS NOT NULL THEN 1 ELSE 0 END) as geocoded,
  ROUND(100.0 * SUM(CASE WHEN lat IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as rate
FROM places;
"

# 作者別統計
docker-compose exec bungo-dev sqlite3 data/bungo_production.db "
SELECT a.name, COUNT(p.place_id) as places, 
       SUM(CASE WHEN p.lat IS NOT NULL THEN 1 ELSE 0 END) as geocoded
FROM authors a 
JOIN works w ON a.author_id = w.author_id 
JOIN places p ON w.work_id = p.work_id 
GROUP BY a.name ORDER BY places DESC;
"

# 抽出方法別統計
docker-compose exec bungo-dev sqlite3 data/bungo_production.db "
SELECT extraction_method, COUNT(*) as count,
       SUM(CASE WHEN lat IS NOT NULL THEN 1 ELSE 0 END) as geocoded
FROM places 
GROUP BY extraction_method ORDER BY count DESC;
"
```

### データエクスポート
```bash
# GeoJSONエクスポート
docker-compose exec bungo-dev python export_updated_geojson.py

# CSVエクスポート（座標付きのみ）
docker-compose exec bungo-dev sqlite3 -header -csv data/bungo_production.db "
SELECT p.place_name, p.lat, p.lng, p.confidence, p.extraction_method,
       w.title, a.name as author
FROM places p
JOIN works w ON p.work_id = w.work_id  
JOIN authors a ON w.author_id = a.author_id
WHERE p.lat IS NOT NULL
ORDER BY a.name, w.title, p.place_name;
" > output/bungo_places_geocoded.csv
```

## 📋 システム要件

### 必須要件
- **Python**: 3.10+ 
- **Docker**: 20.0+（推奨）
- **メモリ**: 4GB+
- **ストレージ**: 2GB+

### Python依存関係
```txt
pandas>=1.5.0
spacy>=3.7.0
ja-ginza>=5.1.0
requests>=2.28.0
beautifulsoup4>=4.11.0
sqlite3 (標準ライブラリ)
```

## 🚀 今後の拡張計画

### Phase 1: データ拡充（座標カバー率向上）
- [ ] 座標データベース拡張（500地名目標）
- [ ] 小地名・町名の詳細対応
- [ ] 地方都市・観光地の網羅
- [ ] **目標**: 座標カバー率 62.9% → 80%

### Phase 2: 高度ジオコーディング
- [ ] Google Maps API統合
- [ ] 歴史的地名の時代対応
- [ ] 曖昧地名の文脈解析
- [ ] **目標**: 座標カバー率 80% → 90%

### Phase 3: 可視化・分析機能
- [ ] インタラクティブ地図
- [ ] 時代別地名分布分析
- [ ] 作者別文学地理の比較
- [ ] **目標**: 研究支援ツール化

### Phase 4: 大規模拡張
- [ ] 青空文庫全作品対応（19,356作品）
- [ ] 現代文学作品への拡張
- [ ] 多言語対応（英語・中国語）
- [ ] **目標**: 文学地理学研究プラットフォーム

## 📞 サポート・コントリビューション

### バグ報告・機能要求
GitHubのIssuesページからご報告ください。

### 座標データの改善提案
地名の座標データに改善提案がある場合、以下の形式でPull Requestをお送りください：

```python
# bungo_map/geo/geocoding_engine.py への追加例
"新地名": (緯度, 経度),  # 都道府県・詳細情報
```

---

**🌟 文豪ゆかり地図システム v3.0** - 日本文学の地理的探求を支援する統合システム