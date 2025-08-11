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
 - Prompt versioning: automatic snapshots on save/edit, history view, and rollback from personal library

## Usage

Prompt-sanctuary's web interface is intuitive and user-friendly. Here's a quick guide on using its features:

- **Landing page**: Accessible from the root URL (`/`). Entry point with quick links to Login/Sign Up and features.
- **Home Page**: Accessible from the URL (`/home`). This is the starting point of the application.
- **Generate Content**: Navigate to `/generate` to access the content generation page. You can input text or select options to generate content.
- **Advanced Options**: For more advanced content generation, navigate to `/advance` and provide the required parameters.
- **Community Library**: Access various content generation templates and tools from the library section. Navigate to `/library` and choose the desired option.
- **Personal library**: contain per user prompt that they have saved before.
  - New: “History” button to view previous versions, preview, and restore.

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

## Environment variables

- `GENAI_API_KEY` (required): One or more Google AI Studio keys, comma-separated
- `GENAI_MODEL_NAME` (optional): Defaults to `gemini-2.5-flash`
- `SECRET_KEY` (optional): Flask session secret; a default is used if not set

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
