#!/usr/bin/env python3
"""從 hobbysearch (1999.co.jp) 抓取閃電霹靂車周邊商品。

只收錄實際抓到的資料；每筆保留來源網址。
"""
import json, re, time, html, urllib.parse, urllib.request, sys

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
BASE = "https://www.1999.co.jp"
DELAY = 2.0  # 禮貌延遲

def get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "ja,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

# 以 c-card 為單位切塊
CARD_RE = re.compile(r'<div class="c-card">(.*?)(?=<div class="c-card">|<div class="c-product-list__item">|\Z)', re.S)

def field(pat, block, group=1, default=None):
    m = re.search(pat, block, re.S)
    return html.unescape(m.group(group).strip()) if m else default

def parse_cards(page_html):
    out = []
    for blk in CARD_RE.findall(page_html):
        code = field(r'href="/(\d{6,})"', blk)
        title = field(r'class="c-card__title">(.*?)</div>', blk)
        if not code or not title:
            continue
        title = re.sub(r'<[^>]+>', '', title).strip()

        price = field(r'lbStreetPrice[^>]*>([\d,]+)<', blk)
        proper = field(r'<del>([\d,]+)</del>', blk)
        discount = field(r'lbDiscountRate[^>]*>(\d+)<', blk)
        maker_line = field(r'class="c-card__maker">(.*?)</div>', blk)
        img = field(r'<img src="(/itbig[^"]+)"', blk)
        alt = field(r'<img src="/itbig[^"]+"\s+alt="([^"]*)"', blk)

        tags = [html.unescape(t.strip()) for t in
                re.findall(r'<li data-tags="[^"]*">([^<]+)</li>', blk)]

        out.append({
            "code": code,
            "title": title,
            "alt": alt,
            "price": int(price.replace(",", "")) if price else None,
            "listPrice": int(proper.replace(",", "")) if proper else None,
            "discount": int(discount) if discount else None,
            "releaseLine": maker_line,
            "tags": tags,
            "image": BASE + img if img else None,
            "url": f"{BASE}/{code}/",
        })
    return out

def main():
    query = "サイバーフォーミュラ"
    q = urllib.parse.quote(query)
    all_items, seen = [], set()

    page = 1
    while page <= 12:
        url = f"{BASE}/search?searchkey={q}&sortid=7&spage={page}"
        sys.stderr.write(f"[page {page}] {url}\n")
        try:
            doc = get(url)
        except Exception as e:
            sys.stderr.write(f"  失敗: {e}\n")
            break

        items = parse_cards(doc)
        if not items:
            sys.stderr.write("  無商品，結束\n")
            break

        new = 0
        for it in items:
            if it["code"] not in seen:
                seen.add(it["code"])
                all_items.append(it)
                new += 1
        sys.stderr.write(f"  取得 {len(items)} 件，新增 {new} 件（累計 {len(all_items)}）\n")

        # 沒有下一頁就停
        if f"spage={page+1}" not in doc:
            sys.stderr.write("  無下一頁，結束\n")
            break
        page += 1
        time.sleep(DELAY)

    json.dump(all_items, open("hs_raw.json", "w"), ensure_ascii=False, indent=1)
    sys.stderr.write(f"\n總計 {len(all_items)} 件 → hs_raw.json\n")

if __name__ == "__main__":
    main()
