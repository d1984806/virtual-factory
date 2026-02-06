# Robo Desktop TW

桌面投資工具（僅提供分析、建議與報表，不做自動下單）。

## 功能
- Dashboard：總資產、投入、未實現損益、近 30 日資產變化。
- Trades：新增/刪除/編輯交易，表格排序/篩選。
- Holdings：即時計算持股、均價、成本、損益（加權平均/FIFO）。
- DCA：定期定額建議，支援滑價與提醒文字複製。
- Prices：價格來源切換（Mock/TWSE），快取至 `data/price_cache.json`。
- Rebalance：設定目標配置與風控，計算建議買賣股數。
- Reports：一鍵匯出 Excel 報表至 `exports/`。
- CSV：交易紀錄匯入/匯出、欄位對應與錯誤列報告。
- Logs：顯示 `logs/app.log` 近期紀錄。

## 需求
- Python 3.11
- Windows 10/11（建議）

## 安裝
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 執行
```bash
python -m robo_app
```

首次啟動會自動建立 `data/`、`exports/`、`logs/` 並初始化 SQLite（`data/robo.db`）。

## 架構
- `robo_app/core`: 資料庫、模型、服務與價格來源。
- `robo_app/ui`: Qt 介面與各功能頁籤。

## 注意
- 僅提供建議與報表，不進行任何自動下單。
