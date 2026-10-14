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

在同一個 Wi-Fi 下用手機開 `http://<電腦 IP>:8000`（啟動時加 `--host 0.0.0.0`）。

- [ ] 正面／背面可切換；正面 8 個、背面 8 個區塊都可點，點到會變綠並顯示名稱
- [ ] 三題沒選完「看動作」不可按；「上一步」保留已選部位
- [ ] 結果頁三種狀態：有 AI 說明 / 無 AI 說明（通用文字）/ 就醫提示（只有 gentle 動作）
- [ ] 每張卡片有名稱、英文名、建議時長、步驟、注意事項；有 AI 時有「為什麼適合你」
- [ ] 右上角紀錄：新增、回看、清除都正常；最多 20 筆
- [ ] 頁面底部每個畫面都看得到免責聲明
- [ ] 關掉伺服器重新整理：顯示錯誤訊息與「重試」按鈕
- [ ] 無橫向捲動，字體在 iPhone SE 寬度（375px）仍可讀
