# Prompt Sanctuary

A Flask web app for generating, refining, and managing AI prompts.
Combines a generator, personal library, community sharing, an API key
pool, and a point economy into a single self-hostable service.

## Origin

This project merges three earlier tools into one codebase:

- [Prompt Library](https://github.com/1999AZZAR/gpt-advance-prompt-library) - curated prompts
- [Prompt Generator](https://github.com/1999AZZAR/prompt-generator) - dynamic generation
- [Stability Chat](https://github.com/1999AZZAR/stability_chat_bot) - multi-modal assistant

## Capabilities

- **Generators** - basic text, random, advanced (text + image), reverse image
- **Refinement** - quick actions (shorten, elaborate, improve, fix grammar) or custom instructions, fed from manual input, your library, or the community feed
- **Personal library** - save, edit, version (snapshots on every save), rollback, share
- **Community library** - share prompts publicly; per-owner attribution
- **Feedback** - per-user feedback log with edit and delete
- **API key management** - bring your own Gemini key (validated on add, earns 100 points + the "API Key Provider" achievement); valid keys feed a shared pool with 0.5-point LRU compensation per system use
- **Point economy** - 80 starting points, daily login bonus, 55 achievements, transaction history with source-based expiration (17 to 95 days), 500-point cap
- **Internationalization** - English and Indonesian, switchable from the sidebar, persisted per session
- **Legal pages** - Terms of Service and Privacy Policy at `/terms` and `/privacy` (public)

## Tech Stack

- **Runtime**: Python 3.12, Flask, gunicorn 23.0 (2 workers x 4 threads), tini
- **Database**: PostgreSQL 16 (SQLite supported for dev fallback) via SQLAlchemy 2.0, schema managed by Alembic
- **Cache + rate limit**: Redis 7. Token bucket for `/generate/*` and `/advance/*`; read-through cache for `get_user_points`, `get_prompt_sharing_status`, and the system prompts list
- **AI**: Google Gemini (`gemini-2.5-flash` default, override via `GENAI_MODEL_NAME`; comma-separated keys auto-rotate)
- **Frontend**: Jinja templates, vanilla JS, Font Awesome 6. No build step.
- **i18n**: Flask-Babel
- **Security**: Flask-WTF CSRF (form + `X-CSRFToken` header), DOMPurify for rendered content
- **Container**: multi-stage `Dockerfile`, non-root user, JSON access logs, healthcheck. Compose stack bundles Postgres + Redis.

## Design Language

Swiss 12-column grid, 1px hairline borders, single Polaris teal accent
(`#008060`), Inter (display + body) plus JetBrains Mono (code), radius
capped at 8px. No shadows, no gradients, no purple. Defined in
`web/static/styles/tokens.css`.

## Quick Start (Local)

```bash
git clone https://github.com/1999AZZAR/prompt-sanctuary.git
cd prompt-sanctuary

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# .env in the repo root
echo 'GENAI_API_KEY=your_gemini_key_here' > .env

python web/app.py
# Open http://127.0.0.1:5000
```

The first request runs `alembic upgrade head` against `web/database/app.db`
and seeds 55 achievements. Subsequent boots are no-ops.

## Quick Start (Docker)

```bash
cp .env.example .env 2>/dev/null || true
# Edit .env and set GENAI_API_KEY (comma-separated for rotation)
# Postgres + Redis credentials are also in .env

docker compose up -d --build
docker compose logs -f app
# Open http://127.0.0.1:${HOST_PORT:-5000}
```

The compose stack bundles three services: `app` (the Flask + gunicorn
image), `sanctuary-postgres` (PostgreSQL 16), and `sanctuary-redis`
(Redis 7). Both data stores are persisted in named volumes
(`sanctuary-postgres-data`, `sanctuary-redis-data`). The first request
runs `alembic upgrade head` against the Postgres database, wrapped in a
`pg_advisory_lock` so gunicorn workers don't race.

```bash
# Bind to a different host port
HOST_PORT=8080 docker compose up -d

# Scale workers
GUNICORN_WORKERS=4 GUNICORN_THREADS=8 docker compose up -d

# Shell into the app container
docker compose exec app bash

# Open a psql session
docker compose exec sanctuary-postgres psql -U sanctuary -d sanctuary

# Inspect the Redis cache + rate-limit state
docker compose exec sanctuary-redis redis-cli KEYS 'sanctuary:*'
```

### SQLite (dev fallback)

For local dev without Docker, set `DATABASE_URL=sqlite:///app.db` (or
just leave it unset; the app falls back to `web/database/app.db`).
SQLite is supported as a single-process dev DB; the Alembic migrations
include dialect-agnostic paths so the same chain applies.

## Database

PostgreSQL 16 in production (SQLite supported as a dev fallback).
Schema is declarative SQLAlchemy 2.0 (`web/db/models.py`) and versioned
with Alembic (`migrations/versions/`).

**Tables** (12): `users`, `sessions`, `user_logins`, `achievements`,
`user_achievements`, `point_transactions`, `point_history`, `prompts`,
`prompt_versions`, `shared_prompts`, `feedback`, `system_prompts`.

The connection pool is sized for `gunicorn workers x threads` with
overflow headroom (`pool_size=10, max_overflow=20` by default;
`pool_pre_ping=True` reconnects stale connections). SQLite connections
get `check_same_thread=False`, `foreign_keys=ON`, `journal_mode=WAL`,
`synchronous=NORMAL`.

The first request runs `alembic upgrade head` against the configured
database. On Postgres, a `pg_advisory_lock` serialises workers so they
don't race the migration. On SQLite, an `fcntl.flock` does the same.

**Migrations**:

```bash
# Apply pending revisions
alembic upgrade head

# Generate a new revision after model changes
alembic revision --autogenerate -m "describe change"

# Roll back one revision
alembic downgrade -1
```

The initial revision imports data from the legacy four-DB layout
(`user.db`, `prompt_data.db`, `community/shared.db`, `feedback.db`) and
seeds the 55 achievements. The import is idempotent (skip-on-existing)
so re-running is safe.

**Switch to Postgres**: set `DATABASE_URL=postgresql+psycopg://...` and
re-run `alembic upgrade head`. The schema is dialect-agnostic.

## Routes

### Public

| Path        | Method  | Notes                          |
| ----------- | ------- | ------------------------------ |
| `/`         | GET     | Landing page                   |
| `/login`    | GET/POST | Auth (returns JSON)           |
| `/signup`   | GET/POST | Creates user (returns JSON)   |
| `/terms`    | GET     | Terms of Service               |
| `/privacy`  | GET     | Privacy Policy                 |
| `/api/health` | GET   | SQLAlchemy smoke check (JSON)  |

### Authenticated pages

| Path            | Method | Description                       |
| --------------- | ------ | --------------------------------- |
| `/home`         | GET    | Dashboard with KPIs and shortcuts  |
| `/generate`     | GET    | Basic text + image generator      |
| `/advance`      | GET    | Advanced generator (params 0-3)   |
| `/refinement`   | GET    | Refine an existing prompt         |
| `/mylib`        | GET    | Personal library (versions)       |
| `/library`      | GET    | Community library                 |
| `/profile`      | GET/POST | Account, API key, achievements  |
| `/feedback`     | GET    | Personal feedback log             |

### Generation endpoints (all POST, auth required)

| Path                       | Description                          |
| -------------------------- | ------------------------------------ |
| `/generate/tprompt`        | Generate from text input             |
| `/generate/tprompt/stream` | Streamed variant                     |
| `/generate/trandom`        | Random text prompt                   |
| `/generate/iprompt`        | Generate from image (data URI)       |
| `/generate/irandom`        | Random image prompt                  |
| `/generate/image`          | Generate image                       |
| `/advance/generate`        | Advanced text                        |
| `/advance/igenerate`       | Advanced image prompt                |
| `/advance/image`           | Advanced image generation            |
| `/refine_prompt`           | Refine an existing prompt            |
| `/generate_title`          | AI title for a saved prompt          |
| `/save_prompt`             | Save prompt to library               |
| `/save_edit`               | Save edits to existing prompt        |
| `/delete_prompt`           | Delete a prompt (cascades versions)  |
| `/share_prompt` / `/unshare_prompt` | Toggle community visibility   |
| `/versions/<id>`           | List versions for a prompt           |
| `/versions/rollback`       | Restore a specific version           |

### User, account, and economy

| Path                          | Method | Description                            |
| ----------------------------- | ------ | -------------------------------------- |
| `/profile`                    | POST   | Update profile / change password / delete account |
| `/get_user_points`            | GET    | Current balance                        |
| `/points/history`             | GET    | Transaction history (modal data)       |
| `/sessions/list`              | GET    | Active sessions                        |
| `/sessions/revoke`            | POST   | Revoke another session                 |
| `/api_key/validate`           | POST   | Validate a Gemini key                  |
| `/api_key/remove`             | POST   | Remove key (costs 100 points)          |
| `/api_key/status`             | GET    | Current key state                      |
| `/api_key/pool_stats`         | GET    | Pool size and per-user rotation        |
| `/health/keys`                | GET    | Health of the key pool                 |
| `/submit_feedback`            | POST   | Submit feedback                        |
| `/feedback/<id>`              | PUT/DELETE | Edit / delete own feedback         |
| `/feedback/<id>/json`         | GET    | Fetch a single feedback entry          |
| `/language/<lang>`            | GET    | Switch language (en, id)               |
| `/delete_account`             | POST   | Self-service account deletion          |
| `/logout`                     | GET    | Clear session                          |
| `/debug/refinement`           | GET    | Dev-only prompt debug view             |

## Configuration

| Variable             | Required | Default                              | Description                                  |
| -------------------- | -------- | ------------------------------------ | -------------------------------------------- |
| `GENAI_API_KEY`      | yes      | -                                    | Gemini API key(s), comma-separated for automatic rotation under load |
| `STABILITY_API_KEY`  | no       | -                                    | Stability AI key (image alt)                 |
| `GENAI_MODEL_NAME`   | no       | `gemini-2.5-flash`                   | Model override (e.g., `gemini-2.5-pro`)      |
| `SECRET_KEY`         | no       | auto-generated                       | Flask session secret (set in production)     |
| `DATABASE_URL`       | no       | `sqlite:///.../web/database/app.db`  | SQLAlchemy URL (use Postgres in production)  |
| `APP_DATABASE`       | no       | `web/database/app.db`                | Path override for the SQLite file            |
| `SECURE_COOKIES`     | no       | `false`                              | Set `true` behind HTTPS                      |
| `TRUSTED_PROXY_COUNT`| no       | `0`                                  | Reverse proxy hop count for `X-Forwarded-For`|
| `GUNICORN_WORKERS`   | no       | `2`                                  | Worker count                                 |
| `GUNICORN_THREADS`   | no       | `4`                                  | Threads per worker                           |
| `GUNICORN_TIMEOUT`   | no       | `120`                                | Per-request timeout (AI calls are slow)      |
| `PORT`               | no       | `5000`                               | Container port                               |
| `HOST_PORT`          | no       | `5000`                               | Host port when using `docker compose`        |

Legacy `USER_DATABASE`, `PROMPT_DATABASE`, `QUERY_DATABASE`,
`COMMUNITY_DATABASE`, and `FEEDBACK_DATABASE` env vars are accepted for
backward compatibility but ignored - everything reads from
`app.db`.

## Point Costs

| Action                | Cost (points) |
| --------------------- | ------------- |
| Basic text            | 1.0           |
| Advanced text         | 1.0           |
| Advanced image        | 1.0           |
| Advanced reverse image| 1.0           |
| Prompt refinement     | 0.5           |
| AI title generation   | 0.2           |
| API key removal       | 100           |
| Using a personal key  | 0.0 (free)    |

## Security

- CSRF tokens on every POST (form field or `X-CSRFToken` header)
- Sessions stored server-side with explicit revoke (`/sessions/revoke`)
- Session token validated on every authenticated request
- `secure` cookie flag toggled by `SECURE_COOKIES`
- Hashed passwords (`werkzeug.security.generate_password_hash`)
- DOMPurify sanitization on all AI-rendered HTML
- SQLAlchemy parametrized queries throughout (no string interpolation)

## Production Deployment

Behind a reverse proxy:

```nginx
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Set `TRUSTED_PROXY_COUNT=1` (or higher) so Flask trusts the forwarded
headers, `SECURE_COOKIES=true` so the session cookie is HTTPS-only, and
a strong `SECRET_KEY`.

For PostgreSQL: provision a database, set
`DATABASE_URL=postgresql+psycopg://user:pass@host/dbname`, then run
`alembic upgrade head` once (the app runs migrations on first boot, but
you may want to do it explicitly during deploys).

## Project Layout

```
.
|-- alembic.ini
|-- docker-compose.yml
|-- Dockerfile
|-- migrations/            # Alembic
|   |-- env.py
|   |-- legacy_import.py   # one-shot data import from legacy DBs
|   `-- versions/
|-- requirements.txt
`-- web/
    |-- app.py             # Flask app factory
    |-- routes.py          # URL routes
    |-- models.py          # Domain functions (SQLAlchemy)
    |-- db/                # SQLAlchemy engine + declarative models
    |   |-- __init__.py
    |   `-- models.py
    |-- static/            # CSS, JS, icons
    |-- templates/         # Jinja templates
    `-- database/          # SQLite volume (app.db, .gitkeep)
```

## License

MIT - see `LICENSE`.
