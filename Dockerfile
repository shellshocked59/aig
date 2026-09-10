# Development images: dependencies live in the image, source is mounted by Compose.
FROM node:24-bookworm-slim AS web
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY frontend ./frontend
COPY scripts ./scripts
EXPOSE 5173
CMD ["npm", "run", "dev"]

FROM python:3.11-slim-bookworm AS api
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md LICENSE .env.example ./
COPY backend ./backend
RUN python -m pip install -e ".[test,infrastructure]"
COPY tests ./tests
COPY frontend ./frontend
COPY scripts ./scripts
EXPOSE 8000
# Each process owns one in-memory game; never run multiple workers.
CMD ["python", "-m", "uvicorn", "aig.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
