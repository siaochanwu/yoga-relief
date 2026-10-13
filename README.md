# Yoga Relief

點選人體圖上的酸痛部位、回答三題，取得緩解瑜伽動作與個人化說明的手機網頁。

## 安裝與執行

```bash
uv sync
uv run uvicorn yoga_relief.main:app --reload
```

打開 http://127.0.0.1:8000 。

## 測試

```bash
uv run pytest
uv run ruff check .
```

## 重新產生 AI 說明（advice.json）

需要 `.env` 裡的 `ANTHROPIC_API_KEY`（複製 `.env.example`）。

```bash
uv run python scripts/build_advice.py          # 只補缺的、過期的
uv run python scripts/build_advice.py --force  # 全部重產
```

## 手機實機驗收清單

見本檔最下方（Task 12 補上）。
