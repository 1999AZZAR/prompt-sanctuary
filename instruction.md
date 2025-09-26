# Prompt Sanctuary - Technical Installation & Configuration Guide

## Project Overview

**Prompt Sanctuary** is a comprehensive web application built with Flask that provides AI-powered prompt generation, management, and sharing capabilities. The application features a modern UI with Tailwind CSS v3, glassmorphism design, and multilingual support.

### Technical Architecture

- **Backend Framework**: Flask with modular Blueprint architecture
- **AI Integration**: Google Generative AI (Gemini) with multi-key rotation support
- **Database**: Multi-database SQLite architecture with automatic schema management
- **Security**: CSRF protection, session management, Content Security Policy headers
- **Internationalization**: Flask-Babel with English and Indonesian support
- **Frontend**: Tailwind CSS v3 with modern UI patterns and responsive design

### Key Features

- **Prompt Generation**: Basic and advanced AI-powered prompt creation
- **Version Control**: Automatic prompt versioning with history and rollback capabilities
- **Community System**: Shared prompt library with user contributions
- **User Management**: Secure authentication with session-based access control
- **Multilingual Support**: Real-time language switching (English/Indonesian)
- **Security**: Comprehensive CSRF protection and input sanitization

## Prerequisites

### System Requirements

- **Python**: 3.8 or higher (3.9+ recommended)
- **Operating System**: Linux, macOS, or Windows (WSL2 recommended for Windows)
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Storage**: 500MB free space for databases and dependencies
- **Network**: Internet connection for API calls to Google Generative AI

### Required Software

- **Git**: For repository cloning and version control
- **pip**: Python package manager (included with Python 3.4+)
- **virtualenv** or **venv**: For isolated Python environments (recommended)

### API Requirements

- **Google AI Studio API Key**: Required for AI functionality
  - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Multiple keys supported for load balancing and redundancy
  - Free tier available with generous usage limits

## Installation & Setup

### 1. Repository Setup

```bash
# Clone the repository
git clone https://github.com/1999AZZAR/prompt-sanctuary.git
cd prompt-sanctuary

# Verify repository structure
ls -la
```

### 2. Environment Configuration

#### Virtual Environment Setup

```bash
# Create virtual environment (recommended approach)
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Upgrade pip to latest version
pip install --upgrade pip
```

#### Alternative: System-wide Installation

```bash
# Install dependencies globally (not recommended for development)
pip install -r requirements.txt
```

### 3. Dependencies Installation

```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(flask|google-generativeai|flask-wtf|flask-babel)"
```

**Core Dependencies:**
- `flask`: Web framework with Werkzeug WSGI utility
- `google-generativeai`: Google Generative AI Python SDK
- `python-dotenv`: Environment variable management
- `flask-wtf`: WTForms integration with CSRF protection
- `flask-babel`: Internationalization and localization
- `pillow`: Image processing for user avatars
- `retrying`: Exponential backoff for API resilience

### 4. Environment Configuration

```bash
# Navigate to web directory
cd web

# Create environment configuration file
touch .env
```

**Required Environment Variables:**

```bash
# Essential Configuration
GENAI_API_KEY=your_api_key_here,your_second_key_here
SECRET_KEY=your_flask_secret_key_here

# Optional Configuration (with defaults)
GENAI_MODEL_NAME=gemini-2.5-flash
SECURE_COOKIES=false
USER_DATABASE=web/database/user.db
PROMPT_DATABASE=web/database/prompt_data.db
QUERY_DATABASE=web/database/community/query.db
COMMUNITY_DATABASE=web/database/community/shared.db
FEEDBACK_DATABASE=web/database/feedback.db
```

#### Configuration Details

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `GENAI_API_KEY` | ✓ | - | Comma-separated Google AI Studio API keys (auto-rotation) |
| `GENAI_MODEL_NAME` | | `gemini-2.5-flash` | AI model override (e.g., `gemini-2.5-pro`) |
| `SECRET_KEY` | | Auto-generated | Flask session encryption key (use strong key in production) |
| `SECURE_COOKIES` | | `false` | Enable secure cookies (set to `true` for HTTPS) |
| `USER_DATABASE` | | `web/database/user.db` | User accounts and sessions database path |
| `PROMPT_DATABASE` | | `web/database/prompt_data.db` | Personal prompts and versioning database |
| `QUERY_DATABASE` | | `web/database/community/query.db` | Built-in system prompts database |
| `COMMUNITY_DATABASE` | | `web/database/community/shared.db` | Community shared prompts database |
| `FEEDBACK_DATABASE` | | `web/database/feedback.db` | User feedback storage database |

