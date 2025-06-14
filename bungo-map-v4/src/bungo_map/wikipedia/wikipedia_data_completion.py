#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wikipedia データ補完システム v4
データベース作者情報の自動補完
"""

import sqlite3
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
from datetime import datetime

from .wikipedia_extractor import WikipediaExtractor

try:
    from ..utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class WikipediaDataCompletion:
    """データベース作者情報のWikipedia自動補完"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.extractor = WikipediaExtractor(db_path)
        
    def connect_db(self):
        """データベース接続"""
        return sqlite3.connect(self.db_path)
    
    def get_incomplete_authors(self) -> List[Dict[str, Any]]:
        """補完が必要な作者を取得"""
        with self.connect_db() as conn:
            cursor = conn.cursor()
            
            # Wikipedia情報が不足している作者を検索
            query = """
            SELECT id, name, birth_year, death_year, wikipedia_url, description
            FROM authors 
            WHERE wikipedia_url IS NULL 
               OR birth_year IS NULL 
               OR death_year IS NULL 
               OR description IS NULL
            ORDER BY name
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            authors = []
            for row in rows:
                authors.append({
                    'id': row[0],
                    'name': row[1],
                    'birth_year': row[2],
                    'death_year': row[3],
                    'wikipedia_url': row[4],
                    'description': row[5]
                })
            
            return authors
    
    def complete_author(self, author_id: int, author_name: str, existing_data: Dict) -> Dict[str, Any]:
        """単一作者の情報補完"""
        logger.info(f"📚 作者情報補完開始: {author_name}")
        
        # Wikipedia検索・データ抽出
        completed_data = self.extractor.complete_author_data(author_name, existing_data)
        
        if not completed_data:
            logger.warning(f"⚠️ Wikipedia情報取得失敗: {author_name}")
            return {'success': False, 'error': 'Wikipedia検索失敗'}
        
        # データベース更新
        update_success = self._update_author_in_db(author_id, completed_data)
        
        result = {
            'success': update_success,
            'author_id': author_id,
            'author_name': author_name,
            'completed_data': completed_data,
            'updated_fields': self._get_updated_fields(existing_data, completed_data)
        }
        
        if update_success:
            logger.info(f"✅ 作者情報補完完了: {author_name}")
        else:
            logger.error(f"❌ データベース更新失敗: {author_name}")
        
        return result
    
    def _update_author_in_db(self, author_id: int, data: Dict) -> bool:
        """データベースの作者情報を更新"""
        try:
            with self.connect_db() as conn:
                cursor = conn.cursor()
                
                # 更新クエリ構築
                updates = []
                params = []
                
                if data.get('birth_year'):
                    updates.append("birth_year = ?")
                    params.append(data['birth_year'])
                
                if data.get('death_year'):
                    updates.append("death_year = ?")
                    params.append(data['death_year'])
                
                if data.get('wikipedia_url'):
                    updates.append("wikipedia_url = ?")
                    params.append(data['wikipedia_url'])
                
                if data.get('description'):
                    updates.append("description = ?")
                    params.append(data['description'])
                
                # Wikipedia メタデータを JSON として保存
                if data.get('wikipedia_data'):
                    updates.append("wikipedia_metadata = ?")
                    params.append(json.dumps(data['wikipedia_data'], ensure_ascii=False))
                
                updates.append("updated_at = ?")
                params.append(datetime.now().isoformat())
                
                params.append(author_id)
                
                if updates:
                    query = f"UPDATE authors SET {', '.join(updates)} WHERE id = ?"
                    cursor.execute(query, params)
                    return cursor.rowcount > 0
                
                return False
                
        except Exception as e:
            logger.error(f"データベース更新エラー: {e}")
            return False
    
    def _get_updated_fields(self, existing: Dict, completed: Dict) -> List[str]:
        """更新されたフィールドのリストを取得"""
        updated_fields = []
        
        fields_to_check = ['birth_year', 'death_year', 'wikipedia_url', 'description']
        
        for field in fields_to_check:
            if not existing.get(field) and completed.get(field):
                updated_fields.append(field)
        
        return updated_fields
    
    def complete_all_authors(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """全作者の情報を一括補完"""
        logger.info("🚀 全作者Wikipedia情報補完開始")
        
        # 補完対象作者取得
        incomplete_authors = self.get_incomplete_authors()
        
        if limit:
            incomplete_authors = incomplete_authors[:limit]
        
        logger.info(f"📊 補完対象作者数: {len(incomplete_authors)}")
        
        results = {
            'total_authors': len(incomplete_authors),
            'completed_authors': [],
            'failed_authors': [],
            'stats': {
                'success_count': 0,
                'failure_count': 0,
                'updated_fields': {}
            }
        }
        
        # 各作者の情報補完
        for i, author in enumerate(incomplete_authors, 1):
            logger.info(f"進行状況: {i}/{len(incomplete_authors)} - {author['name']}")
            
            result = self.complete_author(
                author['id'], 
                author['name'], 
                author
            )
            
            if result['success']:
                results['completed_authors'].append(result)
                results['stats']['success_count'] += 1
                
                # 更新フィールド統計
                for field in result['updated_fields']:
                    if field not in results['stats']['updated_fields']:
                        results['stats']['updated_fields'][field] = 0
                    results['stats']['updated_fields'][field] += 1
            else:
                results['failed_authors'].append(result)
                results['stats']['failure_count'] += 1
        
        logger.info(f"✅ 一括補完完了: {results['stats']['success_count']}成功 / {results['stats']['failure_count']}失敗")
        
        return results
    
    def get_completion_status(self) -> Dict[str, Any]:
        """補完状況の統計を取得"""
        with self.connect_db() as conn:
            cursor = conn.cursor()
            
            # 全作者数
            cursor.execute("SELECT COUNT(*) FROM authors")
            total_authors = cursor.fetchone()[0]
            
            # Wikipedia URL有りの作者数
            cursor.execute("SELECT COUNT(*) FROM authors WHERE wikipedia_url IS NOT NULL")
            wikipedia_url_count = cursor.fetchone()[0]
            
            # 生年有りの作者数
            cursor.execute("SELECT COUNT(*) FROM authors WHERE birth_year IS NOT NULL")
            birth_year_count = cursor.fetchone()[0]
            
            # 没年有りの作者数
            cursor.execute("SELECT COUNT(*) FROM authors WHERE death_year IS NOT NULL")
            death_year_count = cursor.fetchone()[0]
            
            # 説明有りの作者数
            cursor.execute("SELECT COUNT(*) FROM authors WHERE description IS NOT NULL")
            description_count = cursor.fetchone()[0]
            
            # 完全補完済み作者数
            cursor.execute("""
                SELECT COUNT(*) FROM authors 
                WHERE wikipedia_url IS NOT NULL 
                  AND birth_year IS NOT NULL 
                  AND death_year IS NOT NULL 
                  AND description IS NOT NULL
            """)
            fully_completed_count = cursor.fetchone()[0]
            
            return {
                'total_authors': total_authors,
                'completion_rates': {
                    'wikipedia_url': round(wikipedia_url_count / total_authors * 100, 1) if total_authors > 0 else 0,
                    'birth_year': round(birth_year_count / total_authors * 100, 1) if total_authors > 0 else 0,
                    'death_year': round(death_year_count / total_authors * 100, 1) if total_authors > 0 else 0,
                    'description': round(description_count / total_authors * 100, 1) if total_authors > 0 else 0,
                    'fully_completed': round(fully_completed_count / total_authors * 100, 1) if total_authors > 0 else 0
                },
                'counts': {
                    'wikipedia_url': wikipedia_url_count,
                    'birth_year': birth_year_count,
                    'death_year': death_year_count,
                    'description': description_count,
                    'fully_completed': fully_completed_count,
                    'incomplete': total_authors - fully_completed_count
                }
            }
    
    def test_completion(self, author_name: str) -> Dict[str, Any]:
        """補完機能のテスト"""
        logger.info(f"🧪 Wikipedia補完テスト: {author_name}")
        
        # テストデータ作成
        test_author = {
            'id': -1,
            'name': author_name,
            'birth_year': None,
            'death_year': None,
            'wikipedia_url': None,
            'description': None
        }
        
        # 抽出テスト（データベース更新なし）
        test_result = self.extractor.test_extraction(author_name)
        
        return {
            'test_author': test_author,
            'extraction_result': test_result,
            'recommendation': self._get_completion_recommendation(test_result)
        }
    
    def _get_completion_recommendation(self, test_result: Dict) -> str:
        """補完推奨レベルを取得"""
        quality_score = test_result.get('data_quality', 0)
        
        if quality_score >= 6:
            return "推奨：高品質データが取得可能"
        elif quality_score >= 4:
            return "条件付き推奨：一部データ欠損の可能性"
        elif quality_score >= 2:
            return "注意：データ品質が低い可能性"
        else:
            return "非推奨：信頼できるデータが取得困難" 