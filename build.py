"""NCCU Eats — 網站建置腳本"""

import datetime
import html
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

SITE_TITLE = "NCCU Eats"

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
            raise ValueError(f"front matter 這行格式錯誤：{line}")
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
# 驗證
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
            err(item, f"有規格外的欄位 {sorted(extra)}")
        slug = item.get("slug", "")
        if slug and not SLUG_RE.match(slug):
            err(item, f"slug `{slug}` 只能用小寫英文、數字與 -")
        if slug and slug != item["_path"].stem:
            err(item, f"slug `{slug}` 與檔名 `{item['_path'].name}` 不一致")
        if item.get("updated") and not DATE_RE.match(item["updated"]):
            err(item, "updated 必須是 YYYY-MM-DD")
        if len(item.get("summary", "")) > SUMMARY_MAX:
            err(item, f"summary 超過 {SUMMARY_MAX} 字")
        if re.search(r"</?[a-zA-Z][^>]*>", item["_body"]):
            err(item, "內文含有 HTML 標籤，只能使用 AGENTS.md 第 7 節的 Markdown 語法")

    slugs = set()
    for r in restaurants:
        common(r, RESTAURANT_FIELDS)
        slugs.add(r.get("slug"))
        if r.get("name") == "店名" or "一句話推薦" in r.get("summary", ""):
            err(r, "還保留範本的預設文字")
        if r.get("category") and r["category"] not in CATEGORIES:
            err(r, f"category `{r['category']}` 錯誤")
        if r.get("area") and r["area"] not in AREAS:
            err(r, f"area `{r['area']}` 錯誤")
        if r.get("price") and r["price"] not in PRICES:
            err(r, f"price `{r['price']}` 錯誤")
        tags = split_list(r.get("tags", ""))
        if r.get("tags") and not 2 <= len(tags) <= 4:
            err(r, "tags 需要 2–4 個")
        headings = re.findall(r"^## (.+)$", r["_body"], flags=re.M)
        if headings != RESTAURANT_SECTIONS:
            err(r, f"段落必須為 {RESTAURANT_SECTIONS}")

    for g in guides:
        common(g, GUIDE_FIELDS)
        listed = split_list(g.get("restaurants", ""))
        for s in listed:
            if s not in slugs:
                err(g, f"restaurants `{s}` 不存在")
        for s in WIKILINK_RE.findall(g["_body"]):
            if s not in slugs:
                err(g, f"[[{s}]] 不存在")
            elif s not in listed:
                err(g, f"[[{s}]] 未列在 restaurants 欄位中")
    return errors

# ---------------------------------------------------------------------------
# 渲染器
# ---------------------------------------------------------------------------
def inline(text, names, prefix):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    text = WIKILINK_RE.sub(lambda m: f'<a class="shop-link" href="{prefix}restaurants/{m.group(1)}.html">{html.escape(names.get(m.group(1), m.group(1)))}</a>', text)
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
<main>{body}</main>
<footer class="site-footer">
  <p>資料整理自網路文章與親自造訪，營業資訊可能變動，出發前請再確認。</p>
  <p>© {year} NCCU Eats・內容依 <code>AGENTS.md</code> 規則維護</p>
</footer>
<script src="{prefix}assets/app.js"></script>
</body>
</html>"""


def cat_badge(category):
    return f'<span class="badge cat-{CATEGORIES[category]}">{esc(category)}</span>'


def shop_card(r):
    tags = split_list(r["tags"])
    search = " ".join([r["name"], r["summary"], r["area"], r["category"], *tags]).lower()
    return f"""<a class="card" href="restaurants/{r['slug']}.html" data-category="{esc(r['category'])}" data-area="{esc(r['area'])}" data-search="{esc(search)}">
  <div class="card-top">{cat_badge(r['category'])}<span class="price" title="{esc(PRICES[r['price']])}">{esc(r['price'])}</span></div>
  <h3>{esc(r['name'])}</h3>
  <p>{esc(r['summary'])}</p>
  <div class="card-foot"><span class="area">📍 {esc(r['area'])}</span><span class="tags">{' '.join('#' + esc(t) for t in tags)}</span></div>
</a>"""


def page_index(restaurants, guides):
    chips_cat = "".join(f'<button class="chip" data-filter="category" data-value="{esc(c)}">{esc(c)}</button>' for c in CATEGORIES)
    chips_area = "".join(f'<button class="chip" data-filter="area" data-value="{esc(a)}">{esc(a)}</button>' for a in AREAS)
    cards = "\n".join(shop_card(r) for r in restaurants)
    guide_cards = "\n".join(f"""<a class="guide-card" href="guides/{g['slug']}.html">
  <span class="kicker">主題指南・{len(split_list(g['restaurants']))} 間店</span>
  <h3>{esc(g['title'])}</h3><p>{esc(g['summary'])}</p></a>""" for g in guides)
    return layout(SITE_TITLE, f"""
<section class="hero">
  <p class="kicker">國立政治大學・台北市文山區</p>
  <h1>下課了，<br>要吃什麼？</h1>
  <p class="lead">目前收錄 <b>{len(restaurants)}</b> 間店、<b>{len(guides)}</b> 篇指南。依分類、區域篩選，找到你的下一餐。</p>
</section>
<section id="guides" class="section">
  <h2 class="section-title">主題指南</h2>
  <div class="guide-grid">{guide_cards}</div>
