FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY oversight ./oversight
RUN uv sync --frozen --no-dev

COPY fixtures ./fixtures
COPY scripts ./scripts

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "oversight.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
