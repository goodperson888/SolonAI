# Docker Frontend/Backend Test Guide

## Purpose

This document records the minimum Docker-based frontend/backend integration test flow for the Solon AI project.

It covers:

- Starting the full stack with Docker Compose
- Verifying frontend and backend health
- Testing representative REST API endpoints
- Testing chat SSE streaming
- Checking persisted chat sessions and messages
- Reviewing logs and cleaning up containers

## Services

The current Docker Compose stack includes:

- `web`: Next.js frontend, exposed on `http://localhost:3000`
- `api`: FastAPI backend, exposed on `http://localhost:8000`
- `db`: PostgreSQL
- `redis`: Redis

## Start The Stack

```bash
docker compose up --build -d
docker compose ps
```

Expected result:

- `web`, `api`, `db`, `redis` are all `Up`

## Basic Health Checks

Check frontend:

```bash
curl -I http://localhost:3000
```

Expected result:

- HTTP `200 OK`

Check backend docs:

```bash
curl -I http://localhost:8000/docs
```

Expected result:

- HTTP `200 OK`

Check backend health:

```bash
curl -s http://localhost:8000/health
```

Expected result:

```json
{"status":"healthy","redis":"connected"}
```

Check AI chat health:

```bash
curl -s http://localhost:8000/api/v1/chat/health
```

Expected result:

```json
{"status":"healthy","service":"ai-chat"}
```

## Verify Container-to-Container Connectivity

Check backend from inside `api`:

```bash
docker compose exec -T api python - <<'PY'
import urllib.request
for url in ['http://localhost:8000/docs', 'http://localhost:8000/openapi.json']:
    with urllib.request.urlopen(url, timeout=10) as r:
        print(url, r.status)
PY
```

Check backend from inside `web`:

```bash
docker compose exec -T web node -e "Promise.all(['http://api:8000/docs','http://api:8000/openapi.json'].map(async (u)=>{ const r=await fetch(u); console.log(u, r.status); }))"
```

Expected result:

- Both checks return status `200`

## Representative API Smoke Tests

### DeFi Overview

```bash
curl -s http://localhost:8000/api/v1/defi/overview
```

Expected result:

- JSON payload with `prices`, `yields`, `best_opportunities`, `cache`

### Chat Session List

```bash
curl -s 'http://localhost:8000/api/v1/chat/sessions?wallet_address=test_wallet&limit=5'
```

Expected result:

- Usually `[]` for a new wallet

## Test Normal Chat Request

```bash
curl -s -X POST http://localhost:8000/api/v1/chat/message \
  -H 'Content-Type: application/json' \
  -d '{"message":"你好","session_id":"docker-test-session"}'
```

Expected result:

- JSON response containing:
  - `reply`
  - `intent`
  - `intent_params`
  - `session_id`

Example:

```json
{
  "reply": "你好！...",
  "intent": "chat",
  "intent_params": {},
  "session_id": "docker-test-session",
  "data": null
}
```

## Test SSE Streaming Chat

```bash
curl -N -s -X POST http://localhost:8000/api/v1/chat/message/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"你好，简单介绍一下你自己","session_id":"docker-sse-test-session"}'
```

Expected event sequence:

- `session`
- `agent_status` for intent start
- `agent_status` for intent done
- `agent_status` for explanation start
- one or more `token`
- `agent_status` for explanation done
- `data`
- `done`

This verifies the frontend AI page can consume:

- session creation
- agent progress updates
- token streaming
- final completion event

## Verify Chat Persistence

Check session list:

```bash
curl -s 'http://localhost:8000/api/v1/chat/sessions?wallet_address=guest:docker-test-session&limit=5'
```

Expected result:

- The created session is returned

Check message list:

```bash
curl -s 'http://localhost:8000/api/v1/chat/sessions/docker-test-session/messages?limit=20'
```

Expected result:

- The user message and assistant reply are both returned

## Log Inspection

View recent API logs:

```bash
docker compose logs --tail=120 api
```

View recent web logs:

```bash
docker compose logs --tail=120 web
```

Follow API logs:

```bash
docker compose logs -f api
```

What to look for in API logs:

- database initialization success
- prompt loading success
- session creation
- message insertions
- agent execution start and completion
- HTTP `200 OK` responses for tested endpoints

## Stop And Cleanup

Stop services:

```bash
docker compose down
```

Stop services and remove volumes:

```bash
docker compose down -v
```

Use `-v` only when you intentionally want to remove PostgreSQL and Redis persisted data.

## Validated Result In This Repository

This workflow has already been verified in the current repository state.

Confirmed working:

- Docker Compose startup
- frontend on `localhost:3000`
- backend docs and health on `localhost:8000`
- container-to-container connectivity
- DeFi overview API
- normal chat API
- SSE streaming chat API
- chat session persistence
- chat message persistence

## Notes

- If `curl localhost` fails inside a restricted sandbox, retry from the host or use an approved elevated command.
- If AI replies fail, first check external model credentials such as `DOUBAO_API_KEY`.
- If DeFi data is incomplete, inspect RPC/network access from the API container.
