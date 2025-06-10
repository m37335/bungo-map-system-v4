#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 データベーススキーマ最適化ツール
現在のパイプラインに合わせてplacesテーブルを最適化

Features:
- 未使用カラムの識別
- 必要カラムの確認
- スキーマ最適化の実行
- バックアップ機能
"""

import click
import sqlite3
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaOptimizer:
    """スキーマ最適化クラス"""
    
    def __init__(self, db_path: str = 'data/bungo_production.db'):
        self.db_path = db_path
        
        # 現在のパイプラインで使用されているカラム
        self.active_columns = {
            # 基本地名抽出用
            'place_id': '主キー',
            'work_id': '作品ID（外部キー）',
            'place_name': '地名',
            'before_text': '前文脈',
            'sentence': '該当文（青空文庫クリーナー処理済み）',
            'after_text': '後文脈',
            'aozora_url': '青空文庫URL',
            'confidence': '抽出信頼度',
            'extraction_method': '抽出手法',
            'created_at': '作成日時',
            
            # Geocoding用
            'lat': '緯度',
            'lng': '経度',
            'geocoding_confidence': 'Geocoding信頼度',
            'geocoding_source': 'Geocoding情報源',
            'prefecture': '都道府県',
            'city': '市区町村',
        }
        
        # 現在未使用だが将来的に必要になる可能性があるカラム
        self.future_columns = {
            'ai_confidence': 'AI分析信頼度（将来の高度AI分析用）',
            'ai_place_type': 'AI判定地名タイプ（実在/架空等）',
            'ai_is_valid': 'AI有効性判定',
            'ai_normalized_name': 'AI正規化地名',
            'ai_reasoning': 'AI判定理由',
            'ai_analyzed_at': 'AI分析日時',
        }
        
        # 現在不要になったカラム
        self.deprecated_columns = {
            'geocoding_status': '旧Geocoding状態（新方式では不要）',
            'geocoding_updated_at': '旧Geocoding更新日時（geocoding_sourceで代替）',
            'geocoding_accuracy': '旧Geocoding精度（geocoding_confidenceで代替）',
        }
    
    def analyze_current_schema(self) -> dict:
        """現在のスキーマを分析"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("PRAGMA table_info(places)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        analysis = {
            'total_columns': len(columns),
            'active_columns': [],
            'future_columns': [],
            'deprecated_columns': [],
            'unknown_columns': []
        }
        
        for col_name in columns:
            if col_name in self.active_columns:
                analysis['active_columns'].append(col_name)
            elif col_name in self.future_columns:
                analysis['future_columns'].append(col_name)
            elif col_name in self.deprecated_columns:
                analysis['deprecated_columns'].append(col_name)
            else:
                analysis['unknown_columns'].append(col_name)
        
        return analysis
    
    def check_column_usage(self) -> dict:
        """カラムの実際の使用状況をチェック"""
        usage_stats = {}
        
        with sqlite3.connect(self.db_path) as conn:
            # 各カラムのNULL以外の値の数をカウント
            cursor = conn.execute("SELECT COUNT(*) FROM places")
            total_records = cursor.fetchone()[0]
            
            if total_records == 0:
                return {'total_records': 0, 'column_usage': {}}
            
            # 主要カラムの使用状況
            columns_to_check = [
                'ai_confidence', 'ai_place_type', 'ai_is_valid', 'ai_normalized_name',
                'ai_reasoning', 'ai_analyzed_at', 'geocoding_status', 'geocoding_updated_at',
                'geocoding_accuracy', 'geocoding_confidence', 'prefecture', 'city'
            ]
            
            for column in columns_to_check:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM places WHERE {column} IS NOT NULL")
                    non_null_count = cursor.fetchone()[0]
                    usage_stats[column] = {
                        'non_null_count': non_null_count,
                        'usage_percentage': (non_null_count / total_records) * 100 if total_records > 0 else 0
                    }
                except sqlite3.OperationalError:
                    usage_stats[column] = {'error': 'Column not found'}
        
        return {'total_records': total_records, 'column_usage': usage_stats}
    
    def backup_database(self) -> str:
        """データベースをバックアップ"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.db_path}.backup_{timestamp}"
        
        # SQLiteデータベースのバックアップ
        with sqlite3.connect(self.db_path) as source:
            with sqlite3.connect(backup_path) as backup:
                source.backup(backup)
        
        return backup_path
    
    def create_optimized_schema(self) -> str:
        """最適化されたスキーマのCREATE文を生成"""
        return """
CREATE TABLE places_optimized (
    place_id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    place_name TEXT NOT NULL,
    before_text TEXT,
    sentence TEXT,
    after_text TEXT,
    aozora_url TEXT,
    confidence REAL DEFAULT 0.0,
    extraction_method TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Geocoding結果
    lat REAL,
    lng REAL,
    geocoding_confidence REAL,
    geocoding_source TEXT,
    prefecture TEXT,
    city TEXT,
    
    -- 将来のAI分析用（予約）
    ai_confidence REAL,
    ai_place_type TEXT,
    ai_is_valid BOOLEAN,
    ai_normalized_name TEXT,
    ai_reasoning TEXT,
    ai_analyzed_at TIMESTAMP,
    
    FOREIGN KEY (work_id) REFERENCES works (work_id)
);

