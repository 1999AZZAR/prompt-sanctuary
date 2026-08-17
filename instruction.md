# Prompt Sanctuary - Technical Installation & Configuration Guide

## Project Overview

**Prompt Sanctuary** is a comprehensive web application built with Flask that provides AI-powered prompt generation, management, and sharing capabilities. The application features a custom Swiss 12-column grid × Polaris design system, leveraging vanilla CSS, and multilingual support.

### Technical Architecture

- **Backend Framework**: Flask with modular Blueprint architecture
- **AI Integration**: Google Generative AI (Gemini) with multi-key rotation support
- **Database**: Single-database architecture (`app.db`) managed via SQLAlchemy 2.0 and Alembic. PostgreSQL is the production target, with SQLite for development fallback
- **Security**: CSRF protection, secure session management, and strict Content Security Policy (CSP) headers
- **Internationalization**: Flask-Babel with English and Indonesian support
- **Frontend**: Vanilla CSS using CSS variables (no build step) for a fast, responsive UI
- **Deployment**: Dockerized with multi-stage builds (app, postgres, redis)

### Key Features

- **Prompt Generation**: Basic and advanced AI-powered prompt creation
- **Version Control**: Automatic prompt versioning with history and rollback capabilities
- **Community System**: Shared prompt library with user contributions
- **User Management**: Secure authentication with session-based access control
- **Multilingual Support**: Real-time language switching (English/Indonesian)
- **Security**: Comprehensive CSRF protection, CSP headers, and input sanitization

## Prerequisites

### System Requirements

- **Python**: 3.12 (recommended)
- **Operating System**: Linux, macOS, or Windows
- **Docker**: For production-like deployment (optional but recommended)

### Required Software

- **Git**: For repository cloning and version control
- **pip**: Python package manager
- **virtualenv** or **venv**: For isolated Python environments

### API Requirements

- **Google AI Studio API Key**: Required for AI functionality
  - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Multiple keys supported for load balancing and redundancy

## Installation & Setup

### 1. Repository Setup

```bash
git clone https://github.com/1999AZZAR/prompt-sanctuary.git
cd prompt-sanctuary
```

### 2. Environment Configuration

#### Virtual Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install --upgrade pip
```

### 3. Dependencies Installation

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the repository root:

```bash
GENAI_API_KEY=your_gemini_key_here,your_second_key_here
SECRET_KEY=your_flask_secret_key_here
```

**Configuration Details**

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `GENAI_API_KEY` | ✓ | - | Comma-separated Google AI Studio API keys |
| `GENAI_MODEL_NAME` | | `gemini-2.5-flash` | AI model override |
| `SECRET_KEY` | | Auto-generated | Flask session encryption key |
| `SECURE_COOKIES` | | `false` | Enable secure cookies (set to `true` behind HTTPS) |
| `DATABASE_URL` | | `sqlite:///.../web/database/app.db` | SQLAlchemy URL |
| `APP_DATABASE` | | `web/database/app.db` | Path override for the SQLite file |

*(Legacy database variables like `USER_DATABASE`, `PROMPT_DATABASE` are kept for backward compatibility but route to `app.db`)*

### 5. Application Startup (Local Dev)

The application will automatically run Alembic migrations on its first boot to set up the database schema.

```bash
python web/app.py
# Application starts on http://127.0.0.1:5000
```

### 6. Application Startup (Docker)

For a robust production-like setup with PostgreSQL and Redis:

```bash
# Copy the example env file and add your keys
cp .env.example .env

docker compose up -d --build
docker compose logs -f app
# Open http://127.0.0.1:5000
```

## Database Architecture

The application uses SQLAlchemy 2.0 with Alembic for migrations.

**Database schema contains 12 tables:** `users`, `sessions`, `user_logins`, `achievements`, `user_achievements`, `point_transactions`, `point_history`, `prompts`, `prompt_versions`, `shared_prompts`, `feedback`, `system_prompts`.

**Migrations Management:**

```bash
# Apply pending revisions
alembic upgrade head

# Generate a new revision after model changes
alembic revision --autogenerate -m "describe change"

# Roll back one revision
alembic downgrade -1
```

## Security Implementation

### CSRF Protection
- All POST endpoints protected with CSRF tokens (`X-CSRFToken` header)
- Server-side validation with Flask-WTF integration

### Session Management
- Secure session cookies configurable via `SECURE_COOKIES`
- Session token validation with explicit revocation capabilities

### Content Security Policy (CSP)
- Implemented in `app.py` directly on all responses
- Restricts external scripts, objects, and framing

### Authentication Flow
1. Username/password authentication with Werkzeug bcrypt hashing
2. Session token generation and storage
3. Token validation on protected routes

## Project Layout

```text
prompt-sanctuary/
├── alembic.ini              # Alembic configuration
├── docker-compose.yml       # Docker compose stack (app, postgres, redis)
├── Dockerfile               # Multi-stage Docker build
├── migrations/              # Alembic migrations history
├── requirements.txt         # Python dependencies
└── web/
    ├── app.py               # Flask application factory & routing
    ├── db/                  # SQLAlchemy setup and models
    ├── routes.py            # API and view routes
    ├── response2.py         # AI generation logic
    ├── static/              # Vanilla CSS (tokens.css, styles.css) and JS
    ├── templates/           # Jinja templates
    └── translations/        # Babel internationalization catalogs
```

---

**Note**: This application requires active internet connectivity for AI API calls. For production deployments, ensure `SECURE_COOKIES=true` and a reverse proxy (like Nginx) is configured correctly.
