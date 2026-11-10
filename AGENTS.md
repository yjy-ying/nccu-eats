# AGENTS.md — NCCU Eats

> 這份文件是給 AI 協作者（Claude、ChatGPT、Codex、Gemini…）看的專案說明書。
> **在新增或修改任何檔案之前，請先完整讀完這份文件。** 這裡的規則優先於你自己的習慣。

---

## 1. 專案目的

「NCCU Eats」是一個整理**國立政治大學（台北市文山區）周邊美食**的靜態網站，給政大學生、新生與來訪的人查詢。

- 讀者：政大學生，特別是剛入學、還不熟環境的新生。
- 核心問題：「下課了，在政大附近要吃什麼？」
- 網站要做到：可以依**分類**、**區域**篩選店家；每間店有獨立介紹頁；另有「主題指南」把多間店串成一條路線或主題。
- 這個專案的重點不是一次做完，而是**用同一套規則持續新增店家與指南**。

## 2. 技術規則（不可違反）

| 項目 | 規則 |
|---|---|
| 語言 | Python 3（只用標準函式庫），HTML、CSS、原生 JavaScript |
| 禁止 | 不可引入 React、Vue、Tailwind、jQuery、npm 套件或任何需要安裝的 Python 套件 |
| 建置 | 執行 `python build.py`，它會驗證 `content/` 並產生網站到 `docs/` |
| 部署 | GitHub Pages，來源設定為 `main` 分支的 `/docs` 資料夾 |
| 外部資源 | 只允許 Google Fonts（Noto Sans TC、Noto Serif TC） |

## 3. 目錄結構與編譯路徑規範

```
nccu-eats/
├── AGENTS.md              ← 本文件：給 AI 的專案規則（唯一的規則來源）
├── CLAUDE.md              ← 只寫一行，指向 AGENTS.md
├── README.md              ← 給人看的簡介與使用方式
├── build.py               ← 驗證 + 產生網站的腳本
├── content/               ← ✏️ 所有內容都只寫在這裡（純 Markdown，無 HTML/CSS）
│   ├── restaurants/       ← 一間店 = 一個 .md 檔
│   └── guides/            ← 一篇主題指南 = 一個 .md 檔
├── templates/             ← 新增內容時複製的空白範本
│   ├── restaurant.md
│   └── guide.md
├── assets/                ← 共用樣式與腳本
│   ├── style.css
│   └── app.js
└── docs/                  ← ⚠️ 唯讀！所有編譯/發布後的 HTML 都輸出於此，禁止手動編輯
```

**最重要的一條：你只能修改 `content/`、`templates/`、`assets/`、`build.py`。`docs/` 內的 HTML 與資源，嚴禁手動新增、修改或複製。它必須 100% 由 `build.py` 重新編譯產生。**

## 4. 命名規則

- 檔名 = `slug` + `.md`，例如 `content/restaurants/juicy-bun-burger.md`。
- `slug` 只能用**小寫英文、數字、連字號 `-`**，例如 `lion-egg-crepe`、`ming-chi-douhua`。
- 店名有英文就用英文；沒有就用**拼音**（不用聲調），例如 明池豆花 → `ming-chi-douhua`。
- 指南的 slug 描述主題，例如 `one-day-eating-route`、`late-night-snacks`。
- front matter 裡的 `slug` 必須和檔名完全一致，否則 `build.py` 會報錯。

## 5. 內容類型 A：店家頁（`content/restaurants/*.md`）

### 5.1 Front matter 欄位

檔案開頭用 `---` 包住的設定區。每行格式是 `欄位: 值`。

| 欄位 | 必填 | 說明 / 允許的值 |
|---|---|---|
| `name` | ✅ | 店名，用店家招牌上的正式名稱 |
| `slug` | ✅ | 同檔名 |
| `category` | ✅ | 只能是：`早餐早午餐`、`小吃`、`正餐`、`甜點飲料`、`咖啡廳` |
| `area` | ✅ | 只能是：`正門`、`側門`、`後山`、`校內`、`指南路`、`萬壽路` |
| `price` | ✅ | `$`（150 元內）、`$$`（150–300 元）、`$$$`（300 元以上）、`?`（待確認） |
| `summary` | ✅ | 一句話推薦，**30 字以內**，會顯示在首頁卡片 |
| `address` | ✅ | 完整地址；不知道門牌就寫 `待確認` |
| `hours` | ✅ | 營業時間；不知道就寫 `待確認` |
| `tags` | ✅ | 2–4 個標籤，用半形逗號分隔，例如 `份量大, 適合聚餐` |
| `updated` | ✅ | 最後更新日期，格式 `YYYY-MM-DD` |
| `sources` | ✅ | 資料來源網址，多個用 ` | ` 分隔；親自去吃寫 `親自造訪` |

