#!/usr/bin/env bash

# Usage:
#   bash scripts/test_curl.sh                   # run all tests
#   bash scripts/test_curl.sh health            # run a single test by name
#
# Override server URL:
#   GATEWAY_URL=http://localhost:9000 bash scripts/test_curl.sh

set -e

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"
TARGET="${1:-all}"

PASS=0
FAIL=0

run_test() {
    local name="$1"
    local method="$2"
    local path="$3"
    local body="$4"

    if [[ "$TARGET" != "all" && "$TARGET" != "$name" ]]; then
        return
    fi

    echo "========================================"
    echo "TEST: $name"
    echo "----------------------------------------"

    if [[ -z "$body" ]]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "${GATEWAY_URL}${path}")
    else
        echo "REQUEST BODY:"
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
        echo "----------------------------------------"
        response=$(curl -s -w "\n%{http_code}" -X "$method" "${GATEWAY_URL}${path}" \
            -H "Content-Type: application/json" \
            -d "$body")
    fi

    http_code=$(echo "$response" | tail -1)
    body_out=$(echo "$response" | head -n -1)

    echo "RESPONSE ($http_code):"
    echo "$body_out" | python3 -m json.tool 2>/dev/null || echo "$body_out"

    if [[ "$http_code" == 2* ]]; then
        echo "RESULT: PASS"
        ((PASS++)) || true
    else
        echo "RESULT: FAIL"
        ((FAIL++)) || true
    fi
    echo ""
}

# ── Health ────────────────────────────────────────────────────────────────────

run_test "health" GET "/health"

# ── /v1/messages: simple string content ──────────────────────────────────────

run_test "messages_simple" POST "/v1/messages" '{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {"role": "user", "content": "Hello, who are you?"}
  ]
}'

# ── /v1/messages: multi-turn conversation ────────────────────────────────────

run_test "messages_multi_turn" POST "/v1/messages" '{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {"role": "user",      "content": "My name is Alice."},
    {"role": "assistant", "content": "Nice to meet you, Alice!"},
    {"role": "user",      "content": "What is my name?"}
  ]
}'

# ── /v1/messages: block content (Anthropic content array format) ─────────────

run_test "messages_block_content" POST "/v1/messages" '{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "What is 2 + 2?"}
      ]
    }
  ]
}'

# ── /v1/messages: system prompt via leading message ──────────────────────────

run_test "messages_system_prompt" POST "/v1/messages" '{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant that responds only in JSON."},
    {"role": "user",   "content": "Give me a JSON object with keys name and age."}
  ]
}'

# ── /v1/messages: custom temperature ─────────────────────────────────────────

run_test "messages_temperature" POST "/v1/messages" '{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {"role": "user", "content": "Tell me a joke."}
  ],
  "temperature": 1.0
}'

# ── /v1/messages: tool use ────────────────────────────────────────────────────

run_test "messages_tools" POST "/v1/messages" '{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {"role": "user", "content": "What is the weather in Seoul?"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {"type": "string", "description": "City name"}
          },
          "required": ["city"]
        }
      }
    }
  ]
}'

# ── /v1/embeddings: single string ────────────────────────────────────────────

run_test "embeddings_single" POST "/v1/embeddings" '{
  "model": "intfloat/multilingual-e5-large-instruct",
  "input": "The quick brown fox jumps over the lazy dog."
}'

# ── /v1/embeddings: batch (list of strings) ──────────────────────────────────

run_test "embeddings_batch" POST "/v1/embeddings" '{
  "model": "intfloat/multilingual-e5-large-instruct",
  "input": [
    "First sentence to embed.",
    "Second sentence to embed."
  ]
}'

# ── Summary ───────────────────────────────────────────────────────────────────

if [[ "$TARGET" == "all" ]]; then
    echo "========================================"
    echo "SUMMARY: $PASS passed, $FAIL failed"
    echo "========================================"
    [[ $FAIL -eq 0 ]]
fi
