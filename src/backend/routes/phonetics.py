from flask import Blueprint, jsonify, request
import json
from ..models.database import Database

phonetics_bp = Blueprint('phonetics', __name__, url_prefix='/api/phonetics')

@phonetics_bp.route('', methods=['GET'])
def get_phonetics():
    """获取50音图表"""
    try:
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            # 查询所有50音
            cursor.execute('SELECT * FROM phonetics ORDER BY row_num, id')
            rows = cursor.fetchall()
            
            # 按类型分组
            gojyuon = {}
            dakuon = {}
            handakuon = {}
            
            for row in rows:
                row_num = row['row_num']
                if row['type'] == 'gojyuon':
                    if row_num not in gojyuon:
                        gojyuon[row_num] = []
                    gojyuon[row_num].append({
                        'hiragana': row['hiragana'],
                        'katakana': row['katakana'],
                        'romaji': row['romaji']
                    })
                elif row['type'] == 'dakuon':
                    if row_num not in dakuon:
                        dakuon[row_num] = []
                    dakuon[row_num].append({
                        'hiragana': row['hiragana'],
                        'katakana': row['katakana'],
                        'romaji': row['romaji']
                    })
                elif row['type'] == 'handakuon':
                    if row_num not in handakuon:
                        handakuon[row_num] = []
                    handakuon[row_num].append({
                        'hiragana': row['hiragana'],
                        'katakana': row['katakana'],
                        'romaji': row['romaji']
                    })
            
            return jsonify({
                'success': True,
                'data': {
                    'gojyuon': gojyuon,
                    'dakuon': dakuon,
                    'handakuon': handakuon
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

@phonetics_bp.route('/<character>/entries', methods=['GET'])
def search_by_phonetic(character):
    """按50音检索"""
    try:
        entry_type = request.args.get('type', 'all')
        match_type = request.args.get('match_type', 'exact')
        
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            results = {
                'phonetic': character,
                'total_count': 0,
                'raw_entries': [],
                'segmented_words': []
            }
            
            # 查询原始数据
            if entry_type in ['all', 'raw']:
                cursor.execute('''
                    SELECT e.* FROM raw_entries e
                    JOIN phonetic_index p ON e.id = p.entry_id
                    WHERE p.phonetic = ? AND p.entry_table = 'raw_entries'
                    ORDER BY e.created_at DESC
                ''', (character,))
                
                for row in cursor.fetchall():
                    entry = dict(row)
                    entry['tags'] = json.loads(entry.get('tags', '{}'))
                    results['raw_entries'].append(entry)
                    results['total_count'] += 1
            
            # 查询分词数据
            if entry_type in ['all', 'segmented']:
                cursor.execute('''
                    SELECT s.*, e.original_jp as from_sentence, e.created_at
                    FROM segmented_words s
                    JOIN raw_entries e ON s.raw_entry_id = e.id
                    WHERE s.hiragana LIKE ?
                    ORDER BY e.created_at DESC
                ''', (f'%{character}%',))
                
                for row in cursor.fetchall():
                    word = dict(row)
                    word['grammar_info'] = json.loads(word.get('grammar_info', '{}'))
                    results['segmented_words'].append(word)
                    results['total_count'] += 1
            
            return jsonify({
                'success': True,
                'data': results
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500
