#!/bin/bash
# 啟動本機預覽 server（綁 0.0.0.0，同網段裝置可連入）
PORT="${1:-8080}"
cd "$(dirname "$0")" || exit 1

echo "電腦：  http://localhost:$PORT"

# 內網 IP（同一 Wi-Fi 的手機可用）
LAN=$(ipconfig getifaddr en0 2>/dev/null)
[ -n "$LAN" ] && echo "內網：  http://$LAN:$PORT"

# Tailscale IP（若有安裝並啟用）
TS=$(tailscale ip -4 2>/dev/null | head -1)
[ -n "$TS" ] && echo "Tailscale： http://$TS:$PORT"

echo "Ctrl+C 停止"
exec python3 -m http.server "$PORT" --bind 0.0.0.0