### 5. Database Initialization

The application automatically creates and initializes all required databases on startup:

```bash
# Start the application (databases will be created automatically)
python app.py
```

**Database Structure:**
- **SQLite Databases**: Multi-file architecture for data isolation
- **Auto-migration**: Schema updates applied automatically on startup
- **Foreign Key Enforcement**: SQLite foreign key constraints enabled
- **Directory Creation**: Database directories created automatically

### 6. Application Startup

#### Development Mode

```bash
# Standard development startup
cd web
python app.py
# Application starts on http://127.0.0.1:5000
```

#### Production Mode

```bash
# Production deployment with WSGI server
cd web
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app
```

#### Development Server Script

```bash
# Using the provided development script
./devserver.sh
# Requires PORT environment variable to be set
```

## Database Architecture

### Multi-Database Design

The application uses a distributed database architecture for scalability and data isolation:

```
web/database/
├── user.db                    # User accounts, sessions, profiles
├── prompt_data.db             # Personal prompts, versions, user tables
├── feedback.db               # User feedback storage
└── community/
    ├── query.db              # Built-in system prompts
    └── shared.db             # Community shared prompts
```

### Database Schema

#### User Database (`user.db`)
- **users table**: User accounts with email and identicon support
- **sessions table**: Session management with token validation

#### Prompt Database (`prompt_data.db`)
- **prompt_versions table**: Version-controlled prompt storage
- **User-specific tables**: Individual prompt libraries per user

#### Community Database (`community/shared.db`)
- **shared table**: Community-contributed prompts with ownership tracking

#### System Database (`community/query.db`)
- **Built-in prompt templates**: Pre-configured system prompts

#### Feedback Database (`feedback.db`)
- **feedback table**: User feedback collection system

## Security Implementation

### CSRF Protection
- All POST endpoints protected with CSRF tokens
- Frontend automatically includes tokens via `X-CSRFToken` header
- Server-side validation with Flask-WTF integration

### Session Management
- Secure session cookies with configurable security settings
- Session token validation with automatic expiration
- "Remember me" functionality with persistent sessions

### Content Security Policy
```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https:; ...
```
- Restrictive CSP headers applied to all responses
- XSS protection through content sanitization
- External resource loading policies

### Authentication Flow
1. Username/password authentication with bcrypt hashing
2. Session token generation and storage
3. Token validation on protected routes
4. Automatic session refresh on activity

## Development Workflow

### Project Structure

```
prompt-sanctuary/
├── web/                      # Main Flask application
│   ├── app.py               # Application entry point
│   ├── models.py            # Database models and operations
│   ├── routes.py            # Route definitions and handlers
│   ├── response.py          # AI integration (legacy)
│   ├── response2.py         # AI integration (current)
│   ├── static/              # CSS, JavaScript, images
│   ├── templates/           # HTML templates
│   ├── database/            # SQLite databases
│   └── translations/        # Internationalization files
├── requirements.txt         # Python dependencies
├── instruction.md           # This documentation
└── README.md               # Project overview
```

### Key Routes and Endpoints

| Route | Method | Authentication | Description |
|-------|--------|----------------|-------------|
| `/` | GET | No | Landing page with navigation |
| `/login` | GET/POST | No | User authentication |
| `/signup` | GET/POST | No | User registration |
| `/home` | GET | Yes | Main dashboard |
| `/generate` | GET/POST | Yes | Basic prompt generation |
| `/advance` | GET/POST | Yes | Advanced prompt generation |
| `/library` | GET | Yes | Community prompt library |
| `/mylib` | GET | Yes | Personal prompt library |
| `/save_prompt` | POST | Yes | Save generated prompts |
| `/versions/<id>` | GET | Yes | Prompt version history |
| `/language/<lang>` | GET | Yes | Language switching |

### Internationalization

**Supported Languages:**
- **English** (`en`): Default language with complete coverage
- **Indonesian** (`id`): Full translation coverage

**Translation Management:**
```bash
# Extract messages for translation
pybabel extract -F babel.cfg -o messages.pot .

# Initialize new language
pybabel init -i messages.pot -d web/translations -l id

# Compile translations
pybabel compile -d web/translations
```

## Deployment Options

### Local Development

```bash
# Standard development setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd web
python app.py
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY web/ ./web/
WORKDIR /app/web

EXPOSE 5000
CMD ["python", "app.py"]
```

### Production Deployment

#### Using Gunicorn (Recommended)