### 5.2 內文段落（固定順序、固定標題）

```markdown
## 為什麼推薦
（2–3 句，說明這間店的特色與適合什麼情境）

## 必點
- 品項：一句話描述

## 小提醒
- 排隊、付款方式、座位、營業時間不穩定等實用資訊
```

- 三個 `##` 標題**一定要有、順序不能換、文字不能改**。
- 某段資訊不足時，寫 `- 待補：歡迎親自造訪後更新`，不要刪掉標題。

## 6. 內容類型 B：主題指南（`content/guides/*.md`）

| 欄位 | 必填 | 說明 |
|---|---|---|
| `title` | ✅ | 指南標題 |
| `slug` | ✅ | 同檔名 |
| `summary` | ✅ | 一句話說明，30 字以內 |
| `restaurants` | ✅ | 這篇提到的店家 slug，用半形逗號分隔；**每一個都必須存在** |
| `updated` | ✅ | `YYYY-MM-DD` |

- 內文用 `## 小標` 分段，每段介紹一間店時，用 `[[店家slug]]` 連結，例如 `[[juicy-bun-burger]]`。
  `build.py` 會自動把它換成帶店名的連結；寫錯 slug 會報錯。
- front matter 的 `restaurants` 清單必須包含內文所有 `[[...]]` 用到的店。

## 7. 支援的 Markdown 語法與 HTML 風格限制

為了維持全站視覺風格的一致性，並防範安全隱患，我們的建置腳本 `build.py` **僅支援**以下精簡的 Markdown 語法。若在 Markdown 中寫入 HTML 標籤（如 `<div>` 或 `<span>`），建置時 `build.py` 將會報錯並拒絕生成網站。

**⚠️ 禁止行為：**
- **絕對禁止**在 Markdown 內容中直接嵌入 `<div class="...">`、`<p>`、`<span>` 等任何原生 HTML 標籤。
- **絕對禁止**自行引入外部 CSS 框架（如 Tailwind, Bootstrap）或撰寫 inline style。
- 全站的 HTML 結構與 Class 命名習慣（如 `.card`, `.badge`, `.prose`）完全由 `build.py` 和 `assets/style.css` 集中控制。AI 的職責是「純內容提供」，不需且不應參與 HTML 風格設計。

**允許的 Markdown 語法：**
- `## 標題`、`### 小標題`
- 一般段落（段落之間空一行）
- `- 清單項目`
- `> 引言`
- `**粗體**`
- `[文字](網址)`
- `[[店家slug]]`（站內店家連結）

## 8. 寫作風格

- 使用**繁體中文、台灣用語**（例：「份量」不寫「分量」以外的簡體用法，「捷運」不寫「地鐵」）。
- 語氣像**親切的學長姐**：直接、實用、帶一點輕鬆，但不浮誇。不用「絕對」「全台最強」這類誇大詞。
- 每個段落最多 3 句；清單每點一句話。
- 中文與英文、數字之間**加一個半形空格**，例如 `Juicy Bun Burger 的漢堡`、`營業到 23:00`。
- 價錢寫成 `85 元`，不寫 `NT$85`。

## 9. 事實正確性（非常重要）

- **不可捏造**地址、營業時間、價格、菜單品項。不確定就寫 `待確認`。
- 引用網路資料時，在 `sources` 附上網址，並用**自己的話改寫**，不可整段複製文章。
- 不放店家或網路上的照片（版權問題）。網站只用文字與色塊設計。
- 店家若已歇業：不要刪檔，把 `summary` 改為 `（已歇業）原本的推薦文字`，並在「小提醒」註明。

## 10. 視覺風格