</section>
<section id="shops" class="section">
  <h2 class="section-title">所有店家</h2>
  <div class="filters">
    <input id="search" type="search" placeholder="搜尋店名、標籤…" aria-label="搜尋店家">
    <div class="chip-row"><span class="chip-label">分類</span><button class="chip is-active" data-filter="category" data-value="">全部</button>{chips_cat}</div>
    <div class="chip-row"><span class="chip-label">區域</span><button class="chip is-active" data-filter="area" data-value="">全部</button>{chips_area}</div>
  </div>
  <p class="result-count" id="count" aria-live="polite"></p>
  <div class="card-grid" id="cards">{cards}</div>
  <p class="empty" id="empty" hidden>找不到符合的店家，換個條件試試，或依照 AGENTS.md 新增一間吧！</p>
</section>""")


def page_restaurant(r, names, guides_by_shop):
    maps = "https://www.google.com/maps/search/?api=1&query=" + quote(f"{r['name']} {r['address']}")
    sources = []
    for s in split_list(r["sources"], "|"):
        if s.startswith("http"):
            host = re.sub(r"^https?://(www\.)?", "", s).split("/")[0]
            sources.append(f'<li><a href="{esc(s)}" target="_blank" rel="noopener">{esc(host)}</a></li>')
        else:
            sources.append(f"<li>{esc(s)}</li>")
    related = guides_by_shop.get(r["slug"], [])
    related_html = ""
    if related:
        links = "".join(f'<li><a href="../guides/{g["slug"]}.html">{esc(g["title"])}</a></li>' for g in related)
        related_html = f'<aside class="related"><h2>收錄在這些指南</h2><ul>{links}</ul></aside>'
    tbd = lambda v: f'<span class="tbd">{esc(v)}</span>' if "待確認" in v else esc(v)
    body = f"""<article class="detail">
  <a class="back" href="../index.html#shops">← 回到所有店家</a>
  <header class="detail-head">
    <div class="card-top">{cat_badge(r['category'])}<span class="area">📍 {esc(r['area'])}</span></div>
    <h1>{esc(r['name'])}</h1>
    <p class="lead">{esc(r['summary'])}</p>
    <p class="tags">{' '.join('#' + esc(t) for t in split_list(r['tags']))}</p>
  </header>
  <dl class="facts">
    <div><dt>價位</dt><dd>{esc(r['price'])}　{esc(PRICES[r['price']])}</dd></div>
    <div><dt>地址</dt><dd>{tbd(r['address'])}　<a href="{esc(maps)}" target="_blank" rel="noopener">地圖 ↗</a></dd></div>
    <div><dt>營業時間</dt><dd>{tbd(r['hours'])}</dd></div>
    <div><dt>最後更新</dt><dd>{esc(r['updated'])}</dd></div>
  </dl>
  <div class="prose">{markdown(r['_body'], names, '../')}</div>
  {related_html}
  <footer class="sources"><h2>資料來源</h2><ul>{''.join(sources)}</ul></footer>
</article>"""
    return layout(r["name"], body, "../", r["summary"])


def page_guide(g, names):
    body = f"""<article class="detail guide">
  <a class="back" href="../index.html#guides">← 回到首頁</a>
  <header class="detail-head">
    <p class="kicker">主題指南・最後更新 {esc(g['updated'])}</p>
    <h1>{esc(g['title'])}</h1>
    <p class="lead">{esc(g['summary'])}</p>
  </header>
  <div class="prose">{markdown(g['_body'], names, '../')}</div>
</article>"""
    return layout(g["title"], body, "../", g["summary"])

# ---------------------------------------------------------------------------
# 指令集與進入點
# ---------------------------------------------------------------------------
def cmd_new(kind, slug):
    folder = {"restaurant": "restaurants", "guide": "guides"}.get(kind)
    if not folder:
        sys.exit("ERROR: 類型只能是 restaurant 或 guide")
    if not SLUG_RE.match(slug):
        sys.exit("ERROR: slug 只能用小寫英文、數字與 -")
    target = CONTENT / folder / f"{slug}.md"
    if target.exists():
        sys.exit(f"ERROR: {target.relative_to(ROOT)} 已經存在")
    text = (ROOT / "templates" / f"{kind}.md").read_text(encoding="utf-8")
    text = text.replace("__SLUG__", slug).replace("__DATE__", datetime.date.today().isoformat())
    target.write_text(text, encoding="utf-8")
    print(f"已建立 {target.relative_to(ROOT)}")


def main(argv):
    if argv[:1] == ["new"]:
        if len(argv) != 3:
            sys.exit("用法：python build.py new restaurant|guide <slug>")
        return cmd_new(argv[1], argv[2])

    restaurants, guides = load("restaurants"), load("guides")
    errors = validate(restaurants, guides)
    if errors:
        print(f"ERROR: 發現 {len(errors)} 個問題：")
        for e in errors: print("  -", e)
        sys.exit(1)
    print(f"✓ 驗證通過：{len(restaurants)} 間店、{len(guides)} 篇指南")
    if argv[:1] == ["check"]:
        return

    names = {r["slug"]: r["name"] for r in restaurants}
    guides_by_shop = {}
    for g in guides:
        for s in split_list(g["restaurants"]):
            guides_by_shop.setdefault(s, []).append(g)

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "restaurants").mkdir(parents=True)
    (OUT / "guides").mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("")

    (OUT / "index.html").write_text(page_index(restaurants, guides), encoding="utf-8")
    for r in restaurants:
        (OUT / "restaurants" / f"{r['slug']}.html").write_text(page_restaurant(r, names, guides_by_shop), encoding="utf-8")
    for g in guides:
        (OUT / "guides" / f"{g['slug']}.html").write_text(page_guide(g, names), encoding="utf-8")
    print(f"✓ 已產生網站到 docs/（共 {1 + len(restaurants) + len(guides)} 頁）")


if __name__ == "__main__":
    main(sys.argv[1:])
