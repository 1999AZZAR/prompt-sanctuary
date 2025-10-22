from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash,
    Response,
    stream_template,
)

def check_api_key_required(user_db_path, username):
    """Check if user has a valid API key, return True if API key setup is required."""
    return not is_api_key_validated(user_db_path, username)
from utils import validate_csrf_token
from flask_babel import _, gettext
from werkzeug.exceptions import BadRequestKeyError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import sys
# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from models import (
    get_db_connection,
    create_user_table_if_not_exists,
    save_prompt_to_db,
    get_next_version_number,
    insert_prompt_version,
    create_session_record,
    touch_session,
    is_session_valid,
    revoke_session,
    list_sessions_for_user,
    revoke_other_sessions,
    update_user_email,
    get_user_email,
    change_username_everywhere,
    get_user_identicon_value,
    set_user_identicon_value,
    generate_identicon_value,
    get_prompt_sharing_status,
    get_user_api_key,
    set_user_api_key,
    is_api_key_validated,
    set_api_key_validated,
)

# LANGUAGES will be imported from app after initialization
LANGUAGES = None
from response2 import GenerativeAI
from response import GenerativeModel
from api_key_validator import validate_gemini_api_key
from api_key_pool import get_api_key_pool
import logging
import secrets
from datetime import datetime
import re

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AI models
ai = GenerativeAI()
model = GenerativeModel()


def sanitize_for_json(obj):
    """Sanitize data to ensure it's JSON serializable."""
    if obj is None:
        return ''
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    else:
        return str(obj) if obj is not None else ''

