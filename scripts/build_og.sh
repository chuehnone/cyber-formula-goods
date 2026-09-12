#!/usr/bin/env bash
# 產生 repo 根目錄的 og-*.png（FB / Twitter 的社群預覽圖）。
#
# 流程：
#   1. 從 scripts/assets/asurada-source.png 裁出車體區（避開官方 logo 與作品標題美術）
#   2. 疊上深色漸層遮罩，讓左側文字有足夠對比
#   3. 用 Chrome headless 把 scripts/og-*.svg 渲染成 PNG
#
# 為什麼文字用 Chrome 而不是 ImageMagick：
#   ImageMagick 畫中文會掉字或變豆腐字。Chrome 的渲染與使用者看到的一致。
#
# 為什麼要轉 PNG：FB 對 SVG 的 og:image 支援不良，必須給點陣圖。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SRC="$ROOT/scripts/assets/asurada-source.png"
CAR="$ROOT/scripts/assets/car.png"

[ -x "$CHROME" ] || { echo "找不到 Chrome：$CHROME" >&2; exit 1; }
[ -f "$SRC" ]    || { echo "找不到來源圖：$SRC" >&2; exit 1; }

# 裁切參數：只取車體。切掉左側的作品 logo／標題美術、頂端的 ASURADA GSX 橫幅、
# 右下的 SUGO ASURADA 字樣。改圖時用
#   magick "$SRC" -crop WxH+X+Y +repage /tmp/t.png
# 先確認再改這行。
echo "▶ 裁出車體…"
magick "$SRC" -crop 1210x520+790+160 +repage -resize 1200x "$CAR"
echo "  ✓ $(magick identify -format '%wx%h' "$CAR")"

echo "▶ 渲染 OG 圖…"
for name in index timeline; do
  svg="$ROOT/scripts/og-$name.svg"
  png="$ROOT/og-$name.png"
  jpg="$ROOT/og-$name.jpg"
  [ -f "$svg" ] || { echo "缺少 $svg" >&2; exit 1; }

  # --window-size 要與 SVG 的 viewBox 一致，否則會留白或裁切
  "$CHROME" --headless --disable-gpu --hide-scrollbars \
            --default-background-color=00000000 \
            --force-device-scale-factor=1 \
            --window-size=1200,630 \
            --screenshot="$png" "file://$svg" 2>/dev/null

  [ -f "$png" ] || { echo "產生 $png 失敗" >&2; exit 1; }
  # 轉 JPG：含照片的圖用 PNG 會到 500–700KB，JPG 約 100KB 且肉眼無差。
  # FB 建議 og:image 小於 300KB，載入也較快。PNG 只是中間產物，不進 repo。
  magick "$png" -strip -quality 88 "$jpg"
  rm -f "$png"
  echo "  ✓ og-$name.jpg  $(du -h "$jpg" | cut -f1)"
done

echo
echo "完成。改圖後 FB 會沿用舊快取，要到 Sharing Debugger 按 Scrape Again："
echo "  https://developers.facebook.com/tools/debug/"