-- インデックス
CREATE INDEX idx_places_opt_work_id ON places_optimized(work_id);
CREATE INDEX idx_places_opt_place_name ON places_optimized(place_name);
CREATE INDEX idx_places_opt_confidence ON places_optimized(confidence);
CREATE INDEX idx_places_opt_coordinates ON places_optimized(lat, lng);
CREATE INDEX idx_places_opt_extraction_method ON places_optimized(extraction_method);
CREATE INDEX idx_places_opt_prefecture ON places_optimized(prefecture);
"""
    
    def migrate_data(self, dry_run: bool = True) -> dict:
        """データを最適化されたテーブルに移行"""
        if dry_run:
            click.echo("🔍 ドライランモード - 実際の変更は行いません")
        
        migration_stats = {
            'backup_created': False,
            'old_table_renamed': False,
            'new_table_created': False,
            'data_migrated': False,
            'records_migrated': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                if not dry_run:
                    # バックアップ作成
                    backup_path = self.backup_database()
                    migration_stats['backup_created'] = backup_path
                    click.echo(f"✅ バックアップ作成: {backup_path}")
                    
                    # 古いテーブルをリネーム
                    conn.execute("ALTER TABLE places RENAME TO places_old")
                    migration_stats['old_table_renamed'] = True
                    click.echo("✅ 古いテーブルをplaces_oldにリネーム")
                    
                    # 新しいテーブル作成
                    conn.execute("DROP TABLE IF EXISTS places_optimized")
                    conn.executescript(self.create_optimized_schema())
                    conn.execute("ALTER TABLE places_optimized RENAME TO places")
                    migration_stats['new_table_created'] = True
                    click.echo("✅ 最適化されたテーブル作成")
                    
                    # データ移行
                    conn.execute("""
                        INSERT INTO places (
                            place_id, work_id, place_name, before_text, sentence, after_text,
                            aozora_url, confidence, extraction_method, created_at,
                            lat, lng, geocoding_confidence, geocoding_source, prefecture, city
                        )
                        SELECT 
                            place_id, work_id, place_name, before_text, sentence, after_text,
                            aozora_url, confidence, extraction_method, created_at,
                            lat, lng, geocoding_confidence, geocoding_source, prefecture, city
                        FROM places_old
                    """)
                    
                    # 移行レコード数確認
                    cursor = conn.execute("SELECT COUNT(*) FROM places")
                    migration_stats['records_migrated'] = cursor.fetchone()[0]
                    migration_stats['data_migrated'] = True
                    
                    click.echo(f"✅ データ移行完了: {migration_stats['records_migrated']}件")
                else:
                    # ドライランでは移行予定レコード数のみ表示
                    cursor = conn.execute("SELECT COUNT(*) FROM places")
                    migration_stats['records_migrated'] = cursor.fetchone()[0]
                    click.echo(f"📊 移行予定レコード数: {migration_stats['records_migrated']}件")
                
        except Exception as e:
            logger.error(f"移行エラー: {e}")
            migration_stats['error'] = str(e)
        
        return migration_stats

@click.command()
@click.option('--analyze-only', is_flag=True, help='分析のみ実行（変更は行わない）')
@click.option('--migrate', is_flag=True, help='スキーマ最適化移行を実行')
@click.option('--dry-run', is_flag=True, help='ドライランモード')
def main(analyze_only: bool, migrate: bool, dry_run: bool):
    """データベーススキーマ最適化ツール"""
    optimizer = SchemaOptimizer()
    
    click.echo("🔧 データベーススキーマ最適化ツール")
    click.echo("=" * 60)
    
    # 1. 現在のスキーマ分析
    analysis = optimizer.analyze_current_schema()
    click.echo(f"📊 スキーマ分析結果:")
    click.echo(f"  総カラム数: {analysis['total_columns']}")
    click.echo(f"  ✅ 使用中: {len(analysis['active_columns'])}件")
    click.echo(f"  🔮 将来用: {len(analysis['future_columns'])}件")
    click.echo(f"  ⚠️  非推奨: {len(analysis['deprecated_columns'])}件")
    click.echo(f"  ❓ 不明: {len(analysis['unknown_columns'])}件")
    
    # 2. カラム使用状況確認
    usage = optimizer.check_column_usage()
    if usage['total_records'] > 0:
        click.echo(f"\n📈 カラム使用状況 (総レコード数: {usage['total_records']}):")
        for column, stats in usage['column_usage'].items():
            if 'error' in stats:
                click.echo(f"  {column}: エラー")
            else:
                click.echo(f"  {column}: {stats['non_null_count']}件 ({stats['usage_percentage']:.1f}%)")
    
    # 3. 推奨アクション表示
    click.echo(f"\n💡 推奨アクション:")
    if analysis['deprecated_columns']:
        click.echo(f"  ⚠️  非推奨カラム削除: {', '.join(analysis['deprecated_columns'])}")
    
    if analysis['future_columns']:
        click.echo(f"  🔮 将来用カラム保持: {', '.join(analysis['future_columns'])}")
    
    if not analyze_only and migrate:
        click.echo(f"\n🚀 スキーマ最適化移行実行...")
        migration_result = optimizer.migrate_data(dry_run=dry_run)
        
        if migration_result.get('error'):
            click.echo(f"❌ 移行失敗: {migration_result['error']}")
        else:
            click.echo(f"✅ 移行成功!")
            if migration_result.get('backup_created'):
                click.echo(f"   バックアップ: {migration_result['backup_created']}")

if __name__ == '__main__':
    main() 