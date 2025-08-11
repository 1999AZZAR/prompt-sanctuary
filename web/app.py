import os
from flask import Flask
from models import create_tables
from routes import create_main_blueprint

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# Database paths (absolute, relative to this file)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
def default_path(*parts):
    return os.path.join(BASE_DIR, *parts)

USER_DATABASE = os.getenv("USER_DATABASE", default_path("database", "user.db"))
PROMPT_DATABASE = os.getenv("PROMPT_DATABASE", default_path("database", "prompt_data.db"))
QUERY_DATABASE = os.getenv("QUERY_DATABASE", default_path("database", "community", "query.db"))
COMMUNITY_DATABASE = os.getenv("COMMUNITY_DATABASE", default_path("database", "community", "shared.db"))
FEEDBACK_DATABASE = os.getenv("FEEDBACK_DATABASE", default_path("database", "feedback.db"))

# Ensure database directories exist
for db_path in [USER_DATABASE, PROMPT_DATABASE, QUERY_DATABASE, COMMUNITY_DATABASE, FEEDBACK_DATABASE]:
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

# Create necessary tables
create_tables(
    USER_DATABASE, PROMPT_DATABASE, COMMUNITY_DATABASE, FEEDBACK_DATABASE
)

# Create and register the Blueprint with database paths
main_blueprint = create_main_blueprint(
    USER_DATABASE,
    PROMPT_DATABASE,
    QUERY_DATABASE,
    COMMUNITY_DATABASE,
    FEEDBACK_DATABASE,
)
app.register_blueprint(main_blueprint)

if __name__ == "__main__":
    # app.run(debug=True, port=int(os.environ.get('PORT', 80)))
    app.run(host="0.0.0.0", port=5000, debug=True)
