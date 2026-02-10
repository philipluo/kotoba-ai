from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class RawEntry:
    """原始录入数据模型"""
    id: Optional[int] = None
    content_type: str = 'sentence'  # sentence/word/phrase
    original_jp: str = ''
    hiragana: str = ''
    romaji: str = ''
    chinese_meaning: str = ''
    source: str = ''
    created_at: Optional[datetime] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    word_indices: List[int] = field(default_factory=list)
    review_count: int = 0
    last_reviewed: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'content_type': self.content_type,
            'original_jp': self.original_jp,
            'hiragana': self.hiragana,
            'romaji': self.romaji,
            'chinese_meaning': self.chinese_meaning,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'tags': self.tags,
            'processed': self.processed,
            'word_indices': self.word_indices,
            'review_count': self.review_count,
            'last_reviewed': self.last_reviewed.isoformat() if self.last_reviewed else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RawEntry':
        """从字典创建对象"""
        return cls(
            id=data.get('id'),
            content_type=data.get('content_type', 'sentence'),
            original_jp=data.get('original_jp', ''),
            hiragana=data.get('hiragana', ''),
            romaji=data.get('romaji', ''),
            chinese_meaning=data.get('chinese_meaning', ''),
            source=data.get('source', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            tags=data.get('tags', {}),
            processed=data.get('processed', False),
            word_indices=data.get('word_indices', []),
            review_count=data.get('review_count', 0),
            last_reviewed=datetime.fromisoformat(data['last_reviewed']) if data.get('last_reviewed') else None
        )

@dataclass
class SegmentedWord:
    """分词数据模型"""
    id: Optional[int] = None
    raw_entry_id: int = 0
    word_jp: str = ''
    hiragana: str = ''
    word_type: str = ''  # noun/verb/adjective/particle/...
    position: int = 0
    grammar_info: Dict[str, Any] = field(default_factory=dict)
    verb_id: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'raw_entry_id': self.raw_entry_id,
            'word_jp': self.word_jp,
            'hiragana': self.hiragana,
            'word_type': self.word_type,
            'position': self.position,
            'grammar_info': self.grammar_info,
            'verb_id': self.verb_id
        }

@dataclass
class VerbMaster:
    """动词原型数据模型"""
    id: Optional[int] = None
    prototype: str = ''
    reading: str = ''
    meaning: str = ''
    verb_class: str = ''  # 一类/二类/三类
    verb_group: str = ''  # godan/ichidan/kuru/suru
    stem: str = ''
    frequency: str = 'normal'
    first_seen: Optional[datetime] = None
    example_count: int = 0
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'prototype': self.prototype,
            'reading': self.reading,
            'meaning': self.meaning,
            'verb_class': self.verb_class,
            'verb_group': self.verb_group,
            'stem': self.stem,
            'frequency': self.frequency,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'example_count': self.example_count
        }

@dataclass
class VerbConjugation:
    """动词活用数据模型"""
    id: Optional[int] = None
    verb_id: int = 0
    form_type: str = ''  # dictionary/masu/te/ta/nai/...
    form_name: str = ''
    form_value: str = ''
    reading: str = ''
    example: str = ''
    politeness: str = 'plain'
    difficulty: int = 1
    meaning: str = ''
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'verb_id': self.verb_id,
            'form_type': self.form_type,
            'form_name': self.form_name,
            'form_value': self.form_value,
            'reading': self.reading,
            'example': self.example,
            'politeness': self.politeness,
            'difficulty': self.difficulty,
            'meaning': self.meaning
        }

@dataclass
class PhoneticIndex:
    """50音索引数据模型"""
    id: Optional[int] = None
    phonetic: str = ''
    entry_type: str = ''  # raw/segmented
    entry_table: str = ''
    entry_id: int = 0
    match_type: str = 'exact'  # exact/fuzzy
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'phonetic': self.phonetic,
            'entry_type': self.entry_type,
            'entry_table': self.entry_table,
            'entry_id': self.entry_id,
            'match_type': self.match_type
        }

@dataclass
class Question:
    """练习题目数据模型"""
    id: int = 0
    type: str = ''  # translation_jp_to_cn/translation_cn_to_jp/verb_conjugation
    question: str = ''
    options: List[str] = field(default_factory=list)
    correct_answer: str = ''
    hint: str = ''
    source_entry_id: Optional[int] = None
    is_new: bool = False
    days_since_created: int = 0
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type,
            'question': self.question,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'hint': self.hint,
            'source_entry_id': self.source_entry_id,
            'is_new': self.is_new,
            'days_since_created': self.days_since_created
        }

@dataclass
class DailyPractice:
    """每日练习记录数据模型"""
    id: Optional[int] = None
    practice_date: str = ''
    questions: List[Question] = field(default_factory=list)
    answers: List[Dict] = field(default_factory=list)
    completed: bool = False
    score: Optional[int] = None
    prompt_text: str = ''
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'practice_date': self.practice_date,
            'questions': [q.to_dict() for q in self.questions],
            'answers': self.answers,
            'completed': self.completed,
            'score': self.score,
            'prompt_text': self.prompt_text,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
