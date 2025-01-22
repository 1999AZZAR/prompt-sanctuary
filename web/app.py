import secrets
import time
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.exceptions import BadRequestKeyError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlite3 import OperationalError, connect
import logging

# Dedicated models
from chat_area import GeminiChat
from stability import ImageGen
from response2 import GenerativeAI
from response import GenerativeModel

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

# Database paths
USER_DATABASE = os.getenv('USER_DATABASE', './database/user.db')
PROMPT_DATABASE = os.getenv('PROMPT_DATABASE', './database/prompt_data.db')
IMAGE_LOG = os.getenv('IMAGE_LOG', './database/image_log.db')
QUERY_DATABASE = os.getenv('QUERY_DATABASE', './database/community/query.db')
COMMUNITY_DATABASE = os.getenv('COMMUNITY_DATABASE', './database/community/shared.db')
FEEDBACK_DATABASE = os.getenv('FEEDBACK_DATABASE', './database/feedback.db')

# Initialize models
chat_app = GeminiChat()
image_generator = ImageGen()
ai = GenerativeAI()
model = GenerativeModel()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database utility functions
def get_db_connection(db_path):
    return connect(db_path)

def create_table(db_path, table_sql):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(table_sql)
        conn.commit()

# Create necessary tables
create_table(USER_DATABASE, '''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
''')

