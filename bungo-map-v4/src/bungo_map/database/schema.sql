-- Bungo Map System v4.0 Database Schema
-- センテンス中心アーキテクチャ

-- 1. センテンステーブル（メインエンティティ）
CREATE TABLE sentences (
    sentence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sentence_text TEXT NOT NULL,
    work_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    before_text TEXT,
    after_text TEXT,
    source_info TEXT,
    chapter TEXT,
    page_number INTEGER,
    position_in_work INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- インデックス用
    FOREIGN KEY (work_id) REFERENCES works(work_id),
    FOREIGN KEY (author_id) REFERENCES authors(author_id)
);

-- 2. 地名マスターテーブル（正規化済み）
CREATE TABLE places_master (
    place_id INTEGER PRIMARY KEY AUTOINCREMENT,
    place_name TEXT UNIQUE NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases TEXT, -- JSON配列: ["京都府","京都","みやこ"]
    latitude REAL,
    longitude REAL,
    place_type TEXT CHECK(place_type IN ('都道府県', '市区町村', '有名地名', '郡', '歴史地名')),
    confidence REAL DEFAULT 0.0 CHECK(confidence >= 0.0 AND confidence <= 1.0),
    description TEXT,
    wikipedia_url TEXT,
    image_url TEXT,
    
    -- 地理情報
    prefecture TEXT,
    municipality TEXT,
    district TEXT,
    
    -- メタデータ
    source_system TEXT DEFAULT 'v4.0', -- v3.0からの移行 or 新規
    verification_status TEXT DEFAULT 'pending' CHECK(verification_status IN ('pending', 'verified', 'rejected')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. センテンス-地名関連テーブル（N:N関係）
CREATE TABLE sentence_places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sentence_id INTEGER NOT NULL,
    place_id INTEGER NOT NULL,
    
    -- 抽出情報
    extraction_method TEXT NOT NULL, -- regex_有名地名, ai_compound, etc.
    confidence REAL DEFAULT 0.0 CHECK(confidence >= 0.0 AND confidence <= 1.0),
    position_in_sentence INTEGER, -- 文中での出現位置（文字数）
    
    -- 文脈情報
    context_before TEXT,
    context_after TEXT,
    matched_text TEXT, -- 実際にマッチした文字列
    
    -- 品質管理
    verification_status TEXT DEFAULT 'auto' CHECK(verification_status IN ('auto', 'manual_verified', 'manual_rejected')),
    quality_score REAL DEFAULT 0.0,
    
    -- メタデータ
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (sentence_id) REFERENCES sentences(sentence_id) ON DELETE CASCADE,
    FOREIGN KEY (place_id) REFERENCES places_master(place_id) ON DELETE CASCADE,
    UNIQUE(sentence_id, place_id) -- 同一センテンス内の同一地名重複防止
);

-- 4. インデックス作成（パフォーマンス最適化）
CREATE INDEX idx_sentences_work_id ON sentences(work_id);
CREATE INDEX idx_sentences_author_id ON sentences(author_id);
CREATE INDEX idx_sentences_text ON sentences(sentence_text);

CREATE INDEX idx_places_master_name ON places_master(place_name);
CREATE INDEX idx_places_master_canonical ON places_master(canonical_name);
CREATE INDEX idx_places_master_type ON places_master(place_type);
CREATE INDEX idx_places_master_location ON places_master(latitude, longitude);

CREATE INDEX idx_sentence_places_sentence ON sentence_places(sentence_id);
CREATE INDEX idx_sentence_places_place ON sentence_places(place_id);
CREATE INDEX idx_sentence_places_method ON sentence_places(extraction_method);
CREATE INDEX idx_sentence_places_confidence ON sentence_places(confidence);

-- 5. ビュー作成（よく使用されるクエリの最適化）

-- 地名別センテンス一覧ビュー
CREATE VIEW place_sentences AS
SELECT 
    pm.place_id,
    pm.place_name,
    pm.canonical_name,
    pm.latitude,
    pm.longitude,
    s.sentence_id,
    s.sentence_text,
    s.work_id,
    s.author_id,
    sp.confidence,
    sp.extraction_method,
    sp.matched_text
FROM places_master pm
JOIN sentence_places sp ON pm.place_id = sp.place_id
JOIN sentences s ON sp.sentence_id = s.sentence_id;

-- センテンス別地名一覧ビュー
CREATE VIEW sentence_places_view AS
SELECT 
    s.sentence_id,
    s.sentence_text,
    s.work_id,
    s.author_id,
    pm.place_id,
    pm.place_name,
    pm.canonical_name,
    pm.latitude,
    pm.longitude,
    sp.confidence,
    sp.extraction_method,
    sp.position_in_sentence
FROM sentences s
JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
JOIN places_master pm ON sp.place_id = pm.place_id;

-- 統計情報ビュー
CREATE VIEW statistics_summary AS
SELECT 
    (SELECT COUNT(*) FROM sentences) as total_sentences,
    (SELECT COUNT(*) FROM places_master) as total_places,
    (SELECT COUNT(*) FROM sentence_places) as total_relations,
    (SELECT COUNT(DISTINCT work_id) FROM sentences) as total_works,
    (SELECT COUNT(DISTINCT author_id) FROM sentences) as total_authors,
    (SELECT AVG(confidence) FROM sentence_places) as avg_confidence;

-- 6. トリガー（データ整合性維持）

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