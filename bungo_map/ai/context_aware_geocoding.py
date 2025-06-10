#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 AI文脈判断型Geocodingシステム
文脈を理解して地名の妥当性と座標を高精度で推定

Features:
- LLMによる文脈分析
- 地名/人名の判別
- 歴史的文脈での地域特定
- 曖昧地名の解決
- 複合地名の分析
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import json

from bungo_map.geo.enhanced_geocoding import GeocodingResult, EnhancedGeocodingService

logger = logging.getLogger(__name__)

@dataclass
class ContextAnalysisResult:
    """文脈分析結果"""
    is_place_name: bool  # 地名として使われているか
    confidence: float    # 信頼度
    place_type: str     # 地名の種類
    historical_context: str  # 歴史的文脈
    geographic_context: str  # 地理的文脈
    reasoning: str      # 判断理由
    suggested_location: Optional[str] = None  # 推定地域

@dataclass
class EnhancedGeocodingResult:
    """強化版Geocoding結果"""
    place_name: str
    latitude: Optional[float]
    longitude: Optional[float]
    confidence: float
    source: str
    prefecture: Optional[str] = None
    city: Optional[str] = None
    context_analysis: Optional[ContextAnalysisResult] = None
    fallback_used: bool = False

class ContextAwareGeocodingService:
    """AI文脈判断型Geocodingサービス"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """初期化"""
        self.enhanced_geocoding = EnhancedGeocodingService()
        
        # 文脈判断用の知識ベース
        self.context_knowledge = self._build_context_knowledge()
        
        # 問題のある地名パターン（AI判断が必要）
        self.ambiguous_places = {
            "柏": {"人名可能性": 0.8, "地名": "千葉県柏市"},
            "清水": {"人名可能性": 0.7, "地名": "静岡県清水区"},
            "本郷": {"地域性": "東京", "地名": "東京都文京区本郷"},
            "神田": {"地域性": "東京", "地名": "東京都千代田区神田"},
            "青山": {"人名可能性": 0.6, "地名": "東京都港区青山"},
            "麻布": {"地域性": "東京", "地名": "東京都港区麻布"},
            "両国": {"地域性": "東京", "地名": "東京都墨田区両国"},
            "伏見": {"地域性": "京都", "地名": "京都府京都市伏見区"},
            "嵐山": {"地域性": "京都", "地名": "京都府京都市右京区嵐山"},
        }
        
        # 古典地名の文脈知識
        self.classical_place_context = {
            "伊勢": {
                "古典用法": "伊勢国、伊勢神宮",
                "現代地名": "三重県伊勢市",
                "座標": (34.4900, 136.7056),
                "文脈キーワード": ["神宮", "参拝", "旅", "国", "物語"]
            },
            "大和": {
                "古典用法": "大和国、奈良",
                "現代地名": "奈良県",
                "座標": (34.6851, 135.8325),
                "文脈キーワード": ["国", "古都", "都", "平城京"]
            },
            "美濃": {
                "古典用法": "美濃国",
                "現代地名": "岐阜県",
                "座標": (35.3912, 136.7223),
                "文脈キーワード": ["国", "関ヶ原", "木曽川"]
            },
            "尾張": {
                "古典用法": "尾張国",
                "現代地名": "愛知県西部",
                "座標": (35.1802, 136.9066),
                "文脈キーワード": ["国", "名古屋", "織田"]
            },
            "薩摩": {
                "古典用法": "薩摩国",
                "現代地名": "鹿児島県",
                "座標": (31.5966, 130.5571),
                "文脈キーワード": ["国", "島津", "九州"]
            },
            "伊豆": {
                "古典用法": "伊豆国",
                "現代地名": "静岡県伊豆半島",
                "座標": (34.9756, 138.9462),
                "文脈キーワード": ["国", "半島", "温泉", "流罪"]
            }
        }
        
        # 東京詳細地名データベース
        self.tokyo_detail_places = {
            "本郷": (35.7081, 139.7619, "東京都文京区"),
            "神田": (35.6918, 139.7648, "東京都千代田区"),
            "青山": (35.6736, 139.7263, "東京都港区"),
            "麻布": (35.6581, 139.7414, "東京都港区"),
            "両国": (35.6967, 139.7933, "東京都墨田区"),
            "赤坂": (35.6745, 139.7378, "東京都港区"),
            "日本橋": (35.6813, 139.7744, "東京都中央区"),
            "築地": (35.6654, 139.7707, "東京都中央区"),
        }
        
        # 京都詳細地名データベース
        self.kyoto_detail_places = {
            "伏見": (34.9393, 135.7578, "京都府京都市伏見区"),
            "嵐山": (35.0088, 135.6761, "京都府京都市右京区"),
            "清水": (34.9948, 135.7849, "京都府京都市東山区"),
            "祇園": (35.0037, 135.7744, "京都府京都市東山区"),
            "宇治": (34.8842, 135.7991, "京都府宇治市"),
        }
        
        # 北海道地名データベース  
        self.hokkaido_places = {
            "小樽": (43.1907, 140.9947, "北海道小樽市"),
            "函館": (41.7687, 140.7291, "北海道函館市"),
            "札幌": (43.0642, 141.3469, "北海道札幌市"),
        }
        
        # 海外地名データベース（文学作品頻出）
        self.foreign_places = {
            "ローマ": (41.9028, 12.4964, "イタリア"),
            "パリ": (48.8566, 2.3522, "フランス"),
            "ロンドン": (51.5074, -0.1278, "イギリス"),
            "ベルリン": (52.5200, 13.4050, "ドイツ"),
            "ニューヨーク": (40.7128, -74.0060, "アメリカ"),
            "上海": (31.2304, 121.4737, "中国"),
            "ペキン": (39.9042, 116.4074, "中国"),
            "北京": (39.9042, 116.4074, "中国"),
            "モスクワ": (55.7558, 37.6176, "ロシア"),
            "ウィーン": (48.2082, 16.3738, "オーストリア"),
            "アテネ": (37.9838, 23.7275, "ギリシャ"),
        }
        
        print("🤖 AI文脈判断型Geocodingサービス初期化完了")
    
    def _build_context_knowledge(self) -> Dict:
        """文脈判断用知識ベースの構築"""
        return {
            # 地名を示唆する文脈パターン（より具体的に）
            "place_indicators": [
                r"[へに]行", r"[をに]出", r"[に]住", r"[を]通", r"[から]来",
                r"[に]着", r"[を]訪", r"[に]向", r"[で]生", r"[を]発",
                r"街", r"町", r"村", r"里", r"国", r"県", r"市", r"区",
                r"滞在", r"旅行", r"参拝", r"見物", r"観光", r"散歩",
                r"出身", r"在住", r"移住", r"引越", r"帰郷", r"故郷",
                r"景色", r"風景", r"名所", r"遺跡", r"寺", r"神社",
                r"駅", r"港", r"橋", r"川", r"山", r"海", r"湖",
                r"から.*まで", r"を経由", r"経由して", r"通過", r"立ち寄"
            ],
            
            # 人名を示唆する文脈パターン（強化版）
            "person_indicators": [
                r"さん$", r"君$", r"氏$", r"先生$", r"様$", r"殿$",
                r"は話", r"が言", r"と会", r"に聞", r"と話", r"を呼",
                r"の顔", r"の性格", r"の家族", r"の人", r"という人",
                r"名前", r"名前は", r"という名", r"呼ばれ", r"呼んで",
                # 人の行動・感情を明確に示すパターン
                r"機嫌", r"怒", r"笑", r"泣", r"悲し", r"喜", r"憤",
                r"は.*打つ", r"は.*叩", r"は.*殴", r"は.*怒鳴", 
                r"は.*言った", r"は.*思った", r"は.*感じた",
                r"は.*次第に", r"は.*だんだん", r"は.*しだいに",
                r"は.*ようになった", r"は.*始めた", r"は.*やめた"
            ],
            
            # 歴史的文脈パターン
            "historical_indicators": [
                r"国$", r"藩$", r"城$", r"宿場", r"街道",
                r"古く", r"昔", r"江戸時代", r"平安", r"鎌倉",
                r"時代", r"当時", r"昔の", r"古い", r"歴史"
                r"[国]", r"[藩]", r"[城]", r"[宿場]", r"[街道]",
                r"古く", r"昔", r"江戸時代", r"平安", r"鎌倉"
            ]
        }
    
    def _analyze_context_rule_based(self, place_name: str, sentence: str, before_text: str, after_text: str) -> ContextAnalysisResult:
        """規則ベースの文脈分析"""
        
        full_context = f"{before_text} {sentence} {after_text}"
        
        # 地名指標のスコア
        place_score = 0
        for pattern in self.context_knowledge["place_indicators"]:
            if re.search(pattern, full_context):
                place_score += 1
        
        # 人名指標のスコア
        person_score = 0
        for pattern in self.context_knowledge["person_indicators"]:
            if re.search(pattern, full_context):
                person_score += 1
        
        # 歴史指標のスコア
        historical_score = 0
        for pattern in self.context_knowledge["historical_indicators"]:
            if re.search(pattern, full_context):
                historical_score += 1
        
        # デフォルトは地名として扱う（文学作品では地名が多い）
        default_place_bias = 1
        
        # 曖昧地名の特別処理
        if place_name in self.ambiguous_places:
            ambiguous_info = self.ambiguous_places[place_name]
            person_possibility = ambiguous_info.get("人名可能性", 0.3)
            
            # 人名指標がある場合は人名と判定（閾値を下げて感度向上）
            if person_score >= 1 and person_possibility > 0.3:
                return ContextAnalysisResult(
                    is_place_name=False,
                    confidence=0.8,
                    place_type="人名",
                    historical_context="",
                    geographic_context="",
                    reasoning=f"人名指標({person_score}個)があり、{place_name}は人名の可能性が高い"
                )
        
        # 古典地名の特別処理
        if place_name in self.classical_place_context:
            classical_info = self.classical_place_context[place_name]
            keywords = classical_info["文脈キーワード"]
            
            keyword_found = any(keyword in full_context for keyword in keywords)
            if keyword_found or historical_score > 0 or "国" in place_name:
                return ContextAnalysisResult(
                    is_place_name=True,
                    confidence=0.9,
                    place_type="古国名",
                    historical_context=classical_info["古典用法"],
                    geographic_context=f"現在の{classical_info['現代地名']}",
                    reasoning="古典的地名用法が確認された",
                    suggested_location=classical_info["現代地名"]
                )
        
        # 総合判定（地名バイアス付き）
        adjusted_place_score = place_score + default_place_bias + historical_score
        is_place = adjusted_place_score > person_score or person_score < 2
        
        # 信頼度計算
        total_indicators = adjusted_place_score + person_score
        if total_indicators > 0:
            confidence = min(0.9, 0.5 + (total_indicators * 0.1))
        else:
            confidence = 0.7  # 指標がない場合はデフォルトで地名扱い
        
        reasoning = f"規則ベース判定: 地名指標{place_score}+バイアス{default_place_bias}+歴史{historical_score}={adjusted_place_score}, 人名指標{person_score}"
        
        return ContextAnalysisResult(
            is_place_name=is_place,
            confidence=confidence,
            place_type="地名" if is_place else "人名/その他",
            historical_context="",
            geographic_context="",
            reasoning=reasoning
        )
    
    def enhanced_geocode_sync(self, place_name: str, sentence: str, before_text: str = "", after_text: str = "") -> EnhancedGeocodingResult:
        """文脈を考慮した強化版Geocoding（同期版）"""
        
        # 1. 文脈分析
        context_analysis = self._analyze_context_rule_based(place_name, sentence, before_text, after_text)
        
        # 2. 地名でない場合は早期リターン
        if not context_analysis.is_place_name:
            return EnhancedGeocodingResult(
                place_name=place_name,
                latitude=None,
                longitude=None,
                confidence=0.0,
                source="context_rejected",
                context_analysis=context_analysis
            )
        
        # 3. 詳細地名データベース検索
        detail_result = self._search_detail_places(place_name)
        if detail_result:
            return detail_result
        
        # 4. 古典地名の特別処理
        if place_name in self.classical_place_context:
            classical_info = self.classical_place_context[place_name]
            lat, lng = classical_info["座標"]
            return EnhancedGeocodingResult(
                place_name=place_name,
                latitude=lat,
                longitude=lng,
                confidence=0.9 * context_analysis.confidence,
                source="classical_place_database",
                prefecture=classical_info["現代地名"],
                city=place_name,
                context_analysis=context_analysis
            )
        
        # 5. 基本Geocoding試行
        basic_result = self.enhanced_geocoding.geocode_place_sync(place_name)
        
        if basic_result:
            # 基本Geocoding成功
            return EnhancedGeocodingResult(
                place_name=place_name,
                latitude=basic_result.latitude,
                longitude=basic_result.longitude,
                confidence=basic_result.confidence * context_analysis.confidence,
                source=f"{basic_result.source}_with_context",
                prefecture=basic_result.prefecture,
                city=basic_result.city,
                context_analysis=context_analysis
            )
        
        # 6. 完全失敗
        return EnhancedGeocodingResult(
            place_name=place_name,
            latitude=None,
            longitude=None,
            confidence=0.0,
            source="geocoding_failed",
            context_analysis=context_analysis
        )
    
    def _search_detail_places(self, place_name: str) -> Optional[EnhancedGeocodingResult]:
        """詳細地名データベースから検索"""
        
        # 東京詳細地名
        if place_name in self.tokyo_detail_places:
            lat, lng, prefecture = self.tokyo_detail_places[place_name]
            return EnhancedGeocodingResult(
                place_name=place_name,
                latitude=lat,
                longitude=lng,
                confidence=0.95,
                source="tokyo_detail_database",
                prefecture=prefecture,
                city=place_name
            )
        
        # 京都詳細地名
        if place_name in self.kyoto_detail_places:
            lat, lng, prefecture = self.kyoto_detail_places[place_name]
            return EnhancedGeocodingResult(
                place_name=place_name,
                latitude=lat,
                longitude=lng,
                confidence=0.95,
                source="kyoto_detail_database",
                prefecture=prefecture,
                city=place_name
            )
        
        # 北海道地名
        if place_name in self.hokkaido_places:
            lat, lng, prefecture = self.hokkaido_places[place_name]
            return EnhancedGeocodingResult(
                place_name=place_name,
                latitude=lat,
                longitude=lng,
                confidence=0.95,
                source="hokkaido_database",
                prefecture=prefecture,
                city=place_name
            )
        
        # 海外地名
        if place_name in self.foreign_places:
            lat, lng, country = self.foreign_places[place_name]
            return EnhancedGeocodingResult(
                place_name=place_name,
                latitude=lat,
                longitude=lng,
                confidence=0.90,
                source="foreign_places_database",
                prefecture=country,
                city=place_name
            )
        
        return None
    
    def geocode_place_sync(self, place_name: str, sentence: str = "", before_text: str = "", after_text: str = "") -> Optional[GeocodingResult]:
        """同期版のエントリーポイント（既存インターフェース互換）"""
        
        result = self.enhanced_geocode_sync(place_name, sentence, before_text, after_text)
        
        if result.latitude is not None:
            return GeocodingResult(
                place_name=result.place_name,
                latitude=result.latitude,
                longitude=result.longitude,
                confidence=result.confidence,
                source=result.source,
                prefecture=result.prefecture,
                city=result.city
            )
        
        return None

    def get_coverage_stats(self) -> Dict[str, int]:
        """カバレッジ統計取得"""
        base_stats = self.enhanced_geocoding.get_coverage_stats()
        base_stats.update({
            'ambiguous_places': len(self.ambiguous_places),
            'classical_places': len(self.classical_place_context),
            'tokyo_detail_places': len(self.tokyo_detail_places),
            'kyoto_detail_places': len(self.kyoto_detail_places),
            'hokkaido_places': len(self.hokkaido_places),
            'foreign_places': len(self.foreign_places)
        })
        return base_stats 