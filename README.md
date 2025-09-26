# Prompt-Sanctuary

Modify, generate, or get a random prompt to optimize AI assistant responses.

This project provides a redesigned UI and expanded capabilities building on my previous work, which was composed of three parts:

- [Prompt Library](https://github.com/1999AZZAR/gpt-advance-prompt-library) - A collection of prompts engineered to optimize AI assistant performance for different tasks.

- [Prompt Generator](https://github.com/1999AZZAR/prompt-generator) - A tool to generate prompts by combining elements from the library.

- [stability chat](https://github.com/1999AZZAR/stability_chat_bot) - A chatbot web app built with flask to generate image using stability api and text using gemini.

With this new implementation, users can:

- Access the prompt library to copy proven prompts for their use case.

- Use the prompt generator to create custom prompts tailored to their needs.

- Get randomly generated prompts for experimentation.

- Provide feedback on prompts to continuously improve the library.

- ability to save the generated prompt.

> You can try the tools yourself at [**prompt sanctuary**](https://sanctuary01.pythonanywhere.com/) or run(host) it yourself by following the instructions [here](instruction.md).
> You can also try the [**streamlit**](https://github.com/1999AZZAR/streamlit_promptgen) version.

## What’s new (2025 UI/Backend refresh)

- Tailwind CSS v3, pastel theme, and glassmorphism across the app
- Global popup system (details/confirm/custom) with keyboard focus-trap and backdrop click-to-close
- Safer, richer result rendering: Markdown + DOMPurify sanitization + Prism code highlighting with copy buttons
- Default Gemini model updated to latest stable free-tier friendly model (`gemini-2.5-flash`) with easy override
- More robust filesystem handling for SQLite DBs (auto-create DB directories)
- Complete multilingual system: English + Indonesian with instant language switching
- Prompt versioning: automatic snapshots on save/edit, history view, and rollback from personal library

## Multilingual Support

Prompt Sanctuary now supports **English** and **Indonesian** languages with complete internationalization:

- **🌍 Dual Language Interface**: Switch between English and Indonesian instantly
- **💾 Session Persistence**: Language preference remembered across sessions
- **🎨 Complete UI Coverage**: All templates, forms, and UI elements translated
- **⚡ Real-time Switching**: No page reload required
- **📱 Mobile Responsive**: Language switcher works on all devices

### Language Features
- **Default Language**: English (reliable fallback for all strings)
- **Language Switcher**: Located in sidebar navigation (EN/ID buttons)
- **Comprehensive Coverage**: All generator templates, forms, and navigation translated
- **Production Ready**: Full Flask-Babel implementation with compiled translation files

## Features

| Area | Feature | Status |
|---|---|---|
| UI/UX | Tailwind v3 pastel theme with glassmorphism | Done |
| UI/UX | Global popups (details/confirm/custom), wide modal for details/history | Done |
| Results | Markdown rendering, sanitization (DOMPurify), Prism syntax highlighting, copy buttons | Done |
| Prompts | Save, edit, delete, share/unshare (community) | Done |
| Prompts | Versioning (snapshots on save/edit, history, rollback) | Done (diff+fork later) |
| Security | CSRF protection on all POSTs | Done |
| Backend | Absolute DB paths + auto-create directories | Done |
| Backend | Latest stable free Gemini default (gemini-2.5-flash) | Done |
| i18n | Language switch | Done |
| i18n | Complete multilingual system (English + Indonesian) | Done |
| Perf/Infra | Containerization + Tailwind build | Planned |
| Quality | Tests + CI + Alembic migrations | Planned |

## Usage

Prompt-sanctuary's web interface is intuitive and user-friendly. Here's a quick guide on using its features:

- **Landing page**: Accessible from the root URL (`/`). Entry point with quick links to Login/Sign Up and features.
- **Home Page**: Accessible from the URL (`/home`). This is the starting point of the application.
- **Generate Content**: Navigate to `/generate` to access the content generation page. You can input text or select options to generate content.
- **Advanced Options**: For more advanced content generation, navigate to `/advance` and provide the required parameters.
- **Community Library**: Access various content generation templates and tools from the library section. Navigate to `/library` and choose the desired option.
- **Personal library**: contain per user prompt that they have saved before.
  - New: "History" button to view previous versions, preview, and restore.
- **Language Switching**: Click the EN/ID buttons in the sidebar to switch between English and Indonesian. Language preference is saved and persists across sessions.

### Key routes

| Path | Method | Description | Auth |
|---|---|---|:--:|
| `/` | GET | Landing page | - |
| `/login`, `/signup` | GET/POST | Auth flows | - / - |
| `/home` | GET | Home/dashboard | ✓ |
| `/generate` | GET | Basic generator UI | ✓ |
| `/generate/tprompt` | POST | Generate text from input | ✓ |
| `/generate/trandom` | POST | Generate random text | ✓ |
| `/advance` | GET | Advanced generator UI | ✓ |
| `/advance/generate` | POST | Advanced text generation | ✓ |
| `/advance/igenerate` | POST | Advanced image prompt from text | ✓ |
| `/library` | GET | Community library | ✓ |
| `/mylib` | GET | Personal library | ✓ |
| `/save_prompt` | POST | Save current prompt | ✓ |
| `/save_edit` | POST | Save edits to a prompt | ✓ |
| `/delete_prompt` | POST | Delete a saved prompt | ✓ |
| `/share_prompt` | POST | Share a saved prompt to community | ✓ |
| `/unshare_prompt` | POST | Unshare a prompt | ✓ |
| `/versions/<id>` | GET | List versions of a prompt | ✓ |
| `/versions/rollback` | POST | Restore a specific version | ✓ |
| `/language/<lang>` | GET | Set user language preference | ✓ |

## Quick start (local)

1) Create a virtual environment and install deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Create a `.env` file with your Google AI Studio key(s)

```bash
# One or more keys, comma-separated; will auto-rotate
GENAI_API_KEY=key1,key2

# Optional: override model (defaults to gemini-2.5-flash)
# GENAI_MODEL_NAME=gemini-2.5-pro

# Optional: Flask secret
# SECRET_KEY=your-secret
```

3) Run the app

```bash
python web/app.py
# App runs on http://127.0.0.1:5000 by default
```

### Databases

SQLite files are stored under `web/database/`. Paths are created automatically on startup:

- `web/database/user.db`
- `web/database/prompt_data.db`
- `web/database/community/query.db` (system prompts)
- `web/database/community/shared.db`
- `web/database/feedback.db`

To reset data locally, stop the app and remove the relevant `.db` files.

## Configuration

| Variable | Required | Default | Description |
|---|:--:|---|---|
| `GENAI_API_KEY` | ✓ | - | One or more Google AI Studio keys, comma-separated; keys rotate automatically |
| `GENAI_MODEL_NAME` |  | `gemini-2.5-flash` | Override model, e.g., `gemini-2.5-pro` |
| `SECRET_KEY` |  | generated fallback | Flask session secret |
| `USER_DATABASE` |  | `web/database/user.db` | Path to user DB |
| `PROMPT_DATABASE` |  | `web/database/prompt_data.db` | Path to personal prompts DB |
| `QUERY_DATABASE` |  | `web/database/community/query.db` | Path to built-in system prompts DB |
| `COMMUNITY_DATABASE` |  | `web/database/community/shared.db` | Path to shared prompts DB |
| `FEEDBACK_DATABASE` |  | `web/database/feedback.db` | Path to feedback DB |

## Security

- CSRF: All POST endpoints require a CSRF token. The server sets a `csrf_token` cookie; the frontend sends it via `X-CSRFToken`.
- Sanitization: Rendered results are sanitized with DOMPurify before display.
- Sessions: Use a strong `SECRET_KEY` in production; prefer HTTPS with Secure cookies.

## Deployment notes

- This repository’s Flask server runs in debug in development. For production, use a WSGI server (e.g., `gunicorn`) and set a proper `SECRET_KEY`.
- Ensure your environment has the required `GENAI_API_KEY` set and outbound access to Google AI APIs.

## demo

here some of the screenshot of the app looks like:

![landing page](img/3.png)
![home page](img/4.png)
![my library](img/5.png)
![prompt trial](img/6.png)
![advance generator](img/9.png)

## Thanks And Support

You can support me by buymeacoffee if u like to.

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://www.buymeacoffee.com/azzar)
