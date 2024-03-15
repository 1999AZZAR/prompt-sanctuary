# app.py
import secrets
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from gemini_text import generate_response, generate_random, generate_vrandom, generate_imgdescription
from gemini_vis import generate_content
from advance import response, iresponse
from werkzeug.exceptions import BadRequestKeyError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlite3 import OperationalError
import sqlite3
from response import GeminiChat
from stability import Image_gen


app = Flask(__name__)
USER_DATABASE = './web/database/user.db'
PROMPT_DATABASE = './web/database/prompt_data.db'
chat_app = None 
image_generator = Image_gen() 

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
app.secret_key = 'hahahaha' 

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

def required_login(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('login.html')

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
    user_input = request.get_json().get('user_input', '')
    if user_input.startswith('imagine'):
        prompt = user_input[len('imagine'):].strip()
        prompt_text = prompt if prompt else 'Your prompt here'
        image_path = image_generator.generate_image(prompt_text)
        if image_path:
            return jsonify({'image_path': image_path})
        else:
            return jsonify({'bot_response': 'Error generating image'})
    else:
        response = chat_app.generate_chat(user_input)
        return jsonify({'bot_response': response})

@app.route('/generate')
@required_login
def generate():
    return render_template('prompts/generator/generator.html', result=None)

@app.route('/generate/tprompt', methods=['POST'])
@required_login
def process():
    user_input = request.form['user_input']
    response_text = generate_response(user_input)
    return render_template('prompts/generator/generator.html', result=response_text)

@app.route('/generate/trandom', methods=['POST'])
@required_login
def random_prompt():
    response_text = generate_random()
    return render_template('prompts/generator/generator.html', result=response_text)

@app.route('/generate/iprompt', methods=['POST'])
@required_login
def vprocess():
    user_input = request.form['user_input']
    response_text = generate_imgdescription(user_input)
    return render_template('prompts/generator/generator.html', result=response_text)

@app.route('/generate/irandom', methods=['POST'])
@required_login
def vrandom_prompt():
    response_text = generate_vrandom()
    return render_template('prompts/generator/generator.html', result=response_text)

@app.route('/reverse')
@required_login
def reverse():
    return render_template('prompts/generator/reverse.html', result=None)

@app.route('/generate/image', methods=['POST'])
@required_login
def reverse_image():
    try:
        image_file = request.files['image']
        image_data = image_file.read()

        prompt_parts = [
            "\nPlease write a detailed description in proper English to recreate this image in 120 to 340 word. Include the style, mood, lighting, and other key details. Use complete sentences and proofread for spelling and grammar mistakes:",
            {"mime_type": "image/jpeg", "data": image_data},
            "\nAlso select the main artistic style from this list (you can choose more than one): \n",
            "1. Photographic\n2. Enhanced\n3. Anime\n4. Digital art\n5. Comic book\n6. Fantasy art\n",  
            "7. Line art\n8. Analog film\n9. Neon punk\n10. Isometric\n11. Low poly\n12. Origami\n",
            "13. Modeling compound\n14. Cinematic\n15. 3D model\n16. Pixel art\n17. Tile texture\n"
        ]

        generated_text = generate_content(prompt_parts)
        return render_template('prompts/generator/generator.html', result=generated_text)

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/advance')
@required_login
def advance():
    return render_template('prompts/generator/advance.html', result=None)

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
            "\nPlease write a detailed description in proper English to recreate this image in 250 to 500 word. Include the style, mood, lighting, and other key details. Use complete sentences and proofread for spelling and grammar mistakes:",
            {"mime_type": "image/jpeg", "data": image_data},
            f"\naslo use this {parameter1} mood for the image description",
            f"\nand for the image style please use the {parameter2} style for the main style also the {parameter3} as the secondary style.",
            f"\ndon't forget to make it as details and structural as possible"
        ]

        response_text = generate_content(prompt_parts)
        return render_template('prompts/generator/advance.html', result=response_text)

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/advance/save', methods=['POST'])
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
    chat_app = GeminiChat()  # Initialize chat_app here
    app.run(host="0.0.0.0", port=5000, debug=True)
