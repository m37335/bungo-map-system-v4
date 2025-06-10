-- AI分析結果とジオコーディング管理のための列追加
-- 実行日: 2025-06-09

-- AI分析結果保存用列
ALTER TABLE places ADD COLUMN ai_confidence REAL;
ALTER TABLE places ADD COLUMN ai_place_type TEXT;
ALTER TABLE places ADD COLUMN ai_is_valid BOOLEAN;
ALTER TABLE places ADD COLUMN ai_normalized_name TEXT;
ALTER TABLE places ADD COLUMN ai_reasoning TEXT;
ALTER TABLE places ADD COLUMN ai_analyzed_at TIMESTAMP;

-- ジオコーディング管理用列
ALTER TABLE places ADD COLUMN geocoding_status TEXT DEFAULT 'pending';
ALTER TABLE places ADD COLUMN geocoding_source TEXT;
ALTER TABLE places ADD COLUMN geocoding_updated_at TIMESTAMP;
ALTER TABLE places ADD COLUMN geocoding_accuracy TEXT;

-- インデックス追加（パフォーマンス向上）
CREATE INDEX idx_places_ai_confidence ON places(ai_confidence);
CREATE INDEX idx_places_ai_valid ON places(ai_is_valid);
CREATE INDEX idx_places_geocoding_status ON places(geocoding_status);
CREATE INDEX idx_places_ai_analyzed ON places(ai_analyzed_at); 