# Development Setup Guide

This guide will help you set up a local development environment for Prompt Sanctuary.

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
  - Get your free API key from [Google AI Studio](https://aistudio.google.com/)
  - Multiple keys recommended for development and testing

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/1999AZZAR/prompt-sanctuary.git
cd prompt-sanctuary
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install black flake8 pylint pytest
```

### 4. Environment Configuration
Create a `.env` file in the project root:

```bash
# Required: Google AI Studio API key(s)
GENAI_API_KEY=your_api_key_here,optional_second_key

# Optional: Override default model
GENAI_MODEL_NAME=gemini-2.5-flash

# Optional: Flask secret key for sessions
SECRET_KEY=your-secret-key-here

# Optional: Enable/disable streaming
ENABLE_STREAMING=true

# Optional: Database paths (defaults provided)
USER_DATABASE=web/database/user.db
PROMPT_DATABASE=web/database/prompt_data.db
QUERY_DATABASE=web/database/community/query.db
COMMUNITY_DATABASE=web/database/community/shared.db
FEEDBACK_DATABASE=web/database/feedback.db
```

### 5. Database Setup
```bash
# Navigate to web directory
cd web

# Run the application to auto-create databases
python app.py
```

The application will automatically:
- Create necessary database directories
- Initialize database schemas
- Set up default data (achievements, etc.)

### 6. Start Development Server
```bash
# From the web directory
python app.py

# Or from project root using the dev script
./devserver.sh
```

The application will be available at `http://127.0.0.1:5000`

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
│   ├── api_key_pool.py      # API key management
│   ├── api_key_validator.py # API key validation
│   ├── utils.py             # Utility functions
│   ├── safe_migration.py    # Database migration utility
│   ├── static/              # Static assets
│   │   ├── script/          # JavaScript modules
│   │   ├── styles/          # CSS files
│   │   └── icon/            # Icons and images
│   ├── templates/           # HTML templates
│   ├── database/            # SQLite databases
│   └── translations/        # Internationalization files
├── docs/                    # Documentation
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── README.md               # Project overview
```

### Code Organization

#### Backend Structure
- **`app.py`**: Main application configuration and initialization
- **`models.py`**: Database models, queries, and business logic
- **`routes.py`**: HTTP route handlers and request processing
- **`response.py`**: AI model integration and response processing
- **`utils.py`**: Shared utility functions and helpers

#### Frontend Structure
- **`static/script/`**: JavaScript modules organized by feature
- **`static/styles/`**: CSS files and styling
- **`templates/`**: HTML templates with Jinja2 syntax

### Development Tools

#### Code Quality Tools
```bash
# Format code with Black
black web/

# Lint code with flake8
flake8 web/

# Type checking with mypy (if configured)
mypy web/

# Run tests with pytest
pytest tests/
```

#### Database Management
```bash
# Run database migrations
python web/safe_migration.py

# Preview migration changes (dry run)
python web/safe_migration.py --dry-run

# Rebuild all databases (destructive)
python web/safe_migration.py --rebuild
```

### Testing

#### Manual Testing Checklist
- [ ] User registration and login
- [ ] Prompt generation (basic and advanced)
- [ ] Prompt saving and versioning
- [ ] Community features (sharing, browsing)
- [ ] API key management
- [ ] Point system and achievements
- [ ] Language switching
- [ ] Mobile responsiveness
- [ ] Error handling and edge cases

#### Automated Testing (Planned)
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run end-to-end tests
pytest tests/e2e/

# Generate coverage report
pytest --cov=web tests/
```

## Configuration

### Environment Variables

#### Required Variables
- **`GENAI_API_KEY`**: Google AI Studio API key(s), comma-separated

#### Optional Variables
- **`GENAI_MODEL_NAME`**: AI model to use (default: `gemini-2.5-flash`)
- **`SECRET_KEY`**: Flask session secret (auto-generated if not provided)
- **`ENABLE_STREAMING`**: Enable/disable streaming responses (default: `true`)
- **Database paths**: Customize database file locations

#### Development-Specific Variables
```bash
# Enable debug mode
FLASK_DEBUG=true

# Set log level
LOG_LEVEL=DEBUG

# Enable development features
DEV_MODE=true

# Database debug mode
DB_DEBUG=true
```

### Database Configuration

#### Default Database Paths
```
web/database/
├── user.db                    # User accounts and authentication
├── prompt_data.db             # Personal prompts and versions
├── feedback.db                # User feedback storage
└── community/
    ├── query.db              # Built-in system prompts
    └── shared.db             # Community shared prompts
```

#### Database Settings
- **WAL Mode**: Enabled for better concurrency
- **Foreign Keys**: Enabled for referential integrity
- **Synchronous**: Set to NORMAL for performance
- **Journal Mode**: Write-Ahead Logging for reliability

## Troubleshooting

### Common Issues

#### Installation Issues
**Problem**: `pip install` fails with dependency conflicts
**Solution**: 
```bash
# Create fresh virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Problem**: Import errors when running the application
**Solution**:
```bash
# Ensure you're in the correct directory
cd web
python app.py

# Or set PYTHONPATH
export PYTHONPATH=/path/to/prompt-sanctuary/web:$PYTHONPATH
```

#### Database Issues
**Problem**: Database files not created
**Solution**:
```bash
# Ensure database directory exists
mkdir -p web/database/community

# Run the application to auto-create databases
cd web
python app.py
```

**Problem**: Database lock errors
**Solution**:
```bash
# Check for running processes
ps aux | grep python

# Kill any hanging processes
pkill -f "python app.py"

# Restart the application
cd web
python app.py
```

#### API Issues
**Problem**: API key validation fails
**Solution**:
- Verify API key is correct and active
- Check API key has proper permissions
- Ensure internet connection is working
- Try with a different API key

**Problem**: Rate limiting errors
**Solution**:
- Add more API keys to the `GENAI_API_KEY` variable
- Implement proper rate limiting in your requests
- Use the API key pool system for better distribution

### Debug Mode

#### Enable Debug Logging
```bash
# Set environment variable
export FLASK_DEBUG=true

# Or add to .env file
FLASK_DEBUG=true
```

#### Database Debug Mode
```bash
# Enable SQL query logging
export DB_DEBUG=true
```

#### API Debug Mode
```bash
# Enable detailed API request/response logging
export API_DEBUG=true
```

## IDE Setup

### VS Code Configuration
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "web/database/*.db": true
    }
}
```

### PyCharm Configuration
1. Open project in PyCharm
2. Configure Python interpreter to use `.venv/bin/python`
3. Set up code style to use Black formatter
4. Configure pytest as test runner
5. Set up database tools for SQLite

## Contributing

### Development Workflow
1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Make your changes** following the coding standards
4. **Test your changes** thoroughly
5. **Commit your changes**: `git commit -m "Add new feature"`
6. **Push to your fork**: `git push origin feature/new-feature`
7. **Create a pull request** with a detailed description

### Coding Standards
- **Python**: Follow PEP 8, use Black for formatting
- **JavaScript**: Use consistent naming conventions
- **CSS**: Follow BEM methodology with Tailwind utilities
- **Documentation**: Update relevant documentation for new features

### Testing Requirements
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows
- **Performance Tests**: Ensure no performance regressions

---

*For more information about contributing, see the [Contributing Guide](contributing.md).*
