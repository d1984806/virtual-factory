# Godot MVP 原型

此資料夾提供最小可玩原型的 Godot 專案骨架，載入 JSON/CSV 以驅動「開頭 UI → 建角 → 進城 → 接任務 → 戰鬥 → 成長」流程的第一步。

## 專案結構
- `project.godot`：Godot 專案設定
- `scenes/main.tscn`：主場景
- `scripts/main.gd`：啟動時載入資料並輸出到主控台
- `data/角色.json`：角色資料範例
- `data/任務.csv`：任務資料範例

## 執行方式
1. 用 Godot 4 開啟此資料夾。
2. 執行專案後，主控台會列出載入的角色與任務資料。
3. 下一步可在此場景接上 UI 與流程。
