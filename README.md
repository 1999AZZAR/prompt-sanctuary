# Prompt Sanctuary

A comprehensive web application for creating, managing, and optimizing AI prompts to enhance assistant performance across various tasks.

## Overview

Prompt Sanctuary combines the best features from three previous projects into a unified platform:

- **[Prompt Library](https://github.com/1999AZZAR/gpt-advance-prompt-library)** - Curated collection of optimized prompts
- **[Prompt Generator](https://github.com/1999AZZAR/prompt-generator)** - Dynamic prompt creation tool
- **[Stability Chat](https://github.com/1999AZZAR/stability_chat_bot)** - Multi-modal AI assistant

### Key Capabilities

- **Prompt Library Access** - Browse and copy proven prompts for specific use cases
- **Custom Generation** - Create tailored prompts using advanced generation tools
- **Random Generation** - Discover new approaches through experimental prompts
- **Personal Library** - Save, organize, and version your custom prompts
- **Community Sharing** - Contribute to and benefit from community-driven improvements
- **Feedback System** - Continuous improvement through user feedback

### Live Demo

- **Web Application**: [prompt sanctuary](https://sanctuary01.pythonanywhere.com/)
- **Streamlit Version**: [streamlit promptgen](https://github.com/1999AZZAR/streamlit_promptgen)
- **Self-Hosting**: Follow the [setup instructions](instruction.md)

## Latest Updates (2025)

### User Interface & Experience

- **Modern Design System** - Tailwind CSS v3 with pastel theme and glassmorphism effects
- **Enhanced Modals** - Global popup system with keyboard navigation and accessibility features
- **Rich Content Rendering** - Markdown support with DOMPurify sanitization and Prism syntax highlighting
- **Copy Functionality** - One-click copying for generated content and code blocks

### Multilingual Support

- **Dual Language Interface** - Complete English and Indonesian language support
- **Instant Switching** - Real-time language switching without page reloads
- **Session Persistence** - Language preferences saved across sessions

### Prompt Management

- **Version Control** - Automatic snapshots and version history for saved prompts
- **Advanced Editing** - Rollback functionality and prompt evolution tracking
- **Community Integration** - Enhanced sharing and feedback systems
- **AI-Powered Titles** - Smart title generation for saved prompts
- **Prompt Refinement** - Dedicated refinement interface with multiple sources

### Economy & Gamification

- **Point System** - Comprehensive economy with points, achievements, and rewards
- **API Key Management** - Personal API key integration with validation and compensation
- **Usage Tracking** - Detailed transaction history and point expiration management

### Technical Improvements

- **Enhanced Performance** - SQLite WAL mode for improved concurrency
- **Robust Architecture** - Better error handling and retry mechanisms
- **Database Migration** - Production-ready migration utilities
- **Latest AI Models** - Updated to `gemini-2.5-flash` with easy model override

## Getting Started

### Quick Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/1999AZZAR/prompt-sanctuary.git
   cd prompt-sanctuary
   ```
2. **Create virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment**

   ```bash
   # Create .env file with your Google AI Studio key(s)
   GENAI_API_KEY=your_api_key_here
   ```
5. **Run the application**

   ```bash
   python web/app.py
   ```

   The application will be available at `http://127.0.0.1:5000`

### Language Support

- **Available Languages**: English (default) and Indonesian
- **Language Switching**: Use EN/ID buttons in the sidebar navigation
- **Session Persistence**: Language preferences are saved across sessions
- **Complete Coverage**: All UI elements, forms, and templates are translated

## Features

### Economy System

**Point-Based Economy**

- **Starting Balance**: 80 points for new users
- **Daily Bonuses**: 5-12 random points per day
- **Achievement Rewards**: Unlock points through various activities
- **Point Expiration**: Different expiration periods based on source (17-95 days)

**Prompt Generation Costs**

| Prompt Type            | Cost (Points) |
| ---------------------- | ------------- |
| Basic Text             | 1.0           |
| Advanced Text          | 1.0           |
| Advanced Image         | 1.0           |
| Advanced Reverse Image | 1.0           |
| Prompt Refinement      | 0.5           |
| AI Title Generation    | 0.2           |

**Achievement System**

- **Automatic Unlocking**: Based on user activity patterns
- **Multiple Categories**: Generation, sharing, consistency, and more
- **Point Rewards**: Each achievement grants additional points
- **Progress Tracking**: Monitor your statistics and achievements

### API Key Management

**Personal API Keys**

- **Integration**: Use your own Gemini API keys for unlimited usage
- **Validation**: Real-time API key validation with immediate feedback
- **Rewards**: Earn 100 points for successful API key addition
- **Cost-Free Generation**: No point consumption when using personal keys
- **Achievement**: Unlock "API Key Provider" achievement

**API Key Pool System**

- **Community Sharing**: Validated keys are pooled for system-wide use
- **Fair Distribution**: LRU rotation ensures equitable usage
- **Compensation**: Earn 0.5 points per system usage of your key
- **Usage Tracking**: Detailed statistics and usage metrics
- **Pool Management**: Automatic refresh with new validated keys

**Enhanced Point Tracking**

- **Transaction History**: Detailed logs with source attribution
- **Expiration Management**: Different periods based on point source
- **Point Cap**: Maximum 500 points per user
- **Interactive Dashboard**: Click points display for detailed history

### Database Management

**Migration System**

- **Safe Updates**: Incremental migrations without data loss
- **Automatic Backups**: All operations backed up before changes
- **Dry Run Mode**: Preview changes before applying
- **Smart Detection**: Automatic database type detection
- **Rollback Support**: Robust error handling with recovery

**Migration Commands**

```bash
# Standard migration
python safe_migration.py

# Preview changes
python safe_migration.py --dry-run

# Complete rebuild (destructive)
python safe_migration.py --rebuild

# Force migration
python safe_migration.py --force
```

**Database Features**

- **Schema Updates**: Automatic table and column creation
- **Index Optimization**: Performance index management
- **Data Initialization**: Default data seeding
- **WAL Mode**: Enhanced SQLite concurrency

### Content Processing

**Intelligent Formatting**

- **Multi-Layer Processing**: AI prompts, backend, and frontend cleaning
- **Pattern Recognition**: Automatic detection and correction of formatting issues
- **Smart Conversion**: AI formatting quirks converted to proper markdown
- **Security**: DOMPurify sanitization for all rendered content
- **Rich Display**: Proper headers, lists, code blocks, and formatting

**Supported Patterns**

- Square brackets: `[Header]*` → `## Header`
- Double hash brackets: `# # [Header]` → `## Header`
- Standalone asterisks: `text*` → `- text` or `**text**`
- JSON artifacts: Clean removal of formatting characters
- Indentation: Proper markdown list formatting

## Feature Status

| Category                 | Feature                                     | Status     |
| ------------------------ | ------------------------------------------- | ---------- |
| **UI/UX**          | Tailwind v3 pastel theme with glassmorphism | ✅ Done    |
| **UI/UX**          | Global popups with accessibility features   | ✅ Done    |
| **UI/UX**          | Enhanced profile page organization          | ✅ Done    |
| **Content**        | Markdown rendering with sanitization        | ✅ Done    |
| **Content**        | Advanced response formatting                | ✅ Done    |
| **Prompts**        | Save, edit, delete, share functionality     | ✅ Done    |
| **Prompts**        | Versioning with snapshots and rollback      | ✅ Done    |
| **Economy**        | Point system with daily bonuses             | ✅ Done    |
| **Economy**        | Achievement system with rewards             | ✅ Done    |
| **Economy**        | Interactive point history                   | ✅ Done    |
| **API Keys**       | Personal API key management                 | ✅ Done    |
| **API Keys**       | API key pool with compensation              | ✅ Done    |
| **Security**       | CSRF protection and session management      | ✅ Done    |
| **Backend**        | SQLite WAL mode and migration utility       | ✅ Done    |
| **Backend**        | Latest Gemini model integration             | ✅ Done    |
| **i18n**           | Complete multilingual system                | ✅ Done    |
| **Infrastructure** | Containerization + Tailwind build           | 📋 Planned |
| **Quality**        | Tests + CI + Alembic migrations             | 📋 Planned |

## Application Guide

### Navigation

- **Landing Page** (`/`) - Entry point with feature overview and login/signup options
- **Home Dashboard** (`/home`) - Main application interface and starting point
- **Basic Generator** (`/generate`) - Simple content generation with text input and options
- **Advanced Generator** (`/advance`) - Advanced content generation with detailed parameters
- **Prompt Refinement** (`/refinement`) - AI-powered prompt optimization from multiple sources
- **Community Library** (`/library`) - Browse shared prompts and templates
- **Personal Library** (`/mylib`) - Manage your saved prompts with version history

### Key Features Usage

**Prompt Management**

- **Save Prompts**: Store generated content in your personal library
- **Version Control**: Access "History" button to view, preview, and restore previous versions
- **Community Sharing**: Share prompts to the community library for others to use

**Economy System**

- **Point Balance**: Check your points in the sidebar navigation
- **Daily Bonuses**: Log in daily to earn 5-12 random points
- **Achievements**: Unlock achievements through various activities for additional points

**API Key Integration**

- **Personal Keys**: Add your Gemini API key in profile settings
- **Benefits**: No point consumption + 100 bonus points + system compensation
- **Compensation**: Earn 0.5 points each time your key is used by the system

**Language Support**

- **Switching**: Use EN/ID buttons in sidebar for instant language changes
- **Persistence**: Language preferences saved across sessions

### API Endpoints

**Core Application Routes**

| Path                    | Method   | Description                  | Auth |
| ----------------------- | -------- | ---------------------------- | ---- |
| `/`                   | GET      | Landing page                 | ❌   |
| `/login`, `/signup` | GET/POST | Authentication flows         | ❌   |
| `/home`               | GET      | Dashboard                    | ✅   |
| `/generate`           | GET      | Basic generator interface    | ✅   |
| `/advance`            | GET      | Advanced generator interface | ✅   |
| `/library`            | GET      | Community library            | ✅   |
| `/mylib`              | GET      | Personal library             | ✅   |

**Generation Endpoints**

| Path                   | Method | Description                      | Auth |
| ---------------------- | ------ | -------------------------------- | ---- |
| `/generate/tprompt`  | POST   | Generate text from input         | ✅   |
| `/generate/trandom`  | POST   | Generate random text             | ✅   |
| `/advance/generate`  | POST   | Advanced text generation         | ✅   |
| `/advance/igenerate` | POST   | Advanced image prompt generation | ✅   |
| `/refine_prompt`     | POST   | Refine existing prompts          | ✅   |
| `/generate_title`    | POST   | Generate AI-powered titles       | ✅   |

**Prompt Management**

| Path                   | Method | Description               | Auth |
| ---------------------- | ------ | ------------------------- | ---- |
| `/save_prompt`       | POST   | Save current prompt       | ✅   |
| `/save_edit`         | POST   | Save prompt edits         | ✅   |
| `/delete_prompt`     | POST   | Delete saved prompt       | ✅   |
| `/share_prompt`      | POST   | Share prompt to community | ✅   |
| `/unshare_prompt`    | POST   | Unshare prompt            | ✅   |
| `/versions/<id>`     | GET    | List prompt versions      | ✅   |
| `/versions/rollback` | POST   | Restore prompt version    | ✅   |

**User Management**

| Path                    | Method | Description                       | Auth |
| ----------------------- | ------ | --------------------------------- | ---- |
| `/language/<lang>`    | GET    | Set language preference           | ✅   |
| `/get_user_points`    | GET    | Get user points balance           | ✅   |
| `/points/history`     | GET    | Get point transaction history     | ✅   |
| `/api_key/validate`   | POST   | Validate API key                  | ✅   |
| `/api_key/remove`     | POST   | Remove API key (costs 100 points) | ✅   |
| `/api_key/pool_stats` | GET    | Get API key pool statistics       | ✅   |

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Google AI Studio API key(s)
- (Optional) Docker + Docker Compose v2 for containerized runs

### Option A — Local Python (development)

1. **Clone and setup environment**

```bash
   git clone https://github.com/1999AZZAR/prompt-sanctuary.git
   cd prompt-sanctuary
python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables**

```bash
   # Create .env file
   GENAI_API_KEY=your_api_key_here,optional_second_key

   # Optional configurations
# GENAI_MODEL_NAME=gemini-2.5-pro
   # SECRET_KEY=your-secret-key
```

3. **Start the application**

```bash
python web/app.py
```

   Application will be available at `http://127.0.0.1:5000`

### Option B — Docker (recommended for production / parity)

```bash
# 1. Create your env file
cp web/.env.example web/.env
#   → edit web/.env and set GENAI_API_KEY (and any other secrets)

# 2. Build and start
docker compose up -d --build

# 3. Tail logs
docker compose logs -f app

# 4. Stop
docker compose down
```

The image is multi-stage and runs Gunicorn (2 workers × 4 threads by default)
behind a `tini` init. SQLite databases and translation files are persisted in
two named volumes (`prompt-sanctuary-data`, `prompt-sanctuary-translations`).

Useful overrides:

```bash
# Change host port
HOST_PORT=8080 docker compose up -d

# Scale workers
GUNICORN_WORKERS=4 GUNICORN_THREADS=8 docker compose up -d

# Run one-off commands inside the container
docker compose exec app bash
```

### Database Structure

SQLite databases are automatically created in `web/database/`:

- `user.db` - User accounts and authentication
- `prompt_data.db` - Personal prompt library
- `community/query.db` - System prompts
- `community/shared.db` - Community shared prompts
- `feedback.db` - User feedback and ratings

**Reset Data**: Stop the application and delete relevant `.db` files to reset data.

## Configuration

| Variable               | Required | Default                              | Description                                  |
| ---------------------- | -------- | ------------------------------------ | -------------------------------------------- |
| `GENAI_API_KEY`      | ✅       | -                                    | Google AI Studio API key(s), comma-separated |
| `GENAI_MODEL_NAME`   | ❌       | `gemini-2.5-flash`                 | AI model override (e.g.,`gemini-2.5-pro`)  |
| `SECRET_KEY`         | ❌       | auto-generated                       | Flask session secret                         |
| `USER_DATABASE`      | ❌       | `web/database/user.db`             | User database path                           |
| `PROMPT_DATABASE`    | ❌       | `web/database/prompt_data.db`      | Personal prompts database path               |
| `QUERY_DATABASE`     | ❌       | `web/database/community/query.db`  | System prompts database path                 |
| `COMMUNITY_DATABASE` | ❌       | `web/database/community/shared.db` | Community prompts database path              |
| `FEEDBACK_DATABASE`  | ❌       | `web/database/feedback.db`         | Feedback database path                       |

## Security & Deployment

### Security Features

- **CSRF Protection** - All POST endpoints require CSRF tokens
- **Content Sanitization** - DOMPurify sanitization for all rendered content
- **Session Management** - Enhanced session handling with proper revocation
- **Input Validation** - Comprehensive input validation and error handling

### Production Deployment

**Requirements**

- Use a WSGI server (e.g., `gunicorn`) instead of Flask development server
- Set a strong `SECRET_KEY` environment variable
- Ensure HTTPS with Secure cookies
- Configure proper `GENAI_API_KEY` with outbound access to Google AI APIs

**Recommended Setup**

```bash
# Install production dependencies
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web.app:app
```

## Screenshots

### Application Interface

![Home Dashboard](img/1.png)
*Main dashboard with quick access to all features including the new Prompt Refinement*

![Personal Library](img/2.png)
*Personal prompt library with version control, edit capabilities, and sharing options*

![Community Library](img/3.png)
*Community library showcasing shared prompts from users with browsing and filtering options*

![Basic Generator](img/4.png)
*Basic prompt generation interface with text input and simple generation options*

![Advanced Generator](img/5.png)
*Advanced generation interface with detailed parameters, image modes, and custom settings*

![Prompt Refinement](img/6.png)
*AI-powered prompt refinement interface with multiple sources and quick actions*

![Profile Page](img/7.png)
*User profile page with account settings, API key management, and prompt statistics*
