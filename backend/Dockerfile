FROM public.ecr.aws/docker/library/python:3.13.16-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
RUN useradd --uid 10001 --create-home app
COPY --chown=app:app . .
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
