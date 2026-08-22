#!/usr/bin/env python3
"""把 README.md 裡的統計數字同步為 products.json 的實際值。

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
    }


def sync(readme_path, s):
    txt = open(readme_path).read()
    orig = txt

    subs = [
        # 開頭條列：391 件商品，…等 18 個分類
        (r"- \d+ 件商品，(.*?)等 \d+ 個分類",
         rf"- {s['total']} 件商品，\1等 {s['categories']} 個分類"),
        # 來源表格：官方那列的件數
        (r"(\[青島文化教材社（官方）\]\([^)]+\) \| )\d+( \|)",
         rf"\g<1>{s['ao']}\g<2>"),
        # 來源表格：hobbysearch 那列的件數
        (r"(\[ホビーサーチ hobbysearch\]\([^)]+\) \| )\d+( \|)",
         rf"\g<1>{s['hs']}\g<2>"),
        # 合計行
        (r"合計 \*\*\d+ 件\*\*[^。]*。",
         rf"合計 **{s['total']} 件**，其中 {s['both']} 件兩站都有"
         rf"（故上表兩數相加大於總數），可交叉比對價格。"),
        # 抓取日期
        (r"抓取日期：\d{4}-\d{2}-\d{2}。",
         rf"抓取日期：{s['updated']}。"),
        # CLAUDE.md 提示裡的 unknown 件數
        (r"（例如 \d+ 件商品的系列標為「未標示」）",
         rf"（例如 {s['unknown_series']} 件商品的系列標為「未標示」）"),
    ]

    changed = []
    for pat, rep in subs:
        new, n = re.subn(pat, rep, txt)
        if n == 0:
            print(f"  ⚠ 找不到可替換的樣式：{pat[:46]}…", file=sys.stderr)
        elif new != txt:
            changed.append(pat[:36])
        txt = new

    if txt == orig:
        print("  README 數字已是最新，無需更動")
        return False

    open(readme_path, "w").write(txt)
    print(f"  README 已更新（{len(changed)} 處）")
    return True


def main():
    products = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "products.json")
    readme = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "README.md")
    s = stats(products)
    print(f"  實際值：{s['total']} 件 / {s['categories']} 分類 / "
          f"官方 {s['ao']} / hs {s['hs']} / 跨站重複 {s['both']} / {s['updated']}")
    sync(readme, s)


if __name__ == "__main__":
    main()
