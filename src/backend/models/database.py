import sqlite3
import json
import os
from datetime import datetime
from flask import current_app
from contextlib import contextmanager

class Database:
    """数据库连接管理"""
    
    # 默认数据库路径
    DEFAULT_DB_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        'data', 'japanese_learning.db'
    )
    
    @staticmethod
    @contextmanager
    def get_connection(db_path=None):
        """获取数据库连接（上下文管理器）"""
        # 优先使用传入的路径，其次是 Flask 配置，最后是默认路径
        if db_path:
            path = db_path
        else:
            try:
                path = current_app.config['DATABASE_PATH']
            except RuntimeError:
                # 不在 Flask 应用上下文中，使用默认路径
                path = Database.DEFAULT_DB_PATH
        
        # 确保目录存在
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def init_db(db_path=None):
        """初始化数据库表结构"""
        with Database.get_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # 1. 原始录入表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_type TEXT NOT NULL CHECK(content_type IN ('sentence', 'word', 'phrase')),
                    original_jp TEXT NOT NULL,
                    hiragana TEXT NOT NULL,
                    romaji TEXT,
                    chinese_meaning TEXT NOT NULL,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags JSON,
                    processed BOOLEAN DEFAULT 0,
                    word_indices JSON,
                    review_count INTEGER DEFAULT 0,
                    last_reviewed TIMESTAMP
                )
            ''')
            
            # 2. 自动分词表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS segmented_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_entry_id INTEGER NOT NULL,
                    word_jp TEXT NOT NULL,
                    hiragana TEXT NOT NULL,
                    word_type TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    grammar_info JSON,
                    verb_id INTEGER,
                    FOREIGN KEY (raw_entry_id) REFERENCES raw_entries(id) ON DELETE CASCADE,
                    FOREIGN KEY (verb_id) REFERENCES verb_master(id) ON DELETE SET NULL
                )
            ''')
            
            # 3. 动词原型表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verb_master (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prototype TEXT NOT NULL UNIQUE,
                    reading TEXT NOT NULL,
                    meaning TEXT NOT NULL,
                    verb_class TEXT,
                    verb_group TEXT,
                    stem TEXT,
                    frequency TEXT DEFAULT 'normal',
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    example_count INTEGER DEFAULT 0
                )
            ''')
            
            # 4. 动词活用表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verb_conjugations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    verb_id INTEGER NOT NULL,
                    form_type TEXT NOT NULL,
                    form_name TEXT,
                    form_value TEXT NOT NULL,
                    reading TEXT NOT NULL,
                    example TEXT,
                    politeness TEXT,
                    difficulty INTEGER DEFAULT 1,
                    meaning TEXT,
                    FOREIGN KEY (verb_id) REFERENCES verb_master(id) ON DELETE CASCADE,
                    UNIQUE(verb_id, form_type)
                )
            ''')
            
            # 5. 50音索引表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS phonetic_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phonetic TEXT NOT NULL,
                    entry_type TEXT NOT NULL,
                    entry_table TEXT NOT NULL,
                    entry_id INTEGER NOT NULL,
                    match_type TEXT DEFAULT 'exact',
                    UNIQUE(phonetic, entry_table, entry_id)
                )
            ''')
            
            # 6. 每日练习记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_practice (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    practice_date DATE NOT NULL UNIQUE,
                    questions JSON,
                    answers JSON,
                    completed BOOLEAN DEFAULT 0,
                    score INTEGER,
                    prompt_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_entries_created ON raw_entries(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_entries_type ON raw_entries(content_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_entries_processed ON raw_entries(processed)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_words_entry ON segmented_words(raw_entry_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_words_type ON segmented_words(word_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_words_verb ON segmented_words(verb_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_verb_prototype ON verb_master(prototype)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_verb_class ON verb_master(verb_class)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conj_verb ON verb_conjugations(verb_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conj_type ON verb_conjugations(form_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_phonetic_char ON phonetic_index(phonetic)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_phonetic_entry ON phonetic_index(entry_table, entry_id)')
    
    @staticmethod
    def init_phonetics(db_path=None):
        """初始化50音数据"""
        gojyuon_data = [
            # 清音
            ('あ', 'ア', 'a', 'gojyuon', 1), ('い', 'イ', 'i', 'gojyuon', 1),
            ('う', 'ウ', 'u', 'gojyuon', 1), ('え', 'エ', 'e', 'gojyuon', 1),
            ('お', 'オ', 'o', 'gojyuon', 1),
            ('か', 'カ', 'ka', 'gojyuon', 2), ('き', 'キ', 'ki', 'gojyuon', 2),
            ('く', 'ク', 'ku', 'gojyuon', 2), ('け', 'ケ', 'ke', 'gojyuon', 2),
            ('こ', 'コ', 'ko', 'gojyuon', 2),
            ('さ', 'サ', 'sa', 'gojyuon', 3), ('し', 'シ', 'shi', 'gojyuon', 3),
            ('す', 'ス', 'su', 'gojyuon', 3), ('せ', 'セ', 'se', 'gojyuon', 3),
            ('そ', 'ソ', 'so', 'gojyuon', 3),
            ('た', 'タ', 'ta', 'gojyuon', 4), ('ち', 'チ', 'chi', 'gojyuon', 4),
            ('つ', 'ツ', 'tsu', 'gojyuon', 4), ('て', 'テ', 'te', 'gojyuon', 4),
            ('と', 'ト', 'to', 'gojyuon', 4),
            ('な', 'ナ', 'na', 'gojyuon', 5), ('に', 'ニ', 'ni', 'gojyuon', 5),
            ('ぬ', 'ヌ', 'nu', 'gojyuon', 5), ('ね', 'ネ', 'ne', 'gojyuon', 5),
            ('の', 'ノ', 'no', 'gojyuon', 5),
            ('は', 'ハ', 'ha', 'gojyuon', 6), ('ひ', 'ヒ', 'hi', 'gojyuon', 6),
            ('ふ', 'フ', 'fu', 'gojyuon', 6), ('へ', 'ヘ', 'he', 'gojyuon', 6),
            ('ほ', 'ホ', 'ho', 'gojyuon', 6),
            ('ま', 'マ', 'ma', 'gojyuon', 7), ('み', 'ミ', 'mi', 'gojyuon', 7),
            ('む', 'ム', 'mu', 'gojyuon', 7), ('め', 'メ', 'me', 'gojyuon', 7),
            ('も', 'モ', 'mo', 'gojyuon', 7),
            ('や', 'ヤ', 'ya', 'gojyuon', 8), ('ゆ', 'ユ', 'yu', 'gojyuon', 8),
            ('よ', 'ヨ', 'yo', 'gojyuon', 8),
            ('ら', 'ラ', 'ra', 'gojyuon', 9), ('り', 'リ', 'ri', 'gojyuon', 9),
            ('る', 'ル', 'ru', 'gojyuon', 9), ('れ', 'レ', 're', 'gojyuon', 9),
            ('ろ', 'ロ', 'ro', 'gojyuon', 9),
            ('わ', 'ワ', 'wa', 'gojyuon', 10), ('を', 'ヲ', 'wo', 'gojyuon', 10),
            ('ん', 'ン', 'n', 'gojyuon', 10),
            # 浊音
            ('が', 'ガ', 'ga', 'dakuon', 2), ('ぎ', 'ギ', 'gi', 'dakuon', 2),
            ('ぐ', 'グ', 'gu', 'dakuon', 2), ('げ', 'ゲ', 'ge', 'dakuon', 2),
            ('ご', 'ゴ', 'go', 'dakuon', 2),
            ('ざ', 'ザ', 'za', 'dakuon', 3), ('じ', 'ジ', 'ji', 'dakuon', 3),
            ('ず', 'ズ', 'zu', 'dakuon', 3), ('ぜ', 'ゼ', 'ze', 'dakuon', 3),
            ('ぞ', 'ゾ', 'zo', 'dakuon', 3),
            ('だ', 'ダ', 'da', 'dakuon', 4), ('ぢ', 'ヂ', 'ji', 'dakuon', 4),
            ('づ', 'ヅ', 'zu', 'dakuon', 4), ('で', 'デ', 'de', 'dakuon', 4),
            ('ど', 'ド', 'do', 'dakuon', 4),
            ('ば', 'バ', 'ba', 'dakuon', 6), ('び', 'ビ', 'bi', 'dakuon', 6),
            ('ぶ', 'ブ', 'bu', 'dakuon', 6), ('べ', 'ベ', 'be', 'dakuon', 6),
            ('ぼ', 'ボ', 'bo', 'dakuon', 6),
            # 半浊音
            ('ぱ', 'パ', 'pa', 'handakuon', 6), ('ぴ', 'ピ', 'pi', 'handakuon', 6),
            ('ぷ', 'プ', 'pu', 'handakuon', 6), ('ぺ', 'ペ', 'pe', 'handakuon', 6),
            ('ぽ', 'ポ', 'po', 'handakuon', 6),
        ]
        
        with Database.get_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # 创建50音表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS phonetics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hiragana TEXT NOT NULL UNIQUE,
                    katakana TEXT NOT NULL,
                    romaji TEXT NOT NULL,
                    type TEXT NOT NULL,
                    row_num INTEGER NOT NULL
                )
            ''')
            
            # 插入数据
            for hira, kata, roma, typ, row in gojyuon_data:
                cursor.execute('''
                    INSERT OR IGNORE INTO phonetics (hiragana, katakana, romaji, type, row_num)
                    VALUES (?, ?, ?, ?, ?)
                ''', (hira, kata, roma, typ, row))
