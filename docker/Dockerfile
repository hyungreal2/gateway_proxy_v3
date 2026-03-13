FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY requirements.txt .
COPY src src

RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir -e .

ENV VLLM_BASE_URL=http://localhost:8080

CMD ["uvicorn","gateway_proxy.main:app","--host","0.0.0.0","--port","8080"]
