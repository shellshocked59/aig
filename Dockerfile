# Development images: dependencies live in the image, source is mounted by Compose.
FROM node:24-bookworm-slim AS web
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY frontend ./frontend
COPY scripts ./scripts
EXPOSE 5173
CMD ["npm", "run", "dev"]

FROM web AS frontend-build
ARG PUBLIC_API_BASE_URL=https://api.agentstrategy.online
ARG APP_REVISION=unknown
ENV PUBLIC_API_BASE_URL=$PUBLIC_API_BASE_URL
RUN npm run build \
    && node -e "require('fs').writeFileSync('dist/release.json', JSON.stringify({revision: process.env.APP_REVISION}) + '\\n')"

FROM scratch AS frontend-export
COPY --from=frontend-build /app/dist/ /

FROM python:3.11-slim-bookworm AS python-base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
RUN python -m venv "$VIRTUAL_ENV"
COPY pyproject.toml README.md LICENSE .env.example ./
COPY backend ./backend
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "aig.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

FROM python-base AS api-runtime
ARG APP_REVISION=unknown
ENV AIG_RELEASE_SHA=$APP_REVISION
LABEL org.opencontainers.image.revision=$APP_REVISION
RUN python -m pip install ".[infrastructure]"
USER 10001:10001

FROM python-base AS api
RUN python -m pip install -e ".[test,infrastructure]"
COPY tests ./tests
COPY frontend ./frontend
COPY scripts ./scripts
EXPOSE 8000
# Each process owns one in-memory game; never run multiple workers.
CMD ["python", "-m", "uvicorn", "aig.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
