from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import random
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# データベースの初期化
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT,
            username TEXT,
            n INTEGER,
            num_trials INTEGER,
            display_time INTEGER,
            interval_time INTEGER,
            elements TEXT,
            distractor INTEGER,
            correct_a INTEGER,
            correct_b INTEGER,
            incorrect_a INTEGER,
            incorrect_b INTEGER,
            accuracy REAL,
            error_rate REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # フォームからのデータを取得
        session['username'] = request.form['username']
        session['n'] = int(request.form['n'])
        session['num_trials'] = int(request.form['num_trials'])
        session['display_time'] = int(request.form['display_time'])
        session['interval_time'] = int(request.form['interval_time'])
        session['elements'] = request.form.getlist('elements')
        session['distractor'] = int(request.form.get('distractor', 0))
        return redirect(url_for('task'))
    return render_template('index.html')

@app.route('/task')
def task():
    # タスク設定を取得
    n = session.get('n', 1)
    num_trials = session.get('num_trials', 10)
    elements = session.get('elements', ['colors'])
    distractor = session.get('distractor', 0)
    # 要素のリストを生成
    stimuli_list = generate_stimuli_list(elements, n, num_trials)
    session['stimuli_list'] = stimuli_list
    session['responses'] = []
    return render_template(
        'task.html',
        stimuli_list=stimuli_list,
        display_time=session['display_time'],
        interval_time=session['interval_time'],
        distractor=distractor
    )

@app.route('/submit', methods=['POST'])
def submit():
    responses = request.get_json()
    session['responses'] = responses
    # 結果を計算
    result = calculate_result(session['stimuli_list'], responses, session['n'])
    # データベースに保存
    save_result(session, result)
    session['result'] = result  # 結果をセッションに保存
    return jsonify(result)

@app.route('/result')
def result():
    result = session.get('result', {})
    return render_template('result.html', result=result)

def generate_stimuli_list(elements, n, num_trials):
    stimuli_list = []
    total_items = num_trials + n

    # 要素の定義
    colors = ['red', 'blue', 'green', 'yellow']
    color_names_jp = ['赤', '青', '緑', '黄']
    color_words = ['赤', '青', '緑', '黄', '黒']
    color_hex = {'赤': 'red', '青': 'blue', '緑': 'green', '黄': 'yellow', '黒': 'black'}
    symbols = ['〇', '△', '□', '×', '☆', '◎']
    positive_words = ['幸福', '愛', '平和', '喜び', '友情', '成功']
    negative_words = ['悲しみ', '怒り', '恐怖', '失敗', '憎しみ', '絶望']
    neutral_words = ['机', '本', '窓', '椅子', 'ペン', '時計']
    words = positive_words + negative_words + neutral_words
    faces = ['face1.png', 'face2.png', 'face3.png', 'face4.png', 'face5.png', 'face6.png']
    emotions = ['positive1', 'positive2', 'neutral', 'negative1', 'negative2']
    characters = ['あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ']
    numbers = [str(i) for i in range(1, 10)]

    # 刺激リストを生成
    for _ in range(total_items):
        if 'color_words' in elements:
            # 色を表す単語（単体）
            word = random.choice(color_words)
            color_options = [c for c in color_names_jp if c != word]
            color = random.choice(color_options)
            color_code = color_hex[color]
            stimulus = f'<span style="color:{color_code};">{word}</span>'
            stimuli_list.append({'type': 'color_word', 'value': stimulus})
        elif 'faces' in elements:
            # 顔と表情のセット
            face = random.choice(faces)
            emotion = random.choice(emotions)
            stimulus = f'<img src="/images/faces/{emotion}/{face}" alt="face">'
            stimuli_list.append({'type': 'face', 'value': stimulus})
        elif 'colors' in elements:
            # 色とセットの要素
            color = random.choice(colors)
            color_code = color
            if 'words' in elements:
                word = random.choice(words)
                stimulus = f'<span style="color:{color_code};">{word}</span>'
                stimuli_list.append({'type': 'word', 'value': stimulus})
            elif 'symbols' in elements:
                symbol = random.choice(symbols)
                stimulus = f'<span style="color:{color_code};">{symbol}</span>'
                stimuli_list.append({'type': 'symbol', 'value': stimulus})
            elif 'characters' in elements:
                char = random.choice(characters)
                stimulus = f'<span style="color:{color_code};">{char}</span>'
                stimuli_list.append({'type': 'character', 'value': stimulus})
            elif 'numbers' in elements:
                num = random.choice(numbers)
                stimulus = f'<span style="color:{color_code};">{num}</span>'
                stimuli_list.append({'type': 'number', 'value': stimulus})
            else:
                # デフォルトで色の●を表示
                stimulus = f'<span style="color:{color_code};">●</span>'
                stimuli_list.append({'type': 'color', 'value': stimulus})
        else:
            # エラー処理
            stimulus = '<span>エラー: 有効な要素が選択されていません。</span>'
            stimuli_list.append({'type': 'error', 'value': stimulus})
    return stimuli_list

def calculate_result(stimuli_list, responses, n):
    correct_a = 0  # ユーザーが応答し、正解だった数
    correct_b = 0  # ユーザーが応答せず、正解だった数
    incorrect_a = 0  # ユーザーが応答し、間違っていた数
    incorrect_b = 0  # ユーザーが応答せず、間違っていた数

    total_trials = len(stimuli_list)
    response_indices = {resp['index'] for resp in responses if resp['response']}

    for i in range(n, total_trials):
        current_stimulus = stimuli_list[i]
        previous_stimulus = stimuli_list[i - n]
        is_match = current_stimulus['value'] == previous_stimulus['value']
        user_responded = i in response_indices

        if is_match and user_responded:
            correct_a += 1  # 正答A
        elif not is_match and not user_responded:
            correct_b += 1  # 正答B
        elif is_match and not user_responded:
            incorrect_a += 1  # 誤答A
        elif not is_match and user_responded:
            incorrect_b += 1  # 誤答B

    total_responses = correct_a + correct_b + incorrect_a + incorrect_b
    accuracy = (correct_a + correct_b) / total_responses if total_responses > 0 else 0
    error_rate = 1 - accuracy

    return {
        'correct_a': correct_a,
        'correct_b': correct_b,
        'incorrect_a': incorrect_a,
        'incorrect_b': incorrect_b,
        'accuracy': round(accuracy * 100, 2),
        'error_rate': round(error_rate * 100, 2)
    }

def save_result(session, result):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO results (
            datetime, username, n, num_trials, display_time, interval_time, elements, distractor,
            correct_a, correct_b, incorrect_a, incorrect_b, accuracy, error_rate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
        session['username'],
        session['n'],
        session['num_trials'],
        session['display_time'],
        session['interval_time'],
        ','.join([e['type'] for e in session['stimuli_list']]),
        session['distractor'],
        result['correct_a'],
        result['correct_b'],
        result['incorrect_a'],
        result['incorrect_b'],
        result['accuracy'],
        result['error_rate']
    ))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    app.run(debug=True)
