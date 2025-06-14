#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文書構造解析システム v4
文豪作品の複雑な構造（章・節・段落・詩歌形式）を自動認識・解析
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import unicodedata

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """文書タイプ"""
    NOVEL = "小説"
    SHORT_STORY = "短編"
    ESSAY = "随筆"
    POETRY = "詩歌"
    TANKA = "短歌"
    HAIKU = "俳句"
    DRAMA = "戯曲"
    LETTER = "書簡"
    DIARY = "日記"
    CRITICISM = "評論"
    UNKNOWN = "不明"

class StructureType(Enum):
    """構造タイプ"""
    CHAPTER = "章"
    SECTION = "節"
    PARAGRAPH = "段落"
    VERSE = "詩節"
    DIALOGUE = "対話"
    NARRATION = "地の文"
    DESCRIPTION = "描写"
    MONOLOGUE = "独白"

@dataclass
class StructureElement:
    """構造要素"""
    type: StructureType
    content: str
    level: int
    line_start: int
    line_end: int
    char_start: int
    char_end: int
    metadata: Dict[str, Any]

@dataclass
class DocumentAnalysis:
    """文書解析結果"""
    document_type: DocumentType
    title: str
    author: str
    structure_elements: List[StructureElement]
    metadata: Dict[str, Any]
    statistics: Dict[str, Any]
    confidence_score: float

