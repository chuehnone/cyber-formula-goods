#!/usr/bin/env python3
"""比對新舊 products.json，把變動寫進 meta.changes 供網頁顯示。

由 update.sh 在資料更新後呼叫。舊資料取自 git HEAD（即線上版）。
只記錄「這次 vs 上次」，不累積歷史——過去的變動看 git log 即可。

寫入結構：
  meta.changes = {
    "since": "2026-08-22",        上一版的抓取日期
    "added":   [{id, name, ...}],  新增商品
    "removed": [{id, name}],       消失商品（僅名稱，已無完整資料）
    "price":   [{id, name, from, to, diff}],
    "stock":   [{id, name, from, to, fromState, toState}],
  }
每個商品另加 changeType 欄位（added/price-down/price-up/stock），供卡片標記用。
"""
import io, json, subprocess, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_previous(path_in_repo="products.json"):
    """從 git HEAD 取上一版資料；取不到回傳 None。"""
    try:
        raw = subprocess.run(["git", "show", f"HEAD:{path_in_repo}"],
                             capture_output=True, text=True, check=True,
                             cwd=ROOT).stdout
        return json.load(io.StringIO(raw))
    except Exception as e:
        print(f"  （無法取得上一版做比對：{e}）", file=sys.stderr)
        return None


def name_of(x):
    return x.get("nameZh") or x.get("name") or x.get("id")


def urls_of(x):
    return {s.get("url") for s in x.get("sources", []) if s.get("url")}


def pair_up(old, new):
    """把新舊商品配對，回傳 (pairs, added, removed)。

    先用 id 配對，剩下的再用來源 URL 配對。
    一件商品在來源站有多個頁面時，id 取決於抓取順序（見 build.py 的
    norm_title 合併），順序一變 id 就翻轉，單用 id 會把同一件商品
    算成一下架加一新增。只要共用任一來源 URL 就是同一件商品。
    """
    o = {x["id"]: x for x in old}
    n = {x["id"]: x for x in new}

    pairs = [(o[i], n[i]) for i in n if i in o]
    rest_old = [o[i] for i in o if i not in n]
    rest_new = [n[i] for i in n if i not in o]

    by_url = {}
    for x in rest_old:
        for u in urls_of(x):
            by_url.setdefault(u, x)

    matched_old = set()
    added = []
    for b in rest_new:
        a = next((by_url[u] for u in urls_of(b) if u in by_url), None)
        if a is not None and id(a) not in matched_old:
            matched_old.add(id(a))
            pairs.append((a, b))
        else:
            added.append(b)

    removed = [x for x in rest_old if id(x) not in matched_old]
    return pairs, added, removed


def build_changes(old_doc, new_doc):
    pairs, added, removed = pair_up(old_doc["products"], new_doc["products"])

    price, stock = [], []
    for a, b in pairs:
        i = b["id"]
        pa, pb = a.get("shopPrice"), b.get("shopPrice")
        if pa != pb and pa is not None and pb is not None:
            price.append({
                "id": i, "name": name_of(b),
                "from": pa, "to": pb, "diff": pb - pa,
            })
        if a.get("stockState") != b.get("stockState"):
            stock.append({
                "id": i, "name": name_of(b),
                "from": a.get("stockText"), "to": b.get("stockText"),
                "fromState": a.get("stockState"), "toState": b.get("stockState"),
            })

    return {
        "since": old_doc.get("meta", {}).get("updatedAt"),
        "added": [{"id": x["id"], "name": name_of(x),
                   "kind": x.get("kindName"), "price": x.get("shopPrice")}
                  for x in added],
        "removed": [{"id": x["id"], "name": name_of(x)} for x in removed],
        "price": price,
        "stock": stock,
    }


def tag_products(new_doc, changes):
    """在商品上標記 changeType，供卡片顯示徽章。"""
    by_id = {x["id"]: x for x in new_doc["products"]}

    for x in new_doc["products"]:
        x.pop("changeType", None)      # 清掉上一輪的標記

    for c in changes["added"]:
        if c["id"] in by_id:
            by_id[c["id"]]["changeType"] = "added"

    for c in changes["price"]:
        if c["id"] in by_id:
            by_id[c["id"]]["changeType"] = "price-down" if c["diff"] < 0 else "price-up"
            by_id[c["id"]]["priceChange"] = c["diff"]

    # 庫存變動優先度高於價格：快沒了比便宜了更需要知道
    for c in changes["stock"]:
        if c["id"] in by_id and c["toState"] in ("low", "unavailable"):
            by_id[c["id"]]["changeType"] = "stock"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "products.json")
    new_doc = json.load(open(path))

    old_doc = load_previous()
    if old_doc is None:
        new_doc["meta"].pop("changes", None)
        json.dump(new_doc, open(path, "w"), ensure_ascii=False, indent=1)
        print("  無上一版可比對，未產生變動紀錄")
        return

    changes = build_changes(old_doc, new_doc)
    total = (len(changes["added"]) + len(changes["removed"])
             + len(changes["price"]) + len(changes["stock"]))

    if total == 0:
        new_doc["meta"].pop("changes", None)
        for x in new_doc["products"]:
            x.pop("changeType", None)
            x.pop("priceChange", None)
        json.dump(new_doc, open(path, "w"), ensure_ascii=False, indent=1)
        print("  無變動")
        return

    new_doc["meta"]["changes"] = changes
    tag_products(new_doc, changes)
    json.dump(new_doc, open(path, "w"), ensure_ascii=False, indent=1)

    print(f"  自 {changes['since']} 起：新增 {len(changes['added'])}、"
          f"下架 {len(changes['removed'])}、價格 {len(changes['price'])}、"
          f"庫存 {len(changes['stock'])}")


if __name__ == "__main__":
    main()
