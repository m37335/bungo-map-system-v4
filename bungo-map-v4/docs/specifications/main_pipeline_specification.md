# 文豪ゆかり地図システム v4.0 詳細仕様書

## 1. システム概要

### 1.1 目的
文豪作品から地名を抽出し、地理情報として可視化するシステム。センテンス中心のアーキテクチャを採用し、高精度な地名抽出と地理情報の管理を実現する。

### 1.2 主要機能
- 青空文庫からの作品取得
- テキストクリーニング
- 地名抽出
- ジオコーディング
- データベース管理
- 統計情報の提供

## 2. システム構成

### 2.1 コンポーネント構成
```
src/bungo_map/
├── core/          - コア機能
├── database/      - データベース管理
├── extractors/    - 地名抽出エンジン
├── api/          - Web API
├── services/     - ビジネスロジック
├── cli/          - コマンドライン管理
└── visualization/ - データ可視化
```

### 2.2 主要クラス
- `MainPipeline`: メインパイプライン統合クラス
- `ExtractionPipeline`: 地名抽出パイプライン
- `DatabaseManager`: データベース管理
- `AozoraClient`: 青空文庫クライアント
- `ContextAwareGeocoder`: ジオコーディング

## 3. 処理フロー詳細

### 3.1 メインパイプライン（MainPipeline）

#### 3.1.1 初期化
```python
def __init__(self, db_path: str):
    self.db_path = db_path
    self.db = DatabaseManager(db_path)
    self.aozora_client = AozoraClient()
    self.aozora_cleaner = AozoraCleaner()
    self.extraction_pipeline = ExtractionPipeline()
    self.geocoder = ContextAwareGeocoder()
```

#### 3.1.2 作品処理フロー
1. **作品取得**
   - 青空文庫から作品内容を取得
   - エラーハンドリングとリトライ処理

2. **テキストクリーニング**
   - テキストの正規化
   - 不要な文字の除去
   - 文字コードの統一

3. **データベース登録**
   - 作者情報の登録/取得
   - 作品情報の登録
   - トランザクション管理

4. **地名抽出**
   - センテンス単位での処理
   - 地名の抽出と正規化
   - コンテキスト情報の保持

5. **ジオコーディング**
   - 地名の座標取得
   - 信頼度スコアの計算
   - エラー処理とリトライ

6. **データベース保存**
   - 抽出地名の保存
   - 関連情報の更新
   - インデックス更新

### 3.2 地名抽出パイプライン（ExtractionPipeline）

#### 3.2.1 センテンス処理
```python
def process_sentence(self, sentence_text: str, work_id: int = None, author_id: int = None):
    # 地名抽出
    places = self.sentence_extractor.extract_places_from_sentence(
        sentence_text, work_id, author_id
    )
    
    # 地名正規化
    normalized_places = []
    for place in places:
        normalized = self._normalize_extracted_place(place)
        normalized_places.append(normalized)
```

## 4. 設定仕様

### 4.1 データベース設定
```yaml
database:
  path: "data/bungo_v4.db"
  backup_dir: "data/backups"
  vacuum_after_reset: true
```

### 4.2 パイプライン設定
```yaml
pipeline:
  batch_size: 10
  geocoding_confidence: 0.5
  quality_threshold: 0.7
  max_retries: 3
  timeout: 30
```

### 4.3 AI設定
```yaml
ai:
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 1000
  context_window: 2000
```

## 5. エラーハンドリング

### 5.1 エラー種別
- ネットワークエラー
- データベースエラー
- パースエラー
- ジオコーディングエラー

### 5.2 エラー処理方針
- リトライ処理
- エラーログ記録
- ユーザーへの通知
- 回復処理

## 6. パフォーマンス仕様

### 6.1 処理速度
- 単一作品処理: 5秒以内
- バッチ処理: 1作品あたり3秒以内
- API応答時間: 100ms以内

### 6.2 リソース使用量
- メモリ使用量: 500MB以下
- ディスク使用量: 1GB以下
- CPU使用率: 50%以下

## 7. セキュリティ仕様

### 7.1 データ保護
- データベース暗号化
- アクセス制御
- バックアップ管理

### 7.2 APIセキュリティ
- 認証・認可
- レート制限
- 入力バリデーション

## 8. 監視・ログ

### 8.1 ログ設定
```yaml
logging:
  level: "INFO"
  file: "logs/bungo_map.log"
  max_size: 10485760  # 10MB
  backup_count: 5
```

### 8.2 監視項目
- 処理成功率
- エラー発生率
- リソース使用率
- パフォーマンス指標

## 9. テスト仕様

### 9.1 テスト種別
- 単体テスト
- 統合テスト
- パフォーマンステスト
- セキュリティテスト

### 9.2 テストカバレッジ
- コードカバレッジ: 80%以上
- 機能カバレッジ: 100%
- エッジケース: 90%以上 