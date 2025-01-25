from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from werkzeug.exceptions import BadRequestKeyError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import get_db_connection, create_user_table_if_not_exists, save_prompt_to_db, delete_old_images
from chat_area import GeminiChat
from stability import ImageGen
from response2 import GenerativeAI
from response import GenerativeModel
import logging
import secrets
from datetime import datetime

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AI models
chat_app = GeminiChat()
image_generator = ImageGen()
ai = GenerativeAI()
model = GenerativeModel()

def create_main_blueprint(user_db, prompt_db, image_log, query_db, community_db, feedback_db):
    """Create and return the main Blueprint with database paths."""
    main_blueprint = Blueprint('main', __name__)

    # Store database paths in the Blueprint's context
    main_blueprint.user_db = user_db
    main_blueprint.prompt_db = prompt_db
    main_blueprint.image_log = image_log
    main_blueprint.query_db = query_db
    main_blueprint.community_db = community_db
    main_blueprint.feedback_db = feedback_db

    # Decorator for login required
    def required_login(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                return redirect(url_for('main.index'))
            return func(*args, **kwargs)
        return decorated_function

    @main_blueprint.route('/')
    def index():
        return render_template('login.html', error_message=None)

    @main_blueprint.route('/signup', methods=['POST'])
    def signup():
        honeypot_value = request.form.get('honeypot', '')
        if honeypot_value:
            return jsonify({'success': False, 'error': 'Bot activity detected. Access denied.'})

        username = request.form['username']
        password = request.form['password']

        with get_db_connection(main_blueprint.user_db) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': 'Username already exists. Please choose another.'})

            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()

        return jsonify({'success': True, 'redirect': url_for('main.home')}) 

    @main_blueprint.route('/login', methods=['POST'])
    def login():
        honeypot_value = request.form.get('honeypot', '')
        if honeypot_value:
            return jsonify({'success': False, 'error': 'Bot activity detected. Access denied.'})

        username = request.form['username']
        password = request.form['password']

        with get_db_connection(main_blueprint.user_db) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user[1], password):
            session['username'] = username
            return jsonify({'success': True, 'redirect': url_for('main.home')}) 

        return jsonify({'success': False, 'error': 'Invalid username or password. Please try again.'})

    @main_blueprint.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('main.index'))

    @main_blueprint.route('/home')
    @required_login
    def home():
        return render_template('index.html')

    @main_blueprint.route('/mylib')
    @required_login
    def mylib():
        username = session['username']
        table_name = username

        try:
            with get_db_connection(main_blueprint.prompt_db) as conn:
                cursor = conn.cursor()
                cursor.execute(f'SELECT random_val, title, prompt, time FROM {table_name}')
                saved_prompts = cursor.fetchall()
        except OperationalError:
            saved_prompts = None

        return render_template('prompts/lib/personal_library.html', saved_prompts=saved_prompts)

    @main_blueprint.route('/save_edit', methods=['POST'])
    @required_login
    def save_edit():
        username = session['username']
        table_name = username

        random_val = request.form['random_val']
        edited_title = request.form['edited_title']
        edited_prompt = request.form['edited_prompt']

        with get_db_connection(main_blueprint.prompt_db) as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE {table_name} SET title=?, prompt=? WHERE random_val=?', (edited_title, edited_prompt, random_val))
            conn.commit()

        return redirect(url_for('main.mylib'))

    @main_blueprint.route('/share_prompt', methods=['POST'])
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

        with get_db_connection(main_blueprint.community_db) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO shared (owner, random_val, title, prompt) VALUES (?, ?, ?, ?)', (owner, random_val, title, prompt))
            conn.commit()

        return jsonify({'success': True})

    @main_blueprint.route('/delete_prompt', methods=['POST'])
    @required_login
    def delete_prompt():
        prompt_id = request.form['prompt_id']
        username = session['username']

        with get_db_connection(main_blueprint.prompt_db) as conn:
            cursor = conn.cursor()
            cursor.execute(f'DELETE FROM {username} WHERE random_val = ?', (prompt_id,))
            conn.commit()

        return redirect(url_for('main.mylib'))

    @main_blueprint.route('/library')
    @required_login
    def library():
        try:
            with get_db_connection(main_blueprint.query_db) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT random_val, username, tittle, prompt, tag, time FROM community')
                system_prompts = cursor.fetchall()

            with get_db_connection(main_blueprint.community_db) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT owner, random_val, title, prompt, time FROM shared')
                shared_prompts = cursor.fetchall()

        except Exception as e:
            logger.error(f"Error fetching prompts: {e}")
            system_prompts, shared_prompts = [], []

        return render_template('prompts/lib/community_library.html', system_prompts=system_prompts, shared_prompts=shared_prompts)

    @main_blueprint.route('/trying')
    @required_login
    def trying():
        return render_template('try.html')

    @main_blueprint.route('/user_input', methods=['POST'])
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
                with get_db_connection(main_blueprint.image_log) as conn:
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

    @main_blueprint.route('/generate')
    @required_login
    def generate():
        return render_template('prompts/generator/basic.html')

    @main_blueprint.route('/generate/tprompt', methods=['POST'])
    @required_login
    def process():
        user_input = request.form['user_input']
        response_text = model.generate_response('./instruction/basic1.txt', user_input)
        return response_text

    @main_blueprint.route('/generate/trandom', methods=['POST'])
    @required_login
    def random_prompt():
        response_text = model.generate_random('./instruction/basic2.txt')
        return response_text

    @main_blueprint.route('/generate/iprompt', methods=['POST'])
    @required_login
    def vprocess():
        user_input = request.form['user_input']
        response_text = model.generate_imgdescription('./instruction/image_styles.txt', user_input)
        return response_text

    @main_blueprint.route('/generate/irandom', methods=['POST'])
    @required_login
    def vrandom_prompt():
        response_text = model.generate_vrandom('./instruction/image_styles.txt')
        return response_text

    @main_blueprint.route('/generate/image', methods=['POST'])
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

    @main_blueprint.route('/advance')
    @required_login
    def advance():
        return render_template('prompts/generator/advance.html')

    @main_blueprint.route('/advance/generate', methods=['POST'])
    @required_login
    def generate_advance_response():
        try:
            parameters = [request.form[f'parameter{i}'] for i in range(4)]
            response_text = ai.response(*parameters, './instruction/advance1.txt')
            return response_text
        except BadRequestKeyError as e:
            logger.error(f"Bad Request: {e}")
            return f"Bad Request: {e.description}"

    @main_blueprint.route('/advance/igenerate', methods=['POST'])
    @required_login
    def generate_advance_iresponse():
        try:
            parameters = [request.form[f'parameter{i}'] for i in range(4)]
            response_text = ai.response(*parameters, './instruction/advance2.txt')
            return response_text
        except BadRequestKeyError as e:
            logger.error(f"Bad Request: {e}")
            return f"Bad Request: {e.description}"

    @main_blueprint.route('/advance/image', methods=['POST'])
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

    @main_blueprint.route('/save_prompt', methods=['POST'])
    @required_login
    def save_prompt():
        try:
            title = request.form['title']
            prompt = request.form['prompt']
            username = session['username']

            # Create user table if it doesn't exist
            create_user_table_if_not_exists(username, main_blueprint.prompt_db)

            # Save the prompt
            random_value = save_prompt_to_db(username, title, prompt, main_blueprint.prompt_db)

            return 'Prompt saved successfully!'
        except Exception as e:
            logger.error(f"Error saving prompt: {e}")
            return f"Error: {str(e)}"

    @main_blueprint.route('/submit_feedback', methods=['POST'])
    @required_login
    def submit_feedback():
        username = session['username']
        feedback = request.form['feedback']

        with get_db_connection(main_blueprint.feedback_db) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO feedback (username, feedback) VALUES (?, ?)', (username, feedback))
            conn.commit()

        return jsonify({'status': 'success', 'message': 'Feedback submitted successfully!'})

    return main_blueprint