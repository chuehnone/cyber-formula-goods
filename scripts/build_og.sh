#!/usr/bin/env bash
# 產生 repo 根目錄的 og-*.jpg（FB / Twitter 的社群預覽圖）。
#
# 素材：scripts/assets/car.jpg —— 阿斯拉 G.S.X 主視覺裁出的車體部分，
#       已切掉作品 logo、標題美術與賽道看板字樣。原始未裁的主視覺不留在 repo，
#       所以**裁切範圍無法再調整**；要改構圖就得重新取得原圖。
#
# 版面與文字在 scripts/og-*.svg，用 Chrome headless 渲染後轉成 JPG。
# 為什麼文字用 Chrome 而不是 ImageMagick：
#   ImageMagick 走 librsvg，中文字型會掉字或變豆腐字。
# 為什麼輸出 JPG：FB 對 SVG 支援不良；含照片的圖存 PNG 要 500-700KB，
#   JPG（quality 88）約 100-130KB 且肉眼無差，FB 建議小於 300KB。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CAR="$ROOT/scripts/assets/car.jpg"

[ -x "$CHROME" ] || { echo "找不到 Chrome：$CHROME" >&2; exit 1; }
[ -f "$CAR" ]    || { echo "找不到車體素材：$CAR" >&2; exit 1; }

echo "▶ 渲染 OG 圖…"
for name in index timeline; do
  svg="$ROOT/scripts/og-$name.svg"
  png="$ROOT/og-$name.png"     # 中間產物，轉完即刪
  jpg="$ROOT/og-$name.jpg"
  [ -f "$svg" ] || { echo "缺少 $svg" >&2; exit 1; }

  # --window-size 要與 SVG 的 viewBox 一致，否則會留白或裁切
  "$CHROME" --headless --disable-gpu --hide-scrollbars \
            --default-background-color=00000000 \
            --force-device-scale-factor=1 \
            --window-size=1200,630 \
            --screenshot="$png" "file://$svg" 2>/dev/null

  [ -f "$png" ] || { echo "產生 $png 失敗" >&2; exit 1; }
  magick "$png" -strip -quality 88 "$jpg"
  rm -f "$png"
  echo "  ✓ og-$name.jpg  $(du -h "$jpg" | cut -f1)"
done

echo
echo "完成。改圖後 FB 會沿用舊快取，要到 Sharing Debugger 按 Scrape Again："
echo "  https://developers.facebook.com/tools/debug/"
