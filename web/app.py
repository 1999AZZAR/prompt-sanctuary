import os
import sys
# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, session
from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf
from flask_babel import Babel, gettext, ngettext, _
from db import init_app as db_init_app, get_session
from routes import create_main_blueprint

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
csrf = CSRFProtect(app)

# Configure CSRF to accept tokens from headers for AJAX requests
app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Disable automatic CSRF checking for all requests

# Initialize Babel
babel = Babel(app)

# Define supported languages
LANGUAGES = {
    'en': 'English',
    'id': 'Bahasa Indonesia'
}

# Babel configuration
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(os.path.dirname(__file__), 'translations')
app.config['BABEL_LANGUAGES'] = list(LANGUAGES.keys())  # Explicitly specify supported languages

def get_locale():
    """Get locale from user session or browser preferences"""
    # Check if user has set a language preference
    if 'language' in session:
        return session['language']

    # Try to get language from browser Accept-Language header
    best_match = request.accept_languages.best_match(list(LANGUAGES.keys()))
    if best_match:
        return best_match

    return 'en'  # Default fallback

babel.init_app(app, locale_selector=get_locale)

# Initialize SQLAlchemy (runs `alembic upgrade head` on first call)
db_init_app(app)

# Create and register the Blueprint with the unified database path.
# The four legacy *_DATABASE env vars are preserved for back-compat with
# docker-compose / config, but routes.py no longer uses them (all data lives
# in web.database.app.db now). We pass the unified path as each of the four.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
def default_path(*parts):
    return os.path.join(BASE_DIR, *parts)

DEFAULT_APP_DB = os.getenv("APP_DATABASE", default_path("database", "app.db"))
USER_DATABASE = os.getenv("USER_DATABASE", DEFAULT_APP_DB)
PROMPT_DATABASE = os.getenv("PROMPT_DATABASE", DEFAULT_APP_DB)
QUERY_DATABASE = os.getenv("QUERY_DATABASE", DEFAULT_APP_DB)
COMMUNITY_DATABASE = os.getenv("COMMUNITY_DATABASE", DEFAULT_APP_DB)
FEEDBACK_DATABASE = os.getenv("FEEDBACK_DATABASE", DEFAULT_APP_DB)

# Create and register the Blueprint
main_blueprint = create_main_blueprint(
    USER_DATABASE,
    PROMPT_DATABASE,
    QUERY_DATABASE,
    COMMUNITY_DATABASE,
    FEEDBACK_DATABASE,
)

# Set LANGUAGES in routes module to avoid circular import
import routes
routes.LANGUAGES = LANGUAGES

# Inject LANGUAGES into every template for the language switcher
@app.context_processor
def inject_globals():
    return {
        "LANGUAGES": LANGUAGES,
        "ACTIVE_LANGUAGE": session.get("language") or "en",
    }

app.register_blueprint(main_blueprint)

# Set CSRF cookie for frontend fetches
@app.after_request
def set_csrf_cookie(response):
    try:
        token = generate_csrf()
        response.set_cookie('csrf_token', token, httponly=False, samesite='Lax')
    except Exception:
        pass
    return response

# Secure cookies and security headers (configurable)
SECURE_COOKIES = os.getenv("SECURE_COOKIES", "false").lower() in {"1", "true", "yes"}
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=SECURE_COOKIES,
)

@app.after_request
def add_security_headers(resp):
    # Content Security Policy – permissive for current CDNs; tighten as inline scripts are removed
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https:; "
        "style-src 'self' 'unsafe-inline' https:; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https:; "
        "connect-src 'self' https:; "
        "frame-src 'self' https:; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    resp.headers.setdefault("Content-Security-Policy", csp)
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return resp

# Health endpoint — uses SQLAlchemy session to verify the toolchain works.
@app.route("/api/health")
def health():
    from flask import g
    from db.models import User, Achievement
    s = g.db_session
    user_count = s.query(User).count()
    ach_count = s.query(Achievement).count()
    return {
        "status": "ok",
        "db": "app.db",
        "users": user_count,
        "achievements": ach_count,
    }

if __name__ == "__main__":
    # app.run(debug=True, port=int(os.environ.get('PORT', 80)))
    app.run(host="0.0.0.0", port=5000, debug=True)
