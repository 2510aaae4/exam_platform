from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
import os
import json
from datetime import datetime
from functools import wraps
import traceback
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# 初始化 SQL Database
db = SQLAlchemy(app)



# 数据库模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    exam_records = db.relationship('ExamRecord', backref='user', lazy=True)
    notes = db.relationship('Note', backref='user', lazy=True)

class ExamRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_id = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    score = db.Column(db.Float, nullable=False)
    answers = db.Column(db.JSON, nullable=False)  # 儲存用戶答案
    confidence = db.Column(db.JSON, nullable=False)  # 儲存把握度
    notes = db.relationship('Note', backref='exam_record', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
            'score': self.score,
            'answers': self.answers,
            'confidence': self.confidence
        }

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_record_id = db.Column(db.Integer, db.ForeignKey('exam_record.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_note_exam_question', 'exam_record_id', 'question_number'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'exam_record_id': self.exam_record_id,
            'question_number': self.question_number,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# 只在首次運行時創建表
with app.app_context():
    try:
        # 刪除所有表並重新創建
        db.drop_all()
        db.create_all()
        print("Database tables dropped and recreated successfully")
        
        # 從 allowed_users.txt 讀取並創建用戶
        with open('allowed_users.txt', 'r') as f:
            allowed_users = f.read().splitlines()
            for username in allowed_users:
                if username.strip():
                    user = User(username=username.strip())
                    db.session.add(user)
            db.session.commit()
        print("Initial users created successfully")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        print(traceback.format_exc())

# 验证用户是否存在
def validate_user(username):
    with open('allowed_users.txt', 'r') as f:
        allowed_users = f.read().splitlines()
    return username in allowed_users

def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Error in {f.__name__}:")
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    return wrapper

def load_exam_content(exam_id):
    try:
        year = exam_id.split('_')[0]
        part = exam_id.split('_')[1]
        
        base_dir = os.path.dirname(__file__)
        print(f"Base directory: {base_dir}")
        
        # 讀取題目文件
        questions_file = os.path.join(base_dir, 'questions', year, f'{year}_{part}.md')
        answers_file = os.path.join(base_dir, 'questions', year, f'{year}_{part}_answers.txt')
        
        print(f"Attempting to load exam content from: {questions_file}")
        print(f"Answers file path: {answers_file}")
        
        if not os.path.exists(questions_file):
            print(f"Questions file not found: {questions_file}")
            return None
            
        if not os.path.exists(answers_file):
            print(f"Answers file not found: {answers_file}")
            return None
            
        # 使用 utf-8-sig 來處理可能的 BOM
        with open(questions_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            
        print(f"Successfully read questions file. Content length: {len(content)}")
            
        questions = []
        current_question = None
        current_content = []
        
        # 預處理內容，移除特殊字符
        content = content.replace('\ufeff', '')  # 移除 BOM
        content = ''.join(char for char in content if ord(char) < 65536)  # 只保留基本多語言平面字符
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:  # 跳過空行
                continue
                
            if line.startswith('## '):  # 新題目開始
                if current_question:
                    if current_content:
                        current_question['content'] = '\n'.join(current_content)
                    questions.append(current_question)
                question_text = line[3:].strip()  # 移除 "## "
                # 從題目文字中提取題號
                question_number = question_text.split('.')[0]
                current_question = {
                    'number': question_number,
                    'content': question_text,
                    'options': [],
                    'image': None
                }
                # 檢查是否有對應的圖片
                image_path = os.path.join(base_dir, 'questions', year, 'image', f"{question_number}.png")
                print(f"Checking for image: {image_path}")
                if os.path.exists(image_path):
                    relative_path = os.path.join(year, 'image', f"{question_number}.png")
                    image_url = url_for('serve_questions', filename=relative_path, _external=True)
                    current_question['image'] = image_url
                    print(f"Found image for question {question_number}. URL: {image_url}")
                else:
                    print(f"No image found for question {question_number}")
                current_content = [question_text]
            elif line.startswith(('A.', 'B.', 'C.', 'D.', 'E.')):  # 選項
                if current_question:
                    current_question['options'].append(line[2:].strip())
                    # 如果這是最後一個選項，檢查是否有對應的圖片
                    if line.startswith('E.'):
                        image_path = os.path.join(base_dir, 'questions', year, 'image', f"{current_question['number']}.png")
                        print(f"Checking for image: {image_path}")
                        if os.path.exists(image_path):
                            relative_path = os.path.join(year, 'image', f"{current_question['number']}.png")
                            image_url = url_for('serve_questions', filename=relative_path, _external=True)
                            current_question['image'] = image_url
                            print(f"Found image for question {current_question['number']}. URL: {image_url}")
                        else:
                            print(f"No image found for question {current_question['number']}")
            elif line == '%':  # 答案分隔符
                continue
            elif line in ['A', 'B', 'C', 'D', 'E']:  # 答案
                continue
            else:
                if current_question and not line.startswith('##'):
                    current_content.append(line)
                    
        # 處理最後一題
        if current_question:
            if current_content:
                current_question['content'] = '\n'.join(current_content)
            # 檢查最後一題是否有圖片
            image_path = os.path.join(base_dir, 'questions', year, 'image', f"{current_question['number']}.png")
            print(f"Checking for image: {image_path}")
            if os.path.exists(image_path):
                relative_path = os.path.join(year, 'image', f"{current_question['number']}.png")
                image_url = url_for('serve_questions', filename=relative_path, _external=True)
                current_question['image'] = image_url
                print(f"Found image for question {current_question['number']}. URL: {image_url}")
            else:
                print(f"No image found for question {current_question['number']}")
            questions.append(current_question)
            
        print(f"Successfully processed {len(questions)} questions")
        return {
            'questions': questions
        }
        
    except Exception as e:
        print(f"Error loading exam content: {str(e)}")
        print(traceback.format_exc())
        return None

def convert_letter_to_index(letter):
    """將答案字母轉換為索引"""
    mapping = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}
    return mapping.get(letter.strip().upper())

def calculate_score(exam_id, user_answers):
    """計算考試分數"""
    try:
        # 解析年份和部分
        year = exam_id.split('_')[0]
        part = exam_id.split('_')[1]
        
        # 構建答案文件路徑
        answer_file = os.path.join('questions', year, f'{year}_{part}_answers.txt')
        
        if not os.path.exists(answer_file):
            raise Exception('找不到答案文件')
        
        # 讀取並轉換答案
        with open(answer_file, 'r', encoding='utf-8') as f:
            correct_answers = []
            for line in f:
                letter = line.strip()
                if letter:
                    index = convert_letter_to_index(letter)
                    if index is not None:
                        correct_answers.append(index)
                    else:
                        raise Exception('答案文件格式錯誤')
        
        if len(correct_answers) != 80:
            raise Exception('答案文件格式錯誤')
        
        # 計算分數
        score = 0
        for i, answer in enumerate(user_answers):
            if answer is not None and answer == correct_answers[i]:
                score += 1.25
        
        return score
        
    except Exception as e:
        print(f"Error calculating score: {str(e)}")
        raise e

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username')
        if not username:
            return jsonify({'success': False, 'message': '請輸入用戶名'})
            
        if validate_user(username):
            session['username'] = username
            # 檢查用戶是否存在，如果不存在則創建
            user = User.query.filter_by(username=username).first()
            if not user:
                try:
                    user = User(username=username)
                    db.session.add(user)
                    db.session.commit()
                    print(f"Created new user: {username}")
                except Exception as e:
                    db.session.rollback()
                    print(f"Error creating user: {str(e)}")
                    return jsonify({'success': False, 'message': '創建用戶時發生錯誤'})
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': '無效的用戶名'})
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'success': False, 'message': '登入時發生錯誤'})

