# app.py

# library and import
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
from gemini_text_res import GeminiChat
from stability import Image_gen
from basic import generate_response, generate_random, generate_vrandom, generate_imgdescription
from gemini_vis_res import generate_content
from advance import response, iresponse


# microservices call
app = Flask(__name__)
USER_DATABASE = './web/database/user.db'
PROMPT_DATABASE = './web/database/prompt_data.db'
IMAGE_LOG = './web/database/image_log.db'
chat_app = GeminiChat()
image_generator = Image_gen() 


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

# calculation word for user database
create_table()
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
    return render_template('login.html')


# signup
@app.route('/signup', methods=['POST'])
def signup():
    honeypot_value = request.form.get('honeypot', '')
    if honeypot_value:
        return 'Bot activity detected. Access denied.'
    
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect(USER_DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if user:
        return 'Username already exists. Please choose another.'

    hashed_password = generate_password_hash(password)
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


# login
@app.route('/login', methods=['POST'])
def login():
    honeypot_value = request.form.get('honeypot', '')
    if honeypot_value:
        return 'Bot activity detected. Access denied.'
    
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect(USER_DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[1], password): 
        session['username'] = username
        return redirect(url_for('home'))

    else:
        return 'Invalid username or password. Please try again.'


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
            return render_template('my_library.html', saved_prompts=None)

        cursor.execute(f'SELECT random_val, title, prompt, time FROM {table_name}')
        saved_prompts = cursor.fetchall()
        conn.close()
        return render_template('my_library.html', saved_prompts=saved_prompts)

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
    return render_template('prompts/generator/generator.html', result=None)


# basic generator / text prompt
@app.route('/generate/tprompt', methods=['POST'])
@required_login
def process():
    user_input = request.form['user_input']
    response_text = generate_response(user_input)
    return render_template('prompts/generator/generator.html', result=response_text)


# basic generator / random text prompt
@app.route('/generate/trandom', methods=['POST'])
@required_login
def random_prompt():
    response_text = generate_random()
    return render_template('prompts/generator/generator.html', result=response_text)


# basic generator / image prompt
@app.route('/generate/iprompt', methods=['POST'])
@required_login
def vprocess():
    user_input = request.form['user_input']
    response_text = generate_imgdescription(user_input)
    return render_template('prompts/generator/generator.html', result=response_text)


# basic generator / random image prompt
@app.route('/generate/irandom', methods=['POST'])
@required_login
def vrandom_prompt():
    response_text = generate_vrandom()
    return render_template('prompts/generator/generator.html', result=response_text)


# basic generator / image to prompt
@app.route('/generate/image', methods=['POST'])
@required_login
def reverse_image():
    try:
        image_file = request.files['image']
        image_data = image_file.read()

        image_styles = [
            "3d-model", "abstract", "analog-film", "anime", "chalk-art",
            "cinematic", "comic-book", "cyberpunk", "cubism", "decoupage",
            "digital-art", "enhance", "expressionistic", "fantasy-art", 
            "glitch-art", "graffiti", "hyperrealistic", "impressionistic",
            "isometric", "line-art", "low-poly", "minimalist", "modeling-compound",
            "neon-punk", "origami", "paper-cut", "photographic", "pixel-art", 
            "pop-art", "steampunk", "surreal", "tile-texture", "vaporwave",
            "watercolor",
        ]

        prompt_parts = [
            "\nPlease provide a detailed description, written in proper English, to recreate this image in 250 to 500 words. Include information about the style, mood, lighting, and other important details. Ensure your sentences are complete and free from spelling and grammar errors:",
            {"mime_type": "image/jpeg", "data": image_data},
            f"\nPlease select and use up to four different artistic styles from the following list: \n{', '.join(image_styles)}\nYou can choose the same style multiple times if desired.",
            "Try to make your description as similar as possible to the original image, just like an audio describer would. Remember to begin your description with the word 'imagine.' For example, 'imagine a red-hooded woman in the forest...'",
        ]

        generated_text = generate_content(prompt_parts)
        return render_template('prompts/generator/generator.html', result=generated_text)

    except Exception as e:
        return f"Error: {str(e)}"


# advance generator
@app.route('/advance')
@required_login
def advance():
    return render_template('prompts/generator/advance.html', result=None)


# advance generator / text prompt
@app.route('/advance/generate', methods=['POST'])
@required_login
def generate_advance_response():
    try:
        parameter0 = request.form['parameter0']
        parameter1 = request.form['parameter1']
        parameter2 = request.form['parameter2']
        parameter3 = request.form['parameter3']
        
        response_text = response(parameter0, parameter1, parameter2, parameter3)
        
        return render_template('prompts/generator/advance.html', result=response_text)
    except BadRequestKeyError as e:
        error_message = f"Bad Request: {e.description}"
        return render_template('prompts/generator/advance.html', result=error_message)


# advance generator / image prompt
@app.route('/advance/igenerate', methods=['POST'])
@required_login
def generate_advance_iresponse():
    try:
        parameter0 = request.form['parameter0']
        parameter1 = request.form['parameter1']
        parameter2 = request.form['parameter2']
        parameter3 = request.form['parameter3']
        
        response_text = iresponse(parameter0, parameter1, parameter2, parameter3)
        
        return render_template('prompts/generator/advance.html', result=response_text)
    except BadRequestKeyError as e:
        error_message = f"Bad Request: {e.description}"
        return render_template('prompts/generator/advance.html', result=error_message)


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

        prompt_parts = [
            "\nPlease provide a detailed description in proper English to recreate this image in 250 to 500 words. Include information about the style, mood, lighting, and other key details. Ensure your sentences are complete and free from spelling and grammar errors:",
            {"mime_type": "image/jpeg", "data": image_data},
            f"\nAdditionally, incorporate the '{parameter1}' mood into the image description.",
            f"\nFor the image style, please adopt the '{parameter2}' style as the main style, with '{parameter3}' serving as the secondary style.",
            "\nEnsure that your description is rich in detail and structure.",
            "\nTry to make your description as similar as possible to the original image with the adjustments I have requested, just like an audio describer would.",
            "\nRemember to begin your description with the word 'imagine.' For example, 'imagine a red-hooded woman in the forest...'",
        ]

        response_text = generate_content(prompt_parts)
        return render_template('prompts/generator/advance.html', result=response_text)

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


# general prompt library
@app.route('/library')
@required_login
def library():
    return render_template('prompts/library.html')


@app.route('/library/promptimpro')
@required_login
def promptinmpro():
    return render_template('prompts/global/prompt_improve.html')


@app.route('/library/adjust')
@required_login
def adjust():
    return render_template('prompts/global/adjustable_iq.html')


@app.route('/library/aerea')
@required_login
def aerea():
    return render_template('prompts/global/aerea.html')


@app.route('/library/ultimate')
@required_login
def ultimate():
    return render_template('prompts/global/ultimate_knowladge.html')


@app.route('/library/webdev')
@required_login
def webdev():
    return render_template('prompts/global/web_des.html')


@app.route('/library/mutation')
@required_login
def mutation():
    return render_template('prompts/global/mutation.html')


@app.route('/library/createch')
@required_login
def createch():
    return render_template('prompts/Writers_and_editors/CreaTech.html')


@app.route('/library/enhancement')
@required_login
def enhancement():
    return render_template('prompts/Writers_and_editors/enhancement.html')


@app.route('/library/journalist')
@required_login
def journalist():
    return render_template('prompts/Writers_and_editors/journalist.html')


@app.route('/library/paraphrase')
@required_login
def paraphrase():
    return render_template('prompts/Writers_and_editors/paraphrase.html')


@app.route('/library/emdev')
@required_login
def emdev():
    return render_template('prompts/coding_companion/emdev.html')


@app.route('/library/queria')
@required_login
def queria():
    return render_template('prompts/coding_companion/queria.html')


@app.route('/library/standard')
@required_login
def standard():
    return render_template('prompts/coding_companion/standard.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
