"""政大吃什麼 NCCU Eats — 網站建置腳本

用法：
    python build.py                        驗證 content/ 並產生網站到 docs/
    python build.py check                  只驗證，不產生網站
    python build.py new restaurant <slug>  從 templates/restaurant.md 建立新店家
    python build.py new guide <slug>       從 templates/guide.md 建立新指南

規則說明請見 AGENTS.md。只使用 Python 標準函式庫。
"""

import datetime
import html
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

# ---------------------------------------------------------------------------
# 設定：新增分類／區域時，修改這裡並同步更新 AGENTS.md 與 assets/style.css
# ---------------------------------------------------------------------------
SITE_TITLE = "NCCU Eats"
SITE_SUBTITLE = ""

# 中文分類名稱 → CSS 用的英文代號（對應 style.css 的 --cat-*）
CATEGORIES = {
    "早餐早午餐": "brunch",
    "小吃": "snack",
    "正餐": "meal",
    "甜點飲料": "dessert",
    "咖啡廳": "cafe",
}
AREAS = ["正門", "側門", "後山", "校內", "指南路", "萬壽路"]
PRICES = {"$": "150 元內", "$$": "150–300 元", "$$$": "300 元以上", "?": "價位待確認"}

RESTAURANT_FIELDS = ["name", "slug", "category", "area", "price", "summary",
                     "address", "hours", "tags", "updated", "sources"]
RESTAURANT_SECTIONS = ["為什麼推薦", "必點", "小提醒"]
GUIDE_FIELDS = ["title", "slug", "summary", "restaurants", "updated"]
SUMMARY_MAX = 30

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
OUT = ROOT / "docs"

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


# ---------------------------------------------------------------------------
# 讀檔與解析
# ---------------------------------------------------------------------------
def parse_file(path):
    """把 .md 檔拆成 (front matter dict, 內文字串)。"""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError("檔案開頭缺少 --- front matter")
    try:
        _, fm, body = text.split("---", 2)
    except ValueError:
        raise ValueError("front matter 沒有用兩個 --- 包起來")
    meta = {}
    for line in fm.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"front matter 這行格式錯誤（缺少冒號）：{line}")
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, body.strip()


def split_list(value, sep=","):
    return [x.strip() for x in value.split(sep) if x.strip()]


def load(kind):
    items = []
    for path in sorted((CONTENT / kind).glob("*.md")):
        meta, body = parse_file(path)
        meta["_path"] = path
        meta["_body"] = body
        items.append(meta)
    return items


# ---------------------------------------------------------------------------
# 驗證：讓 AI 或人寫錯格式時，立刻知道錯在哪裡
# ---------------------------------------------------------------------------
def validate(restaurants, guides):
    errors = []

    def err(item, msg):
        errors.append(f"{item['_path'].relative_to(ROOT)}: {msg}")

    def common(item, fields):
        for f in fields:
            if not item.get(f):
                err(item, f"缺少必填欄位 `{f}`")
        extra = set(k for k in item if not k.startswith("_")) - set(fields)
        if extra:
            err(item, f"有規格外的欄位 {sorted(extra)}（請先更新 AGENTS.md）")
        slug = item.get("slug", "")
        if slug and not SLUG_RE.match(slug):
            err(item, f"slug `{slug}` 只能用小寫英文、數字與 -")
        if slug and slug != item["_path"].stem:
            err(item, f"slug `{slug}` 與檔名 `{item['_path'].name}` 不一致")
        if item.get("updated") and not DATE_RE.match(item["updated"]):
            err(item, "updated 必須是 YYYY-MM-DD")
        if len(item.get("summary", "")) > SUMMARY_MAX:
            err(item, f"summary 超過 {SUMMARY_MAX} 字（目前 {len(item['summary'])} 字）")
        if re.search(r"</?[a-zA-Z][^>]*>", item["_body"]):
            err(item, "內文含有 HTML 標籤，只能使用 AGENTS.md 第 7 節的 Markdown 語法")

    slugs = set()
    for r in restaurants:
        common(r, RESTAURANT_FIELDS)
        slugs.add(r.get("slug"))
        if r.get("name") == "店名" or "一句話推薦" in r.get("summary", ""):
            err(r, "還保留範本的預設文字，請填入真正的店名與 summary")
        if r.get("category") and r["category"] not in CATEGORIES:
            err(r, f"category `{r['category']}` 不在允許清單 {list(CATEGORIES)}")
        if r.get("area") and r["area"] not in AREAS:
            err(r, f"area `{r['area']}` 不在允許清單 {AREAS}")
        if r.get("price") and r["price"] not in PRICES:
            err(r, f"price `{r['price']}` 只能是 {list(PRICES)}")
        tags = split_list(r.get("tags", ""))
        if r.get("tags") and not 2 <= len(tags) <= 4:
            err(r, f"tags 需要 2–4 個（目前 {len(tags)} 個）")
        headings = re.findall(r"^## (.+)$", r["_body"], flags=re.M)
        if headings != RESTAURANT_SECTIONS:
            err(r, f"內文段落必須依序為 {RESTAURANT_SECTIONS}，目前是 {headings}")

    for g in guides:
        common(g, GUIDE_FIELDS)
        listed = split_list(g.get("restaurants", ""))
        for s in listed:
            if s not in slugs:
                err(g, f"restaurants 列出的 `{s}` 不存在（請先建立店家頁）")
        for s in WIKILINK_RE.findall(g["_body"]):
            if s not in slugs:
                err(g, f"內文連結 [[{s}]] 指向不存在的店家")
            elif s not in listed:
                err(g, f"內文用到 [[{s}]]，但 restaurants 清單沒有列出")

    return errors


