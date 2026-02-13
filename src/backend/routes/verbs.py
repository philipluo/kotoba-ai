from flask import Blueprint, jsonify
from ..models.database import Database
import json

verbs_bp = Blueprint('verbs', __name__, url_prefix='/api/verbs')

@verbs_bp.route('', methods=['GET'])
def get_verbs():
    """获取所有动词列表"""
    try:
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取所有动词
            cursor.execute('''
                SELECT * FROM verb_master 
                ORDER BY first_seen DESC
            ''')
            verb_rows = cursor.fetchall()
            
            verbs = []
            for verb_row in verb_rows:
                verb = dict(verb_row)
                verb_id = verb['id']
                
                # 获取该动词的所有活用形式
                cursor.execute('''
                    SELECT * FROM verb_conjugations 
                    WHERE verb_id = ? 
                    ORDER BY id
                ''', (verb_id,))
                conj_rows = cursor.fetchall()
                
                conjugations = {}
                for conj_row in conj_rows:
                    conj = dict(conj_row)
                    conjugations[conj['form_type']] = {
                        'form_name': conj['form_name'],
                        'form_value': conj['form_value'],
                        'reading': conj['reading'],
                        'example': conj['example'],
                        'politeness': conj['politeness']
                    }
                
                verb['conjugations'] = conjugations
                verbs.append(verb)
            
            return jsonify({
                'success': True,
                'data': {
                    'total': len(verbs),
                    'verbs': verbs
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

@verbs_bp.route('/<int:verb_id>', methods=['GET'])
def get_verb_detail(verb_id):
    """获取单个动词详情"""
    try:
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取动词信息
            cursor.execute('SELECT * FROM verb_master WHERE id = ?', (verb_id,))
            verb_row = cursor.fetchone()
            
            if not verb_row:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': f'动词不存在: {verb_id}'
                    }
                }), 404
            
            verb = dict(verb_row)
            
            # 获取活用形式
            cursor.execute('''
                SELECT * FROM verb_conjugations 
                WHERE verb_id = ? 
                ORDER BY id
            ''', (verb_id,))
            conj_rows = cursor.fetchall()
            
            conjugations = []
            for conj_row in conj_rows:
                conj = dict(conj_row)
                conjugations.append({
                    'form_type': conj['form_type'],
                    'form_name': conj['form_name'],
                    'form_value': conj['form_value'],
                    'reading': conj['reading'],
                    'example': conj['example'],
                    'politeness': conj['politeness'],
                    'difficulty': conj['difficulty']
                })
            
            verb['conjugations'] = conjugations
            
            return jsonify({
                'success': True,
                'data': verb
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500
