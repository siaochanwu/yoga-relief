# 正式環境映像：uv 安裝依賴、非 root 執行、以 uvicorn 提供服務。
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv

# 先只裝依賴，程式碼改動時這一層可以沿用快取
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

# 不用 root 跑：就算程式被攻破，也只能動到 /app 以外的唯讀內容
RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app

ENV PORT=8000
EXPOSE 8000
# Render、Railway 等平台會以 $PORT 指定要聽的埠；本機沒設就是 8000
CMD ["sh", "-c", "exec /app/.venv/bin/uvicorn yoga_relief.main:app --host 0.0.0.0 --port ${PORT}"]