# ---------------------------------------------------------------------------
# 精簡 Markdown 轉 HTML（支援語法見 AGENTS.md 第 7 節）
# ---------------------------------------------------------------------------
def inline(text, names, prefix):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                  r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    text = WIKILINK_RE.sub(
        lambda m: f'<a class="shop-link" href="{prefix}restaurants/{m.group(1)}.html">'
                  f'{html.escape(names.get(m.group(1), m.group(1)))}</a>', text)
    return text


def markdown(md, names, prefix=""):
    out, para, items = [], [], []

    def flush():
        if para:
            out.append(f"<p>{inline(' '.join(para), names, prefix)}</p>")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i, names, prefix)}</li>" for i in items) + "</ul>")
            items.clear()

    for line in md.splitlines():
        s = line.strip()
        if not s:
            flush()
        elif s.startswith("### "):
            flush(); out.append(f"<h3>{inline(s[4:], names, prefix)}</h3>")
        elif s.startswith("## "):
            flush(); out.append(f"<h2>{inline(s[3:], names, prefix)}</h2>")
        elif s.startswith("- "):
            if para:
                flush()
            items.append(s[2:])
        elif s.startswith("> "):
            flush(); out.append(f"<blockquote>{inline(s[2:], names, prefix)}</blockquote>")
        else:
            if items:
                flush()
            para.append(s)
    flush()
    return "\n".join(out)


# ---------------------------------------------------------------------------
# HTML 版型
# ---------------------------------------------------------------------------
def esc(s):
    return html.escape(str(s))


def layout(title, body, prefix="", description=""):
    full = f"{title}｜NCCU Eats" if title != "NCCU Eats" else "NCCU Eats"
    year = datetime.date.today().year
    return f"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full)}</title>
<meta name="description" content="{esc(description or '政大周邊美食整理：依分類、區域找到下一餐。')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@600;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
<header class="site-header">
  <a class="brand" href="{prefix}index.html"><span class="brand-mark">食</span><span><b>NCCU Eats</b><small></small></span></a>
  <nav><a href="{prefix}index.html#shops">店家</a><a href="{prefix}index.html#guides">指南</a></nav>
</header>
<main>
{body}
</main>
<footer class="site-footer">
  <p>資料整理自網路文章與親自造訪，營業資訊可能變動，出發前請再確認。</p>
  <p>© {year} NCCU Eats・內容依 <code>AGENTS.md</code> 規則維護</p>
</footer>
<script src="{prefix}assets/app.js"></script>
</body>
</html>
"""


def cat_badge(category):
    return f'<span class="badge cat-{CATEGORIES[category]}">{esc(category)}</span>'


def shop_card(r):
    tags = split_list(r["tags"])
    search = " ".join([r["name"], r["summary"], r["area"], r["category"], *tags]).lower()
    return f"""<a class="card" href="restaurants/{r['slug']}.html" data-category="{esc(r['category'])}" data-area="{esc(r['area'])}" data-search="{esc(search)}">
  <div class=
