#!/usr/bin/env python3
"""整併 hobbysearch 與青島官網資料，產出 products.json。

原則：
- 只收錄實際抓到的商品；不補寫未驗證資料。
- 每筆保留來源網址（可點擊）與來源站名。
- 青島官方資料視為權威（官方定價、發售月、系列編號）。
"""
import json, re, sys, collections

# ---------- 分類判定 ----------
# 依商品標題結尾的 (○○) 標記與站方分類決定；不猜測。
KIND_MAP = {
    "プラモデル": ("plamo", "組裝模型"),
    "完成品": ("finished", "完成品模型"),
    "ミニカー": ("minicar", "迷你車"),
    "トミカ": ("minicar", "迷你車"),
    "フィギュア": ("figure", "Figure"),
    "ガレージキット": ("garage", "Garage Kit"),
    "食玩": ("shokugan", "食玩"),
    "書籍": ("book", "書籍"),
    "CD": ("cd", "CD／原聲帶"),
    "DVD": ("dvd", "DVD"),
    "Blu-ray": ("bd", "Blu-ray"),
    "カードサプライ": ("card", "卡牌用品"),
    "トレーディングカード": ("card", "卡牌用品"),
    "塗料": ("paint", "專用塗料"),
    "工具": ("tool", "工具"),
    "ドール": ("doll", "人形"),
    "玩具": ("toy", "玩具"),
}

# キャラクターグッズ 太籠統，依標題關鍵字細分
GOODS_SUB = [
    ("Tシャツ", ("apparel", "服飾")),
    ("パーカー", ("apparel", "服飾")),
    ("スウェット", ("apparel", "服飾")),
    ("ジャケット", ("apparel", "服飾")),
    ("キャップ", ("apparel", "服飾")),
    ("アクリル", ("acrylic", "壓克力周邊")),
    ("ステッカー", ("sticker", "貼紙")),
    ("シール", ("sticker", "貼紙")),
    ("バッジ", ("badge", "徽章")),
    ("ワッペン", ("badge", "徽章")),
    ("キーホルダー", ("keychain", "鑰匙圈")),
    ("ストラップ", ("keychain", "鑰匙圈")),
    ("トート", ("bag", "包袋")),
    ("ポーチ", ("bag", "包袋")),
    ("バッグ", ("bag", "包袋")),
    ("マグカップ", ("tableware", "杯具")),
    ("グラス", ("tableware", "杯具")),
    ("タンブラー", ("tableware", "杯具")),
    ("クリアファイル", ("stationery", "文具")),
    ("ノート", ("stationery", "文具")),
    ("色紙", ("stationery", "文具")),
    ("ポスター", ("poster", "海報")),
    ("タオル", ("towel", "毛巾")),
    ("時計", ("watch", "鐘錶")),
    ("ぬいぐるみ", ("plush", "絨毛玩偶")),
]

def detect_kind(title, cat_name=None):
    t = title or ""
    # 括號類別標記通常在結尾，但可能後接 ★限定版 等尾綴，故容許尾綴
    m = re.search(r"[（(]([^（()）]+)[)）]\s*(?:★[^（()）]*)?$", t)
    raw = m.group(1).strip() if m else None

    if raw:
        for k, v in KIND_MAP.items():
            if k in raw:
                return v
        if "グッズ" in raw or "雑貨" in raw:
            for ja, v in GOODS_SUB:
                if ja in t:
                    return v
            return ("goods", "周邊雜貨")

    if cat_name:
        for k, v in KIND_MAP.items():
            if k in cat_name:
                return v
        if "角色商品" in cat_name:
            for ja, v in GOODS_SUB:
                if ja in t:
                    return v
            return ("goods", "周邊雜貨")
        if "機器人" in cat_name or "機甲" in cat_name:
            return ("finished", "完成品模型")

    # 括號內是形態名等非類別字串時，退回站方分類已在上面處理
    return ("other", "其他")