```bash
# Install production server
pip install gunicorn

# Start with multiple workers
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app

# With configuration file
gunicorn --config gunicorn.conf.py app:app
```

**Gunicorn Configuration:**
```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
```

#### Using Nginx + Gunicorn

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/prompt-sanctuary/web/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Environment-Specific Configuration

#### Development Environment
```bash
# .env.development
DEBUG=True
FLASK_ENV=development
GENAI_API_KEY=dev_key_1,dev_key_2
SECRET_KEY=dev-secret-key-change-in-production
SECURE_COOKIES=false
```

#### Production Environment
```bash
# .env.production
DEBUG=False
FLASK_ENV=production
GENAI_API_KEY=prod_key_1,prod_key_2,prod_key_3
SECRET_KEY=very-long-random-secret-key-here
SECURE_COOKIES=true
```

## Troubleshooting

### Common Installation Issues

#### 1. Import Errors

```bash
# Error: ModuleNotFoundError: No module named 'flask'
# Solution: Ensure virtual environment is activated
source venv/bin/activate

# Error: ImportError: cannot import name 'something'
# Solution: Check requirements.txt and reinstall
pip install --upgrade -r requirements.txt
```

#### 2. Database Connection Issues

```bash
# Error: SQLite database locked
# Solution: Ensure no other processes are accessing the database
# Check for running Flask processes and kill them
ps aux | grep flask
kill -9 <process_id>

# Error: Database permission denied
# Solution: Check file permissions
chmod 644 web/database/*.db
chmod 755 web/database/
```

#### 3. API Key Issues

```bash
# Error: API key not valid or quota exceeded
# Solution: Verify API key in Google AI Studio
# Check quota limits and regenerate if necessary
# Use multiple keys for redundancy
```

#### 4. Port Binding Issues

```bash
# Error: Address already in use
# Solution: Kill existing processes on port 5000
lsof -ti:5000 | xargs kill -9
# Or use different port
python app.py --port 8080
```

#### 5. CSRF Token Issues

```bash
# Error: CSRF token missing or incorrect
# Solution: Check browser developer tools
# Ensure CSRF token cookie is set correctly
# Verify frontend is sending X-CSRFToken header
```

### Debug Mode

Enable detailed error reporting:

```python
# Add to app.py for debugging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or run with debug flag
FLASK_DEBUG=1 python app.py
```

### Performance Monitoring

```bash
# Monitor application performance
pip install flask-profiler
# Add profiler middleware to app.py

# Database query optimization
# Check SQLite query performance with .explain
```

## API Integration

### Google Generative AI Configuration

**Model Options:**
- `gemini-2.5-flash` (default): Fast, efficient for most use cases
- `gemini-2.5-pro`: Higher quality, slower, higher quota usage
- `gemini-1.5-pro`: Legacy model with different capabilities

**API Key Rotation:**
- Multiple keys separated by commas
- Automatic failover on quota exhaustion
- Rate limiting and error handling

### Rate Limiting

**Google AI Studio Limits (Free Tier):**
- 60 requests per minute
- 1,000 requests per day
- Automatic retry with exponential backoff

## Maintenance

### Database Backup

```bash
# Backup all databases
cd web/database
cp user.db user.backup.db
cp prompt_data.db prompt_data.backup.db
cp community/query.db community/query.backup.db
cp community/shared.db community/shared.backup.db
cp feedback.db feedback.backup.db
```

### Log Management

```bash
# View application logs
tail -f /var/log/flask/app.log

# Configure logging in production
import logging
from logging.handlers import RotatingFileHandler

# Add to app.py
if not app.debug:
    file_handler = RotatingFileHandler('/var/log/flask/app.log', maxBytes=1024*1024*10, backupCount=5)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

### Updates and Upgrades

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update application code
git pull origin main

# Restart application
sudo systemctl restart prompt-sanctuary
```

## Support and Contributing

### Getting Help

1. **Documentation**: Check this instruction file and README.md
2. **Issues**: Create GitHub issues for bugs and feature requests
3. **Discussions**: Use GitHub Discussions for questions and support

### Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and test thoroughly
4. Submit pull request with detailed description

### Testing

```bash
# Run basic application tests
python -m pytest tests/

# Manual testing checklist:
# - User registration and login
# - Prompt generation (basic and advanced)
# - Prompt saving and versioning
# - Community features
# - Language switching
# - Mobile responsiveness
```

---

**Note**: This application requires active internet connectivity for AI API calls. All data is stored locally in SQLite databases. For production deployments, ensure proper backup strategies and monitoring are in place.
