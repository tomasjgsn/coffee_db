#!/usr/bin/env bash
# Start THE COUNTER dev server and open it in the real default browser.
# Safe to run repeatedly: reuses a server that's already up, and refuses
# to touch anything on port 5173 that doesn't look like our own vite process.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PORT=5173
URL="http://localhost:${PORT}"
LOG_FILE="/tmp/the-counter-dev.log"

is_up() {
	curl -s -o /dev/null -w '%{http_code}' --max-time 2 "$URL" 2>/dev/null | grep -q '^200$'
}

listener_pid() {
	lsof -ti ":${PORT}" -sTCP:LISTEN 2>/dev/null || true
}

looks_like_our_server() {
	local pid="$1"
	ps -p "$pid" -o command= 2>/dev/null | grep -qiE 'vite|coffee_db/app'
}

if is_up; then
	echo "THE COUNTER is already running at ${URL}"
	open "$URL"
	exit 0
fi

pid="$(listener_pid)"
if [ -n "$pid" ]; then
	if looks_like_our_server "$pid"; then
		echo "Found a stale dev server (pid ${pid}) on port ${PORT} — clearing it."
		kill "$pid" 2>/dev/null || true
		for _ in $(seq 1 10); do
			listener_pid | grep -q "$pid" || break
			sleep 0.3
		done
		kill -9 "$pid" 2>/dev/null || true
	else
		echo "Port ${PORT} is already in use by something that isn't THE COUNTER (pid ${pid}):"
		ps -p "$pid" -o pid,command= 2>/dev/null || true
		echo "Not touching it. Free the port yourself, or stop whatever that is, then retry."
		exit 1
	fi
fi

echo "Starting THE COUNTER dev server…"
(cd "$APP_DIR" && nohup npm run dev >"$LOG_FILE" 2>&1 &)

for _ in $(seq 1 30); do
	if is_up; then
		echo "Up at ${URL}"
		open "$URL"
		exit 0
	fi
	sleep 0.5
done

echo "Server didn't come up within 15s — check ${LOG_FILE}"
exit 1