整體感覺：**像一張手寫的學生餐廳菜單** —— 米白紙張底色、深色文字、番茄紅點綴、襯線字體標題。

| Token（定義在 `assets/style.css` 的 `:root`） | 用途 |
|---|---|
| `--paper` | 頁面背景（米白） |
| `--card` | 卡片背景 |
| `--ink` / `--muted` | 主要文字 / 次要文字 |
| `--line` | 邊框、分隔線 |
| `--accent` | 番茄紅，用在按鈕、強調、連結 hover |
| `--cat-*` | 各分類標籤顏色 |

- **不可在 HTML 或 CSS 其他地方寫死色碼**，一律使用上面的 CSS 變數。
- 新增分類時，要同時在 `style.css` 新增對應的 `--cat-新分類` 顏色（亮色與暗色模式都要）。
- 版面必須在手機寬度（375px）正常顯示，不可出現橫向捲軸。

## 11. 標準工作流程 (新增頁面 SOP)

### 新增一間店

1. **初始化檔案**：執行 `python build.py new restaurant <slug>` —— 腳本會從 `templates/restaurant.md` 自動複製出新檔並填好 slug 與日期，放置於 `content/restaurants/<slug>.md`。**（嚴禁手動在 docs/ 底下建立 HTML 檔）**
2. **撰寫內容**：填寫該檔案 front matter 所有欄位與三個固定段落（必須遵循第 7 節的 Markdown 限制，不寫任何 HTML 標籤）。
3. **驗證與編譯**：執行 `python build.py`。腳本會自動進行格式驗證，並在成功後，將編譯好的頁面輸出至 `docs/restaurants/<slug>.html`。
4. **關聯指南**：如果適合，把這間店加進相關的指南（更新該指南的 `restaurants` 與內文）。

### 新增一篇指南

1. **初始化檔案**：執行 `python build.py new guide <slug>`，檔案將建立在 `content/guides/<slug>.md`。
2. **編輯內容**：在 `restaurants` 列出要用到的店；若店還不存在，**必須先完成該店家的「新增一間店」SOP** 之後再寫指南。
3. **驗證與編譯**：執行 `python build.py`。編譯後的檔案將自動輸出至 `docs/guides/<slug>.html`。

### 新增分類或區域

1. 修改 `build.py` 最上方的 `CATEGORIES` 或 `AREAS`。
2. 新分類要在 `style.css` 補上 `--cat-*` 顏色。
3. 同步更新本文件第 5.1 節的允許值清單。

## 12. 禁止事項

- ❌ 手動修改或新增 `docs/` 裡的任何 HTML / CSS 檔案
- ❌ 繞過 `content/` 資料夾直接去拼湊靜態網頁
- ❌ 在 Markdown 中嵌入任何原生 HTML 標籤或 inline style
- ❌ 新增 front matter 規格以外的欄位（需要新欄位時，先更新本文件與 `build.py`）
- ❌ 刪除既有店家檔案
- ❌ 引入外部 JS / CSS 框架或需要安裝的套件
- ❌ 在內容中放入未經確認的營業資訊、照片 or 轉貼文章

## 13. 完成前檢查清單

每次修改完，回覆使用者之前請逐項確認：

- [ ] `python build.py` 執行成功，沒有 `ERROR`
- [ ] 新檔案的檔名與 `slug` 一致，且只用小寫英文、數字與 `-`
- [ ] `category`、`area`、`price` 都是允許的值
- [ ] `summary` 不超過 30 字
- [ ] 店家頁有「為什麼推薦／必點／小提醒」三段
- [ ] 不確定的資訊都標示為 `待確認`，並附上 `sources`
- [ ] 沒有手動改動 `docs/`

## 14. 給使用者的範例指令（Prompt）

> 請先閱讀 AGENTS.md。幫我新增一間店：「政大側門的敏忠小吃」，
> 我吃過他們的炒飯，大概 90 元，晚上很多人。地址我不確定。

AI 應該：建立 `content/restaurants/min-zhong.md` → `category: 正餐`、`area: 側門`、`price: $`、
`address: 待確認`、`sources: 親自造訪` → 寫好三段內文 → 執行 `python build.py` → 回報結果。
