#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 強化地名抽出パターン
現在のregexパターンを改良してより精密な地名抽出を実現
"""

import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class RegexPattern:
    """正規表現パターンの定義"""
    name: str
    pattern: str
    category: str
    confidence: float
    description: str

class EnhancedRegexPatterns:
    """強化された正規表現パターン集"""
    
    def __init__(self):
        self.patterns = self._build_enhanced_patterns()
        self.problematic_patterns = self._build_problematic_patterns()
    
    def _build_enhanced_patterns(self) -> List[RegexPattern]:
        """改良された地名抽出パターンを構築"""
        return [
            # 1. 都道府県（境界条件強化版）
            RegexPattern(
                name="都道府県_強化",
                pattern=r'(?<![一-龯])[北海青森岩手宮城秋田山形福島茨城栃木群馬埼玉千葉東京神奈川新潟富山石川福井山梨長野岐阜静岡愛知三重滋賀京都大阪兵庫奈良和歌山鳥取島根岡山広島山口徳島香川愛媛高知福岡佐賀長崎熊本大分宮崎鹿児島沖縄][都道府県](?![一-龯])',
                category="都道府県",
                confidence=0.95,
                description="都道府県名（前後に漢字がない場合のみ）"
            ),
            
            # 2. 東京中心部
            RegexPattern(
                name="東京中心部",
                pattern=r'(?:銀座|新宿|渋谷|上野|浅草|品川|池袋|新橋|有楽町|丸の内|表参道|原宿|恵比寿|六本木|赤坂|青山|麻布|目黒|世田谷|本郷|神田|日本橋|築地|月島|両国|浅草橋|秋葉原)',
                category="東京中心部",
                confidence=0.90,
                description="東京都心の主要地名"
            ),
            
            # 3. 古典地名
            RegexPattern(
                name="古典地名",
                pattern=r'(?:平安京|江戸|武蔵|相模|甲斐|信濃|越後|下野|上野|駿河|伊豆|伊勢|山城|大和|河内|和泉|摂津|近江|美濃|尾張|薩摩|土佐|陸奥|出羽)',
                category="古典地名",
                confidence=0.92,
                description="古典文学・歴史文献に出る地名"
            ),
        ]
    
    def _build_problematic_patterns(self) -> List[RegexPattern]:
        """問題のあるパターンを定義"""
        return [
            RegexPattern(
                name="方向語",
                pattern=r'(?<![一-龯])[東西南北上下左右前後中内外](?=から|へ|に向かって|を見て)',
                category="方向",
                confidence=0.0,
                description="方向を示す語"
            ),
            
            RegexPattern(
                name="植物名",
                pattern=r'(?<![一-龯])[桜梅松竹萩楓菊蓮藤椿牡丹](?=[がの](?:咲く|散る|茂る|延びる|花|葉|木))',
                category="植物",
                confidence=0.0,
                description="植物名（植物的文脈）"
            ),
        ]
    
    def analyze_current_patterns(self) -> Dict:
        """現在のパターンの分析結果を返す"""
        return {
            "enhanced_patterns": len(self.patterns),
            "problematic_patterns": len(self.problematic_patterns),
            "categories": list(set(p.category for p in self.patterns)),
            "recommendations": [
                "境界条件（前後の文字チェック）を追加",
                "文脈依存パターンの導入",
                "階層的分類による信頼度調整",
                "問題パターンの明示的定義"
            ]
        }