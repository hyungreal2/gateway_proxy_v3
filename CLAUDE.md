# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`gateway_proxy_v3` is a FastAPI-based HTTP proxy that bridges the **Anthropic messages API** format to the **OpenAI chat completions API** format, allowing Claude Code (and other Anthropic-compatible clients) to use a self-hosted [vLLM](https://github.com/vllm-project/vllm) backend.

## Commands

### Install dependencies
<!-- [Rimi] conda + myenv is the working environment. pydantic-settings must be installed separately because pydantic v2 no longer bundles BaseSettings. -->
```bash
# Inside the myenv conda environment:
conda run -n myenv pip install -r requirements.txt
conda run -n myenv pip install -e .
```

### Run the server (development)
<!-- [Rimi] Running python main.py directly from src/gateway_proxy/ still works because of bare imports, but the preferred way is via the conda script below which uses the installed package. -->
```bash
bash scripts/run_server.sh   # conda run -n myenv, 4 uvicorn workers on port 8080
```

### Run tests
<!-- [Rimi] Always run this after every edit to src/. The script wraps pytest inside the myenv conda environment. -->
```bash
bash scripts/run_tests.sh                                        # all tests
bash scripts/run_tests.sh tests/test_gateway_proxy.py::test_messages  # single test
bash scripts/run_tests.sh --cov=src                              # with coverage
```

### Docker
<!-- [Rimi] build_docker.sh builds the image and exports it as a .tar file for transfer to another host. No sudo needed — user is in the docker group. -->
```bash
bash scripts/build_docker.sh           # builds gateway-proxy:latest → gateway-proxy-latest.tar
bash scripts/build_docker.sh v1.0      # custom tag → gateway-proxy-v1.0.tar

# On the target host:
docker load -i gateway-proxy-latest.tar

# Run (docker or podman):
bash scripts/run_docker.sh             # uses GATEWAY_URL env var, defaults to localhost:8080
bash scripts/run_podman.sh
VLLM_BASE_URL=http://192.168.1.10:8000 bash scripts/run_docker.sh
```

### Test the running server with curl
<!-- [Rimi] test_curl.sh covers all message/model types: simple, multi-turn, block content, system prompt, temperature, tool use, single embedding, batch embedding. -->
```bash
bash scripts/test_curl.sh                    # all tests
bash scripts/test_curl.sh messages_tools     # single test by name
GATEWAY_URL=http://192.168.1.10:8080 bash scripts/test_curl.sh
```

## Architecture

The gateway runs as a single FastAPI app (`src/gateway_proxy/main.py`) with two endpoints:

- `POST /v1/messages` — Anthropic-format chat endpoint. Converts the incoming Anthropic `MessageRequest` → OpenAI payload via `converters.anthropic_to_openai_messages`, forwards to vLLM, then converts the OpenAI response back to Anthropic format via `converters.openai_to_anthropic`.
- `POST /v1/embeddings` — Passes embedding requests through to vLLM unchanged.

### Key modules

| File | Role |
|---|---|
| `main.py` | FastAPI app, route handlers, wires together all modules |
| `converters.py` | Pure functions for Anthropic ↔ OpenAI message format translation |
| `models.py` | Pydantic request models (`MessageRequest`, `EmbeddingRequest`) |
| `vllm_client.py` | `VLLMClient` — async httpx wrapper for vLLM's `/v1/chat/completions` and `/v1/embeddings` |
| `config.py` | `Settings` (pydantic-settings `BaseSettings`): `VLLM_BASE_URL`, `VLLM_API_KEY`, `LOG_DIR` env vars |
| `logger.py` | Stdlib logger with stdout handler + `RotatingFileHandler` writing to `LOG_DIR/gateway.log` |

### Configuration (environment variables)

| Variable | Default | Description |
|---|---|---|
| `VLLM_BASE_URL` | `http://localhost:8080` | Base URL of the vLLM server |
| `VLLM_API_KEY` | `None` | Optional API key sent to vLLM |
| `LOG_DIR` | `logs` | Directory for log files (relative to cwd; mount a host volume here in Docker) |

### Logging
<!-- [Rimi] logger.py writes to both stdout and a rotating file. The logs/ directory at the project root is bind-mounted into the container at /app/logs by the run scripts. Log files rotate at 10 MB, keeping 5 backups. -->

Request input and response output are logged at INFO level in `main.py`:
- Before forwarding: `request model=<model> messages=<openai_msgs>`
- After response: `response <result>`

Log files appear at `logs/gateway.log` on the host when using `run_docker.sh` or `run_podman.sh`.

### Import path note
<!-- [Rimi] Bare imports (from models import ...) were replaced with relative imports (from .models import ...) so the package works correctly when installed and imported as gateway_proxy.main. Running python main.py directly from src/gateway_proxy/ still works. -->

All intra-package imports use relative form (`from .models import ...`). The package must be installed (`pip install -e .`) for tests and uvicorn to resolve `gateway_proxy.main`.

### Pydantic v2 note
<!-- [Rimi] The Docker image and myenv both install pydantic v2. BaseSettings was removed from pydantic core in v2 and moved to the separate pydantic-settings package. config.py imports from pydantic_settings, and requirements.txt includes pydantic-settings. -->

`config.py` imports `BaseSettings` from `pydantic_settings`, not `pydantic`. This is required for pydantic v2 compatibility.

### Testing approach

Tests use `fastapi.testclient.TestClient` (synchronous). The `mock_vllm` fixture in `conftest.py` monkey-patches `main.vllm` with a `MockVLLM` instance so no real vLLM server is needed.

### Converter behaviour note
<!-- [Rimi] converters.py operates on plain dicts only. main.py must call [m.dict() for m in req.messages] before passing to anthropic_to_openai_messages — passing Pydantic Message objects directly causes a TypeError. -->

`converters.anthropic_to_openai_messages` expects a list of plain dicts, not Pydantic model instances. `main.py` converts with `[m.dict() for m in req.messages]` before calling the converter.
