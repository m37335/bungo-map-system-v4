#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正規表現を使用した地名抽出器
"""

import re
from typing import List, Dict, Any, Optional
from .base_extractor import BasePlaceExtractor, ExtractedPlace

class RegexPlaceExtractor(BasePlaceExtractor):
    """正規表現を使用した地名抽出器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.patterns = self._compile_patterns()
        self.min_confidence = self.config.get('min_confidence', 0.5)
    
    def _compile_patterns(self) -> List[Dict[str, Any]]:
        """正規表現パターンをコンパイル"""
        return [
            {
                'pattern': re.compile(r'([東西南北]京都|大阪府?|北海道|青森県?|岩手県?|宮城県?|秋田県?|山形県?|福島県?|茨城県?|栃木県?|群馬県?|埼玉県?|千葉県?|神奈川県?|新潟県?|富山県?|石川県?|福井県?|山梨県?|長野県?|岐阜県?|静岡県?|愛知県?|三重県?|滋賀県?|兵庫県?|奈良県?|和歌山県?|鳥取県?|島根県?|岡山県?|広島県?|山口県?|徳島県?|香川県?|愛媛県?|高知県?|福岡県?|佐賀県?|長崎県?|熊本県?|大分県?|宮崎県?|鹿児島県?|沖縄県?)'),
                'type': 'prefecture',
                'confidence': 0.9
            },
            {
                'pattern': re.compile(r'([東西南北]京(?:都|区)|大阪(?:市|区)|横浜市|名古屋市|札幌市|仙台市|福岡市|神戸市|川崎市|さいたま市|千葉市|堺市|新潟市|浜松市|熊本市|相模原市|岡山市|静岡市|船橋市|鹿児島市|八王子市|姫路市|宇都宮市|松山市|東大阪市|川口市|市川市|松本市|西宮市|大分市|倉敷市|金沢市|福山市|長崎市|豊田市|高知市|富山市|高松市|長野市|秋田市|和歌山市|大津市|北九州市|豊中市|枚方市|岐阜市|藤沢市|柏市|青森市|盛岡市|前橋市|高崎市|宇都宮市|水戸市|つくば市|土浦市|取手市|守谷市|龍ケ崎市|下妻市|常総市|古河市|石岡市|結城市|下館市|筑西市|坂東市|稲敷市|かすみがうら市|桜川市|神栖市|行方市|鉾田市|つくばみらい市|小美玉市)'),
                'type': 'city',
                'confidence': 0.8
            },
            {
                'pattern': re.compile(r'([東西南北]京(?:都|区)|大阪(?:市|区)|横浜(?:市|区)|名古屋(?:市|区)|札幌(?:市|区)|仙台(?:市|区)|福岡(?:市|区)|神戸(?:市|区)|川崎(?:市|区)|さいたま(?:市|区)|千葉(?:市|区)|堺(?:市|区)|新潟(?:市|区)|浜松(?:市|区)|熊本(?:市|区)|相模原(?:市|区)|岡山(?:市|区)|静岡(?:市|区)|船橋(?:市|区)|鹿児島(?:市|区)|八王子(?:市|区)|姫路(?:市|区)|宇都宮(?:市|区)|松山(?:市|区)|東大阪(?:市|区)|川口(?:市|区)|市川(?:市|区)|松本(?:市|区)|西宮(?:市|区)|大分(?:市|区)|倉敷(?:市|区)|金沢(?:市|区)|福山(?:市|区)|長崎(?:市|区)|豊田(?:市|区)|高知(?:市|区)|富山(?:市|区)|高松(?:市|区)|長野(?:市|区)|秋田(?:市|区)|和歌山(?:市|区)|大津(?:市|区)|北九州(?:市|区)|豊中(?:市|区)|枚方(?:市|区)|岐阜(?:市|区)|藤沢(?:市|区)|柏(?:市|区)|青森(?:市|区)|盛岡(?:市|区)|前橋(?:市|区)|高崎(?:市|区)|宇都宮(?:市|区)|水戸(?:市|区)|つくば(?:市|区)|土浦(?:市|区)|取手(?:市|区)|守谷(?:市|区)|龍ケ崎(?:市|区)|下妻(?:市|区)|常総(?:市|区)|古河(?:市|区)|石岡(?:市|区)|結城(?:市|区)|下館(?:市|区)|筑西(?:市|区)|坂東(?:市|区)|稲敷(?:市|区)|かすみがうら(?:市|区)|桜川(?:市|区)|神栖(?:市|区)|行方(?:市|区)|鉾田(?:市|区)|つくばみらい(?:市|区)|小美玉(?:市|区))'),
                'type': 'district',
                'confidence': 0.7
            }
        ]
    
    def extract(self, text: str, context_before: Optional[str] = None, 
                context_after: Optional[str] = None) -> List[ExtractedPlace]:
        """
        テキストから地名を抽出
        
        Args:
            text: 抽出対象のテキスト
            context_before: 前の文脈（オプション）
            context_after: 後の文脈（オプション）
            
        Returns:
            抽出された地名のリスト
        """
        places = []
        
        for pattern_info in self.patterns:
            for match in pattern_info['pattern'].finditer(text):
                place = ExtractedPlace(
                    place_name=match.group(1),
                    start_pos=match.start(1),
                    end_pos=match.end(1),
                    confidence=pattern_info['confidence'],
                    context_before=context_before,
                    context_after=context_after,
                    place_type=pattern_info['type']
                )
                
                if self.validate_place(place):
                    places.append(place)
        
        return places
    
    def get_description(self) -> str:
        """抽出器の説明を取得"""
        return "正規表現を使用した地名抽出器（都道府県、市区町村、地区）"
    
    def validate_place(self, place: ExtractedPlace) -> bool:
        """
        抽出された地名の妥当性を検証
        
        Args:
            place: 検証対象の地名情報
            
        Returns:
            妥当な場合はTrue
        """
        if not super().validate_place(place):
            return False
        
        # 正規表現固有の検証
        if place.place_type not in ['prefecture', 'city', 'district']:
            return False
        
        if place.confidence < self.min_confidence:
            return False
        
        return True 