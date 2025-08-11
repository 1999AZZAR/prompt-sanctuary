from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
)
from werkzeug.exceptions import BadRequestKeyError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import (
    get_db_connection,
    create_user_table_if_not_exists,
    save_prompt_to_db,
    get_next_version_number,
    insert_prompt_version,
)
from response2 import GenerativeAI
from response import GenerativeModel
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
        if len(username) < 3 or len(username) > 32:
            return jsonify({"success": False, "error": "Username must be between 3 and 32 characters."}), 400
        if len(password) < 6:
            return jsonify({"success": False, "error": "Password must be at least 6 characters."}), 400
        if not is_valid_username(username):
            return jsonify({"success": False, "error": "Invalid username format. Only letters, numbers, and underscores are allowed."}), 400

        try:
            with get_db_connection(main_blueprint.user_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    return jsonify({"success": False, "error": "Username already exists. Please choose another."}), 409

                hashed_password = generate_password_hash(password)
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
                create_user_table_if_not_exists(username, main_blueprint.prompt_db)
        except Exception as e:
            logger.exception("Signup error")
            return jsonify({"success": False, "error": "Internal server error."}), 500

        return jsonify({"success": True, "redirect": url_for("main.home")})

    @main_blueprint.route("/login", methods=["GET", "POST"])
    def login():
        """Handle user login. Validates input and authenticates user."""
        if request.method == "GET":
            return render_template("login.html", show_signup=False)
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
            return jsonify({"success": True, "redirect": url_for("main.home")})

        return jsonify({"success": False, "error": "Invalid username or password. Please try again."}), 401

    @main_blueprint.route("/logout")
    def logout():
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
        conn = get_db_connection(main_blueprint.prompt_db)
        cursor = conn.cursor()

        create_user_table_if_not_exists(username, main_blueprint.prompt_db)

        table_name = f'"{username}"'
        try:
            cursor.execute(f"SELECT random_val, title, prompt, time FROM {table_name} ORDER BY time DESC")
            saved_prompts = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching prompts: {e}")
            saved_prompts = []

        conn.close()
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
                # Prevent duplicate share (same user, same prompt)
                cursor.execute("SELECT 1 FROM shared WHERE owner=? AND random_val=?", (owner, random_val))
                if cursor.fetchone():
                    return jsonify({"success": False, "error": "Prompt already shared."}), 409
                cursor.execute(
                    "INSERT INTO shared (owner, random_val, title, prompt) VALUES (?, ?, ?, ?)",
                    (owner, random_val, title, prompt_text),
                )
                conn.commit()
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
        try:
            with get_db_connection(main_blueprint.query_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT random_val, username, tittle, prompt, tag, time FROM community"
                )
                system_prompts = cursor.fetchall()

            with get_db_connection(main_blueprint.community_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT owner, random_val, title, prompt, time FROM shared"
                )
                shared_prompts = cursor.fetchall()

        except Exception as e:
            logger.error(f"Error fetching prompts: {e}")
            system_prompts, shared_prompts = [], []

        return render_template(
            "prompts/lib/community.html",
            system_prompts=system_prompts,
            shared_prompts=shared_prompts,
        )

    @main_blueprint.route("/profile", methods=["GET", "POST"])
    @required_login
    def profile():
        error = None
        success = None
        if request.method == "POST":
            old_password = request.form["old_password"]
            new_password = request.form["new_password"]
            confirm_password = request.form["confirm_password"]
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
        # Fetch recent user activity
        username = session["username"]
        with get_db_connection(main_blueprint.prompt_db) as conn:
            cursor = conn.cursor()
            # Fetch prompt ID, title, content, and timestamp for saved prompts
            cursor.execute(
                f'SELECT random_val AS prompt_id, title, prompt, time FROM "{username}" '
                'ORDER BY time DESC LIMIT 5'
            )
            saved_prompts = cursor.fetchall()
        with get_db_connection(main_blueprint.community_db) as conn:
            cursor = conn.cursor()
            # Fetch shared prompt ID, title, content, and timestamp
            cursor.execute(
                "SELECT random_val AS prompt_id, title, prompt, time FROM shared "
                "WHERE owner = ? ORDER BY time DESC LIMIT 5",
                (username,)
            )
            shared_prompts = cursor.fetchall()
        return render_template(
            "account/profile.html",
            error=error,
            success=success,
            saved_prompts=saved_prompts,
            shared_prompts=shared_prompts,
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
        # drop user's prompt table
        with get_db_connection(main_blueprint.prompt_db) as conn:
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {username}")
            conn.commit()
        session.clear()
        return redirect(url_for("main.index"))

    @main_blueprint.route("/generate")
    @required_login
    def generate():
        return render_template("prompts/generator/basic.html")

    @main_blueprint.route("/generate/tprompt", methods=["POST"])
    @required_login
    def process():
        """Generate a text prompt using user input. Validates input and returns model response."""
        user_input = request.form.get("user_input", "").strip()
        if not user_input:
            return jsonify({"success": False, "error": "Input cannot be empty."}), 400
        if len(user_input) > 500:
            return jsonify({"success": False, "error": "Input is too long (max 500 characters)."}), 400
        try:
            response_text = model.generate_response("./instruction/basic1.txt", user_input)
            return jsonify({"success": True, "response": response_text})
        except Exception as e:
            logger.exception("Error generating prompt response")
            return jsonify({"success": False, "error": "Failed to generate response."}), 500

    @main_blueprint.route("/generate/trandom", methods=["POST"])
    @required_login
    def random_prompt():
        response_text = model.generate_random("./instruction/basic2.txt")
        return response_text

    @main_blueprint.route("/generate/iprompt", methods=["POST"])
    @required_login
    def vprocess():
        user_input = request.form["user_input"]
        response_text = model.generate_imgdescription(
            "./instruction/image_styles.txt", user_input
        )
        return response_text

    @main_blueprint.route("/generate/irandom", methods=["POST"])
    @required_login
    def vrandom_prompt():
        response_text = model.generate_vrandom("./instruction/image_styles.txt")
        return response_text

    @main_blueprint.route("/generate/image", methods=["POST"])
    @required_login
    def reverse_image():
        try:
            image_file = request.files["image"]
            image_data = image_file.read()
            response_text = model.generate_visual(
                "./instruction/image_styles.txt", image_data
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
            image_file = request.files["image"]
            image_data = image_file.read()
            parameters = [request.form[f"parameter{i}"] for i in range(1, 4)]
            response_text = model.generate_visual2(image_data, *parameters)
            return response_text
        except Exception as e:
            logger.error(f"Error processing advance image: {e}")
            return f"Error: {str(e)}"

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

    return main_blueprint
