# KLTN — AQI Agent

Text-to-SQL chat assistant for Vietnam air-quality data. A Next.js frontend talks to a FastAPI agent that plans, generates, validates, and executes SQL against Postgres, with OpenSearch for example/schema retrieval and Redis for state.

## Stack

- **Frontend** — Next.js 14 (`frontend/`)
- **Agent** — FastAPI + LangGraph (`services/aqi_agent/`)
- **Libs** — shared Python workspace packages (`libs/`: `pg`, `lite_llm`, `opensearch`, `logger`, `base`)
- **Infra** — Postgres, OpenSearch, Redis, LiteLLM proxy (via Docker Compose)

## Quick start

```bash
# 1. Provide secrets — copy & fill in
cp .env.example .env   # or create .env with POSTGRES__USERNAME, POSTGRES__PASSWORD,
                       # POSTGRES__DB, OPENSEARCH_INITIAL_ADMIN_PASSWORD,
                       # LITELLM__TOKEN, GEMINI_API_KEY1, OPENAI_API_KEY

# 2. Bring everything up
docker compose up -d --build

# 3. Open the app
open http://localhost:3000
```

The first time you launch, click **Sign up** to create an account; subsequent visits show your past conversations.

## Service ports

| Service             | URL                                  |
| ------------------- | ------------------------------------ |
| Frontend            | http://localhost:3000                |
| AQI Agent API       | http://localhost:3334                |
| Postgres            | localhost:15432                      |
| OpenSearch          | http://localhost:19200               |
| OpenSearch Dashboards | http://localhost:5601              |
| Redis / RedisInsight | localhost:6379 / http://localhost:5540 |
| LiteLLM proxy       | http://localhost:9510                |

## Project layout

```
frontend/                 Next.js UI (chat, auth, history)
services/aqi_agent/       FastAPI service + LangGraph pipeline
libs/                     Python workspace packages (uv workspace)
script/                   One-off scripts (seeding, batch tests, debugging)
csv/                      Test cases & seed data
init_db/                  DB bootstrap
devops/Dockerfile         Generic Python service image
docker-compose.yml        Local stack
```

## Auth & history

- `POST /v1/auth/register` — `{ email, password, full_name? }`
- `POST /v1/auth/login` — `{ email, password }`
- `GET  /v1/conversations?email=...`
- `GET  /v1/conversations/{id}/messages?email=...`
- `POST /v1/aqi_agent` — `{ question, conversation_id, user_id }` (`user_id` is the email)

Passwords are hashed with bcrypt. The frontend persists the logged-in email in `localStorage` and loads conversations + messages from Postgres on login.

## Development

```bash
# Watch backend logs
docker logs -f kltn-aqi_agent_service-1

# Rebuild after changing pyproject.toml (lockfile)
uv lock
docker compose up -d --build aqi_agent_service

# Frontend dev (outside docker)
cd frontend && npm install && npm run dev
```

The backend bind-mounts `services/aqi_agent/` and `libs/`, so Python source edits hot-reload via uvicorn `--reload`. Dependency changes require a rebuild.
