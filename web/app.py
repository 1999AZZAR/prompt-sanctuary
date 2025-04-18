import os
from flask import Flask
from models import create_tables
from routes import create_main_blueprint

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# Database paths
USER_DATABASE = os.getenv("USER_DATABASE", "./database/user.db")
PROMPT_DATABASE = os.getenv("PROMPT_DATABASE", "./database/prompt_data.db")
QUERY_DATABASE = os.getenv("QUERY_DATABASE", "./database/community/query.db")
COMMUNITY_DATABASE = os.getenv("COMMUNITY_DATABASE", "./database/community/shared.db")
FEEDBACK_DATABASE = os.getenv("FEEDBACK_DATABASE", "./database/feedback.db")

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
