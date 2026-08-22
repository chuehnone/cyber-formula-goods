#!/usr/bin/env python3
"""從青島文化教材社官網 (aoshima-bk.co.jp) 抓取閃電霹靂車商品。

官方專頁 /special/product/cyberformula/ 列出全部品項，
逐一進入商品頁取得官方規格（系列編號、比例、發售月、含稅定價、JAN）。
"""
import json, re, time, html, urllib.request, sys

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
BASE = "https://www.aoshima-bk.co.jp"
DELAY = 1.5

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

def parse_item(doc, url):
    doc = re.sub(r"<(script|style).*?</\1>", "", doc, flags=re.S)

    title = clean(re.search(r"<h1[^>]*>(.*?)</h1>", doc, re.S).group(1)) \
        if re.search(r"<h1[^>]*>(.*?)</h1>", doc, re.S) else None
    if not title:
        return None

    # 規格：以「鍵\n值」序列出現於麵包屑之後
    txt = re.sub(r"<[^>]+>", "\n", doc)
    lines = [html.unescape(l).strip() for l in txt.split("\n") if l.strip()]

    spec = {}
    keys = {"ブランド": "brand", "シリーズ": "series", "スケール": "scale",
            "発売月": "release", "価格": "price", "JANコード": "jan"}
    for i, l in enumerate(lines):
        if l in keys and keys[l] not in spec and i + 1 < len(lines):
            nxt = lines[i + 1]
            # 跳過搜尋表單（下一行是「すべて」）
            if nxt == "すべて":
                continue
            spec[keys[l]] = nxt

    # 商品種類：麵包屑「製品情報 > ○○ > 標題」
    kind = None
    KINDS = {"プラモデル", "ミニカー", "完成品", "フィギュア", "雑貨",
             "合金", "R/C", "輸入商品", "その他"}
    for i, l in enumerate(lines):
        if l == "製品情報":
            for j in range(i + 1, min(i + 4, len(lines))):
                if lines[j] in KINDS:
                    kind = lines[j]
                    break
            if kind:
                break

    desc = None
    m = re.search(r'class="wysiwygArea">(.*?)</div>', doc, re.S)
    if m:
        ps = [clean(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", m.group(1), re.S)]
        ps = [p for p in ps if p and not p.startswith("※")]
        desc = " ".join(ps) or None

    img = None
    m = re.search(r'class="itemGallery".*?<img[^>]+src="([^"]+)"', doc, re.S)
    if m:
        img = m.group(1)
        if img.startswith("/"):
            img = BASE + img

    price = None
    if spec.get("price"):
        pm = re.search(r"([\d,]+)", spec["price"])
        if pm:
            price = int(pm.group(1).replace(",", ""))

    jan = spec.get("jan") or ""
    jan_digits = re.sub(r"\D", "", jan)
    if len(jan_digits) < 13:
        jan_digits = None

    return {
        "title": title,
        "kind": kind,
        "brand": spec.get("brand"),
        "seriesLine": spec.get("series"),
        "scale": spec.get("scale"),
        "release": spec.get("release"),
        "price": price,
        "priceText": spec.get("price"),
        "jan": jan_digits,
        "desc": desc,
        "image": img,
        "url": url,
    }

def main():
    sys.stderr.write("讀取官方專頁…\n")
    idx = get(BASE + "/special/product/cyberformula/")
    codes = sorted(set(re.findall(r'href="/product/(\d+)/"', idx)))
    sys.stderr.write(f"專頁列出 {len(codes)} 件商品\n")

    items = []
    for n, code in enumerate(codes, 1):
        url = f"{BASE}/product/{code}/"
        try:
            doc = get(url)
            it = parse_item(doc, url)
            if it:
                it["jan"] = code  # URL 代碼即完整 JAN
                items.append(it)
                sys.stderr.write(f"[{n}/{len(codes)}] {it['title'][:40]} | {it['price']}\n")
            else:
                sys.stderr.write(f"[{n}/{len(codes)}] {code} 解析失敗\n")
        except Exception as e:
            sys.stderr.write(f"[{n}/{len(codes)}] {code} 失敗: {e}\n")
        time.sleep(DELAY)

    json.dump(items, open("ao_raw.json", "w"), ensure_ascii=False, indent=1)
    sys.stderr.write(f"\n總計 {len(items)} 件 -> ao_raw.json\n")

if __name__ == "__main__":
    main()
