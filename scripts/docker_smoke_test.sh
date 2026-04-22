#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ "${1:-}" == "--up" ]]; then
  docker compose up -d --build
fi

echo "== Docker services =="
docker compose ps

echo
echo "== API / Web smoke test =="
docker compose exec -T api python - <<'PY'
import json
import urllib.request


def fetch(url: str, *, data: dict | None = None, timeout: int = 60):
    payload = None
    headers = {}
    if data is not None:
        payload = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode()
        print(f"[OK] {url} -> {response.status}")
        print(body[:600])
        print("-" * 80)


fetch("http://127.0.0.1:8000/health")
fetch("http://127.0.0.1:8000/api/v1/chat/health")
fetch("http://127.0.0.1:8000/api/v1/assets/vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg")
fetch("http://127.0.0.1:8000/api/v1/defi/overview", timeout=120)
fetch(
    "http://127.0.0.1:8000/api/v1/transactions/history/vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg?limit=3",
    timeout=120,
)
fetch(
    "http://127.0.0.1:8000/api/v1/chat/message",
    data={
        "message": "帮我概括一下我这个钱包的资产情况",
        "wallet_address": "vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg",
        "session_id": "docker-smoke-test",
    },
    timeout=120,
)
fetch("http://web:3000", timeout=30)
PY

echo
echo "Smoke test passed."
