import secrets
import time
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.exceptions import BadRequestKeyError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlite3 import OperationalError
import sqlite3

# dedicated models
from chat_area import GeminiChat #used on prompt trial
from stability import Image_gen #used on prompt trial
from response2 import GenerativeAI
from response import GenerativeModel

# microservices call
app = Flask(__name__)
USER_DATABASE = './database/user.db'
PROMPT_DATABASE = './database/prompt_data.db'
IMAGE_LOG = './database/image_log.db'
QUERY_DATABASE = './database/community/query.db'
COMMUNITY_DATABASE = './database/community/shared.db'
FEEDBACK_DATABASE = './database/feedback.db'
chat_app = GeminiChat()
image_generator = Image_gen() 
ai = GenerativeAI()
model = GenerativeModel()

# user database
def create_table():
    conn = sqlite3.connect(USER_DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_table()
#secret for user account table
app.secret_key = 'hahahaha' 

# image log database
def image_table():
    conn = sqlite3.connect(IMAGE_LOG)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS images (
            filename TEXT,
            creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

image_table()


# personal user prompt database
def create_prompt_table(username):
    conn = sqlite3.connect(PROMPT_DATABASE)
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {username} (
            random_val TEXT,
            title TEXT,
            prompt TEXT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# shared user prompt database
def create_community_table():
    conn = sqlite3.connect(COMMUNITY_DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shared (
            owner TEXT,
            random_val TEXT,
            title TEXT,
            prompt TEXT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

create_community_table()

# feedback database
def feedback_table():
    conn = sqlite3.connect(FEEDBACK_DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            feedback TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

feedback_table()

# login check
def required_login(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_function

# Function to delete old images from database and filesystem
def delete_old_images():
    conn = sqlite3.connect(IMAGE_LOG)
    c = conn.cursor()
    image_dir = "./web/static/image"
    if os.path.exists(image_dir):
        now = time.time()
        for row in c.execute("SELECT filename, creation_time FROM images"):
            filename, creation_time = row
            # Convert creation_time to a numeric timestamp
            creation_time = time.mktime(time.strptime(creation_time, "%Y-%m-%d %H:%M:%S"))
            file_path = os.path.join(image_dir, filename)
            if os.path.isfile(file_path):
                # Check if file is older than 1/2 hour
                if now - creation_time > 1800:
                    os.remove(file_path)
                    c.execute("DELETE FROM images WHERE filename=?", (filename,))
                    conn.commit()
    conn.close()

# index
@app.route('/')
def index():
    return render_template('login.html', error_message=None)

# signup
@app.route('/signup', methods=['POST'])
def signup():
    # prevent bot with honeypot
    honeypot_value = request.form.get('honeypot', '')
    if honeypot_value:
        return 'Bot activity detected. Access denied.'
    
    # add user to the database
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect(USER_DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if user:
        error_message = 'Username already exists. Please choose another.'
        return render_template('login.html', error_message=error_message)

    # hashing the user password
    hashed_password = generate_password_hash(password)
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# login
@app.route('/login', methods=['POST'])
def login():
    # prevent bot with honeypot
    honeypot_value = request.form.get('honeypot', '')
    if honeypot_value:
        error_message = 'Bot activity detected. Access denied.'
        return render_template('login.html', error_message=error_message)

    # retrieve user database
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect(USER_DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    # check if user exists and password matches
    if user and check_password_hash(user[1], password): 
        session['username'] = username
        return redirect(url_for('home'))

    else:
        error_message = 'Invalid username or password. Please try again.'
        return render_template('login.html', error_message=error_message)

# logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# home
@app.route('/home')
@required_login
def home():
    return render_template('index.html')

# user personal library
@app.route('/mylib')
@required_login
def mylib():
    try:
        username = session['username']
        table_name = username 
        conn = sqlite3.connect(PROMPT_DATABASE)
        cursor = conn.cursor()

        try:
            cursor.execute(f'SELECT 1 FROM {table_name} LIMIT 1')
        except OperationalError:
            conn.close()
            return render_template('prompts/lib/personal_library.html', saved_prompts=None)

        cursor.execute(f'SELECT random_val, title, prompt, time FROM {table_name}')
        saved_prompts = cursor.fetchall()
        conn.close()
        return render_template('prompts/lib/personal_library.html', saved_prompts=saved_prompts)

    except Exception as e:
        return f"Error: {str(e)}"

# save new prompt that have been edited
@app.route('/save_edit', methods=['POST'])
@required_login
def save_edit():
    try:
        username = session['username']
        table_name = username 
        conn = sqlite3.connect(PROMPT_DATABASE)
        cursor = conn.cursor()

        random_val = request.form['random_val']  # Get the random_val from the form
        edited_title = request.form['edited_title']  # Get the edited title from the form
        edited_prompt = request.form['edited_prompt']  # Get the edited prompt from the form

        # Update the title and prompt in the database using the random_val as the key
        cursor.execute(f'UPDATE {table_name} SET title=?, prompt=? WHERE random_val=?', (edited_title, edited_prompt, random_val))
        conn.commit()
        conn.close()

        return redirect(url_for('mylib'))

    except Exception as e:
        return f"Error: {str(e)}"

# share to community
@app.route('/share_prompt', methods=['POST'])
@required_login
def share_prompt():
    try:
        data = request.json
        print('Received data:', data)  # Log the received data

        owner = session['username']
        if not owner:
            return jsonify({'success': False, 'error': 'User not logged in'}), 401

        random_val = data.get('prompt_id')
        title = data.get('title')
        prompt = data.get('prompt')

        if not random_val or not title or not prompt:
            return jsonify({'success': False, 'error': 'Missing data'}), 400

        conn = sqlite3.connect(COMMUNITY_DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO shared (owner, random_val, title, prompt)
            VALUES (?, ?, ?, ?)
        ''', (owner, random_val, title, prompt))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)}), 500

# delete prompt from user library
@app.route('/delete_prompt', methods=['POST'])
@required_login
def delete_prompt():
    try:
        prompt_id = request.form['prompt_id']
        username = session['username']

        conn = sqlite3.connect(PROMPT_DATABASE)
        cursor = conn.cursor()

        cursor.execute(f'DELETE FROM {username} WHERE random_val = ?', (prompt_id,))

        conn.commit()
        conn.close()

        return redirect(url_for('mylib'))
    except Exception as e:
        return f"Error: {str(e)}"

# community prompt library
@app.route('/library')
@required_login
def library():
    try: 
        conn = sqlite3.connect(QUERY_DATABASE)
        cursor = conn.cursor()
        cursor.execute(f'SELECT random_val, username, tittle, prompt, tag, time FROM community')
        system_prompts = cursor.fetchall()
        conn.close()
        conn = sqlite3.connect(COMMUNITY_DATABASE)
        cursor = conn.cursor()
        cursor.execute(f'SELECT owner, random_val, title, prompt, time FROM shared')
        shared_prompts = cursor.fetchall()
        conn.close()
        return render_template('prompts/lib/community_library.html', system_prompts=system_prompts, shared_prompts=shared_prompts)

    except Exception as e:
        return f"Error: {str(e)}"

# prompt trial / chat bot
@app.route('/trying')
@required_login
def trying():
    return render_template('try.html')

# chat bot form and reply
@app.route('/user_input', methods=['POST'])
@required_login
def handle_user_input():
    honeypot_value = request.form.get('honeypot', '')
    if honeypot_value:
        return 'Bot activity detected. Access denied.'

    user_input = request.get_json().get('user_input', '').lower()
    # handle the image tag input
    if user_input.startswith('imagine'):
        prompt = user_input[len('imagine'):].strip()
        prompt_text = prompt if prompt else 'Your prompt here'
        image_path = image_generator.generate_image(prompt_text)
        if image_path:
            # Delete old images before returning response
            delete_old_images()
            # Insert metadata into database with current timestamp
            conn = sqlite3.connect(IMAGE_LOG)
            c = conn.cursor()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO images (filename, creation_time) VALUES (?, ?)", (image_path, current_time))
            conn.commit()
            conn.close()
            return jsonify({'image_path': image_path})
        else:
            return jsonify({'bot_response': 'Error generating image'})
    
    # handle the tittle tag input
    elif user_input.startswith('tittle'):
        prompt = user_input[len('tittle'):].strip()
        prompt_text = prompt if prompt else 'Your prompt here'
        response = chat_app.generate_tittle(user_input)
        if response:
            return jsonify({'bot_response': response})
        else:
            return jsonify({'bot_response': 'Error generating tittle'})
    
    # handle global input
    else:
        response = chat_app.generate_chat(user_input)
        if response:
            return jsonify({'bot_response': response})
        else:
            return jsonify({'bot_response': 'Error generating response'})

# basic generator
@app.route('/generate')
@required_login
def generate():
    return render_template('prompts/generator/basic.html')

# basic generator / text prompt
@app.route('/generate/tprompt', methods=['POST'])
@required_login
def process():
    user_input = request.form['user_input']
    response_text = model.generate_response('./instruction/basic1.txt',user_input)
    return response_text

# basic generator / random text prompt
@app.route('/generate/trandom', methods=['POST'])
@required_login
def random_prompt():
    response_text = model.generate_random('./instruction/basic2.txt')
    return response_text

# basic generator / image prompt
@app.route('/generate/iprompt', methods=['POST'])
@required_login
def vprocess():
    user_input = request.form['user_input']
    response_text = model.generate_imgdescription('./instruction/image_styles.txt', user_input)
    return response_text

# basic generator / random image prompt
@app.route('/generate/irandom', methods=['POST'])
@required_login
def vrandom_prompt():
    response_text = model.generate_vrandom('./instruction/image_styles.txt')
    return response_text

# basic generator / image to prompt
@app.route('/generate/image', methods=['POST'])
@required_login
def reverse_image():
    try:
        image_file = request.files['image']
        image_data = image_file.read()

        response_text = model.generate_visual('./instruction/image_styles.txt', image_data)
        return response_text
    except Exception as e:
        return f"Error: {str(e)}"

# advance generator
@app.route('/advance')
@required_login
def advance():
    return render_template('prompts/generator/advance.html')

# advance generator / text prompt
@app.route('/advance/generate', methods=['POST'])
@required_login
def generate_advance_response():
    try:
        parameter0 = request.form['parameter0']
        parameter1 = request.form['parameter1']
        parameter2 = request.form['parameter2']
        parameter3 = request.form['parameter3']
        
        response_text = ai.response(parameter0, parameter1, parameter2, parameter3, './instruction/advance1.txt')
        return response_text
    except BadRequestKeyError as e:
        return f"Bad Request: {e.description}"

# advance generator / image prompt
@app.route('/advance/igenerate', methods=['POST'])
@required_login
def generate_advance_iresponse():
    try:
        parameter0 = request.form['parameter0']
        parameter1 = request.form['parameter1']
        parameter2 = request.form['parameter2']
        parameter3 = request.form['parameter3']
        
        response_text = ai.response(parameter0, parameter1, parameter2, parameter3, './instruction/advance2.txt')
        return response_text
    except BadRequestKeyError as e:
        return f"Bad Request: {e.description}"

# advance generator / image to prompt
@app.route('/advance/image', methods=['POST'])
@required_login
def advance_image():
    try:
        image_file = request.files['image']
        image_data = image_file.read()
        parameter1 = request.form['parameter1']
        parameter2 = request.form['parameter2']
        parameter3 = request.form['parameter3']
        response_text = model.generate_visual2(image_data, parameter1, parameter2, parameter3)
        return response_text
    except Exception as e:
        return f"Error: {str(e)}"

# save prompt to user library
@app.route('/save_prompt', methods=['POST'])
@required_login
def save_prompt():
    try:
        title = request.form['title']
        prompt = request.form['prompt']
        random_value = secrets.token_urlsafe(8)

        username = session['username']
        create_prompt_table(username)

        conn = sqlite3.connect(PROMPT_DATABASE)
        cursor = conn.cursor()

        cursor.execute(f'INSERT INTO {username} (random_val, title, prompt) VALUES (?, ?, ?)', (random_value, title, prompt))

        conn.commit()
        conn.close()

        return 'Prompt saved successfully!'
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/submit_feedback', methods=['POST'])
@required_login
def submit_feedback():
    # name = request.form['name']
    username = session['username']
    feedback = request.form['feedback']

    conn = sqlite3.connect(FEEDBACK_DATABASE)
    cursor = conn.cursor()

    cursor.execute('INSERT INTO feedback (username, feedback) VALUES (?, ?)', (username, feedback))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'message': 'Feedback submitted successfully!'})

# run the app
if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=5000)
    app.run(debug=True, port=int(os.environ.get('PORT', 80)))
