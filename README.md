# LLM Gateway

A lightweight FastAPI proxy that bridges the **Anthropic Messages API** format to the **OpenAI Chat Completions API** format, letting Claude Code (and other Anthropic-compatible clients) talk to a self-hosted [vLLM](https://github.com/vllm-project/vllm) backend.

```
Claude Code  →  /v1/messages (Anthropic format)  →  Gateway  →  /v1/chat/completions (OpenAI format)  →  vLLM
```

---

## Requirements

- Python 3.10+
- [Conda](https://docs.conda.io/) with a `myenv` environment
- Docker (user must be in the `docker` group)
- A running [vLLM](https://github.com/vllm-project/vllm) server

---

## Installation

```bash
conda run -n myenv pip install -r requirements.txt
conda run -n myenv pip install -e .
```

---

## Configuration

All configuration is via environment variables:

| Variable | Default | Description |
|---|---|---|
| `VLLM_BASE_URL` | `http://localhost:8080` | URL of your vLLM server |
| `VLLM_API_KEY` | _(none)_ | Optional API key for vLLM |
| `LOG_DIR` | `logs` | Directory where `gateway.log` is written |

---

## Running

### Local (development)

```bash
bash scripts/run_server.sh
```

Starts 4 uvicorn workers on port `8080` inside the `myenv` conda environment.

### Docker

```bash
# Build the image and export as a .tar for transfer
bash scripts/build_docker.sh           # → gateway-proxy-latest.tar
bash scripts/build_docker.sh v1.0      # → gateway-proxy-v1.0.tar

# Run with Docker
VLLM_BASE_URL=http://<vllm-host>:<port> bash scripts/run_docker.sh

# Run with Podman
VLLM_BASE_URL=http://<vllm-host>:<port> bash scripts/run_podman.sh
```

> **Note:** Inside the container, `localhost` refers to the container itself — always provide the host machine's IP or hostname as `VLLM_BASE_URL`.

Logs are written to `logs/gateway.log` on the host (bind-mounted into the container).

### Transfer to another host

```bash
# On source host — build and save:
bash scripts/build_docker.sh

# Copy the .tar to the target host, then load:
docker load -i gateway-proxy-latest.tar

# Run on the target host:
VLLM_BASE_URL=http://<vllm-host>:<port> docker run \
    -e VLLM_BASE_URL \
    -v ./logs:/app/logs \
    -p 8080:8080 \
    gateway-proxy:latest
```

---

## API Endpoints

### `POST /v1/messages`

Accepts Anthropic-format requests and forwards them to vLLM.

**Request body:**
```json
{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "tools": []
}
```

Content can be a plain string or an Anthropic content block array:
```json
"content": [{"type": "text", "text": "Hello!"}]
```

**Response:**
```json
{
  "role": "assistant",
  "content": [{"type": "text", "text": "Hi there!"}]
}
```

---

### `POST /v1/embeddings`

Passes embedding requests through to vLLM unchanged.

**Request body:**
```json
{
  "model": "intfloat/multilingual-e5-large-instruct",
  "input": "Text to embed"
}
```

`input` can also be a list of strings for batch embedding.

---

### `GET /health`

Returns `{"status": "ok"}` when the gateway is running.

---

## Testing

### Unit tests

```bash
bash scripts/run_tests.sh                                        # all tests
bash scripts/run_tests.sh tests/test_gateway_proxy.py::test_messages  # single test
bash scripts/run_tests.sh --cov=src                              # with coverage
```

Tests use a `MockVLLM` fixture — no real vLLM server required.

### Live curl tests

With a gateway server running (`bash scripts/run_server.sh` or via Docker):

```bash
bash scripts/test_curl.sh                        # all tests
bash scripts/test_curl.sh messages_tools         # single test by name
GATEWAY_URL=http://192.168.1.10:8080 bash scripts/test_curl.sh
```

Available test names:

| Name | What it tests |
|---|---|
| `health` | `GET /health` |
| `messages_simple` | Single user message |
| `messages_multi_turn` | Multi-turn conversation |
| `messages_block_content` | Anthropic content-block array format |
| `messages_system_prompt` | System role message |
| `messages_temperature` | Custom temperature |
| `messages_tools` | Tool / function calling |
| `embeddings_single` | Single string embedding |
| `embeddings_batch` | Batch list of strings |

---

## Logs

Request and response payloads are logged at INFO level to both stdout and `logs/gateway.log`. The log file rotates at 10 MB, keeping 5 backups.

```
2026-03-13 00:34:32,835 INFO gateway_proxy.main request model=Qwen/... messages=[...]
2026-03-13 00:34:32,836 INFO gateway_proxy.main response {'role': 'assistant', ...}
```
