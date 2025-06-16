-- Bungo Map System v4.0 Database Schema
-- センテンス中心アーキテクチャ

-- 1. センテンステーブル（メインエンティティ）
CREATE TABLE sentences (
    sentence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 地名マスターテーブル（正規化済み）
CREATE TABLE places_master (
    place_id INTEGER PRIMARY KEY AUTOINCREMENT,
    place_name TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases TEXT,
    latitude REAL,
    longitude REAL,
    place_type TEXT NOT NULL CHECK(place_type IN ('都道府県', '市区町村', '有名地名', '郡', '歴史地名')),
    confidence REAL,
    description TEXT,
    wikipedia_url TEXT,
    image_url TEXT,
    prefecture TEXT,
    municipality TEXT,
    district TEXT,
    source_system TEXT,
    verification_status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- 3. センテンス-地名関連テーブル（N:N関係）
CREATE TABLE sentence_places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sentence_id INTEGER NOT NULL,
    place_id INTEGER NOT NULL,
    extraction_method TEXT,
    confidence REAL,
    normalized_name TEXT,
    prev_sentence TEXT,
    next_sentence TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(sentence_id) REFERENCES sentences(sentence_id),
    FOREIGN KEY(place_id) REFERENCES places_master(place_id)
);

-- 4. 正規化履歴
CREATE TABLE normalizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place_id INTEGER NOT NULL,
    before_name TEXT,
    after_name TEXT,
    method TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(place_id) REFERENCES places_master(place_id)
);

-- 5. ユーザー管理（オプション）
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    role TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. インデックス作成（パフォーマンス最適化）
CREATE INDEX idx_places_master_name ON places_master(place_name);
CREATE INDEX idx_sentence_places_sentence_id ON sentence_places(sentence_id);
CREATE INDEX idx_sentence_places_place_id ON sentence_places(place_id);

-- 7. ビュー作成（よく使用されるクエリの最適化）

-- 地名別センテンス一覧ビュー
CREATE VIEW place_sentences AS
SELECT 
    pm.place_id,
    pm.place_name,
    pm.canonical_name,
    pm.latitude,
    pm.longitude,
    s.sentence_id,
    s.text,
    s.source,
    sp.confidence,
    sp.extraction_method,
    sp.normalized_name
FROM places_master pm
JOIN sentence_places sp ON pm.place_id = sp.place_id
JOIN sentences s ON sp.sentence_id = s.sentence_id;

-- センテンス別地名一覧ビュー
CREATE VIEW sentence_places_view AS
SELECT 
    s.sentence_id,
    s.text,
    s.source,
    pm.place_id,
    pm.place_name,
    pm.canonical_name,
    pm.latitude,
    pm.longitude,
    sp.confidence,
    sp.extraction_method,
    sp.normalized_name
FROM sentences s
JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
JOIN places_master pm ON sp.place_id = pm.place_id;

-- 統計情報ビュー
CREATE VIEW statistics_summary AS
SELECT 
    (SELECT COUNT(*) FROM sentences) as total_sentences,
    (SELECT COUNT(*) FROM places_master) as total_places,
    (SELECT COUNT(*) FROM sentence_places) as total_relations,
    (SELECT COUNT(DISTINCT source) FROM sentences) as total_works,
    (SELECT COUNT(DISTINCT place_id) FROM sentence_places) as total_places_with_confidence,
    (SELECT AVG(confidence) FROM sentence_places) as avg_confidence;

-- 8. トリガー（データ整合性維持）

-- updated_at自動更新トリガー
CREATE TRIGGER update_sentences_timestamp 
    AFTER UPDATE ON sentences
BEGIN
    UPDATE sentences SET updated_at = CURRENT_TIMESTAMP WHERE sentence_id = NEW.sentence_id;
END;

CREATE TRIGGER update_places_master_timestamp 
    AFTER UPDATE ON places_master
BEGIN
    UPDATE places_master SET updated_at = CURRENT_TIMESTAMP WHERE place_id = NEW.place_id;
END;

CREATE TRIGGER update_sentence_places_timestamp 
    AFTER UPDATE ON sentence_places
BEGIN
    UPDATE sentence_places SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END; 