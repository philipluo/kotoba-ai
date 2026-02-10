from flask import Blueprint, jsonify
from datetime import datetime, timedelta
from ..models.database import Database

stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')

@stats_bp.route('/overview', methods=['GET'])
def get_overview():
    """获取学习统计概览"""
    try:
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. 总录入数
            cursor.execute('SELECT COUNT(*) FROM raw_entries')
            total_entries = cursor.fetchone()[0]
            
            # 2. 总单词数（分词表）
            cursor.execute('SELECT COUNT(*) FROM segmented_words')
            total_words = cursor.fetchone()[0]
            
            # 3. 动词数量
            cursor.execute('SELECT COUNT(*) FROM verb_master')
            total_verbs = cursor.fetchone()[0]
            
            # 4. 今日新学
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) FROM raw_entries 
                WHERE date(created_at) = date('now')
            ''')
            today_new = cursor.fetchone()[0]
            
            # 5. 连续学习天数（简化计算：最近7天内有多少天有录入）
            cursor.execute('''
                SELECT COUNT(DISTINCT date(created_at)) 
                FROM raw_entries 
                WHERE created_at >= datetime('now', '-7 days')
            ''')
            streak_days = cursor.fetchone()[0]
            
            # 6. 分类统计
            cursor.execute('''
                SELECT word_type, COUNT(*) 
                FROM segmented_words 
                GROUP BY word_type
            ''')
            type_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            return jsonify({
                'success': True,
                'data': {
                    'total_entries': total_entries,
                    'total_words': total_words,
                    'total_verbs': total_verbs,
                    'today_new': today_new,
                    'streak_days': streak_days,
                    'type_stats': type_stats
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