def create_main_blueprint(
    user_db, prompt_db, query_db, community_db, feedback_db
):
    """Create and return the main Blueprint with database paths."""
    main_blueprint = Blueprint("main", __name__)

    # Store database paths in the Blueprint's context
    main_blueprint.user_db = user_db
    main_blueprint.prompt_db = prompt_db
    main_blueprint.query_db = query_db
    main_blueprint.community_db = community_db
    main_blueprint.feedback_db = feedback_db

    # Decorator for login required
    def required_login(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if "username" not in session:
                return redirect(url_for("main.index"))
            # Optional session token validation if present
            token = session.get("session_token")
            if token and not is_session_valid(main_blueprint.user_db, token, session["username"]):
                session.clear()
                return redirect(url_for("main.index"))
            elif token:
                try:
                    touch_session(main_blueprint.user_db, token)
                except Exception:
                    logger.exception("Failed to touch session last_active")
            return func(*args, **kwargs)

        return decorated_function

    @main_blueprint.errorhandler(BadRequestKeyError)
    def handle_bad_request(e):
        """Handle missing form or JSON parameters in requests."""
        logger.error(f"Missing parameter: {e}")
        return jsonify({"success": False, "error": f"Missing parameter: {e}"}), 400

    @main_blueprint.errorhandler(404)
    def handle_404(e):
        """Handle 404 Not Found errors."""
        logger.error(f"404 Not Found: {e}")
        return jsonify({"success": False, "error": "Resource not found."}), 404

    @main_blueprint.errorhandler(500)
    def handle_500(e):
        """Handle 500 Internal Server Error."""
        logger.error(f"500 Internal Server Error: {e}")
        return jsonify({"success": False, "error": "Internal server error."}), 500

    def is_valid_username(name):
        """Check if the username contains only allowed characters (A-Za-z0-9_)."""
        return bool(re.match(r'^[A-Za-z0-9_]+$', name))

    @main_blueprint.route("/")
    def index():
        return render_template("landing.html")

    @main_blueprint.route("/signup", methods=["GET", "POST"])
    def signup():
        """Handle user signup. Validates input and creates a new user if valid."""
        if request.method == "GET":
            return render_template("login.html", show_signup=True)

        # Validate CSRF token
        if not validate_csrf_token():
            return jsonify({"success": False, "error": "CSRF token validation failed."}), 400

        honeypot_value = request.form.get("honeypot", "")
        if honeypot_value:
            return jsonify(
                {"success": False, "error": "Bot activity detected. Access denied."}
            )

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip() or None
        # Input validation
        if not username or not password:
            return jsonify({"success": False, "error": "Username and password are required."}), 400
        if len(username) < 3 or len(username) > 32:
            return jsonify({"success": False, "error": "Username must be between 3 and 32 characters."}), 400
        if len(password) < 6:
            return jsonify({"success": False, "error": "Password must be at least 6 characters."}), 400
        if not is_valid_username(username):
            return jsonify({"success": False, "error": "Invalid username format. Only letters, numbers, and underscores are allowed."}), 400
        if email and (len(email) > 254 or "@" not in email):
            return jsonify({"success": False, "error": "Invalid email address."}), 400

        try:
            with get_db_connection(main_blueprint.user_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    return jsonify({"success": False, "error": "Username already exists. Please choose another."}), 409
                if email:
                    cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
                    if cursor.fetchone():
                        return jsonify({"success": False, "error": "Email is already in use."}), 409

                hashed_password = generate_password_hash(password)
                cursor.execute("INSERT INTO users (username, password, email, gemini_api_key, api_key_validated) VALUES (?, ?, ?, '', 0)", (username, hashed_password, email))
                conn.commit()
                create_user_table_if_not_exists(username, main_blueprint.prompt_db)
        except Exception as e:
            logger.exception("Signup error")
            return jsonify({"success": False, "error": "Internal server error."}), 500

        # Automatically log in the user after successful signup
        session["username"] = username
        # Create a session token for optional session management and revocation
        token = secrets.token_urlsafe(24)
        session["session_token"] = token
        ua = request.headers.get("User-Agent")
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        # Prepare default response data
        response_data = {"success": True, "redirect": url_for("main.home")}

        try:
            create_session_record(main_blueprint.user_db, username, token, ua, ip)
        except Exception as e:
            logger.exception("Error creating session record")
            # Log the error but don't prevent signup if session record fails
            pass

        # Check if API key is required and redirect if not set
        if check_api_key_required(main_blueprint.user_db, username):
            response_data["redirect"] = url_for("main.api_key_setup")

        return jsonify(response_data)

    @main_blueprint.route("/login", methods=["GET", "POST"])
    def login():
        """Handle user login. Validates input and authenticates user."""
        if request.method == "GET":
            return render_template("login.html", show_signup=False)

        # Validate CSRF token
        if not validate_csrf_token():
            return jsonify({"success": False, "error": "CSRF token validation failed."}), 400

        honeypot_value = request.form.get("honeypot", "")
        if honeypot_value:
            return jsonify(
                {"success": False, "error": "Bot activity detected. Access denied."}
            )

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        # Input validation
        if not username or not password:
            return jsonify({"success": False, "error": "Username and password are required."}), 400
        if not is_valid_username(username):
            return jsonify({"success": False, "error": "Invalid username format. Only letters, numbers, and underscores are allowed."}), 400

        try:
            with get_db_connection(main_blueprint.user_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT username, password FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()
        except Exception as e:
            logger.exception("Login error")
            return jsonify({"success": False, "error": "Internal server error."}), 500

        if user and check_password_hash(user[1], password):
            session["username"] = username
            # Create a session token for optional session management and revocation
            token = secrets.token_urlsafe(24)
            session["session_token"] = token
            ua = request.headers.get("User-Agent")
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)

            # Prepare default response data
            response_data = {"success": True, "redirect": url_for("main.home")}

            try:
                create_session_record(main_blueprint.user_db, username, token, ua, ip)
                # Session created successfully (no point system)
            except Exception:
                logger.exception("Failed to create session record")

            return jsonify(response_data)

        return jsonify({"success": False, "error": "Invalid username or password. Please try again."}), 401

    @main_blueprint.route("/logout")
    def logout():
        username = session.get("username")
        token = session.get("session_token")
        if username and token:
            try:
                revoke_session(main_blueprint.user_db, token, username)
            except Exception:
                logger.exception("Failed to revoke session on logout")
        session.clear()
        return redirect(url_for("main.index"))

    @main_blueprint.route("/home")
    @required_login
    def home():
        return render_template("index.html")

    @main_blueprint.route("/mylib")
    @required_login
    def mylib():
        username = session["username"]
        create_user_table_if_not_exists(username, main_blueprint.prompt_db)

        table_name = f'"{username}"'
        try:
            cursor.execute(f"SELECT random_val, title, prompt, time FROM {table_name} ORDER BY time DESC")
            raw_saved_prompts = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching prompts: {e}")
            raw_saved_prompts = []

        conn.close()

        # Add sharing status to each saved prompt
        saved_prompts = []
        for prompt in raw_saved_prompts:
            prompt_id = prompt[0]
            title = prompt[1]
            content = prompt[2]
            time = prompt[3]

            sharing_status = get_prompt_sharing_status(
                username, prompt_id, title, content,
                main_blueprint.prompt_db, main_blueprint.community_db
            )

            enhanced_prompt = {
                'random_val': prompt_id,
                'title': title,
                'prompt': content,
                'time': time,
                'is_shared': sharing_status['is_shared'],
                'needs_update': sharing_status['needs_update']
            }
            saved_prompts.append(enhanced_prompt)

        return render_template("prompts/lib/personal.html", saved_prompts=saved_prompts, title="My Library")

    @main_blueprint.route("/save_edit", methods=["POST"])
    @required_login
    def save_edit():
        if request.method == "POST":
            prompt_id = request.form.get("random_val")
            edited_title = request.form.get("edited_title")
            edited_prompt = request.form.get("edited_prompt")
            username = session["username"]
            table_name = f'"{username}"'

            if not all([prompt_id, edited_title, edited_prompt]):
                return jsonify(success=False, message="Missing data for editing."), 400

            try:
                with get_db_connection(main_blueprint.prompt_db) as conn:
                    # Update the user's prompt table (table_name already quoted)
                    conn.execute(
                        f"UPDATE {table_name} SET title = ?, prompt = ? WHERE random_val = ?",
                        (edited_title, edited_prompt, prompt_id),
                    )
                    conn.commit()
                # Insert new version after edit
                version_number = get_next_version_number(username, prompt_id, main_blueprint.prompt_db)
                insert_prompt_version(username, prompt_id, version_number, edited_title, edited_prompt, main_blueprint.prompt_db)
                return jsonify(success=True, message="Prompt updated successfully!")
            except Exception as e:
                logger.error(f"Error updating prompt {prompt_id} for {username}: {e}")
                return jsonify(success=False, message="Failed to update prompt."), 500
        return jsonify(success=False, message="Invalid request method."), 405

    @main_blueprint.route("/versions/<prompt_id>", methods=["GET"])
    @required_login
    def list_versions(prompt_id):
        username = session["username"]
        with get_db_connection(main_blueprint.prompt_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT version_number, title, prompt, created_at
                FROM prompt_versions
                WHERE username = ? AND prompt_id = ?
                ORDER BY version_number DESC
                """,
                (username, prompt_id),
            )
            rows = cursor.fetchall()
        versions = [
            {
                "version_number": row[0],
                "title": row[1],
                "prompt": row[2],
                "created_at": row[3],
            }
            for row in rows
        ]
        return jsonify({"success": True, "versions": versions})

    @main_blueprint.route("/versions/rollback", methods=["POST"])
    @required_login
    def rollback_version():
        username = session["username"]
        prompt_id = request.form.get("prompt_id")
        version_number = request.form.get("version_number", type=int)
        if not prompt_id or version_number is None:
            return jsonify({"success": False, "error": "Missing prompt_id or version_number"}), 400
        try:
            with get_db_connection(main_blueprint.prompt_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT title, prompt FROM prompt_versions WHERE username = ? AND prompt_id = ? AND version_number = ?",
                    (username, prompt_id, version_number),
                )
                row = cursor.fetchone()
                if not row:
                    return jsonify({"success": False, "error": "Version not found"}), 404
                title, prompt_text = row[0], row[1]
                # Update the current record in user's table to match selected version
                cursor.execute(f'UPDATE "{username}" SET title = ?, prompt = ? WHERE random_val = ?', (title, prompt_text, prompt_id))
                conn.commit()
            # Record a new version snapshot for the rollback action
            new_version = get_next_version_number(username, prompt_id, main_blueprint.prompt_db)
            insert_prompt_version(username, prompt_id, new_version, title, prompt_text, main_blueprint.prompt_db)
            return jsonify({"success": True, "message": "Rolled back to selected version."})
        except Exception as e:
            logger.exception("Rollback error")
            return jsonify({"success": False, "error": "Internal server error."}), 500

    @main_blueprint.route("/share_prompt", methods=["POST"])
    @required_login
    def share_prompt():
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON payload."}), 400
        owner = session["username"]
        if not owner:
            return jsonify({"success": False, "error": "User not logged in"}), 401
        random_val = data.get("prompt_id")
        title = data.get("title")
        prompt_text = data.get("prompt")
        if not random_val or not title or not prompt_text:
            return jsonify({"success": False, "error": "Missing required data."}), 400
        try:
            with get_db_connection(main_blueprint.community_db) as conn:
                cursor = conn.cursor()
                # Check if prompt is already shared
                cursor.execute("SELECT title, prompt FROM shared WHERE owner=? AND random_val=?", (owner, random_val))
                existing = cursor.fetchone()

                if existing:
                    # Prompt is already shared, check if content changed
                    existing_title, existing_prompt = existing
                    if existing_title == title and existing_prompt == prompt_text:
                        # Same content, no need to update
                        return jsonify({"success": True, "message": "Prompt already shared."})
                    else:
                        # Content changed, update the shared prompt
                        cursor.execute(
                            "UPDATE shared SET title=?, prompt=? WHERE owner=? AND random_val=?",
                            (title, prompt_text, owner, random_val)
                        )
                        conn.commit()
                        return jsonify({"success": True, "message": "Shared prompt updated."})
                else:
                    # Prompt not shared yet, insert new record
                    cursor.execute(
                        "INSERT INTO shared (owner, random_val, title, prompt) VALUES (?, ?, ?, ?)",
                        (owner, random_val, title, prompt_text),
                    )
                    conn.commit()

            # Prompt shared successfully (no point system)
        except Exception as e:
            logger.exception("Error sharing prompt")
            return jsonify({"success": False, "error": "Internal server error."}), 500
        return jsonify({"success": True})

    @main_blueprint.route("/unshare_prompt", methods=["POST"])
    @required_login
    def unshare_prompt():
        data = request.get_json(silent=True)
        if not data or "prompt_id" not in data:
            return jsonify({"success": False, "error": "Missing prompt_id"}), 400
        owner = session.get("username")
        prompt_id = data.get("prompt_id")
        try:
            with get_db_connection(main_blueprint.community_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM shared WHERE owner=? AND random_val=?",
                    (owner, prompt_id),
                )
                conn.commit()

            # Prompt unshared successfully (no point system)
        except Exception as e:
            logger.exception("Error unsharing prompt")
            return jsonify({"success": False, "error": "Internal server error."}), 500
        return jsonify({"success": True, "message": "Prompt deleted successfully!"})

    @main_blueprint.route("/delete_prompt", methods=["POST"])
    @required_login
    def delete_prompt():
        prompt_id = request.form["prompt_id"]
        username = session["username"]

        with get_db_connection(main_blueprint.prompt_db) as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM \"{username}\" WHERE random_val = ?", (prompt_id,))
            conn.commit()

        return jsonify({"success": True, "message": "Prompt deleted successfully!"})

    @main_blueprint.route("/library")
    @required_login
    def library():
        username = session["username"]

        try:
            with get_db_connection(main_blueprint.query_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT random_val, username, tittle, prompt, tag, time FROM community"
                )
                raw_system_prompts = cursor.fetchall()

            with get_db_connection(main_blueprint.community_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT owner, random_val, title, prompt, time FROM shared"
                )
                raw_shared_prompts = cursor.fetchall()

        except Exception as e:
            logger.error(f"Error fetching prompts: {e}")
            raw_system_prompts, raw_shared_prompts = [], []

        # Convert system prompts to dictionary structure
        system_prompts = []
        for prompt in raw_system_prompts:
            system_prompts.append({
                'random_val': prompt[0] or '',
                'username': prompt[1] or '',
                'title': prompt[2] or '',  # Note: 'tittle' in DB but using 'title' in template
                'prompt': prompt[3] or '',
                'tag': prompt[4] or '',
                'time': prompt[5] or '',
                'is_shared': False,  # System prompts are not shared by users
                'type': 'system'
            })

        # Convert shared prompts to dictionary structure
        shared_prompts = []
        for prompt in raw_shared_prompts:
            owner = prompt[0] or ''
            prompt_id = prompt[1] or ''
            title = prompt[2] or ''
            content = prompt[3] or ''
            time = prompt[4] or ''

            # Check if current user owns this prompt
            is_user_owned = (owner == username)

            shared_prompts.append({
                'owner': owner,
                'random_val': prompt_id,
                'title': title,
                'prompt': content,
                'time': time,
                'is_shared': True,  # These are already shared
                'type': 'shared',
                'is_user_owned': is_user_owned
            })

        # Sanitize data to ensure JSON serialization works
        sanitized_system_prompts = sanitize_for_json(system_prompts)
        sanitized_shared_prompts = sanitize_for_json(shared_prompts)
        
        return render_template(
            "prompts/lib/community.html",
            system_prompts=sanitized_system_prompts,
            shared_prompts=sanitized_shared_prompts,
        )

    @main_blueprint.route("/profile", methods=["GET", "POST"])
    @required_login
    def profile():
        # Get messages from URL parameters (for redirects from other routes)
        error = request.args.get('error', None)
        success = request.args.get('success', None)
        
        # Override with POST form messages if this is a POST request
        if request.method == "POST":
            action = request.form.get("action", "")
            if action == "change_password":
                old_password = request.form.get("old_password", "")
                new_password = request.form.get("new_password", "")
                confirm_password = request.form.get("confirm_password", "")
                with get_db_connection(main_blueprint.user_db) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT password FROM users WHERE username = ?", (session["username"],)
                    )
                    user = cursor.fetchone()
                if not user or not check_password_hash(user[0], old_password):
                    error = "Old password is incorrect."
                elif new_password != confirm_password:
                    error = "New passwords do not match."
                elif len(new_password) < 6:
                    error = "New password must be at least 6 characters."
                else:
                    hashed = generate_password_hash(new_password)
                    with get_db_connection(main_blueprint.user_db) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE users SET password = ? WHERE username = ?",
                            (hashed, session["username"]),
                        )
                        conn.commit()
                    success = "Password updated successfully."
            elif action == "update_email":
                email = request.form.get("email", "").strip() or None
                if email and (len(email) > 254 or "@" not in email):
                    error = "Invalid email address."
                else:
                    try:
                        update_user_email(main_blueprint.user_db, session["username"], email)
                        success = "Email updated."
                    except Exception as e:
                        logger.exception("Email update error")
                        error = "Email already in use."
            elif action == "change_username":
                new_username = request.form.get("new_username", "").strip()
                if not new_username or not is_valid_username(new_username) or not (3 <= len(new_username) <= 32):
                    error = "Invalid username format."
                else:
                    try:
                        old_username = session["username"]
                        change_username_everywhere(
                            old_username,
                            new_username,
                            main_blueprint.user_db,
                            main_blueprint.prompt_db,
                            main_blueprint.community_db,
                            main_blueprint.feedback_db,
                        )
                        # Update session name and optionally revoke other sessions
                        session["username"] = new_username
                        token = session.get("session_token")
                        try:
                            revoke_other_sessions(main_blueprint.user_db, new_username, except_token=token)
                        except Exception:
                            logger.exception("Failed to revoke other sessions after username change")
                        success = "Username updated."
                    except ValueError as ve:
                        error = str(ve)
                    except Exception:
                        logger.exception("Username change error")
                        error = "Failed to change username."
        # Fetch recent user activity
        username = session["username"]
        # Ensure table exists to avoid 'no such table' after username change or first visit
        try:
            create_user_table_if_not_exists(username, main_blueprint.prompt_db)
        except Exception:
            logger.exception("Failed to ensure user table exists")
        with get_db_connection(main_blueprint.prompt_db) as conn:
            cursor = conn.cursor()
            # Fetch prompt ID, title, content, and timestamp for saved prompts
            cursor.execute(
                f'SELECT random_val AS prompt_id, title, prompt, time FROM "{username}" '
                'ORDER BY time DESC LIMIT 5'
            )
            raw_saved_prompts = cursor.fetchall()

        # Add sharing status to each saved prompt
        saved_prompts = []
        for prompt in raw_saved_prompts:
            prompt_id = prompt[0]
            title = prompt[1]
            content = prompt[2]
            time = prompt[3]

            sharing_status = get_prompt_sharing_status(
                username, prompt_id, title, content,
                main_blueprint.prompt_db, main_blueprint.community_db
            )

            # Create enhanced prompt object with sharing status
            enhanced_prompt = {
                'prompt_id': prompt_id,
                'title': title,
                'prompt': content,
                'time': time,
                'is_shared': sharing_status['is_shared'],
                'needs_update': sharing_status['needs_update']
            }
            saved_prompts.append(enhanced_prompt)
        with get_db_connection(main_blueprint.community_db) as conn:
            cursor = conn.cursor()
            # Fetch shared prompt ID, title, content, and timestamp
            cursor.execute(
                "SELECT random_val AS prompt_id, title, prompt, time FROM shared "
                "WHERE owner = ? ORDER BY time DESC LIMIT 5",
                (username,)
            )
            shared_prompts = cursor.fetchall()
        # List sessions
        try:
            sessions_list = list_sessions_for_user(main_blueprint.user_db, username)
        except Exception:
            logger.exception("Failed to list sessions")
            sessions_list = []
        # Email
        email_value = None
        try:
            email_value = get_user_email(main_blueprint.user_db, username)
        except Exception:
            logger.exception("Failed to get user email")

        # Identicon value
        identicon_value = None
        try:
            identicon_value = get_user_identicon_value(main_blueprint.user_db, username)
            # Generate identicon value if not exists
            if not identicon_value:
                identicon_value = generate_identicon_value(username)
                set_user_identicon_value(main_blueprint.user_db, username, identicon_value)
        except Exception:
            logger.exception("Failed to get or set user identicon value")

        # No point system - API key system only

        # No achievement system - API key system only

        # Get API key status
        api_key_status = {
            'has_api_key': False,
            'is_validated': False,
            'masked_key': None
        }
        try:
            user_api_key = get_user_api_key(main_blueprint.user_db, username)
            is_validated = is_api_key_validated(main_blueprint.user_db, username)
            api_key_status = {
                'has_api_key': bool(user_api_key),
                'is_validated': is_validated,
                'masked_key': f"***{user_api_key[-4:]}" if user_api_key else None
            }
        except Exception:
            logger.exception("Failed to get API key status")

        return render_template(
            "account/profile.html",
            error=error,
            success=success,
            saved_prompts=saved_prompts,
            shared_prompts=shared_prompts,
            sessions=sessions_list,
            email=email_value,
            current_token=session.get("session_token"),
            identicon_value=identicon_value,
            api_key_status=api_key_status,
        )

    @main_blueprint.route("/delete_account", methods=["POST"])
    @required_login
    def delete_account():
        username = session["username"]
        # delete user credentials
        with get_db_connection(main_blueprint.user_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM users WHERE username = ?", (username,)
            )
            conn.commit()
        # delete user sessions
        with get_db_connection(main_blueprint.user_db) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE username = ?", (username,))
            conn.commit()
        # drop user's prompt table
        with get_db_connection(main_blueprint.prompt_db) as conn:
            cursor = conn.cursor()
            cursor.execute(f'DROP TABLE IF EXISTS "{username}"')
            conn.commit()
        session.clear()
        return redirect(url_for("main.index"))

    @main_blueprint.route("/sessions/revoke", methods=["POST"])
    @required_login
    def revoke_a_session():
        token = request.form.get("token", "")
        if not token:
            return redirect(url_for('main.profile', error='Missing session token.'))
        
        ok = False
        try:
            ok = revoke_session(main_blueprint.user_db, token, session["username"])
        except Exception:
            logger.exception("Failed to revoke session")
        
        if not ok:
            return redirect(url_for('main.profile', error='Unable to revoke session.'))
        else:
            return redirect(url_for('main.profile', success='Session revoked successfully.'))

    @main_blueprint.route("/sessions/list", methods=["GET"])
    @required_login
    def list_my_sessions():
        try:
            return jsonify({"success": True, "sessions": list_sessions_for_user(main_blueprint.user_db, session["username"])})
        except Exception:
            logger.exception("Failed to list sessions")
            return jsonify({"success": False}), 500

    @main_blueprint.route("/api_key_setup")
    @required_login
    def api_key_setup():
        """API key setup page for users without valid API keys."""
        username = session["username"]
        is_validated = is_api_key_validated(main_blueprint.user_db, username)
        return render_template("api_key_setup.html", api_key_validated=is_validated)

    @main_blueprint.route("/generate")
    @required_login
    def generate():
        return render_template("prompts/generator/basic.html")

    @main_blueprint.route("/generate/tprompt", methods=["POST"])
    @required_login
    def process():
        """Generate a text prompt using user input. Validates input and returns model response."""
        user_input = request.form.get("user_input", "").strip()
        username = session["username"]
        cost = 1.5  # Basic prompt cost

        if not user_input:
            return jsonify({"success": False, "error": "Input cannot be empty."}), 400
        if len(user_input) > 500:
            return jsonify({"success": False, "error": "Input is too long (max 500 characters)."}), 400

        # Check if user has a validated API key
        if check_api_key_required(main_blueprint.user_db, username):
            return jsonify({
                "success": False, 
                "error": "API key required. Please set up your Gemini API key first.",
                "redirect": url_for("main.api_key_setup")
            }), 403

        try:
            # Set user API key
            user_api_key = get_user_api_key(main_blueprint.user_db, username)
            model.set_current_user(username)
            model.set_user_db_path(main_blueprint.user_db)
            model.set_user_api_key(user_api_key)
            
            response_text = model.generate_response("./instruction/basic1.txt", user_input, use_streaming=model.streaming_enabled)
            return response_text
        except Exception as e:
            logger.exception("Error generating prompt response")
            return f"Error: {str(e)}"

    @main_blueprint.route("/generate/tprompt/stream", methods=["POST"])
    @required_login
    def process_stream():
        """Generate a text prompt using streaming response."""
        user_input = request.form.get("user_input", "").strip()
        username = session["username"]
        cost = 1.5  # Basic prompt cost

        if not user_input:
            return jsonify({"success": False, "error": "Input cannot be empty."}), 400
        if len(user_input) > 500:
            return jsonify({"success": False, "error": "Input is too long (max 500 characters)."}), 400

        # Check if user has a validated API key
        if check_api_key_required(main_blueprint.user_db, username):
            return jsonify({
                "success": False, 
                "error": "API key required. Please set up your Gemini API key first.",
                "redirect": url_for("main.api_key_setup")
            }), 403

        try:
            # Set user API key
            user_api_key = get_user_api_key(main_blueprint.user_db, username)
            model.set_current_user(username)
            model.set_user_db_path(main_blueprint.user_db)
            model.set_user_api_key(user_api_key)
            
            def generate():
                try:
                    yield "data: \n\n"  # Start streaming
                    for chunk in model.generate_response_stream("./instruction/basic1.txt", user_input):
                        yield chunk
                    yield "data: [DONE]\n\n"  # End streaming
                except Exception as e:
                    logger.exception("Error in streaming response")
                    yield f"data: Error: {str(e)}\n\n"
            
            return Response(generate(), mimetype='text/plain')
        except Exception as e:
            logger.exception("Error setting up streaming response")
            return f"Error: {str(e)}"

    @main_blueprint.route("/generate/trandom", methods=["POST"])
    @required_login
    def random_prompt():
        username = session["username"]
        cost = 0.8  # Basic random prompt cost

        # Check if user has a validated API key
        if check_api_key_required(main_blueprint.user_db, username):
            return jsonify({
                "success": False, 
                "error": "API key required. Please set up your Gemini API key first.",
                "redirect": url_for("main.api_key_setup")
            }), 403

        try:
            # Set user API key
            user_api_key = get_user_api_key(main_blueprint.user_db, username)
            model.set_current_user(username)
            model.set_user_db_path(main_blueprint.user_db)
            model.set_user_api_key(user_api_key)
            
            response_text = model.generate_random("./instruction/basic2.txt", use_streaming=model.streaming_enabled)
            return response_text
        except Exception as e:
            logger.exception("Error generating random prompt")
            return f"Error: {str(e)}"

    @main_blueprint.route("/generate/iprompt", methods=["POST"])
    @required_login
    def vprocess():
        user_input = request.form["user_input"]
        username = session["username"]
        cost = 1.5  # Basic image prompt cost

        # Check if user has a validated API key
        if check_api_key_required(main_blueprint.user_db, username):
            return jsonify({
                "success": False, 
                "error": "API key required. Please set up your Gemini API key first.",
                "redirect": url_for("main.api_key_setup")
            }), 403

        try:
            # Set user API key
            user_api_key = get_user_api_key(main_blueprint.user_db, username)
            model.set_current_user(username)
            model.set_user_db_path(main_blueprint.user_db)
            model.set_user_api_key(user_api_key)
            
            response_text = model.generate_imgdescription(
                "./instruction/image_styles.txt", user_input, use_streaming=model.streaming_enabled
            )
            return response_text
        except Exception as e:
            logger.exception("Error generating image prompt")
            return f"Error: {str(e)}"

    @main_blueprint.route("/generate/irandom", methods=["POST"])
    @required_login
    def vrandom_prompt():
        username = session["username"]
        cost = 0.8  # Basic random image prompt cost

        # Check if user has a validated API key
        if check_api_key_required(main_blueprint.user_db, username):
            return jsonify({
                "success": False, 
                "error": "API key required. Please set up your Gemini API key first.",
                "redirect": url_for("main.api_key_setup")
            }), 403

        try:
            # Set user API key
            user_api_key = get_user_api_key(main_blueprint.user_db, username)
            model.set_current_user(username)
            model.set_user_db_path(main_blueprint.user_db)
            model.set_user_api_key(user_api_key)
            
            response_text = model.generate_vrandom("./instruction/image_styles.txt", use_streaming=model.streaming_enabled)
            return response_text
        except Exception as e:
            logger.exception("Error generating random image prompt")
            return f"Error: {str(e)}"

    @main_blueprint.route("/generate/image", methods=["POST"])
    @required_login
    def reverse_image():
        try:
            username = session["username"]
            cost = 2.0  # Basic reverse image prompt cost

            # Check if user has a validated API key
            user_has_api_key = is_api_key_validated(main_blueprint.user_db, username)
            
            # API key system - no point deduction needed

            # Set user API key if available
            user_api_key = get_user_api_key(main_blueprint.user_db, username)
            model.set_current_user(username)
            model.set_user_db_path(main_blueprint.user_db)
            if user_api_key:
                model.set_user_api_key(user_api_key)
            else:
                model.clear_user_api_key()

            image_file = request.files["image"]
            image_data = image_file.read()
            response_text = model.generate_visual(
                "./instruction/image_styles.txt", image_data, use_streaming=model.streaming_enabled
            )
            return response_text
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return f"Error: {str(e)}"

    @main_blueprint.route("/advance")
    @required_login
    def advance():
        return render_template("prompts/generator/advance.html")

    @main_blueprint.route("/advance/generate", methods=["POST"])
    @required_login
    def generate_advance_response():
        try:
            username = session["username"]
            # Advanced prompt cost varies based on prompt type (1.7-2.1)
            # For now, use a fixed cost of 1.9
            cost = 1.9

            # Check if user has a validated API key
            user_has_api_key = is_api_key_validated(main_blueprint.user_db, username)
            
            # API key system - no point deduction needed

            parameters = [request.form[f"parameter{i}"] for i in range(4)]
            response_text = ai.response(*parameters, "./instruction/advance1.txt")
            return response_text
        except BadRequestKeyError as e:
            logger.error(f"Bad Request: {e}")
            return f"Bad Request: {e.description}"

    @main_blueprint.route("/advance/igenerate", methods=["POST"])
    @required_login
    def generate_advance_iresponse():
        try:
            username = session["username"]
            # Advanced image prompt cost varies (1.8-2.0)
            # For now, use a fixed cost of 1.9
            cost = 1.9

            # Check if user has a validated API key
            user_has_api_key = is_api_key_validated(main_blueprint.user_db, username)
            
            # API key system - no point deduction needed

            parameters = [request.form[f"parameter{i}"] for i in range(4)]
            response_text = ai.response(*parameters, "./instruction/advance2.txt")
            return response_text
        except BadRequestKeyError as e:
            logger.error(f"Bad Request: {e}")
            return f"Bad Request: {e.description}"

    @main_blueprint.route("/advance/image", methods=["POST"])
    @required_login
    def advance_image():
        try:
            username = session["username"]
            cost = 2.5  # Advanced reverse image prompt cost

            # Check if user has a validated API key
            user_has_api_key = is_api_key_validated(main_blueprint.user_db, username)
            
            # API key system - no point deduction needed

            # Set user API key if available
            user_api_key = get_user_api_key(main_blueprint.user_db, username)
            model.set_current_user(username)
            model.set_user_db_path(main_blueprint.user_db)
            if user_api_key:
                model.set_user_api_key(user_api_key)
            else:
                model.clear_user_api_key()

            image_file = request.files["image"]
            image_data = image_file.read()
            parameters = [request.form[f"parameter{i}"] for i in range(1, 4)]
            response_text = model.generate_visual2(image_data, *parameters, use_streaming=model.streaming_enabled)
            return response_text
        except Exception as e:
            logger.error(f"Error processing advance image: {e}")
            return f"Error: {str(e)}"

    @main_blueprint.route("/health/keys", methods=["GET"])
    @required_login
    def key_health():
        try:
            return jsonify({"success": True, **model.get_health()})
        except Exception as e:
            logger.exception("Health endpoint error")
            return jsonify({"success": False, "error": "Internal server error."}), 500

    @main_blueprint.route("/save_prompt", methods=["POST"])
    @required_login
    def save_prompt():
        if request.method == "POST":
            title = request.form.get("title")
            prompt_text = request.form.get("prompt")
            username = session["username"]

            if not title or not prompt_text:
                return jsonify(success=False, message="Title and prompt cannot be empty."), 400

            try:
                create_user_table_if_not_exists(username, main_blueprint.prompt_db)

                random_val = secrets.token_urlsafe(8) 
                if save_prompt_to_db(username, random_val, title, prompt_text, main_blueprint.prompt_db):
                    # Initial version = 1
                    insert_prompt_version(username, random_val, 1, title, prompt_text, main_blueprint.prompt_db)
                    return jsonify(success=True, message="Prompt saved successfully!")
                else:
                    return jsonify(success=False, message="Failed to save prompt."), 500
            except ValueError as e: 
                return jsonify(success=False, message=str(e)), 400
            except Exception as e:
                logger.error(f"Error saving prompt for {username}: {e}")
                return jsonify(success=False, message="An internal error occurred."), 500
        return jsonify(success=False, message="Invalid request method."), 405

    @main_blueprint.route("/submit_feedback", methods=["POST"])
    @required_login
    def submit_feedback():
        # Validate CSRF token
        if not validate_csrf_token():
            return jsonify({"success": False, "error": "CSRF token validation failed."}), 400

        username = session["username"]
        feedback = request.form["feedback"]

        with get_db_connection(main_blueprint.feedback_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO feedback (username, feedback) VALUES (?, ?)",
                (username, feedback),
            )
            conn.commit()

        return jsonify(
            {"status": "success", "message": "Feedback submitted successfully!"}
        )

    # Additional CRUD endpoints for feedback
    @main_blueprint.route("/feedback", methods=["GET"])
    @required_login
    def feedback_list():
        with get_db_connection(main_blueprint.feedback_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, feedback FROM feedback ORDER BY id DESC")
            feedbacks = cursor.fetchall()
        return render_template("feedback_list.html", feedbacks=feedbacks)

    @main_blueprint.route("/feedback/<int:feedback_id>", methods=["PUT"])
    @required_login
    def update_feedback(feedback_id):
        feedback = request.json.get("feedback")
        with get_db_connection(main_blueprint.feedback_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE feedback SET feedback = ? WHERE id = ?", (feedback, feedback_id)
            )
            conn.commit()
        return jsonify(
            {"status": "success", "message": "Feedback updated successfully!"}
        )

    @main_blueprint.route("/feedback/<int:feedback_id>", methods=["DELETE"])
    @required_login
    def delete_feedback(feedback_id):
        with get_db_connection(main_blueprint.feedback_db) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
            conn.commit()
        return jsonify(
            {"status": "success", "message": "Feedback deleted successfully!"}
        )

    @main_blueprint.route("/feedback/<int:feedback_id>/json", methods=["GET"])
    @required_login
    def get_feedback_json(feedback_id):
        with get_db_connection(main_blueprint.feedback_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, feedback FROM feedback WHERE id = ?", (feedback_id,))
            row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "error": "Feedback not found"}), 404
        return jsonify({"id": feedback_id, "username": row[0], "feedback": row[1]})


    @main_blueprint.route("/api_key/validate", methods=["POST"])
    @required_login
    def validate_api_key():
        """Validate and store user's Gemini API key."""
        if not validate_csrf_token():
            return jsonify({"success": False, "error": "CSRF token validation failed."}), 400
        
        username = session["username"]
        api_key = request.form.get("api_key", "").strip()
        
        if not api_key:
            return jsonify({"success": False, "error": "API key is required."}), 400
        
        try:
            # Validate the API key
            is_valid, message = validate_gemini_api_key(api_key)
            
            if not is_valid:
                return jsonify({"success": False, "error": message}), 400
            
            # Store the API key
            set_user_api_key(main_blueprint.user_db, username, api_key)
            
            # Check if this is the first time validating an API key
            was_validated = is_api_key_validated(main_blueprint.user_db, username)
            if not was_validated:
                # Mark as validated
                set_api_key_validated(main_blueprint.user_db, username, True)
                
                # API key validated successfully (no point system)
                
                response_data = {
                    "success": True, 
                    "message": "API key validated successfully!"
                }
            else:
                response_data = {
                    "success": True, 
                    "message": "API key updated successfully!"
                }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.exception("Error validating API key")
            return jsonify({"success": False, "error": "Internal server error."}), 500

    @main_blueprint.route("/api_key/test", methods=["POST"])
    @required_login
    def test_api_key():
        """Test user's Gemini API key without saving it."""
        if not validate_csrf_token():
            return jsonify({"success": False, "error": "CSRF token validation failed."}), 400
        
        api_key = request.form.get("api_key", "").strip()
        
        if not api_key:
            return jsonify({"success": False, "error": "API key is required."}), 400
        
        try:
            # Test the API key
            is_valid, message = validate_gemini_api_key(api_key)
            
            if not is_valid:
                return jsonify({"success": False, "error": message}), 400
            
            # Get additional info about the API key
            from api_key_validator import get_api_key_info
            info = get_api_key_info(api_key)
            
            return jsonify({
                "success": True, 
                "info": {
                    "is_valid": True,
                    "has_quota": info.get("has_quota", False),
                    "model_available": info.get("model_available", False),
                    "error_message": None
                }
            })
            
        except Exception as e:
            logger.exception("Error testing API key")
            return jsonify({"success": False, "error": "Internal server error."}), 500

    @main_blueprint.route("/api_key/remove", methods=["POST"])
    @required_login
    def remove_api_key():
        """Remove user's Gemini API key."""
        if not validate_csrf_token():
            return jsonify({"success": False, "error": "CSRF token validation failed."}), 400
        
        username = session["username"]
        
        try:
            # API key removal (no point system)
            
            # Clear the API key and validation status
            set_user_api_key(main_blueprint.user_db, username, "")
            set_api_key_validated(main_blueprint.user_db, username, False)
            
            return jsonify({"success": True, "message": "API key removed successfully."})
            
        except Exception as e:
            logger.exception("Error removing API key")
            return jsonify({"success": False, "error": "Internal server error."}), 500

    @main_blueprint.route("/api_key/status")
    @required_login
    def api_key_status():
        """Get user's API key status."""
        username = session["username"]
        
        try:
            api_key = get_user_api_key(main_blueprint.user_db, username)
            is_validated = is_api_key_validated(main_blueprint.user_db, username)
            
            return jsonify({
                "success": True, 
                "has_api_key": bool(api_key),
                "is_validated": is_validated,
                "masked_key": f"***{api_key[-4:]}" if api_key else None
            })
            
        except Exception as e:
            logger.exception("Error getting API key status")
            return jsonify({"success": False, "error": "Internal server error."}), 500


    @main_blueprint.route("/api_key/pool_stats")
    @required_login
    def api_key_pool_stats():
        """Get API key pool statistics for system administrators."""
        username = session["username"]
        
        try:
            # Get user's own API key stats
            pool = get_api_key_pool(main_blueprint.user_db)
            user_stats = pool.get_user_stats(username)
            pool_stats = pool.get_pool_stats()
            
            return jsonify({
                "success": True,
                "user_stats": user_stats,
                "pool_stats": pool_stats
            })
            
        except Exception as e:
            logger.exception("Error getting API key pool stats")
            return jsonify({"success": False, "error": "Internal server error."}), 500

    @main_blueprint.route("/refine_prompt", methods=["POST"])
    @required_login
    def refine_prompt():
        """Refine a prompt using AI with various actions and custom instructions."""
        if not validate_csrf_token():
            return jsonify({"success": False, "error": "CSRF token validation failed."}), 400
        
        username = session["username"]
        text = request.form.get("prompt_text", "").strip()
        action = request.form.get("action", "").strip().lower()
        custom_instructions = request.form.get("custom_instructions", "").strip()
        
        if not text:
            return jsonify({"success": False, "error": "No prompt text provided."}), 400
        
        # Validate action or custom instructions
        if not action and not custom_instructions:
            return jsonify({"success": False, "error": "Please provide either an action or custom instructions."}), 400
        
        if action and action not in ["shorten", "elaborate", "improve", "fix", "custom"]:
            return jsonify({"success": False, "error": "Invalid action. Use 'shorten', 'elaborate', 'improve', 'fix', or 'custom'."}), 400
        
        # Check if user has a validated API key
        user_has_api_key = is_api_key_validated(main_blueprint.user_db, username)
        
        # API key system - no point deduction needed
        
        try:
            # Set user API key if available
            user_api_key = get_user_api_key(main_blueprint.user_db, username)
            model.set_current_user(username)
            model.set_user_db_path(main_blueprint.user_db)
            if user_api_key:
                model.set_user_api_key(user_api_key)
            else:
                model.clear_user_api_key()
            
            # Generate refinement prompt based on action or custom instructions
            if custom_instructions:
                refinement_prompt = f"""Please refine the following text according to these specific instructions: "{custom_instructions}"

Original text:
"{text}"

Provide only the refined version, no explanations."""
            else:
                if action == "shorten":
                    refinement_prompt = f"""Please shorten the following text while keeping the essential meaning and key information. Make it more concise and to the point:

"{text}"

Provide only the shortened version, no explanations."""
                elif action == "elaborate":
                    refinement_prompt = f"""Please elaborate on the following text by adding more details, context, and specificity while maintaining the core meaning:

"{text}"

Provide only the elaborated version, no explanations."""
                elif action == "improve":
                    refinement_prompt = f"""Please improve the following text to make it clearer, more effective, and better structured while maintaining its core meaning:

"{text}"

Provide only the improved version, no explanations."""
                elif action == "fix":
                    refinement_prompt = f"""Please fix any grammar, spelling, and language issues in the following text while maintaining its meaning and style:

"{text}"

Provide only the corrected version, no explanations."""
            
            # Use the AI model to refine the prompt
            refined_text = model._generate_content_with_retry(refinement_prompt, model.get_effective_api_key(), use_streaming=False)
            
            if refined_text and refined_text.strip():
                return jsonify({"success": True, "response": refined_text.strip()})
            else:
                return jsonify({"success": False, "error": "Failed to refine prompt."}), 500
                
        except Exception as e:
            logger.exception("Error refining prompt")
            return jsonify({"success": False, "error": f"Error refining prompt: {str(e)}"}), 500

    @main_blueprint.route("/debug/refinement")
    @required_login
    def debug_refinement():
        """Debug route to test database connections for refinement."""
        username = session["username"]
        
        debug_info = {
            'username': username,
            'prompt_db_path': main_blueprint.prompt_db,
            'community_db_path': main_blueprint.community_db,
            'prompt_db_exists': os.path.exists(main_blueprint.prompt_db),
            'community_db_exists': os.path.exists(main_blueprint.community_db),
            'saved_prompts_count': 0,
            'community_prompts_count': 0,
            'saved_prompts': [],
            'community_prompts': [],
            'errors': []
        }
        
        try:
            # Test user's saved prompts
            with get_db_connection(main_blueprint.prompt_db) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM \"{username}\" ORDER BY time DESC LIMIT 50")
                saved_rows = cursor.fetchall()
                debug_info['saved_prompts_count'] = len(saved_rows)
                
                for row in saved_rows:
                    debug_info['saved_prompts'].append({
                        'prompt_id': row['random_val'],
                        'title': row['title'],
                        'prompt': row['prompt'][:100] + '...' if len(row['prompt']) > 100 else row['prompt'],
                        'time': row['time'],
                        'source': 'personal'
                    })
        except Exception as e:
            debug_info['errors'].append(f"Saved prompts error: {str(e)}")

        try:
            # Test community prompts
            with get_db_connection(main_blueprint.community_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM shared ORDER BY time DESC LIMIT 50")
                community_rows = cursor.fetchall()
                debug_info['community_prompts_count'] = len(community_rows)
                
                for row in community_rows:
                    debug_info['community_prompts'].append({
                        'prompt_id': row['random_val'],
                        'title': row['title'],
                        'prompt': row['prompt'][:100] + '...' if len(row['prompt']) > 100 else row['prompt'],
                        'time': row['time'],
                        'owner': row['owner'],
                        'source': 'community'
                    })
        except Exception as e:
            debug_info['errors'].append(f"Community prompts error: {str(e)}")

        return jsonify(debug_info)

    @main_blueprint.route("/refinement")
    @required_login
    def refinement():
        """Prompt refinement page - allows users to refine existing prompts."""
        username = session["username"]
        try:
            # Get user's saved prompts
            saved_prompts = []
            logger.info(f"Loading saved prompts for user: {username}")
            logger.info(f"Prompt database path: {main_blueprint.prompt_db}")
            
            with get_db_connection(main_blueprint.prompt_db) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM \"{username}\" ORDER BY time DESC LIMIT 50")
                saved_rows = cursor.fetchall()
                logger.info(f"Found {len(saved_rows)} saved prompts for user {username}")
                
                for row in saved_rows:
                    saved_prompts.append({
                        'prompt_id': row['random_val'],
                        'title': row['title'],
                        'prompt': row['prompt'],
                        'time': row['time'],
                        'source': 'personal'
                    })

            # Get community prompts
            community_prompts = []
            logger.info(f"Loading community prompts")
            logger.info(f"Community database path: {main_blueprint.community_db}")
            
            with get_db_connection(main_blueprint.community_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM shared ORDER BY time DESC LIMIT 50")
                community_rows = cursor.fetchall()
                logger.info(f"Found {len(community_rows)} community prompts")
                
                for row in community_rows:
                    community_prompts.append({
                        'prompt_id': row['random_val'] or '',
                        'title': row['title'] or '',
                        'prompt': row['prompt'] or '',
                        'time': row['time'] or '',
                        'owner': row['owner'] or '',
                        'source': 'community'
                    })

        except Exception as e:
            logger.exception("Failed to load prompts for refinement")
            logger.error(f"Error details: {str(e)}")
            saved_prompts = []
            community_prompts = []

        # Sanitize data to ensure JSON serialization works
        sanitized_saved_prompts = sanitize_for_json(saved_prompts)
        sanitized_community_prompts = sanitize_for_json(community_prompts)
        
        return render_template(
            "prompts/generator/refinement.html",
            saved_prompts=sanitized_saved_prompts,
            community_prompts=sanitized_community_prompts,
            # No point system - API key system only
        )

    @main_blueprint.route("/generate_title", methods=["POST"])
    @required_login
    def generate_title():
        """Generate a smart title for a prompt using AI."""
        if request.method == "POST":
            prompt_text = request.form.get("prompt_text", "").strip()
            prompt_type = request.form.get("prompt_type", "basic").strip()
            username = session["username"]

            if not prompt_text:
                return jsonify({"success": False, "error": "Prompt text is required."}), 400

            try:
                # API key system - no point deduction needed
                cost = 0.2
                user_has_api_key = is_api_key_validated(main_blueprint.user_db, username)
                
                # API key system - no point deduction needed

                # Create title generation prompt based on type
                title_prompts = {
                    'basic': "Generate a concise, descriptive title (3-8 words) for this basic prompt. Focus on the main purpose or topic:",
                    'advanced': "Generate a concise, descriptive title (3-8 words) for this advanced prompt. Focus on the main purpose or topic:",
                    'advanced_image': "Generate a concise, descriptive title (3-8 words) for this image generation prompt. Focus on the visual content or style:",
                    'advanced_reverse': "Generate a concise, descriptive title (3-8 words) for this reverse image prompt. Focus on the analysis or description:",
                    'refinement': "Generate a concise, descriptive title (3-8 words) for this refined prompt. Focus on the improvement or enhancement:"
                }
                
                title_prompt = title_prompts.get(prompt_type, title_prompts['basic'])
                full_prompt = f"{title_prompt}\n\nPrompt content:\n{prompt_text}\n\nTitle:"

                # Set user API key if available
                user_api_key = get_user_api_key(main_blueprint.user_db, username)
                if user_api_key:
                    model.set_user_api_key(user_api_key)

                # Generate title using AI
                title = model._generate_content_with_retry(full_prompt, model.get_effective_api_key(), use_streaming=False)
                
                if title and title.strip():
                    # Clean up the title
                    clean_title = title.strip()
                    # Remove quotes if present
                    clean_title = clean_title.strip('"\'')
                    # Ensure it's not too long
                    if len(clean_title) > 60:
                        clean_title = clean_title[:57] + "..."
                    
                    return jsonify({"success": True, "title": clean_title})
                else:
                    return jsonify({"success": False, "error": "Failed to generate title."}), 500

            except Exception as e:
                logger.error(f"Error generating title for {username}: {e}")
                return jsonify({"success": False, "error": "Failed to generate title."}), 500

        return jsonify({"success": False, "error": "Invalid request method."}), 405

    @main_blueprint.route("/language/<language>")
    def set_language(language):
        """Set user language preference"""
        if language not in LANGUAGES:
            flash(_("Language not supported"), "error")
            return redirect(request.referrer or url_for('main.home'))

        session['language'] = language
        flash(_("Language changed to %(language)s", language=LANGUAGES[language]), "success")
        return redirect(request.referrer or url_for('main.home'))

    @main_blueprint.route("/src/main.tsx")
    def handle_missing_main_tsx():
        """Handle requests for missing main.tsx file - return 404 with proper headers"""
        return "File not found", 404, {'Content-Type': 'text/plain'}

    @main_blueprint.route("/src/<path:filename>")
    def handle_missing_src_files(filename):
        """Handle requests for missing files in src/ directory - return 404 with proper headers"""
        return "File not found", 404, {'Content-Type': 'text/plain'}

    return main_blueprint
