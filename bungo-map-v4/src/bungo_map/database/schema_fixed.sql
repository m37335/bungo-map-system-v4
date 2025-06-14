-- Bungo Map System v4.0 Database Schema (修正版)
-- センテンス中心アーキテクチャ + 作者・作品テーブル

-- 1. 作者テーブル
CREATE TABLE authors (
    author_id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_name TEXT UNIQUE NOT NULL,
    author_name_kana TEXT,
    birth_year INTEGER,
    death_year INTEGER,
    birth_place TEXT,
    death_place TEXT,
    period TEXT, -- 明治・大正・昭和・平成
    major_works TEXT, -- JSON配列形式
    wikipedia_url TEXT,
    description TEXT,
    portrait_url TEXT,
    
    -- 統計情報
    works_count INTEGER DEFAULT 0,
    total_sentences INTEGER DEFAULT 0,
    
    -- メタデータ
    source_system TEXT DEFAULT 'v4.0',
    verification_status TEXT DEFAULT 'pending' CHECK(verification_status IN ('pending', 'verified', 'rejected')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. 作品テーブル
CREATE TABLE works (
    work_id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_title TEXT NOT NULL,
    author_id INTEGER NOT NULL,
    publication_year INTEGER,
    genre TEXT, -- 小説、随筆、詩、戯曲
    aozora_url TEXT,
    file_path TEXT,
    content_length INTEGER DEFAULT 0,
    sentence_count INTEGER DEFAULT 0,
    place_count INTEGER DEFAULT 0,
    
    -- 青空文庫情報
    aozora_work_id TEXT,
    card_id TEXT,
    copyright_status TEXT,
    input_person TEXT,
    proof_person TEXT,
    
    -- メタデータ
    source_system TEXT DEFAULT 'v4.0',
    processing_status TEXT DEFAULT 'pending' CHECK(processing_status IN ('pending', 'processing', 'completed', 'error')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE
);

-- 3. センテンステーブル（メインエンティティ）
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
    sentence_length INTEGER DEFAULT 0,
    
    -- 品質情報
    quality_score REAL DEFAULT 0.0,
    place_count INTEGER DEFAULT 0,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE
);

-- 4. 地名マスターテーブル（正規化済み）
CREATE TABLE places_master (
    place_id INTEGER PRIMARY KEY AUTOINCREMENT,
    place_name TEXT UNIQUE NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases TEXT, -- JSON配列: ["京都府","京都","みやこ"]
    latitude REAL,
    longitude REAL,
    place_type TEXT CHECK(place_type IN ('都道府県', '市区町村', '有名地名', '郡', '歴史地名', '外国', '架空地名')),
    confidence REAL DEFAULT 0.0 CHECK(confidence >= 0.0 AND confidence <= 1.0),
    description TEXT,
    wikipedia_url TEXT,
    image_url TEXT,
    
    -- 地理情報
    country TEXT DEFAULT '日本',
    prefecture TEXT,
    municipality TEXT,
    district TEXT,
    
    -- 統計情報
    mention_count INTEGER DEFAULT 0,
    author_count INTEGER DEFAULT 0,
    work_count INTEGER DEFAULT 0,
    
    -- メタデータ
    source_system TEXT DEFAULT 'v4.0', -- v3.0からの移行 or 新規
    verification_status TEXT DEFAULT 'pending' CHECK(verification_status IN ('pending', 'verified', 'rejected')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. センテンス-地名関連テーブル（N:N関係）
CREATE TABLE sentence_places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sentence_id INTEGER NOT NULL,
    place_id INTEGER NOT NULL,
    
    -- 抽出情報
    extraction_method TEXT NOT NULL, -- regex_有名地名, ai_compound, simple_place_extractor, etc.
    confidence REAL DEFAULT 0.0 CHECK(confidence >= 0.0 AND confidence <= 1.0),
    position_in_sentence INTEGER, -- 文中での出現位置（文字数）
    
    -- 文脈情報
    context_before TEXT,
    context_after TEXT,
    matched_text TEXT, -- 実際にマッチした文字列
    
    -- 品質管理
    verification_status TEXT DEFAULT 'auto' CHECK(verification_status IN ('auto', 'manual_verified', 'manual_rejected')),
    quality_score REAL DEFAULT 0.0,
    relevance_score REAL DEFAULT 0.0, -- 地名の関連度
    
    -- メタデータ
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (sentence_id) REFERENCES sentences(sentence_id) ON DELETE CASCADE,
    FOREIGN KEY (place_id) REFERENCES places_master(place_id) ON DELETE CASCADE,
    UNIQUE(sentence_id, place_id) -- 同一センテンス内の同一地名重複防止
);

-- 6. インデックス作成（パフォーマンス最適化）

-- 作者テーブル
CREATE INDEX idx_authors_name ON authors(author_name);
CREATE INDEX idx_authors_birth_year ON authors(birth_year);
CREATE INDEX idx_authors_death_year ON authors(death_year);

-- 作品テーブル  
CREATE INDEX idx_works_title ON works(work_title);
CREATE INDEX idx_works_author ON works(author_id);
CREATE INDEX idx_works_year ON works(publication_year);
CREATE INDEX idx_works_genre ON works(genre);

-- センテンステーブル
CREATE INDEX idx_sentences_work_id ON sentences(work_id);
CREATE INDEX idx_sentences_author_id ON sentences(author_id);
CREATE INDEX idx_sentences_text ON sentences(sentence_text);
CREATE INDEX idx_sentences_length ON sentences(sentence_length);

-- 地名マスターテーブル
CREATE INDEX idx_places_master_name ON places_master(place_name);
CREATE INDEX idx_places_master_canonical ON places_master(canonical_name);
CREATE INDEX idx_places_master_type ON places_master(place_type);
CREATE INDEX idx_places_master_location ON places_master(latitude, longitude);
CREATE INDEX idx_places_master_prefecture ON places_master(prefecture);

-- 関連テーブル
CREATE INDEX idx_sentence_places_sentence ON sentence_places(sentence_id);
CREATE INDEX idx_sentence_places_place ON sentence_places(place_id);
CREATE INDEX idx_sentence_places_method ON sentence_places(extraction_method);
CREATE INDEX idx_sentence_places_confidence ON sentence_places(confidence);

-- 7. ビュー作成（よく使用されるクエリの最適化）

-- 地名別センテンス一覧ビュー
CREATE VIEW place_sentences AS
SELECT 
    pm.place_id,
    pm.place_name,
    pm.canonical_name,
    pm.latitude,
    pm.longitude,
    pm.place_type,
    s.sentence_id,
    s.sentence_text,
    s.work_id,
    s.author_id,
    w.work_title,
    a.author_name,
    sp.confidence,
    sp.extraction_method,
    sp.matched_text
FROM places_master pm
JOIN sentence_places sp ON pm.place_id = sp.place_id
JOIN sentences s ON sp.sentence_id = s.sentence_id
JOIN works w ON s.work_id = w.work_id
JOIN authors a ON s.author_id = a.author_id;

-- センテンス別地名一覧ビュー
CREATE VIEW sentence_places_view AS
SELECT 
    s.sentence_id,
    s.sentence_text,
    s.work_id,
    s.author_id,
    w.work_title,
    a.author_name,
    pm.place_id,
    pm.place_name,
    pm.canonical_name,
    pm.latitude,
    pm.longitude,
    pm.place_type,
    sp.confidence,
    sp.extraction_method,
    sp.position_in_sentence
FROM sentences s
JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
JOIN places_master pm ON sp.place_id = pm.place_id
JOIN works w ON s.work_id = w.work_id
JOIN authors a ON s.author_id = a.author_id;

-- 作者別地名統計ビュー  
CREATE VIEW author_place_statistics AS
SELECT 
    a.author_id,
    a.author_name,
    a.birth_year,
    a.death_year,
    pm.place_id,
    pm.place_name,
    pm.place_type,
    COUNT(sp.id) as mention_count,
    AVG(sp.confidence) as avg_confidence,
    COUNT(DISTINCT s.work_id) as work_count
FROM authors a
JOIN sentences s ON a.author_id = s.author_id
JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
JOIN places_master pm ON sp.place_id = pm.place_id
GROUP BY a.author_id, pm.place_id;

-- 作品別地名統計ビュー
CREATE VIEW work_place_statistics AS
SELECT 
    w.work_id,
    w.work_title,
    w.author_id,
    a.author_name,
    pm.place_id,
    pm.place_name,
    pm.place_type,
    COUNT(sp.id) as mention_count,
    AVG(sp.confidence) as avg_confidence
FROM works w
JOIN authors a ON w.author_id = a.author_id
JOIN sentences s ON w.work_id = s.work_id
JOIN sentence_places sp ON s.sentence_id = sp.sentence_id
JOIN places_master pm ON sp.place_id = pm.place_id
GROUP BY w.work_id, pm.place_id;

-- 統計情報ビュー（拡張版）
CREATE VIEW statistics_summary AS
SELECT 
    (SELECT COUNT(*) FROM authors) as total_authors,
    (SELECT COUNT(*) FROM works) as total_works,
    (SELECT COUNT(*) FROM sentences) as total_sentences,
    (SELECT COUNT(*) FROM places_master) as total_places,
    (SELECT COUNT(*) FROM sentence_places) as total_relations,
    (SELECT COUNT(DISTINCT work_id) FROM sentences) as processed_works,
    (SELECT COUNT(DISTINCT author_id) FROM sentences) as processed_authors,
    (SELECT AVG(confidence) FROM sentence_places) as avg_confidence,
    (SELECT MAX(sentence_length) FROM sentences) as max_sentence_length,
    (SELECT AVG(sentence_length) FROM sentences) as avg_sentence_length;

-- 地名タイプ別統計ビュー
CREATE VIEW place_type_statistics AS
SELECT 
    pm.place_type,
    COUNT(pm.place_id) as place_count,
    COUNT(sp.id) as mention_count,
    AVG(sp.confidence) as avg_confidence,
    COUNT(DISTINCT s.author_id) as author_count,
    COUNT(DISTINCT s.work_id) as work_count
FROM places_master pm
LEFT JOIN sentence_places sp ON pm.place_id = sp.place_id
LEFT JOIN sentences s ON sp.sentence_id = s.sentence_id
GROUP BY pm.place_type;

-- 8. トリガー（データ整合性維持）

-- updated_at自動更新トリガー
CREATE TRIGGER update_authors_timestamp 
    AFTER UPDATE ON authors
BEGIN
    UPDATE authors SET updated_at = CURRENT_TIMESTAMP WHERE author_id = NEW.author_id;
END;

CREATE TRIGGER update_works_timestamp 
    AFTER UPDATE ON works
BEGIN
    UPDATE works SET updated_at = CURRENT_TIMESTAMP WHERE work_id = NEW.work_id;
END;

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

-- 統計カウンタ更新トリガー
CREATE TRIGGER update_place_mention_count 
    AFTER INSERT ON sentence_places
BEGIN
    UPDATE places_master 
    SET mention_count = mention_count + 1 
    WHERE place_id = NEW.place_id;
END;

CREATE TRIGGER update_sentence_place_count 
    AFTER INSERT ON sentence_places
BEGIN
    UPDATE sentences 
    SET place_count = place_count + 1 
    WHERE sentence_id = NEW.sentence_id;
END; 