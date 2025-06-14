# 🗺️ Bungo Map v4.0

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-4.0.0-orange.svg)](https://github.com/bungo-map/bungo-map-v4)

**文豪作品地名抽出・可視化システム** - センテンス中心アーキテクチャによる次世代文学地理情報システム

## ✨ 特徴

### 🚀 v4.0の革新的改善
- **センテンス中心アーキテクチャ**: v3.0の地名中心から根本的転換
- **重複排除機能**: 20.3%の重複データを自動統合・正規化
- **正規化地名マスター**: 別名・座標・信頼度の統合管理
- **双方向高速検索**: 地名⇄センテンスの効率的クエリ
- **統合ビューシステム**: 複雑JOINクエリの簡素化

### 💎 主要機能
- 📝 **高精度地名抽出**: 4つの手法（都道府県・市区町村・郡・有名地名）
- 🔍 **柔軟な検索システム**: テキスト・地名・複合検索
- 📊 **詳細統計分析**: 作者別・地域別・手法別分析
- 🗺️ **インタラクティブ可視化**: 地図・グラフによる可視化
- 🌐 **REST API**: FastAPIベースの高性能API
- 🛠️ **CLI管理ツール**: データベース管理・移行・分析

## 📋 要件

- Python 3.8+
- SQLite 3
- 1GB+ ディスク容量

## 🚀 クイックスタート

### インストール

```bash
# レポジトリクローン
git clone https://github.com/bungo-map/bungo-map-v4.git
cd bungo-map-v4

# 仮想環境作成・アクティベート
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate     # Windows

# 依存関係インストール
pip install -e .
```

### 基本使用例

```bash
# データベース初期化
bungo-map database init

# サンプルデータ投入
bungo-map data import-sample

# 統計表示
bungo-map analytics summary

# Web API起動
bungo-api --host 0.0.0.0 --port 8000
```

## 📊 システム構成

```
src/bungo_map/
├── 💾 database/           # データベース・モデル
├── 🔍 extractors/         # 地名抽出エンジン
├── 🌐 api/               # Web API (FastAPI)
├── 📊 services/          # ビジネスロジック
├── 🛠️ cli/              # コマンドライン管理
├── 🗺️ visualization/     # データ可視化
└── ⚙️ core/             # 共通ユーティリティ
```

## 🔧 CLI使用例

### データベース管理
```bash
# 初期化
bungo-map database init

# 統計表示  
bungo-map database stats

# バックアップ
bungo-map database backup --output backup_20231201.db
```

### データ分析
```bash
# 全体サマリー
bungo-map analytics summary

# 地名統計
bungo-map analytics places --top 20

# 作者別統計
bungo-map analytics authors
```

### 検索機能
```bash
# 地名検索
bungo-map search place "京都" --limit 10

# テキスト検索
bungo-map search text "漱石" --min-confidence 0.8

# 複合検索
bungo-map search advanced --place "東京" --text "明治" 
```

## 🌐 Web API

### API起動
```bash
# 開発サーバー
bungo-api --debug

# プロダクション
bungo-api --host 0.0.0.0 --port 8000 --workers 4
```

### API エンドポイント例
```bash
# 統計情報
curl http://localhost:8000/api/v1/statistics

# 地名検索
curl "http://localhost:8000/api/v1/search/places?q=京都&limit=10"

# センテンス検索
curl "http://localhost:8000/api/v1/search/sentences?q=漱石&min_confidence=0.7"

# 分析データ
curl http://localhost:8000/api/v1/analytics/summary
```

## 📈 パフォーマンス指標

### v3.0からの移行結果
- **データ量**: 5,268件 → 4,197センテンス (20.3%重複削減)
- **地名マスター**: 527件に正規化統合
- **処理速度**: 78.3レコード/秒
- **平均信頼度**: 0.723 (高品質データ)

### ベンチマーク
- **検索速度**: <100ms (10,000件データ)
- **API応答**: <50ms (平均)
- **メモリ使用量**: <500MB (通常運用)

## 🧪 テスト

```bash
# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=src/bungo_map --cov-report=html

# 特定テスト
pytest tests/test_database.py -v

# パフォーマンステスト
pytest tests/test_performance.py -m slow
```

## 📦 開発

### 開発環境セットアップ
```bash
# 開発用依存関係
pip install -e ".[dev]"

# pre-commitフック
pre-commit install

# コード整形
black src/
isort src/

# 型チェック
mypy src/bungo_map/
```

### 新機能追加
1. feature/新機能名 ブランチ作成
2. テスト作成・実装
3. ドキュメント更新
4. プルリクエスト作成

## 📚 ドキュメント

- [📖 完全ガイド](docs/guide.md)
- [🏗️ アーキテクチャ](docs/architecture.md) 
- [🌐 API仕様](docs/api.md)
- [🔧 開発者ガイド](docs/development.md)

## 🤝 コントリビューション

1. Issueで提案・バグ報告
2. フォーク・ブランチ作成
3. 変更・テスト実装
4. プルリクエスト作成

詳細は[CONTRIBUTING.md](CONTRIBUTING.md)参照

## 📄 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)参照

## 🙏 謝辞

- 青空文庫プロジェクト
- 日本文学研究コミュニティ
- オープンソースコントリビューター

## 📞 サポート

- 🐛 [バグ報告](https://github.com/bungo-map/bungo-map-v4/issues)
- 💡 [機能提案](https://github.com/bungo-map/bungo-map-v4/discussions)
- 📧 [コンタクト](mailto:info@bungomap.dev)

---

**Bungo Map v4.0** - 文学と地理の新しい架け橋 