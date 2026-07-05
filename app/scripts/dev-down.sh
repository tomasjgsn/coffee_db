#!/usr/bin/env bash
# Stop THE COUNTER dev server. A plain OS-level port free, independent of
# however the server was started — Claude's preview tool doesn't reliably
# remember servers it started across turns, so this doesn't depend on it.
set -euo pipefail

PORT=5173

listener_pid() {
	lsof -ti ":${PORT}" -sTCP:LISTEN 2>/dev/null || true
}

looks_like_our_server() {
	local pid="$1"
	ps -p "$pid" -o command= 2>/dev/null | grep -qiE 'vite|coffee_db/app'
}

pid="$(listener_pid)"
if [ -z "$pid" ]; then
	echo "Nothing running on port ${PORT} — already stopped."
	exit 0
fi

if ! looks_like_our_server "$pid"; then
	echo "Port ${PORT} is held by something that isn't THE COUNTER (pid ${pid}):"
	ps -p "$pid" -o pid,command= 2>/dev/null || true
	echo "Not touching it."
	exit 1
fi

echo "Stopping dev server (pid ${pid})…"
kill "$pid" 2>/dev/null || true
for _ in $(seq 1 10); do
	listener_pid | grep -q "$pid" || break
	sleep 0.3
done
kill -9 "$pid" 2>/dev/null || true

if [ -z "$(listener_pid)" ]; then
	echo "Port ${PORT} is free."
else
	echo "Warning: something is still listening on ${PORT}."
	exit 1
fi
