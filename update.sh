#!/bin/bash
# 重新抓取商品資料並更新 products.json
#
#   ./update.sh          抓取 → 整併 → 翻譯 → 顯示差異（不自動 commit）
#   ./update.sh --quick  跳過耗時的分類版爬蟲（約省 8 分鐘，商品數會略少）
#   ./update.sh --push   完成後自動 commit 並 push（會觸發 Pages 重新部署）
#
# 中間產物放在 scripts/.cache/，已被 .gitignore 排除。

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CACHE="$ROOT/scripts/.cache"
QUICK=0
PUSH=0

for arg in "$@"; do
  case "$arg" in
    --quick) QUICK=1 ;;
    --push)  PUSH=1 ;;
    -h|--help) sed -n '2,10p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) echo "未知參數：$arg（用 --help 看說明）"; exit 1 ;;
  esac
done

mkdir -p "$CACHE"
cd "$CACHE"

echo "▶ 1/4 抓取青島官網…"
python3 "$ROOT/scripts/scrape_ao.py" 2>&1 | tail -2

echo "▶ 2/4 抓取 hobbysearch…"
python3 "$ROOT/scripts/scrape_hs.py" 2>&1 | tail -2

if [ "$QUICK" -eq 0 ]; then
  echo "▶ 2.5/4 抓取 hobbysearch 分類版（約 8 分鐘，可用 --quick 跳過）…"
  python3 "$ROOT/scripts/scrape2.py" 2>&1 | tail -2
else
  echo "▶ 2.5/4 略過分類版爬蟲（--quick）"
fi

echo "▶ 3/4 整併資料…"
python3 "$ROOT/scripts/build.py" 2>&1 | tail -3

echo "▶ 4/4 補上繁體中文翻譯…"
cp "$CACHE/products.json" "$ROOT/products.raw.json"
cp "$CACHE/products.json" "$ROOT/products.json"
python3 "$ROOT/scripts/translate.py" "$ROOT/products.json" 2>&1 | head -2

# 把抓取日期更新為今天
python3 - "$ROOT/products.json" <<'PY'
import json, sys, datetime
p = sys.argv[1]
d = json.load(open(p))
d["meta"]["updatedAt"] = datetime.date.today().isoformat()
json.dump(d, open(p, "w"), ensure_ascii=False, indent=1)
print("抓取日期已更新為", d["meta"]["updatedAt"])
PY

echo "▶ 產生變動紀錄…"
python3 "$ROOT/scripts/changelog.py" "$ROOT/products.json"

echo ""
echo "─────────── 與線上版的差異 ───────────"
cd "$ROOT"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  python3 - <<'PY'
import io, json, subprocess
new = json.load(open("products.json"))["products"]
try:
    old_raw = subprocess.run(["git", "show", "HEAD:products.json"],
                             capture_output=True, text=True, check=True).stdout
    old = json.load(io.StringIO(old_raw))["products"]
except Exception as e:
    print("（無法取得線上版做比對：%s）" % e)
    raise SystemExit

o = {x["id"]: x for x in old}
n = {x["id"]: x for x in new}
added   = [n[i] for i in n if i not in o]
removed = [o[i] for i in o if i not in n]
priced  = [(o[i], n[i]) for i in n if i in o
           and o[i].get("shopPrice") != n[i].get("shopPrice")]
stock   = [(o[i], n[i]) for i in n if i in o
           and o[i].get("stockState") != n[i].get("stockState")]

print(f"商品總數：{len(old)} → {len(new)}")
print(f"  新增 {len(added)}、下架 {len(removed)}、價格異動 {len(priced)}、庫存異動 {len(stock)}")
for x in added[:8]:
    print("  + " + (x.get("nameZh") or x["name"])[:56])
for x in removed[:8]:
    print("  - " + (x.get("nameZh") or x["name"])[:56])
for a, b in priced[:8]:
    print(f"  ¥ {(b.get('nameZh') or b['name'])[:40]}: "
          f"{a.get('shopPrice')} → {b.get('shopPrice')}")
PY
else
  echo "（非 git repo，略過比對）"
fi

echo "──────────────────────────────────────"
echo ""

if [ "$PUSH" -eq 1 ]; then
  if [ -z "$(git status --porcelain products.json products.raw.json)" ]; then
    echo "✓ 資料無變化，不需要 commit"
    exit 0
  fi
  DATE=$(date +%Y-%m-%d)
  git add products.json products.raw.json
  git commit -q -m "data: 更新商品資料至 $DATE"
  git push -q origin main
  echo "✓ 已推送，GitHub Pages 約 1–2 分鐘後生效"
  echo "  https://chuehnone.viovie.co/cyber-formula-goods/"
else
  echo "資料已更新到本機。確認無誤後："
  echo "  ./serve.sh                    # 本機預覽"
  echo "  git add products.json products.raw.json"
  echo "  git commit -m 'data: 更新商品資料至 $(date +%Y-%m-%d)'"
  echo "  git push"
fi