def strip_kind(title):
    t = title or ""
    m = re.search(r"\s*[（(]([^（()）]+)[)）]\s*(?P<suffix>★[^（()）]*)?$", t)
    if not m:
        return t.strip()
    inner = m.group(1)
    known = list(KIND_MAP) + ["キャラクターグッズ", "グッズ", "雑貨"]
    if any(k in inner for k in known):
        # 只拿掉類別括號，保留 ★限定版 之類的尾綴
        suffix = m.group("suffix") or ""
        return (t[:m.start()].strip() + " " + suffix).strip()
    return t.strip()   # 形態名等，保留

# ---------- 商品系列判定 ----------
# 這是「產品線」而非作品系列（作品系列見 detect_series）。
# 來源站的分類會把同一產品線拆到不同類別（例如 C.F.C. 有 完成品 也有 食玩），
# 故另立此欄位讓使用者能一次看齊整個系列。
PRODUCT_LINES = [
    ("cfc", "C.F.C.", r"C\.F\.C\."),
    ("va", "Variable Action", r"ヴァリアブルアクション"),
    ("aoshima124", "1/24 組裝模型（青島）",
     r"^(アスラーダ|スーパーアスラーダ|νアスラーダ|ν\(ニュー\)アスラーダ|"
     r"イシュザーク|ガーランド|シュピーゲル|凰呀|ナイトセイバー)"),
    ("playp", "PlayP 系列", r"PlayP-"),
    ("cfcolor", "閃電霹靂車專用色", r"^CM-\d+"),
    ("tomica", "TOMICA", r"トミカ"),
    ("hotwheels", "Hot Wheels", r"ホットウィール|キャラウィール"),
]


def detect_line(title):
    t = title or ""
    for lid, name, pat in PRODUCT_LINES:
        if re.search(pat, t):
            return {"id": lid, "name": name}
    return None


# ---------- 機體判定（僅依標題明確字串） ----------
MACHINES = [
    ("スーパーアスラーダ01", "超級阿斯拉 01"),
    ("スーパーアスラーダ AKF-11", "超級阿斯拉 AKF-11"),
    ("スーパーアスラーダ SA-01", "超級阿斯拉 SA-01"),
    ("スーパーアスラーダ", "超級阿斯拉"),
    ("νアスラーダ", "ν 阿斯拉"),
    ("アスラーダG.S.X", "阿斯拉 G.S.X"),
    ("アスラーダ", "阿斯拉"),
    ("イシュザーク", "伊修撒克"),
    ("ナイトセイバー", "奈特薩貝爾"),
    ("凰呀", "凰呀（Ogre）"),
    ("オーガ", "凰呀（Ogre）"),
    ("ガーランド", "加蘭德"),
    ("シュピーゲル", "史匹格"),
    ("エクスペリオン", "艾克斯佩利安"),
    ("ファイアスペリオン", "火焰佩利安"),
    ("プロトジャガー", "原型捷豹"),
    ("ステルスジャガー", "匿蹤捷豹"),
    ("ブーステッドアスラーダ", "增壓阿斯拉"),
    ("エキスペリオン", "艾克斯佩利安"),
    ("ミハエル", "米海爾"),
    ("ジャッカル", "豺狼"),
]

def detect_machine(title):
    for ja, zh in MACHINES:
        if ja in (title or ""):
            return {"ja": ja, "zh": zh}
    return None

# ---------- 系列判定（僅依標題明確字串） ----------
def detect_series(title):
    t = title or ""
    if "SIN" in t or "ＳＩＮ" in t:
        return "sin"
    if "SAGA" in t:
        return "saga"
    if "ZERO" in t or "ゼロ" in t:
        return "zero"
    if "11" in t and "サイバーフォーミュラ" in t:
        return "s11"
    if "DOUBLE-ONE" in t.upper():
        return "s11"
    return "unknown"

