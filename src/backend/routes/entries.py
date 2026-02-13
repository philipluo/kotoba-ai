from flask import Blueprint, request, jsonify, current_app
import json
from datetime import datetime, timedelta
from ..models.database import Database
from ..services.segmenter import JapaneseSegmenter, VerbConjugator

entries_bp = Blueprint('entries', __name__, url_prefix='/api/entries')

# 辅助函数
def extract_phonetics(hiragana: str) -> list:
    """提取50音"""
    gojyuon = set('あいうえおかきくけこさしすせそたちつてとなにぬねの'
                  'はひふへほまみむめもやゆよらりるれろわをん'
                  'がぎぐげござじずぜぞだぢづでどばびぶべぼ'
                  'ぱぴぷぺぽ')
    
    phonetics = []
    seen = set()
    
    for char in hiragana:
        if char in gojyuon and char not in seen:
            phonetics.append(char)
            seen.add(char)
    
    return phonetics

def extract_verbs(segmented_words: list) -> list:
    """提取动词"""
    verbs = []
    for word in segmented_words:
        if word.word_type == 'verb':
            verbs.append({
                'word': word.word_jp,
                'prototype': word.grammar_info.get('prototype'),
                'form': word.grammar_info.get('form')
            })
    return verbs

def get_or_create_verb(cursor, prototype: str, word_data: dict) -> int:
    """获取或创建动词"""
    # 检查是否已存在
    cursor.execute('SELECT id FROM verb_master WHERE prototype = ?', (prototype,))
    row = cursor.fetchone()
    
    if row:
        return row[0]
    
    # 创建新动词
    hiragana = word_data.get('hiragana', '')
    verb_class = word_data.get('grammar_info', {}).get('verb_class', '一类动词')
    
    cursor.execute('''
        INSERT INTO verb_master (prototype, reading, meaning, verb_class, example_count)
        VALUES (?, ?, ?, ?, 1)
    ''', (
        prototype,
        hiragana,
        word_data.get('grammar_info', {}).get('meaning', ''),
        verb_class
    ))
    
    verb_id = cursor.lastrowid
    
    # 生成动词活用
    conjugator = VerbConjugator()
    conjugations = conjugator.conjugate(prototype, hiragana, verb_class)
    
    for conj in conjugations:
        cursor.execute('''
            INSERT INTO verb_conjugations
            (verb_id, form_type, form_name, form_value, reading, example, politeness, difficulty, meaning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            verb_id, conj.form_type, conj.form_name, conj.form_value,
            conj.reading, conj.example, conj.politeness, conj.difficulty, conj.meaning
        ))
    
    return verb_id

def create_phonetic_index(cursor, entry_id: int, hiragana: str, word_indices: list):
    """创建50音索引"""
    phonetics = extract_phonetics(hiragana)
    
    for phonetic in phonetics:
        cursor.execute('''
            INSERT OR IGNORE INTO phonetic_index
            (phonetic, entry_type, entry_table, entry_id, match_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (phonetic, 'raw', 'raw_entries', entry_id, 'exact'))

def validate_entry(data, index=None):
    """验证单条数据"""
    prefix = f"第{index + 1}条数据" if index is not None else "数据"
    required_fields = ['original_jp', 'hiragana', 'chinese_meaning']
    
    for field in required_fields:
        if not data.get(field):
            return False, f'{prefix}缺少必填字段: {field}'
    
    return True, None

def process_single_entry(data):
    """处理单条数据，返回预览结果"""
    # 优先使用AI预分词的数据
    pre_segmented = data.get('segmented_words')
    
    if pre_segmented and len(pre_segmented) > 0:
        # 使用AI预分词结果
        segmented_words_data = pre_segmented
        print(f"✅ 使用AI预分词结果: {len(pre_segmented)} 个单词")
    else:
        # 降级使用自动分词（不推荐）
        segmenter = JapaneseSegmenter()
        segmented_words = segmenter.segment(
            data['original_jp'],
            data['hiragana']
        )
        segmented_words_data = [word.to_dict() for word in segmented_words]
        print(f"⚠️  使用自动分词结果（可能不准确）: {len(segmented_words_data)} 个单词")
    
    phonetics = extract_phonetics(data['hiragana'])
    
    return {
        'original_data': data,
        'segmented_words': segmented_words_data,
        'verbs_detected': [w for w in segmented_words_data if w.get('word_type') == 'verb'],
        'phonetic_index': phonetics,
        'total_words': len(segmented_words_data),
        'segmentation_source': 'ai' if pre_segmented else 'auto'
    }

@entries_bp.route('/preview', methods=['POST'])
def create_preview():
    """创建预览（支持批量，不入库）"""
    try:
        input_data = request.get_json()
        
        # 判断是单条还是批量（数组）
        if isinstance(input_data, list):
            entries = input_data
            is_batch = True
        else:
            entries = [input_data]
            is_batch = False
        
        # 验证所有数据
        for i, entry in enumerate(entries):
            is_valid, error_msg = validate_entry(entry, i if len(entries) > 1 else None)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': error_msg
                    }
                }), 400
        
        # 生成预览ID
        preview_id = f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 处理所有条目
        preview_results = []
        for entry in entries:
            result = process_single_entry(entry)
            preview_results.append(result)
        
        return jsonify({
            'success': True,
            'data': {
                'preview_id': preview_id,
                'is_batch': is_batch,
                'total_count': len(entries),
                'entries': preview_results
            },
            'message': f'预览生成成功，共{len(entries)}条数据，请确认后提交'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500

@entries_bp.route('/<preview_id>/confirm', methods=['POST'])
def confirm_entry(preview_id):
    """确认并入库（支持批量）"""
    try:
        data = request.get_json()
        preview_entries = data.get('entries', [])
        
        if not preview_entries:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': '没有要入库的数据'
                }
            }), 400
        
        results = []
        
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            for entry_data in preview_entries:
                original_data = entry_data.get('original_data', {})
                segmented_words_data = entry_data.get('segmented_words', [])
                
                # 1. 插入原始数据
                cursor.execute('''
                    INSERT INTO raw_entries 
                    (content_type, original_jp, hiragana, romaji, chinese_meaning, source, tags, processed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    original_data.get('content_type', 'sentence'),
                    original_data['original_jp'],
                    original_data['hiragana'],
                    original_data.get('romaji', ''),
                    original_data['chinese_meaning'],
                    original_data.get('source', ''),
                    json.dumps(original_data.get('tags', {})),
                    True
                ))
                
                entry_id = cursor.lastrowid
                word_indices = []
                
                # 2. 插入分词数据
                for word_data in segmented_words_data:
                    verb_id = None
                    
                    # 如果是动词，处理动词原型
                    if word_data.get('word_type') == 'verb' and word_data.get('grammar_info', {}).get('prototype'):
                        prototype = word_data['grammar_info']['prototype']
                        verb_id = get_or_create_verb(cursor, prototype, word_data)
                    
                    cursor.execute('''
                        INSERT INTO segmented_words
                        (raw_entry_id, word_jp, hiragana, word_type, position, grammar_info, verb_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        entry_id,
                        word_data['word_jp'],
                        word_data['hiragana'],
                        word_data['word_type'],
                        word_data['position'],
                        json.dumps(word_data.get('grammar_info', {})),
                        verb_id
                    ))
                    
                    word_indices.append(cursor.lastrowid)
                
                # 3. 更新raw_entries的word_indices
                cursor.execute('''
                    UPDATE raw_entries SET word_indices = ? WHERE id = ?
                ''', (json.dumps(word_indices), entry_id))
                
                # 4. 生成50音索引
                if entry_id:
                    create_phonetic_index(cursor, entry_id, original_data['hiragana'], word_indices)
                
                results.append({
                    'entry_id': entry_id,
                    'original_jp': original_data['original_jp'],
                    'segmented_count': len(segmented_words_data)
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'total_entries': len(results),
                    'entries': results,
                    'verbs_added': sum(1 for e in preview_entries 
                                     for w in e.get('segmented_words', []) 
                                     if w.get('word_type') == 'verb')
                },
                'message': f'成功入库{len(results)}条数据'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500

@entries_bp.route('', methods=['GET'])
def get_entries():
    """获取录入列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        content_type = request.args.get('content_type')
        search = request.args.get('search', '')
        order_by = request.args.get('order_by', 'created_at')
        order = request.args.get('order', 'desc')
        
        # 限制每页数量
        limit = min(limit, current_app.config.get('MAX_PAGE_SIZE', 100))
        offset = (page - 1) * limit
        
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            # 构建查询
            query = 'SELECT * FROM raw_entries WHERE 1=1'
            count_query = 'SELECT COUNT(*) FROM raw_entries WHERE 1=1'
            params = []
            
            if content_type:
                query += ' AND content_type = ?'
                count_query += ' AND content_type = ?'
                params.append(content_type)
            
            # 添加搜索功能
            if search:
                search_pattern = f'%{search}%'
                query += ' AND (original_jp LIKE ? OR hiragana LIKE ? OR chinese_meaning LIKE ? OR romaji LIKE ?)'
                count_query += ' AND (original_jp LIKE ? OR hiragana LIKE ? OR chinese_meaning LIKE ? OR romaji LIKE ?)'
                params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
            
            # 获取总数
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # 排序和分页
            query += f' ORDER BY {order_by} {order}'
            query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            entries = []
            for row in rows:
                entry = dict(row)
                entry['tags'] = json.loads(entry.get('tags', '{}'))
                entry['word_indices'] = json.loads(entry.get('word_indices', '[]'))
                entries.append(entry)
            
            return jsonify({
                'success': True,
                'data': {
                    'items': entries,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total,
                        'total_pages': (total + limit - 1) // limit
                    }
                }
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500

@entries_bp.route('/<int:entry_id>', methods=['GET'])
def get_entry(entry_id):
    """获取录入详情"""
    try:
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            # 查询原始数据
            cursor.execute('SELECT * FROM raw_entries WHERE id = ?', (entry_id,))
            row = cursor.fetchone()
            
            if not row:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': f'录入不存在: {entry_id}'
                    }
                }), 404
            
            entry = dict(row)
            entry['tags'] = json.loads(entry.get('tags', '{}'))
            entry['word_indices'] = json.loads(entry.get('word_indices', '[]'))
            
            # 查询分词数据
            cursor.execute('''
                SELECT * FROM segmented_words WHERE raw_entry_id = ? ORDER BY position
            ''', (entry_id,))
            word_rows = cursor.fetchall()
            
            segmented_words = []
            for word_row in word_rows:
                word = dict(word_row)
                word['grammar_info'] = json.loads(word.get('grammar_info', '{}'))
                segmented_words.append(word)
            
            entry['segmented_words'] = segmented_words
            
            return jsonify({
                'success': True,
                'data': entry
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500

@entries_bp.route('/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    """删除录入"""
    try:
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM raw_entries WHERE id = ?', (entry_id,))
            
            if cursor.rowcount == 0:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': f'录入不存在: {entry_id}'
                    }
                }), 404
            
            return jsonify({
                'success': True,
                'message': '删除成功'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500

@entries_bp.route('/categories/<word_type>', methods=['GET'])
def get_categories(word_type):
    """获取分类数据（名词/动词/形容词/助词）"""
    try:
        # 词性映射
        type_map = {
            'nouns': 'noun',
            'verbs': 'verb',
            'adjectives': ['adjective_i', 'adjective_na'],
            'particles': 'particle'
        }
        
        target_types = type_map.get(word_type, [word_type])
        if not isinstance(target_types, list):
            target_types = [target_types]
        
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            # 查询所有分词及其对应的原始句子
            placeholders = ','.join(['?' for _ in target_types])
            cursor.execute(f'''
                SELECT s.*, r.original_jp as from_sentence, r.romaji, r.created_at
                FROM segmented_words s
                JOIN raw_entries r ON s.raw_entry_id = r.id
                WHERE s.word_type IN ({placeholders})
                ORDER BY r.created_at DESC
                LIMIT 100
            ''', target_types)
            
            rows = cursor.fetchall()
            
            words = []
            for row in rows:
                word = dict(row)
                word['grammar_info'] = json.loads(word.get('grammar_info', '{}'))
                words.append(word)
            
            return jsonify({
                'success': True,
                'data': {
                    'type': word_type,
                    'count': len(words),
                    'words': words
                }
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500
