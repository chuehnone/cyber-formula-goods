#!/usr/bin/env python3
"""印出 products.json 的統計數字。

文件裡刻意不寫死件數（會過期），需要時用這個查：

    python3 scripts/stats.py

兩站件數用「來源含該站」定義，故兩數相加會大於總數——
有部分商品兩站都收錄，那些正是可交叉比對價格的。
"""
import json, sys, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "products.json")
    d = json.load(open(path))
    p = d["products"]

    has_ao = lambda x: any("青島" in s["site"] for s in x["sources"])
    has_hs = lambda x: any("ホビー" in s["site"] for s in x["sources"])

    print(f"抓取日期   {d['meta']['updatedAt']}")
    print(f"商品總數   {len(p)}")
    print(f"分類數     {len(d['categories'])}")
    print()
    print(f"青島官方   {sum(1 for x in p if has_ao(x))}")
    print(f"hobbysearch {sum(1 for x in p if has_hs(x))}")
    print(f"兩站都有   {sum(1 for x in p if has_ao(x) and has_hs(x))}"
          f"（可交叉比對價格）")
    print()
    print(f"有中文描述 {sum(1 for x in p if x.get('descZh'))}")
    print(f"系列未標示 {sum(1 for x in p if x['series'] == 'unknown')}")
    print()
    print("分類分布：")
    for c in d["categories"]:
        print(f"  {c['icon']} {c['name']:<12} {c['count']}")
    print()
    print("機體分布（前 10）：")
    for m in d["machines"][:10]:
        print(f"  {m['name']:<16} {m['count']}")

    states = collections.Counter(x.get("stockState") for x in p)
    print()
    print("庫存狀態：")
    for k, v in states.most_common():
        print(f"  {k or '(無)':<14} {v}")


if __name__ == "__main__":
    main()