create_table(IMAGE_LOG, '''
    CREATE TABLE IF NOT EXISTS images (
        filename TEXT,
        creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

create_table(COMMUNITY_DATABASE, '''
    CREATE TABLE IF NOT EXISTS shared (
        owner TEXT,
        random_val TEXT,
        title TEXT,
        prompt TEXT,
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

create_table(FEEDBACK_DATABASE, '''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        feedback TEXT NOT NULL
    )
''')

# Decorator for login required
def required_login(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_function

# Function to delete old images
def delete_old_images():
    with get_db_connection(IMAGE_LOG) as conn:
        cursor = conn.cursor()
        image_dir = "./web/static/image"
        if os.path.exists(image_dir):
            now = time.time()
            for row in cursor.execute("SELECT filename, creation_time FROM images"):
                filename, creation_time = row
                creation_time = time.mktime(time.strptime(creation_time, "%Y-%m-%d %H:%M:%S"))
                file_path = os.path.join(image_dir, filename)
                if os.path.isfile(file_path) and now - creation_time > 1800:
                    os.remove(file_path)
                    cursor.execute("DELETE FROM images WHERE filename=?", (filename,))
                    conn.commit()

# Routes
@app.route('/')
def index():
    return render_template('login.html', error_message=None)

@app.route('/signup', methods=['POST'])
def signup():
    honeypot_value = request.form.get('honeypot', '')
    if honeypot_value:
        return 'Bot activity detected. Access denied.'

    username = request.form['username']
    password = request.form['password']

    with get_db_connection(USER_DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            return render_template('login.html', error_message='Username already exists. Please choose another.')

        hashed_password = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()

    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    honeypot_value = request.form.get('honeypot', '')
    if honeypot_value:
        return render_template('login.html', error_message='Bot activity detected. Access denied.')

    username = request.form['username']
    password = request.form['password']

    with get_db_connection(USER_DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

    if user and check_password_hash(user[1], password):
        session['username'] = username
        return redirect(url_for('home'))

    return render_template('login.html', error_message='Invalid username or password. Please try again.')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/home')
@required_login
def home():
    return render_template('index.html')

@app.route('/mylib')
@required_login
def mylib():
    username = session['username']
    table_name = username

    try:
        with get_db_connection(PROMPT_DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(f'SELECT random_val, title, prompt, time FROM {table_name}')
            saved_prompts = cursor.fetchall()
    except OperationalError:
        saved_prompts = None

    return render_template('prompts/lib/personal_library.html', saved_prompts=saved_prompts)

@app.route('/save_edit', methods=['POST'])
@required_login
def save_edit():
    username = session['username']
    table_name = username

    random_val = request.form['random_val']
    edited_title = request.form['edited_title']
    edited_prompt = request.form['edited_prompt']

    with get_db_connection(PROMPT_DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(f'UPDATE {table_name} SET title=?, prompt=? WHERE random_val=?', (edited_title, edited_prompt, random_val))
        conn.commit()

    return redirect(url_for('mylib'))

@app.route('/share_prompt', methods=['POST'])
@required_login
def share_prompt():
    data = request.json
    owner = session['username']

    if not owner:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    random_val = data.get('prompt_id')
    title = data.get('title')
    prompt = data.get('prompt')

    if not random_val or not title or not prompt:
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    with get_db_connection(COMMUNITY_DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO shared (owner, random_val, title, prompt) VALUES (?, ?, ?, ?)', (owner, random_val, title, prompt))
        conn.commit()

    return jsonify({'success': True})

@app.route('/delete_prompt', methods=['POST'])
@required_login
def delete_prompt():
    prompt_id = request.form['prompt_id']
    username = session['username']

    with get_db_connection(PROMPT_DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM {username} WHERE random_val = ?', (prompt_id,))
        conn.commit()

    return redirect(url_for('mylib'))

@app.route('/library')
@required_login
def library():
    try:
        with get_db_connection(QUERY_DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT random_val, username, tittle, prompt, tag, time FROM community')
            system_prompts = cursor.fetchall()

        with get_db_connection(COMMUNITY_DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT owner, random_val, title, prompt, time FROM shared')
            shared_prompts = cursor.fetchall()

    except Exception as e:
        logger.error(f"Error fetching prompts: {e}")
        system_prompts, shared_prompts = [], []

    return render_template('prompts/lib/community_library.html', system_prompts=system_prompts, shared_prompts=shared_prompts)

@app.route('/trying')
@required_login
def trying():
    return render_template('try.html')

@app.route('/user_input', methods=['POST'])
@required_login
def handle_user_input():
    honeypot_value = request.form.get('honeypot', '')
    if honeypot_value:
        return 'Bot activity detected. Access denied.'

    user_input = request.get_json().get('user_input', '').lower()

    if user_input.startswith('imagine'):
        prompt = user_input[len('imagine'):].strip()
        prompt_text = prompt if prompt else 'Your prompt here'
        image_path = image_generator.generate_image(prompt_text)
        if image_path:
            delete_old_images()
            with get_db_connection(IMAGE_LOG) as conn:
                cursor = conn.cursor()
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO images (filename, creation_time) VALUES (?, ?)", (image_path, current_time))
                conn.commit()
            return jsonify({'image_path': image_path})
        return jsonify({'bot_response': 'Error generating image'})

    elif user_input.startswith('tittle'):
        prompt = user_input[len('tittle'):].strip()
        prompt_text = prompt if prompt else 'Your prompt here'
        response = chat_app.generate_tittle(user_input)
        return jsonify({'bot_response': response}) if response else jsonify({'bot_response': 'Error generating tittle'})

    else:
        response = chat_app.generate_chat(user_input)
        return jsonify({'bot_response': response}) if response else jsonify({'bot_response': 'Error generating response'})

@app.route('/generate')
@required_login
def generate():
    return render_template('prompts/generator/basic.html')

@app.route('/generate/tprompt', methods=['POST'])
@required_login
def process():
    user_input = request.form['user_input']
    response_text = model.generate_response('./instruction/basic1.txt', user_input)
    return response_text

@app.route('/generate/trandom', methods=['POST'])
@required_login
def random_prompt():
    response_text = model.generate_random('./instruction/basic2.txt')
    return response_text

@app.route('/generate/iprompt', methods=['POST'])
@required_login
def vprocess():
    user_input = request.form['user_input']
    response_text = model.generate_imgdescription('./instruction/image_styles.txt', user_input)
    return response_text

@app.route('/generate/irandom', methods=['POST'])
@required_login
def vrandom_prompt():
    response_text = model.generate_vrandom('./instruction/image_styles.txt')
    return response_text

@app.route('/generate/image', methods=['POST'])
@required_login
def reverse_image():
    try:
        image_file = request.files['image']
        image_data = image_file.read()
        response_text = model.generate_visual('./instruction/image_styles.txt', image_data)
        return response_text
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return f"Error: {str(e)}"

@app.route('/advance')
@required_login
def advance():
    return render_template('prompts/generator/advance.html')

@app.route('/advance/generate', methods=['POST'])
@required_login
def generate_advance_response():
    try:
        parameters = [request.form[f'parameter{i}'] for i in range(4)]
        response_text = ai.response(*parameters, './instruction/advance1.txt')
        return response_text
    except BadRequestKeyError as e:
        logger.error(f"Bad Request: {e}")
        return f"Bad Request: {e.description}"

@app.route('/advance/igenerate', methods=['POST'])
@required_login
def generate_advance_iresponse():
    try:
        parameters = [request.form[f'parameter{i}'] for i in range(4)]
        response_text = ai.response(*parameters, './instruction/advance2.txt')
        return response_text
    except BadRequestKeyError as e:
        logger.error(f"Bad Request: {e}")
        return f"Bad Request: {e.description}"

@app.route('/advance/image', methods=['POST'])
@required_login
def advance_image():
    try:
        image_file = request.files['image']
        image_data = image_file.read()
        parameters = [request.form[f'parameter{i}'] for i in range(1, 4)]
        response_text = model.generate_visual2(image_data, *parameters)
        return response_text
    except Exception as e:
        logger.error(f"Error processing advance image: {e}")
        return f"Error: {str(e)}"

@app.route('/save_prompt', methods=['POST'])
@required_login
def save_prompt():
    try:
        title = request.form['title']
        prompt = request.form['prompt']
        random_value = secrets.token_urlsafe(8)
        username = session['username']

        with get_db_connection(PROMPT_DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(f'INSERT INTO {username} (random_val, title, prompt) VALUES (?, ?, ?)', (random_value, title, prompt))
            conn.commit()

        return 'Prompt saved successfully!'
    except Exception as e:
        logger.error(f"Error saving prompt: {e}")
        return f"Error: {str(e)}"

@app.route('/submit_feedback', methods=['POST'])
@required_login
def submit_feedback():
    username = session['username']
    feedback = request.form['feedback']

    with get_db_connection(FEEDBACK_DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO feedback (username, feedback) VALUES (?, ?)', (username, feedback))
        conn.commit()

    return jsonify({'status': 'success', 'message': 'Feedback submitted successfully!'})

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 80)))