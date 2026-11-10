# 🍜 NCCU Eats

整理國立政治大學周邊美食的靜態網站。可依分類、區域篩選店家，並有把多間店串成路線的主題指南。

## 特色

- **內容與網頁分離**：每間店是一個 Markdown 檔，`build.py` 自動產生整個網站。
- **給 AI 的規則書**：[`AGENTS.md`](./AGENTS.md) 寫清楚格式、命名、風格與檢查清單，AI 讀完就能接手新增內容。
- **自動驗證**：分類、區域、slug、指南引用的店家寫錯，建置會直接報錯。
- **零依賴**：只用 Python 標準函式庫與原生 HTML／CSS／JS。

## 使用方式

```bash
python build.py                         # 驗證內容並產生網站到 docs/
python build.py check                   # 只驗證，不產生
python build.py new restaurant <slug>   # 從範本建立新店家
python build.py new guide <slug>        # 從範本建立新指南
```

## 部署

GitHub → Settings → Pages → Source 選 `Deploy from a branch`，Branch 選 `main`、資料夾選 `/docs`。

## 資料說明

店家資訊整理自網路文章與親自造訪，來源列在每間店頁面底部。營業時間與價格可能變動，出發前請再確認。
