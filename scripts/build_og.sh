#!/usr/bin/env bash
# 把 scripts/og-*.svg 轉成 repo 根目錄的 og-*.png（FB / Twitter 的社群預覽圖）。
#
# 為什麼用 Chrome 而不是 ImageMagick：
#   ImageMagick 轉 SVG 走 librsvg/Ghostscript，中文字型常掉字或換成豆腐字。
#   Chrome 的渲染結果與使用者實際看到的一致，且本機一定有。
#
# 為什麼要轉 PNG：FB 對 SVG 的 og:image 支援不良，必須給點陣圖。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

[ -x "$CHROME" ] || { echo "找不到 Chrome：$CHROME" >&2; exit 1; }

for name in index timeline; do
  svg="$ROOT/scripts/og-$name.svg"
  png="$ROOT/og-$name.png"
  [ -f "$svg" ] || { echo "缺少 $svg" >&2; exit 1; }

  # --window-size 要與 SVG 的 viewBox 一致，否則會留白或裁切
  "$CHROME" --headless --disable-gpu --hide-scrollbars \
            --default-background-color=00000000 \
            --force-device-scale-factor=1 \
            --window-size=1200,630 \
            --screenshot="$png" "file://$svg" 2>/dev/null

  [ -f "$png" ] || { echo "產生 $png 失敗" >&2; exit 1; }
  echo "  ✓ og-$name.png  $(du -h "$png" | cut -f1)"
done

echo "完成。改圖後記得重跑本腳本，並注意 FB 會快取舊圖："
echo "  https://developers.facebook.com/tools/debug/ → 貼網址 → Scrape Again"