class DocumentStructureAnalyzer:
    """文書構造解析システム v4"""
    
    def __init__(self):
        """初期化"""
        
        # 章・節パターン
        self.chapter_patterns = [
            # 数字による章立て
            r'^[　\s]*第[一二三四五六七八九十百千万壱弐参拾]*[章編部巻册][　\s]*(.*)$',
            r'^[　\s]*[一二三四五六七八九十百千万壱弐参拾]{1,4}[　\s]*(.*)$',
            r'^[　\s]*[１２３４５６７８９０]{1,3}[　\s]*(.*)$',
            r'^[　\s]*[0-9]{1,3}[\.、\s][　\s]*(.*)$',
            
            # 文字による章立て
            r'^[　\s]*[序破急上中下前後左右甲乙丙丁][編部巻册][　\s]*(.*)$',
            r'^[　\s]*[春夏秋冬][の章編][　\s]*(.*)$',
            r'^[　\s]*[朝昼夕夜][の章編][　\s]*(.*)$',
            
            # 小見出し形式
            r'^[　\s]*その[一二三四五六七八九十]{1,3}[　\s]*(.*)$',
            r'^[　\s]*[序章終章序文後書きはじめにおわりに][　\s]*(.*)$',
            
            # 特殊な章立て
            r'^[　\s]*[●○◆◇■□▲△▼▽][　\s]*(.*)$',
            r'^[　\s]*[＊＊＊＊＊][　\s]*(.*)$',
            r'^[　\s]*[-－=＝]{3,}[　\s]*(.*)$',
        ]
        
        # 詩歌パターン
        self.poetry_patterns = {
            'tanka': [
                r'^[　\s]*[五七五七七調]',  # 短歌の基本形
                r'[あ-ん]{5,7}[　\s]*[あ-ん]{5,7}[　\s]*[あ-ん]{5,7}',  # ひらがな短歌
            ],
            'haiku': [
                r'^[　\s]*[あ-ん]{5,7}[　\s]*[あ-ん]{5,7}[　\s]*[あ-ん]{5,7}[　\s]*$',  # 俳句
                r'[五七五調]',
            ],
            'free_verse': [
                r'^[　\s]*[^。、]*\n[　\s]*[^。、]*\n[　\s]*[^。、]*$',  # 自由詩
            ]
        }
        
        # 対話パターン
        self.dialogue_patterns = [
            r'^[　\s]*[「『]([^」』]+)[」』]',  # 基本的な対話
            r'^[　\s]*「([^」]+)」\s*と[^。]*[。]',  # 「〜」と言った形式
            r'^[　\s]*『([^』]+)』',  # 引用・思考
            r'^[　\s]*―([^―]+)―',  # ダッシュによる対話
        ]
        
        # 文体パターン
        self.style_patterns = {
            'descriptive': [
                r'[は].*[である]',  # である調
                r'[が][、。].*[だ]',  # だ調
                r'[美しい|美しき|麗しい|優雅な|静寂な]',  # 美的描写
            ],
            'narrative': [
                r'[私|僕|俺|わたし|わたくし][は|が]',  # 一人称
                r'[彼|彼女|その人][は|が]',  # 三人称
                r'[した|だった|であった][。]',  # 過去時制
            ],
            'classical': [
                r'[なり|けり|たり|ぬ|つ][。]',  # 古典語尾
                r'[候|そうろう|さぶらい]',  # 候文
                r'[かな|哉|哉][。]',  # 感嘆の古語
            ]
        }
        
        # 文書タイプ判定パターン
        self.document_type_patterns = {
            DocumentType.NOVEL: [
                r'第[一二三四五六七八九十]+章',
                r'[春夏秋冬]の[章編]',
                r'[上中下][巻編]',
                r'[序破急][編]',
            ],
            DocumentType.SHORT_STORY: [
                r'^[　\s]*[一二三四五六七八九十]$',
                r'その[一二三四五六七八九十]',
                r'[●○◆][　\s]*',
            ],
            DocumentType.POETRY: [
                r'^[あ-ん]{5,7}$',  # ひらがな行
                r'^[　\s]*[^。、]+[　\s]*$',  # 句点なし短行
                r'[五七五|七五調]',
            ],
            DocumentType.DRAMA: [
                r'^[　\s]*[A-Za-z][^：]*：',  # 登場人物名：
                r'^[　\s]*[一-龯]+[：]',  # 漢字名：
                r'[幕場]第[一二三四五六七八九十]+',
            ],
            DocumentType.ESSAY: [
                r'について',
                r'に関して',
                r'を論じる',
                r'考察',
            ]
        }
        
        logger.info("📖 文書構造解析システム v4 初期化完了")
    
    def analyze_document_structure(self, text: str, author_hint: str = "", title_hint: str = "") -> DocumentAnalysis:
        """文書構造の包括的解析"""
        
        if not text:
            return self._create_empty_analysis()
        
        lines = text.split('\n')
        
        # 基本情報抽出
        title = self._extract_title(text, title_hint)
        author = self._extract_author(text, author_hint)
        
        # 文書タイプ判定
        document_type = self._determine_document_type(text)
        
        # 構造要素抽出
        structure_elements = self._extract_structure_elements(lines, document_type)
        
        # メタデータ抽出
        metadata = self._extract_metadata(text, lines)
        
        # 統計計算
        statistics = self._calculate_statistics(text, structure_elements)
        
        # 信頼度計算
        confidence_score = self._calculate_confidence(text, structure_elements, document_type)
        
        analysis = DocumentAnalysis(
            document_type=document_type,
            title=title,
            author=author,
            structure_elements=structure_elements,
            metadata=metadata,
            statistics=statistics,
            confidence_score=confidence_score
        )
        
        logger.info(f"📖 文書解析完了: タイプ={document_type.value}, 構造要素={len(structure_elements)}個")
        
        return analysis
    
    def _extract_title(self, text: str, hint: str = "") -> str:
        """タイトル抽出"""
        
        if hint:
            return hint
        
        lines = text.split('\n')[:20]  # 最初の20行を確認
        
        for line in lines:
            line = line.strip()
            
            # 明示的なタイトル表記
            title_patterns = [
                r'^作品名[：:]\s*(.+)$',
                r'^題名[：:]\s*(.+)$',
                r'^タイトル[：:]\s*(.+)$',
                r'^Title[：:]\s*(.+)$',
            ]
            
            for pattern in title_patterns:
                match = re.match(pattern, line)
                if match:
                    return match.group(1).strip()
            
            # 推定タイトル（最初の非空行で短いもの）
            if line and len(line) <= 50 and not self._is_metadata_line(line):
                return line
        
        return "不明"
    
    def _extract_author(self, text: str, hint: str = "") -> str:
        """著者抽出"""
        
        if hint:
            return hint
        
        lines = text.split('\n')[:20]
        
        for line in lines:
            line = line.strip()
            
            # 明示的な著者表記
            author_patterns = [
                r'^著者名[：:]\s*(.+)$',
                r'^作者[：:]\s*(.+)$',
                r'^作家名[：:]\s*(.+)$',
                r'^Author[：:]\s*(.+)$',
                r'^by\s+(.+)$',
            ]
            
            for pattern in author_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        
        return "不明"
    
    def _determine_document_type(self, text: str) -> DocumentType:
        """文書タイプ判定"""
        
        scores = {doc_type: 0 for doc_type in DocumentType}
        
        # パターンマッチングによる判定
        for doc_type, patterns in self.document_type_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.MULTILINE))
                scores[doc_type] += matches
        
        # 追加的な判定基準
        lines = text.split('\n')
        
        # 詩歌の判定
        short_lines = sum(1 for line in lines if line.strip() and len(line.strip()) < 20)
        if short_lines > len(lines) * 0.6:
            scores[DocumentType.POETRY] += 10
        
        # 対話の多さで戯曲判定
        dialogue_lines = sum(1 for line in lines if any(re.match(p, line) for p in self.dialogue_patterns))
        if dialogue_lines > len(lines) * 0.3:
            scores[DocumentType.DRAMA] += 5
        
        # 長さで小説・短編判定
        if len(text) > 10000:
            scores[DocumentType.NOVEL] += 3
        elif len(text) > 3000:
            scores[DocumentType.SHORT_STORY] += 3
        
        # 最高スコアの文書タイプを返す
        best_type = max(scores, key=scores.get)
        
        if scores[best_type] == 0:
            return DocumentType.UNKNOWN
        
        return best_type
    
    def _extract_structure_elements(self, lines: List[str], doc_type: DocumentType) -> List[StructureElement]:
        """構造要素の抽出"""
        
        elements = []
        char_position = 0
        
        for line_num, line in enumerate(lines):
            original_line = line
            line = line.strip()
            
            if not line:
                char_position += len(original_line) + 1
                continue
            
            # 章・節の検出
            chapter_element = self._detect_chapter(line, line_num, char_position)
            if chapter_element:
                elements.append(chapter_element)
            
            # 段落の検出
            elif self._is_paragraph_start(line, doc_type):
                para_element = StructureElement(
                    type=StructureType.PARAGRAPH,
                    content=line,
                    level=0,
                    line_start=line_num,
                    line_end=line_num,
                    char_start=char_position,
                    char_end=char_position + len(line),
                    metadata={'paragraph_type': 'standard'}
                )
                elements.append(para_element)
            
            # 対話の検出
            dialogue_element = self._detect_dialogue(line, line_num, char_position)
            if dialogue_element:
                elements.append(dialogue_element)
            
            # 詩歌の検出
            if doc_type == DocumentType.POETRY:
                verse_element = self._detect_verse(line, line_num, char_position)
                if verse_element:
                    elements.append(verse_element)
            
            char_position += len(original_line) + 1
        
        # 階層構造の構築
        elements = self._build_hierarchy(elements)
        
        return elements
    
    def _detect_chapter(self, line: str, line_num: int, char_pos: int) -> Optional[StructureElement]:
        """章・節の検出"""
        
        for level, pattern in enumerate(self.chapter_patterns):
            match = re.match(pattern, line)
            if match:
                title = match.group(1).strip() if match.groups() else ""
                
                return StructureElement(
                    type=StructureType.CHAPTER if level < 4 else StructureType.SECTION,
                    content=line,
                    level=level,
                    line_start=line_num,
                    line_end=line_num,
                    char_start=char_pos,
                    char_end=char_pos + len(line),
                    metadata={
                        'title': title,
                        'pattern_level': level,
                        'structural_marker': True
                    }
                )
        
        return None
    
    def _detect_dialogue(self, line: str, line_num: int, char_pos: int) -> Optional[StructureElement]:
        """対話の検出"""
        
        for pattern in self.dialogue_patterns:
            match = re.match(pattern, line)
            if match:
                dialogue_text = match.group(1) if match.groups() else line
                
                return StructureElement(
                    type=StructureType.DIALOGUE,
                    content=line,
                    level=0,
                    line_start=line_num,
                    line_end=line_num,
                    char_start=char_pos,
                    char_end=char_pos + len(line),
                    metadata={
                        'dialogue_text': dialogue_text,
                        'speech_type': 'direct'
                    }
                )
        
        return None
    
    def _detect_verse(self, line: str, line_num: int, char_pos: int) -> Optional[StructureElement]:
        """詩歌の検出"""
        
        # 短歌・俳句の検出
        for verse_type, patterns in self.poetry_patterns.items():
            for pattern in patterns:
                if re.match(pattern, line):
                    return StructureElement(
                        type=StructureType.VERSE,
                        content=line,
                        level=0,
                        line_start=line_num,
                        line_end=line_num,
                        char_start=char_pos,
                        char_end=char_pos + len(line),
                        metadata={
                            'verse_type': verse_type,
                            'syllable_count': len(re.sub(r'[^あ-ん]', '', line))
                        }
                    )
        
        return None
    
    def _is_paragraph_start(self, line: str, doc_type: DocumentType) -> bool:
        """段落開始の判定"""
        
        # 詩歌の場合は段落概念が異なる
        if doc_type in [DocumentType.POETRY, DocumentType.TANKA, DocumentType.HAIKU]:
            return False
        
        # 標準的な段落開始
        paragraph_indicators = [
            r'^[　\s]+[^　\s]',  # インデントあり
            r'^[私僕俺彼彼女]',  # 主語から開始
            r'^[その時ある]',    # 時間表現
            r'^[しかしだがところが]',  # 接続詞
        ]
        
        for pattern in paragraph_indicators:
            if re.match(pattern, line):
                return True
        
        return False
    
    def _build_hierarchy(self, elements: List[StructureElement]) -> List[StructureElement]:
        """階層構造の構築"""
        
        if not elements:
            return elements
        
        # 章・節要素のレベルに基づいて親子関係を構築
        hierarchical_elements = []
        current_chapter = None
        current_section = None
        
        for element in elements:
            if element.type == StructureType.CHAPTER:
                current_chapter = element
                current_section = None
                element.metadata['children'] = []
                hierarchical_elements.append(element)
            
            elif element.type == StructureType.SECTION:
                if current_chapter:
                    current_chapter.metadata['children'].append(element)
                    element.metadata['parent'] = current_chapter
                current_section = element
                hierarchical_elements.append(element)
            
            else:
                # その他の要素は現在の節または章に属する
                if current_section:
                    current_section.metadata.setdefault('children', []).append(element)
                    element.metadata['parent'] = current_section
                elif current_chapter:
                    current_chapter.metadata.setdefault('children', []).append(element)
                    element.metadata['parent'] = current_chapter
                
                hierarchical_elements.append(element)
        
        return hierarchical_elements
    
    def _extract_metadata(self, text: str, lines: List[str]) -> Dict[str, Any]:
        """メタデータ抽出"""
        
        metadata = {}
        
        # 基本統計
        metadata['total_chars'] = len(text)
        metadata['total_lines'] = len(lines)
        metadata['non_empty_lines'] = len([line for line in lines if line.strip()])
        
        # 文体分析
        metadata['style_analysis'] = self._analyze_writing_style(text)
        
        # 時代性の分析
        metadata['period_analysis'] = self._analyze_historical_period(text)
        
        # 文字使用統計
        metadata['character_stats'] = self._analyze_character_usage(text)
        
        return metadata
    
    def _analyze_writing_style(self, text: str) -> Dict[str, Any]:
        """文体分析"""
        
        style_scores = {}
        
        for style_type, patterns in self.style_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text))
                score += matches
            style_scores[style_type] = score
        
        total_score = sum(style_scores.values())
        if total_score > 0:
            style_ratios = {k: v/total_score for k, v in style_scores.items()}
        else:
            style_ratios = style_scores
        
        return {
            'scores': style_scores,
            'ratios': style_ratios,
            'dominant_style': max(style_scores, key=style_scores.get) if style_scores else 'unknown'
        }
    
    def _analyze_historical_period(self, text: str) -> Dict[str, Any]:
        """時代性分析"""
        
        period_indicators = {
            'classical': [r'[なり|けり|たり|ぬ|つ]', r'[候|そうろう]', r'[かな|哉]'],
            'modern': [r'である', r'でした', r'します'],
            'contemporary': [r'だ[。]', r'である[。]', r'です[。]']
        }
        
        period_scores = {}
        for period, patterns in period_indicators.items():
            score = sum(len(re.findall(pattern, text)) for pattern in patterns)
            period_scores[period] = score
        
        return {
            'scores': period_scores,
            'estimated_period': max(period_scores, key=period_scores.get) if period_scores else 'unknown'
        }
    
    def _analyze_character_usage(self, text: str) -> Dict[str, Any]:
        """文字使用統計"""
        
        stats = {
            'hiragana': len(re.findall(r'[あ-ん]', text)),
            'katakana': len(re.findall(r'[ア-ン]', text)),
            'kanji': len(re.findall(r'[一-龯]', text)),
            'ascii': len(re.findall(r'[a-zA-Z0-9]', text)),
            'punctuation': len(re.findall(r'[。、！？]', text)),
        }
        
        total_chars = sum(stats.values())
        if total_chars > 0:
            ratios = {k: v/total_chars for k, v in stats.items()}
        else:
            ratios = {k: 0 for k in stats.keys()}
        
        return {
            'counts': stats,
            'ratios': ratios,
            'total_analyzed': total_chars
        }
    
    def _calculate_statistics(self, text: str, elements: List[StructureElement]) -> Dict[str, Any]:
        """統計計算"""
        
        element_counts = {}
        for element in elements:
            element_type = element.type.value
            element_counts[element_type] = element_counts.get(element_type, 0) + 1
        
        # 平均文長
        sentences = text.split('。')
        avg_sentence_length = sum(len(s.strip()) for s in sentences if s.strip()) / len(sentences) if sentences else 0
        
        # 段落統計
        paragraphs = text.split('\n\n')
        avg_paragraph_length = sum(len(p.strip()) for p in paragraphs if p.strip()) / len(paragraphs) if paragraphs else 0
        
        return {
            'element_counts': element_counts,
            'total_elements': len(elements),
            'avg_sentence_length': round(avg_sentence_length, 2),
            'avg_paragraph_length': round(avg_paragraph_length, 2),
            'structural_complexity': len(element_counts),
        }
    
    def _calculate_confidence(self, text: str, elements: List[StructureElement], doc_type: DocumentType) -> float:
        """信頼度計算"""
        
        confidence_factors = {
            'text_length': min(1.0, len(text) / 1000),  # 1000文字で満点
            'structure_detected': min(1.0, len(elements) / 10),  # 10要素で満点
            'type_confidence': 0.8 if doc_type != DocumentType.UNKNOWN else 0.2,
            'pattern_matches': 0.0,
        }
        
        # パターンマッチの信頼度
        if doc_type in self.document_type_patterns:
            pattern_matches = 0
            for pattern in self.document_type_patterns[doc_type]:
                pattern_matches += len(re.findall(pattern, text))
            confidence_factors['pattern_matches'] = min(1.0, pattern_matches / 5)
        
        # 重み付き信頼度
        weights = {
            'text_length': 0.2,
            'structure_detected': 0.3,
            'type_confidence': 0.3,
            'pattern_matches': 0.2,
        }
        
        confidence = sum(confidence_factors[key] * weights[key] for key in weights)
        
        return round(confidence, 3)
    
    def _is_metadata_line(self, line: str) -> bool:
        """メタデータ行の判定"""
        
        metadata_patterns = [
            r'^作品名[：:]',
            r'^著者名[：:]',
            r'^分類[：:]',
            r'^初出[：:]',
            r'^底本[：:]',
            r'青空文庫',
            r'^[-=]{3,}$',
            r'^※',
        ]
        
        for pattern in metadata_patterns:
            if re.match(pattern, line):
                return True
        
        return False
    
    def _create_empty_analysis(self) -> DocumentAnalysis:
        """空の解析結果作成"""
        return DocumentAnalysis(
            document_type=DocumentType.UNKNOWN,
            title="不明",
            author="不明",
            structure_elements=[],
            metadata={},
            statistics={},
            confidence_score=0.0
        )
    
    def export_structure_analysis(self, analysis: DocumentAnalysis, format: str = 'dict') -> Any:
        """構造解析結果のエクスポート"""
        
        if format == 'dict':
            return {
                'document_type': analysis.document_type.value,
                'title': analysis.title,
                'author': analysis.author,
                'structure_elements': [
                    {
                        'type': elem.type.value,
                        'content': elem.content[:100] + '...' if len(elem.content) > 100 else elem.content,
                        'level': elem.level,
                        'line_range': f"{elem.line_start}-{elem.line_end}",
                        'char_range': f"{elem.char_start}-{elem.char_end}",
                        'metadata': elem.metadata
                    }
                    for elem in analysis.structure_elements
                ],
                'metadata': analysis.metadata,
                'statistics': analysis.statistics,
                'confidence_score': analysis.confidence_score
            }
        
        elif format == 'summary':
            return {
                'title': analysis.title,
                'author': analysis.author,
                'type': analysis.document_type.value,
                'structure_summary': {
                    elem_type.value: len([e for e in analysis.structure_elements if e.type == elem_type])
                    for elem_type in set(elem.type for elem in analysis.structure_elements)
                },
                'confidence': analysis.confidence_score
            }
        
        else:
            return analysis

def main():
    """文書構造解析システムのテスト実行"""
    
    analyzer = DocumentStructureAnalyzer()
    
    # サンプルテキスト
    sample_text = """
作品名：羅生門
著者名：芥川龍之介

一

　ある日の暮方の事である。一人の下人が、羅生門の下で雨やみを待っていた。
　広い門の下には、この男のほかに誰もいない。

二

　下人は、雨をつくづくと見ていた。
「困ったことになった」と思った。
    """
    
    analysis = analyzer.analyze_document_structure(sample_text)
    
    print("📖 文書構造解析結果:")
    summary = analyzer.export_structure_analysis(analysis, 'summary')
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    return analysis

if __name__ == '__main__':
    main() 