    def _extract_places_with_regex(self, text: str, work_info: Dict) -> List[Dict]:
        """
        正規表現ベースの地名抽出（大幅強化版）
        """
        places = []
        
        try:
            # 🗾 日本の地名パターン（拡張版）
            # 都道府県（漢字1-2文字 + 都道府県）
            prefecture_patterns = [
                r'[北海青森岩手宮城秋田山形福島茨城栃木群馬埼玉千葉東京神奈川新潟富山石川福井山梨長野岐阜静岡愛知三重滋賀京都大阪兵庫奈良和歌山鳥取島根岡山広島山口徳島香川愛媛高知福岡佐賀長崎熊本大分宮崎鹿児島沖縄][都道府県]',
                r'北海道'
            ]
            
            # 市区町村（漢字2-4文字 + 市区町村）
            city_patterns = [
                r'[一-龯]{2,4}[市区町村]',
                r'[一-龯]{2,}[郡]'
            ]
            
            # 🌟 有名な地名・駅名・観光地（大幅拡張）
            famous_places = [
                # 東京エリア
                r'銀座', r'新宿', r'渋谷', r'上野', r'浅草', r'品川', r'池袋', r'新橋', r'有楽町', r'丸の内',
                r'表参道', r'原宿', r'恵比寿', r'六本木', r'赤坂', r'青山', r'麻布', r'目黒', r'世田谷',
                r'江戸', r'本郷', r'神田', r'日本橋', r'築地', r'月島', r'両国', r'浅草橋', r'秋葉原',
                
                # 関東エリア
                r'横浜', r'川崎', r'千葉', r'埼玉', r'大宮', r'浦和', r'船橋', r'柏', r'所沢', r'川越',
                r'鎌倉', r'湘南', r'箱根', r'熱海', r'軽井沢', r'日光', r'那須', r'草津', r'伊香保',
                
                # 関西エリア
                r'京都', r'大阪', r'神戸', r'奈良', r'和歌山', r'滋賀', r'比叡山', r'嵐山', r'祇園',
                r'清水', r'金閣寺', r'銀閣寺', r'伏見', r'宇治', r'平安京', r'難波', r'梅田', r'心斎橋',
                
                # 中部エリア
                r'名古屋', r'金沢', r'富山', r'新潟', r'長野', r'松本', r'諏訪', r'上高地', r'立山',
                
                # 東北エリア
                r'仙台', r'青森', r'盛岡', r'秋田', r'山形', r'福島', r'会津', r'松島',
                
                # 北海道
                r'札幌', r'函館', r'小樽', r'旭川', r'釧路', r'帯広', r'北見',
                
                # 中国・四国
                r'広島', r'岡山', r'山口', r'鳥取', r'島根', r'高松', r'松山', r'高知', r'徳島',
                
                # 九州・沖縄
                r'福岡', r'博多', r'北九州', r'佐賀', r'長崎', r'熊本', r'大分', r'宮崎', r'鹿児島', r'沖縄', r'那覇',
                
                # 🌏 古典的・文学的地名
                r'平安京', r'江戸', r'武蔵', r'相模', r'甲斐', r'信濃', r'越後', r'下野', r'上野',
                r'羅生門', r'桂川', r'鴨川', r'隅田川', r'多摩川', r'富士山', r'筑波山', r'比叡山',
                
                # 🏛️ 仏教・神道関連地名（「蜀川」「阿修羅」「帝釈天」タイプ）
                r'蜀川', r'阿修羅', r'帝釈天', r'須弥山', r'兜率天', r'忉利天', r'極楽', r'浄土',
                r'龍宮', r'蓬莱', r'桃源郷', r'天竺', r'震旦', r'朝鮮', r'高麗', r'百済', r'新羅',
                
                # 🌊 川・山・湖の自然地名
                r'[一-龯]{1,3}川', r'[一-龯]{1,3}山', r'[一-龯]{1,3}湖', r'[一-龯]{1,3}海',
                r'[一-龯]{1,3}峠', r'[一-龯]{1,3}谷', r'[一-龯]{1,3}野', r'[一-龯]{1,3}原',
                
                # 🏯 城・宿場・古い地名
                r'[一-龯]{1,3}城', r'[一-龯]{1,3}宿', r'[一-龯]{1,3}駅', r'[一-龯]{1,3}港',
                
                # 🌸 寺院・神社関連
                r'[一-龯]{1,4}寺', r'[一-龯]{1,4}神社', r'[一-龯]{1,3}院', r'[一-龯]{1,3}宮',
                
                # 🌍 外国地名（文学作品によく登場）
                r'ロンドン', r'パリ', r'ベルリン', r'ニューヨーク', r'シカゴ', r'ボストン',
                r'中国', r'朝鮮', r'満州', r'台湾', r'樺太', r'シベリア', r'ヨーロッパ', r'アメリカ',
                
                # 🗾 地方名
                r'関東', r'関西', r'東北', r'九州', r'四国', r'中国地方', r'中部', r'北陸', r'山陰', r'山陽'
            ]
            
            # ✨ 全パターンを統合
            all_patterns = prefecture_patterns + city_patterns + famous_places
            
            # 地名抽出実行
            for pattern in all_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    place_name = match.group()
                    if self._is_valid_place_name_enhanced(place_name):
                        place_info = {
                            'place_name': place_name,
                            'author_name': work_info.get('author_name', ''),
                            'work_title': work_info.get('title', ''),
                            'extraction_method': 'regex_enhanced',
                            'confidence': self._calculate_confidence_enhanced(place_name, text),
                            'context': self._get_context(text, match.start(), match.end()),
                            'sentence': self._get_sentence_context(text, match.start(), match.end()),
                            'before_text': self._get_context(text, match.start(), match.end(), context_len=30),
                            'after_text': self._get_context(text, match.start(), match.end(), context_len=30)
                        }
                        places.append(place_info)
        
        except Exception as e:
            self.logger.error(f"❌ 強化正規表現地名抽出エラー: {e}")
        
        # 重複除去
        unique_places = self._remove_duplicates_enhanced(places)
        return unique_places

    def _is_valid_place_name_enhanced(self, place_name: str) -> bool:
        """
        地名の妥当性をチェック（強化版）
        """
        if not place_name or len(place_name) < 1:
            return False
        
        # 一文字地名も許可（「京」「江戸」の「江」等）
        if len(place_name) == 1:
            # 明らかに地名でない単語は除外
            single_char_exclusions = {'日', '月', '年', '時', '分', '秒', '春', '夏', '秋', '冬'}
            if place_name in single_char_exclusions:
                return False
        
        # 無効な地名をフィルタ（緩和版）
        if place_name in {'上', '下', '左', '右', '前', '後', '中', '内', '外', '大', '小', '高', '低'}:
            return False
        
        # 数字のみは除外
        if place_name.isdigit():
            return False
        
        return True

    def _calculate_confidence_enhanced(self, place_name: str, text: str) -> float:
        """
        地名の信頼度を計算（強化版）
        """
        confidence = 0.6  # ベース信頼度（正規表現）
        
        # 地名の種類による重み付け
        if any(suffix in place_name for suffix in ['都', '道', '府', '県']):
            confidence += 0.2  # 都道府県
        elif any(suffix in place_name for suffix in ['市', '区', '町', '村']):
            confidence += 0.15  # 市区町村
        elif any(suffix in place_name for suffix in ['川', '山', '海', '湖']):
            confidence += 0.1   # 自然地名
        elif place_name in ['蜀川', '阿修羅', '帝釈天', '平安京', '江戸']:
            confidence += 0.15  # 古典・文学的地名
        
        # 地名の長さによる重み付け
        if len(place_name) >= 3:
            confidence += 0.1
        elif len(place_name) >= 2:
            confidence += 0.05
        
        # 文脈による重み付け
        context_keywords = ['行く', '住む', '生まれる', '来る', '帰る', 'へ', 'から', 'で', 'に', 'の']
        for keyword in context_keywords:
            if keyword in text:
                confidence += 0.05
                break
        
        return min(confidence, 1.0)  # 最大値は1.0

    def _get_sentence_context(self, text: str, start: int, end: int) -> str:
        """
        地名を含む文を抽出
        """
        # 前後の句読点を探して文を抽出
        sentence_start = start
        sentence_end = end
        
        # 前方検索
        for i in range(start - 1, max(0, start - 200), -1):
            if text[i] in '。！？\n':
                sentence_start = i + 1
                break
        
        # 後方検索
        for i in range(end, min(len(text), end + 200)):
            if text[i] in '。！？\n':
                sentence_end = i
                break
        
        return text[sentence_start:sentence_end].strip()

    def _remove_duplicates_enhanced(self, places: List[Dict]) -> List[Dict]:
        """
        重複地名を除去（強化版）
        """
        seen = set()
        unique_places = []
        
        for place in places:
            # 地名+作品の組み合わせで重複チェック
            key = (place['place_name'], place['work_title'])
            if key not in seen:
                seen.add(key)
                unique_places.append(place)
        
        return unique_places 