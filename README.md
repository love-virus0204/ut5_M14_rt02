# RT 外觀抽驗記錄表 API（Flask）

最小可用 API：接受前端表單，寫入 `records.csv`，並提供最近 50 筆倒序查詢。

## 部署（Render / Railway）
1. 建新專案，選 Python。
2. 環境變數（可選）：
   - `CSV_FILE`：預設 `records.csv`
3. Build 指令：`pip install -r requirements.txt`
4. Start 指令（已有 `Procfile`）：自動使用 `web: gunicorn app:app`
5. 部署完成後，取得 `https://<your-host>/`

## 端點
- `GET /health`
- `GET /api/records?date=YYYY-MM-DD&shift=A&limit=50`
- `POST /api/records`（JSON）
  - 必填：`date_shift`, `inspector`, `part_no`, `qty`
  - 伺服器會自動組合 `lot_full`（也可自行傳）
  - 若同 `date_shift+part_no+lot_full` 但不同 `inspector`，回 `409`。可用 `POST /api/records?force=1` 強制寫入。

## 與前端整合
在 `form.html` 送出時，將 action 指到你的 API，例如：
```html
<form id="recordForm" method="post" action="https://<your-host>/api/records">
```
或使用 JS：
```js
fetch('https://<your-host>/api/records', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
})
```
