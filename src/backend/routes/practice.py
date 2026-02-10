from flask import Blueprint, jsonify, request
import json
from datetime import datetime, timedelta
import random
from ..models.database import Database

practice_bp = Blueprint('practice', __name__, url_prefix='/api/practice')

@practice_bp.route('/daily', methods=['GET'])
def generate_daily_practice():
    """生成每日一练"""
    try:
        count = request.args.get('count', 20, type=int)
        count = min(count, 50)  # 最多50题
        
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.now()
            questions = []
            
            # 1. 获取最近7天的内容（新知识，40%）
            cursor.execute('''
                SELECT * FROM raw_entries
                WHERE created_at >= datetime('now', '-7 days')
                AND processed = 1
                ORDER BY created_at DESC
            ''')
            recent_entries = [dict(row) for row in cursor.fetchall()]
            
            # 2. 获取7-30天的内容（30%）
            cursor.execute('''
                SELECT * FROM raw_entries
                WHERE created_at BETWEEN datetime('now', '-30 days') AND datetime('now', '-7 days')
                AND processed = 1
                ORDER BY created_at DESC
            ''')
            medium_entries = [dict(row) for row in cursor.fetchall()]
            
            # 3. 获取30天以上的内容（20%）
            cursor.execute('''
                SELECT * FROM raw_entries
                WHERE created_at < datetime('now', '-30 days')
                AND processed = 1
                ORDER BY RANDOM()
            ''')
            old_entries = [dict(row) for row in cursor.fetchall()]
            
            # 4. 计算各区间选题数量
            new_count = int(count * 0.4)
            medium_count = int(count * 0.3)
            old_count = int(count * 0.2)
            random_count = count - new_count - medium_count - old_count
            
            selected = []
            
            # 选择新学内容
            if len(recent_entries) >= new_count:
                selected.extend(random.sample(recent_entries, new_count))
            else:
                selected.extend(recent_entries)
                medium_count += new_count - len(recent_entries)
            
            # 选择近期内容
            if len(medium_entries) >= medium_count:
                selected.extend(random.sample(medium_entries, medium_count))
            else:
                selected.extend(medium_entries)
                old_count += medium_count - len(medium_entries)
            
            # 选择旧知识
            if len(old_entries) >= old_count:
                selected.extend(random.sample(old_entries, old_count))
            else:
                selected.extend(old_entries)
                random_count += old_count - len(old_entries)
            
            # 5. 生成题目
            for i, entry in enumerate(selected[:count], 1):
                question = _create_question(entry, i, now)
                questions.append(question)
            
            # 打乱顺序
            random.shuffle(questions)
            
            # 6. 保存到数据库
            today = now.strftime('%Y-%m-%d')
            questions_json = json.dumps([q for q in questions])
            
            cursor.execute('''
                INSERT OR REPLACE INTO daily_practice
                (practice_date, questions, completed, created_at)
                VALUES (?, ?, 0, ?)
            ''', (today, questions_json, now))
            
            return jsonify({
                'success': True,
                'data': {
                    'date': today,
                    'total_questions': len(questions),
                    'questions': questions,
                    'stats': {
                        'new_content': len([q for q in questions if q.get('is_new')]),
                        'recent_review': len([q for q in questions if 0 < q.get('days_since_created', 0) <= 30]),
                        'old_review': len([q for q in questions if q.get('days_since_created', 0) > 30])
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

@practice_bp.route('/prompt', methods=['POST'])
def generate_prompt():
    """生成豆包Prompt"""
    try:
        data = request.get_json()
        questions = data.get('questions', [])
        style = data.get('style', 'gentle')
        include_hints = data.get('include_hints', True)
        
        style_instructions = {
            'gentle': '温柔地纠正我的发音和语法错误，给予鼓励',
            'strict': '严格纠正我的错误，指出具体问题'
        }
        
        prompt = f"""【日语每日一练 - {datetime.now().strftime('%Y年%m月%d日')}】

我是你的日语学生，请按以下顺序考我{len(questions)}道题。

每道题：
1. 用中文或日语说出题目
2. 等我回答（语音）
3. {style_instructions.get(style, style_instructions['gentle'])}
4. 给出正确答案
5. 简单讲解相关语法点

题目列表：

"""
        
        for i, q in enumerate(questions, 1):
            q_type = q.get('type', '')
            q_text = q.get('question', '')
            hint = q.get('hint', '')
            
            if q_type == 'translation_jp_to_cn':
                prompt += f"第{i}题：请翻译「{q_text}」\n"
            elif q_type == 'translation_cn_to_jp':
                prompt += f"第{i}题：「{q_text}」用日语怎么说？\n"
            elif q_type == 'verb_conjugation':
                prompt += f"第{i}题：{q_text}\n"
            else:
                prompt += f"第{i}题：{q_text}\n"
            
            if include_hints and hint:
                prompt += f"提示：{hint}\n"
            
            prompt += "\n"
        
        prompt += """请一题一题来，不要一次性说完。准备好后请说「我们开始吧」。

如果我对某个语法点不理解，请用简单的方式解释，并给我1-2个例句。"""
        
        # 保存到今日练习记录
        today = datetime.now().strftime('%Y-%m-%d')
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE daily_practice SET prompt_text = ? WHERE practice_date = ?
            ''', (prompt, today))
        
        return jsonify({
            'success': True,
            'data': {
                'prompt': prompt,
                'question_count': len(questions),
                'estimated_time': f'{len(questions) * 1}-{len(questions) * 1.5:.0f}分钟'
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

@practice_bp.route('/submit', methods=['POST'])
def submit_practice():
    """提交练习结果"""
    try:
        data = request.get_json()
        practice_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        answers = data.get('answers', [])
        completed = data.get('completed', True)
        
        # 计算得分
        correct_count = sum(1 for a in answers if a.get('is_correct', False))
        total = len(answers)
        score = int(correct_count / total * 100) if total > 0 else 0
        
        # 分析薄弱点
        weak_points = []
        for answer in answers:
            if not answer.get('is_correct', False):
                q_type = answer.get('question_type', '')
                if q_type == 'verb_conjugation':
                    weak_points.append('动词活用')
                elif q_type == 'particle':
                    weak_points.append('助词用法')
        
        weak_points = list(set(weak_points))[:3]  # 最多3个
        
        # 保存结果
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE daily_practice
                SET answers = ?, completed = ?, score = ?
                WHERE practice_date = ?
            ''', (json.dumps(answers), completed, score, practice_date))
        
        return jsonify({
            'success': True,
            'data': {
                'score': correct_count,
                'total': total,
                'accuracy': round(correct_count / total, 2) if total > 0 else 0,
                'wrong_questions': [i+1 for i, a in enumerate(answers) if not a.get('is_correct', False)],
                'review_recommendations': weak_points
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

def _create_question(entry: dict, question_id: int, now: datetime) -> dict:
    """根据学习内容创建题目"""
    # 计算已创建天数
    created_at = datetime.fromisoformat(entry['created_at'].replace('Z', '+00:00'))
    days_ago = (now - created_at).days
    is_new = days_ago <= 7
    
    # 随机选择题型
    question_types = ['translation_jp_to_cn', 'translation_cn_to_jp']
    if entry.get('content_type') == 'sentence':
        q_type = random.choice(question_types)
    else:
        q_type = 'word_recognition'
    
    if q_type == 'translation_jp_to_cn':
        return {
            'id': question_id,
            'type': 'translation_jp_to_cn',
            'question': entry['original_jp'],
            'correct_answer': entry['chinese_meaning'],
            'hint': f"读音: {entry['hiragana']}",
            'source_entry_id': entry['id'],
            'is_new': is_new,
            'days_since_created': days_ago
        }
    elif q_type == 'translation_cn_to_jp':
        return {
            'id': question_id,
            'type': 'translation_cn_to_jp',
            'question': entry['chinese_meaning'],
            'correct_answer': entry['original_jp'],
            'hint': f"读音: {entry.get('romaji', entry['hiragana'])}",
            'source_entry_id': entry['id'],
            'is_new': is_new,
            'days_since_created': days_ago
        }
    else:
        return {
            'id': question_id,
            'type': 'word_recognition',
            'question': entry['original_jp'],
            'correct_answer': entry['chinese_meaning'],
            'hint': f"读音: {entry['hiragana']}",
            'source_entry_id': entry['id'],
            'is_new': is_new,
            'days_since_created': days_ago
        }
