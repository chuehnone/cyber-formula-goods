#!/usr/bin/env python3
"""把 README.md 與 CLAUDE.md 裡的統計數字同步為 products.json 的實際值。

由 update.sh 在資料更新後自動呼叫，避免 README 與實際資料脫節。

用「來源含該站」的定義計算兩站件數（兩者相加會大於總數，因為有跨站重複，
下一行會標明重複件數），與表格語意一致。
"""
import json, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def stats(path):
    d = json.load(open(path))
    p = d["products"]
    has_ao = lambda x: any("青島" in s["site"] for s in x["sources"])
    has_hs = lambda x: any("ホビー" in s["site"] for s in x["sources"])
    return {
        "total": len(p),
        "categories": len(d["categories"]),
        "updated": d["meta"]["updatedAt"],
        "ao": sum(1 for x in p if has_ao(x)),
        "hs": sum(1 for x in p if has_hs(x)),
        # 真正跨兩站的才算可交叉比對（同站多筆不算）
        "both": sum(1 for x in p if has_ao(x) and has_hs(x)),
        "unknown_series": sum(1 for x in p if x["series"] == "unknown"),
        "desc": sum(1 for x in p if x.get("descZh")),
    }


def sync(path, s, subs):
    txt = open(path).read()
    orig = txt

    changed = []
    for pat, rep in subs:
        new, n = re.subn(pat, rep, txt, flags=re.M)
        if n == 0:
            print(f"  ⚠ 找不到可替換的樣式：{pat[:46]}…", file=sys.stderr)
        elif new != txt:
            changed.append(pat[:36])
        txt = new

    if txt == orig:
        print("數字已是最新，無需更動")
        return False

    open(path, "w").write(txt)
    print(f"已更新（{len(changed)} 處）")
    return True


def readme_subs(s):
    return [
        (r"- \d+ 件商品，(.*?)等 \d+ 個分類",
         rf"- {s['total']} 件商品，\1等 {s['categories']} 個分類"),
        (r"(\[青島文化教材社（官方）\]\([^)]+\) \| )\d+( \|)",
         rf"\g<1>{s['ao']}\g<2>"),
        (r"(\[ホビーサーチ hobbysearch\]\([^)]+\) \| )\d+( \|)",
         rf"\g<1>{s['hs']}\g<2>"),
        (r"合計 \*\*\d+ 件\*\*[^。]*。",
         rf"合計 **{s['total']} 件**，其中 {s['both']} 件兩站都有"
         rf"（故上表兩數相加大於總數），可交叉比對價格。"),
        (r"抓取日期：\d{4}-\d{2}-\d{2}。",
         rf"抓取日期：{s['updated']}。"),
        (r"（例如 \d+ 件商品的系列標為「未標示」）",
         rf"（例如 {s['unknown_series']} 件商品的系列標為「未標示」）"),
    ]


def claude_subs(s):
    return [
        (r"商品資料（\d+ 件，翻譯後）",
         rf"商品資料（{s['total']} 件，翻譯後）"),
        (r"^\d+ 件商品的 `series` 是 `unknown`",
         rf"{s['unknown_series']} 件商品的 `series` 是 `unknown`"),
        (r"商品描述（目前 \d+ 筆）",
         rf"商品描述（目前 {s['desc']} 筆）"),
        (r"只有青島官方那 \d+ 件有商品描述",
         rf"只有青島官方那 {s['ao']} 件有商品描述"),
        (r"故 \d+ \+ \d+ > \d+——有 \d+ 件兩站都有",
         rf"故 {s['ao']} + {s['hs']} > {s['total']}——有 {s['both']} 件兩站都有"),
        (r"(\[青島官方\]\([^)]+\) \| )\d+( \|)",
         rf"\g<1>{s['ao']}\g<2>"),
        (r"(\[hobbysearch\]\([^)]+\) \| )\d+( \|)",
         rf"\g<1>{s['hs']}\g<2>"),
        (r"故兩數相加大於總數：\d+ 件兩站都有。\n這 \d+ 件",
         rf"故兩數相加大於總數：{s['both']} 件兩站都有。\n這 {s['both']} 件"),
    ]


def main():
    products = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "products.json")
    s = stats(products)
    print(f"  實際值：{s['total']} 件 / {s['categories']} 分類 / "
          f"官方 {s['ao']} / hs {s['hs']} / 跨站重複 {s['both']} / {s['updated']}")

    targets = [
        (sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "README.md"),
         readme_subs(s), "README.md"),
        (os.path.join(ROOT, "CLAUDE.md"), claude_subs(s), "CLAUDE.md"),
    ]
    for path, subs, label in targets:
        if not os.path.exists(path):
            continue
        print(f"  {label}:", end=" ")
        sync(path, s, subs)


if __name__ == "__main__":
    main()