@app.route('/simulation')
def simulation():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('simulation.html')

@app.route('/past_exams')
def past_exams():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('past_exams.html')

@app.route('/load-exam/<exam_id>')
@handle_errors
def load_exam_route(exam_id):
    if 'username' not in session:
        return jsonify({
            'success': False,
            'error': '請先登入'
        }), 401
    
    print(f"User {session['username']} attempting to load exam {exam_id}")
    
    try:
        # 使用 load_exam_content 函數載入考卷
        exam_content = load_exam_content(exam_id)
        
        if exam_content is None:
            return jsonify({
                'success': False,
                'error': '找不到試卷文件'
            }), 404
            
        return jsonify({
            'success': True,
            'questions': exam_content['questions']
        })
        
    except Exception as e:
        print(f"Error loading exam: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'載入試卷時發生錯誤：{str(e)}'
        }), 500

@app.route('/submit-exam', methods=['POST'])
def submit_exam():
    try:
        if 'username' not in session:
            return jsonify({'success': False, 'message': '請先登入'})

        data = request.get_json()
        exam_id = data.get('exam_id')
        answers = data.get('answers')
        confidence = data.get('confidence')

        if not all([exam_id, answers]):
            return jsonify({'success': False, 'message': '缺少必要資料'})

        # 獲取用戶
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            return jsonify({'success': False, 'message': '用戶不存在'})

        # 計算分數
        score = calculate_score(exam_id, answers)

        # 創建考試記錄
        record = ExamRecord(
            user_id=user.id,
            exam_id=exam_id,
            score=score,
            answers=answers,
            confidence=confidence or []
        )
        db.session.add(record)
        db.session.commit()

        return jsonify({
            'success': True,
            'record_id': record.id
        })

    except Exception as e:
        print(f"Error in submit_exam: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/score-result/<int:record_id>')
def score_result(record_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    try:
        record = ExamRecord.query.get(record_id)
        if not record:
            abort(404)

        user = User.query.filter_by(username=session['username']).first()
        if not user or record.user_id != user.id:
            abort(403)

        return render_template('score_result.html', record=record)

    except Exception as e:
        print(f"Error in score_result: {str(e)}")
        return render_template('404.html'), 404

@app.route('/api/exam-notes/<record_id>')
def get_exam_notes(record_id):
    if 'username' not in session:
        return jsonify({'success': False, 'error': '請先登入'})

    try:
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            return jsonify({'success': False, 'error': '找不到用戶'})

        # 獲取特定考試記錄
        exam_record = ExamRecord.query.get(record_id)
        if not exam_record:
            return jsonify({'success': False, 'error': '找不到考試記錄'})

        # 只獲取當前用戶對這個考試記錄的筆記
        notes = Note.query.filter_by(
            user_id=user.id,
            exam_record_id=record_id
        ).order_by(Note.question_number).all()

        # 按題號組織筆記
        notes_by_question = {}
        for note in notes:
            notes_by_question[str(note.question_number)] = [{
                'content': note.content,
                'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }]

        return jsonify({
            'success': True,
            'notes': notes_by_question
        })

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save-notes', methods=['POST'])
def save_notes():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '請先登入'})

    try:
        data = request.get_json()
        record_id = data.get('record_id')
        notes_data = data.get('notes', {})

        if not record_id:
            return jsonify({'success': False, 'message': '缺少考試記錄ID'})

        user = User.query.filter_by(username=session['username']).first()
        if not user:
            return jsonify({'success': False, 'message': '用戶不存在'})

        exam_record = ExamRecord.query.get(record_id)
        if not exam_record:
            return jsonify({'success': False, 'message': '考試記錄不存在'})

        # 刪除該用戶對該考試的所有舊筆記
        Note.query.filter_by(
            user_id=user.id,
            exam_record_id=record_id
        ).delete()

        # 添加新筆記
        for question_num, content in notes_data.items():
            if content.strip():  # 只保存非空筆記
                note = Note(
                    user_id=user.id,
                    exam_record_id=record_id,
                    question_number=int(question_num),
                    content=content.strip()
                )
                db.session.add(note)

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        print(f"Error in save_notes: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/exam-records')
def get_exam_records():
    if 'username' not in session:
        return jsonify({'success': False, 'error': '請先登入'})

    try:
        # 獲取用戶ID
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            return jsonify({'success': False, 'error': '找不到用戶'})

        # 獲取用戶的所有考試記錄，按日期降序排序
        records = ExamRecord.query.filter_by(user_id=user.id).order_by(ExamRecord.date.desc()).all()

        # 將記錄按考試ID分組
        grouped_records = {}
        for record in records:
            exam_id = record.exam_id
            year = exam_id.split('_')[0]
            part = '前80題' if exam_id.endswith('_1') else '後80題'
            exam_title = f'{year}年度{part}'

            if exam_id not in grouped_records:
                grouped_records[exam_id] = {
                    'exam_id': exam_id,
                    'title': exam_title,
                    'attempts': [],
                    'highest_score': 0
                }

            # 添加本次嘗試記錄
            attempt = {
                'record_id': record.id,
                'score': record.score,
                'date': record.date.strftime('%Y-%m-%d %H:%M'),
                'confidence_stats': {
                    'high': sum(1 for c in record.confidence if c == 'high'),
                    'medium': sum(1 for c in record.confidence if c == 'medium'),
                    'low': sum(1 for c in record.confidence if c == 'low')
                }
            }
            grouped_records[exam_id]['attempts'].append(attempt)

            # 更新最高分
            if record.score > grouped_records[exam_id]['highest_score']:
                grouped_records[exam_id]['highest_score'] = record.score

        return jsonify({
            'success': True,
            'records': list(grouped_records.values())
        })

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'success': False, 'error': str(e)})

@app.route('/exam-detail/<int:record_id>')
def exam_detail(record_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        abort(403)

    record = ExamRecord.query.get_or_404(record_id)
    if record.user_id != user.id:
        abort(403)

    try:
        # 載入題目
        questions = load_exam_content(record.exam_id)

        # 解析年份和部分
        year = record.exam_id.split('_')[0]
        part = record.exam_id.split('_')[1]

        # 構建答案文件路徑
        answer_file = os.path.join(app.root_path, 'questions', year, f'{year}_{part}_answers.txt')

        # 載入答案並轉換為索引
        with open(answer_file, 'r', encoding='utf-8') as f:
            correct_answers = []
            for line in f:
                letter = line.strip()
                if letter:
                    index = convert_letter_to_index(letter)
                    if index is not None:
                        correct_answers.append(index)

        # 載入筆記
        notes = {note.question_number: note.content for note in 
                Note.query.filter_by(exam_record_id=record_id).all()}

        # 載入其他用戶的筆記
        other_notes = Note.query.join(ExamRecord).filter(
            ExamRecord.exam_id == record.exam_id,
            Note.user_id != user.id
        ).all()

        other_notes_by_question = {}
        for note in other_notes:
            if note.question_number not in other_notes_by_question:
                other_notes_by_question[note.question_number] = []
            note_dict = note.to_dict()
            note_dict['username'] = User.query.get(note.user_id).username
            other_notes_by_question[note.question_number].append(note_dict)

        # 準備題目資料
        questions_data = []
        for i, question in enumerate(questions['questions']):
            user_answer = record.answers[i]
            correct_answer = correct_answers[i]
            question_number = i + 1

            options_data = []
            for j, option in enumerate(question['options']):
                options_data.append({
                    'content': option,
                    'is_user_answer': user_answer == j,
                    'is_correct': correct_answer == j
                })

            questions_data.append({
                'number': question_number,
                'content': question['content'],
                'image': question.get('image'),
                'options': options_data,
                'confidence': record.confidence[i],
                'is_correct': user_answer == correct_answer,
                'notes': notes.get(question_number, ''),
                'other_notes': other_notes_by_question.get(question_number, [])
            })

        exam_year = record.exam_id.split('_')[0]
        exam_part = '前80題' if record.exam_id.endswith('_1') else '後80題'
        exam_title = f'{exam_year}年度{exam_part}'

        return render_template('exam_detail.html',
                             exam_record=record,
                             exam_title=exam_title,
                             score=record.score,
                             date=record.date.strftime('%Y-%m-%d %H:%M'),
                             questions=questions_data)

    except Exception as e:
        print("錯誤詳情:", str(e))
        import traceback
        print("完整錯誤追蹤:", traceback.format_exc())
        return render_template('error.html', error="載入考試詳情時發生錯誤")

@app.route('/api/save-notes', methods=['POST'])
def save_notes_api():
    if 'username' not in session:
        return jsonify({'success': False, 'error': '請先登入'})

    try:
        data = request.get_json()
        record_id = data.get('record_id')
        notes_data = data.get('notes', {})

        if not record_id:
            return jsonify({'success': False, 'error': '缺少考試記錄ID'})

        user = User.query.filter_by(username=session['username']).first()
        if not user:
            return jsonify({'success': False, 'error': '找不到用戶'})

        exam_record = ExamRecord.query.get(record_id)
        if not exam_record:
            return jsonify({'success': False, 'error': '考試記錄不存在'})

        # 處理每一題的筆記
        for question_num, content in notes_data.items():
            if content.strip():  # 只保存非空筆記
                # 檢查是否已有筆記
                note = Note.query.filter_by(
                    user_id=user.id,
                    exam_record_id=record_id,
                    question_number=int(question_num)
                ).first()

                if note:
                    # 更新現有筆記
                    note.content = content.strip()
                else:
                    # 創建新筆記
                    note = Note(
                        user_id=user.id,
                        exam_record_id=record_id,
                        question_number=int(question_num),
                        content=content.strip()
                    )
                    db.session.add(note)

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        print(f"Error in save_notes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/questions/<path:filename>')
@handle_errors
def serve_questions(filename):
    """處理靜態文件請求"""
    try:
        # 移除任何可能的路徑操作
        filename = os.path.normpath(filename).replace('\\', '/')
        if filename.startswith('..') or filename.startswith('/'):
            return jsonify({
                'success': False,
                'error': '無效的文件路徑'
            }), 400

        questions_dir = os.path.join(os.path.dirname(__file__), 'questions')
        file_path = os.path.join(questions_dir, filename)

        print(f"Attempting to serve file: {filename}")
        print(f"Full path: {file_path}")

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            return jsonify({
                'success': False,
                'error': '文件不存在'
            }), 404

        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)

        try:
            return send_from_directory(directory, filename)
        except Exception as e:
            print(f"Error sending file: {str(e)}")
            return jsonify({
                'success': False,
                'error': '無法發送文件'
            }), 500

    except Exception as e:
        print(f"Error serving file {filename}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'處理文件請求時發生錯誤：{str(e)}'
        }), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'success': False,
            'error': 'Not found'
        }), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
