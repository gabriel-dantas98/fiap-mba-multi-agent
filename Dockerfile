# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:0.5-python3.13-bookworm-slim AS base

WORKDIR /app
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 UV_PYTHON_DOWNLOADS=never

# Frontend build stage (no-op if no package.json found)
FROM node:20-bookworm-slim AS frontend-build
WORKDIR /work
COPY apps ./apps
RUN set -e; \
    for pkg in $(find apps -name package.json -not -path '*/node_modules/*'); do \
      dir=$(dirname "$pkg"); \
      echo "Building $dir"; \
      (cd "$dir" && npm ci && npm run build); \
    done

FROM base AS runtime
COPY pyproject.toml uv.lock ./
COPY homepage/ homepage/
COPY apps/ apps/
COPY --from=frontend-build /work/apps ./apps
RUN uv sync --frozen --no-dev

ENV MBA_APPS_ROOT=/app/apps
EXPOSE 8080
CMD ["uv", "run", "--no-dev", "uvicorn", "homepage.main:app", "--host", "0.0.0.0", "--port", "8080"]