SERIES_DEF = [
    {"id": "tv",      "name": "TV版"},
    {"id": "s11",     "name": "11"},
    {"id": "zero",    "name": "ZERO"},
    {"id": "saga",    "name": "SAGA"},
    {"id": "sin",     "name": "SIN"},
    {"id": "unknown", "name": "未標示"},
]

def norm_title(t):
    """用於跨站去重的正規化標題。"""
    t = strip_kind(t)
    t = re.sub(r"[\s　]+", "", t)
    t = t.replace("／", "/").replace("・", "").replace("－", "-")
    t = re.sub(r"[（(].*?[)）]", "", t)
    return t.lower()

# ---------- 庫存判定 ----------
def stock_from_tags(tags):
    joined = " ".join(tags or [])
    if "販売中" in joined:
        return "in_stock", "販售中"
    m = re.search(r"残り(\d+)個", joined)
    if m:
        return "low", f"僅剩 {m.group(1)} 個"
    if "残りわずか" in joined:
        return "low", "剩餘不多"
    if "予約品" in joined:
        return "preorder", "預購中"
    if "注文再開メール" in joined:
        return "unavailable", "暫停接單"
    return "unknown", "狀態未標示"

def main():
    hs_by_code = {}
    for fn in ("hs_raw.json", "hs_raw2.json"):   # raw2 後讀，其分類資訊覆蓋
        try:
            part = json.load(open(fn))
        except FileNotFoundError:
            continue
        sys.stderr.write(f"讀取 {fn}: {len(part)} 件\n")
        for it in part:
            prev = hs_by_code.get(it["code"])
            if prev:
                prev.update({k: v for k, v in it.items() if v is not None})
            else:
                hs_by_code[it["code"]] = dict(it)
    hs = list(hs_by_code.values())
    sys.stderr.write(f"hobbysearch 合併後: {len(hs)} 件\n")
    ao = json.load(open("ao_raw.json"))
    sys.stderr.write(f"讀取 ao_raw.json: {len(ao)} 件\n")

    products = []
    by_norm = {}

    # --- 青島官方（權威） ---
    for a in ao:
        title = a["title"]
        kind_id, kind_name = detect_kind(title, a.get("kind"))
        img = a.get("image") or ""
        img = re.sub(r"-\d+x\d+(\.\w+)$", r"\1", img)  # 縮圖 -> 原圖

        no = None
        m = re.search(r"No\.\s*(\d+)", a.get("seriesLine") or "")
        if m:
            no = m.group(1)

        p = {
            "id": "ao-" + a["jan"],
            "name": strip_kind(title),
            "nameJa": title,
            "kind": kind_id,
            "kindName": kind_name,
            "series": detect_series(title + " " + (a.get("seriesLine") or "")),
            "machine": detect_machine(title),
            "line": detect_line(title),
            "scale": a.get("scale") if a.get("scale") != "Non" else None,
            "maker": a.get("brand") or "AOSHIMA",
            "seriesNo": no,
            "seriesLine": a.get("seriesLine"),
            "price": a.get("price"),
            "priceNote": "官方定價（含稅）",
            "release": a.get("release"),
            "jan": a.get("jan"),
            "desc": a.get("desc"),
            "image": img or None,
            "stockState": None,
            "stockText": None,
            "sources": [{"site": "青島文化教材社（官方）", "url": a["url"]}],
        }
        products.append(p)
        by_norm[norm_title(title)] = p

    # --- hobbysearch（廣度 + 售價 + 庫存） ---
    added = 0
    for h in hs:
        title = h["title"]
        key = norm_title(title)
        state, stext = stock_from_tags(h.get("tags"))
        src = {"site": "ホビーサーチ hobbysearch", "url": h["url"]}

        if key in by_norm:  # 併入官方那筆
            p = by_norm[key]
            if all(s["url"] != src["url"] for s in p["sources"]):
                p["sources"].append(src)
            if p["stockState"] is None:
                p["stockState"], p["stockText"] = state, stext
            if h.get("price"):
                p["shopPrice"] = h["price"]
                p["shopDiscount"] = h.get("discount")
                p["shopListPrice"] = h.get("listPrice")
            continue

        kind_id, kind_name = detect_kind(title, h.get("catName"))
        p = {
            "id": "hs-" + h["code"],
            "name": strip_kind(title),
            "nameJa": title,
            "kind": kind_id,
            "kindName": kind_name,
            "series": detect_series(title),
            "machine": detect_machine(title),
            "line": detect_line(title),
            "scale": None,
            "maker": None,
            "seriesNo": None,
            "seriesLine": None,
            "price": h.get("listPrice") or h.get("price"),
            "priceNote": "店家定價" if h.get("listPrice") else "店家售價",
            "shopPrice": h.get("price"),
            "shopDiscount": h.get("discount"),
            "shopListPrice": h.get("listPrice"),
            "release": h.get("releaseLine"),
            "jan": None,
            "desc": None,
            "image": h.get("image"),
            "stockState": state,
            "stockText": stext,
            "sources": [src],
        }
        products.append(p)
        by_norm[key] = p
        added += 1

    sys.stderr.write(f"官方 {len(ao)} 件 + hobbysearch 新增 {added} 件 = {len(products)} 件\n")

    # 分類清單（只列實際出現的）
    counter = collections.Counter(p["kind"] for p in products)
    name_of = {p["kind"]: p["kindName"] for p in products}
    ICONS = {"plamo": "🏎️", "finished": "🏁", "minicar": "🚗", "figure": "🧍",
             "garage": "🛠️", "book": "📚", "cd": "🎵", "dvd": "📀", "bd": "📀",
             "goods": "🎒", "paint": "🎨", "tool": "🔧", "card": "🃏",
             "doll": "🎎", "other": "📦"}
    categories = [{"id": k, "name": name_of[k], "icon": ICONS.get(k, "📦"), "count": n}
                  for k, n in counter.most_common()]

    scount = collections.Counter(p["series"] for p in products)
    series = [dict(s, count=scount.get(s["id"], 0)) for s in SERIES_DEF
              if scount.get(s["id"], 0) > 0]

    mcount = collections.Counter(
        p["machine"]["zh"] for p in products if p.get("machine"))
    lcount = collections.Counter(
        p["line"]["name"] for p in products if p.get("line"))

    out = {
        "meta": {
            "title": "閃電霹靂車 周邊商品",
            "subtitle": "新世紀GPX Cyber Formula / 新世紀GPXサイバーフォーミュラ",
            "updatedAt": "2026-08-22",
            "sources": [
                {"site": "青島文化教材社（官方）",
                 "url": "https://www.aoshima-bk.co.jp/special/product/cyberformula/",
                 "note": "官方模型商品：定價、發售月、系列編號、JAN"},
                {"site": "ホビーサーチ hobbysearch",
                 "url": "https://www.1999.co.jp/",
                 "note": "商品廣度、實際售價與庫存狀態"},
            ],
            # 不寫死日期——網頁會用 updatedAt 自行組合，否則兩處會不一致
            "notice": "由上列來源實際抓取。價格與庫存為抓取當下狀態，"
                      "非即時報價；點擊商品可前往來源頁確認最新資訊。",
            "currency": "JPY",
        },
        "categories": categories,
        "series": series,
        "machines": [{"name": k, "count": v} for k, v in mcount.most_common()],
        "lines": [{"name": k, "count": v} for k, v in lcount.most_common()],
        "products": products,
    }

    json.dump(out, open("products.json", "w"), ensure_ascii=False, indent=1)
    sys.stderr.write(f"\n輸出 products.json：{len(products)} 件\n")
    sys.stderr.write(f"分類：{[(c['name'], c['count']) for c in categories]}\n")
    sys.stderr.write(f"系列：{[(s['name'], s['count']) for s in series]}\n")

if __name__ == "__main__":
    main()
