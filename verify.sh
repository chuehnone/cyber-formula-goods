#!/bin/bash
# 檢驗線上版是否與本機一致
#
#   ./verify.sh          比對線上與本機 HEAD
#   ./verify.sh --watch  持續檢查直到一致（部署後等待用）
#
# 比對 index.html 與 products.json 的 SHA-256。
# 相同即代表線上跑的就是本機這份，不受瀏覽器快取影響。

set -uo pipefail

BASE="https://chuehnone.viovie.co/cyber-formula-goods"
ROOT="$(cd "$(dirname "$0")" && pwd)"
CURL=/usr/bin/curl
WATCH=0

for a in "$@"; do
  case "$a" in
    --watch) WATCH=1 ;;
    -h|--help) sed -n '2,8p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) echo "未知參數：$a"; exit 1 ;;
  esac
done

cd "$ROOT"

check() {
  local allsame=1
  for f in index.html products.json; do
    local L R
    L=$(shasum -a 256 "$f" | cut -c1-12)
    R=$($CURL -sL --max-time 25 -H 'Cache-Control: no-cache' -H 'Pragma: no-cache' \
        "$BASE/$f?_=$(date +%s)" 2>/dev/null | shasum -a 256 | cut -c1-12)
    if [ "$L" = "$R" ]; then
      printf "  ✓ %-14s %s\n" "$f" "$L"
    else
      printf "  ✗ %-14s 本機 %s / 線上 %s\n" "$f" "$L" "$R"
      allsame=0
    fi
  done
  return $((1 - allsame))
}

echo "本機 HEAD：$(git log -1 --format='%h %s' 2>/dev/null || echo '(非 git repo)')"

# 有未 commit 的變更要先提醒，否則比對必然不一致
DIRTY=$(git status --porcelain index.html products.json 2>/dev/null)
[ -n "$DIRTY" ] && echo "⚠  index.html / products.json 有未 commit 的變更，線上不可能與本機相同"

echo "線上：$BASE/"
echo ""

if [ "$WATCH" -eq 1 ]; then
  for i in $(seq 1 40); do
    echo "[$(date +%H:%M:%S)] 第 $i 次檢查"
    if check; then
      echo ""
      echo "✓ 線上版已與本機一致"
      exit 0
    fi
    echo "  …等待 20 秒後重試（Pages CDN 快取 10 分鐘，最久可能等這麼久）"
    sleep 20
  done
  echo "✗ 逾時仍不一致，請檢查部署狀態："
  echo "  gh api repos/chuehnone/cyber-formula-goods/pages/builds/latest --jq .status"
  exit 1
else
  if check; then
    echo ""
    echo "✓ 線上版就是本機這一份"
  else
    echo ""
    echo "✗ 線上與本機不同。可能原因："
    echo "  1. 還沒 push，或 Pages 尚在建置"
    echo "     gh api repos/chuehnone/cyber-formula-goods/pages/builds/latest --jq .status"
    echo "  2. CDN 快取未過期（max-age=600，最多 10 分鐘）→ 用 ./verify.sh --watch 等"
    exit 1
  fi
fi
