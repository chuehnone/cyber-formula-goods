#!/usr/bin/env python3
"""hobbysearch 抓取（第二版）：對每個商品大分類跑關鍵字搜尋。

分類由 URL 參數決定，因此每筆商品的分類是站方標記、非我方猜測。
詳情頁有 Cloudflare challenge，不觸碰；僅用搜尋結果頁的公開欄位。
"""
import json, re, time, html, urllib.parse, urllib.request, sys

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
BASE = "https://www.1999.co.jp"
DELAY = 2.0

# 站方大分類 -> (代碼, 中文名)
CATS = {
    "plamo":  ("102", "組裝模型"),
    "figure": ("101", "Figure／完成品"),
    "mini":   ("106", "迷你車／合金"),
    "car":    ("112", "汽車模型"),
    "chara":  ("110", "角色商品"),
    "book":   ("115", "書籍"),
    "toy":    ("119", "玩具／雜貨"),
    "mecha":  ("111", "機器人／機甲"),
    "doll":   ("108", "人形"),
    "paint":  ("107", "塗料"),
}

QUERIES = ["サイバーフォーミュラ", "アスラーダ", "オーガ AN-21", "イシュザーク",
           "ナイトセイバー", "ガーランド SF-03", "エクスペリオン", "スゴウ",
           "菅生あすか", "風見ハヤト", "ブーステッドアスラーダ", "プロトジャガー"]

CARD_RE = re.compile(r'<div class="c-card">(.*?)(?=<div class="c-card">|<div class="c-product-list__item">|\Z)', re.S)

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def field(pat, blk, g=1, default=None):
    m = re.search(pat, blk, re.S)
    return html.unescape(m.group(g).strip()) if m else default

def parse(doc, cat_key, cat_name, query):
    out = []
    for blk in CARD_RE.findall(doc):
        code = field(r'href="/(\d{6,})"', blk)
        title = field(r'class="c-card__title">(.*?)</div>', blk)
        if not code or not title:
            continue
        title = re.sub(r"<[^>]+>", "", title).strip()
        price = field(r"lbStreetPrice[^>]*>([\d,]+)<", blk)
        proper = field(r"<del>([\d,]+)</del>", blk)
        disc = field(r"lbDiscountRate[^>]*>(\d+)<", blk)
        rel = field(r'class="c-card__maker">(.*?)</div>', blk)
        img = field(r'<img src="(/itbig[^"]+)"', blk)
        tags = [html.unescape(t.strip()) for t in
                re.findall(r'<li data-tags="[^"]*">([^<]+)</li>', blk)]
        out.append({
            "code": code, "title": title,
            "price": int(price.replace(",", "")) if price else None,
            "listPrice": int(proper.replace(",", "")) if proper else None,
            "discount": int(disc) if disc else None,
            "releaseLine": re.sub(r"<[^>]+>", "", rel).strip() if rel else None,
            "tags": tags,
            "image": BASE + img if img else None,
            "url": f"{BASE}/{code}/",
            "catKey": cat_key, "catName": cat_name,
            "matchedQuery": query,
        })
    return out

def main():
    items = {}
    for query in QUERIES:
        q = urllib.parse.quote(query)
        for cat_key, (code, cat_name) in CATS.items():
            page = 1
            while page <= 6:
                url = f"{BASE}/search?searchkey={q}&typ1_c={code}&cat={cat_key}&sold=0&sortid=7&spage={page}"
                try:
                    doc = get(url)
                except Exception as e:
                    sys.stderr.write(f"  ! {query}/{cat_key} p{page}: {e}\n")
                    break
                got = parse(doc, cat_key, cat_name, query)
                if not got:
                    break
                new = 0
                for it in got:
                    if it["code"] not in items:
                        items[it["code"]] = it
                        new += 1
                sys.stderr.write(f"  {query}/{cat_key} p{page}: {len(got)} 件, 新增 {new} (總 {len(items)})\n")
                if f"spage={page+1}" not in doc:
                    break
                page += 1
                time.sleep(DELAY)
            time.sleep(DELAY)

    data = list(items.values())
    json.dump(data, open("hs_raw2.json", "w"), ensure_ascii=False, indent=1)
    sys.stderr.write(f"\n總計 {len(data)} 件 -> hs_raw2.json\n")

if __name__ == "__main__":
    main()
